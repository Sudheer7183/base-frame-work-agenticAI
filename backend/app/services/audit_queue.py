"""
Audit Queue Service  —  Redis Streams belt
==========================================
Thin wrapper around Redis Streams (XADD / XREADGROUP / XACK) that forms the
asynchronous "belt" between the Ingestion step (producer) and the LangGraph
worker (consumer).

Why Redis Streams and NOT asyncio.Queue:
  • asyncio.Queue lives in-process and dies on restart
  • Redis Streams survive restarts, scale to multiple workers, and give
    at-least-once delivery via consumer-group acknowledgement
  • Already in your stack (port 6379, redis==5.0.3 in requirements.txt)

Stream key layout
─────────────────
  wc:audit:pipeline          ← main processing belt (ingested → variance → report)
  wc:audit:pipeline.{tenant} ← optional tenant-scoped sub-stream (future use)

Message payload (all string values — Redis requires it)
───────────────────────────────────────────────────────
  audit_case_id       DB integer PK of the wc_audit_cases row
  policy_number       human-readable policy identifier
  tenant_id           tenant slug (for setting search_path in worker)
  schema_name         postgres schema to SET search_path for this tenant
  payroll_file_path   file path stored when case was created
  policy_xml_path
  audit_meta_file_path

File: backend/app/services/audit_queue.py
"""

import logging
from typing import Optional

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# ── Stream / group constants ──────────────────────────────────────────────────

STREAM_KEY     = "wc:audit:pipeline"
CONSUMER_GROUP = "wc-variance-workers"

# Max entries kept in the stream (older entries trimmed automatically)
STREAM_MAXLEN  = 10_000


# ── Connection helper ─────────────────────────────────────────────────────────

_redis_client: Optional[aioredis.Redis] = None


def get_redis() -> aioredis.Redis:
    """
    Return the module-level Redis client.
    Call set_redis_client() once at startup (from main.py lifespan).
    """
    if _redis_client is None:
        raise RuntimeError(
            "Redis client not initialised. "
            "Call audit_queue.set_redis_client(client) in your startup handler."
        )
    return _redis_client


def set_redis_client(client: aioredis.Redis) -> None:
    """Store the shared redis client — called once from main.py startup."""
    global _redis_client
    _redis_client = client
    logger.info("[AuditQueue] Redis client registered.")


# ── Consumer group bootstrap ──────────────────────────────────────────────────

async def ensure_consumer_group(redis: aioredis.Redis) -> None:
    """
    Create the consumer group if it does not exist yet.
    id="0" means "deliver all messages from the beginning of the stream".
    mkstream=True creates the stream key if it does not exist.
    Safe to call on every startup — the BUSYGROUP error is suppressed.
    """
    try:
        await redis.xgroup_create(
            STREAM_KEY,
            CONSUMER_GROUP,
            id="0",
            mkstream=True,
        )
        logger.info(
            f"[AuditQueue] Consumer group '{CONSUMER_GROUP}' "
            f"created on stream '{STREAM_KEY}'."
        )
    except Exception as exc:
        # BUSYGROUP = group already exists — totally fine
        if "BUSYGROUP" in str(exc):
            logger.debug(f"[AuditQueue] Consumer group already exists — OK.")
        else:
            logger.error(f"[AuditQueue] xgroup_create error: {exc}")
            raise


# ── Producer ──────────────────────────────────────────────────────────────────

async def push_to_pipeline(
    redis:                aioredis.Redis,
    audit_case_id:        int,
    policy_number:        str,
    tenant_id:            str,
    schema_name:          str,
    payroll_file_path:    str,
    policy_xml_path:      str,
    audit_meta_file_path: str = "",
    data_source:          str = "upload",
) -> str:
    """
    XADD a new job onto the audit pipeline stream.

    Returns the Redis message ID (e.g. "1712345678901-0").
    This call is non-blocking — it returns as soon as the message is written.

    Call this once from the /start endpoint AFTER the AuditCase row has been
    created in PostgreSQL with status="pending".
    """
    payload = {
        "audit_case_id":        str(audit_case_id),
        "policy_number":        policy_number,
        "tenant_id":            tenant_id,
        "schema_name":          schema_name,
        "payroll_file_path":    payroll_file_path,
        "policy_xml_path":      policy_xml_path,
        "audit_meta_file_path": audit_meta_file_path,
        "data_source":          data_source,
    }

    msg_id = await redis.xadd(STREAM_KEY, payload, maxlen=STREAM_MAXLEN, approximate=True)

    logger.info(
        f"[AuditQueue] XADD → stream={STREAM_KEY}  "
        f"case={audit_case_id}  policy={policy_number}  msg_id={msg_id}"
    )
    return msg_id


# ── Consumer read (called inside the worker loop) ─────────────────────────────

async def read_next(
    redis:         aioredis.Redis,
    consumer_name: str,
    block_ms:      int = 2000,
    count:         int = 1,
) -> list:
    """
    XREADGROUP — block up to `block_ms` ms waiting for new messages.

    Returns a list of (msg_id, data_dict) tuples.
    If the stream has no new messages within the timeout, returns [].

    '>' means "deliver only messages not yet seen by this consumer group".
    """
    raw = await redis.xreadgroup(
        CONSUMER_GROUP,
        consumer_name,
        {STREAM_KEY: ">"},
        count=count,
        block=block_ms,
    )

    if not raw:
        return []

    results = []
    for _stream, entries in raw:
        for msg_id, data in entries:
            # Redis returns bytes keys/values — decode them
            decoded = {
                k.decode() if isinstance(k, bytes) else k:
                v.decode() if isinstance(v, bytes) else v
                for k, v in data.items()
            }
            results.append((msg_id, decoded))

    return results


async def ack(redis: aioredis.Redis, msg_id) -> None:
    """
    XACK — mark a message as successfully processed.
    After this call Redis will never re-deliver the message.
    """
    await redis.xack(STREAM_KEY, CONSUMER_GROUP, msg_id)
    logger.debug(f"[AuditQueue] XACK msg_id={msg_id}")


# ── Queue health / monitoring helpers ────────────────────────────────────────

async def queue_length(redis: aioredis.Redis) -> int:
    """Return the total number of messages currently in the stream."""
    try:
        info = await redis.xlen(STREAM_KEY)
        return info
    except Exception:
        return -1


async def pending_count(redis: aioredis.Redis) -> int:
    """Return the number of messages delivered but not yet ACKed."""
    try:
        info = await redis.xpending(STREAM_KEY, CONSUMER_GROUP)
        # info is a dict with 'pending' key
        return info.get("pending", 0) if isinstance(info, dict) else int(info[0])
    except Exception:
        return -1
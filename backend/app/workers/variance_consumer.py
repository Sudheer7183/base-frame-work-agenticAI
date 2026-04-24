

"""
Variance Consumer Worker  — FULLY FIXED + HITL CONFIG
======================================================
Fixes applied vs the uploaded version:

1. REDIS DISTRIBUTED LOCK  (existing)
   Prevents two coroutines from ever running _run_graph() for the same
   audit_case_id simultaneously.  Key = "audit_lock:{id}", TTL = 30 min.

2. ACK-EARLY  (existing)
   XACK is sent BEFORE _run_graph() starts (after lock is acquired).
   Prevents replay of long-running HITL cases on server restart.

3. IDEMPOTENCY GUARD  (existing)
   If the case is already "processing", "review", or "completed", skip.

4. SCHEMA_NAME passed to create_initial_state  (existing bug fix)
   hitl_checkpoint.py needs the schema name for correct DB schema routing.

5. _db_update_status("review") REMAINS REMOVED  (existing fix)
   That line ran AFTER hitl_checkpoint returned, resetting status back to
   "review" and showing the HITL panel a second time.

6. HITL GLOBAL CONFIG INJECTION  (NEW)
   Before building the initial state, _load_hitl_globally_enabled() reads
   the tenant's hitl_enabled flag (Redis cache -> DB fallback, defaults True).
   The flag is injected as hitl_globally_enabled into create_initial_state
   so assess_risk can force hitl_required=False when the administrator has
   disabled HITL for all audits via the Administration -> Configuration tab.

File: backend/app/workers/variance_consumer.py
"""

import asyncio
import json
import logging
import os
import socket
from datetime import datetime
from typing import Optional

import redis.asyncio as aioredis
from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.cache import get_cache_manager          # NEW (for HITL config)
from app.models.wc_audit import AuditCase, AuditReport
from app.agent_langgraph.wc_graph_builder import build_wc_audit_graph
from app.agent_langgraph.wc_state import create_initial_state
from app.services.audit_queue import (
    STREAM_KEY,
    CONSUMER_GROUP,
    ensure_consumer_group,
    read_next,
    ack,
)

logger = logging.getLogger(__name__)

CONSUMER_NAME = f"worker-{socket.gethostname()}-{os.getpid()}"

# Config DB key — must match wc_hitl_config_endpoint.py
_AUDIT_CONFIG_DB_KEY   = "audit_config"
_HITL_CONFIG_CACHE_TTL = 60   # seconds


# -----------------------------------------------------------------------------
# Distributed lock helpers  (existing)
# -----------------------------------------------------------------------------

async def _acquire_lock(redis: aioredis.Redis, audit_case_id: int) -> bool:
    """
    Try to acquire a per-case execution lock.
    Returns True if lock was acquired, False if another coroutine holds it.
    TTL = 30 minutes — long enough to survive a slow HITL review.
    """
    lock_key = f"audit_lock:{audit_case_id}"
    return bool(await redis.set(lock_key, "1", nx=True, ex=1800))


async def _release_lock(redis: aioredis.Redis, audit_case_id: int) -> None:
    """Release the per-case execution lock."""
    lock_key = f"audit_lock:{audit_case_id}"
    await redis.delete(lock_key)


# -----------------------------------------------------------------------------
# HITL global config loader  (NEW — Fix 6)
# -----------------------------------------------------------------------------

async def _load_hitl_globally_enabled(schema: str, tenant_slug: str) -> bool:
    """
    Return the tenant's ``hitl_globally_enabled`` flag.

    Read order:
      1. Redis cache  (key: wc:config:<tenant_slug>, TTL 60 s)
         Written/invalidated by PATCH /api/v1/wc-audit/admin/config.
      2. PostgreSQL   wc_tenant_config table, key = 'audit_config'
      3. Defaults to True if config row does not exist yet —
         full backwards compatibility for existing tenants.
    """
    cache     = get_cache_manager()
    cache_key = f"wc:config:{tenant_slug}"

    # 1. Redis cache
    try:
        cached = await cache.get(cache_key)
        if cached is not None:
            flag = bool(cached.get("hitl_enabled", True))
            logger.debug(
                f"[Worker] HITL config from cache: "
                f"tenant={tenant_slug} hitl_globally_enabled={flag}"
            )
            return flag
    except Exception as cache_exc:
        logger.warning(
            f"[Worker] HITL config cache read failed "
            f"(falling through to DB): {cache_exc}"
        )

    # 2. PostgreSQL fallback
    db = SessionLocal()
    try:
        db.execute(text(f'SET search_path TO "{schema}", public'))
        row = db.execute(
            text("SELECT value FROM wc_tenant_config WHERE key = :k"),
            {"k": _AUDIT_CONFIG_DB_KEY},
        ).fetchone()
        cfg  = dict(row[0]) if row else {}
        flag = bool(cfg.get("hitl_enabled", True))
    except Exception as db_exc:
        # Table may not exist yet on first deploy — treat as HITL enabled
        logger.warning(
            f"[Worker] HITL config DB read failed for tenant={tenant_slug} "
            f"(defaulting to hitl_globally_enabled=True): {db_exc}"
        )
        flag = True
    finally:
        db.close()

    # Populate cache so subsequent audits in this minute skip the DB round-trip
    try:
        await cache.set(
            cache_key,
            {"hitl_enabled": flag},
            ttl=_HITL_CONFIG_CACHE_TTL,
        )
    except Exception:
        pass  # non-fatal

    logger.info(
        f"[Worker] HITL config loaded from DB: "
        f"tenant={tenant_slug} hitl_globally_enabled={flag}"
    )
    return flag


# -----------------------------------------------------------------------------
# DB helpers (sync — run in thread pool via asyncio.to_thread)
# -----------------------------------------------------------------------------

def _db_get_case(audit_case_id: int, schema: str) -> Optional[AuditCase]:
    db = SessionLocal()
    try:
        db.execute(text(f'SET search_path TO "{schema}", public'))
        return db.query(AuditCase).filter(AuditCase.id == audit_case_id).first()
    finally:
        db.close()


def _db_update_status(
    audit_case_id: int,
    schema: str,
    status: str,
    error_msg: str = "",
) -> None:
    db = SessionLocal()
    try:
        db.execute(text(f'SET search_path TO "{schema}", public'))
        case = db.query(AuditCase).filter(AuditCase.id == audit_case_id).first()
        if case:
            case.status = status
            if status == "completed":
                case.completed_at = datetime.utcnow()
            if error_msg:
                case.auditor_notes = error_msg
            case.updated_at = datetime.utcnow()
            db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(f"[Worker] _db_update_status failed: {exc}")
    finally:
        db.close()


def _db_flush_intermediate_state(
    audit_case_id: int,
    schema: str,
    state: dict,
) -> None:
    """
    Write variance / risk data from LangGraph state into the wc_audit_cases row.
    Called from the worker when hitl_checkpoint node output is detected AND
    from hitl_checkpoint.py itself before blocking on event.wait().
    """
    from sqlalchemy.orm.attributes import flag_modified

    db = SessionLocal()
    try:
        db.execute(text(f'SET search_path TO "{schema}", public'))
        case = db.query(AuditCase).filter(AuditCase.id == audit_case_id).first()
        if not case:
            return

        overall = state.get("overall_variance") or {}
        case.total_earned_exposure = overall.get("earned_exposure", 0) or 0
        case.total_earned_premium  = overall.get("earned_premium",  0) or 0
        case.total_est_exposure    = overall.get("est_exposure",    0) or 0
        case.total_est_ytd_premium = overall.get("est_ytd_premium", 0) or 0
        case.total_variance        = overall.get("variance",        0) or 0
        case.total_variance_pct    = overall.get("variance_pct",    0) or 0

        if state.get("risk_level"):
            case.risk_level     = state["risk_level"]
        if state.get("recommendation"):
            case.recommendation = state["recommendation"]
        if state.get("hitl_required") is not None:
            case.hitl_required  = bool(state["hitl_required"])
        if state.get("submitted_count") is not None:
            case.submitted_count      = state["submitted_count"]
        if state.get("expected_submissions") is not None:
            case.expected_submissions = state["expected_submissions"]
        if state.get("actual_submissions") is not None:
            case.actual_submissions   = state["actual_submissions"]
        if state.get("first_check_date"):
            case.first_check_date = state["first_check_date"]
        if state.get("last_check_date"):
            case.last_check_date  = state["last_check_date"]

        case.updated_at = datetime.utcnow()
        db.commit()
        logger.info(
            f"[Worker] Intermediate state flushed for case {audit_case_id}: "
            f"variance={overall.get('variance', 0):.2f}  "
            f"risk={state.get('risk_level')}  "
            f"hitl_required={state.get('hitl_required')}"
        )
    except Exception as exc:
        db.rollback()
        logger.error(
            f"[Worker] _db_flush_intermediate_state failed case={audit_case_id}: {exc}"
        )
    finally:
        db.close()


def _db_append_agent_log(
    audit_case_id: int,
    schema: str,
    log_entry: dict,
) -> None:
    """Append one agent log entry to wc_audit_reports.report_json."""
    from sqlalchemy.orm.attributes import flag_modified

    db = SessionLocal()
    try:
        db.execute(text(f'SET search_path TO "{schema}", public'))
        report = (
            db.query(AuditReport)
            .filter(AuditReport.audit_case_id == audit_case_id)
            .with_for_update()
            .first()
        )
        if report is None:
            report = AuditReport(
                audit_case_id = audit_case_id,
                report_json   = {"agent_logs": [log_entry]},
                generated_at  = datetime.utcnow(),
            )
            db.add(report)
        else:
            existing = report.report_json if report.report_json else {}
            logs = list(existing.get("agent_logs", []))
            logs.append(log_entry)
            report.report_json = {"agent_logs": logs}
            flag_modified(report, "report_json")

        db.commit()
        logger.debug(
            f"[Worker] log saved: case={audit_case_id} agent={log_entry.get('agent')}"
        )
    except Exception as exc:
        db.rollback()
        logger.error(
            f"[Worker] _db_append_agent_log failed case={audit_case_id}: {exc}"
        )
    finally:
        db.close()


# -----------------------------------------------------------------------------
# Core graph runner
# -----------------------------------------------------------------------------

async def _run_graph(
    audit_case_id:         int,
    policy_number:         str,
    tenant_id:             str,
    schema_name:           str,
    payroll_file_path:     str,
    policy_xml_path:       str,
    audit_meta_file_path:  str,
    data_source:           str  = "upload",
    hitl_globally_enabled: bool = True,       # NEW (Fix 6)
) -> None:
    """
    Build the initial WCAuditState, run build_wc_audit_graph().astream(),
    and stream each node output back to the DB.

    The only change vs the original is the new ``hitl_globally_enabled``
    parameter which is passed straight into create_initial_state.
    assess_risk reads it and forces hitl_required=False when it is False.
    All other logic is unchanged.
    """
    # FIX 3 — Idempotency guard: skip if already being processed or done
    case = await asyncio.to_thread(_db_get_case, audit_case_id, schema_name)
    if case and case.status in ("processing", "review", "completed"):
        logger.warning(
            f"[Worker] Skipping case={audit_case_id} — "
            f"already in status='{case.status}'. Duplicate execution blocked."
        )
        return

    # Mark processing
    await asyncio.to_thread(
        _db_update_status, audit_case_id, schema_name, "processing"
    )

    # Build LangGraph initial state — inject HITL global flag (Fix 6)
    initial_state = create_initial_state(
        audit_case_id         = audit_case_id,
        policy_number         = policy_number,
        payroll_file_path     = payroll_file_path,
        policy_xml_path       = policy_xml_path,
        audit_meta_file_path  = audit_meta_file_path,
        tenant_id             = tenant_id,
        schema_name           = schema_name,            # FIX 4
        data_source           = data_source,
        hitl_globally_enabled = hitl_globally_enabled,  # FIX 6
    )

    graph = build_wc_audit_graph()

    last_state: dict = {}
    current_status   = "processing"

    _NODE_TO_AGENT_KEY = {
        "parse_payroll_excel":  "ingestion_excel",
        "parse_policy_xml":     "ingestion_xml",
        "parse_audit_metadata": "ingestion_audit_meta",
        "api_ingestion":        "ingestion_excel",
        "noop_xml":             "ingestion_xml",
        "noop_meta":            "ingestion_audit_meta",
        "officer_agent":        "officer_agent",
        "class_code_agent":     "class_code_agent",
        "frequency_agent":      "frequency_agent",
        "calculate_variance":   "premium_agent",
        "assess_risk":          "risk_assessor",
        "explanation_agent":    "explanation_agent",
        "generate_report":      "explanation_agent",
        "persist_to_database":  "explanation_agent",
        "hitl_checkpoint":      "hitl_checkpoint",
    }

    async for state_chunk in graph.astream(initial_state):
        if not isinstance(state_chunk, dict):
            continue

        for node_name, node_output in state_chunk.items():
            if not isinstance(node_output, dict):
                continue

            agent_key   = _NODE_TO_AGENT_KEY.get(node_name, node_name)
            node_errors = node_output.get("errors") or []
            node_status = "error" if node_errors else "complete"

            await asyncio.to_thread(
                _db_append_agent_log,
                audit_case_id,
                schema_name,
                {
                    "agent":     agent_key,
                    "status":    node_status,
                    "node":      node_name,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            # Merge node output into running state snapshot
            # MUST happen before HITL flush so last_state has variance data
            last_state.update(node_output)

            # HITL node completed (i.e. user already approved) — flush final state
            # FIX 5: _db_update_status("review") is NOT called here — it was the
            # bug that showed the HITL panel a second time after approval.
            if node_name == "hitl_checkpoint":
                await asyncio.to_thread(
                    _db_flush_intermediate_state,
                    audit_case_id,
                    schema_name,
                    last_state,
                )
                logger.info(
                    f"[Worker] Case {audit_case_id}: HITL resolved, "
                    "post-approval state flushed."
                )

    # Graph fully finished
    errors = last_state.get("errors") or []
    if current_status not in ("review", "error"):
        final_status = "error" if errors else "completed"
        await asyncio.to_thread(
            _db_update_status,
            audit_case_id,
            schema_name,
            final_status,
            str(errors) if errors else "",
        )

    logger.info(
        f"[Worker] Case {audit_case_id} finished — "
        f"status={'error' if errors else 'completed'}"
    )


# -----------------------------------------------------------------------------
# Main consumer loop
# -----------------------------------------------------------------------------

async def run_variance_worker(redis: aioredis.Redis) -> None:
    """
    Infinite consumer loop. Runs as a background asyncio task.

    Error behaviour
    ---------------
    Graph execution errors are caught, written to DB as status="error".
    With ACK-early, the message is already consumed so Redis will not retry.
    Manual retry is done by re-queueing the case via /start-from-api.
    """
    logger.info(f"[Worker] Starting — consumer_name={CONSUMER_NAME}")

    await ensure_consumer_group(redis)

    consecutive_errors = 0

    while True:
        try:
            messages = await read_next(redis, CONSUMER_NAME, block_ms=2000, count=1)
            consecutive_errors = 0
        except asyncio.CancelledError:
            logger.info("[Worker] Cancelled — shutting down gracefully.")
            break
        except Exception as exc:
            consecutive_errors += 1
            wait = min(2 ** consecutive_errors, 60)
            logger.error(
                f"[Worker] Redis read error (attempt {consecutive_errors}): {exc}. "
                f"Retrying in {wait}s."
            )
            await asyncio.sleep(wait)
            continue

        if not messages:
            await asyncio.sleep(0)
            continue

        for msg_id, data in messages:
            audit_case_id        = int(data["audit_case_id"])
            policy_number        = data["policy_number"]
            tenant_id            = data["tenant_id"]
            schema_name          = data.get("schema_name", "public")
            payroll_file_path    = data["payroll_file_path"]
            policy_xml_path      = data["policy_xml_path"]
            audit_meta_file_path = data.get("audit_meta_file_path", "")
            data_source          = data.get("data_source", "upload")

            logger.info(
                f"[Worker] Picked up msg_id={msg_id}  "
                f"case={audit_case_id}  policy={policy_number}  tenant={tenant_id}"
            )

            # FIX 1 — Acquire distributed lock before doing anything
            lock_acquired = await _acquire_lock(redis, audit_case_id)
            if not lock_acquired:
                logger.warning(
                    f"[Worker] Duplicate execution blocked — "
                    f"lock already held for case={audit_case_id}. ACKing to discard."
                )
                await ack(redis, msg_id)
                continue

            # FIX 2 — ACK EARLY: message is consumed before graph starts.
            # The DB row already exists, so no data is lost on restart.
            await ack(redis, msg_id)
            logger.info(f"[Worker] ACKed (early) msg_id={msg_id}  case={audit_case_id}")

            try:
                # FIX 6 — Load HITL global config before starting the graph.
                # Reads from Redis cache (written by PATCH /admin/config),
                # falls back to the wc_tenant_config DB table,
                # defaults to True (HITL on) if the row does not exist yet.
                hitl_globally_enabled = await _load_hitl_globally_enabled(
                    schema=schema_name,
                    tenant_slug=tenant_id,
                )
                logger.info(
                    f"[Worker] Case {audit_case_id} — "
                    f"hitl_globally_enabled={hitl_globally_enabled}"
                )

                await _run_graph(
                    audit_case_id         = audit_case_id,
                    policy_number         = policy_number,
                    tenant_id             = tenant_id,
                    schema_name           = schema_name,
                    payroll_file_path     = payroll_file_path,
                    policy_xml_path       = policy_xml_path,
                    audit_meta_file_path  = audit_meta_file_path,
                    data_source           = data_source,
                    hitl_globally_enabled = hitl_globally_enabled,  # FIX 6
                )

            except asyncio.CancelledError:
                raise

            except Exception as exc:
                logger.error(
                    f"[Worker] Graph error for case={audit_case_id}: {exc}",
                    exc_info=True,
                )
                await asyncio.to_thread(
                    _db_update_status,
                    audit_case_id,
                    schema_name,
                    "error",
                    str(exc),
                )

            finally:
                # Always release the lock, even if graph errored
                await _release_lock(redis, audit_case_id)
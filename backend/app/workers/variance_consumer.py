"""
Variance Consumer Worker
========================
Runs as an asyncio background task inside the FastAPI process (started via
asyncio.create_task() in main.py lifespan).

Lifecycle
─────────
1. On startup: create Redis consumer group if missing.
2. Loop: XREADGROUP with 2-second block → process one message at a time.
3. For each message:
   a. Update AuditCase.status = "processing" in DB.
   b. Build initial LangGraph state from DB values (file paths already stored).
   c. Run build_wc_audit_graph().astream() — your graph is UNTOUCHED.
   d. Stream node outputs back into the DB incrementally (agent_logs, partial state).
   e. On graph completion → status = "completed" / "error".
   f. XACK the message so Redis doesn't re-deliver.
4. If any exception → log error, update DB status = "error", do NOT XACK
   (Redis will re-deliver after the PEL timeout for automatic retry).

HITL integration
────────────────
The hitl_checkpoint node in wc_graph_builder.py calls
  app.services.hitl_store.create_event(audit_case_id)
then awaits the event.  The /hitl-decision API endpoint calls
  app.services.hitl_store.resolve(...)
which sets the event from inside the same event loop — the graph resumes.
No inter-process signalling needed.

File: backend/app/workers/variance_consumer.py
"""

import asyncio
import logging
import os
import socket
from datetime import datetime
from typing import Optional

import redis.asyncio as aioredis
from sqlalchemy import text

from app.core.database import SessionLocal
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

# Unique per worker instance — safe even when running multiple uvicorn workers
# because each process gets its own hostname + PID combination.
CONSUMER_NAME = f"worker-{socket.gethostname()}-{os.getpid()}"


# ─────────────────────────────────────────────────────────────────────────────
# DB helpers (sync — run in thread pool via asyncio.to_thread)
# ─────────────────────────────────────────────────────────────────────────────

def _db_get_case(audit_case_id: int, schema: str) -> Optional[AuditCase]:
    """Load the AuditCase ORM row for the given case id inside the tenant schema."""
    db = SessionLocal()
    try:
        db.execute(text(f'SET search_path TO "{schema}", public'))
        return db.query(AuditCase).filter(AuditCase.id == audit_case_id).first()
    finally:
        db.close()


def _db_update_status(audit_case_id: int, schema: str, status: str, error_msg: str = "") -> None:
    """Update AuditCase.status (and optionally store an error note)."""
    db = SessionLocal()
    try:
        db.execute(text(f'SET search_path TO "{schema}", public'))
        case = db.query(AuditCase).filter(AuditCase.id == audit_case_id).first()
        if case:
            case.status = status
            if status == "completed":
                case.completed_at = datetime.utcnow()
            if error_msg:
                # store error in auditor_notes as a fallback field
                case.auditor_notes = error_msg
            case.updated_at = datetime.utcnow()
            db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(f"[Worker] _db_update_status failed: {exc}")
    finally:
        db.close()



def _db_flush_intermediate_state(audit_case_id: int, schema: str, state: dict) -> None:
    """
    Write the intermediate variance / risk data from LangGraph state into the
    wc_audit_cases row BEFORE the graph pauses at hitl_checkpoint.

    Why this is needed
    ──────────────────
    The graph order is:
        calculate_variance → assess_risk → hitl_checkpoint → (await) → persist_to_database

    `persist_to_database` only runs AFTER HITL approval.  Until then the
    variance numbers exist only in the LangGraph in-memory state.
    The /status endpoint reads from the DB, so the Audit Results panel
    shows all zeros while the case is paused for HITL review.

    This function writes the key computed fields to wc_audit_cases immediately
    when hitl_checkpoint fires, so the frontend can display real numbers
    while the auditor is reviewing.
    """
    from sqlalchemy.orm.attributes import flag_modified

    db = SessionLocal()
    try:
        db.execute(text(f'SET search_path TO "{schema}", public'))
        case = db.query(AuditCase).filter(AuditCase.id == audit_case_id).first()
        if not case:
            return

        # ── Overall variance totals ───────────────────────────────────
        overall = state.get("overall_variance") or {}
        case.total_earned_exposure = overall.get("earned_exposure", 0) or 0
        case.total_earned_premium  = overall.get("earned_premium",  0) or 0
        case.total_est_exposure    = overall.get("est_exposure",    0) or 0
        case.total_est_ytd_premium = overall.get("est_ytd_premium", 0) or 0
        case.total_variance        = overall.get("variance",        0) or 0
        case.total_variance_pct    = overall.get("variance_pct",    0) or 0

        # ── Risk / recommendation ─────────────────────────────────────
        if state.get("risk_level"):
            case.risk_level     = state["risk_level"]
        if state.get("recommendation"):
            case.recommendation = state["recommendation"]
        if state.get("hitl_required") is not None:
            case.hitl_required  = bool(state["hitl_required"])

        # ── Submission stats ──────────────────────────────────────────
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
        logger.error(f"[Worker] _db_flush_intermediate_state failed case={audit_case_id}: {exc}")
    finally:
        db.close()


def _db_append_agent_log(audit_case_id: int, schema: str, log_entry: dict) -> None:
    """
    Append one agent log entry to wc_audit_reports.report_json.

    CRITICAL FIX — SQLAlchemy JSON mutation bug:
    SQLAlchemy tracks JSON columns by reference not deep copy.  If you call
    .get("agent_logs") you get back the SAME list object that lives inside
    report.report_json.  Mutating it with .append() then reassigning the
    same list back looks like "no change" to SQLAlchemy — it skips the UPDATE.

    Fixes applied:
    1. list()           — copy the list before appending, breaks shared reference
    2. flag_modified()  — force SQLAlchemy to emit the UPDATE regardless
    3. with_for_update()— row lock prevents concurrent races
    4. Exception logged — was silently swallowed before
    """
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
            # COPY the list — never mutate the original reference
            logs = list(existing.get("agent_logs", []))
            logs.append(log_entry)
            report.report_json = {"agent_logs": logs}
            # Force SQLAlchemy to include the JSON column in the UPDATE
            flag_modified(report, "report_json")

        db.commit()
        logger.debug(
            f"[Worker] log saved: case={audit_case_id} agent={log_entry.get('agent')}"
        )
    except Exception as exc:
        db.rollback()
        logger.error(f"[Worker] _db_append_agent_log failed case={audit_case_id}: {exc}")
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# Core graph runner
# ─────────────────────────────────────────────────────────────────────────────

async def _run_graph(
    audit_case_id:        int,
    policy_number:        str,
    tenant_id:            str,
    schema_name:          str,
    payroll_file_path:    str,
    policy_xml_path:      str,
    audit_meta_file_path: str,
) -> None:
    """
    Build the initial WCAuditState, run build_wc_audit_graph().astream(),
    and stream each node output back to the DB.

    Your wc_graph_builder.py and every agent node are completely untouched.
    """
    # Mark processing
    await asyncio.to_thread(
        _db_update_status, audit_case_id, schema_name, "processing"
    )

    initial_state = create_initial_state(
        audit_case_id        = audit_case_id,
        policy_number        = policy_number,
        payroll_file_path    = payroll_file_path,
        policy_xml_path      = policy_xml_path,
        audit_meta_file_path = audit_meta_file_path,
        tenant_id            = tenant_id,
    )

    graph = build_wc_audit_graph()

    last_state: dict = {}
    current_status   = "processing"

    # Map LangGraph node_name → frontend-compatible agent key.
    # Writing node_name directly guarantees the key is always correct,
    # regardless of what the node itself puts in its agent_logs dict.
    _NODE_TO_AGENT_KEY = {
        "parse_payroll_excel":  "ingestion_excel",
        "parse_policy_xml":     "ingestion_xml",
        "parse_audit_metadata": "ingestion_audit_meta",
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

            # ── Write ONE reliable log entry per node ────────────────
            # Use node_name (always known) as the agent key so the frontend
            # pipeline steps light up correctly. This avoids relying on
            # whatever key the node itself emits in its agent_logs dict.
            agent_key = _NODE_TO_AGENT_KEY.get(node_name, node_name)
            # Determine if the node reported an error
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

            # ── Merge node output into running state snapshot ────────
            # MUST happen before HITL flush so last_state has variance data
            last_state.update(node_output)

            # ── Detect HITL pause — flush intermediate state first ────
            if node_name == "hitl_checkpoint":
                current_status = "review"
                # Flush variance/risk data into the DB so the Audit Results
                # panel shows real numbers while the auditor is reviewing.
                # (persist_to_database only runs AFTER HITL approval)
                await asyncio.to_thread(
                    _db_flush_intermediate_state, audit_case_id, schema_name, last_state
                )
                await asyncio.to_thread(
                    _db_update_status, audit_case_id, schema_name, "review"
                )
                logger.info(
                    f"[Worker] Case {audit_case_id}: intermediate state flushed, "
                    "graph paused at hitl_checkpoint"
                )

    # ── Graph fully finished ──────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────────────────
# Main consumer loop  (started as asyncio.create_task in main.py)
# ─────────────────────────────────────────────────────────────────────────────

async def run_variance_worker(redis: aioredis.Redis) -> None:
    """
    Infinite consumer loop.  Meant to run as a background asyncio task alongside
    the FastAPI application.

    Error behaviour
    ───────────────
    • Graph execution errors are caught per-message, logged, written to DB as
      status="error", and the message is NOT acknowledged so Redis will re-deliver
      it after the PEL claim timeout (default 1 hour).
    • Connection / infrastructure errors are retried with exponential back-off.
    """
    logger.info(f"[Worker] Starting — consumer_name={CONSUMER_NAME}")

    # Bootstrap consumer group (idempotent)
    await ensure_consumer_group(redis)

    consecutive_errors = 0

    while True:
        try:
            messages = await read_next(redis, CONSUMER_NAME, block_ms=2000, count=1)
            consecutive_errors = 0  # reset on any successful read (even empty)
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
            # Normal timeout — yield and loop
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

            logger.info(
                f"[Worker] Picked up msg_id={msg_id}  "
                f"case={audit_case_id}  policy={policy_number}  tenant={tenant_id}"
            )

            try:
                await _run_graph(
                    audit_case_id        = audit_case_id,
                    policy_number        = policy_number,
                    tenant_id            = tenant_id,
                    schema_name          = schema_name,
                    payroll_file_path    = payroll_file_path,
                    policy_xml_path      = policy_xml_path,
                    audit_meta_file_path = audit_meta_file_path,
                )
                # ── ACK only on success ────────────────────────────────
                await ack(redis, msg_id)
                logger.info(f"[Worker] ACKed msg_id={msg_id}  case={audit_case_id}")

            except asyncio.CancelledError:
                # Propagate cancellation — don't swallow it
                raise

            except Exception as exc:
                logger.error(
                    f"[Worker] Graph error for case={audit_case_id}: {exc}",
                    exc_info=True,
                )
                # Write error status to DB
                await asyncio.to_thread(
                    _db_update_status,
                    audit_case_id,
                    schema_name,
                    "error",
                    str(exc),
                )
                # Do NOT XACK → Redis auto-retries after PEL timeout
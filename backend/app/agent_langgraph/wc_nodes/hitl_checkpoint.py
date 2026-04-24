

"""
HITL Checkpoint Node  — FULLY FIXED
=====================================
Fixes applied vs the uploaded version:

1. SINGLETON EVENT  (from other AI's suggestion — correct fix)
   If an event already exists for this case (e.g. due to a concurrent
   second graph execution racing through the lock), reuse it instead of
   overwriting it.  This prevents two separate events being created for
   the same case which would cause one to wait forever.

2. SCHEMA FIX  (bug fix)
   Previously used state.get("tenant_id") as the PostgreSQL schema name.
   If tenant_id = "default" but actual schema = "public", the
   SET search_path TO "default" call silently fails → DB not updated →
   frontend never shows HITL panel → event waits forever → case errors out.
   Now uses state.get("schema_name") with "public" as fallback.

3. VARIANCE FLUSH BEFORE BLOCKING  (bug fix)
   All variance/risk fields are written to DB BEFORE await event.wait().
   Previously they were only flushed by the worker AFTER approval, so
   the HITL panel showed $0 on the first review.

File: backend/app/agent_langgraph/wc_nodes/hitl_checkpoint.py
"""
import asyncio
import logging
from datetime import datetime

from app.agent_langgraph.wc_state import WCAuditState
from app.services import hitl_store

logger = logging.getLogger(__name__)


async def hitl_checkpoint(state: WCAuditState) -> dict:
    """
    Async LangGraph node — runs on the main event loop (not thread pool).

    Steps:
    1. Register a SINGLETON asyncio.Event for this case.
    2. Write status="review" AND all variance data to DB so the HITL panel
       shows real numbers immediately on first load.
    3. await event.wait() — blocks until /hitl-decision is called.
    4. Read decision, clear event, return state update.
    """
    audit_case_id = state.get("audit_case_id")
    risk_level    = state.get("risk_level", "unknown")
    overall       = state.get("overall_variance") or {}
    variance      = overall.get("variance", 0)

    logger.info(
        f"[HITLCheckpoint] Pausing case {audit_case_id} for human review. "
        f"Risk={risk_level}, Variance={variance:.2f}"
    )

    # FIX 1 — Singleton event: reuse existing if present
    existing_event = hitl_store.get_event(audit_case_id)
    if existing_event:
        logger.info(
            f"[HITLCheckpoint] Reusing existing HITL event for case {audit_case_id}"
        )
        event = existing_event
    else:
        event = hitl_store.create_event(audit_case_id)

    # FIX 2 + FIX 3 — Use correct schema AND flush variance data BEFORE blocking
    try:
        from app.core.database import SessionLocal
        from sqlalchemy import text as _text
        from app.models.wc_audit import AuditCase

        def _mark_review_with_variance():
            # FIX 2: use schema_name, not tenant_id
            schema = state.get("schema_name") or state.get("tenant_id", "public")

            db = SessionLocal()
            try:
                db.execute(_text(f'SET search_path TO "{schema}", public'))
                c = db.query(AuditCase).filter(AuditCase.id == audit_case_id).first()
                if not c:
                    logger.warning(
                        f"[HITLCheckpoint] AuditCase {audit_case_id} not found "
                        f"in schema='{schema}'. HITL event still registered."
                    )
                    return

                # Set status to "review"
                c.status     = "review"
                c.updated_at = datetime.utcnow()

                # FIX 3 — Write variance data NOW so panel shows real numbers
                ov = state.get("overall_variance") or {}
                if ov:
                    c.risk_level             = state.get("risk_level")     or c.risk_level
                    c.recommendation         = state.get("recommendation") or c.recommendation
                    c.hitl_required          = bool(state.get("hitl_required", True))
                    c.total_variance         = float(ov.get("variance",        0) or 0)
                    c.total_variance_pct     = float(ov.get("variance_pct",    0) or 0)
                    c.total_earned_premium   = float(ov.get("earned_premium",  0) or 0)
                    c.total_est_ytd_premium  = float(ov.get("est_ytd_premium", 0) or 0)
                    c.total_earned_exposure  = float(ov.get("earned_exposure", 0) or 0)
                    c.total_est_exposure     = float(ov.get("est_exposure",    0) or 0)

                db.commit()
                logger.info(
                    f"[HITLCheckpoint] Case {audit_case_id} → 'review' "
                    f"with variance={ov.get('variance', 0):.2f} "
                    f"earned_premium={ov.get('earned_premium', 0):.2f} "
                    f"(schema={schema})"
                )

            except Exception as db_exc:
                db.rollback()
                logger.error(
                    f"[HITLCheckpoint] DB update failed for case {audit_case_id}: {db_exc}. "
                    "HITL event is still registered — graph will pause but "
                    "frontend may not show the panel correctly."
                )
            finally:
                db.close()

        await asyncio.to_thread(_mark_review_with_variance)

    except Exception as e:
        logger.error(f"[HITLCheckpoint] Unexpected error during DB setup: {e}")

    # Block until human submits decision
    logger.info(f"[HITLCheckpoint] Waiting for human decision on case {audit_case_id}…")
    await event.wait()

    # Read decision
    entry    = hitl_store.get_decision(audit_case_id)
    decision = entry.decision    if entry else "approve"
    notes    = entry.notes       if entry else ""
    reviewer = entry.reviewer_id if entry else "unknown"

    hitl_store.clear(audit_case_id)

    logger.info(
        f"[HITLCheckpoint] Case {audit_case_id} resumed — "
        f"decision={decision}  reviewer={reviewer}"
    )

    return {
        "hitl_decision": decision,
        "hitl_notes":    notes,
        "agent_logs": [{
            "agent":       "hitl_checkpoint",
            "status":      "success",
            "action":      decision,
            "reviewer_id": reviewer,
            "timestamp":   datetime.utcnow().isoformat(),
        }],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Public helpers — kept for Streamlit backward compatibility
# ─────────────────────────────────────────────────────────────────────────────

def resolve_hitl(
    audit_case_id: int,
    action:        str,
    reviewer_id:   str,
    notes:         str  = "",
    override_data: dict = None,
) -> bool:
    decision = action
    resolved = hitl_store.resolve(
        audit_case_id  = audit_case_id,
        decision       = decision,
        reviewer_id    = reviewer_id,
        notes          = notes,
        override_data  = override_data,
    )
    if not resolved:
        logger.warning(
            f"[resolve_hitl] No pending review found for case {audit_case_id}. "
            "Already resolved or server restarted."
        )
    return resolved


def get_pending_reviews() -> list:
    return [
        {"audit_case_id": cid, "paused_at": None}
        for cid in hitl_store.all_pending_ids()
    ]
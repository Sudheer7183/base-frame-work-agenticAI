"""
HITL Checkpoint Node  (async-native, v5-compatible)
====================================================
Pauses the LangGraph workflow for human review on high-risk audits.

Changes vs previous version
────────────────────────────
• Removed dead import of mark_hitl_pending (function no longer exists in v5 API)
• Single event store — uses only app.services.hitl_store (no _PENDING_REVIEWS dict)
• After event.wait() resumes, reads decision from hitl_store (not a dead local dict)
• resolve_hitl() / get_pending_reviews() kept for Streamlit backward compat —
  they now delegate to hitl_store so there is only one source of truth

File: backend/app/agent_langgraph/wc_nodes/hitl_checkpoint.py
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict

from app.agent_langgraph.wc_state import WCAuditState
from app.services import hitl_store

logger = logging.getLogger(__name__)


async def hitl_checkpoint(state: WCAuditState) -> dict:
    """
    Async LangGraph node — runs on the main event loop (not thread pool).

    Steps:
    1. Register an asyncio.Event for this case via hitl_store.
    2. Update AuditCase status → "review" in DB so the frontend sees it
       on the very next /status poll.
    3. await event.wait() — suspends HERE until the /hitl-decision API
       endpoint calls hitl_store.resolve(), which sets the event.
    4. Read the decision back from hitl_store and return a partial state dict.
    """
    audit_case_id = state.get("audit_case_id")
    risk_level    = state.get("risk_level", "unknown")
    overall       = state.get("overall_variance") or {}
    variance      = overall.get("variance", 0)

    logger.info(
        f"[HITLCheckpoint] Pausing audit case {audit_case_id} for human review. "
        f"Risk={risk_level}, Variance={variance:.2f}"
    )

    # ── Register event — MUST happen before any awaits ────────────────
    event = hitl_store.create_event(audit_case_id)

    # ── Update DB status to "review" so /status shows hitl_pending ────
    # Use asyncio.to_thread so the sync DB call doesn't block the loop
    try:
        import asyncio as _asyncio
        from app.core.database import SessionLocal
        from sqlalchemy import text as _text
        from app.models.wc_audit import AuditCase

        def _mark_review():
            schema = state.get("tenant_id", "public")
            db = SessionLocal()
            try:
                db.execute(_text(f'SET search_path TO "{schema}", public'))
                c = db.query(AuditCase).filter(AuditCase.id == audit_case_id).first()
                if c:
                    c.status     = "review"
                    c.updated_at = datetime.utcnow()
                    db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()

        await _asyncio.to_thread(_mark_review)
    except Exception as e:
        logger.warning(f"[HITLCheckpoint] DB status update failed (non-fatal): {e}")

    # ── Block until the human submits a decision ──────────────────────
    logger.info(f"[HITLCheckpoint] Waiting for human decision on case {audit_case_id}…")
    await event.wait()

    # ── Read decision from hitl_store (set by /hitl-decision endpoint) ─
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
# Both now delegate to hitl_store so there is only ONE event registry.
# ─────────────────────────────────────────────────────────────────────────────

def resolve_hitl(
    audit_case_id: int,
    action:        str,
    reviewer_id:   str,
    notes:         str  = "",
    override_data: dict = None,
) -> bool:
    """
    Signal the blocked hitl_checkpoint to resume the graph.
    Delegates to hitl_store.resolve().
    Returns True if an active event was found and set, False otherwise.
    """
    decision = action  # "approve" / "reject" / "override"
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
    """Return list of case IDs currently awaiting human review."""
    return [
        {"audit_case_id": cid, "paused_at": None}
        for cid in hitl_store.all_pending_ids()
    ]
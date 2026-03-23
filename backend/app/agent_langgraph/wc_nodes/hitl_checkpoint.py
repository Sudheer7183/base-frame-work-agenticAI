"""
HITL Checkpoint Node  (async-native)
=====================================
Pauses the LangGraph workflow for human review on high-risk audits.

FIX: hitl_checkpoint is now declared as `async def` directly.
     The previous version wrapped it in a sync function that called
     asyncio.get_event_loop(), which crashed with:
       RuntimeError: There is no current event loop in thread 'ThreadPoolExecutor-0_0'
     because LangGraph runs sync nodes in a thread pool executor.

     Declaring the node as `async def` means LangGraph awaits it on the
     main event loop — no thread pool, no missing event loop.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict

from app.agent_langgraph.wc_state import WCAuditState

logger = logging.getLogger(__name__)

# ── In-process HITL event store ───────────────────────────────────────────────
_PENDING_REVIEWS: Dict[int, dict] = {}


async def hitl_checkpoint(state: WCAuditState) -> dict:
    """
    Async LangGraph node — runs on the main event loop (not thread pool).

    Steps:
    1.  Register an asyncio.Event for this case.
    2.  Call mark_hitl_pending() → registry immediately shows "hitl_pending"
        so the frontend sees it on the very next /status poll.
    3.  await event.wait() — suspends HERE until resolve_hitl() is called.
    4.  Return partial state dict (only the keys this node sets).
    """
    audit_case_id = state.get("audit_case_id")
    risk_level    = state.get("risk_level", "unknown")
    overall       = state.get("overall_variance") or {}
    variance      = overall.get("variance", 0)

    logger.info(
        f"[HITLCheckpoint] Pausing audit case {audit_case_id} for human review. "
        f"Risk={risk_level}, Variance={variance:.2f}"
    )

    # Register event BEFORE any awaits so resolve_hitl() can always find it
    event = asyncio.Event()
    _PENDING_REVIEWS[audit_case_id] = {
        "event":     event,
        "action":    None,
        "notes":     "",
        "paused_at": datetime.utcnow().isoformat(),
    }

    # ── Update registry to "hitl_pending" BEFORE blocking ─────────────────
    try:
        from app.api.v1.wc_aduit_api import mark_hitl_pending
        mark_hitl_pending(audit_case_id, dict(state))
    except (ImportError, Exception) as e:
        logger.warning(f"[HITLCheckpoint] mark_hitl_pending failed: {e}")

    # ── Block until the human makes a decision ─────────────────────────────
    logger.info(f"[HITLCheckpoint] Waiting for human decision on case {audit_case_id}…")
    await event.wait()

    review = _PENDING_REVIEWS.pop(audit_case_id, {})
    action = review.get("action", "approve")
    notes  = review.get("notes",  "")

    logger.info(
        f"[HITLCheckpoint] Case {audit_case_id} resumed — action={action}"
    )

    return {
        "hitl_decision": action,
        "hitl_notes":    notes,
        "agent_logs": [{
            "agent":     "hitl_checkpoint",
            "status":    "success",
            "action":    action,
            "timestamp": datetime.utcnow().isoformat(),
        }],
    }


# ─────────────────────────────────────────────
# Public helpers used by wc_aduit_api.py
# ─────────────────────────────────────────────

def resolve_hitl(
    audit_case_id: int,
    action:        str,
    reviewer_id:   str,
    notes:         str  = "",
    override_data: dict = None,
) -> bool:
    """
    Signal the blocked hitl_checkpoint to resume the graph.
    Returns True if an active event was found and set.
    """
    review = _PENDING_REVIEWS.get(audit_case_id)
    if not review:
        logger.warning(
            f"[resolve_hitl] No pending review found for case {audit_case_id}. "
            "Already resolved or server restarted."
        )
        return False

    review["action"]      = action
    review["notes"]       = notes
    review["reviewer_id"] = reviewer_id
    review["resolved_at"] = datetime.utcnow().isoformat()
    review["event"].set()

    logger.info(f"[resolve_hitl] Case {audit_case_id} — action={action} by {reviewer_id}")
    return True


def get_pending_reviews() -> list:
    """Return list of case IDs currently awaiting human review."""
    return [
        {"audit_case_id": cid, "paused_at": r.get("paused_at")}
        for cid, r in _PENDING_REVIEWS.items()
    ]
"""
HITL Event Store  —  shared asyncio events for human-in-the-loop decisions
==========================================================================
Since the variance_consumer worker runs as an asyncio.create_task() inside
the SAME FastAPI process and event loop, we can share asyncio.Events across
the worker coroutine and the API endpoint handlers without any inter-process
communication.

Pattern
───────
Worker (hitl_checkpoint node):
    event = hitl_store.create_event(audit_case_id)
    await event.wait()                    # blocks the graph here
    decision = hitl_store.get_decision(audit_case_id)
    hitl_store.clear(audit_case_id)

API endpoint (/hitl-decision):
    hitl_store.resolve(audit_case_id, decision="approve", reviewer="alice", notes="OK")
    # sets the event → unblocks the graph

File: backend/app/services/hitl_store.py
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict

logger = logging.getLogger(__name__)


@dataclass
class HITLEntry:
    event:       asyncio.Event
    decision:    Optional[str]    = None   # "approve" | "reject" | "override"
    reviewer_id: Optional[str]    = None
    notes:       Optional[str]    = None
    override_data: Optional[dict] = None
    resolved_at: Optional[str]    = None


# Module-level registry — lives for the lifetime of the FastAPI process
_HITL_REGISTRY: Dict[int, HITLEntry] = {}


def create_event(audit_case_id: int) -> asyncio.Event:
    """
    Create and register an asyncio.Event for a new HITL pause.
    Called by the hitl_checkpoint LangGraph node before it awaits.
    """
    event = asyncio.Event()
    _HITL_REGISTRY[audit_case_id] = HITLEntry(event=event)
    logger.info(f"[HITLStore] Event created for case {audit_case_id}")
    return event


def resolve(
    audit_case_id:  int,
    decision:       str,
    reviewer_id:    str,
    notes:          str       = "",
    override_data:  Optional[dict] = None,
) -> bool:
    """
    Called by the /hitl-decision API endpoint.
    Sets the event so the waiting graph resumes.
    Returns True if the event was found, False if case is not waiting.
    """
    entry = _HITL_REGISTRY.get(audit_case_id)
    if entry is None:
        logger.warning(f"[HITLStore] No pending HITL event for case {audit_case_id}")
        return False

    entry.decision      = decision
    entry.reviewer_id   = reviewer_id
    entry.notes         = notes
    entry.override_data = override_data
    entry.resolved_at   = datetime.utcnow().isoformat()

    entry.event.set()   # ← unblocks graph.astream() in the worker
    logger.info(
        f"[HITLStore] Resolved case {audit_case_id}: "
        f"decision={decision}  reviewer={reviewer_id}"
    )
    return True


def get_decision(audit_case_id: int) -> Optional[HITLEntry]:
    """Return the full HITL entry after the event has been resolved."""
    return _HITL_REGISTRY.get(audit_case_id)


def clear(audit_case_id: int) -> None:
    """Remove the entry after the graph has consumed the decision."""
    _HITL_REGISTRY.pop(audit_case_id, None)
    logger.debug(f"[HITLStore] Entry cleared for case {audit_case_id}")


def is_pending(audit_case_id: int) -> bool:
    """Return True if this case currently has a live HITL event awaiting resolution."""
    entry = _HITL_REGISTRY.get(audit_case_id)
    return entry is not None and not entry.event.is_set()


def all_pending_ids() -> list[int]:
    """Return all case IDs currently blocked at HITL."""
    return [cid for cid, e in _HITL_REGISTRY.items() if not e.event.is_set()]


def get_event(audit_case_id: int):
    """
    Return the asyncio.Event for a pending HITL entry, or None if not found.
    Used by hitl_checkpoint to reuse an existing event instead of creating
    a duplicate — prevents two separate events for the same case when a
    second execution races through (should be blocked by the lock, but
    this is a final safety net).
    """
    entry = _HITL_REGISTRY.get(audit_case_id)
    if entry is None:
        return None
    return entry.event
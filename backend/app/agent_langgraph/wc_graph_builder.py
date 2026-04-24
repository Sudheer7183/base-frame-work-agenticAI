


"""
Workers' Compensation Audit – LangGraph Graph Builder  — FULLY FIXED
======================================================================
Fix applied vs the uploaded version:

UNCONDITIONAL parse_policy_xml / parse_audit_metadata EDGES REMOVED

The uploaded file still has:
    workflow.add_edge(START, "parse_policy_xml")      ← unconditional
    workflow.add_edge(START, "parse_audit_metadata")  ← unconditional

These run even when data_source == "api", with empty file paths.
They complete before api_ingestion_node (no HTTP round-trips), write
{xml_records: [], policy_config: {}} into state, and overwrite the
good data from api_ingestion_node.  This causes $0 variance calculations.

FIX: Both edges are now conditional — they route to no-op nodes that
return {} (no state change) when data_source == "api".

Workflow DAG (API mode):
  START → api_ingestion  ──────────────────────┐
  START → noop_xml       (returns {})  ────────┤ fan-in satisfies
  START → noop_meta      (returns {})  ────────┘ downstream agents
                              │
                    officer_agent (waits for api_ingestion + noop_xml)
                    class_code_agent (waits for api_ingestion + noop_xml)
                    frequency_agent (waits for api_ingestion + noop_xml + noop_meta)
                              │
                        calculate_variance → assess_risk → ...

Workflow DAG (upload mode):
  START → parse_payroll_excel ──────────────────┐
  START → parse_policy_xml    ─────────────────┤ fan-in (unchanged)
  START → parse_audit_metadata ────────────────┘
                              │
                    officer_agent, class_code_agent, frequency_agent
                              │ ...

File: backend/app/agent_langgraph/wc_graph_builder.py
"""
import logging
from typing import Literal

from langgraph.graph import StateGraph, START, END

from app.agent_langgraph.wc_state import WCAuditState
from app.agent_langgraph.ingestion_agent import (
    parse_payroll_excel,
    parse_policy_xml,
    parse_audit_metadata,
)
from app.agent_langgraph.specialist_agents import (
    officer_agent,
    class_code_agent,
    frequency_agent,
)
from app.agent_langgraph.premium_agent import (
    calculate_variance,
    assess_risk,
)
from app.agent_langgraph.explanation_agent import explanation_agent
from app.agent_langgraph.wc_nodes.report_generator import generate_report
from app.agent_langgraph.wc_nodes.db_persistence import persist_to_database
from app.agent_langgraph.wc_nodes.hitl_checkpoint import hitl_checkpoint
from app.agent_langgraph.wc_nodes.api_ingestion_node import api_ingestion_node

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# No-op nodes for API mode (NEW)
# Return {} — no state change, but satisfy LangGraph's fan-in counter
# so downstream agents get the right number of parent completions.
# ─────────────────────────────────────────────────────────────────────────────

def _noop_xml(state: WCAuditState) -> dict:
    """Stand-in for parse_policy_xml when data_source == 'api'."""
    logger.debug("[noop_xml] API mode — skipping file-based XML parse")
    return {}


def _noop_meta(state: WCAuditState) -> dict:
    """Stand-in for parse_audit_metadata when data_source == 'api'."""
    logger.debug("[noop_meta] API mode — skipping file-based metadata parse")
    return {}


# ─────────────────────────────────────────────────────────────────────────────
# Routing functions
# ─────────────────────────────────────────────────────────────────────────────

def route_payroll_ingestion(
    state: WCAuditState,
) -> Literal["api_ingestion", "parse_payroll_excel"]:
    if state.get("data_source") == "api":
        return "api_ingestion"
    return "parse_payroll_excel"


def route_xml_ingestion(
    state: WCAuditState,
) -> Literal["parse_policy_xml", "noop_xml"]:
    """Route to noop in API mode to avoid overwriting api_ingestion data."""
    if state.get("data_source") == "api":
        return "noop_xml"
    return "parse_policy_xml"


def route_meta_ingestion(
    state: WCAuditState,
) -> Literal["parse_audit_metadata", "noop_meta"]:
    """Route to noop in API mode to avoid overwriting api_ingestion data."""
    if state.get("data_source") == "api":
        return "noop_meta"
    return "parse_audit_metadata"


def route_after_risk_assessment(
    state: WCAuditState,
) -> Literal["hitl_checkpoint", "explanation_agent"]:
    """
    Route based on the ``hitl_required`` flag set by ``assess_risk``.

    When the administrator has disabled HITL globally
    (``hitl_globally_enabled=False`` in the initial state),
    ``assess_risk`` will have already forced ``hitl_required=False``
    before this router runs — so no special handling is needed here.
    The single flag is the contract between assess_risk and this router.
    """
    if state.get("hitl_required", False):
        logger.info("[Router] Routing to HITL checkpoint (high-risk audit).")
        return "hitl_checkpoint"
    logger.info("[Router] Routing directly to explanation agent (low/medium-risk or HITL disabled).")
    return "explanation_agent"


# ─────────────────────────────────────────────────────────────────────────────
# Graph builder
# ─────────────────────────────────────────────────────────────────────────────

def build_wc_audit_graph() -> StateGraph:
    """Compile and return the complete WC Audit LangGraph workflow."""
    workflow = StateGraph(WCAuditState)

    # ── Nodes ──────────────────────────────────────────────────────────
    # File-upload ingestion
    workflow.add_node("parse_payroll_excel",  parse_payroll_excel)
    workflow.add_node("parse_policy_xml",     parse_policy_xml)
    workflow.add_node("parse_audit_metadata", parse_audit_metadata)

    # API ingestion
    workflow.add_node("api_ingestion",        api_ingestion_node)

    # No-op skip nodes (used in API mode to satisfy fan-in without file reads)
    workflow.add_node("noop_xml",             _noop_xml)
    workflow.add_node("noop_meta",            _noop_meta)

    # Specialist agents
    workflow.add_node("officer_agent",        officer_agent)
    workflow.add_node("class_code_agent",     class_code_agent)
    workflow.add_node("frequency_agent",      frequency_agent)

    # Calculation
    workflow.add_node("calculate_variance",   calculate_variance)
    workflow.add_node("assess_risk",          assess_risk)

    # HITL
    workflow.add_node("hitl_checkpoint",      hitl_checkpoint)

    # Output
    workflow.add_node("explanation_agent",    explanation_agent)
    workflow.add_node("generate_report",      generate_report)
    workflow.add_node("persist_to_database",  persist_to_database)

    # ── Edges from START (all three are now conditional) ───────────────

    # Branch 1: payroll / full API data
    workflow.add_conditional_edges(
        START,
        route_payroll_ingestion,
        {
            "api_ingestion":       "api_ingestion",
            "parse_payroll_excel": "parse_payroll_excel",
        },
    )

    # Branch 2: policy XML — FIX: was unconditional, now routes to noop in API mode
    workflow.add_conditional_edges(
        START,
        route_xml_ingestion,
        {
            "parse_policy_xml": "parse_policy_xml",
            "noop_xml":         "noop_xml",
        },
    )

    # Branch 3: audit metadata — FIX: was unconditional, now routes to noop in API mode
    workflow.add_conditional_edges(
        START,
        route_meta_ingestion,
        {
            "parse_audit_metadata": "parse_audit_metadata",
            "noop_meta":            "noop_meta",
        },
    )

    # ── Ingestion → Specialist agents ─────────────────────────────────

    # Upload path
    workflow.add_edge("parse_payroll_excel",  "officer_agent")
    workflow.add_edge("parse_payroll_excel",  "class_code_agent")
    workflow.add_edge("parse_policy_xml",     "officer_agent")
    workflow.add_edge("parse_policy_xml",     "class_code_agent")
    workflow.add_edge("parse_policy_xml",     "frequency_agent")
    workflow.add_edge("parse_audit_metadata", "frequency_agent")

    # API path
    workflow.add_edge("api_ingestion",        "officer_agent")
    workflow.add_edge("api_ingestion",        "class_code_agent")
    workflow.add_edge("api_ingestion",        "frequency_agent")
    # Noop nodes must also feed into specialist agents to satisfy fan-in
    workflow.add_edge("noop_xml",             "officer_agent")
    workflow.add_edge("noop_xml",             "class_code_agent")
    workflow.add_edge("noop_xml",             "frequency_agent")
    workflow.add_edge("noop_meta",            "frequency_agent")

    # ── Specialist agents → variance ───────────────────────────────────
    workflow.add_edge("officer_agent",        "calculate_variance")
    workflow.add_edge("class_code_agent",     "calculate_variance")
    workflow.add_edge("frequency_agent",      "calculate_variance")

    # ── Variance → risk ────────────────────────────────────────────────
    workflow.add_edge("calculate_variance",   "assess_risk")

    # ── Conditional HITL routing ───────────────────────────────────────
    workflow.add_conditional_edges(
        "assess_risk",
        route_after_risk_assessment,
        {
            "hitl_checkpoint":   "hitl_checkpoint",
            "explanation_agent": "explanation_agent",
        },
    )

    # ── HITL → explanation ─────────────────────────────────────────────
    workflow.add_edge("hitl_checkpoint",      "explanation_agent")

    # ── Output chain ───────────────────────────────────────────────────
    workflow.add_edge("explanation_agent",    "generate_report")
    workflow.add_edge("generate_report",      "persist_to_database")
    workflow.add_edge("persist_to_database",  END)

    graph = workflow.compile()
    logger.info("[GraphBuilder] WC Audit LangGraph compiled successfully.")
    return graph


# ─────────────────────────────────────────────────────────────────────────────
# Convenience executor
# ─────────────────────────────────────────────────────────────────────────────

async def run_wc_audit(initial_state: WCAuditState) -> WCAuditState:
    graph  = build_wc_audit_graph()
    result = await graph.ainvoke(initial_state)
    logger.info(
        f"[WCAudit] Completed audit for policy {initial_state['policy_number']}. "
        f"Risk={result.get('risk_level')}, "
        f"Variance={result.get('overall_variance', {}).get('variance', 0):+.2f}"
    )
    return result
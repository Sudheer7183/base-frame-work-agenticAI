"""
Workers' Compensation Audit – LangGraph Graph Builder
Orchestrates the full audit workflow using a StateGraph.

Workflow DAG:
  START
    ├── parse_payroll_excel   ──┐
    ├── parse_audit_metadata  ──┤ (parallel ingestion)
    └── parse_policy_xml      ──┘
                                │
                            officer_agent
                            class_code_agent
                            frequency_agent
                                │
                            calculate_variance
                                │
                            assess_risk
                                │
                        [conditional edge]
                       /                   \
               hitl_checkpoint        explanation_agent
                    │                        │
              (human review)           generate_report
                    │                        │
              explanation_agent            END
                    │
              generate_report
                    │
                  END
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
from app.agent_langgraph.wc_nodes.db_persistence    import persist_to_database
from app.agent_langgraph.wc_nodes.hitl_checkpoint   import hitl_checkpoint
from app.agent_langgraph.wc_nodes.api_ingestion_node import (   # ← ADD
        api_ingestion_node,                                          # ← ADD
    )    

logger = logging.getLogger(__name__)



def route_ingestion(state):
    return "api_ingestion" if state.get("data_source") == "api" else "parse_payroll_excel"
 

# ─────────────────────────────────────────────
# Routing function
# ─────────────────────────────────────────────

def route_ingestion(state: WCAuditState) -> Literal["api_ingestion", "parse_payroll_excel"]:
        """Decide at START whether to fetch from API or read from uploaded files."""
        if state.get("data_source") == "api":
            return "api_ingestion"
        return "parse_payroll_excel"

def route_after_risk_assessment(
    state: WCAuditState,
) -> Literal["hitl_checkpoint", "explanation_agent"]:
    """Route to HITL review if required, otherwise proceed to narrative generation."""
    if state.get("hitl_required", False):
        logger.info("[Router] Routing to HITL checkpoint (high-risk audit).")
        return "hitl_checkpoint"
    logger.info("[Router] Routing directly to explanation agent (low/medium risk).")
    return "explanation_agent"


# ─────────────────────────────────────────────
# Graph builder
# ─────────────────────────────────────────────

def build_wc_audit_graph() -> StateGraph:
    """
    Compile and return the complete WC Audit LangGraph workflow.
    Usage:
        graph = build_wc_audit_graph()
        result = await graph.ainvoke(initial_state)
    """
    workflow = StateGraph(WCAuditState)

    # ── Nodes ──────────────────────────────────────────────────────────
    # Ingestion layer
    workflow.add_node("parse_payroll_excel",   parse_payroll_excel)
    workflow.add_node("parse_policy_xml",      parse_policy_xml)
    workflow.add_node("parse_audit_metadata",  parse_audit_metadata)
    workflow.add_node("api_ingestion",         api_ingestion_node)   # ← ADD

    # Specialist validation agents (run after ingestion completes)
    workflow.add_node("officer_agent",         officer_agent)
    workflow.add_node("class_code_agent",      class_code_agent)
    workflow.add_node("frequency_agent",       frequency_agent)

    # Deterministic calculation
    workflow.add_node("calculate_variance",    calculate_variance)
    workflow.add_node("assess_risk",           assess_risk)

    # HITL checkpoint (pauses for human review)
    workflow.add_node("hitl_checkpoint",       hitl_checkpoint)

    # AI narrative + report
    workflow.add_node("explanation_agent",     explanation_agent)
    workflow.add_node("generate_report",       generate_report)
    workflow.add_node("persist_to_database",   persist_to_database)

    # ── Edges ──────────────────────────────────────────────────────────

    # Parallel ingestion from START
    # workflow.add_edge(START, "parse_payroll_excel")
    # workflow.add_edge(START, "parse_policy_xml")
    # workflow.add_edge(START, "parse_audit_metadata")

    workflow.add_conditional_edges(
        START,
        route_ingestion,
        {
            "api_ingestion":      "api_ingestion",
            "parse_payroll_excel": "parse_payroll_excel",
        }
    )
    # Upload path still fans out in parallel (unchanged)
    workflow.add_edge(START, "parse_policy_xml")
    workflow.add_edge(START, "parse_audit_metadata")

    # After all three ingestion nodes → specialist agents
    # (LangGraph waits for all parents before executing child)
    workflow.add_edge("parse_payroll_excel",  "officer_agent")
    workflow.add_edge("parse_payroll_excel",  "class_code_agent")
    workflow.add_edge("parse_policy_xml",     "officer_agent")
    workflow.add_edge("parse_policy_xml",     "class_code_agent")
    workflow.add_edge("parse_policy_xml",     "frequency_agent")
    workflow.add_edge("parse_audit_metadata", "frequency_agent")
    workflow.add_edge("api_ingestion",        "officer_agent")        # ← ADD
    workflow.add_edge("api_ingestion",        "class_code_agent")     # ← ADD
    workflow.add_edge("api_ingestion",        "frequency_agent")      # ← ADD

    # Specialist agents → variance calculation
    workflow.add_edge("officer_agent",        "calculate_variance")
    workflow.add_edge("class_code_agent",     "calculate_variance")
    workflow.add_edge("frequency_agent",      "calculate_variance")

    # Variance → risk assessment
    workflow.add_edge("calculate_variance",   "assess_risk")

    # Conditional routing based on risk level
    workflow.add_conditional_edges(
        "assess_risk",
        route_after_risk_assessment,
        {
            "hitl_checkpoint":  "hitl_checkpoint",
            "explanation_agent": "explanation_agent",
        },
    )

    # After HITL approval → proceed to explanation
    workflow.add_edge("hitl_checkpoint",      "explanation_agent")

    # Explanation → Report → Persist → END
    workflow.add_edge("explanation_agent",    "generate_report")
    workflow.add_edge("generate_report",      "persist_to_database")
    workflow.add_edge("persist_to_database",  END)

    graph = workflow.compile()
    logger.info("[GraphBuilder] WC Audit LangGraph compiled successfully.")
    return graph


# ─────────────────────────────────────────────
# Convenience executor
# ─────────────────────────────────────────────

async def run_wc_audit(initial_state: WCAuditState) -> WCAuditState:
    """
    Execute the full WC Audit workflow and return the final state.

    Args:
        initial_state: Created via state.create_initial_state(...)

    Returns:
        Final WCAuditState with all results populated.
    """
    graph  = build_wc_audit_graph()
    result = await graph.ainvoke(initial_state)
    logger.info(
        f"[WCAudit] Completed audit for policy {initial_state['policy_number']}. "
        f"Risk={result.get('risk_level')}, "
        f"Variance={result.get('overall_variance', {}).get('variance', 0):+.2f}"
    )
    return result

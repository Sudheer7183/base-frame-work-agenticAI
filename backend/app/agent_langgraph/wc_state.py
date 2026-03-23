"""
Workers' Compensation Audit - LangGraph State
Defines the shared state object passed between all nodes in the audit graph.
"""
from typing import TypedDict, List, Dict, Optional, Any
from typing import Annotated
from operator import add

class WCAuditState(TypedDict):
    """
    Central state object for the Workers' Compensation Audit LangGraph workflow.
    All agents read from and write to this shared state.
    """

    # ── Input parameters ──────────────────────────────────────────────
    audit_case_id:          int
    policy_number:          str
    payroll_file_path:      str          # Path to insured Excel payroll file
    policy_xml_path:        str          # Path to policy XML / carrier config
    audit_meta_file_path:   str          # Path to audit metadata Excel (check dates)
    tenant_id:              str

    # ── Ingested raw records ──────────────────────────────────────────
    excel_records:          List[Dict]   # Payroll detail rows from Excel
    xml_records:            List[Dict]   # Policy class code rows from XML
    audit_xl_records:       List[Dict]   # Audit metadata (check dates, submission count)

    # ── Normalization outputs ─────────────────────────────────────────
    normalized_payroll:     List[Dict]
    policy_config:          Dict
    payroll_frequency:      str
    expected_submissions:   float
    actual_submissions:     float
    submitted_count:        int
    first_check_date:       str
    last_check_date:        str

    # ── Variance calculation results ──────────────────────────────────
    class_code_variance:    List[Dict]   # Per (policy, state, class_code) variance
    overall_variance:       Dict         # Totals summary

    # ── Specialist agent findings ─────────────────────────────────────
    officer_findings:       List[Dict]
    class_code_findings:    List[Dict]
    frequency_findings:     List[Dict]

    # ── Risk & recommendation ─────────────────────────────────────────
    risk_level:             str          # low / medium / high
    hitl_required:          bool
    recommendation:         str          # refund / additional_premium / clarification / no_action

    # ── AI-generated narrative ────────────────────────────────────────
    ai_narrative:           str

    # ── Report output ─────────────────────────────────────────────────
    report_data:            Dict
    report_file_path:       str

    # ── Workflow control ──────────────────────────────────────────────
    current_stage:          str
    errors:                 List[str]
    warnings:               List[str]
    agent_logs: Annotated[List[dict], add]


def create_initial_state(
    audit_case_id: int,
    policy_number: str,
    payroll_file_path: str,
    policy_xml_path: str,
    audit_meta_file_path: str,
    tenant_id: str = "default"
) -> WCAuditState:
    """Create a fresh state for a new audit execution."""
    return WCAuditState(
        audit_case_id=audit_case_id,
        policy_number=policy_number,
        payroll_file_path=payroll_file_path,
        policy_xml_path=policy_xml_path,
        audit_meta_file_path=audit_meta_file_path,
        tenant_id=tenant_id,

        excel_records=[],
        xml_records=[],
        audit_xl_records=[],

        normalized_payroll=[],
        policy_config={},
        payroll_frequency="1W",
        expected_submissions=0.0,
        actual_submissions=0.0,
        submitted_count=0,
        first_check_date="",
        last_check_date="",

        class_code_variance=[],
        overall_variance={},

        officer_findings=[],
        class_code_findings=[],
        frequency_findings=[],

        risk_level="low",
        hitl_required=False,
        recommendation="no_action",

        ai_narrative="",

        report_data={},
        report_file_path="",

        current_stage="init",
        errors=[],
        warnings=[],
        agent_logs=[],
    )

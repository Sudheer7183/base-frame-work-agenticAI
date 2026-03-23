"""
Specialist Validation Agents
─────────────────────────────
• OfficerAgent      – Detects officer payroll misclassification
• ClassCodeAgent    – Validates class code assignment vs policy
• FrequencyAgent    – Detects missing submission periods

FIX: All nodes now return PARTIAL dicts (only the keys they change).
     Returning the full `state` object from parallel nodes causes
     INVALID_CONCURRENT_GRAPH_UPDATE because LangGraph sees every key
     (including `audit_case_id`) being written by multiple nodes at once.

     agent_logs uses Annotated[List[dict], add], so each node must return
     only its NEW log entry as a one-item list — the reducer appends it.
"""
import logging
from datetime import datetime
from typing import List, Dict

from app.agent_langgraph.wc_state import WCAuditState

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Officer Agent
# ─────────────────────────────────────────────

def officer_agent(state: WCAuditState) -> dict:
    """
    Detects officer payroll misclassification.
    Returns only: officer_findings, warnings, agent_logs
    """
    excel_records = state.get("excel_records", [])
    policy_config = state.get("policy_config", {})

    findings: List[dict] = []
    new_warnings: List[str] = []

    officers = policy_config.get("officers", [])

    if not officers:
        new_warnings.append("No officer payroll data available in policy config for validation.")
        log_entry = {
            "agent":     "officer_agent",
            "status":    "skipped",
            "reason":    "No officer data in policy config",
            "timestamp": datetime.utcnow().isoformat(),
        }
        logger.info("[OfficerAgent] Skipped — no officer data in policy config.")
        return {
            "officer_findings": [],
            "warnings":         (state.get("warnings") or []) + new_warnings,
            "agent_logs":       [log_entry],   # ← single new entry; add-reducer appends it
        }

    # Collect employee names from payroll with non-zero wages
    employees_with_wages = {
        str(r.get("employee_name", "")).strip().lower()
        for r in excel_records
        if float(r.get("wages", 0) or 0) > 0
    }

    for officer in officers:
        name          = str(officer.get("name", "")).strip()
        is_on_payroll = bool(officer.get("is_on_payroll", True))
        name_lower    = name.lower()

        if is_on_payroll and name_lower not in employees_with_wages:
            findings.append({
                "officer_name": name,
                "expected":     "on_payroll",
                "actual":       "not_found_in_payroll",
                "severity":     "critical",
                "description":  (
                    f"Officer '{name}' is designated 'on payroll' in policy but "
                    "no wages were found in the payroll detail records."
                ),
                "class_code":   officer.get("class_code", ""),
                "state_code":   officer.get("state_code", ""),
            })
        elif not is_on_payroll and name_lower in employees_with_wages:
            findings.append({
                "officer_name": name,
                "expected":     "never_on_payroll",
                "actual":       "found_with_wages",
                "severity":     "critical",
                "description":  (
                    f"Officer '{name}' is designated 'never on payroll' in policy "
                    "but wages were recorded in payroll detail — premium impact."
                ),
                "class_code":   officer.get("class_code", ""),
                "state_code":   officer.get("state_code", ""),
            })

    log_entry = {
        "agent":     "officer_agent",
        "status":    "success",
        "findings":  len(findings),
        "timestamp": datetime.utcnow().isoformat(),
    }

    if findings:
        logger.warning(f"[OfficerAgent] {len(findings)} officer misclassification(s) found.")
    else:
        logger.info("[OfficerAgent] No officer misclassifications detected.")

    # ── Only return keys this agent owns ──────────────────────────────
    return {
        "officer_findings": findings,
        "agent_logs":       [log_entry],
    }


# ─────────────────────────────────────────────
# Class Code Agent
# ─────────────────────────────────────────────

def class_code_agent(state: WCAuditState) -> dict:
    """
    Validates class code usage in payroll vs policy configuration.
    Returns only: class_code_findings, agent_logs
    """
    excel_records = state.get("excel_records", [])
    xml_records   = state.get("xml_records",   [])

    if not xml_records:
        log_entry = {
            "agent":     "class_code_agent",
            "status":    "skipped",
            "reason":    "No XML policy records",
            "timestamp": datetime.utcnow().isoformat(),
        }
        logger.warning("[ClassCodeAgent] Skipped — no XML records available.")
        return {
            "class_code_findings": [],
            "agent_logs":          [log_entry],
        }

    findings: List[dict] = []

    # Valid class codes from policy (per state)
    policy_codes: Dict[str, set] = {}
    for rec in xml_records:
        sc = str(rec.get("StateCode", "")).strip()
        cc = str(rec.get("classCode", "")).strip()
        policy_codes.setdefault(sc, set()).add(cc)

    # Class codes actually used in payroll records (per state)
    payroll_codes: Dict[str, set] = {}
    for rec in excel_records:
        sc = str(rec.get("state_code", "")).strip()
        cc = str(rec.get("class_code", "")).strip()
        if cc:
            payroll_codes.setdefault(sc, set()).add(cc)

    # Payroll codes absent from policy
    for sc, codes in payroll_codes.items():
        valid   = policy_codes.get(sc, set())
        invalid = codes - valid
        for cc in invalid:
            findings.append({
                "class_code":  cc,
                "state_code":  sc,
                "issue":       "invalid_class_code",
                "severity":    "critical",
                "description": (
                    f"Class code {cc} in state {sc} appears in payroll records "
                    "but is NOT listed in the policy configuration."
                ),
            })

    # Policy codes with no payroll activity
    for sc, codes in policy_codes.items():
        used    = payroll_codes.get(sc, set())
        missing = codes - used
        for cc in missing:
            findings.append({
                "class_code":  cc,
                "state_code":  sc,
                "issue":       "no_payroll_reported",
                "severity":    "warning",
                "description": (
                    f"Class code {cc} in state {sc} is in the policy "
                    "but has NO payroll reported. Verify if intentional."
                ),
            })

    log_entry = {
        "agent":     "class_code_agent",
        "status":    "success",
        "findings":  len(findings),
        "timestamp": datetime.utcnow().isoformat(),
    }
    logger.info(f"[ClassCodeAgent] {len(findings)} class-code issue(s) found.")

    return {
        "class_code_findings": findings,
        "agent_logs":          [log_entry],
    }


# ─────────────────────────────────────────────
# Frequency Agent
# ─────────────────────────────────────────────

def frequency_agent(state: WCAuditState) -> dict:
    """
    Detects missing submission periods and frequency anomalies.
    Returns only: frequency_findings, agent_logs
    """
    expected  = float(state.get("expected_submissions", 0) or 0)
    actual    = float(state.get("actual_submissions",   0) or 0)
    submitted = int(state.get("submitted_count",        0) or 0)
    frequency = str(state.get("payroll_frequency",      "1W"))

    if expected <= 0:
        log_entry = {
            "agent":     "frequency_agent",
            "status":    "skipped",
            "reason":    "expected_submissions is zero",
            "timestamp": datetime.utcnow().isoformat(),
        }
        logger.warning("[FrequencyAgent] Skipped — expected_submissions is 0.")
        return {
            "frequency_findings": [],
            "agent_logs":         [log_entry],
        }

    findings: List[dict] = []
    gap     = expected - submitted
    gap_pct = (gap / expected * 100) if expected > 0 else 0.0

    if gap > 2:
        findings.append({
            "state_code":     state.get("policy_config", {}).get("state_code", "ALL"),
            "issue":          "missing_submissions",
            "severity":       "critical" if gap > 4 else "warning",
            "expected_count": round(expected, 1),
            "actual_count":   submitted,
            "gap":            round(gap, 1),
            "gap_pct":        round(gap_pct, 2),
            "description":    (
                f"Expected {expected:.0f} payroll submissions (frequency: {frequency}) "
                f"but only {submitted} were received — {gap:.0f} submission(s) missing."
            ),
        })

    # Low period-coverage check
    if actual > 0 and expected > 0:
        coverage_pct = (actual / expected) * 100
        if coverage_pct < 80:
            findings.append({
                "state_code":   "ALL",
                "issue":        "low_period_coverage",
                "severity":     "warning",
                "coverage_pct": round(coverage_pct, 1),
                "description":  (
                    f"Payroll period coverage is only {coverage_pct:.1f}% of the "
                    "policy term — verify for missing periods."
                ),
            })

    log_entry = {
        "agent":     "frequency_agent",
        "status":    "success",
        "findings":  len(findings),
        "expected":  expected,
        "submitted": submitted,
        "gap":       round(gap, 1),
        "timestamp": datetime.utcnow().isoformat(),
    }

    if findings:
        logger.warning(f"[FrequencyAgent] {len(findings)} frequency issue(s) found.")
    else:
        logger.info("[FrequencyAgent] Submission frequency looks normal.")

    return {
        "frequency_findings": findings,
        "agent_logs":         [log_entry],
    }
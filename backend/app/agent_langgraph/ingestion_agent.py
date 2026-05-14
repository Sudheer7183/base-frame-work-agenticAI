"""
Ingestion Agent
Parses three data sources:
  1. Payroll Excel   → excel_records
  2. Policy XML      → xml_records
  3. Audit Meta XL   → audit_xl_records  (first/last check date, submission count)

FIX: Removed all in-place `state[key] = ...` mutations.
     Each node now only returns a partial dict of the keys it produces.
     agent_logs returns a single-item list; the Annotated[add] reducer
     appends it — no more duplicate log entries.
"""
import logging
from datetime import datetime
from typing import Any
import xml.etree.ElementTree as ET

import pandas as pd

from app.agent_langgraph.wc_state import WCAuditState

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int_str(value: Any) -> str:
    """Convert class code (possibly float) to clean int string."""
    try:
        if pd.isna(value):
            return ""
        return str(int(float(value)))
    except Exception:
        return str(value).strip()


def _safe_date(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.strftime("%m/%d/%Y")
    return str(value).strip()


# ─────────────────────────────────────────────
# Node 1 – Parse Payroll Excel
# ─────────────────────────────────────────────

def parse_payroll_excel(state: WCAuditState) -> dict:
    """Read insured/payroll-provider Excel file → excel_records."""
    filepath = state["payroll_file_path"]
    logger.info(f"[IngestionAgent] Reading payroll Excel: {filepath}")

    try:
        df = pd.read_excel(filepath)
        records = []
        for _, row in df.iterrows():
            records.append({
                "client_name":    str(row.get("Client Name", "") or ""),
                "policy_number":  str(row.get("Policy Number", "") or "").strip(),
                "check_date":     _safe_date(row.get("CheckDate")),
                "ee_no":          str(row.get("EE No", "") or ""),
                "employee_name":  str(row.get("Employee Name", "") or ""),
                "state_code":     str(row.get("St.", "") or "").strip(),
                "class_code":     _safe_int_str(row.get("Class Code")),
                "wages":          _safe_float(row.get("Wages")),
                "overtime_pay":   _safe_float(row.get("OT")),
                "double_time":    _safe_float(row.get("DT")),
                "tips":           _safe_float(row.get("Tips")),
                "net_pay":        _safe_float(row.get("Net")),
                "exposure":       _safe_float(row.get("Exposure")),
                "net_rate":       _safe_float(row.get("Net Rate")),
                "earned_premium": _safe_float(row.get("Earned Prem.")),
                "census_rate":    _safe_float(row.get("Census Rate")),
                "census_premium": _safe_float(row.get("Census Prem.")),
                "pol_eff_date":   _safe_date(row.get("Pol Eff. Date")),
                "process_date":   _safe_date(row.get("Process Date")),
            })

        logger.info(f"[IngestionAgent] Loaded {len(records)} payroll rows.")
        return {
            "excel_records": records,
            "agent_logs": [{
                "agent":     "ingestion_excel",
                "status":    "success",
                "count":     len(records),
                "timestamp": datetime.utcnow().isoformat(),
            }],
        }

    except Exception as exc:
        logger.error(f"[IngestionAgent] Excel parse error: {exc}")
        return {
            "excel_records": [],
            "errors": (state.get("errors") or []) + [f"Payroll Excel parse failed: {exc}"],
            "agent_logs": [{
                "agent":     "ingestion_excel",
                "status":    "error",
                "error":     str(exc),
                "timestamp": datetime.utcnow().isoformat(),
            }],
        }


# ─────────────────────────────────────────────
# Node 2 – Parse Policy XML
# ─────────────────────────────────────────────

def parse_policy_xml(state: WCAuditState) -> dict:
    """Read policy XML (carrier system export) → xml_records + policy_config."""

    if state.get("data_source") == "api":
        return {}   # ← ADD THESE TWO LINES
    filepath = state["policy_xml_path"]
    logger.info(f"[IngestionAgent] Reading policy XML: {filepath}")

    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        policy_node = root.find("Policy")
        policy_data = policy_node.find("PolicyData")

        policy_number   = policy_data.findtext("PolicyNumber",  "").strip()
        effective_date  = policy_data.findtext("EffectiveDate",  "")
        expiration_date = policy_data.findtext("ExpirationDate", "")
        insured_name    = policy_data.findtext("InsuredName",    "")
        est_premium     = float(policy_data.findtext("Premium", "0"))
        payroll_freq    = policy_node.findtext("PayrollFrequency", "1W")

        # Compute expected payroll submissions
        fmt = "%m/%d/%Y"
        d1  = datetime.strptime(effective_date,  fmt)
        d2  = datetime.now()
        expected_submissions = (d2 - d1).days / 7   # weekly default

        policy_config = {
            "policy_number":          policy_number,
            "effective_date":         effective_date,
            "expiration_date":        expiration_date,
            "insured_name":           insured_name,
            "est_premium":            est_premium,
            "payroll_freq":           payroll_freq,
            "expected_submissions":   expected_submissions,
        }

        # Parse class codes per state
        records_xml: list = []
        states_node = policy_node.find("States")
        if states_node is not None:
            for state_node in states_node.findall("ComplexRateState"):
                state_code  = state_node.findtext("State", "")
                time_period = state_node.find("TimePeriod")
                if time_period is None:
                    continue
                rates_node = time_period.find("Rates")
                if rates_node is None:
                    continue
                for rate in rates_node.findall("Rate"):
                    class_code     = str(int(float(rate.findtext("ClassCode", "0"))))
                    composite_rate = float(rate.findtext("CompositeRate", "0"))
                    exposure       = float(rate.findtext("Exposure",      "0"))
                    est_prem       = float(rate.findtext("EstPremium",    "0"))
                    est_cc_prem    = exposure * composite_rate

                    records_xml.append({
                        "PolicyNumber":   policy_number,
                        "EffectiveDate":  effective_date,
                        "ExpirationDate": expiration_date,
                        "InsuredName":    insured_name,
                        "premium":        est_premium,
                        "StateCode":      state_code,
                        "classCode":      class_code,
                        "CompositeRate":  composite_rate,
                        "Exposure":       exposure,
                        "EstPremium":     est_prem,
                        "EstCCpremium":   est_cc_prem,
                        "expected_payroll_submissions": expected_submissions,
                    })

        logger.info(f"[IngestionAgent] Loaded {len(records_xml)} policy class-code rows.")
        return {
            "xml_records":          records_xml,
            "policy_config":        policy_config,
            "payroll_frequency":    payroll_freq,
            "expected_submissions": expected_submissions,
            "agent_logs": [{
                "agent":       "ingestion_xml",
                "status":      "success",
                "class_codes": len(records_xml),
                "timestamp":   datetime.utcnow().isoformat(),
            }],
        }

    except Exception as exc:
        logger.error(f"[IngestionAgent] XML parse error: {exc}")
        return {
            "xml_records":       [],
            "policy_config":     {},
            "errors": (state.get("errors") or []) + [f"Policy XML parse failed: {exc}"],
            "agent_logs": [{
                "agent":     "ingestion_xml",
                "status":    "error",
                "error":     str(exc),
                "timestamp": datetime.utcnow().isoformat(),
            }],
        }


# ─────────────────────────────────────────────
# Node 3 – Parse Audit Metadata Excel
# ─────────────────────────────────────────────

def parse_audit_metadata(state: WCAuditState) -> dict:
    """
    Read audit metadata Excel (first/last check date, submitted count).
    Also computes actual_submissions (weeks between first and last check date).
    Returns only the keys it produces; xml_records enrichment is done
    inside the premium_agent which already has both datasets.
    """
    if state.get("data_source") == "api":
        return {}   # ← ADD THESE TWO LINES
    filepath = state["audit_meta_file_path"]
    logger.info(f"[IngestionAgent] Reading audit metadata: {filepath}")

    try:
        raw_df = pd.read_excel(filepath, header=None)

        # Locate header row containing "First Check Date Reported"
        header_row = None
        for i, row in raw_df.iterrows():
            if row.astype(str).str.contains(
                "First Check Date Reported", case=False, na=False
            ).any():
                header_row = i
                break

        if header_row is None:
            raise ValueError(
                "Header row 'First Check Date Reported' not found in audit metadata."
            )

        df  = pd.read_excel(filepath, header=header_row)
        row = df.iloc[0]

        first_check = str(row.get("First Check Date Reported",             "")).strip()
        last_check  = str(row.get("Last Check Date Reported",              "")).strip()
        submitted   = float(row.get("Number of Payroll Reports Submitted", 0) or 0)

        fmt = "%m/%d/%Y"
        c_first = datetime.strptime(first_check, fmt)
        c_last  = datetime.strptime(last_check,  fmt)
        actual_submissions = (c_last - c_first).days / 7

        audit_meta = {
            "first_check_date":   first_check,
            "last_check_date":    last_check,
            "submitted_count":    submitted,
            "actual_submissions": actual_submissions,
        }

        logger.info(
            f"[IngestionAgent] Audit meta: {first_check} → {last_check}, "
            f"{submitted} submissions, {actual_submissions:.1f} weeks"
        )
        return {
            "audit_xl_records":  [audit_meta],
            "first_check_date":  first_check,
            "last_check_date":   last_check,
            "submitted_count":   int(submitted),
            "actual_submissions": actual_submissions,
            "agent_logs": [{
                "agent":        "ingestion_audit_meta",
                "status":       "success",
                "first_check":  first_check,
                "last_check":   last_check,
                "submitted":    submitted,
                "actual_weeks": actual_submissions,
                "timestamp":    datetime.utcnow().isoformat(),
            }],
        }

    except Exception as exc:
        logger.error(f"[IngestionAgent] Audit metadata parse error: {exc}")
        return {
            "audit_xl_records": [],
            "errors": (state.get("errors") or []) + [f"Audit metadata parse failed: {exc}"],
            "agent_logs": [{
                "agent":     "ingestion_audit_meta",
                "status":    "error",
                "error":     str(exc),
                "timestamp": datetime.utcnow().isoformat(),
            }],
        }
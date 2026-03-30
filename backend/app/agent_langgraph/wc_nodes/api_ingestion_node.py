import os
import logging
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

MOCK_API_BASE = os.getenv("MOCK_API_BASE_URL", "http://localhost:9000/api/v1")


def api_ingestion_node(state: dict) -> dict:
    """
    Single node that replaces the three parallel ingestion nodes
    (parse_payroll_excel + parse_policy_xml + parse_audit_metadata)
    when data_source == "api".

    Normalizes the Mock API response into the exact field shapes that
    every downstream agent (officer, class_code, frequency, variance)
    expects — matching what parse_payroll_excel / parse_policy_xml /
    parse_audit_metadata produce from file uploads.

    Key normalizations applied:
      Payroll rows  : class_code → ClassCode, state_code → StateCode
      XML records   : "classCode": "5190 78" → ClassCode="5190", StateCode="FL"
      audit_xl_records: mapped to the a_* key names the frequency/variance
                        agents read
    """
    policy_number = state.get("policy_number", "").strip()
    if not policy_number:
        return _err("policy_number missing from state")

    try:
        # ── Call 1: payroll rows ─────────────────────────────────────
        r1 = requests.get(
            f"{MOCK_API_BASE}/policies/{policy_number}/payroll",
            timeout=20,
        )
        r1.raise_for_status()
        raw_payroll = r1.json().get("records", [])

        # Normalize payroll rows to PascalCase keys the agents expect
        excel_records = [_normalize_payroll_row(row) for row in raw_payroll]

        # ── Call 2: policy config ────────────────────────────────────
        r2 = requests.get(
            f"{MOCK_API_BASE}/policies/{policy_number}/policy-config",
            timeout=20,
        )
        r2.raise_for_status()
        config = r2.json()

        raw_xml      = config.get("xml_records", [])
        raw_meta     = config.get("audit_meta", {})
        raw_officers = config.get("officers", [])

        # Normalize xml_records — split combined "classCode" field,
        # add explicit ClassCode / StateCode keys
        xml_records = [_normalize_xml_record(row) for row in raw_xml]

        # audit_xl_records — already has a_* keys; pass through but
        # ensure the keys the frequency/variance agents read are present
        audit_xl_records = [_normalize_audit_meta(raw_meta)]

        # policy_config — built from first xml record + audit_meta
        first_xml = xml_records[0] if xml_records else {}
        policy_config = {
            "policy_number":        first_xml.get("PolicyNumber", policy_number),
            "effective_date":       first_xml.get("EffectiveDate", ""),
            "expiration_date":      first_xml.get("ExpirationDate", ""),
            "insured_name":         first_xml.get("InsuredName", ""),
            "est_premium":          first_xml.get("premium", 0.0),
            "payroll_frequency":    raw_meta.get("a_payroll_frequency", "1W"),
            "expected_submissions": raw_meta.get("a_expected_payroll_sub",
                                        first_xml.get("expected_payroll_submissions", 0)),
            "state_code":           first_xml.get("StateCode", ""),
            "officers":             raw_officers,
        }

        logger.info(
            f"[APIIngestion] {policy_number}: "
            f"{len(excel_records)} payroll rows, {len(xml_records)} class codes, "
            f"freq={policy_config['payroll_frequency']}"
        )

        return {
            # ── same keys parse_payroll_excel returns ──────────────
            "excel_records":        excel_records,
            # ── same keys parse_policy_xml returns ─────────────────
            "xml_records":          xml_records,
            "policy_config":        policy_config,
            "payroll_frequency":    policy_config["payroll_frequency"],
            "expected_submissions": policy_config["expected_submissions"],
            # ── same keys parse_audit_metadata returns ──────────────
            "audit_xl_records":     audit_xl_records,
            # ── pre-populate submission counts from audit_meta ──────
            "submitted_count":      raw_meta.get("a_actual_payroll_sub", 0),
            "first_check_date":     raw_meta.get("a_first_check_date", ""),
            "last_check_date":      raw_meta.get("a_last_check_date", ""),
            "actual_submissions":   float(raw_meta.get("a_actual_payroll_sub", 0)),
            "agent_logs": [{
                "agent":        "ingestion_excel",   # frontend key for Ingestion Agent
                "status":       "complete",
                "payroll_rows": len(excel_records),
                "class_codes":  len(xml_records),
                "source":       MOCK_API_BASE,
                "timestamp":    datetime.utcnow().isoformat(),
            }, {
                "agent":     "ingestion_xml",        # frontend key for Policy Parser
                "status":    "complete",
                "timestamp": datetime.utcnow().isoformat(),
            }, {
                "agent":     "ingestion_audit_meta", # frontend key for Metadata Agent
                "status":    "complete",
                "timestamp": datetime.utcnow().isoformat(),
            }],
        }

    except Exception as exc:
        logger.exception(f"[APIIngestion] Unhandled error for {policy_number}")
        return _err(str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# Normalizers
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_payroll_row(row: dict) -> dict:
    """
    Map snake_case payroll fields → PascalCase keys the downstream
    agents (officer_agent, class_code_agent, premium_agent) read.

    Mock API payroll row keys:
      class_code, state_code, wages, exposure, net_rate,
      earned_premium, employee_name, ee_no, check_date, ...
    """
    return {
        # PascalCase aliases (what agents read)
        "ClassCode":      str(row.get("class_code", "") or "").strip(),
        "StateCode":      str(row.get("state_code",  "") or "").strip(),
        "EmployeeName":   row.get("employee_name", ""),
        "EENo":           str(row.get("ee_no", "") or ""),
        "CheckDate":      row.get("check_date", ""),
        "Wages":          float(row.get("wages", 0) or 0),
        "OvertimePay":    float(row.get("overtime_pay", 0) or 0),
        "DoubleTime":     float(row.get("double_time", 0) or 0),
        "Tips":           float(row.get("tips", 0) or 0),
        "NetPay":         float(row.get("net_pay", 0) or 0),
        "Exposure":       float(row.get("exposure", 0) or 0),
        "NetRate":        float(row.get("net_rate", 0) or 0),
        "EarnedPremium":  float(row.get("earned_premium", 0) or 0),
        "PolicyNumber":   row.get("policy_number", ""),
        "ClientName":     row.get("client_name", ""),
        "PolEffDate":     row.get("pol_eff_date", ""),
        "ProcessDate":    row.get("process_date", ""),
        # Keep originals too so nothing downstream breaks
        **row,
    }


def _normalize_xml_record(row: dict) -> dict:
    """
    Map the Mock API policy-config xml_record shape to what
    parse_policy_xml produces.

    Mock API shape:
      { "classCode": "5190 78", "StateCode": "FL",
        "CompositeRate": 0.034931, "Exposure": 93408.85,
        "EstPremium": 2338.87, ... }

    Target shape (what class_code_agent / premium_agent read):
      { "ClassCode": "5190", "StateCode": "FL",
        "CompositeRate": 0.034931,
        "est_exposure": 93408.85,
        "est_ytd_premium": 2338.87,
        "expected_payroll_submissions": 52, ... }
    """
    # "classCode" field is "5190 78" — the number after the space is
    # a state-specific modifier/suffix, not meaningful for matching.
    raw_cc    = str(row.get("classCode") or row.get("ClassCode") or "").strip()
    class_code = raw_cc.split()[0] if raw_cc else ""   # take first token only

    state_code = str(row.get("StateCode") or row.get("state_code") or "").strip()

    return {
        # Core identity — PascalCase so agents find them
        "ClassCode":    class_code,
        "StateCode":    state_code,
        "PolicyNumber": row.get("PolicyNumber", ""),
        "EffectiveDate":   row.get("EffectiveDate", ""),
        "ExpirationDate":  row.get("ExpirationDate", ""),
        "InsuredName":     row.get("InsuredName", ""),

        # Premium / exposure figures
        "premium":          float(row.get("premium", 0) or 0),
        "CompositeRate":    float(row.get("CompositeRate", 0) or 0),
        "net_rate":         float(row.get("CompositeRate", 0) or 0),  # alias

        # EST figures (what the variance node reads as "estimated")
        "est_exposure":     float(row.get("Exposure", 0) or 0),
        "Exposure":         float(row.get("Exposure", 0) or 0),
        "est_ytd_premium":  float(row.get("EstPremium", 0) or 0),
        "EstPremium":       float(row.get("EstPremium", 0) or 0),
        "EstCCpremium":     float(row.get("EstCCpremium", 0) or 0),

        # Submission counts
        "expected_payroll_submissions": int(row.get("expected_payroll_submissions", 0) or 0),
        "actual_payroll_submissions":   int(row.get("actual_payroll_submissions", 0) or 0),
        "Number_of_Payroll_Reports_Submitted": int(
            row.get("Number_of_Payroll_Reports_Submitted", 0) or 0
        ),

        # Keep originals
        **row,
        # Override classCode with split value so nothing reads the raw "5190 78"
        "classCode": class_code,
    }


def _normalize_audit_meta(meta: dict) -> dict:
    """
    Ensure all a_* keys the frequency_agent and variance agents read
    are present, with sensible defaults if missing.
    """
    return {
        "a_payroll_frequency":   meta.get("a_payroll_frequency", "1W"),
        "a_first_check_date":    meta.get("a_first_check_date", ""),
        "a_last_check_date":     meta.get("a_last_check_date", ""),
        "a_actual_payroll_sub":  int(meta.get("a_actual_payroll_sub", 0) or 0),
        "a_expected_payroll_sub": int(meta.get("a_expected_payroll_sub", 0) or 0),
        "a_officer_on_payroll":  meta.get("a_officer_on_payroll", "No"),
        "a_reporting_by_class_code": meta.get("a_reporting_by_class_code", "Yes"),
        # Keep originals
        **meta,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Error helper
# ─────────────────────────────────────────────────────────────────────────────

def _err(msg: str) -> dict:
    logger.error(f"[APIIngestion] {msg}")
    return {
        "excel_records":    [],
        "xml_records":      [],
        "policy_config":    {},
        "audit_xl_records": [{}],
        "errors": [f"api_ingestion_node failed: {msg}"],
        "agent_logs": [{
            "agent":     "ingestion_excel",
            "status":    "error",
            "error":     msg,
            "timestamp": datetime.utcnow().isoformat(),
        }],
    }
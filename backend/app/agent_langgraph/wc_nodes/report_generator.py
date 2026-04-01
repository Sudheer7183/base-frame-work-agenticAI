"""
Report Generator Node
Produces the final audit report in Excel format matching the
"XC AI Audit" sheet layout from POC Table Structures v8.xlsx.

Also builds the structured report_data dict for database storage.
"""
import logging
import os
from datetime import datetime
from typing import Any

from app.agent_langgraph.wc_state import WCAuditState

logger = logging.getLogger(__name__)

# Optional: openpyxl for Excel output
try:
    import openpyxl
    from openpyxl.styles import (
        Font, Alignment, PatternFill, Border, Side, numbers
    )
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logger.warning("[ReportGenerator] openpyxl not installed. Excel export disabled.")


def generate_report(state: WCAuditState) -> WCAuditState:
    """Build structured report_data and optionally export Excel."""
    overall      = state.get("overall_variance", {})
    cc_variances = state.get("class_code_variance", [])
    policy_cfg   = state.get("policy_config", {})

    # ── Build structured report dict ──────────────────────────────────
    report_data = {
        "report_ref":   f"WCA-{state.get('policy_number', 'UNKNOWN')}-"
                        f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "generated_at": datetime.utcnow().isoformat(),
        "policy": {
            "policy_number":    state.get("policy_number"),
            "insured_name":     policy_cfg.get("insured_name"),
            "effective_date":   policy_cfg.get("effective_date"),
            "expiration_date":  policy_cfg.get("expiration_date"),
            "estimated_premium": policy_cfg.get("est_premium"),
        },
        "audit_summary": {
            "first_check_date":   state.get("first_check_date"),
            "last_check_date":    state.get("last_check_date"),
            "submitted_count":    state.get("submitted_count"),
            "expected_submissions": round(float(state.get("expected_submissions", 0)), 1),
            "actual_submissions":   round(float(state.get("actual_submissions",   0)), 1),
        },
        "variance_summary": overall,
        "variance_by_class_code": cc_variances,
        "findings": {
            "officer_issues":    state.get("officer_findings",    []),
            "class_code_issues": state.get("class_code_findings", []),
            "frequency_issues":  state.get("frequency_findings",  []),
        },
        "risk_assessment": {
            "risk_level":     state.get("risk_level"),
            "recommendation": state.get("recommendation"),
            "hitl_required":  state.get("hitl_required"),
        },
        "ai_narrative": state.get("ai_narrative", ""),
        "agent_logs":   state.get("agent_logs", []),
    }

    state["report_data"] = report_data

    # ── Excel export ──────────────────────────────────────────────────
    if OPENPYXL_AVAILABLE:
        try:
            output_dir  = os.getenv("REPORT_OUTPUT_DIR", "/tmp/wc_audit_reports")
            os.makedirs(output_dir, exist_ok=True)
            report_file = os.path.join(
                output_dir,
                f"{report_data['report_ref']}.xlsx"
            )
            _write_excel_report(report_data, report_file)
            state["report_file_path"] = report_file
            logger.info(f"[ReportGenerator] Excel report saved: {report_file}")
        except Exception as exc:
            logger.error(f"[ReportGenerator] Excel export failed: {exc}")
            state["warnings"].append(f"Excel report generation failed: {exc}")
    else:
        logger.info("[ReportGenerator] Skipping Excel export (openpyxl not available).")

    state["agent_logs"].append({
        "agent":    "report_generator",
        "status":   "success",
        "report_ref": report_data["report_ref"],
        "timestamp": datetime.utcnow().isoformat(),
    })

    return state


# ─────────────────────────────────────────────
# Excel Report Writer
# Matches the "XC AI Audit" sheet format
# ─────────────────────────────────────────────

HEADER_FILL   = PatternFill("solid", fgColor="1F4E79") if OPENPYXL_AVAILABLE else None
SECTION_FILL  = PatternFill("solid", fgColor="2E75B6") if OPENPYXL_AVAILABLE else None
TOTAL_FILL    = PatternFill("solid", fgColor="D6E4F0") if OPENPYXL_AVAILABLE else None
FLAG_FILL     = PatternFill("solid", fgColor="FFCCCC") if OPENPYXL_AVAILABLE else None
WHITE_FONT    = Font(color="FFFFFF", bold=True)       if OPENPYXL_AVAILABLE else None
BOLD_FONT     = Font(bold=True)                        if OPENPYXL_AVAILABLE else None
CENTER        = Alignment(horizontal="center", vertical="center")
MONEY_FMT     = '#,##0.00'
PCT_FMT       = '0.00"%"'

THIN_BORDER   = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'),  bottom=Side(style='thin')
) if OPENPYXL_AVAILABLE else None


def _cell(ws, row, col, value, font=None, fill=None, align=None,
          num_format=None, border=None):
    c = ws.cell(row=row, column=col, value=value)
    if font:      c.font       = font
    if fill:      c.fill       = fill
    if align:     c.alignment  = align
    if num_format: c.number_format = num_format
    if border:    c.border     = border
    return c


def _write_excel_report(data: dict, filepath: str) -> None:
    wb = openpyxl.Workbook()

    # ── Sheet 1: XC AI Audit (main variance report) ──────────────────
    ws = wb.active
    ws.title = "XC AI Audit"
    ws.sheet_view.showGridLines = False

    policy   = data["policy"]
    summary  = data["audit_summary"]
    variance = data["variance_summary"]
    cc_lines = data["variance_by_class_code"]
    risk     = data["risk_assessment"]

    # Title block
    ws.merge_cells("A1:J1")
    _cell(ws, 1, 1,
          f"Workers Compensation Premium Audit – {policy.get('policy_number', '')}",
          font=Font(size=14, bold=True, color="FFFFFF"),
          fill=HEADER_FILL, align=CENTER)
    ws.row_dimensions[1].height = 28

    ws.merge_cells("A2:J2")
    _cell(ws, 2, 1,
          f"Insured: {policy.get('insured_name', '')}   |   "
          f"Policy Period: {policy.get('effective_date', '')} – {policy.get('expiration_date', '')}   |   "
          f"Generated: {data['generated_at'][:19]}",
          font=Font(size=10, italic=True, color="FFFFFF"),
          fill=SECTION_FILL, align=CENTER)
    ws.row_dimensions[2].height = 18

    # ── Audit Summary block (row 4–8) ─────────────────────────────────
    _cell(ws, 4, 1, "AUDIT PERIOD SUMMARY", font=BOLD_FONT, fill=TOTAL_FILL)
    ws.merge_cells("A4:C4")

    labels = [
        ("First Check Date",    summary.get("first_check_date")),
        ("Last Check Date",     summary.get("last_check_date")),
        ("Submitted Reports",   summary.get("submitted_count")),
        ("Expected Reports",    summary.get("expected_submissions")),
        ("Actual Weeks Worked", summary.get("actual_submissions")),
    ]
    for i, (lbl, val) in enumerate(labels, start=5):
        _cell(ws, i, 1, lbl,  font=BOLD_FONT, border=THIN_BORDER)
        _cell(ws, i, 2, val,  border=THIN_BORDER)

    # ── Variance Detail Table header (row 11 onwards) ─────────────────
    hdr_row = 11
    headers = [
        "Policy Number", "State", "Class Code",
        "Earned Exposure", "EST Exposure",
        "Earned Premium", "EST YTD Premium",
        "Premium Variance ($)", " Premium Variance pct (%)", "Root Cause"
    ]
    col_widths = [18, 8, 12, 16, 16, 16, 18, 16, 14, 22]

    for col_idx, (hdr, width) in enumerate(zip(headers, col_widths), start=1):
        c = _cell(ws, hdr_row, col_idx, hdr,
                  font=WHITE_FONT, fill=HEADER_FILL,
                  align=CENTER, border=THIN_BORDER)
        ws.column_dimensions[c.column_letter].width = width

    # Data rows
    for row_offset, line in enumerate(cc_lines, start=1):
        r = hdr_row + row_offset
        is_flagged = line.get("is_flagged", False)
        row_fill   = FLAG_FILL if is_flagged else None

        values = [
            line.get("PolicyNumber"),
            line.get("StateCode"),
            line.get("ClassCode"),
            line.get("earned_exposure", 0),
            line.get("est_exposure",  0),
            line.get("earned_premium",    0),
            line.get("est_ytd_premium", 0),
            line.get("variance",        0),
            line.get("variance_pct",    0),
            line.get("root_cause", "").replace("_", " ").title(),
        ]
        num_formats = [None, None, None,
                       MONEY_FMT, MONEY_FMT, MONEY_FMT, MONEY_FMT,
                       MONEY_FMT, PCT_FMT,   None]

        for col_idx, (val, fmt) in enumerate(zip(values, num_formats), start=1):
            _cell(ws, r, col_idx, val,
                  fill=row_fill, num_format=fmt, border=THIN_BORDER)

    # Totals row
    total_row = hdr_row + len(cc_lines) + 1
    ws.merge_cells(f"A{total_row}:C{total_row}")
    _cell(ws, total_row, 1, "TOTAL",
          font=BOLD_FONT, fill=TOTAL_FILL, align=CENTER, border=THIN_BORDER)

    totals = [
        variance.get("earned_exposure", 0),
        variance.get("est_exposure",  0),
        variance.get("earned_premium",    0),
        variance.get("est_ytd_premium", 0),
        variance.get("variance",        0),
        variance.get("variance_pct",    0),
        "",
    ]
    total_num_fmts = [MONEY_FMT, MONEY_FMT, MONEY_FMT, MONEY_FMT,
                      MONEY_FMT, PCT_FMT,   None]
    for i, (val, fmt) in enumerate(zip(totals, total_num_fmts), start=4):
        _cell(ws, total_row, i, val,
              font=BOLD_FONT, fill=TOTAL_FILL,
              num_format=fmt, border=THIN_BORDER)

    # ── Risk & Recommendation block ───────────────────────────────────
    risk_row = total_row + 3
    _cell(ws, risk_row, 1, "RISK ASSESSMENT", font=BOLD_FONT, fill=TOTAL_FILL)
    ws.merge_cells(f"A{risk_row}:C{risk_row}")
    _cell(ws, risk_row + 1, 1, "Risk Level",     font=BOLD_FONT, border=THIN_BORDER)
    _cell(ws, risk_row + 1, 2, risk.get("risk_level", "").upper(), border=THIN_BORDER)
    _cell(ws, risk_row + 2, 1, "Recommendation", font=BOLD_FONT, border=THIN_BORDER)
    _cell(ws, risk_row + 2, 2,
          risk.get("recommendation", "").replace("_", " ").title(),
          border=THIN_BORDER)
    _cell(ws, risk_row + 3, 1, "HITL Required",  font=BOLD_FONT, border=THIN_BORDER)
    _cell(ws, risk_row + 3, 2, "Yes" if risk.get("hitl_required") else "No",
          border=THIN_BORDER)

    # ── Narrative sheet ───────────────────────────────────────────────
    ws2 = wb.create_sheet("Narrative")
    ws2["A1"] = "AI-Generated Audit Narrative"
    ws2["A1"].font = Font(size=12, bold=True)
    ws2["A3"] = data.get("ai_narrative", "")
    ws2["A3"].alignment = Alignment(wrap_text=True)
    ws2.column_dimensions["A"].width = 120
    ws2.row_dimensions[3].height = 300

    # ── Findings sheet ────────────────────────────────────────────────
    ws3 = wb.create_sheet("Agent Findings")
    ws3.column_dimensions["A"].width = 20
    ws3.column_dimensions["B"].width = 15
    ws3.column_dimensions["C"].width = 80

    findings_hdrs = ["Agent / Finding Type", "Severity", "Description"]
    for i, h in enumerate(findings_hdrs, 1):
        _cell(ws3, 1, i, h, font=WHITE_FONT, fill=HEADER_FILL, border=THIN_BORDER)

    r = 2
    for finding_list, agent_label in [
        (data["findings"]["officer_issues"],    "Officer Agent"),
        (data["findings"]["class_code_issues"], "Class Code Agent"),
        (data["findings"]["frequency_issues"],  "Frequency Agent"),
    ]:
        for finding in finding_list:
            _cell(ws3, r, 1, agent_label, border=THIN_BORDER)
            _cell(ws3, r, 2, finding.get("severity", ""), border=THIN_BORDER)
            _cell(ws3, r, 3, finding.get("description", ""),
                  align=Alignment(wrap_text=True), border=THIN_BORDER)
            ws3.row_dimensions[r].height = 40
            r += 1

    wb.save(filepath)

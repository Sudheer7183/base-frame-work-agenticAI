

"""
Workers' Compensation Audit Platform – Streamlit UI
Implements the full audit workflow interface including:
  • Dashboard / KPI summary
  • File upload & audit initiation
  • Variance explorer with drill-down
  • HITL review panel with override controls
  • Report download
"""
import json
import os
import time
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
API_BASE = os.getenv("WC_AUDIT_API_BASE", "http://localhost:8000/api/v1/wc-audit")
PAGE_REFRESH_SECS = 5

st.set_page_config(
    page_title="WC Audit Platform",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom CSS (matching wireframe)
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Main theme */
    .main { background-color: #F0F4F8; }
    .block-container { padding: 1.5rem 2rem; }

    /* KPI Cards */
    .kpi-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #1F4E79;
        margin-bottom: 1rem;
    }
    .kpi-card h3 { color: #1F4E79; margin: 0; font-size: 14px; font-weight: 600; }
    .kpi-card h2 { margin: 4px 0 0 0; font-size: 26px; color: #0A2540; }

    /* Status badges */
    .badge-high   { background:#FFCCCC; color:#C0392B; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
    .badge-medium { background:#FFF3CD; color:#856404; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
    .badge-low    { background:#D4EDDA; color:#155724; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }

    /* Section headers */
    .section-header {
        background: #1F4E79; color: white;
        padding: 10px 16px; border-radius: 6px;
        margin: 1.5rem 0 0.8rem 0; font-size: 15px; font-weight: 700;
    }

    /* Flagged rows */
    .flagged-row { background-color: #FFF3CD !important; }

    /* HITL panel */
    .hitl-panel {
        background: #FFF8E1;
        border: 2px solid #FFC107;
        border-radius: 10px;
        padding: 20px;
        margin: 1rem 0;
    }

    /* Sidebar */
    [data-testid="stSidebar"] { background: #0A2540; }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] .stSelectbox label { color: #ADB5BD !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────

def api_get(path: str, default=None):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return default


def api_post(path: str, data: dict = None, files=None):
    try:
        if files:
            r = requests.post(f"{API_BASE}{path}", files=files, timeout=30)
        else:
            r = requests.post(
                f"{API_BASE}{path}",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
        return r.json(), r.status_code
    except Exception as exc:
        return {"error": str(exc)}, 500


def fmt_money(v):
    try:
        v = float(v)
        sign = "+" if v > 0 else ""
        return f"{sign}${v:,.2f}"
    except Exception:
        return str(v)


def fmt_pct(v):
    try:
        return f"{float(v):+.2f}%"
    except Exception:
        return str(v)


def risk_badge(risk):
    cls = {"high": "badge-high", "medium": "badge-medium", "low": "badge-low"}.get(
        str(risk).lower(), "badge-low"
    )
    return f'<span class="{cls}">{str(risk).upper()}</span>'


# ─────────────────────────────────────────────
# Sidebar Navigation
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 📋 WC Audit Platform")
    st.markdown("---")
    nav = st.radio(
        "Navigation",
        ["🏠 Dashboard", "📂 New Audit", "🔍 Variance Explorer",
         "👤 HITL Review", "📊 Reports", "⚙️ Settings"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**Platform v1.3** | WC Audit Module")
    st.markdown("Powered by LangGraph + Claude")


# ─────────────────────────────────────────────
# Page: Dashboard
# ─────────────────────────────────────────────

if nav == "🏠 Dashboard":
    st.title("Workers' Compensation Audit Dashboard")
    st.markdown("*Real-time audit pipeline monitoring*")

    # Load all audits
    all_audits = api_get("/list?limit=100", default={"items": [], "total": 0})
    items      = all_audits.get("items", [])

    # KPI row
    total      = len(items)
    pending    = sum(1 for i in items if i.get("status") in ("pending", "processing"))
    completed  = sum(1 for i in items if i.get("status") == "completed")
    hitl_wait  = sum(1 for i in items if i.get("status") == "review")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="kpi-card">
            <h3>Total Audits</h3><h2>{total}</h2></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="kpi-card" style="border-left-color:#FFC107;">
            <h3>In Progress</h3><h2>{pending}</h2></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="kpi-card" style="border-left-color:#28A745;">
            <h3>Completed</h3><h2>{completed}</h2></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="kpi-card" style="border-left-color:#DC3545;">
            <h3>Awaiting HITL</h3><h2>{hitl_wait}</h2></div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Recent audits table
    st.markdown('<div class="section-header">📋 Recent Audit Cases</div>',
                unsafe_allow_html=True)

    if items:
        table_data = []
        for item in reversed(items[-20:]):
            res = item.get("result") or {}
            ov  = res.get("overall_variance", {})
            table_data.append({
                "Case ID":       item.get("audit_case_id"),
                "Policy #":      item.get("policy_number", "—"),
                "Status":        item.get("status", "—").title(),
                "Risk":          res.get("risk_level", "—").upper() if res else "—",
                "Variance $":    fmt_money(ov.get("variance",   0)) if ov else "—",
                "Variance %":    fmt_pct(ov.get("variance_pct", 0)) if ov else "—",
                "Recommendation": res.get("recommendation", "—").replace("_", " ").title()
                                  if res else "—",
                "Created":       item.get("created_at", "")[:16],
            })

        df = pd.DataFrame(table_data)

        def highlight_row(row):
            if "High" in str(row.get("Risk", "")):
                return ["background-color: #FFCCCC"] * len(row)
            if "Medium" in str(row.get("Risk", "")):
                return ["background-color: #FFF3CD"] * len(row)
            return [""] * len(row)

        st.dataframe(
            df.style.apply(highlight_row, axis=1),
            use_container_width=True,
            height=400,
        )
    else:
        st.info("No audit cases yet. Start a new audit from the **📂 New Audit** page.")


# ─────────────────────────────────────────────
# Page: New Audit
# ─────────────────────────────────────────────

elif nav == "📂 New Audit":
    st.title("Start a New Audit")
    st.markdown("Upload payroll and policy data to initiate the automated audit workflow.")

    with st.form("new_audit_form"):
        st.markdown('<div class="section-header">📁 Policy Information</div>',
                    unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            policy_number = st.text_input("Policy Number *", placeholder="e.g. WC-2025-001234")
            tenant_id     = st.text_input("Tenant ID", value="default")
        with col2:
            st.info("💡 Upload files below then click **Start Audit** to begin the automated workflow.")

        st.markdown('<div class="section-header">📎 Data Files</div>',
                    unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            payroll_file = st.file_uploader(
                "Payroll Excel *  (.xlsx)",
                type=["xlsx", "xls"],
                key="payroll_upload",
            )
        with col_b:
            policy_xml = st.file_uploader(
                "Policy XML * (.xml)",
                type=["xml"],
                key="xml_upload",
            )
        with col_c:
            audit_meta = st.file_uploader(
                "Audit Metadata (.xlsx)",
                type=["xlsx", "xls"],
                key="meta_upload",
            )

        submitted = st.form_submit_button("🚀 Start Audit Workflow", type="primary",
                                          use_container_width=True)

    if submitted:
        if not policy_number:
            st.error("Policy Number is required.")
        elif not payroll_file or not policy_xml:
            st.error("Payroll Excel and Policy XML are required.")
        else:
            with st.spinner("Uploading files and initialising audit workflow…"):
                # Upload files
                files_payload = {
                    "payroll_file": (payroll_file.name, payroll_file.getvalue(),
                                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                    "policy_xml":   (policy_xml.name, policy_xml.getvalue(), "text/xml"),
                }
                if audit_meta:
                    files_payload["audit_meta"] = (
                        audit_meta.name, audit_meta.getvalue(),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                upload_resp, upload_status = api_post("/upload", files=files_payload)

                if upload_status != 200:
                    st.error(f"File upload failed: {upload_resp}")
                else:
                    # Start audit
                    start_payload = {
                        "policy_number":        policy_number,
                        "tenant_id":            tenant_id,
                        "payroll_file_path":    upload_resp.get("payroll_file_path", ""),
                        "policy_xml_path":      upload_resp.get("policy_xml_path", ""),
                        "audit_meta_file_path": upload_resp.get("audit_meta_file_path", ""),
                    }
                    start_resp, start_status = api_post("/start", data=start_payload)

                    if start_status == 200:
                        case_id = start_resp.get("audit_case_id")
                        st.success(
                            f"✅ Audit started! Case ID: **{case_id}**  \n"
                            "The LangGraph workflow is running. Navigate to "
                            "**🔍 Variance Explorer** to see results."
                        )
                        st.session_state["last_case_id"] = case_id
                    else:
                        st.error(f"Failed to start audit: {start_resp}")


# ─────────────────────────────────────────────
# Page: Variance Explorer
# ─────────────────────────────────────────────

elif nav == "🔍 Variance Explorer":
    st.title("Variance Explorer")
    st.markdown("*Drill down into audit variance by class code, state, and root cause.*")

    # Case selector
    col1, col2 = st.columns([3, 1])
    with col1:
        case_id_input = st.number_input(
            "Audit Case ID",
            min_value=1,
            value=int(st.session_state.get("last_case_id", 1)),
            step=1,
        )
    with col2:
        refresh = st.button("🔄 Refresh", use_container_width=True)

    # Fetch status
    status_data  = api_get(f"/status/{case_id_input}", default={})
    status_label = status_data.get("status", "unknown")

    status_colors = {
        "completed":  "#28A745", "review": "#FFC107",
        "processing": "#17A2B8", "error":  "#DC3545", "pending": "#6C757D"
    }
    color = status_colors.get(status_label, "#6C757D")
    st.markdown(
        f"**Status:** <span style='color:{color}; font-weight:700;'>"
        f"{status_label.upper()}</span>",
        unsafe_allow_html=True,
    )

    if status_label not in ("completed", "review", "hitl_approved"):
        if status_label == "processing":
            st.info("⏳ Audit is still processing. This page will show results once complete.")
            time.sleep(PAGE_REFRESH_SECS)
            st.rerun()
        else:
            st.warning("No completed results available for this case ID.")
        st.stop()

    # Fetch full results
    results = api_get(f"/results/{case_id_input}", default={})
    if not results:
        st.error("Could not retrieve results.")
        st.stop()

    overall  = results.get("overall_variance", {})
    cc_lines = results.get("class_code_variance", [])

    # ── KPI Summary ──────────────────────────────────────────────────
    st.markdown('<div class="section-header">📊 Variance Summary</div>',
                unsafe_allow_html=True)

    k1, k2, k3, k4, k5 = st.columns(5)
    kpis = [
        ("Earned Premium",   overall.get("earned_premium",  0), MONEY_FMT := "money"),
        ("EST YTD Premium",  overall.get("est_ytd_premium", 0), "money"),
        ("Variance ($)",     overall.get("variance",        0), "money"),
        ("Variance (%)",     overall.get("variance_pct",    0), "pct"),
        ("Risk Level",       status_data.get("risk_level",  "—"), "badge"),
    ]
    for col, (label, val, fmt) in zip([k1, k2, k3, k4, k5], kpis):
        with col:
            if fmt == "money":
                display = fmt_money(val)
                color_style = "color:#C0392B;" if float(val or 0) > 0 else "color:#155724;"
            elif fmt == "pct":
                display      = fmt_pct(val)
                color_style  = "color:#C0392B;" if float(val or 0) > 0 else "color:#155724;"
            else:
                display      = str(val).upper()
                color_style  = {"HIGH": "color:#C0392B;", "MEDIUM": "color:#856404;",
                                "LOW": "color:#155724;"}.get(display, "")
            st.markdown(
                f"""<div class="kpi-card">
                    <h3>{label}</h3>
                    <h2 style="{color_style}">{display}</h2>
                </div>""",
                unsafe_allow_html=True,
            )

    # ── Recommendation ────────────────────────────────────────────────
    rec = results.get("recommendation", "no_action").replace("_", " ").title()
    rec_colors = {
        "Refund":              "#D4EDDA",
        "Additional Premium":  "#F8D7DA",
        "Clarification":       "#FFF3CD",
        "No Action":           "#E2E3E5",
    }
    bg = rec_colors.get(rec, "#E2E3E5")
    st.markdown(
        f"<div style='background:{bg}; padding:12px 16px; border-radius:8px; margin:1rem 0;'>"
        f"<strong>📌 Recommendation:</strong> {rec}</div>",
        unsafe_allow_html=True,
    )

    # ── Variance by Class Code table ──────────────────────────────────
    st.markdown('<div class="section-header">📋 Variance by Class Code</div>',
                unsafe_allow_html=True)

    if cc_lines:
        df_cc = pd.DataFrame([{
            "Policy #":         l.get("PolicyNumber", ""),
            "State":            l.get("StateCode", ""),
            "Class Code":       l.get("ClassCode", ""),
            "Earned Exposure":  l.get("earned_exposure",  0),
            "Earned Premium":   l.get("earned_premium",   0),
            "EST Exposure":     l.get("est_exposure",     0),
            "EST YTD Premium":  l.get("est_ytd_premium",  0),
            "Variance ($)":     l.get("variance",         0),
            "Variance (%)":     l.get("variance_pct",     0),
            "Root Cause":       l.get("root_cause", "").replace("_", " ").title(),
            "Flagged":          "⚠️ YES" if l.get("is_flagged") else "",
        } for l in cc_lines])

        def _flag_style(row):
            return ["background-color:#FFF3CD" if "YES" in str(row.get("Flagged", "")) else ""] * len(row)

        money_cols = ["Earned Exposure", "Earned Premium", "EST Exposure", "EST YTD Premium",
                      "Variance ($)"]
        pct_cols   = ["Variance (%)"]

        styled = (
            df_cc.style
            .apply(_flag_style, axis=1)
            .format({c: "${:,.2f}" for c in money_cols})
            .format({c: "{:+.2f}%" for c in pct_cols})
        )
        st.dataframe(styled, use_container_width=True, height=350)
    else:
        st.info("No class-code variance lines available.")

    # ── Findings ─────────────────────────────────────────────────────
    tabs = st.tabs(["👤 Officer Findings", "🏷️ Class Code Findings",
                    "📅 Frequency Findings", "📝 AI Narrative"])

    with tabs[0]:
        officer_f = results.get("officer_findings", [])
        if officer_f:
            for f in officer_f:
                sev = f.get("severity", "info")
                icon = "🔴" if sev == "critical" else "🟡"
                st.markdown(f"{icon} **{f.get('officer_name', '')}**: {f.get('description', '')}")
        else:
            st.success("✅ No officer misclassifications detected.")

    with tabs[1]:
        cc_f = results.get("class_code_findings", [])
        if cc_f:
            for f in cc_f:
                sev  = f.get("severity", "info")
                icon = "🔴" if sev == "critical" else "🟡"
                st.markdown(
                    f"{icon} **CC {f.get('class_code', '')} / {f.get('state_code', '')}**: "
                    f"{f.get('description', '')}"
                )
        else:
            st.success("✅ No class code issues detected.")

    with tabs[2]:
        freq_f = results.get("frequency_findings", [])
        if freq_f:
            for f in freq_f:
                sev  = f.get("severity", "info")
                icon = "🔴" if sev == "critical" else "🟡"
                st.markdown(f"{icon} {f.get('description', '')}")
        else:
            st.success("✅ Submission frequency is within expected range.")

    with tabs[3]:
        narrative = results.get("ai_narrative", "")
        if narrative:
            st.markdown(f"""<div style="background:white; padding:20px; border-radius:8px;
                border-left:4px solid #1F4E79; font-size:15px; line-height:1.7;">
                {narrative.replace(chr(10), '<br/>')}
            </div>""", unsafe_allow_html=True)
        else:
            st.info("Narrative will appear after workflow completes.")

    # ── Report Download ───────────────────────────────────────────────
    st.markdown("---")
    if st.button("⬇️ Download Excel Report", type="primary"):
        try:
            r = requests.get(f"{API_BASE}/report/{case_id_input}/download", timeout=30)
            if r.status_code == 200:
                st.download_button(
                    label="📥 Save Report",
                    data=r.content,
                    file_name=f"WC_Audit_{case_id_input}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.warning("Report not yet available. Please wait for workflow to complete.")
        except Exception as exc:
            st.error(f"Download failed: {exc}")


# ─────────────────────────────────────────────
# Page: HITL Review
# ─────────────────────────────────────────────

elif nav == "👤 HITL Review":
    st.title("Human-in-the-Loop Review")
    st.markdown("*Review high-risk audits and apply manual overrides before finalisation.*")

    # Fetch pending reviews
    pending_data = api_get("/hitl/pending", default={"pending": []})
    pending      = pending_data.get("pending", [])

    if not pending:
        st.success("✅ No audits currently awaiting human review.")
        st.stop()

    st.markdown(f"**{len(pending)} audit(s) pending review**")

    for review in pending:
        case_id    = review.get("audit_case_id")
        policy_num = review.get("policy_number", "Unknown")
        risk       = review.get("risk_level", "high").lower()
        rec        = review.get("recommendation", "").replace("_", " ").title()
        overall    = review.get("overall_variance", {})

        st.markdown(
            f"<div class='hitl-panel'>"
            f"<h3>⚠️ Case {case_id} – Policy {policy_num}</h3>"
            f"<p>Risk: {risk_badge(risk)} &nbsp;|&nbsp; "
            f"Recommendation: <strong>{rec}</strong> &nbsp;|&nbsp; "
            f"Variance: <strong>{fmt_money(overall.get('variance', 0))}</strong> "
            f"({fmt_pct(overall.get('variance_pct', 0))})</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

        with st.expander(f"📋 Review Details – Case {case_id}", expanded=True):
            # Show variance breakdown
            cc_lines = review.get("class_code_variance", [])
            if cc_lines:
                st.markdown("**Variance by Class Code:**")
                df_cc = pd.DataFrame([{
                    "State":            l.get("StateCode"),
                    "Class Code":       l.get("ClassCode"),
                    "Earned Premium":   l.get("earned_premium", 0),
                    "EST YTD Premium":  l.get("est_ytd_premium", 0),
                    "Variance":         l.get("variance", 0),
                    "Variance %":       l.get("variance_pct", 0),
                    "Root Cause":       l.get("root_cause", "").replace("_", " ").title(),
                } for l in cc_lines])
                st.dataframe(df_cc, use_container_width=True, height=200)

            # Officer issues
            officer_issues = review.get("officer_findings", [])
            if officer_issues:
                st.markdown("**⚠️ Officer Issues:**")
                for f in officer_issues:
                    st.error(f.get("description", ""))

            # Frequency issues
            freq_issues = review.get("frequency_issues", [])
            if freq_issues:
                st.markdown("**⚠️ Frequency Issues:**")
                for f in freq_issues:
                    st.warning(f.get("description", ""))

            # Review form
            st.markdown("---")
            st.markdown("**Submit Your Review Decision:**")

            with st.form(key=f"hitl_form_{case_id}"):
                reviewer_id = st.text_input("Reviewer ID / Username *",
                                            key=f"rev_id_{case_id}")
                action = st.radio(
                    "Decision *",
                    ["approve", "reject", "override"],
                    horizontal=True,
                    key=f"action_{case_id}",
                )
                notes = st.text_area("Review Notes", height=100, key=f"notes_{case_id}")

                # Override section
                override_data = {}
                if action == "override":
                    st.markdown("**Override Values:**")
                    oc1, oc2 = st.columns(2)
                    with oc1:
                        new_rec = st.selectbox(
                            "Override Recommendation",
                            ["refund", "additional_premium", "clarification", "no_action"],
                            key=f"override_rec_{case_id}",
                        )
                        new_risk = st.selectbox(
                            "Override Risk Level",
                            ["low", "medium", "high"],
                            key=f"override_risk_{case_id}",
                        )
                    with oc2:
                        override_variance = st.number_input(
                            "Override Variance Amount ($)",
                            value=float(overall.get("variance", 0)),
                            key=f"override_var_{case_id}",
                        )
                        auditor_notes = st.text_area(
                            "Auditor Override Notes",
                            height=80,
                            key=f"aud_notes_{case_id}",
                        )
                    override_data = {
                        "recommendation":  new_rec,
                        "risk_level":      new_risk,
                        "overall_variance": {"variance": override_variance},
                        "auditor_notes":   auditor_notes,
                    }

                submit_btn = st.form_submit_button(
                    f"✅ Submit {action.title()} Decision",
                    type="primary",
                    use_container_width=True,
                )

            if submit_btn:
                if not reviewer_id:
                    st.error("Reviewer ID is required.")
                else:
                    payload = {
                        "action":        action,
                        "reviewer_id":   reviewer_id,
                        "notes":         notes,
                        "override_data": override_data if action == "override" else None,
                    }
                    resp, status = api_post(f"/hitl/{case_id}/resolve", data=payload)
                    if status == 200:
                        st.success(
                            f"✅ Decision submitted! Case {case_id} has been "
                            f"**{action}d** by {reviewer_id}. Workflow resuming."
                        )
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"Failed to submit review: {resp}")


# ─────────────────────────────────────────────
# Page: Reports
# ─────────────────────────────────────────────

elif nav == "📊 Reports":
    st.title("Audit Reports")
    st.markdown("*Download completed audit reports in Excel format.*")

    all_audits = api_get("/list?limit=100", default={"items": []})
    completed  = [
        i for i in all_audits.get("items", [])
        if i.get("status") in ("completed", "review")
    ]

    if not completed:
        st.info("No completed audits available yet.")
        st.stop()

    for item in reversed(completed):
        case_id    = item.get("audit_case_id")
        policy_num = item.get("policy_number", "—")
        res        = item.get("result") or {}
        ov         = res.get("overall_variance", {})

        col_a, col_b, col_c, col_d = st.columns([2, 2, 2, 1])
        with col_a:
            st.markdown(f"**Policy:** {policy_num}")
        with col_b:
            st.markdown(f"**Variance:** {fmt_money(ov.get('variance', 0))}")
        with col_c:
            st.markdown(f"**Risk:** {res.get('risk_level', '—').upper()}")
        with col_d:
            dl_url = f"{API_BASE}/report/{case_id}/download"
            st.markdown(
                f"<a href='{dl_url}' target='_blank'>"
                f"<button style='background:#1F4E79;color:white;border:none;"
                f"padding:6px 14px;border-radius:5px;cursor:pointer;'>⬇️ Download</button>"
                f"</a>",
                unsafe_allow_html=True,
            )
        st.divider()


# ─────────────────────────────────────────────
# Page: Settings
# ─────────────────────────────────────────────

elif nav == "⚙️ Settings":
    st.title("Platform Settings")

    st.markdown('<div class="section-header">🔌 API Configuration</div>',
                unsafe_allow_html=True)
    st.code(f"API Base URL: {API_BASE}")

    st.markdown('<div class="section-header">🤖 LangGraph Workflow</div>',
                unsafe_allow_html=True)
    st.markdown("""
| Node | Role | Type |
|------|------|------|
| `parse_payroll_excel` | Ingest Excel payroll data | Deterministic |
| `parse_policy_xml` | Ingest policy XML config | Deterministic |
| `parse_audit_metadata` | Ingest check dates & submission count | Deterministic |
| `officer_agent` | Detect officer misclassification | Deterministic |
| `class_code_agent` | Validate class code assignment | Deterministic |
| `frequency_agent` | Detect missing submission periods | Deterministic |
| `calculate_variance` | Compute earned vs EST premium | Deterministic ✅ |
| `assess_risk` | Assign risk level & recommendation | Deterministic ✅ |
| `hitl_checkpoint` | Pause for human review (AG-UI) | HITL 👤 |
| `explanation_agent` | Generate audit narrative | AI (Claude) 🤖 |
| `generate_report` | Create Excel report | Deterministic |
| `persist_to_database` | Save to PostgreSQL | Deterministic |
    """)

    st.markdown('<div class="section-header">🔑 Environment Variables</div>',
                unsafe_allow_html=True)
    st.code("""
ANTHROPIC_API_KEY=sk-ant-...       # For AI narrative generation
WC_AUDIT_API_BASE=http://localhost:8000/api/v1/wc-audit
HITL_TIMEOUT_MINUTES=60
REPORT_OUTPUT_DIR=/tmp/wc_audit_reports
UPLOAD_DIR=/tmp/wc_audit_uploads
DB_URL=postgresql://user:pass@localhost:5432/agentic
    """)

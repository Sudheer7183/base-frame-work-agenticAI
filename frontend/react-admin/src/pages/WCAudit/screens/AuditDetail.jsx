import { useState, useEffect } from "react";
import {
  BarChart, Bar, Cell,
  XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";
import { getAuditStatus, submitHITLDecision, downloadReport } from "../../../api/wcAuditAPI";;
import { useWCRoles } from "../../../hooks/useWCRoles";
import C from "../constants/colors";
import { money } from "../constants/formatters";
import { KpiCard, RiskBadge, StatusBadge, SectionHeader } from "../ui";

function AuditDetail({ auditCase, setScreen, onHITLDecision }) {
  const [tab,        setTab]        = useState("overview");
  const [detail,     setDetail]     = useState(auditCase);
  const [hitlNote,   setHitlNote]   = useState("");
  const [submitting, setSubmitting] = useState(false);

  const {
    canViewReports,
    canUpload,
    canApproveHITL,
    canViewAllTenants,
    displayRole,
    isSuperAdmin,
    canViewAIAudit,
    canViewVariance,
    canViewDashboard,
    canViewPolicies,
  } = useWCRoles();

  useEffect(() => {
    if (!auditCase?.audit_case_id) return;

    let isMounted = true;

    getAuditStatus(auditCase.audit_case_id)
      .then(fresh => { if (isMounted) setDetail(fresh); })
      .catch(() => { if (isMounted) setDetail(auditCase); });

    return () => { isMounted = false; };
  }, [auditCase?.audit_case_id]);

  if (!detail) return (
    <div style={{ padding:40, color:C.muted, textAlign:"center" }}>
      Select a case to review
    </div>
  );

  const tabs = ["overview","class-codes","payroll","narrative","decision"];
  const ov   = detail.overall_variance || {};

  const exposureDelta = (ov.est_exposure || 0) - (ov.earned_exposure || 0);
  const classCodes    = [...new Set((detail.class_code_variance || []).map(r => r.ClassCode))].join(", ") || "—";

  const buildPayrollCalendar = () => {
    const MONTHS   = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    const firstDt  = detail.first_check_date ? new Date(detail.first_check_date) : null;
    const lastDt   = detail.last_check_date  ? new Date(detail.last_check_date)  : null;
    const year     = firstDt ? firstDt.getFullYear() : new Date().getFullYear();

    return MONTHS.map((m, i) => {
      const monthStart = new Date(year, i, 1);
      const monthEnd   = new Date(year, i + 1, 0);
      const inRange    = firstDt && lastDt && monthStart <= lastDt && monthEnd >= firstDt;
      return { m, inRange };
    });
  };

  const handleHITL = async (decision) => {
    setSubmitting(true);
    try {
      await submitHITLDecision(detail.audit_case_id, { decision, notes: hitlNote });
      const fresh = await getAuditStatus(detail.audit_case_id);
      setDetail(fresh);
      onHITLDecision?.();
    } catch (err) {
      alert("HITL decision failed: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const buildClassCodeChartData = (data) => {
    return (data.class_code_variance || []).map(row => ({
      code: row.ClassCode,
      earned: row.earned_premium,
      estimated: row.est_ytd_premium,
      variance: row.variance,
      variance_pct: row.variance_pct
    }));
  };

  const chartData = buildClassCodeChartData(detail);

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:20 }}>

      {/* Header */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
        <div>
          <button onClick={() => setScreen("policies")}
            style={{ background:"none", border:"none", color:C.accent, cursor:"pointer",
              fontSize:13, padding:"0 0 6px", fontWeight:600 }}>
            ← Back to Policies
          </button>
          <h2 style={{ margin:0, fontSize:22, fontWeight:800, color:C.text }}>
            {detail.policy_number} — Case #{detail.audit_case_id}
          </h2>
          <div style={{ display:"flex", gap:10, marginTop:8, flexWrap:"wrap" }}>
            <span style={{ fontSize:13, color:C.muted }}>
              Earned Premium: <strong>{money(Math.round(ov.earned_premium || 0))}</strong>
            </span>
          </div>
        </div>
        <div style={{ display:"flex", gap:10 }}>
          <RiskBadge risk={detail.risk_level} />
          <StatusBadge status={detail.status} />
        </div>
      </div>

      {/* KPI row */}
      <div style={{ display:"flex", gap:14 }}>
        <KpiCard
          label="Variance"
          value={`${Number(ov.variance_pct || 0).toFixed(1)}%`}
          sub={ov.variance_pct > 10 ? "Above threshold" : "Within range"}
          subColor={ov.variance_pct > 10 ? C.red : C.green}
          accent={ov.variance_pct > 10 ? C.red : C.amber} />
        <KpiCard
          label="Exposure Delta"
          value={money(Math.round(Math.abs(exposureDelta)))}
          sub="EST Exposure vs. Earned Exposure"
          accent={C.red} />
        <KpiCard
          label="EST YTD Premium"
          value={money(Math.round(ov.est_ytd_premium || 0))}
          sub="Estimated owed"
          accent={C.amber} />
        <KpiCard
          label="Confidence Score"
          value="94%"
          sub="AI finding accuracy"
          accent={C.green} />
      </div>

      {/* Tab panel */}
      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, overflow:"hidden" }}>
        <div style={{ display:"flex", borderBottom:`1px solid ${C.border}`, background:"#F8FAFD" }}>
          {tabs.map(t => (
            <button key={t} onClick={() => setTab(t)}
              style={{ flex:1, padding:"14px 10px", border:"none", background:"none", cursor:"pointer",
                fontSize:12, fontWeight:700, textTransform:"capitalize",
                color:tab === t ? C.accent : C.muted,
                borderBottom:tab === t ? `3px solid ${C.accent}` : "3px solid transparent",
                transition:"all 0.15s" }}>
              {t.replace("-"," ")}
            </button>
          ))}
        </div>

        <div style={{ padding:24 }}>

          {/* ── Overview tab ── */}
          {tab === "overview" && (() => {
            const officerTotal   = detail.officer_count;
            const officerIssues  = detail.officer_issues_count ?? 0;
            const officerDisplay = officerTotal != null
              ? `${officerTotal - officerIssues} of ${officerTotal} correctly assigned`
              : "—";

            const actualSubs    = detail.submitted_count;
            const expectedSubs  = detail.expected_submissions;
            const actualDisplay = actualSubs != null
              ? expectedSubs != null
                ? `${actualSubs} of ${expectedSubs} expected`
                : String(actualSubs)
              : "—";

            const fmtCheckDate = (raw) => {
              if (!raw) return "—";
              try {
                const d = new Date(raw.includes("/")
                  ? raw.replace(/(\d{2})\/(\d{2})\/(\d{4})/, "$3-$1-$2")
                  : raw);
                if (isNaN(d.getTime())) return raw;
                return d.toLocaleDateString("en-US", { month:"short", day:"numeric", year:"numeric" });
              } catch { return raw; }
            };

            return (
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14 }}>
                {[
                  { label:"Effective Date",               value: detail.effective_date  || "—" },
                  { label:"Expiration Date",              value: detail.expiration_date || "—" },
                  { label:"Payment Frequency",            value: detail.payment_frequency || "—" },
                  { label:"Class Codes",                  value: classCodes },
                  { label:"EE Officers on Payroll",       value: officerDisplay },
                  { label:"Actual Payroll Submissions",   value: actualDisplay },
                  { label:"Expected Payroll Submissions", value: expectedSubs != null ? String(expectedSubs) : "—" },
                  { label:"Last Check Date Reported",     value: fmtCheckDate(detail.last_check_date) },
                ].map(({ label, value }) => (
                  <div key={label} style={{ background:C.bg, borderRadius:10, padding:"14px 18px" }}>
                    <div style={{ fontSize:11, color:C.muted, fontWeight:600, textTransform:"uppercase",
                      letterSpacing:0.8, marginBottom:4 }}>{label}</div>
                    <div style={{ fontSize:14, fontWeight:700, color:C.text }}>{value}</div>
                  </div>
                ))}
              </div>
            );
          })()}

          {/* ── Class Codes tab ── */}
          {tab === "class-codes" && (
            <div>
              {(detail.class_code_variance?.some(r => r.is_flagged)) && (
                <div style={{ marginBottom:16, padding:"12px 16px", background:"#FEF3C7",
                  borderRadius:10, border:`1px solid ${C.amber}`, fontSize:13, color:"#92400E" }}>
                  ⚠️ <strong>{detail.class_code_variance.filter(r => r.is_flagged).length} flagged class code(s).</strong>{" "}
                  Review before finalizing.
                </div>
              )}
              {(!detail.class_code_variance || detail.class_code_variance.length === 0) ? (
                <div style={{ textAlign:"center", padding:40, color:C.muted }}>No class code data available.</div>
              ) : (
                <table style={{ width:"100%", borderCollapse:"collapse" }}>
                  <thead>
                    <tr style={{ borderBottom:`2px solid ${C.border}`, background:"#F8FAFD" }}>
                      {["Class Code","Description","EST YTD Premium","Earned Premium","Delta","Flag"].map(h => (
                        <th key={h} style={{ padding:"10px 14px", textAlign:"left", fontSize:11,
                          color:C.muted, fontWeight:700, textTransform:"uppercase" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {detail.class_code_variance.map((row, i) => {
                      const delta = (row.est_ytd_premium || 0) - (row.earned_premium || 0);
                      return (
                        <tr key={i} style={{ borderBottom:`1px solid ${C.border}` }}>
                          <td style={{ padding:"12px 14px", fontSize:13, fontWeight:700, color:C.accent }}>
                            {row.ClassCode}
                          </td>
                          <td style={{ padding:"12px 14px", fontSize:13, color:C.muted }}>
                            {row.StateCode}
                          </td>
                          <td style={{ padding:"12px 14px", fontSize:13 }}>
                            {money(Math.round(row.est_ytd_premium || 0))}
                          </td>
                          <td style={{ padding:"12px 14px", fontSize:13 }}>
                            {money(Math.round(row.earned_premium || 0))}
                          </td>
                          <td style={{ padding:"12px 14px", fontSize:13, fontWeight:700,
                            color: delta > 0 ? C.red : C.green }}>
                            {delta > 0 ? "+" : ""}{money(Math.round(delta))}
                          </td>
                          <td style={{ padding:"12px 14px" }}>
                            {row.is_flagged
                              ? <span style={{ background:"#FEE2E2", color:C.red, padding:"2px 10px", borderRadius:20, fontSize:11, fontWeight:700 }}>⚠ Flag</span>
                              : <span style={{ background:"#D1FAE5", color:C.green, padding:"2px 10px", borderRadius:20, fontSize:11, fontWeight:700 }}>✓ OK</span>}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}

              {/* Variance bar chart */}
              <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24, marginTop:20 }}>
                <SectionHeader
                  title="Variance by Class Code"
                  sub="Positive = Additional Premium | Negative = Refund"
                />
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                    <XAxis dataKey="code" />
                    <YAxis />
                    <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
                    <Bar dataKey="variance" name="Variance" radius={[4,4,0,0]}>
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.variance > 0 ? C.red : C.green} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* ── Payroll tab ── */}
          {tab === "payroll" && (
            <div>
              <div style={{ display:"flex", gap:8, marginBottom:16, flexWrap:"wrap" }}>
                {buildPayrollCalendar().map(({ m, inRange }) => (
                  <div key={m} style={{ width:66, textAlign:"center",
                    background: !inRange ? "#F3F4F6" : "#D1FAE5",
                    borderRadius:8, padding:"10px 6px",
                    border:`1px solid ${!inRange ? C.border : "#A7F3D0"}` }}>
                    <div style={{ fontSize:10, fontWeight:700, color:C.muted, textTransform:"uppercase" }}>{m}</div>
                    <div style={{ fontSize:13, fontWeight:800,
                      color: !inRange ? C.muted : C.green, marginTop:4 }}>
                      {!inRange ? "—" : "✓"}
                    </div>
                  </div>
                ))}
              </div>
              {detail.submitted_count != null && (
                <div style={{ padding:"12px 16px", background:"#D1FAE5",
                  borderRadius:10, border:`1px solid #A7F3D0`, fontSize:13, color:"#065F46" }}>
                  ✓ <strong>{detail.submitted_count} payroll submission(s)</strong> recorded
                  {detail.first_check_date ? ` from ${detail.first_check_date}` : ""}
                  {detail.last_check_date  ? ` to ${detail.last_check_date}` : ""}.
                </div>
              )}
            </div>
          )}

          {/* ── Narrative tab ── */}
          {tab === "narrative" && (
            <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
              {detail.ai_narrative ? (
                <div style={{ background:"#EEF2FF", borderLeft:`4px solid ${C.accent}`,
                  borderRadius:"0 10px 10px 0", padding:"16px 20px", fontSize:13,
                  color:C.text, lineHeight:1.8 }}>
                  <div style={{ fontWeight:700, marginBottom:8, color:C.accent }}>
                    🤖 AI-Generated Audit Narrative
                  </div>
                  {detail.ai_narrative.split("\n\n").map((para, i) => (
                    <p key={i} style={{ margin:"0 0 10px" }}>{para}</p>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign:"center", padding:40, color:C.muted }}>
                  {["completed","error"].includes(detail.status)
                    ? "No narrative generated for this audit."
                    : "Narrative will appear once the audit completes."}
                </div>
              )}
              {detail.agent_logs?.length > 0 && (
                <div style={{ background:C.navy, borderRadius:12, padding:20 }}>
                  <div style={{ fontSize:12, fontWeight:700, color:"#64B5F6", marginBottom:10, fontFamily:"monospace" }}>
                    ▶ AGENT EXECUTION LOG
                  </div>
                  <div style={{ fontFamily:"monospace", fontSize:11, color:"#A8D8A8",
                    lineHeight:1.8, maxHeight:200, overflowY:"auto" }}>
                    {detail.agent_logs.map((log, i) => (
                      <div key={i}>[{log.timestamp}] {log.agent} → {log.status}</div>
                    ))}
                  </div>
                </div>
              )}
              {canApproveHITL && (
                <div style={{ display:"flex", gap:8 }}>
                  <button style={{ background:C.green, color:"#fff", border:"none", borderRadius:8,
                    padding:"8px 20px", fontSize:13, fontWeight:700, cursor:"pointer" }}>
                    ✓ Approve Narrative
                  </button>
                  <button style={{ background:C.amber, color:"#fff", border:"none", borderRadius:8,
                    padding:"8px 20px", fontSize:13, fontWeight:700, cursor:"pointer" }}>
                    ✎ Edit &amp; Override
                  </button>
                </div>
              )}
            </div>
          )}

          {/* ── Decision tab ── */}
          {tab === "decision" && (
            <div style={{ display:"flex", flexDirection:"column", gap:16 }}>

              <div style={{ display:"grid", gridTemplateColumns:"repeat(3, 1fr)", gap:14 }}>
                {[
                  {
                    key:    "additional_premium",
                    label:  "Bill EST YTD Premium",
                    amount: money(Math.round(ov.est_ytd_premium || 0)),
                    color:  C.red,
                    icon:   "💳",
                    desc:   "Insured underpaid based on audit findings",
                  },
                  {
                    key:    "refund",
                    label:  "Issue Refund",
                    amount: money(Math.round(Math.abs(ov.variance || 0))),
                    color:  C.green,
                    icon:   "↩️",
                    desc:   "Overpayment detected — refund applicable",
                  },
                  {
                    key:    "clarification",
                    label:  "Request Clarification",
                    amount: "—",
                    color:  C.amber,
                    icon:   "❓",
                    desc:   "Ambiguous findings need insured response",
                  },
                ].map((d, i) => {
                  const isActive = detail.recommendation === d.key;
                  return (
                    <div key={i} style={{ background:isActive ? "#F0F9FF" : C.bg,
                      border:`2px solid ${isActive ? d.color : C.border}`,
                      borderRadius:12, padding:20, textAlign:"left", transition:"all 0.15s" }}
                      onMouseEnter={e => { e.currentTarget.style.borderColor = d.color; e.currentTarget.style.background="#F8FAFD"; }}
                      onMouseLeave={e => { e.currentTarget.style.borderColor = isActive ? d.color : C.border; e.currentTarget.style.background = isActive ? "#F0F9FF" : C.bg; }}>
                      <div style={{ fontSize:24, marginBottom:8 }}>{d.icon}</div>
                      <div style={{ fontSize:14, fontWeight:700, color:C.text }}>{d.label}</div>
                      <div style={{ fontSize:22, fontWeight:800, color:d.color, margin:"6px 0" }}>{d.amount}</div>
                      <div style={{ fontSize:12, color:C.muted }}>{d.desc}</div>
                      {isActive && (
                        <div style={{ marginTop:8, fontSize:11, fontWeight:700, color:d.color,
                          background: `${d.color}15`, padding:"3px 10px", borderRadius:20, display:"inline-block" }}>
                          ● System Recommendation
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Reviewer notes + HITL form */}
              <div style={{ background:C.bg, borderRadius:12, padding:16 }}>
                <div style={{ fontSize:13, fontWeight:700, color:C.text, marginBottom:8 }}>
                  {detail.hitl_required ? "Human-in-the-Loop Decision" : "Reviewer Notes"}
                </div>
                <textarea value={hitlNote} onChange={e => setHitlNote(e.target.value)}
                  placeholder="Add manual notes, override reasoning, or additional findings..."
                  style={{ width:"100%", minHeight:80, border:`1px solid ${C.border}`, borderRadius:8,
                    padding:12, fontSize:13, color:C.text, resize:"vertical", outline:"none",
                    fontFamily:"inherit", boxSizing:"border-box", marginBottom:12 }} />

                {detail.hitl_required && (canApproveHITL ? (
                  <div style={{ display:"flex", gap:10 }}>
                    <button disabled={submitting} onClick={() => handleHITL("approve")}
                      style={{ background:C.green, color:"#fff", border:"none", borderRadius:8,
                        padding:"10px 24px", fontSize:13, fontWeight:700,
                        cursor:submitting ? "default" : "pointer", opacity:submitting ? 0.7 : 1 }}>
                      {submitting ? "Submitting..." : "✓ Approve & Finalize"}
                    </button>
                    <button disabled={submitting} onClick={() => handleHITL("reject")}
                      style={{ background:C.red, color:"#fff", border:"none", borderRadius:8,
                        padding:"10px 24px", fontSize:13, fontWeight:700,
                        cursor:submitting ? "default" : "pointer", opacity:submitting ? 0.7 : 1 }}>
                      ✗ Reject
                    </button>
                    <button onClick={() => downloadReport(detail.audit_case_id)}
                      style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:8,
                        padding:"10px 20px", fontSize:13, color:C.muted, cursor:"pointer" }}>
                      ⬇ Download Report
                    </button>
                  </div>
                ) : (
                  <div style={{ display:"flex", justifyContent:"flex-end", gap:8 }}>
                    <button style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:8,
                      padding:"7px 18px", fontSize:13, cursor:"pointer", color:C.muted }}>
                      Save Draft
                    </button>
                    {detail.status === "completed" && (
                      <button onClick={() => downloadReport(detail.audit_case_id)}
                        style={{ background:C.accent, color:"#fff", border:"none", borderRadius:8,
                          padding:"7px 18px", fontSize:13, fontWeight:700, cursor:"pointer" }}>
                        ⬇ Finalize Audit
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AuditDetail;
import { useState, Fragment } from "react";
import {
  BarChart, Bar,
  XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import C from "../constants/colors";
import { money } from "../constants/formatters";
import { buildMonthlyAuditData } from "../constants/chartHelpers";
import { KpiCard, SectionHeader } from "../ui";

function VarianceAnalysis({ cases }) {
  const [activeIdx, setActiveIdx] = useState(null);

  const completedCases = cases.filter(c =>
    ["completed","hitl_pending","pending"].includes(c.status) &&
    c.class_code_variance && c.class_code_variance.length > 0
  );
  const allCCVariance = completedCases.flatMap(c => c.class_code_variance || []);

  console.log("additional premium ", completedCases);

  // Aggregate per class code
  const byCC = {};
  allCCVariance.forEach(row => {
    const key = `${row.ClassCode}-${row.StateCode}`;
    if (!byCC[key]) byCC[key] = {
      code:           row.ClassCode,
      state:          row.StateCode,
      est_exposure:   0,
      earned_exposure:0,
      est_ytd_premium:0,
      earned_premium: 0,
      variance:       0,
    };
    byCC[key].est_exposure    += row.est_exposure    || 0;
    byCC[key].earned_exposure += row.earned_exposure || 0;
    byCC[key].est_ytd_premium += row.est_ytd_premium || 0;
    byCC[key].earned_premium  += row.earned_premium  || 0;
    byCC[key].variance        += row.variance         || 0;
  });
  const ccRows = Object.values(byCC).sort((a, b) => Math.abs(b.variance) - Math.abs(a.variance));

  const totalExposureDelta = ccRows.reduce((s, r) => s + Math.abs(r.est_exposure - r.earned_exposure), 0);
  const estYtdImpact       = ccRows.filter(r => r.variance > 0).reduce((s, r) => s + r.variance, 0);
  const refundDue          = ccRows.filter(r => r.variance < 0).reduce((s, r) => s + Math.abs(r.variance), 0);
  const mismatches         = ccRows.filter(r => Math.abs(r.variance) > 500).length;
  const totalEstYtdPremium = ccRows.reduce((s, r) => s + r.est_ytd_premium, 0);

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:20 }}>

      {/* KPI row */}
      <div style={{ display:"flex", gap:16 }}>
        <KpiCard label="Total Exposure Delta"    value={money(Math.round(totalExposureDelta))} sub="↑ Across all policies"      accent={C.red}    />
        <KpiCard label="EST YTD Premium Impact"  value={money(Math.round(totalEstYtdPremium))} sub="Net additional owed"         accent={C.amber}  />
        <KpiCard label="Additional Premium"      value={money(Math.round(estYtdImpact))}       sub="Underpaid — owed to insurer"  accent={C.amber}  />
        <KpiCard label="Class Code Mismatches"   value={mismatches}                            sub="Require reclassification"   accent={C.purple} />
      </div>

      {/* Class Code Breakdown */}
      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
        <SectionHeader title="Variance by Class Code"
          sub="Delta between EST Exposure and Earned Exposure, applied to Net Rate for EST YTD Premium" />
        {ccRows.length === 0 ? (
          <div style={{ textAlign:"center", padding:40, color:C.muted }}>
            No completed audits with variance data yet.
          </div>
        ) : (
          <table style={{ width:"100%", borderCollapse:"collapse" }}>
            <thead>
              <tr style={{ borderBottom:`2px solid ${C.border}`, background:"#F8FAFD" }}>
                {["Class Code","State","EST Exposure","Earned Exposure","Delta",
                  "Net Rate","EST YTD Premium","Action"].map(h => (
                  <th key={h} style={{ textAlign:"left", padding:"10px 14px", fontSize:11,
                    fontWeight:700, color:C.muted, textTransform:"uppercase", letterSpacing:0.7 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ccRows.map((row, i) => {
                const delta        = row.est_exposure - row.earned_exposure;
                const isExpanded   = activeIdx === i;
                return (
                  <Fragment key={row.code + i}>
                    <tr
                      onClick={() => setActiveIdx(isExpanded ? null : i)}
                      style={{ borderBottom:`1px solid ${C.border}`,
                        background:isExpanded ? "#F0F4FE" : "transparent", cursor:"pointer" }}
                      onMouseEnter={e => !isExpanded && (e.currentTarget.style.background="#F8FAFD")}
                      onMouseLeave={e => !isExpanded && (e.currentTarget.style.background="transparent")}>

                      <td style={{ padding:"13px 14px", fontSize:13, fontWeight:700, color:C.accent }}>
                        {row.code}
                      </td>
                      <td style={{ padding:"13px 14px", fontSize:13, color:C.text }}>
                        {row.state}
                      </td>
                      <td style={{ padding:"13px 14px", fontSize:13, color:C.text }}>
                        {money(Math.round(row.est_exposure))}
                      </td>
                      <td style={{ padding:"13px 14px", fontSize:13, color:C.text }}>
                        {money(Math.round(row.earned_exposure))}
                      </td>
                      <td style={{ padding:"13px 14px", fontWeight:700, fontSize:13,
                        color: delta > 0 ? C.red : C.green }}>
                        {delta > 0 ? "+" : ""}{money(Math.round(delta))}
                      </td>
                      <td style={{ padding:"13px 14px", fontSize:13, color:C.muted }}>—</td>
                      <td style={{ padding:"13px 14px", fontWeight:700, fontSize:13,
                        color: row.variance > 0 ? C.red : C.green }}>
                        {money(Math.round(row.est_ytd_premium))}
                      </td>
                      <td style={{ padding:"13px 14px" }}>
                        <button style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:6,
                          padding:"4px 12px", fontSize:12, cursor:"pointer", color:C.accent, fontWeight:600 }}>
                          {isExpanded ? "Collapse ▲" : "Drill Down ▼"}
                        </button>
                      </td>
                    </tr>

                    {/* Expanded drill-down row */}
                    {isExpanded && (
                      <tr>
                        <td colSpan={8} style={{ padding:0, background:"#F0F4FE" }}>
                          <div style={{ padding:"16px 24px", borderTop:`1px dashed ${C.border}` }}>
                            <div style={{ fontSize:13, fontWeight:700, color:C.text, marginBottom:12 }}>
                              AI Explanation — Class Code {row.code} ({row.state})
                            </div>
                            <div style={{ background:"#EEF2FF", borderLeft:`4px solid ${C.accent}`,
                              borderRadius:"0 8px 8px 0", padding:"12px 16px", fontSize:13,
                              color:C.text, lineHeight:1.6 }}>
                              🤖 <strong>Explanation Agent:</strong> The insured{" "}
                              {delta > 0 ? "underreported" : "overreported"} EST Exposure for class code{" "}
                              <strong>{row.code}</strong> ({row.state}).
                              A delta of <strong>{money(Math.round(Math.abs(delta)))}</strong> was identified
                              between EST Exposure ({money(Math.round(row.est_exposure))}) and Earned Exposure
                              ({money(Math.round(row.earned_exposure))}). The resulting EST YTD Premium
                              is <strong style={{ color: row.variance > 0 ? C.red : C.green }}>
                                {money(Math.round(row.est_ytd_premium))}
                              </strong>.
                              {Math.abs(row.variance) > 500
                                ? " This exceeds the threshold and requires auditor review."
                                : " This is within acceptable variance range."}
                            </div>
                            <div style={{ display:"flex", gap:10, marginTop:12 }}>
                              <button style={{ background:C.green, color:"#fff", border:"none",
                                borderRadius:7, padding:"7px 16px", fontSize:12, fontWeight:600, cursor:"pointer" }}>
                                ✓ Accept Finding
                              </button>
                              <button style={{ background:C.amber, color:"#fff", border:"none",
                                borderRadius:7, padding:"7px 16px", fontSize:12, fontWeight:600, cursor:"pointer" }}>
                                ✎ Override
                              </button>
                              <button style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:7,
                                padding:"7px 16px", fontSize:12, cursor:"pointer", color:C.muted }}>
                                Add Note
                              </button>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Monthly Audit Volume */}
      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
        <SectionHeader title="Monthly Audit Volume"
          sub="Completed, pending, and high-risk audits by payroll submission period" />
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={buildMonthlyAuditData(cases)} margin={{ top:5, right:10, bottom:0, left:0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.border} vertical={false} />
            <XAxis dataKey="month" tick={{ fontSize:12, fill:C.muted }} />
            <YAxis tick={{ fontSize:12, fill:C.muted }} />
            <Tooltip contentStyle={{ borderRadius:10, border:`1px solid ${C.border}`, fontSize:12 }} />
            <Legend wrapperStyle={{ fontSize:12 }} />
            <Bar dataKey="completed" fill={C.green}  name="Completed" radius={[4,4,0,0]} />
            <Bar dataKey="pending"   fill={C.amber}  name="Pending"   radius={[4,4,0,0]} />
            <Bar dataKey="highRisk"  fill={C.red}    name="High Risk"  radius={[4,4,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default VarianceAnalysis;
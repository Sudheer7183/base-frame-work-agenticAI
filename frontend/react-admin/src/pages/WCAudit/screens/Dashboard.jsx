import { useState } from "react";
import {
  AreaChart, Area,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";

import C from "../constants/colors";
import { fmt } from "../constants/formatters";
import { buildVarianceTrendData } from "../constants/chartHelpers";
import { KpiCard, SectionHeader, StatusBadge } from "../ui";

function Dashboard({ setScreen, setSelectedCase, cases }) {
  const [hovered, setHovered] = useState(null);
  console.log("intial cases data", cases);

  const high    = cases.filter(c => c.risk_level === "high").length;
  const done    = cases.filter(c => c.status === "completed").length;

  const refunds = cases
    .filter(c => c.variance < 0)
    .reduce((s, c) => s + Math.abs(c.variance || 0), 0);

  const additionalPremium = cases
    .filter(c => c.variance > 0)
    .reduce((s, c) => s + (c.variance || 0), 0);

  const totalEarnedPremium  = cases.reduce((sum, c) => sum + (c.overall_variance?.earned_premium  || 0), 0);
  const totalEstYTDPremium  = cases.reduce((sum, c) => sum + (c.overall_variance?.est_ytd_premium || 0), 0);

  // AI Insights derived from live data
  const highVarianceCases   = cases.filter(c => Math.abs(c.variance_pct) > 25).length;
  console.log("cases variance perecntage more than 20", cases.filter(c => (Math.abs(c.variance_pct) > 20)));

  const additionalPremCases = cases.filter(c => c.recommendation === "additional_premium").length;
  const pendingCases        = cases.filter(c => ["pending","running"].includes(c.status)).length;
  const hitlPending         = cases.filter(c => c.hitl_required && c.status !== "completed").length;
  const autoResolved        = cases.length > 0 ? Math.round((done / cases.length) * 100) : 0;

  const riskData = [
    { name:"Low Risk",  value: cases.filter(c => c.risk_level === "low").length,    color:C.green },
    { name:"Medium",    value: cases.filter(c => c.risk_level === "medium").length, color:C.amber },
    { name:"High Risk", value: high,                                                  color:C.red   },
  ];

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:24 }}>

      {/* KPI row */}
      <div style={{ display:"flex", gap:16, flexWrap:"wrap" }}>
        <KpiCard label="Total Policies"  value={cases.length}             sub="↑ All time"               accent={C.accent} icon="📋" />
        <KpiCard label="EST YTD Premium" value={fmt(totalEstYTDPremium)}  sub="↑ Estimated total"        accent={C.amber}  icon="💰" />
        <KpiCard label="Earned Premium"  value={fmt(totalEarnedPremium)}  sub="↑ Actual reported"        accent={C.amber}  icon="💰" />
        <KpiCard label="Refunds"         value={fmt(refunds)}             accent={C.green} icon="↩️" />
        <KpiCard label="Adittional Premium" value={fmt(additionalPremium)} accent={C.green} icon="↪️" />
      </div>

      {/* Charts row */}
      <div style={{ display:"flex", gap:16 }}>
        <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24, flex:2 }}>
          <SectionHeader title="Variance Trend"
            sub="Month-over-Month — Earned Premium vs. EST YTD Premium" />
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={buildVarianceTrendData(cases)} margin={{ top:5, right:10, bottom:0, left:0 }}>
              <defs>
                <linearGradient id="gV" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={C.accent} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={C.accent} stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="gP" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={C.teal} stopOpacity={0.2}/>
                  <stop offset="95%" stopColor={C.teal} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
              <XAxis dataKey="date" tick={{ fontSize:11, fill:C.muted }} />
              <YAxis tickFormatter={v => `$${v/1000}K`} tick={{ fontSize:11, fill:C.muted }} width={55} />
              <Tooltip formatter={v => [`$${(v/1000).toFixed(0)}K`]}
                contentStyle={{ borderRadius:10, border:`1px solid ${C.border}`, fontSize:12 }} />
              <Area type="monotone" dataKey="variance" stroke={C.accent} strokeWidth={2.5} fill="url(#gV)" name="Variance" />
              <Area type="monotone" dataKey="premium"  stroke={C.teal}   strokeWidth={2}   fill="url(#gP)" name="Earned Premium" strokeDasharray="5 3" />
              <Legend wrapperStyle={{ fontSize:12 }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24, flex:1, minWidth:220 }}>
          <SectionHeader title="Policy Risk Distribution" />
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie data={riskData} cx="50%" cy="50%" innerRadius={45} outerRadius={70}
                paddingAngle={3} dataKey="value">
                {riskData.map((d, i) => <Cell key={i} fill={d.color} />)}
              </Pie>
              <Tooltip contentStyle={{ borderRadius:10, fontSize:12 }} />
            </PieChart>
          </ResponsiveContainer>
          <div style={{ display:"flex", flexDirection:"column", gap:8, marginTop:4 }}>
            {riskData.map((d, i) => (
              <div key={i} style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                  <div style={{ width:10, height:10, borderRadius:"50%", background:d.color }} />
                  <span style={{ fontSize:12, color:C.muted }}>{d.name}</span>
                </div>
                <span style={{ fontSize:13, fontWeight:700, color:C.text }}>{d.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom row: Top Policies + AI Insights */}
      <div style={{ display:"flex", gap:16 }}>

        {/* Top Policies */}
        <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24, flex:3 }}>
          <SectionHeader title="Top Policies Requiring Review"
            sub="Sorted by variance severity" action="View All"
            onAction={() => setScreen("policies")} />
          {cases.length === 0 ? (
            <div style={{ textAlign:"center", padding:40, color:C.muted, fontSize:14 }}>
              No audits yet. Start one via Data Upload →
            </div>
          ) : (
            <table style={{ width:"100%", borderCollapse:"collapse" }}>
              <thead>
                <tr style={{ borderBottom:`2px solid ${C.border}` }}>
                  {["Policy Number","Insured Name","St.","Variance","Earned Premium","Status","Action"].map(h => (
                    <th key={h} style={{ textAlign:"left", padding:"8px 12px", fontSize:11,
                      fontWeight:700, color:C.muted, textTransform:"uppercase", letterSpacing:0.8 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {cases.slice(0, 5).map((c, i) => (
                  <tr key={c.audit_case_id}
                    onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)}
                    style={{ background:hovered === i ? "#F5F8FF" : "transparent",
                      transition:"background 0.15s", borderBottom:`1px solid ${C.border}` }}>
                    <td style={{ padding:"12px 12px", fontSize:13, fontWeight:700, color:C.accent,
                      cursor:"pointer" }}
                      onClick={() => { setSelectedCase(c); setScreen("audit-detail"); }}>
                      {c.policy_number}
                    </td>
                    <td style={{ padding:"12px 12px", fontSize:13, color:C.muted }}>{c.insured_name}</td>
                    <td style={{ padding:"12px 12px", fontSize:13, fontWeight:700, color:C.muted }}>{c.class_code_variance[0]?.StateCode}</td>
                    <td style={{ padding:"12px 12px", fontWeight:700, fontSize:13,
                      color:(c.variance_pct || 0) > 20 ? C.red : (c.variance_pct || 0) > 10 ? C.amber : C.green }}>
                      {c.variance_pct != null ? `${Number(c.variance_pct).toFixed(1)}%` : "—"}
                    </td>
                    <td style={{ padding:"12px 12px", fontSize:13, fontWeight:600, color:C.text }}>
                      {fmt(c.overall_variance?.earned_premium)}
                    </td>
                    <td style={{ padding:"12px 12px" }}><StatusBadge status={c.status} /></td>
                    <td style={{ padding:"12px 12px" }}>
                      <button onClick={() => { setSelectedCase(c); setScreen("audit-detail"); }}
                        style={{ background:C.accent, color:"#fff", border:"none", borderRadius:7,
                          padding:"5px 14px", fontSize:12, fontWeight:600, cursor:"pointer" }}>
                        Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* AI Insights */}
        <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24, flex:1, minWidth:220 }}>
          <SectionHeader title="AI Insights" />
          <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
            {[
              { icon:"📊", label:`${highVarianceCases} High Variance`,
                sub:"Above 25% threshold", color:C.purple, screen:"variance" },
              { icon:"💳", label:`${additionalPremCases} Additional Premium`,
                sub:"EST YTD premium owed", color:C.red, screen:"variance" },
              { icon:"📅", label:`${pendingCases} Pending Submissions`,
                sub:"Awaiting processing", color:C.accent, screen:"policies" },
              { icon:"⚠️", label:`${hitlPending} HITL Reviews`,
                sub:"Awaiting auditor action", color:C.amber, screen:"ai-audit" },
              { icon:"✅", label:`${autoResolved}% Auto-resolved`,
                sub:"No human review needed", color:C.green, screen:"policies" },
            ].map((item, i) => (
              <div key={i} onClick={() => setScreen(item.screen)}
                style={{ display:"flex", alignItems:"center", gap:12, padding:"10px 14px",
                  borderRadius:10, background:C.bg, cursor:"pointer", transition:"all 0.15s" }}
                onMouseEnter={e => e.currentTarget.style.background = "#E8F0FE"}
                onMouseLeave={e => e.currentTarget.style.background = C.bg}>
                <span style={{ fontSize:20 }}>{item.icon}</span>
                <div style={{ flex:1 }}>
                  <div style={{ fontSize:13, fontWeight:700, color:item.color }}>{item.label}</div>
                  <div style={{ fontSize:11, color:C.muted }}>{item.sub}</div>
                </div>
                <span style={{ color:C.muted, fontSize:14 }}>›</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
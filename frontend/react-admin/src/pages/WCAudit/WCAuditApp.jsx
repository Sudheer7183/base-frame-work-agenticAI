


// import { useState, useEffect, useRef, useCallback, Fragment } from "react";
// import {
//   AreaChart, Area, BarChart, Bar,
//   PieChart, Pie, Cell,
//   XAxis, YAxis, CartesianGrid,
//   Tooltip, Legend, ResponsiveContainer,
// } from "recharts";
// import {
//   uploadAuditFiles,
//   startAudit,
//   listAuditCases,
//   getAuditStatus,
//   pollAuditStatus,
//   submitHITLDecision,
//   downloadReport,
//   startBatchAuditFromAPI,
//   clearAllAuditData,
//   getAuditConfig,
//   updateAuditConfig,
//   previewAPIPolicies
// } from "../../api/wcAuditAPI";
 

// import { useWCRoles } from "../../hooks/useWCRoles";

// // ── Color Palette ─────────────────────────────────────────────────────────────
// const C = {
//   navy:    "#0D1B2A",
//   navyMid: "#132338",
//   navyLt:  "#1A3050",
//   accent:  "#1E6FD9",
//   accentLt:"#3D8FFF",
//   teal:    "#0ABFBC",
//   amber:   "#F59E0B",
//   red:     "#EF4444",
//   green:   "#10B981",
//   purple:  "#7C3AED",
//   bg:      "#F0F4FA",
//   card:    "#FFFFFF",
//   border:  "#E2EAF4",
//   text:    "#1A2B42",
//   muted:   "#6B7E99",
// };
 
// // ── Formatters ────────────────────────────────────────────────────────────────
// const fmt = (n) =>
//   n == null ? "—" :
//   n >= 1_000_000 ? `$${(n / 1_000_000).toFixed(1)}M` :
//   `$${(n / 1_000).toFixed(0)}K`;
// const pct   = (n) => `${n ?? 0}%`;
// const money = (n) => n == null ? "—" : `$${Number(n).toLocaleString()}`;

// function AccessDenied({ requiredRole }) {
//   return (
//     <div style={{ display:"flex", flexDirection:"column", alignItems:"center",
//       justifyContent:"center", height:300, gap:16, color:C.muted }}>
//       <span style={{ fontSize:48 }}>🔒</span>
//       <div style={{ textAlign:"center" }}>
//         <div style={{ fontSize:16, fontWeight:700, color:C.text, marginBottom:6 }}>
//           Access Restricted
//         </div>
//         <div style={{ fontSize:13 }}>
//           This section requires <strong>{requiredRole}</strong> access.
//           Contact your administrator to request the appropriate role.
//         </div>
//       </div>
//     </div>
//   );
// }
 
// // ── Shared Atoms ──────────────────────────────────────────────────────────────
// const RiskBadge = ({ risk }) => {
//   const map = {
//     high:   { bg:"#FEE2E2", color:"#DC2626", label:"High Risk" },
//     High:   { bg:"#FEE2E2", color:"#DC2626", label:"High Risk" },
//     medium: { bg:"#FEF3C7", color:"#D97706", label:"Medium" },
//     Medium: { bg:"#FEF3C7", color:"#D97706", label:"Medium" },
//     low:    { bg:"#D1FAE5", color:"#059669", label:"Low" },
//     Low:    { bg:"#D1FAE5", color:"#059669", label:"Low" },
//   };
//   const s = map[risk] || map.Low;
//   return (
//     <span style={{ background:s.bg, color:s.color, padding:"2px 10px",
//       borderRadius:20, fontSize:11, fontWeight:700, whiteSpace:"nowrap" }}>
//       {s.label}
//     </span>
//   );
// };
 
// const StatusBadge = ({ status }) => {
//   const map = {
//     "Under Review": { bg:"#EDE9FE", color:"#7C3AED" },
//     "Pending":       { bg:"#FEF9C3", color:"#B45309" },
//     "pending":       { bg:"#FEF9C3", color:"#B45309" },
//     "Completed":     { bg:"#DCFCE7", color:"#16A34A" },
//     "completed":     { bg:"#DCFCE7", color:"#16A34A" },
//     "In Progress":   { bg:"#DBEAFE", color:"#1D4ED8" },
//     "running":       { bg:"#DBEAFE", color:"#1D4ED8" },
//     "processing":    { bg:"#DBEAFE", color:"#1D4ED8" },
//     "error":         { bg:"#FEE2E2", color:"#DC2626" },
//     "hitl_pending":  { bg:"#EDE9FE", color:"#7C3AED" },
//     "rejected":      { bg:"#FEE2E2", color:"#DC2626" },
//   };
//   const s = map[status] || { bg:"#F3F4F6", color:"#374151" };
//   return (
//     <span style={{ background:s.bg, color:s.color, padding:"2px 10px",
//       borderRadius:20, fontSize:11, fontWeight:600 }}>
//       {status}
//     </span>
//   );
// };
 
// const KpiCard = ({ label, value, sub, subColor = "#10B981", icon, accent }) => (
//   <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14,
//     padding:"20px 24px", flex:1, minWidth:180, position:"relative", overflow:"hidden" }}>
//     <div style={{ position:"absolute", top:0, left:0, width:4, height:"100%",
//       background:accent || C.accent, borderRadius:"14px 0 0 14px" }} />
//     <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
//       <div>
//         <div style={{ fontSize:12, color:C.muted, fontWeight:600, textTransform:"uppercase",
//           letterSpacing:1, marginBottom:6 }}>{label}</div>
//         <div style={{ fontSize:28, fontWeight:800, color:C.text, lineHeight:1 }}>{value}</div>
//         {sub && <div style={{ fontSize:12, color:subColor, fontWeight:600, marginTop:6 }}>{sub}</div>}
//       </div>
//       {icon && <div style={{ fontSize:28, opacity:0.15, color:accent || C.accent }}>{icon}</div>}
//     </div>
//   </div>
// );
 
// const SectionHeader = ({ title, sub, action, onAction }) => (
//   <div style={{ display:"flex", justifyContent:"space-between",
//     alignItems:"center", marginBottom:18 }}>
//     <div>
//       <h2 style={{ margin:0, fontSize:18, fontWeight:700, color:C.text }}>{title}</h2>
//       {sub && <p style={{ margin:"4px 0 0", fontSize:13, color:C.muted }}>{sub}</p>}
//     </div>
//     {action && (
//       <button onClick={onAction} style={{ background:C.accent, color:"#fff", border:"none",
//         borderRadius:8, padding:"7px 16px", fontSize:13, fontWeight:600, cursor:"pointer" }}>
//         {action}
//       </button>
//     )}
//   </div>
// );
 
// // ── Chart data helpers ────────────────────────────────────────────────────────
// function buildVarianceTrendData(cases) {
//   const byMonth = {};
//   cases
//     .filter(c => c.created_at && c.overall_variance?.earned_premium != null)
//     .forEach(c => {
//       const d = new Date(c.created_at);
//       // Sort key: "YYYY-MM" for correct chronological ordering
//       const key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
//       const label = d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
//       if (!byMonth[key]) byMonth[key] = { date: label, variance: 0, premium: 0, estPremium: 0, count: 0, _key: key };
//       byMonth[key].variance   += Math.abs(c.overall_variance?.variance || 0);
//       byMonth[key].premium    += c.overall_variance?.earned_premium || 0;
//       byMonth[key].estPremium += c.overall_variance?.est_premium || 0;
//       byMonth[key].count      += 1;
//     });
//   return Object.values(byMonth).sort((a, b) => a._key.localeCompare(b._key));
//   // No more slice(-10) — show all audit months
// }
// function buildMonthlyAuditData(cases) {
//   const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
//                   "Jul","Aug","Sep","Oct","Nov","Dec"];
//   const byMonth = {};
//   cases.forEach(c => {
//     if (!c.created_at) return;
//     const m = MONTHS[new Date(c.created_at).getMonth()];
//     if (!byMonth[m]) byMonth[m] = { month:m, completed:0, pending:0, highRisk:0 };
//     if (c.status === "completed" || c.status === "rejected") byMonth[m].completed += 1;
//     else if (["pending","processing","running","hitl_pending"].includes(c.status)) byMonth[m].pending += 1;
//     if (c.risk_level === "high") byMonth[m].highRisk += 1;
//   });
//   return MONTHS.filter(m => byMonth[m]).map(m => byMonth[m]);
// }
 
// // ═══════════════════════════════════════════════════════════════════════════════
// // SCREENS
// // ═══════════════════════════════════════════════════════════════════════════════
 
// // ── Dashboard ─────────────────────────────────────────────────────────────────
// function Dashboard({ setScreen, setSelectedCase, cases }) {
//   const [hovered, setHovered] = useState(null);
//   console.log("intial cases data",cases);
  
//   const high    = cases.filter(c => c.risk_level === "high").length;
//   const done    = cases.filter(c => c.status === "completed").length;
//   // const refunds = cases.filter(c => c.recommendation === "refund")
//   //                      .reduce((s, c) => s + Math.abs(c.variance || 0), 0);

//   const refunds = cases
//   .filter(c => c.variance < 0)
//   .reduce((s, c) => s + Math.abs(c.variance || 0), 0);

//   const additionalPremium = cases
//   .filter(c => c.variance > 0)
//   .reduce((s, c) => s + (c.variance || 0), 0);
 
//   const totalEarnedPremium  = cases.reduce((sum, c) => sum + (c.overall_variance?.earned_premium  || 0), 0);
//   const totalEstYTDPremium  = cases.reduce((sum, c) => sum + (c.overall_variance?.est_ytd_premium || 0), 0);
 
//   // AI Insights derived from live data
//   const highVarianceCases   = cases.filter(c => Math.abs(c.variance_pct) > 25).length;
//   console.log("cases variance perecntage more than 20", cases.filter(c=>(Math.abs(c.variance_pct)>20)));
  
//   const additionalPremCases = cases.filter(c => c.recommendation === "additional_premium").length;
//   const pendingCases        = cases.filter(c => ["pending","running"].includes(c.status)).length;
//   const hitlPending         = cases.filter(c => c.hitl_required && c.status !== "completed").length;
//   const autoResolved        = cases.length > 0 ? Math.round((done / cases.length) * 100) : 0;
 
//   const riskData = [
//     { name:"Low Risk",  value: cases.filter(c => c.risk_level === "low").length,    color:C.green },
//     { name:"Medium",    value: cases.filter(c => c.risk_level === "medium").length, color:C.amber },
//     { name:"High Risk", value: high,                                                  color:C.red   },
//   ];
 
//   return (
//     <div style={{ display:"flex", flexDirection:"column", gap:24 }}>
 
//       {/* KPI row */}
//       <div style={{ display:"flex", gap:16, flexWrap:"wrap" }}>
//         <KpiCard label="Total Policies"  value={cases.length}             sub="↑ All time"               accent={C.accent} icon="📋" />
//                 <KpiCard label="EST YTD Premium" value={fmt(totalEstYTDPremium)}  sub="↑ Estimated total"        accent={C.amber}  icon="💰" />
//         <KpiCard label="Earned Premium"  value={fmt(totalEarnedPremium)}  sub="↑ Actual reported"        accent={C.amber}  icon="💰" />

//         <KpiCard label="Refunds"  value={fmt(refunds)}              accent={C.green} icon="↩️" />
//         <KpiCard label="Adittional Premium"  value={fmt(additionalPremium)}              accent={C.green} icon="↪️" />
//       </div>
 
//       {/* Charts row */}
//       <div style={{ display:"flex", gap:16 }}>
//         <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24, flex:2 }}>
//           <SectionHeader title="Variance Trend"
//             sub="Month-over-Month — Earned Premium vs. EST YTD Premium" />
//           <ResponsiveContainer width="100%" height={200}>
//             <AreaChart data={buildVarianceTrendData(cases)} margin={{ top:5, right:10, bottom:0, left:0 }}>
//               <defs>
//                 <linearGradient id="gV" x1="0" y1="0" x2="0" y2="1">
//                   <stop offset="5%"  stopColor={C.accent} stopOpacity={0.3}/>
//                   <stop offset="95%" stopColor={C.accent} stopOpacity={0}/>
//                 </linearGradient>
//                 <linearGradient id="gP" x1="0" y1="0" x2="0" y2="1">
//                   <stop offset="5%"  stopColor={C.teal} stopOpacity={0.2}/>
//                   <stop offset="95%" stopColor={C.teal} stopOpacity={0}/>
//                 </linearGradient>
//               </defs>
//               <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
//               <XAxis dataKey="date" tick={{ fontSize:11, fill:C.muted }} />
//               <YAxis tickFormatter={v => `$${v/1000}K`} tick={{ fontSize:11, fill:C.muted }} width={55} />
//               <Tooltip formatter={v => [`$${(v/1000).toFixed(0)}K`]}
//                 contentStyle={{ borderRadius:10, border:`1px solid ${C.border}`, fontSize:12 }} />
//               <Area type="monotone" dataKey="variance" stroke={C.accent} strokeWidth={2.5} fill="url(#gV)" name="Variance" />
//               <Area type="monotone" dataKey="premium"  stroke={C.teal}   strokeWidth={2}   fill="url(#gP)" name="Earned Premium" strokeDasharray="5 3" />
//               <Legend wrapperStyle={{ fontSize:12 }} />
//             </AreaChart>
//           </ResponsiveContainer>
//         </div>
 
//         <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24, flex:1, minWidth:220 }}>
//           <SectionHeader title="Policy Risk Distribution" />
//           <ResponsiveContainer width="100%" height={160}>
//             <PieChart>
//               <Pie data={riskData} cx="50%" cy="50%" innerRadius={45} outerRadius={70}
//                 paddingAngle={3} dataKey="value">
//                 {riskData.map((d, i) => <Cell key={i} fill={d.color} />)}
//               </Pie>
//               <Tooltip contentStyle={{ borderRadius:10, fontSize:12 }} />
//             </PieChart>
//           </ResponsiveContainer>
//           <div style={{ display:"flex", flexDirection:"column", gap:8, marginTop:4 }}>
//             {riskData.map((d, i) => (
//               <div key={i} style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
//                 <div style={{ display:"flex", alignItems:"center", gap:8 }}>
//                   <div style={{ width:10, height:10, borderRadius:"50%", background:d.color }} />
//                   <span style={{ fontSize:12, color:C.muted }}>{d.name}</span>
//                 </div>
//                 <span style={{ fontSize:13, fontWeight:700, color:C.text }}>{d.value}</span>
//               </div>
//             ))}
//           </div>
//         </div>
//       </div>
 
//       {/* Bottom row: Top Policies + AI Insights */}
//       <div style={{ display:"flex", gap:16 }}>
 
//         {/* Top Policies */}
//         <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24, flex:3 }}>
//           <SectionHeader title="Top Policies Requiring Review"
//             sub="Sorted by variance severity" action="View All"
//             onAction={() => setScreen("policies")} />
//           {cases.length === 0 ? (
//             <div style={{ textAlign:"center", padding:40, color:C.muted, fontSize:14 }}>
//               No audits yet. Start one via Data Upload →
//             </div>
//           ) : (
//             <table style={{ width:"100%", borderCollapse:"collapse" }}>
//               <thead>
//                 <tr style={{ borderBottom:`2px solid ${C.border}` }}>
//                   {["Policy Number","Insured Name","St.","Variance","Earned Premium","Status","Action"].map(h => (
//                     <th key={h} style={{ textAlign:"left", padding:"8px 12px", fontSize:11,
//                       fontWeight:700, color:C.muted, textTransform:"uppercase", letterSpacing:0.8 }}>{h}</th>
//                   ))}
//                 </tr>
//               </thead>
//               <tbody>
//                 {cases.slice(0, 5).map((c, i) => (
//                   <tr key={c.audit_case_id}
//                     onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)}
//                     style={{ background:hovered === i ? "#F5F8FF" : "transparent",
//                       transition:"background 0.15s", borderBottom:`1px solid ${C.border}` }}>
//                     <td style={{ padding:"12px 12px", fontSize:13, fontWeight:700, color:C.accent,
//                       cursor:"pointer" }}
//                       onClick={() => { setSelectedCase(c); setScreen("audit-detail"); }}>
//                       {c.policy_number}
//                     </td>
//                     <td style={{ padding:"12px 12px", fontSize:13, color:C.muted }}>{c.insured_name}</td>
//                     <td style={{ padding:"12px 12px", fontSize:13, fontWeight:700, color:C.muted }}>{c.class_code_variance[0]?.StateCode}</td>
//                     <td style={{ padding:"12px 12px", fontWeight:700, fontSize:13,
//                       color:(c.variance_pct || 0) > 20 ? C.red : (c.variance_pct || 0) > 10 ? C.amber : C.green }}>
//                       {c.variance_pct != null ? `${Number(c.variance_pct).toFixed(1)}%` : "—"}
//                     </td>
//                     <td style={{ padding:"12px 12px", fontSize:13, fontWeight:600, color:C.text }}>
//                       {fmt(c.overall_variance?.earned_premium)}
//                     </td>
//                     <td style={{ padding:"12px 12px" }}><StatusBadge status={c.status} /></td>
//                     <td style={{ padding:"12px 12px" }}>
//                       <button onClick={() => { setSelectedCase(c); setScreen("audit-detail"); }}
//                         style={{ background:C.accent, color:"#fff", border:"none", borderRadius:7,
//                           padding:"5px 14px", fontSize:12, fontWeight:600, cursor:"pointer" }}>
//                         Review
//                       </button>
//                     </td>
//                   </tr>
//                 ))}
//               </tbody>
//             </table>
//           )}
//         </div>
 
//         {/* AI Insights */}
//         <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24, flex:1, minWidth:220 }}>
//           <SectionHeader title="AI Insights" />
//           <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
//             {[
//               { icon:"📊", label:`${highVarianceCases} High Variance`,
//                 sub:"Above 25% threshold", color:C.purple, screen:"variance" },
//               { icon:"💳", label:`${additionalPremCases} Additional Premium`,
//                 sub:"EST YTD premium owed", color:C.red, screen:"variance" },
//               { icon:"📅", label:`${pendingCases} Pending Submissions`,
//                 sub:"Awaiting processing", color:C.accent, screen:"policies" },
//               { icon:"⚠️", label:`${hitlPending} HITL Reviews`,
//                 sub:"Awaiting auditor action", color:C.amber, screen:"ai-audit" },
//               { icon:"✅", label:`${autoResolved}% Auto-resolved`,
//                 sub:"No human review needed", color:C.green, screen:"policies" },
//             ].map((item, i) => (
//               <div key={i} onClick={() => setScreen(item.screen)}
//                 style={{ display:"flex", alignItems:"center", gap:12, padding:"10px 14px",
//                   borderRadius:10, background:C.bg, cursor:"pointer", transition:"all 0.15s" }}
//                 onMouseEnter={e => e.currentTarget.style.background = "#E8F0FE"}
//                 onMouseLeave={e => e.currentTarget.style.background = C.bg}>
//                 <span style={{ fontSize:20 }}>{item.icon}</span>
//                 <div style={{ flex:1 }}>
//                   <div style={{ fontSize:13, fontWeight:700, color:item.color }}>{item.label}</div>
//                   <div style={{ fontSize:11, color:C.muted }}>{item.sub}</div>
//                 </div>
//                 <span style={{ color:C.muted, fontSize:14 }}>›</span>
//               </div>
//             ))}
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// }
 
 
// // ── Policies Screen ───────────────────────────────────────────────────────────
// function PoliciesScreen({ setScreen, setSelectedCase, cases, onRefresh }) {
//   const [search, setSearch] = useState("");
//   const [filter, setFilter] = useState("All");
 
//   const filtered = cases.filter(c =>
//     (filter === "All" || c.risk_level?.toLowerCase() === filter.toLowerCase()) &&
//     (c.policy_number?.toLowerCase().includes(search.toLowerCase()) ||
//      String(c.audit_case_id).includes(search))
//   );

//   console.log("filtered data -->",cases);
  
 
//   const high    = cases.filter(c => c.risk_level === "high").length;
//   const pending = cases.filter(c => ["pending","running"].includes(c.status)).length;
//   const done    = cases.filter(c => c.status === "completed").length;
 
//   return (
//     <div>
//       <div style={{ display:"flex", gap:16, marginBottom:24, flexWrap:"wrap" }}>
//         <KpiCard label="Total Policies"  value={cases.length} sub="Active policy terms"         accent={C.accent} />
//         <KpiCard label="Pending Review"  value={pending}      sub="Awaiting auditor action"      accent={C.amber}  />
//         <KpiCard label="High Risk"       value={high}         sub="Require immediate attention"  accent={C.red}    />
//         <KpiCard label="Completed"       value={done}         sub="Fully audited"                accent={C.green}  />
//       </div>
 
//       <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
//         <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center",
//           marginBottom:20, flexWrap:"wrap", gap:12 }}>
//           <h2 style={{ margin:0, fontSize:18, fontWeight:700, color:C.text }}>Policy Management</h2>
//           <div style={{ display:"flex", gap:10, alignItems:"center", flexWrap:"wrap" }}>
//             <input value={search} onChange={e => setSearch(e.target.value)}
//               placeholder="Search policy # or case ID..."
//               style={{ border:`1px solid ${C.border}`, borderRadius:8, padding:"8px 14px",
//                 fontSize:13, width:240, outline:"none", color:C.text }} />
//             {["All","High","Medium","Low"].map(f => (
//               <button key={f} onClick={() => setFilter(f)}
//                 style={{ background:filter === f ? C.accent : C.bg,
//                   color:filter === f ? "#fff" : C.muted,
//                   border:`1px solid ${filter === f ? C.accent : C.border}`,
//                   borderRadius:20, padding:"5px 16px", fontSize:12, fontWeight:600, cursor:"pointer" }}>
//                 {f}
//               </button>
//             ))}
//             <button onClick={onRefresh}
//               style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:8,
//                 padding:"7px 14px", fontSize:12, cursor:"pointer", color:C.muted }}>
//               ↻ Refresh
//             </button>
//           </div>
//         </div>
 
//         {cases.length === 0 ? (
//           <div style={{ textAlign:"center", padding:60, color:C.muted, fontSize:14 }}>
//             No audit cases found. Go to <strong>Data Upload</strong> to run your first audit.
//           </div>
//         ) : (
//           <>
//             <table style={{ width:"100%", borderCollapse:"collapse" }}>
//               <thead>
//                 <tr style={{ borderBottom:`2px solid ${C.border}`, background:"#F8FAFD" }}>
//                   {["Policy Number","Insured Name","St.","Variance","Earned Premium",
//                     "Risk","Status","Agent Name","Actions"].map(h => (
//                     <th key={h} style={{ textAlign:"left", padding:"10px 14px", fontSize:11,
//                       fontWeight:700, color:C.muted, textTransform:"uppercase", letterSpacing:0.8 }}>{h}</th>
//                   ))}
//                 </tr>
//               </thead>
//               <tbody>
//                 {filtered.map(c => (
//                   <tr key={c.audit_case_id}
//                     style={{ borderBottom:`1px solid ${C.border}`, transition:"background 0.1s" }}
//                     onMouseEnter={e => e.currentTarget.style.background = "#F5F8FF"}
//                     onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
 
//                     {/* Policy Number */}
//                     <td style={{ padding:"13px 14px", fontSize:13, fontWeight:700, color:C.accent,
//                       cursor:"pointer" }}
//                       onClick={() => { setSelectedCase(c); setScreen("audit-detail"); }}>
//                       {c.policy_number}
//                     </td>
 
//                     {/* Insured Name — not returned by current API */}
//                     <td style={{ padding:"13px 14px", fontSize:13, color:C.muted }}>{c.insured_name}</td>
 
//                     {/* St. — not returned by current API */}
//                     <td style={{ padding:"13px 14px", fontSize:13, fontWeight:700, color:C.muted }}>{c.class_code_variance[0]?.StateCode}</td>
 
//                     {/* Variance with progress bar */}
//                     <td style={{ padding:"13px 14px" }}>
//                       <div style={{ display:"flex", alignItems:"center", gap:8 }}>
//                         <div style={{ width:50, height:6, borderRadius:3, background:C.border, overflow:"hidden" }}>
//                           <div style={{ width:`${Math.min((c.variance_pct || 0) * 3, 100)}%`,
//                             height:"100%",
//                             background:(c.variance_pct || 0) >= 25 ? C.red :
//                                        (c.variance_pct || 0) >= 10 ? C.amber : C.green }} />
//                         </div>
//                         <span style={{ fontSize:13, fontWeight:700,
//                           color:(c.variance_pct || 0) >= 25 ? C.red :
//                                (c.variance_pct || 0) >= 10 ? C.amber : C.green }}>
//                           {c.variance_pct != null ? `${Number(c.variance_pct).toFixed(1)}%` : "—"}
//                         </span>
//                       </div>
//                     </td>
 
//                     {/* Earned Premium */}
//                     <td style={{ padding:"13px 14px", fontSize:13, fontWeight:600, color:C.text }}>
//                       {fmt(c.overall_variance?.earned_premium)}
//                     </td>
 
//                     {/* Risk */}
//                     <td style={{ padding:"13px 14px" }}><RiskBadge risk={c.risk_level} /></td>
 
//                     {/* Status */}
//                     <td style={{ padding:"13px 14px" }}><StatusBadge status={c.status} /></td>
 
//                     {/* Agent Name — not in API response */}
//                     <td style={{ padding:"13px 14px", fontSize:12, color:C.muted }}>—</td>
 
//                     {/* Actions */}
//                     <td style={{ padding:"13px 14px" }}>
//                       <div style={{ display:"flex", gap:6 }}>
//                         <button onClick={() => { setSelectedCase(c); setScreen("audit-detail"); }}
//                           style={{ background:C.accent, color:"#fff", border:"none", borderRadius:6,
//                             padding:"5px 12px", fontSize:12, fontWeight:600, cursor:"pointer" }}>
//                           Review
//                         </button>
//                         <button onClick={() => downloadReport(c.audit_case_id)}
//                           style={{ background:C.bg, color:C.muted, border:`1px solid ${C.border}`,
//                             borderRadius:6, padding:"5px 10px", fontSize:12, cursor:"pointer" }}>
//                           ⬇
//                         </button>
//                       </div>
//                     </td>
//                   </tr>
//                 ))}
//               </tbody>
//             </table>
//             {filtered.length === 0 && (
//               <div style={{ textAlign:"center", padding:40, color:C.muted, fontSize:14 }}>
//                 No cases match your filter.
//               </div>
//             )}
//           </>
//         )}
//       </div>
//     </div>
//   );
// }
 
 
// // ── Variance Analysis ─────────────────────────────────────────────────────────
// function VarianceAnalysis({ cases }) {
//   const [activeIdx, setActiveIdx] = useState(null);
 
//   const completedCases = cases.filter(c =>
//     ["completed","hitl_pending","pending"].includes(c.status) &&
//     c.class_code_variance && c.class_code_variance.length > 0
//   );
//   const allCCVariance = completedCases.flatMap(c => c.class_code_variance || []);
  
//   console.log("additional premium ",completedCases);
  
//   // Aggregate per class code — include all exposure and premium fields
//   const byCC = {};
//   allCCVariance.forEach(row => {
//     const key = `${row.ClassCode}-${row.StateCode}`;
//     if (!byCC[key]) byCC[key] = {
//       code:           row.ClassCode,
//       state:          row.StateCode,
//       est_exposure:   0,
//       earned_exposure:0,
//       est_ytd_premium:0,
//       earned_premium: 0,
//       variance:       0,
//     };
//     byCC[key].est_exposure    += row.est_exposure    || 0;
//     byCC[key].earned_exposure += row.earned_exposure || 0;
//     byCC[key].est_ytd_premium += row.est_ytd_premium || 0;
//     byCC[key].earned_premium  += row.earned_premium  || 0;
//     byCC[key].variance        += row.variance         || 0;
//   });
//   const ccRows = Object.values(byCC).sort((a, b) => Math.abs(b.variance) - Math.abs(a.variance));
 
//   // KPI derivations
//   const totalExposureDelta = ccRows.reduce((s, r) => s + Math.abs(r.est_exposure - r.earned_exposure), 0);
//   const estYtdImpact       = ccRows.filter(r => r.variance > 0).reduce((s, r) => s + r.variance, 0);
//   const refundDue          = ccRows.filter(r => r.variance < 0).reduce((s, r) => s + Math.abs(r.variance), 0);
//   const mismatches         = ccRows.filter(r => Math.abs(r.variance) > 500).length;
//   const totalEstYtdPremium = ccRows.reduce(
//   (s, r) => s + r.est_ytd_premium,
//   0
// );
 
//   return (
//     <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
 
//       {/* KPI row */}
//       <div style={{ display:"flex", gap:16 }}>
//         <KpiCard label="Total Exposure Delta"    value={money(Math.round(totalExposureDelta))} sub="↑ Across all policies"      accent={C.red}    />
//         <KpiCard label="EST YTD Premium Impact"  value={money(Math.round(totalEstYtdPremium))}       sub="Net additional owed"         accent={C.amber}  />
//         <KpiCard label="Additional Premium"        value={money(Math.round(estYtdImpact))}        sub="Underpaid — owed to insurer"  accent={C.amber}  />
//         <KpiCard label="Class Code Mismatches"   value={mismatches}                             sub="Require reclassification"   accent={C.purple} />
//       </div>
 
//       {/* Class Code Breakdown */}
//       <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
//         <SectionHeader title="Variance by Class Code"
//           sub="Delta between EST Exposure and Earned Exposure, applied to Net Rate for EST YTD Premium" />
//         {ccRows.length === 0 ? (
//           <div style={{ textAlign:"center", padding:40, color:C.muted }}>
//             No completed audits with variance data yet.
//           </div>
//         ) : (
//           <table style={{ width:"100%", borderCollapse:"collapse" }}>
//             <thead>
//               <tr style={{ borderBottom:`2px solid ${C.border}`, background:"#F8FAFD" }}>
//                 {["Class Code","State","EST Exposure","Earned Exposure","Delta",
//                   "Net Rate","EST YTD Premium","Action"].map(h => (
//                   <th key={h} style={{ textAlign:"left", padding:"10px 14px", fontSize:11,
//                     fontWeight:700, color:C.muted, textTransform:"uppercase", letterSpacing:0.7 }}>{h}</th>
//                 ))}
//               </tr>
//             </thead>
//             <tbody>
//               {ccRows.map((row, i) => {
//                 const delta        = row.est_exposure - row.earned_exposure;
//                 const isExpanded   = activeIdx === i;
//                 return (
//                   <Fragment key={row.code + i}>
//                     <tr
//                       onClick={() => setActiveIdx(isExpanded ? null : i)}
//                       style={{ borderBottom:`1px solid ${C.border}`,
//                         background:isExpanded ? "#F0F4FE" : "transparent", cursor:"pointer" }}
//                       onMouseEnter={e => !isExpanded && (e.currentTarget.style.background="#F8FAFD")}
//                       onMouseLeave={e => !isExpanded && (e.currentTarget.style.background="transparent")}>
 
//                       {/* Class Code */}
//                       <td style={{ padding:"13px 14px", fontSize:13, fontWeight:700, color:C.accent }}>
//                         {row.code}
//                       </td>
 
//                       {/* Description — using state code as description */}
//                       <td style={{ padding:"13px 14px", fontSize:13, color:C.text }}>
//                         {row.state}
//                       </td>
 
//                       {/* EST Exposure */}
//                       <td style={{ padding:"13px 14px", fontSize:13, color:C.text }}>
//                         {money(Math.round(row.est_exposure))}
//                       </td>
 
//                       {/* Earned Exposure */}
//                       <td style={{ padding:"13px 14px", fontSize:13, color:C.text }}>
//                         {money(Math.round(row.earned_exposure))}
//                       </td>
 
//                       {/* Delta (EST – Earned exposure) */}
//                       <td style={{ padding:"13px 14px", fontWeight:700, fontSize:13,
//                         color: delta > 0 ? C.red : C.green }}>
//                         {delta > 0 ? "+" : ""}{money(Math.round(delta))}
//                       </td>
 
//                       {/* Net Rate — not available from API */}
//                       <td style={{ padding:"13px 14px", fontSize:13, color:C.muted }}>—</td>
 
//                       {/* EST YTD Premium */}
//                       <td style={{ padding:"13px 14px", fontWeight:700, fontSize:13,
//                         color: row.variance > 0 ? C.red : C.green }}>
//                         {money(Math.round(row.est_ytd_premium))}
//                       </td>
 
//                       {/* Drill down */}
//                       <td style={{ padding:"13px 14px" }}>
//                         <button style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:6,
//                           padding:"4px 12px", fontSize:12, cursor:"pointer", color:C.accent, fontWeight:600 }}>
//                           {isExpanded ? "Collapse ▲" : "Drill Down ▼"}
//                         </button>
//                       </td>
//                     </tr>
 
//                     {/* Expanded drill-down row */}
//                     {isExpanded && (
//                       <tr>
//                         <td colSpan={8} style={{ padding:0, background:"#F0F4FE" }}>
//                           <div style={{ padding:"16px 24px", borderTop:`1px dashed ${C.border}` }}>
//                             <div style={{ fontSize:13, fontWeight:700, color:C.text, marginBottom:12 }}>
//                               AI Explanation — Class Code {row.code} ({row.state})
//                             </div>
//                             <div style={{ background:"#EEF2FF", borderLeft:`4px solid ${C.accent}`,
//                               borderRadius:"0 8px 8px 0", padding:"12px 16px", fontSize:13,
//                               color:C.text, lineHeight:1.6 }}>
//                               🤖 <strong>Explanation Agent:</strong> The insured{" "}
//                               {delta > 0 ? "underreported" : "overreported"} EST Exposure for class code{" "}
//                               <strong>{row.code}</strong> ({row.state}).
//                               A delta of <strong>{money(Math.round(Math.abs(delta)))}</strong> was identified
//                               between EST Exposure ({money(Math.round(row.est_exposure))}) and Earned Exposure
//                               ({money(Math.round(row.earned_exposure))}). The resulting EST YTD Premium
//                               is <strong style={{ color: row.variance > 0 ? C.red : C.green }}>
//                                 {money(Math.round(row.est_ytd_premium))}
//                               </strong>.
//                               {Math.abs(row.variance) > 500
//                                 ? " This exceeds the threshold and requires auditor review."
//                                 : " This is within acceptable variance range."}
//                             </div>
//                             <div style={{ display:"flex", gap:10, marginTop:12 }}>
//                               <button style={{ background:C.green, color:"#fff", border:"none",
//                                 borderRadius:7, padding:"7px 16px", fontSize:12, fontWeight:600, cursor:"pointer" }}>
//                                 ✓ Accept Finding
//                               </button>
//                               <button style={{ background:C.amber, color:"#fff", border:"none",
//                                 borderRadius:7, padding:"7px 16px", fontSize:12, fontWeight:600, cursor:"pointer" }}>
//                                 ✎ Override
//                               </button>
//                               <button style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:7,
//                                 padding:"7px 16px", fontSize:12, cursor:"pointer", color:C.muted }}>
//                                 Add Note
//                               </button>
//                             </div>
//                           </div>
//                         </td>
//                       </tr>
//                     )}
//                   </Fragment>
//                 );
//               })}
//             </tbody>
//           </table>
//         )}
//       </div>
 
//       {/* Monthly Audit Volume */}
//       <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
//         <SectionHeader title="Monthly Audit Volume"
//           sub="Completed, pending, and high-risk audits by payroll submission period" />
//         <ResponsiveContainer width="100%" height={220}>
//           <BarChart data={buildMonthlyAuditData(cases)} margin={{ top:5, right:10, bottom:0, left:0 }}>
//             <CartesianGrid strokeDasharray="3 3" stroke={C.border} vertical={false} />
//             <XAxis dataKey="month" tick={{ fontSize:12, fill:C.muted }} />
//             <YAxis tick={{ fontSize:12, fill:C.muted }} />
//             <Tooltip contentStyle={{ borderRadius:10, border:`1px solid ${C.border}`, fontSize:12 }} />
//             <Legend wrapperStyle={{ fontSize:12 }} />
//             <Bar dataKey="completed" fill={C.green}  name="Completed" radius={[4,4,0,0]} />
//             <Bar dataKey="pending"   fill={C.amber}  name="Pending"   radius={[4,4,0,0]} />
//             <Bar dataKey="highRisk"  fill={C.red}    name="High Risk"  radius={[4,4,0,0]} />
//           </BarChart>
//         </ResponsiveContainer>
//       </div>
//     </div>
//   );
// }
 
 
// // ── Results + HITL Panel ──────────────────────────────────────────────────────
// function ResultsAndHITLPanel({ status, onApprove }) {
//   const [note,       setNote]       = useState("");
//   const [submitting, setSubmitting] = useState(false);
//   const [decision,   setDecision]   = useState(null);
 
//   const isHITL      = status.status === "hitl_pending";
//   const isCompleted = status.status === "completed";
//   const ov          = status.overall_variance || {};
 
//   const riskColor = status.risk_level === "high"   ? C.red
//                   : status.risk_level === "medium"  ? C.amber : C.green;
//   const recColor  = status.recommendation === "additional_premium" ? C.amber
//                   : status.recommendation === "refund"             ? C.green
//                   : status.recommendation === "clarification"      ? C.purple : C.muted;
 
//   const handleDecision = async (d) => {
//     setDecision(d);
//     setSubmitting(true);
//     try {
//       await onApprove(d, note);
//     } finally {
//       setSubmitting(false);
//       setDecision(null);
//     }
//   };
 
//   return (
//     <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
 
//       {/* HITL banner */}
//       {isHITL && (
//         <div style={{ padding:"14px 18px", borderRadius:12,
//           background:"linear-gradient(135deg, #FEF3C7, #FDE68A)",
//           border:`1px solid ${C.amber}`, display:"flex", alignItems:"center", gap:14 }}>
//           <span style={{ fontSize:26 }}>⚠️</span>
//           <div>
//             <div style={{ fontSize:14, fontWeight:800, color:"#78350F" }}>
//               Human Review Required — High-Risk Audit
//             </div>
//             <div style={{ fontSize:12, color:"#92400E", marginTop:2 }}>
//               The AI pipeline has paused and is awaiting your approval before finalizing.
//               Review the findings below then approve or reject.
//             </div>
//           </div>
//         </div>
//       )}
 
//       {/* Metrics grid */}
//       <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:20 }}>
//         <div style={{ fontSize:14, fontWeight:700, color:C.text, marginBottom:12 }}>
//           Audit Results — Case #{status.audit_case_id}
//         </div>
 
//         <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10, marginBottom:14 }}>
//           {[
//             { label:"Overall Variance",
//               value:money(Math.round(ov.variance || status.variance || 0)),
//               color:(ov.variance || status.variance || 0) > 0 ? C.red : C.green },
//             { label:"Variance %",
//               value:`${Number(ov.variance_pct || status.variance_pct || 0).toFixed(2)}%`,
//               color:Math.abs(ov.variance_pct || status.variance_pct || 0) > 10 ? C.red : C.green },
//             { label:"Risk Level",        value:status.risk_level?.toUpperCase() || "—", color:riskColor },
//             { label:"Recommendation",    value:status.recommendation?.replace(/_/g," ") || "—", color:recColor },
//             { label:"Earned Premium",    value:money(Math.round(ov.earned_premium    || 0)), color:C.text },
//             { label:"EST YTD Premium",   value:money(Math.round(ov.est_ytd_premium   || 0)), color:C.text },
//           ].map(({ label, value, color }) => (
//             <div key={label} style={{ background:C.bg, borderRadius:10, padding:"11px 14px" }}>
//               <div style={{ fontSize:10, color:C.muted, fontWeight:700, textTransform:"uppercase",
//                 letterSpacing:0.8, marginBottom:3 }}>{label}</div>
//               <div style={{ fontSize:15, fontWeight:800, color }}>{value}</div>
//             </div>
//           ))}
//         </div>
 
//         {/* Flagged class codes */}
//         {(status.class_code_variance || []).filter(r => r.is_flagged).length > 0 && (
//           <div style={{ marginBottom:14 }}>
//             <div style={{ fontSize:12, fontWeight:700, color:C.text, marginBottom:8 }}>
//               Flagged Class Codes
//             </div>
//             {(status.class_code_variance || []).filter(r => r.is_flagged).map((row, i) => (
//               <div key={i} style={{ display:"flex", justifyContent:"space-between",
//                 alignItems:"center", padding:"8px 12px", background:"#FEF2F2",
//                 borderRadius:8, marginBottom:6, border:`1px solid #FECACA` }}>
//                 <div style={{ fontSize:12, color:C.text }}>
//                   <strong>Class {row.ClassCode}</strong> ({row.StateCode}) —{" "}
//                   Variance: <strong style={{ color:C.red }}>{money(Math.round(row.variance))}</strong>
//                   {" "}({Number(row.variance_pct).toFixed(1)}%)
//                 </div>
//                 <span style={{ fontSize:10, fontWeight:700, color:C.red,
//                   background:"#FEE2E2", padding:"2px 8px", borderRadius:20 }}>⚠ Flag</span>
//               </div>
//             ))}
//           </div>
//         )}
 
//         {/* HITL Approval Form */}
//         {isHITL && (
//           <div style={{ borderTop:`1px solid ${C.border}`, paddingTop:14 }}>
//             <div style={{ fontSize:13, fontWeight:700, color:C.text, marginBottom:8 }}>
//               Auditor Decision
//             </div>
//             <textarea value={note} onChange={e => setNote(e.target.value)}
//               placeholder="Add notes, overrides, or justification for your decision (optional)…"
//               style={{ width:"100%", border:`1px solid ${C.border}`, borderRadius:8, padding:"10px 12px",
//                 fontSize:13, color:C.text, resize:"vertical", minHeight:72, outline:"none",
//                 boxSizing:"border-box", marginBottom:12, fontFamily:"inherit" }} />
//             <div style={{ display:"flex", gap:10 }}>
//               <button disabled={submitting} onClick={() => handleDecision("approve")}
//                 style={{ flex:1, background:submitting && decision === "approve" ? "#86EFAC" : C.green,
//                   color:"#fff", border:"none", borderRadius:10, padding:"12px 0",
//                   fontSize:14, fontWeight:800, cursor:submitting ? "default" : "pointer",
//                   display:"flex", alignItems:"center", justifyContent:"center", gap:8 }}>
//                 {submitting && decision === "approve" ? "⏳ Submitting…" : "✓ Approve & Finalize"}
//               </button>
//               <button disabled={submitting} onClick={() => handleDecision("reject")}
//                 style={{ flex:1, background:submitting && decision === "reject" ? "#FCA5A5" : C.red,
//                   color:"#fff", border:"none", borderRadius:10, padding:"12px 0",
//                   fontSize:14, fontWeight:800, cursor:submitting ? "default" : "pointer",
//                   display:"flex", alignItems:"center", justifyContent:"center", gap:8 }}>
//                 {submitting && decision === "reject" ? "⏳ Submitting…" : "✗ Reject"}
//               </button>
//             </div>
//           </div>
//         )}
 
//         {/* Download for completed */}
//         {isCompleted && (
//           <button onClick={() => downloadReport(status.audit_case_id)}
//             style={{ width:"100%", background:C.accent, color:"#fff", border:"none", borderRadius:10,
//               padding:"11px 0", fontSize:13, fontWeight:700, cursor:"pointer", marginTop:4 }}>
//             ⬇ Download Audit Report
//           </button>
//         )}
//       </div>
//     </div>
//   );
// }
 
 
// // // ── AI Audit Screen ───────────────────────────────────────────────────────────


// // function AIAuditScreen({ cases, onCaseCreated, activeCaseId: propCaseId, batchCaseIds }) {
// //   // ── Single-case watch (original behaviour) ─────────────────────
// //   const [auditCaseId, setAuditCaseId] = useState(null);
// //   const [status,      setStatus]      = useState(null);
// //   const [logs,        setLogs]        = useState([]);
// //   const [agentStatus, setAgentStatus] = useState({});
// //   const stopPollRef = useRef(null);
 
// //   // ── Batch mode state ────────────────────────────────────────────
// //   // batchQueue: ordered list of case IDs still waiting for HITL or to finish
// //   const [batchQueue,      setBatchQueue]      = useState([]);  // all case IDs in this batch
// //   const [batchStatuses,   setBatchStatuses]   = useState({}); // caseId → status object
// //   const [hitlQueuedIds,   setHitlQueuedIds]   = useState([]); // cases waiting for HITL
// //   const [activeHITLCase,  setActiveHITLCase]  = useState(null); // currently displayed HITL
// //   const batchPollsRef = useRef({});  // caseId → stop function
 
// //   const isBatchMode = batchCaseIds && batchCaseIds.length > 0;
 
// //   const AGENT_LOG_LABELS = {
// //     ingestion_excel:      "Ingestion Agent     → payroll Excel parsed",
// //     ingestion_xml:        "Policy Parser       → XML class codes loaded",
// //     ingestion_audit_meta: "Metadata Agent      → audit dates & submission count loaded",
// //     api_ingestion_node:   "API Ingestion       → payroll & policy config fetched from API",
// //     officer_agent:        "Officer Agent       → officer payroll classification checked",
// //     class_code_agent:     "Class Code Agent    → class code usage validated",
// //     frequency_agent:      "Frequency Agent     → submission frequency analysed",
// //     premium_agent:        "Premium Agent       → variance calculation complete",
// //     risk_assessor:        "Risk Assessor       → risk level & recommendation assigned",
// //     explanation_agent:    "Explanation Agent   → AI narrative generated",
// //     hitl_checkpoint:      "HITL Checkpoint     → paused for human review",
// //   };
 
// //   // ── Single-case watcher (unchanged logic) ───────────────────────
// //   const watchCase = useCallback((caseId) => {
// //     setAuditCaseId(caseId);
// //     setLogs([`[${new Date().toLocaleTimeString()}] 🚀 Workflow started — Case #${caseId}`]);
// //     if (stopPollRef.current) stopPollRef.current();
// //     const loggedAgents = new Set();
 
// //     stopPollRef.current = pollAuditStatus(caseId, (s) => {
// //       setStatus(s);
// //       const ts = new Date().toLocaleTimeString();
// //       const newAgentSt = {};
// //       (s.agent_logs || []).forEach(log => {
// //         if (!log.agent) return;
// //         newAgentSt[log.agent] = log.status === "error" ? "error" : "complete";
// //         if (!loggedAgents.has(log.agent)) {
// //           loggedAgents.add(log.agent);
// //           const label  = AGENT_LOG_LABELS[log.agent] ?? log.agent;
// //           const prefix = log.status === "error" ? "✗" : log.status === "skipped" ? "⏭" : "✓";
// //           setLogs(l => [...l, `[${ts}] ${prefix} ${label}`]);
// //         }
// //       });
// //       setAgentStatus(prev => ({...prev, ...newAgentSt}));
// //       if (s.status === "hitl_pending") {
// //         setLogs(l => [...l,
// //           `[${ts}] ⚠️  HITL required — case paused for human review`,
// //           `[${ts}]    Risk: ${s.risk_level?.toUpperCase()}, Variance: ${Number(s.variance_pct || 0).toFixed(2)}%`,
// //         ]);
// //         onCaseCreated?.();
// //       }
// //       if (s.status === "completed") {
// //         setLogs(l => [...l,
// //           `[${ts}] 🎉 Audit complete`,
// //           `[${ts}]    Variance: ${Number(s.variance_pct || 0).toFixed(2)}%  |  Risk: ${s.risk_level}  |  Rec: ${s.recommendation}`,
// //         ]);
// //         onCaseCreated?.();
// //         stopPollRef.current?.();
// //       }
// //       if (s.status === "rejected") { setLogs(l => [...l, `[${ts}] ✗ Audit rejected`]); stopPollRef.current?.(); }
// //       if (s.status === "error")    { setLogs(l => [...l, `[${ts}] ✗ Error: ${s.errors}`]); stopPollRef.current?.(); }
// //     });
// //   }, [onCaseCreated]);
 
// //   // ── Batch: start polling each case ID ───────────────────────────
// //   useEffect(() => {
// //     if (!isBatchMode || batchCaseIds.length === 0) return;
// //     setBatchQueue(batchCaseIds);
// //     setBatchStatuses({});
// //     setHitlQueuedIds([]);
// //     setActiveHITLCase(null);
 
// //     // Clear any previous batch polls
// //     Object.values(batchPollsRef.current).forEach(stop => stop?.());
// //     batchPollsRef.current = {};
 
// //     batchCaseIds.forEach(caseId => {
// //       const stop = pollAuditStatus(caseId, (s) => {
// //         setBatchStatuses(prev => ({ ...prev, [caseId]: s }));
// //         onCaseCreated?.();
 
// //         if (s.status === "hitl_pending") {
// //           setHitlQueuedIds(prev =>
// //             prev.includes(caseId) ? prev : [...prev, caseId]
// //           );
// //           // Show the first waiting HITL case immediately
// //           setActiveHITLCase(cur => cur ?? caseId);
// //         }
 
// //         if (["completed", "rejected", "error"].includes(s.status)) {
// //           // Stop polling this case
// //           batchPollsRef.current[caseId]?.();
// //           delete batchPollsRef.current[caseId];
 
// //           // Remove from HITL queue if it was there
// //           setHitlQueuedIds(prev => {
// //             const next = prev.filter(id => id !== caseId);
// //             return next;
// //           });
 
// //           // If this was the active HITL case, advance to the next
// //           setActiveHITLCase(cur => {
// //             if (cur === caseId) {
// //               const remaining = hitlQueuedIds.filter(id => id !== caseId);
// //               return remaining[0] ?? null;
// //             }
// //             return cur;
// //           });
// //         }
// //       });
// //       batchPollsRef.current[caseId] = stop;
// //     });
 
// //     return () => {
// //       Object.values(batchPollsRef.current).forEach(stop => stop?.());
// //       batchPollsRef.current = {};
// //     };
// //   }, [JSON.stringify(batchCaseIds)]); // eslint-disable-line react-hooks/exhaustive-deps
 
// //   // Advance activeHITLCase whenever hitlQueuedIds changes
// //   useEffect(() => {
// //     if (!activeHITLCase && hitlQueuedIds.length > 0) {
// //       setActiveHITLCase(hitlQueuedIds[0]);
// //     }
// //   }, [hitlQueuedIds, activeHITLCase]);
 
// //   // ── Cleanup on unmount ──────────────────────────────────────────
// //   useEffect(() => {
// //     return () => {
// //       stopPollRef.current?.();
// //       Object.values(batchPollsRef.current).forEach(stop => stop?.());
// //     };
// //   }, []);
 
// //   useEffect(() => {
// //     if (propCaseId && propCaseId !== auditCaseId) watchCase(propCaseId);
// //   }, [propCaseId]); // eslint-disable-line react-hooks/exhaustive-deps
 
// //   useEffect(() => {
// //     if (propCaseId || isBatchMode) return;
// //     const active = cases.find(c => ["running","pending","hitl_pending"].includes(c.status));
// //     if (active && active.audit_case_id !== auditCaseId) watchCase(active.audit_case_id);
// //   }, [cases]); // eslint-disable-line react-hooks/exhaustive-deps
 
// //   const agentLabels = [
// //     { keys:["ingestion_excel","ingestion_audit_meta","api_ingestion_node"], label:"Ingestion Agent",   sub:"Payroll + audit metadata" },
// //     { keys:["ingestion_xml"],                          label:"Policy Parser",     sub:"XML class codes & rates" },
// //     { keys:["officer_agent"],                          label:"Officer Agent",     sub:"Officer classification" },
// //     { keys:["class_code_agent"],                       label:"Class Code Agent",  sub:"Class code validation" },
// //     { keys:["frequency_agent"],                        label:"Frequency Agent",   sub:"Submission frequency" },
// //     { keys:["premium_agent","risk_assessor"],          label:"Premium Agent",     sub:"Variance & risk scoring" },
// //     { keys:["explanation_agent"],                      label:"Explanation Agent", sub:"AI narrative" },
// //   ];
 
// //   const resolveStepStatus = (keys) => {
// //     let anyError = false, doneCount = 0;
// //     for (const k of keys) {
// //       if (agentStatus[k] === "error")    anyError = true;
// //       if (agentStatus[k] === "complete") doneCount++;
// //     }
// //     if (anyError)                  return "error";
// //     if (doneCount === keys.length) return "complete";
// //     if (doneCount > 0)             return "partial";
// //     return "pending";
// //   };
 
// //   // ── Batch summary helpers ────────────────────────────────────────
// //   const batchDone      = Object.values(batchStatuses).filter(s => s.status === "completed").length;
// //   const batchRejected  = Object.values(batchStatuses).filter(s => s.status === "rejected").length;
// //   const batchError_cnt = Object.values(batchStatuses).filter(s => s.status === "error").length;
// //   const batchRunning   = Object.values(batchStatuses).filter(s => ["pending","processing","running"].includes(s.status)).length;
// //   const batchHITL      = hitlQueuedIds.length;
 
// //   const activeHITLStatus = activeHITLCase ? batchStatuses[activeHITLCase] : null;
 
// //   // ── HITL decision handler for batch mode ────────────────────────
// //   const handleBatchHITL = async (decision, note) => {
// //     if (!activeHITLCase) return;
// //     try {
// //       await submitHITLDecision(activeHITLCase, { decision, notes: note });
// //       const fresh = await getAuditStatus(activeHITLCase);
// //       setBatchStatuses(prev => ({ ...prev, [activeHITLCase]: fresh }));
// //       onCaseCreated?.();
 
// //       // Remove from HITL queue and advance
// //       setHitlQueuedIds(prev => {
// //         const next = prev.filter(id => id !== activeHITLCase);
// //         setActiveHITLCase(next[0] ?? null);
// //         return next;
// //       });
// //     } catch (err) {
// //       alert("HITL submission failed: " + (err.response?.data?.detail || err.message));
// //     }
// //   };
 
// //   // ════════════════════════════════════════════════════════════════
// //   // RENDER
// //   // ════════════════════════════════════════════════════════════════
// //   return (
// //     <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
 
// //       {/* Header card */}
// //       <div style={{ background:`linear-gradient(135deg, ${C.navy} 0%, ${C.navyLt} 100%)`,
// //         borderRadius:14, padding:28, color:"#fff" }}>
// //         <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
// //           <div>
// //             <h2 style={{ margin:"0 0 6px", fontSize:22, fontWeight:800 }}>🤖 AI Audit Engine</h2>
// //             <p style={{ margin:0, opacity:0.7, fontSize:14 }}>
// //               LangGraph-powered multi-agent orchestration for automated earned exposure &amp; premium variance detection
// //             </p>
// //           </div>
// //           {/* Single-case badge */}
// //           {!isBatchMode && auditCaseId && (
// //             <div style={{ textAlign:"right" }}>
// //               <div style={{ fontSize:12, opacity:0.6, marginBottom:4 }}>Monitoring Case</div>
// //               <div style={{ fontSize:22, fontWeight:800 }}>#{auditCaseId}</div>
// //               {status && <StatusBadge status={status.status} />}
// //             </div>
// //           )}
// //           {/* Batch badge */}
// //           {isBatchMode && (
// //             <div style={{ textAlign:"right", minWidth:160 }}>
// //               <div style={{ fontSize:12, opacity:0.6, marginBottom:4 }}>Batch Mode</div>
// //               <div style={{ fontSize:22, fontWeight:800 }}>{batchCaseIds.length} policies</div>
// //               <div style={{ fontSize:12, opacity:0.6, marginTop:4 }}>
// //                 ✅ {batchDone} done · ⚠️ {batchHITL} HITL · ⚙️ {batchRunning} running
// //               </div>
// //             </div>
// //           )}
// //         </div>
// //         {!auditCaseId && !isBatchMode && (
// //           <div style={{ marginTop:16, padding:"12px 16px", background:"rgba(255,255,255,0.07)",
// //             borderRadius:10, fontSize:13, opacity:0.8 }}>
// //             Upload files in <strong>Data Upload</strong> to run an audit. The AI pipeline will
// //             automatically appear here once started.
// //           </div>
// //         )}
// //       </div>
 
// //       {/* ══════════════════════════════════════
// //           BATCH MODE: KPI bar + HITL queue
// //       ══════════════════════════════════════ */}
// //       {isBatchMode && (
// //         <>
// //           {/* Batch progress KPIs */}
// //           <div style={{ display:"flex", gap:14 }}>
// //             <KpiCard label="Total Queued"   value={batchCaseIds.length}  sub="From API batch"          accent={C.accent} />
// //             <KpiCard label="Completed"      value={batchDone}            sub="Fully audited"           accent={C.green}  />
// //             <KpiCard label="HITL Pending"   value={batchHITL}            sub="Awaiting your review"    accent={C.amber}  />
// //             <KpiCard label="Running"        value={batchRunning}         sub="In pipeline"             accent={C.purple} />
// //             {(batchRejected + batchError_cnt) > 0 && (
// //               <KpiCard label="Issues"       value={batchRejected + batchError_cnt} sub="Rejected / Error" accent={C.red} />
// //             )}
// //           </div>
 
// //           {/* HITL review queue banner */}
// //           {hitlQueuedIds.length > 0 && (
// //             <div style={{ background:"linear-gradient(135deg, #FEF3C7, #FDE68A)",
// //               border:`1px solid ${C.amber}`, borderRadius:12, padding:"14px 20px",
// //               display:"flex", alignItems:"center", gap:14 }}>
// //               <span style={{ fontSize:28 }}>⚠️</span>
// //               <div style={{ flex:1 }}>
// //                 <div style={{ fontSize:14, fontWeight:800, color:"#78350F" }}>
// //                   {hitlQueuedIds.length} policy(ies) require human review
// //                 </div>
// //                 <div style={{ fontSize:12, color:"#92400E", marginTop:2 }}>
// //                   Reviewing case #{activeHITLCase} now
// //                   {hitlQueuedIds.length > 1
// //                     ? ` · ${hitlQueuedIds.length - 1} more in queue after this`
// //                     : ""}
// //                 </div>
// //               </div>
// //               {/* Queue pills */}
// //               <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
// //                 {hitlQueuedIds.map((id, i) => (
// //                   <button key={id} onClick={() => setActiveHITLCase(id)}
// //                     style={{ background: id === activeHITLCase ? C.amber : "rgba(0,0,0,0.1)",
// //                       color: id === activeHITLCase ? "#fff" : "#78350F",
// //                       border:"none", borderRadius:20, padding:"4px 12px",
// //                       fontSize:12, fontWeight:700, cursor:"pointer" }}>
// //                     #{id}{i === 0 && id === activeHITLCase ? " ← now" : ""}
// //                   </button>
// //                 ))}
// //               </div>
// //             </div>
// //           )}
 
// //           {/* Active HITL panel */}
// //           {activeHITLCase && activeHITLStatus && (
// //             <div style={{ background:C.card, border:`2px solid ${C.amber}`, borderRadius:14, padding:24 }}>
// //               <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
// //                 <div>
// //                   <div style={{ fontSize:16, fontWeight:800, color:C.text }}>
// //                     Reviewing: {activeHITLStatus.policy_number} — Case #{activeHITLCase}
// //                   </div>
// //                   <div style={{ fontSize:12, color:C.muted, marginTop:2 }}>
// //                     Risk: <strong style={{ color:C.red }}>{activeHITLStatus.risk_level?.toUpperCase()}</strong>
// //                     &nbsp;·&nbsp;Variance: <strong>{Number(activeHITLStatus.variance_pct || 0).toFixed(2)}%</strong>
// //                     &nbsp;·&nbsp;Rec: <strong>{activeHITLStatus.recommendation?.replace(/_/g," ")}</strong>
// //                   </div>
// //                 </div>
// //                 <div style={{ display:"flex", gap:8 }}>
// //                   <RiskBadge risk={activeHITLStatus.risk_level} />
// //                   <StatusBadge status={activeHITLStatus.status} />
// //                 </div>
// //               </div>
// //               <ResultsAndHITLPanel
// //                 status={activeHITLStatus}
// //                 onApprove={handleBatchHITL}
// //               />
// //             </div>
// //           )}
 
// //           {/* Batch policy status grid */}
// //           <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
// //             <SectionHeader title="Batch Policy Progress"
// //               sub="All policies queued in this API batch — click a HITL case to review it" />
// //             <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(260px, 1fr))", gap:10 }}>
// //               {batchCaseIds.map(caseId => {
// //                 const s = batchStatuses[caseId];
// //                 const isHITL = hitlQueuedIds.includes(caseId);
// //                 const isActive = caseId === activeHITLCase;
// //                 const border = isActive ? `2px solid ${C.amber}` : isHITL ? `1px solid ${C.amber}` : `1px solid ${C.border}`;
// //                 const bg     = isActive ? "#FFFBEB" : isHITL ? "#FFFDE7" : C.bg;
// //                 return (
// //                   <div key={caseId}
// //                     onClick={() => isHITL && setActiveHITLCase(caseId)}
// //                     style={{ background:bg, border, borderRadius:10, padding:"12px 16px",
// //                       cursor:isHITL ? "pointer" : "default", transition:"all 0.15s" }}>
// //                     <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
// //                       <div style={{ fontSize:13, fontWeight:700, color:C.accent }}>
// //                         {s?.policy_number || `Case #${caseId}`}
// //                       </div>
// //                       <StatusBadge status={s?.status || "pending"} />
// //                     </div>
// //                     <div style={{ fontSize:11, color:C.muted, marginTop:4 }}>
// //                       Case #{caseId}
// //                       {s?.variance_pct != null && ` · Var: ${Number(s.variance_pct).toFixed(1)}%`}
// //                     </div>
// //                     {isHITL && (
// //                       <div style={{ marginTop:6, fontSize:11, fontWeight:700, color:C.amber }}>
// //                         ⚠️ Awaiting HITL {isActive ? "(reviewing now)" : "(click to review)"}
// //                       </div>
// //                     )}
// //                   </div>
// //                 );
// //               })}
// //             </div>
// //           </div>
// //         </>
// //       )}
 
// //       {/* ══════════════════════════════════════
// //           SINGLE-CASE MODE (original layout)
// //       ══════════════════════════════════════ */}
// //       {!isBatchMode && (
// //         <div style={{ display:"flex", gap:16 }}>
// //           {/* Agent Pipeline */}
// //           <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24, flex:1 }}>
// //             <SectionHeader title="Agent Pipeline Status" sub="Real-time LangGraph orchestration" />
// //             <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
// //               {agentLabels.map((a, i) => {
// //                 const st        = resolveStepStatus(a.keys);
// //                 const bgColor   = st === "complete" ? "#F0FDF4" : st === "error" ? "#FEF2F2" : st === "partial" ? "#EEF2FF" : C.bg;
// //                 const bdColor   = st === "complete" ? C.green   : st === "error" ? C.red     : st === "partial" ? C.accent  : C.border;
// //                 const circleClr = st === "complete" ? C.green   : st === "error" ? C.red     : st === "partial" ? C.accent  : C.border;
// //                 const badge     = st === "complete" ? { bg:"#DCFCE7", color:C.green,  text:"Done" }
// //                                 : st === "error"    ? { bg:"#FEE2E2", color:C.red,    text:"Error" }
// //                                 : st === "partial"  ? { bg:"#DBEAFE", color:C.accent, text:"Running" }
// //                                 :                    { bg:"#F3F4F6", color:C.muted,   text:"Pending" };
// //                 const subText   = st === "complete" ? a.sub
// //                                 : st === "error"    ? "Error encountered"
// //                                 : st === "partial"  ? "Processing…" : "Waiting…";
// //                 return (
// //                   <div key={a.keys.join()} style={{ display:"flex", alignItems:"center", gap:14,
// //                     padding:"12px 16px", borderRadius:10, transition:"all 0.3s",
// //                     background:bgColor, border:`1px solid ${bdColor}` }}>
// //                     <div style={{ width:32, height:32, borderRadius:"50%", flexShrink:0,
// //                       display:"flex", alignItems:"center", justifyContent:"center", fontSize:14,
// //                       background:circleClr, color: st === "pending" ? C.muted : "#fff" }}>
// //                       {st === "complete" ? "✓" : st === "error" ? "✗" : st === "partial" ? "⚙" : i + 1}
// //                     </div>
// //                     <div style={{ flex:1 }}>
// //                       <div style={{ fontSize:13, fontWeight:700, color:C.text }}>{a.label}</div>
// //                       <div style={{ fontSize:11, color:C.muted }}>{subText}</div>
// //                     </div>
// //                     <span style={{ fontSize:11, fontWeight:600, padding:"3px 10px", borderRadius:20,
// //                       background:badge.bg, color:badge.color }}>{badge.text}</span>
// //                   </div>
// //                 );
// //               })}
// //             </div>
// //           </div>
 
// //           {/* Live log + results */}
// //           <div style={{ flex:1, display:"flex", flexDirection:"column", gap:16 }}>
// //             <div style={{ background:C.navy, borderRadius:14, padding:20, flex:1, minHeight:300 }}>
// //               <div style={{ fontSize:13, fontWeight:700, color:"#64B5F6", marginBottom:12,
// //                 fontFamily:"monospace" }}>▶ AUDIT LOG</div>
// //               <div style={{ fontFamily:"'Courier New', monospace", fontSize:11.5, color:"#A8D8A8",
// //                 lineHeight:1.8, overflowY:"auto", maxHeight:280 }}>
// //                 {logs.length === 0
// //                   ? <span style={{ color:"#546E7A" }}>// Upload files then start an audit to see live output</span>
// //                   : logs.map((l, i) => <div key={i}>{l}</div>)}
// //               </div>
// //             </div>
 
// //             {status && ["completed","hitl_pending"].includes(status.status) && (
// //               <ResultsAndHITLPanel status={status} onApprove={async (decision, note) => {
// //                 try {
// //                   await submitHITLDecision(status.audit_case_id, { decision, notes: note });
// //                   const fresh = await getAuditStatus(status.audit_case_id);
// //                   setStatus(fresh);
// //                   onCaseCreated?.();
// //                   const ts = new Date().toLocaleTimeString();
// //                   setLogs(l => [...l, `[${ts}] ✓ HITL decision submitted: ${decision}`]);
// //                 } catch (err) {
// //                   alert("HITL submission failed: " + (err.response?.data?.detail || err.message));
// //                 }
// //               }} />
// //             )}
// //           </div>
// //         </div>
// //       )}
// //     </div>
// //   );
// // }

// function AIAuditScreen({ cases, onCaseCreated, activeCaseId: propCaseId, batchCaseIds }) {
//   // ── Single-case watch (original behaviour) ─────────────────────
//   const [auditCaseId, setAuditCaseId] = useState(null);
//   const [status,      setStatus]      = useState(null);
//   const [logs,        setLogs]        = useState([]);
//   const [agentStatus, setAgentStatus] = useState({});
//   const stopPollRef = useRef(null);
 
//   // ── Batch mode state ────────────────────────────────────────────
//   // batchQueue: ordered list of case IDs still waiting for HITL or to finish
//   const [batchQueue,      setBatchQueue]      = useState([]);  // all case IDs in this batch
//   const [batchStatuses,   setBatchStatuses]   = useState({}); // caseId → status object
//   const [hitlQueuedIds,   setHitlQueuedIds]   = useState([]); // cases waiting for HITL
//   const [activeHITLCase,  setActiveHITLCase]  = useState(null); // currently displayed HITL
//   const batchPollsRef = useRef({});  // caseId → stop function
//   const [batchView,        setBatchView]        = useState("table");  // "card" | "table"
 
//   const isBatchMode = batchCaseIds && batchCaseIds.length > 0;
 
//   const AGENT_LOG_LABELS = {
//     ingestion_excel:      "Ingestion Agent     → payroll Excel parsed",
//     ingestion_xml:        "Policy Parser       → XML class codes loaded",
//     ingestion_audit_meta: "Metadata Agent      → audit dates & submission count loaded",
//     api_ingestion_node:   "API Ingestion       → payroll & policy config fetched from API",
//     officer_agent:        "Officer Agent       → officer payroll classification checked",
//     class_code_agent:     "Class Code Agent    → class code usage validated",
//     frequency_agent:      "Frequency Agent     → submission frequency analysed",
//     premium_agent:        "Premium Agent       → variance calculation complete",
//     risk_assessor:        "Risk Assessor       → risk level & recommendation assigned",
//     explanation_agent:    "Explanation Agent   → AI narrative generated",
//     hitl_checkpoint:      "HITL Checkpoint     → paused for human review",
//   };
 
//   // ── Single-case watcher (unchanged logic) ───────────────────────
//   const watchCase = useCallback((caseId) => {
//     setAuditCaseId(caseId);
//     setLogs([`[${new Date().toLocaleTimeString()}] 🚀 Workflow started — Case #${caseId}`]);
//     if (stopPollRef.current) stopPollRef.current();
//     const loggedAgents = new Set();
 
//     stopPollRef.current = pollAuditStatus(caseId, (s) => {
//       setStatus(s);
//       const ts = new Date().toLocaleTimeString();
//       const newAgentSt = {};
//       (s.agent_logs || []).forEach(log => {
//         if (!log.agent) return;
//         newAgentSt[log.agent] = log.status === "error" ? "error" : "complete";
//         if (!loggedAgents.has(log.agent)) {
//           loggedAgents.add(log.agent);
//           const label  = AGENT_LOG_LABELS[log.agent] ?? log.agent;
//           const prefix = log.status === "error" ? "✗" : log.status === "skipped" ? "⏭" : "✓";
//           setLogs(l => [...l, `[${ts}] ${prefix} ${label}`]);
//         }
//       });
//       setAgentStatus(prev => ({...prev, ...newAgentSt}));
//       if (s.status === "hitl_pending") {
//         setLogs(l => [...l,
//           `[${ts}] ⚠️  HITL required — case paused for human review`,
//           `[${ts}]    Risk: ${s.risk_level?.toUpperCase()}, Variance: ${Number(s.variance_pct || 0).toFixed(2)}%`,
//         ]);
//         onCaseCreated?.();
//       }
//       if (s.status === "completed") {
//         setLogs(l => [...l,
//           `[${ts}] 🎉 Audit complete`,
//           `[${ts}]    Variance: ${Number(s.variance_pct || 0).toFixed(2)}%  |  Risk: ${s.risk_level}  |  Rec: ${s.recommendation}`,
//         ]);
//         onCaseCreated?.();
//         stopPollRef.current?.();
//       }
//       if (s.status === "rejected") { setLogs(l => [...l, `[${ts}] ✗ Audit rejected`]); stopPollRef.current?.(); }
//       if (s.status === "error")    { setLogs(l => [...l, `[${ts}] ✗ Error: ${s.errors}`]); stopPollRef.current?.(); }
//     });
//   }, [onCaseCreated]);
 
//   // ── Batch: start polling each case ID ───────────────────────────
//   useEffect(() => {
//     if (!isBatchMode || batchCaseIds.length === 0) return;
//     setBatchQueue(batchCaseIds);
//     setBatchStatuses({});
//     setHitlQueuedIds([]);
//     setActiveHITLCase(null);
 
//     // Clear any previous batch polls
//     Object.values(batchPollsRef.current).forEach(stop => stop?.());
//     batchPollsRef.current = {};
 
//     batchCaseIds.forEach(caseId => {
//       const stop = pollAuditStatus(caseId, (s) => {
//         setBatchStatuses(prev => ({ ...prev, [caseId]: s }));
//         onCaseCreated?.();
 
//         if (s.status === "hitl_pending") {
//           setHitlQueuedIds(prev =>
//             prev.includes(caseId) ? prev : [...prev, caseId]
//           );
//           // Show the first waiting HITL case immediately
//           setActiveHITLCase(cur => cur ?? caseId);
//         }
 
//         if (["completed", "rejected", "error"].includes(s.status)) {
//           // Stop polling this case
//           batchPollsRef.current[caseId]?.();
//           delete batchPollsRef.current[caseId];
 
//           // Remove from HITL queue if it was there
//           setHitlQueuedIds(prev => {
//             const next = prev.filter(id => id !== caseId);
//             return next;
//           });
 
//           // If this was the active HITL case, advance to the next
//           setActiveHITLCase(cur => {
//             if (cur === caseId) {
//               const remaining = hitlQueuedIds.filter(id => id !== caseId);
//               return remaining[0] ?? null;
//             }
//             return cur;
//           });
//         }
//       });
//       batchPollsRef.current[caseId] = stop;
//     });
 
//     return () => {
//       Object.values(batchPollsRef.current).forEach(stop => stop?.());
//       batchPollsRef.current = {};
//     };
//   }, [JSON.stringify(batchCaseIds)]); // eslint-disable-line react-hooks/exhaustive-deps
 
//   // Advance activeHITLCase whenever hitlQueuedIds changes
//   useEffect(() => {
//     if (!activeHITLCase && hitlQueuedIds.length > 0) {
//       setActiveHITLCase(hitlQueuedIds[0]);
//     }
//   }, [hitlQueuedIds, activeHITLCase]);
 
//   // ── Cleanup on unmount ──────────────────────────────────────────
//   useEffect(() => {
//     return () => {
//       stopPollRef.current?.();
//       Object.values(batchPollsRef.current).forEach(stop => stop?.());
//     };
//   }, []);
 
//   useEffect(() => {
//     if (propCaseId && propCaseId !== auditCaseId) watchCase(propCaseId);
//   }, [propCaseId]); // eslint-disable-line react-hooks/exhaustive-deps
 
//   useEffect(() => {
//     if (propCaseId || isBatchMode) return;
//     const active = cases.find(c => ["running","pending","hitl_pending"].includes(c.status));
//     if (active && active.audit_case_id !== auditCaseId) watchCase(active.audit_case_id);
//   }, [cases]); // eslint-disable-line react-hooks/exhaustive-deps
 
//   const agentLabels = [
//     { keys:["ingestion_excel","ingestion_audit_meta","api_ingestion_node"], label:"Ingestion Agent",   sub:"Payroll + audit metadata" },
//     { keys:["ingestion_xml"],                          label:"Policy Parser",     sub:"XML class codes & rates" },
//     { keys:["officer_agent"],                          label:"Officer Agent",     sub:"Officer classification" },
//     { keys:["class_code_agent"],                       label:"Class Code Agent",  sub:"Class code validation" },
//     { keys:["frequency_agent"],                        label:"Frequency Agent",   sub:"Submission frequency" },
//     { keys:["premium_agent","risk_assessor"],          label:"Premium Agent",     sub:"Variance & risk scoring" },
//     { keys:["explanation_agent"],                      label:"Explanation Agent", sub:"AI narrative" },
//   ];
 
//   const resolveStepStatus = (keys) => {
//     let anyError = false, doneCount = 0;
//     for (const k of keys) {
//       if (agentStatus[k] === "error")    anyError = true;
//       if (agentStatus[k] === "complete") doneCount++;
//     }
//     if (anyError)                  return "error";
//     if (doneCount === keys.length) return "complete";
//     if (doneCount > 0)             return "partial";
//     return "pending";
//   };
 
//   // ── Batch summary helpers ────────────────────────────────────────
//   const batchDone      = Object.values(batchStatuses).filter(s => s.status === "completed").length;
//   const batchRejected  = Object.values(batchStatuses).filter(s => s.status === "rejected").length;
//   const batchError_cnt = Object.values(batchStatuses).filter(s => s.status === "error").length;
//   const batchRunning   = Object.values(batchStatuses).filter(s => ["pending","processing","running"].includes(s.status)).length;
//   const batchHITL      = hitlQueuedIds.length;
 
//   const activeHITLStatus = activeHITLCase ? batchStatuses[activeHITLCase] : null;
 
//   // ── HITL decision handler for batch mode ────────────────────────
//   const handleBatchHITL = async (decision, note) => {
//     if (!activeHITLCase) return;
//     try {
//       await submitHITLDecision(activeHITLCase, { decision, notes: note });
//       const fresh = await getAuditStatus(activeHITLCase);
//       setBatchStatuses(prev => ({ ...prev, [activeHITLCase]: fresh }));
//       onCaseCreated?.();
 
//       // Remove from HITL queue and advance
//       setHitlQueuedIds(prev => {
//         const next = prev.filter(id => id !== activeHITLCase);
//         setActiveHITLCase(next[0] ?? null);
//         return next;
//       });
//     } catch (err) {
//       alert("HITL submission failed: " + (err.response?.data?.detail || err.message));
//     }
//   };
 
//   // ════════════════════════════════════════════════════════════════
//   // RENDER
//   // ════════════════════════════════════════════════════════════════
//   return (
//     <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
 
//       {/* Header card */}
//       <div style={{ background:`linear-gradient(135deg, ${C.navy} 0%, ${C.navyLt} 100%)`,
//         borderRadius:14, padding:28, color:"#fff" }}>
//         <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
//           <div>
//             <h2 style={{ margin:"0 0 6px", fontSize:22, fontWeight:800 }}>🤖 AI Audit Engine</h2>
//             <p style={{ margin:0, opacity:0.7, fontSize:14 }}>
//               LangGraph-powered multi-agent orchestration for automated earned exposure &amp; premium variance detection
//             </p>
//           </div>
//           {/* Single-case badge */}
//           {!isBatchMode && auditCaseId && (
//             <div style={{ textAlign:"right" }}>
//               <div style={{ fontSize:12, opacity:0.6, marginBottom:4 }}>Monitoring Case</div>
//               <div style={{ fontSize:22, fontWeight:800 }}>#{auditCaseId}</div>
//               {status && <StatusBadge status={status.status} />}
//             </div>
//           )}
//           {/* Batch badge */}
//           {isBatchMode && (
//             <div style={{ textAlign:"right", minWidth:160 }}>
//               <div style={{ fontSize:12, opacity:0.6, marginBottom:4 }}>Batch Mode</div>
//               <div style={{ fontSize:22, fontWeight:800 }}>{batchCaseIds.length} policies</div>
//               <div style={{ fontSize:12, opacity:0.6, marginTop:4 }}>
//                 ✅ {batchDone} done · ⚠️ {batchHITL} HITL · ⚙️ {batchRunning} running
//               </div>
//             </div>
//           )}
//         </div>
//         {!auditCaseId && !isBatchMode && (
//           <div style={{ marginTop:16, padding:"12px 16px", background:"rgba(255,255,255,0.07)",
//             borderRadius:10, fontSize:13, opacity:0.8 }}>
//             Upload files in <strong>Data Upload</strong> to run an audit. The AI pipeline will
//             automatically appear here once started.
//           </div>
//         )}
//       </div>
 
//       {/* ══════════════════════════════════════
//           BATCH MODE: KPI bar + HITL queue
//       ══════════════════════════════════════ */}
//       {isBatchMode && (
//         <>
//           {/* Batch progress KPIs */}
//           <div style={{ display:"flex", gap:14 }}>
//             <KpiCard label="Total Queued"   value={batchCaseIds.length}  sub="From API batch"          accent={C.accent} />
//             <KpiCard label="Completed"      value={batchDone}            sub="Fully audited"           accent={C.green}  />
//             <KpiCard label="HITL Pending"   value={batchHITL}            sub="Awaiting your review"    accent={C.amber}  />
//             <KpiCard label="Running"        value={batchRunning}         sub="In pipeline"             accent={C.purple} />
//             {(batchRejected + batchError_cnt) > 0 && (
//               <KpiCard label="Issues"       value={batchRejected + batchError_cnt} sub="Rejected / Error" accent={C.red} />
//             )}
//           </div>
 
//           {/* HITL review queue banner */}
//           {hitlQueuedIds.length > 0 && (
//             <div style={{ background:"linear-gradient(135deg, #FEF3C7, #FDE68A)",
//               border:`1px solid ${C.amber}`, borderRadius:12, padding:"14px 20px",
//               display:"flex", alignItems:"center", gap:14 }}>
//               <span style={{ fontSize:28 }}>⚠️</span>
//               <div style={{ flex:1 }}>
//                 <div style={{ fontSize:14, fontWeight:800, color:"#78350F" }}>
//                   {hitlQueuedIds.length} policy(ies) require human review
//                 </div>
//                 <div style={{ fontSize:12, color:"#92400E", marginTop:2 }}>
//                   Reviewing case #{activeHITLCase} now
//                   {hitlQueuedIds.length > 1
//                     ? ` · ${hitlQueuedIds.length - 1} more in queue after this`
//                     : ""}
//                 </div>
//               </div>
//               {/* Queue pills */}
//               <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
//                 {hitlQueuedIds.map((id, i) => (
//                   <button key={id} onClick={() => setActiveHITLCase(id)}
//                     style={{ background: id === activeHITLCase ? C.amber : "rgba(0,0,0,0.1)",
//                       color: id === activeHITLCase ? "#fff" : "#78350F",
//                       border:"none", borderRadius:20, padding:"4px 12px",
//                       fontSize:12, fontWeight:700, cursor:"pointer" }}>
//                     #{id}{i === 0 && id === activeHITLCase ? " ← now" : ""}
//                   </button>
//                 ))}
//               </div>
//             </div>
//           )}
 
//           {/* Active HITL panel */}
//           {activeHITLCase && activeHITLStatus && (
//             <div style={{ background:C.card, border:`2px solid ${C.amber}`, borderRadius:14, padding:24 }}>
//               <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
//                 <div>
//                   <div style={{ fontSize:16, fontWeight:800, color:C.text }}>
//                     Reviewing: {activeHITLStatus.policy_number} — Case #{activeHITLCase}
//                   </div>
//                   <div style={{ fontSize:12, color:C.muted, marginTop:2 }}>
//                     Risk: <strong style={{ color:C.red }}>{activeHITLStatus.risk_level?.toUpperCase()}</strong>
//                     &nbsp;·&nbsp;Variance: <strong>{Number(activeHITLStatus.variance_pct || 0).toFixed(2)}%</strong>
//                     &nbsp;·&nbsp;Rec: <strong>{activeHITLStatus.recommendation?.replace(/_/g," ")}</strong>
//                   </div>
//                 </div>
//                 <div style={{ display:"flex", gap:8 }}>
//                   <RiskBadge risk={activeHITLStatus.risk_level} />
//                   <StatusBadge status={activeHITLStatus.status} />
//                 </div>
//               </div>
//               <ResultsAndHITLPanel
//                 status={activeHITLStatus}
//                 onApprove={handleBatchHITL}
//               />
//             </div>
//           )}
 
//           {/* Batch policy status grid — card / table toggle */}
//           <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>

//             {/* Header row with toggle */}
//             <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:18 }}>
//               <div>
//                 <h2 style={{ margin:0, fontSize:18, fontWeight:700, color:C.text }}>
//                   Batch Policy Progress
//                 </h2>
//                 <p style={{ margin:"4px 0 0", fontSize:13, color:C.muted }}>
//                   All policies queued in this API batch — click a HITL case to review it
//                 </p>
//               </div>

//               {/* View toggle pill */}
//               <div style={{ display:"flex", background:C.bg, border:`1px solid ${C.border}`,
//                 borderRadius:10, overflow:"hidden", flexShrink:0 }}>
//                 {[
//                   { key:"card",  icon:"⊞", label:"Cards"  },
//                   { key:"table", icon:"☰", label:"Table"  },
//                 ].map(({ key, icon, label }) => (
//                   <button key={key} onClick={() => setBatchView(key)}
//                     style={{
//                       display:"flex", alignItems:"center", gap:6,
//                       padding:"7px 16px", border:"none", cursor:"pointer",
//                       fontWeight:700, fontSize:12,
//                       background: batchView === key
//                         ? `linear-gradient(135deg, ${C.accent}, ${C.teal})`
//                         : "transparent",
//                       color: batchView === key ? "#fff" : C.muted,
//                       transition:"all 0.15s",
//                     }}>
//                     <span style={{ fontSize:14 }}>{icon}</span>
//                     {label}
//                   </button>
//                 ))}
//               </div>
//             </div>

//             {/* ── CARD VIEW ── */}
//             {batchView === "card" && (
//               <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(260px, 1fr))", gap:10 }}>
//                 {batchCaseIds.map(caseId => {
//                   const s        = batchStatuses[caseId];
//                   const isHITL   = hitlQueuedIds.includes(caseId);
//                   const isActive = caseId === activeHITLCase;
//                   const varPct   = s?.variance_pct != null ? Number(s.variance_pct) : null;
//                   const varColor = varPct == null ? C.muted
//                                  : Math.abs(varPct) > 20 ? C.red
//                                  : Math.abs(varPct) > 10 ? C.amber : C.green;
//                   return (
//                     <div key={caseId}
//                       onClick={() => isHITL && setActiveHITLCase(caseId)}
//                       style={{
//                         background: isActive ? "#FFFBEB" : isHITL ? "#FFFDE7" : C.bg,
//                         border: isActive ? `2px solid ${C.amber}`
//                                : isHITL  ? `1px solid ${C.amber}`
//                                : `1px solid ${C.border}`,
//                         borderRadius:10, padding:"14px 16px",
//                         cursor:isHITL ? "pointer" : "default",
//                         transition:"all 0.15s", position:"relative",
//                       }}
//                       onMouseEnter={e => { if (!isHITL) e.currentTarget.style.background = "#F5F8FF"; }}
//                       onMouseLeave={e => {
//                         e.currentTarget.style.background =
//                           isActive ? "#FFFBEB" : isHITL ? "#FFFDE7" : C.bg;
//                       }}>

//                       {/* Policy number + status */}
//                       <div style={{ display:"flex", justifyContent:"space-between",
//                         alignItems:"center", marginBottom:6 }}>
//                         <div style={{ fontSize:13, fontWeight:800, color:C.accent }}>
//                           {s?.policy_number || `Case #${caseId}`}
//                         </div>
//                         <StatusBadge status={s?.status || "pending"} />
//                       </div>

//                       {/* Case ID + risk */}
//                       <div style={{ display:"flex", justifyContent:"space-between",
//                         alignItems:"center", marginBottom:4 }}>
//                         <div style={{ fontSize:11, color:C.muted }}>Case #{caseId}</div>
//                         {s?.risk_level && <RiskBadge risk={s.risk_level} />}
//                       </div>

//                       {/* Variance bar */}
//                       {varPct != null && (
//                         <div style={{ marginTop:8 }}>
//                           <div style={{ display:"flex", justifyContent:"space-between",
//                             fontSize:11, color:C.muted, marginBottom:3 }}>
//                             <span>Variance</span>
//                             <span style={{ fontWeight:700, color:varColor }}>
//                               {varPct > 0 ? "+" : ""}{varPct.toFixed(1)}%
//                             </span>
//                           </div>
//                           <div style={{ background:C.border, borderRadius:4, height:4, overflow:"hidden" }}>
//                             <div style={{
//                               width:`${Math.min(Math.abs(varPct) * 2.5, 100)}%`,
//                               height:"100%", background:varColor,
//                               borderRadius:4, transition:"width 0.4s",
//                             }} />
//                           </div>
//                         </div>
//                       )}

//                       {/* HITL indicator */}
//                       {isHITL && (
//                         <div style={{ marginTop:8, fontSize:11, fontWeight:700, color:C.amber,
//                           display:"flex", alignItems:"center", gap:4 }}>
//                           ⚠️ {isActive ? "Reviewing now" : "Click to review"}
//                         </div>
//                       )}

//                       {/* Earned premium */}
//                       {/* {s?.overall_variance?.earned_premium != null && (
//                         <div style={{ marginTop:6, fontSize:11, color:C.muted }}>
//                           Premium: <strong style={{ color:C.text }}>
//                             {money(Math.round(s.overall_variance.earned_premium))}
//                           </strong>
//                         </div>
//                       )} */}
//                       {(() => {
//                         const ov       = s?.overall_variance || {};
//                         const isPend   = ["pending","processing","running"].includes(s?.status);
//                         const premium  = isPend
//                           ? (ov.earned_premium  || ov.est_ytd_premium || 0)
//                           : (ov.earned_premium  || ov.est_ytd_premium || 0);
//                         const label    = (isPend && !ov.earned_premium && ov.est_ytd_premium)
//                           ? "Est. Premium"
//                           : "Premium";
//                         if (!premium) return null;
//                         return (
//                           <div style={{ marginTop:6, fontSize:11, color:C.muted }}>
//                             {label}: <strong style={{ color:C.text }}>
//                               {money(Math.round(premium))}
//                             </strong>
//                           </div>
//                         );
//                       })()}
//                     </div>
//                   );
//                 })}
//               </div>
//             )}

//             {/* ── TABLE VIEW ── */}
//             {batchView === "table" && (
//               <div style={{ overflowX:"auto" }}>
//                 <table style={{ width:"100%", borderCollapse:"collapse" }}>
//                   <thead>
//                     <tr style={{ borderBottom:`2px solid ${C.border}`, background:"#F8FAFD" }}>
//                       {["#","Policy Number","Case ID","Status","Risk","Variance %",
//                         "Earned Premium","Recommendation","Action"].map(h => (
//                         <th key={h} style={{ textAlign:"left", padding:"10px 14px", fontSize:11,
//                           fontWeight:700, color:C.muted, textTransform:"uppercase",
//                           letterSpacing:0.7, whiteSpace:"nowrap" }}>{h}</th>
//                       ))}
//                     </tr>
//                   </thead>
//                   <tbody>
//                     {batchCaseIds.map((caseId, idx) => {
//                       const s        = batchStatuses[caseId];
//                       const isHITL   = hitlQueuedIds.includes(caseId);
//                       const isActive = caseId === activeHITLCase;
//                       const varPct   = s?.variance_pct != null ? Number(s.variance_pct) : null;
//                       const varColor = varPct == null ? C.muted
//                                      : Math.abs(varPct) > 20 ? C.red
//                                      : Math.abs(varPct) > 10 ? C.amber : C.green;
//                       const rowBg    = isActive ? "#FFFBEB" : isHITL ? "#FFFDE7" : "transparent";
//                       return (
//                         <tr key={caseId}
//                           onClick={() => isHITL && setActiveHITLCase(caseId)}
//                           style={{
//                             borderBottom:`1px solid ${C.border}`,
//                             background:rowBg,
//                             cursor:isHITL ? "pointer" : "default",
//                             transition:"background 0.15s",
//                           }}
//                           onMouseEnter={e => {
//                             if (!isHITL && !isActive) e.currentTarget.style.background = "#F5F8FF";
//                           }}
//                           onMouseLeave={e => {
//                             e.currentTarget.style.background = rowBg;
//                           }}>

//                           {/* # */}
//                           <td style={{ padding:"12px 14px", fontSize:12, color:C.muted,
//                             fontWeight:600 }}>{idx + 1}</td>

//                           {/* Policy Number */}
//                           <td style={{ padding:"12px 14px", fontSize:13, fontWeight:800,
//                             color:C.accent }}>
//                             {s?.policy_number || "—"}
//                             {isHITL && (
//                               <span style={{ marginLeft:6, fontSize:10, fontWeight:700,
//                                 color:C.amber }}>
//                                 ⚠️ {isActive ? "reviewing" : "HITL"}
//                               </span>
//                             )}
//                           </td>

//                           {/* Case ID */}
//                           <td style={{ padding:"12px 14px", fontSize:12, color:C.muted }}>
//                             #{caseId}
//                           </td>

//                           {/* Status */}
//                           <td style={{ padding:"12px 14px" }}>
//                             <StatusBadge status={s?.status || "pending"} />
//                           </td>

//                           {/* Risk */}
//                           <td style={{ padding:"12px 14px" }}>
//                             {s?.risk_level ? <RiskBadge risk={s.risk_level} /> : <span style={{ color:C.muted }}>—</span>}
//                           </td>

//                           {/* Variance % with mini bar */}
//                           <td style={{ padding:"12px 14px", minWidth:110 }}>
//                             {varPct != null ? (
//                               <div>
//                                 <div style={{ fontWeight:700, fontSize:13, color:varColor, marginBottom:3 }}>
//                                   {varPct > 0 ? "+" : ""}{varPct.toFixed(1)}%
//                                 </div>
//                                 <div style={{ background:C.border, borderRadius:4, height:4, width:80 }}>
//                                   <div style={{
//                                     width:`${Math.min(Math.abs(varPct) * 2.5, 100)}%`,
//                                     height:"100%", background:varColor, borderRadius:4,
//                                   }} />
//                                 </div>
//                               </div>
//                             ) : <span style={{ color:C.muted }}>—</span>}
//                           </td>

//                           {/* Earned Premium */}
//                           {/* <td style={{ padding:"12px 14px", fontSize:13, fontWeight:600,
//                             color:C.text }}>
//                             {s?.overall_variance?.earned_premium != null
//                               ? money(Math.round(s.overall_variance.earned_premium))
//                               : "—"}
//                           </td> */}

//                           <td style={{ padding:"12px 14px", fontSize:13, fontWeight:600,
//                             color:C.text }}>
//                             {(() => {
//                               const ov      = s?.overall_variance || {};
//                               const premium = ov.earned_premium || ov.est_ytd_premium || 0;
//                               return premium ? money(Math.round(premium)) : "—";
//                             })()}
//                           </td>

//                           {/* Recommendation */}
//                           <td style={{ padding:"12px 14px", fontSize:12, color:C.muted }}>
//                             {s?.recommendation
//                               ? s.recommendation.replace(/_/g, " ")
//                               : "—"}
//                           </td>

//                           {/* Action */}
//                           <td style={{ padding:"12px 14px" }}>
//                             {isHITL ? (
//                               <button
//                                 onClick={e => { e.stopPropagation(); setActiveHITLCase(caseId); }}
//                                 style={{ background:C.amber, color:"#fff", border:"none",
//                                   borderRadius:6, padding:"5px 12px", fontSize:11,
//                                   fontWeight:700, cursor:"pointer", whiteSpace:"nowrap" }}>
//                                 Review ▲
//                               </button>
//                             ) : (
//                               <span style={{ fontSize:12, color:C.muted }}>—</span>
//                             )}
//                           </td>
//                         </tr>
//                       );
//                     })}
//                   </tbody>
//                 </table>

//                 {batchCaseIds.length === 0 && (
//                   <div style={{ textAlign:"center", padding:40, color:C.muted, fontSize:14 }}>
//                     No policies in this batch yet.
//                   </div>
//                 )}
//               </div>
//             )}
//           </div>
//         </>
//       )}
 
//       {/* ══════════════════════════════════════
//           SINGLE-CASE MODE (original layout)
//       ══════════════════════════════════════ */}
//       {!isBatchMode && (
//         <div style={{ display:"flex", gap:16 }}>
//           {/* Agent Pipeline */}
//           <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24, flex:1 }}>
//             <SectionHeader title="Agent Pipeline Status" sub="Real-time LangGraph orchestration" />
//             <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
//               {agentLabels.map((a, i) => {
//                 const st        = resolveStepStatus(a.keys);
//                 const bgColor   = st === "complete" ? "#F0FDF4" : st === "error" ? "#FEF2F2" : st === "partial" ? "#EEF2FF" : C.bg;
//                 const bdColor   = st === "complete" ? C.green   : st === "error" ? C.red     : st === "partial" ? C.accent  : C.border;
//                 const circleClr = st === "complete" ? C.green   : st === "error" ? C.red     : st === "partial" ? C.accent  : C.border;
//                 const badge     = st === "complete" ? { bg:"#DCFCE7", color:C.green,  text:"Done" }
//                                 : st === "error"    ? { bg:"#FEE2E2", color:C.red,    text:"Error" }
//                                 : st === "partial"  ? { bg:"#DBEAFE", color:C.accent, text:"Running" }
//                                 :                    { bg:"#F3F4F6", color:C.muted,   text:"Pending" };
//                 const subText   = st === "complete" ? a.sub
//                                 : st === "error"    ? "Error encountered"
//                                 : st === "partial"  ? "Processing…" : "Waiting…";
//                 return (
//                   <div key={a.keys.join()} style={{ display:"flex", alignItems:"center", gap:14,
//                     padding:"12px 16px", borderRadius:10, transition:"all 0.3s",
//                     background:bgColor, border:`1px solid ${bdColor}` }}>
//                     <div style={{ width:32, height:32, borderRadius:"50%", flexShrink:0,
//                       display:"flex", alignItems:"center", justifyContent:"center", fontSize:14,
//                       background:circleClr, color: st === "pending" ? C.muted : "#fff" }}>
//                       {st === "complete" ? "✓" : st === "error" ? "✗" : st === "partial" ? "⚙" : i + 1}
//                     </div>
//                     <div style={{ flex:1 }}>
//                       <div style={{ fontSize:13, fontWeight:700, color:C.text }}>{a.label}</div>
//                       <div style={{ fontSize:11, color:C.muted }}>{subText}</div>
//                     </div>
//                     <span style={{ fontSize:11, fontWeight:600, padding:"3px 10px", borderRadius:20,
//                       background:badge.bg, color:badge.color }}>{badge.text}</span>
//                   </div>
//                 );
//               })}
//             </div>
//           </div>
 
//           {/* Live log + results */}
//           <div style={{ flex:1, display:"flex", flexDirection:"column", gap:16 }}>
//             <div style={{ background:C.navy, borderRadius:14, padding:20, flex:1, minHeight:300 }}>
//               <div style={{ fontSize:13, fontWeight:700, color:"#64B5F6", marginBottom:12,
//                 fontFamily:"monospace" }}>▶ AUDIT LOG</div>
//               <div style={{ fontFamily:"'Courier New', monospace", fontSize:11.5, color:"#A8D8A8",
//                 lineHeight:1.8, overflowY:"auto", maxHeight:280 }}>
//                 {logs.length === 0
//                   ? <span style={{ color:"#546E7A" }}>// Upload files then start an audit to see live output</span>
//                   : logs.map((l, i) => <div key={i}>{l}</div>)}
//               </div>
//             </div>
 
//             {status && ["completed","hitl_pending"].includes(status.status) && (
//               <ResultsAndHITLPanel status={status} onApprove={async (decision, note) => {
//                 try {
//                   await submitHITLDecision(status.audit_case_id, { decision, notes: note });
//                   const fresh = await getAuditStatus(status.audit_case_id);
//                   setStatus(fresh);
//                   onCaseCreated?.();
//                   const ts = new Date().toLocaleTimeString();
//                   setLogs(l => [...l, `[${ts}] ✓ HITL decision submitted: ${decision}`]);
//                 } catch (err) {
//                   alert("HITL submission failed: " + (err.response?.data?.detail || err.message));
//                 }
//               }} />
//             )}
//           </div>
//         </div>
//       )}
//     </div>
//   );
// }
 
// // ── Audit Detail ──────────────────────────────────────────────────────────────
// function AuditDetail({ auditCase, setScreen, onHITLDecision }) {
//   const [tab,        setTab]        = useState("overview");
//   const [detail,     setDetail]     = useState(auditCase);
//   const [hitlNote,   setHitlNote]   = useState("");
//   const [submitting, setSubmitting] = useState(false);
//   const {
//     canViewReports,
//     canUpload,
//     canApproveHITL,
//     canViewAllTenants,
//     displayRole,
//     isSuperAdmin,
//     canViewAIAudit,
//     canViewVariance,
//     canViewDashboard,
//     canViewPolicies,
//   } = useWCRoles();
//   useEffect(() => {
//     if (!auditCase?.audit_case_id) return;
 
//     // ── Single fetch on mount only — no polling. ─────────────────────────────
//     // The AI Audit screen handles live progress while a job runs.
//     // This Review screen is read-only; it loads the full record once, then stops.
//     // The only subsequent requests are explicit user actions:
//     //   • HITL approve / reject  (handleHITL → POST + GET)
//     //   • Narrative save         (future endpoint → POST + GET)
//     let isMounted = true;
 
//     getAuditStatus(auditCase.audit_case_id)
//       .then(fresh => { if (isMounted) setDetail(fresh); })
//       .catch(() => { if (isMounted) setDetail(auditCase); });
 
//     return () => { isMounted = false; };
 
//   }, [auditCase?.audit_case_id]);
 
//   if (!detail) return (
//     <div style={{ padding:40, color:C.muted, textAlign:"center" }}>
//       Select a case to review
//     </div>
//   );
 
//   const tabs = ["overview","class-codes","payroll","narrative","decision"];
//   const ov   = detail.overall_variance || {};
 
//   // Derived fields for detail view
//   const exposureDelta = (ov.est_exposure || 0) - (ov.earned_exposure || 0);
//   const classCodes    = [...new Set((detail.class_code_variance || []).map(r => r.ClassCode))].join(", ") || "—";
 
//   // Payroll calendar helpers
//   const buildPayrollCalendar = () => {
//     const MONTHS   = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
//     const firstDt  = detail.first_check_date ? new Date(detail.first_check_date) : null;
//     const lastDt   = detail.last_check_date  ? new Date(detail.last_check_date)  : null;
//     const year     = firstDt ? firstDt.getFullYear() : new Date().getFullYear();
 
//     return MONTHS.map((m, i) => {
//       const monthStart = new Date(year, i, 1);
//       const monthEnd   = new Date(year, i + 1, 0);
//       const inRange    = firstDt && lastDt && monthStart <= lastDt && monthEnd >= firstDt;
//       return { m, inRange };
//     });
//   };
 
//   const handleHITL = async (decision) => {
//     setSubmitting(true);
//     try {
//       await submitHITLDecision(detail.audit_case_id, { decision, notes: hitlNote });
//       const fresh = await getAuditStatus(detail.audit_case_id);
//       setDetail(fresh);
//       onHITLDecision?.();
//     } catch (err) {
//       alert("HITL decision failed: " + err.message);
//     } finally {
//       setSubmitting(false);
//     }
//   };

//   const buildClassCodeChartData = (data) => {
//   return (data.class_code_variance || []).map(row => ({
//     code: row.ClassCode,
//     earned: row.earned_premium,
//     estimated: row.est_ytd_premium,
//     variance: row.variance,
//     variance_pct: row.variance_pct
//   }));
// };

// const chartData = buildClassCodeChartData(detail);
 
//   return (
//     <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
 
//       {/* Header */}
//       <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
//         <div>
//           <button onClick={() => setScreen("policies")}
//             style={{ background:"none", border:"none", color:C.accent, cursor:"pointer",
//               fontSize:13, padding:"0 0 6px", fontWeight:600 }}>
//             ← Back to Policies
//           </button>
//           <h2 style={{ margin:0, fontSize:22, fontWeight:800, color:C.text }}>
//             {detail.policy_number} — Case #{detail.audit_case_id}
//           </h2>
//           <div style={{ display:"flex", gap:10, marginTop:8, flexWrap:"wrap" }}>
//             <span style={{ fontSize:13, color:C.muted }}>
//               Earned Premium: <strong>{money(Math.round(ov.earned_premium || 0))}</strong>
//             </span>
//           </div>
//         </div>
//         <div style={{ display:"flex", gap:10 }}>
//           <RiskBadge risk={detail.risk_level} />
//           <StatusBadge status={detail.status} />
//         </div>
//       </div>
 
//       {/* KPI row */}
//       <div style={{ display:"flex", gap:14 }}>
//         <KpiCard
//           label="Variance"
//           value={`${Number(ov.variance_pct || 0).toFixed(1)}%`}
//           sub={ov.variance_pct > 10 ? "Above threshold" : "Within range"}
//           subColor={ov.variance_pct > 10 ? C.red : C.green}
//           accent={ov.variance_pct > 10 ? C.red : C.amber} />
//         <KpiCard
//           label="Exposure Delta"
//           value={money(Math.round(Math.abs(exposureDelta)))}
//           sub="EST Exposure vs. Earned Exposure"
//           accent={C.red} />
//         <KpiCard
//           label="EST YTD Premium"
//           value={money(Math.round(ov.est_ytd_premium || 0))}
//           sub="Estimated owed"
//           accent={C.amber} />
//         <KpiCard
//           label="Confidence Score"
//           value="94%"
//           sub="AI finding accuracy"
//           accent={C.green} />
//       </div>
 
//       {/* Tab panel */}
//       <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, overflow:"hidden" }}>
//         <div style={{ display:"flex", borderBottom:`1px solid ${C.border}`, background:"#F8FAFD" }}>
//           {tabs.map(t => (
//             <button key={t} onClick={() => setTab(t)}
//               style={{ flex:1, padding:"14px 10px", border:"none", background:"none", cursor:"pointer",
//                 fontSize:12, fontWeight:700, textTransform:"capitalize",
//                 color:tab === t ? C.accent : C.muted,
//                 borderBottom:tab === t ? `3px solid ${C.accent}` : "3px solid transparent",
//                 transition:"all 0.15s" }}>
//               {t.replace("-"," ")}
//             </button>
//           ))}
//         </div>
 
//         <div style={{ padding:24 }}>
 
//           {/* ── Overview tab ── */}
//           {tab === "overview" && (() => {
//             // EE Officers on Payroll — "X of Y correctly assigned"
//             const officerTotal   = detail.officer_count;
//             const officerIssues  = detail.officer_issues_count ?? 0;
//             const officerDisplay = officerTotal != null
//               ? `${officerTotal - officerIssues} of ${officerTotal} correctly assigned`
//               : "—";
 
//             // Actual Payroll Submissions — "X of Y expected"
//             const actualSubs    = detail.submitted_count;
//             const expectedSubs  = detail.expected_submissions;
//             const actualDisplay = actualSubs != null
//               ? expectedSubs != null
//                 ? `${actualSubs} of ${expectedSubs} expected`
//                 : String(actualSubs)
//               : "—";
 
//             // Format last check date: "2026-02-20" or "02/20/2026" → "Feb 20, 2026"
//             const fmtCheckDate = (raw) => {
//               if (!raw) return "—";
//               try {
//                 const d = new Date(raw.includes("/")
//                   ? raw.replace(/(\d{2})\/(\d{2})\/(\d{4})/, "$3-$1-$2")
//                   : raw);
//                 if (isNaN(d.getTime())) return raw;
//                 return d.toLocaleDateString("en-US", { month:"short", day:"numeric", year:"numeric" });
//               } catch { return raw; }
//             };
 
//             return (
//               <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14 }}>
//                 {[
//                   { label:"Effective Date",               value: detail.effective_date  || "—" },
//                   { label:"Expiration Date",              value: detail.expiration_date || "—" },
//                   { label:"Payment Frequency",            value: detail.payment_frequency || "—" },
//                   { label:"Class Codes",                  value: classCodes },
//                   { label:"EE Officers on Payroll",       value: officerDisplay },
//                   { label:"Actual Payroll Submissions",   value: actualDisplay },
//                   { label:"Expected Payroll Submissions", value: expectedSubs != null ? String(expectedSubs) : "—" },
//                   { label:"Last Check Date Reported",     value: fmtCheckDate(detail.last_check_date) },
//                 ].map(({ label, value }) => (
//                   <div key={label} style={{ background:C.bg, borderRadius:10, padding:"14px 18px" }}>
//                     <div style={{ fontSize:11, color:C.muted, fontWeight:600, textTransform:"uppercase",
//                       letterSpacing:0.8, marginBottom:4 }}>{label}</div>
//                     <div style={{ fontSize:14, fontWeight:700, color:C.text }}>{value}</div>
//                   </div>
//                 ))}
//               </div>
//             );
//           })()}
 
//           {/* ── Class Codes tab ── */}
//           {tab === "class-codes" && (
//             <div>
//               {(detail.class_code_variance?.some(r => r.is_flagged)) && (
//                 <div style={{ marginBottom:16, padding:"12px 16px", background:"#FEF3C7",
//                   borderRadius:10, border:`1px solid ${C.amber}`, fontSize:13, color:"#92400E" }}>
//                   ⚠️ <strong>{detail.class_code_variance.filter(r => r.is_flagged).length} flagged class code(s).</strong>{" "}
//                   Review before finalizing.
//                 </div>
//               )}
//               {(!detail.class_code_variance || detail.class_code_variance.length === 0) ? (
//                 <div style={{ textAlign:"center", padding:40, color:C.muted }}>No class code data available.</div>
//               ) : (
//                 <table style={{ width:"100%", borderCollapse:"collapse" }}>
//                   <thead>
//                     <tr style={{ borderBottom:`2px solid ${C.border}`, background:"#F8FAFD" }}>
//                       {["Class Code","Description","EST YTD Premium","Earned Premium","Delta","Flag"].map(h => (
//                         <th key={h} style={{ padding:"10px 14px", textAlign:"left", fontSize:11,
//                           color:C.muted, fontWeight:700, textTransform:"uppercase" }}>{h}</th>
//                       ))}
//                     </tr>
//                   </thead>
//                   <tbody>
//                     {detail.class_code_variance.map((row, i) => {
//                       const delta = (row.est_ytd_premium || 0) - (row.earned_premium || 0);
//                       return (
//                         <tr key={i} style={{ borderBottom:`1px solid ${C.border}` }}>
//                           <td style={{ padding:"12px 14px", fontSize:13, fontWeight:700, color:C.accent }}>
//                             {row.ClassCode}
//                           </td>
//                           <td style={{ padding:"12px 14px", fontSize:13, color:C.muted }}>
//                             {row.StateCode}
//                           </td>
//                           <td style={{ padding:"12px 14px", fontSize:13 }}>
//                             {money(Math.round(row.est_ytd_premium || 0))}
//                           </td>
//                           <td style={{ padding:"12px 14px", fontSize:13 }}>
//                             {money(Math.round(row.earned_premium || 0))}
//                           </td>
//                           <td style={{ padding:"12px 14px", fontSize:13, fontWeight:700,
//                             color: delta > 0 ? C.red : C.green }}>
//                             {delta > 0 ? "+" : ""}{money(Math.round(delta))}
//                           </td>
//                           <td style={{ padding:"12px 14px" }}>
//                             {row.is_flagged
//                               ? <span style={{ background:"#FEE2E2", color:C.red, padding:"2px 10px", borderRadius:20, fontSize:11, fontWeight:700 }}>⚠ Flag</span>
//                               : <span style={{ background:"#D1FAE5", color:C.green, padding:"2px 10px", borderRadius:20, fontSize:11, fontWeight:700 }}>✓ OK</span>}
//                           </td>
//                         </tr>
//                       );
//                     })}
//                   </tbody>
//                 </table>
//               )}
//               <div style={{
//   background: C.card,
//   border: `1px solid ${C.border}`,
//   borderRadius: 14,
//   padding: 24
// }}>
//   <SectionHeader
//     title="Variance by Class Code"
//     sub="Positive = Additional Premium | Negative = Refund"
//   />

//   <ResponsiveContainer width="100%" height={220}>
//     <BarChart data={chartData}>
//       <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
      
//       <XAxis dataKey="code" />
//       <YAxis />
      
//       <Tooltip
//         formatter={(value) => `$${value.toLocaleString()}`}
//       />

//       <Bar
//         dataKey="variance"
//         name="Variance"
//         radius={[4,4,0,0]}
//       >
//         {chartData.map((entry, index) => (
//           <Cell
//             key={`cell-${index}`}
//             fill={entry.variance > 0 ? C.red : C.green}
//           />
//         ))}
//       </Bar>
//     </BarChart>
//   </ResponsiveContainer>
// </div>
//             </div>
//           )}
 
//           {/* ── Payroll tab ── */}
//           {tab === "payroll" && (
//             <div>
//               <div style={{ display:"flex", gap:8, marginBottom:16, flexWrap:"wrap" }}>
//                 {buildPayrollCalendar().map(({ m, inRange }) => (
//                   <div key={m} style={{ width:66, textAlign:"center",
//                     background: !inRange ? "#F3F4F6" : "#D1FAE5",
//                     borderRadius:8, padding:"10px 6px",
//                     border:`1px solid ${!inRange ? C.border : "#A7F3D0"}` }}>
//                     <div style={{ fontSize:10, fontWeight:700, color:C.muted, textTransform:"uppercase" }}>{m}</div>
//                     <div style={{ fontSize:13, fontWeight:800,
//                       color: !inRange ? C.muted : C.green, marginTop:4 }}>
//                       {!inRange ? "—" : "✓"}
//                     </div>
//                   </div>
//                 ))}
//               </div>
//               {detail.submitted_count != null && (
//                 <div style={{ padding:"12px 16px", background:"#D1FAE5",
//                   borderRadius:10, border:`1px solid #A7F3D0`, fontSize:13, color:"#065F46" }}>
//                   ✓ <strong>{detail.submitted_count} payroll submission(s)</strong> recorded
//                   {detail.first_check_date ? ` from ${detail.first_check_date}` : ""}
//                   {detail.last_check_date  ? ` to ${detail.last_check_date}` : ""}.
//                 </div>
//               )}
//             </div>
//           )}
 
//           {/* ── Narrative tab ── */}
//           {tab === "narrative" && (
//             <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
//               {detail.ai_narrative ? (
//                 <div style={{ background:"#EEF2FF", borderLeft:`4px solid ${C.accent}`,
//                   borderRadius:"0 10px 10px 0", padding:"16px 20px", fontSize:13,
//                   color:C.text, lineHeight:1.8 }}>
//                   <div style={{ fontWeight:700, marginBottom:8, color:C.accent }}>
//                     🤖 AI-Generated Audit Narrative
//                   </div>
//                   {detail.ai_narrative.split("\n\n").map((para, i) => (
//                     <p key={i} style={{ margin:"0 0 10px" }}>{para}</p>
//                   ))}
//                 </div>
//               ) : (
//                 <div style={{ textAlign:"center", padding:40, color:C.muted }}>
//                   {["completed","error"].includes(detail.status)
//                     ? "No narrative generated for this audit."
//                     : "Narrative will appear once the audit completes."}
//                 </div>
//               )}
//               {detail.agent_logs?.length > 0 && (
//                 <div style={{ background:C.navy, borderRadius:12, padding:20 }}>
//                   <div style={{ fontSize:12, fontWeight:700, color:"#64B5F6", marginBottom:10, fontFamily:"monospace" }}>
//                     ▶ AGENT EXECUTION LOG
//                   </div>
//                   <div style={{ fontFamily:"monospace", fontSize:11, color:"#A8D8A8",
//                     lineHeight:1.8, maxHeight:200, overflowY:"auto" }}>
//                     {detail.agent_logs.map((log, i) => (
//                       <div key={i}>[{log.timestamp}] {log.agent} → {log.status}</div>
//                     ))}
//                   </div>
//                 </div>
//               )}
//               {canApproveHITL &&(<div style={{ display:"flex", gap:8 }}>
//                 <button style={{ background:C.green, color:"#fff", border:"none", borderRadius:8,
//                   padding:"8px 20px", fontSize:13, fontWeight:700, cursor:"pointer" }}>
//                   ✓ Approve Narrative
//                 </button>
//                 <button style={{ background:C.amber, color:"#fff", border:"none", borderRadius:8,
//                   padding:"8px 20px", fontSize:13, fontWeight:700, cursor:"pointer" }}>
//                   ✎ Edit &amp; Override
//                 </button>
//               </div>)}
//             </div>
//           )}
 
//           {/* ── Decision tab ── */}
//           {tab === "decision" && (
//             <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
 
//               {/* 3 option cards */}
//               <div style={{ display:"grid", gridTemplateColumns:"repeat(3, 1fr)", gap:14 }}>
//                 {[
//                   {
//                     key:    "additional_premium",
//                     label:  "Bill EST YTD Premium",
//                     amount: money(Math.round(ov.est_ytd_premium || 0)),
//                     color:  C.red,
//                     icon:   "💳",
//                     desc:   "Insured underpaid based on audit findings",
//                   },
//                   {
//                     key:    "refund",
//                     label:  "Issue Refund",
//                     amount: money(Math.round(Math.abs(ov.variance || 0))),
//                     color:  C.green,
//                     icon:   "↩️",
//                     desc:   "Overpayment detected — refund applicable",
//                   },
//                   {
//                     key:    "clarification",
//                     label:  "Request Clarification",
//                     amount: "—",
//                     color:  C.amber,
//                     icon:   "❓",
//                     desc:   "Ambiguous findings need insured response",
//                   },
//                 ].map((d, i) => {
//                   const isActive = detail.recommendation === d.key;
//                   return (
//                     <div key={i} style={{ background:isActive ? "#F0F9FF" : C.bg,
//                       border:`2px solid ${isActive ? d.color : C.border}`,
//                       borderRadius:12, padding:20, textAlign:"left",
//                       transition:"all 0.15s" }}
//                       onMouseEnter={e => { e.currentTarget.style.borderColor = d.color; e.currentTarget.style.background="#F8FAFD"; }}
//                       onMouseLeave={e => { e.currentTarget.style.borderColor = isActive ? d.color : C.border; e.currentTarget.style.background = isActive ? "#F0F9FF" : C.bg; }}>
//                       <div style={{ fontSize:24, marginBottom:8 }}>{d.icon}</div>
//                       <div style={{ fontSize:14, fontWeight:700, color:C.text }}>{d.label}</div>
//                       <div style={{ fontSize:22, fontWeight:800, color:d.color, margin:"6px 0" }}>{d.amount}</div>
//                       <div style={{ fontSize:12, color:C.muted }}>{d.desc}</div>
//                       {isActive && (
//                         <div style={{ marginTop:8, fontSize:11, fontWeight:700, color:d.color,
//                           background: `${d.color}15`, padding:"3px 10px", borderRadius:20, display:"inline-block" }}>
//                           ● System Recommendation
//                         </div>
//                       )}
//                     </div>
//                   );
//                 })}
//               </div>
 
//               {/* Reviewer notes + HITL form */}
//               <div style={{ background:C.bg, borderRadius:12, padding:16 }}>
//                 <div style={{ fontSize:13, fontWeight:700, color:C.text, marginBottom:8 }}>
//                   {detail.hitl_required ? "Human-in-the-Loop Decision" : "Reviewer Notes"}
//                 </div>
//                 <textarea value={hitlNote} onChange={e => setHitlNote(e.target.value)}
//                   placeholder="Add manual notes, override reasoning, or additional findings..."
//                   style={{ width:"100%", minHeight:80, border:`1px solid ${C.border}`, borderRadius:8,
//                     padding:12, fontSize:13, color:C.text, resize:"vertical", outline:"none",
//                     fontFamily:"inherit", boxSizing:"border-box", marginBottom:12 }} />
 
//                 {detail.hitl_required && (canApproveHITL

//                  ? (
//                   <div style={{ display:"flex", gap:10 }}>
//                     <button disabled={submitting} onClick={() => handleHITL("approve")}
//                       style={{ background:C.green, color:"#fff", border:"none", borderRadius:8,
//                         padding:"10px 24px", fontSize:13, fontWeight:700,
//                         cursor:submitting ? "default" : "pointer", opacity:submitting ? 0.7 : 1 }}>
//                       {submitting ? "Submitting..." : "✓ Approve & Finalize"}
//                     </button>
//                     <button disabled={submitting} onClick={() => handleHITL("reject")}
//                       style={{ background:C.red, color:"#fff", border:"none", borderRadius:8,
//                         padding:"10px 24px", fontSize:13, fontWeight:700,
//                         cursor:submitting ? "default" : "pointer", opacity:submitting ? 0.7 : 1 }}>
//                       ✗ Reject
//                     </button>
//                     <button onClick={() => downloadReport(detail.audit_case_id)}
//                       style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:8,
//                         padding:"10px 20px", fontSize:13, color:C.muted, cursor:"pointer" }}>
//                       ⬇ Download Report
//                     </button>
//                   </div>
//                 ) : (
//                   <div style={{ display:"flex", justifyContent:"flex-end", gap:8 }}>
//                     <button style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:8,
//                       padding:"7px 18px", fontSize:13, cursor:"pointer", color:C.muted }}>
//                       Save Draft
//                     </button>
//                     {detail.status === "completed" && (
//                       <button onClick={() => downloadReport(detail.audit_case_id)}
//                         style={{ background:C.accent, color:"#fff", border:"none", borderRadius:8,
//                           padding:"7px 18px", fontSize:13, fontWeight:700, cursor:"pointer" }}>
//                         ⬇ Finalize Audit
//                       </button>
//                     )}
//                   </div>
//                 ))}
//               </div>
//             </div>
//           )}
//         </div>
//       </div>
//     </div>
//   );
// }
 
 


// function DataUpload({ onAuditStarted, onBatchStarted }) {
//   // ── File-upload state (unchanged) ─────────────────────────────────
//   const [payrollFile,  setPayrollFile]  = useState(null);
//   const [policyFile,   setPolicyFile]   = useState(null);
//   const [metaFile,     setMetaFile]     = useState(null);
//   const [policyNumber, setPolicyNumber] = useState("");
//   const [dragging,     setDragging]     = useState(null);
//   const [uploading,    setUploading]    = useState(false);
//   const [uploadResult, setUploadResult] = useState(null);
//   const [starting,     setStarting]     = useState(false);
//   const [started,      setStarted]      = useState(null);
//   const [error,        setError]        = useState(null);
 
//   // ── API Batch state (two-step) ─────────────────────────────────────
//   const [apiMode,       setApiMode]       = useState(false);
//   // Step 1 — Preview
//   const [previewing,    setPreviewing]    = useState(false);
//   const [previewData,   setPreviewData]   = useState(null);   // PolicyPreviewResponse
//   const [previewError,  setPreviewError]  = useState(null);
//   // Step 2 — Start batch
//   const [starting2,     setStarting2]     = useState(false);
//   const [batchResult,   setBatchResult]   = useState(null);
//   const [batchError,    setBatchError]    = useState(null);
 
//   const allReady = payrollFile && policyFile && metaFile && policyNumber.trim();
//   const money    = (n) => n == null ? "—" : `$${Number(n).toLocaleString(undefined, {minimumFractionDigits:0})}`;
 
//   // ── File upload handlers (unchanged) ──────────────────────────────
//   const handleUpload = async () => {
//     if (!allReady) return;
//     setUploading(true); setError(null);
//     try {
//       const result = await uploadAuditFiles(payrollFile, policyFile, metaFile);
//       setUploadResult(result);
//     } catch (err) {
//       setError(err.response?.data?.detail || err.message);
//     } finally {
//       setUploading(false);
//     }
//   };
 
//   const handleStart = async () => {
//     if (!uploadResult) return;
//     setStarting(true); setError(null);
//     try {
//       const result = await startAudit({
//         policy_number:        policyNumber.trim(),
//         payroll_file_path:    uploadResult.payroll_file_path,
//         policy_xml_path:      uploadResult.policy_xml_path,
//         audit_meta_file_path: uploadResult.audit_meta_file_path,
//       });
//       setStarted(result);
//       onAuditStarted?.(result.audit_case_id);
//     } catch (err) {
//       setError(err.response?.data?.detail || err.message);
//     } finally {
//       setStarting(false);
//     }
//   };
 
//   // ── Step 1: Preview policies ───────────────────────────────────────
//   const handlePreview = async () => {
//     setPreviewing(true); setPreviewError(null); setPreviewData(null); setBatchResult(null);
//     try {
//       const result = await previewAPIPolicies();  // GET /wc-audit/preview-api-policies
//       setPreviewData(result);
//     } catch (err) {
//       setPreviewError(err.response?.data?.detail || err.message || "Preview failed");
//     } finally {
//       setPreviewing(false);
//     }
//   };
 
//   // ── Step 2: Start the batch ────────────────────────────────────────
//   const handleStartBatch = async () => {
//     setStarting2(true); setBatchError(null);
//     try {
//       const result = await startBatchAuditFromAPI();
//       setBatchResult(result);
//       onBatchStarted?.(result.cases.map(c => c.audit_case_id));
//     } catch (err) {
//       setBatchError(err.response?.data?.detail || err.message || "Batch start failed");
//     } finally {
//       setStarting2(false);
//     }
//   };
 
//   const handleReset = () => {
//     setPreviewData(null); setPreviewError(null);
//     setBatchResult(null); setBatchError(null);
//   };
 
//   const FileDropZone = ({ label, file, setFile, accept, dragKey }) => (
//     <div
//       style={{ background:dragging === dragKey ? "#EEF2FF" : C.bg,
//         border:`2px dashed ${dragging === dragKey ? C.accent : C.border}`,
//         borderRadius:12, padding:"20px 24px", cursor:"pointer", transition:"all 0.2s",
//         display:"flex", alignItems:"center", gap:14 }}
//       onDragOver={e => { e.preventDefault(); setDragging(dragKey); }}
//       onDragLeave={() => setDragging(null)}
//       onDrop={e => { e.preventDefault(); setDragging(null);
//         const f = e.dataTransfer.files[0]; if (f) setFile(f); }}
//       onClick={() => document.getElementById(`inp-${dragKey}`).click()}>
//       <span style={{ fontSize:28 }}>{file ? "✅" : "📂"}</span>
//       <div>
//         <div style={{ fontSize:13, fontWeight:700, color:C.text }}>{label}</div>
//         <div style={{ fontSize:12, color:C.muted }}>
//           {file ? file.name : `Drop or click to select — ${accept}`}
//         </div>
//       </div>
//       <input id={`inp-${dragKey}`} type="file" accept={accept} style={{ display:"none" }}
//         onChange={e => e.target.files[0] && setFile(e.target.files[0])} />
//     </div>
//   );
 
//   return (
//     <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
 
//       {/* ── Source selector tabs ──────────────────────────────────── */}
//       <div style={{ display:"flex", gap:0, background:C.bg, borderRadius:12,
//         border:`1px solid ${C.border}`, overflow:"hidden", alignSelf:"flex-start" }}>
//         {[
//           { key:false, label:"📂  File Upload",    desc:"Upload Excel & XML files" },
//           { key:true,  label:"🔌  Fetch from API", desc:"Pull all policies from Mock API" },
//         ].map(tab => (
//           <button key={String(tab.key)} onClick={() => { setApiMode(tab.key); handleReset(); }}
//             style={{ padding:"12px 28px", border:"none", cursor:"pointer",
//               background: apiMode === tab.key
//                 ? `linear-gradient(135deg, ${C.accent}, ${C.teal})`
//                 : "transparent",
//               color: apiMode === tab.key ? "#fff" : C.muted,
//               fontWeight:700, fontSize:13, transition:"all 0.2s",
//               borderRight:`1px solid ${C.border}` }}>
//             {tab.label}
//           </button>
//         ))}
//       </div>
 
//       {/* ══════════════════════════════════════════════════════════════
//           FILE UPLOAD TAB
//       ══════════════════════════════════════════════════════════════ */}
//       {!apiMode && (
//         <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:28 }}>
//           <SectionHeader title="Run New Audit"
//             sub="Upload three source files, enter policy number, then start the AI pipeline" />
 
//           <div style={{ display:"flex", flexDirection:"column", gap:12, marginBottom:20 }}>
//             <FileDropZone label="Payroll Excel (.xlsx)"  file={payrollFile} setFile={setPayrollFile} accept=".xlsx" dragKey="payroll" />
//             <FileDropZone label="Policy XML (.xml)"      file={policyFile}  setFile={setPolicyFile}  accept=".xml"  dragKey="policy" />
//             <FileDropZone label="Audit Metadata (.xlsx)" file={metaFile}    setFile={setMetaFile}    accept=".xlsx" dragKey="meta" />
//           </div>
 
//           <div style={{ marginBottom:20 }}>
//             <label style={{ fontSize:12, fontWeight:700, color:C.muted, textTransform:"uppercase",
//               letterSpacing:0.8, display:"block", marginBottom:6 }}>Policy Number</label>
//             <input value={policyNumber} onChange={e => setPolicyNumber(e.target.value)}
//               placeholder="e.g. MWC0183363-05"
//               style={{ border:`1px solid ${C.border}`, borderRadius:8, padding:"10px 14px", fontSize:13,
//                 width:"100%", outline:"none", color:C.text, boxSizing:"border-box", maxWidth:340 }} />
//           </div>
 
//           {error && (
//             <div style={{ padding:"10px 14px", background:"#FEE2E2", borderRadius:8,
//               border:`1px solid #FECACA`, fontSize:13, color:"#991B1B", marginBottom:16 }}>✗ {error}</div>
//           )}
 
//           <div style={{ display:"flex", gap:12, alignItems:"center" }}>
//             {!uploadResult ? (
//               <button disabled={!allReady || uploading} onClick={handleUpload}
//                 style={{ background:allReady ? C.accent : C.border, color:"#fff", border:"none",
//                   borderRadius:10, padding:"11px 28px", fontSize:14, fontWeight:700,
//                   cursor:allReady && !uploading ? "pointer" : "default", opacity:uploading ? 0.7 : 1 }}>
//                 {uploading ? "⚙️ Uploading..." : "⬆ Upload Files"}
//               </button>
//             ) : !started ? (
//               <>
//                 <div style={{ padding:"8px 16px", background:"#DCFCE7", borderRadius:8,
//                   fontSize:13, fontWeight:600, color:"#15803D" }}>
//                   ✓ Files uploaded — Session: {uploadResult.session_id}
//                 </div>
//                 <button disabled={starting} onClick={handleStart}
//                   style={{ background:C.green, color:"#fff", border:"none", borderRadius:10,
//                     padding:"11px 28px", fontSize:14, fontWeight:700,
//                     cursor:starting ? "default" : "pointer", opacity:starting ? 0.7 : 1 }}>
//                   {starting ? "⚙️ Starting..." : "▶ Start AI Audit"}
//                 </button>
//               </>
//             ) : (
//               <div style={{ padding:"12px 20px", background:"#DCFCE7", borderRadius:10,
//                 border:`1px solid #86EFAC`, fontSize:14, fontWeight:700, color:"#15803D" }}>
//                 🚀 Audit started! Case #{started.audit_case_id} — Check AI Audit screen for live progress.
//               </div>
//             )}
//           </div>
//         </div>
//       )}
 
//       {/* ══════════════════════════════════════════════════════════════
//           API FETCH TAB — two-step: Preview → Start Batch
//       ══════════════════════════════════════════════════════════════ */}
//       {apiMode && (
//         <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:28 }}>
 
//           {/* ── IDLE: nothing loaded yet ── */}
//           {!previewData && !batchResult && (
//             <>
//               <SectionHeader
//                 title="Fetch All Policies from API"
//                 sub="Preview available policies before starting the batch audit" />
 
//               {/* Info cards */}
//               <div style={{ display:"flex", gap:14, marginBottom:24 }}>
//                 {[
//                   { icon:"🔍", title:"Preview First",    desc:"Loads all policy details from the Mock API so you can review before committing" },
//                   { icon:"⚡", title:"Cache & Queue",    desc:"Policy configs are cached in Redis — worker only fetches payroll data" },
//                   { icon:"🤖", title:"Full Pipeline",    desc:"Each policy runs the complete LangGraph pipeline with HITL when required" },
//                 ].map((item, i) => (
//                   <div key={i} style={{ flex:1, background:C.bg, borderRadius:12,
//                     padding:"16px 18px", border:`1px solid ${C.border}` }}>
//                     <div style={{ fontSize:22, marginBottom:8 }}>{item.icon}</div>
//                     <div style={{ fontSize:13, fontWeight:700, color:C.text, marginBottom:4 }}>{item.title}</div>
//                     <div style={{ fontSize:12, color:C.muted, lineHeight:1.5 }}>{item.desc}</div>
//                   </div>
//                 ))}
//               </div>
 
//               {previewError && (
//                 <div style={{ padding:"10px 14px", background:"#FEE2E2", borderRadius:8,
//                   border:`1px solid #FECACA`, fontSize:13, color:"#991B1B", marginBottom:16 }}>
//                   ✗ {previewError}
//                 </div>
//               )}
 
//               {/* Step 1 button */}
//               <button disabled={previewing} onClick={handlePreview}
//                 style={{
//                   background: previewing ? C.border : `linear-gradient(135deg, ${C.accent}, ${C.teal})`,
//                   color:"#fff", border:"none", borderRadius:10, padding:"13px 32px",
//                   fontSize:15, fontWeight:800, cursor:previewing ? "default" : "pointer",
//                   display:"flex", alignItems:"center", gap:10, transition:"all 0.2s",
//                   opacity:previewing ? 0.7 : 1,
//                   boxShadow:previewing ? "none" : "0 4px 16px rgba(30,111,217,0.3)",
//                 }}>
//                 {previewing
//                   ? <><span style={{ fontSize:18 }}>⚙️</span> Loading Policy Details…</>
//                   : <><span style={{ fontSize:18 }}>🔍</span> Preview Policies from API</>
//                 }
//               </button>
//             </>
//           )}
 
//           {/* ── STEP 1 DONE: Policy preview table ── */}
//           {previewData && !batchResult && (
//             <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
 
//               {/* Summary bar */}
//               <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center",
//                 flexWrap:"wrap", gap:12 }}>
//                 <div>
//                   <h3 style={{ margin:0, fontSize:17, fontWeight:800, color:C.text }}>
//                     Policy Preview — {previewData.total} Policies Found
//                   </h3>
//                   <div style={{ fontSize:12, color:C.muted, marginTop:3 }}>
//                     Policy details loaded and cached. Review below, then start the batch.
//                   </div>
//                 </div>
//                 <div style={{ display:"flex", gap:10 }}>
//                   <button onClick={handleReset}
//                     style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:8,
//                       padding:"7px 14px", fontSize:12, cursor:"pointer", color:C.muted, fontWeight:600 }}>
//                     ↺ Reload
//                   </button>
//                   <button onClick={handleStartBatch} disabled={starting2}
//                     style={{
//                       background: starting2 ? "#86EFAC" : C.green,
//                       color:"#fff", border:"none", borderRadius:10,
//                       padding:"10px 24px", fontSize:14, fontWeight:800,
//                       cursor: starting2 ? "default" : "pointer",
//                       display:"flex", alignItems:"center", gap:8,
//                       boxShadow: starting2 ? "none" : "0 4px 14px rgba(16,185,129,0.35)",
//                       transition:"all 0.2s",
//                     }}>
//                     {starting2
//                       ? <><span>⚙️</span> Queuing…</>
//                       : <><span>▶</span> Start Batch Audit ({previewData.policies.filter(p => p.available).length} policies)</>
//                     }
//                   </button>
//                 </div>
//               </div>
 
//               {batchError && (
//                 <div style={{ padding:"10px 14px", background:"#FEE2E2", borderRadius:8,
//                   border:`1px solid #FECACA`, fontSize:13, color:"#991B1B" }}>
//                   ✗ {batchError}
//                 </div>
//               )}
 
//               {/* KPI chips */}
//               <div style={{ display:"flex", gap:12 }}>
//                 {[
//                   { label:"Available",    value: previewData.policies.filter(p => p.available).length,  color:C.green  },
//                   { label:"Unavailable",  value: previewData.policies.filter(p => !p.available).length, color:C.red    },
//                   { label:"States",       value: new Set(previewData.policies.map(p => p.state_code).filter(Boolean)).size, color:C.accent },
//                 ].map(({ label, value, color }) => (
//                   <div key={label} style={{ background:C.bg, borderRadius:10,
//                     padding:"10px 18px", border:`1px solid ${C.border}`, textAlign:"center" }}>
//                     <div style={{ fontSize:20, fontWeight:800, color }}>{value}</div>
//                     <div style={{ fontSize:11, color:C.muted, fontWeight:600 }}>{label}</div>
//                   </div>
//                 ))}
//               </div>
 
//               {/* Policy detail table */}
//               <div style={{ border:`1px solid ${C.border}`, borderRadius:12, overflow:"hidden" }}>
//                 {/* Table header */}
//                 <div style={{ display:"grid",
//                   gridTemplateColumns:"1.6fr 2fr 1fr 1fr 0.8fr 1.2fr 1fr 0.7fr",
//                   background:"#F8FAFD", borderBottom:`1px solid ${C.border}`,
//                   padding:"10px 16px", gap:8 }}>
//                   {["Policy Number","Insured Name","Eff. Date","Exp. Date","State","Class Codes","Est Premium","Freq"].map(h => (
//                     <div key={h} style={{ fontSize:10, fontWeight:700, color:C.muted,
//                       textTransform:"uppercase", letterSpacing:0.7 }}>{h}</div>
//                   ))}
//                 </div>
 
//                 {/* Table rows */}
//                 <div style={{ maxHeight:380, overflowY:"auto" }}>
//                   {previewData.policies.map((p, i) => (
//                     <div key={p.policy_number}
//                       style={{
//                         display:"grid",
//                         gridTemplateColumns:"1.6fr 2fr 1fr 1fr 0.8fr 1.2fr 1fr 0.7fr",
//                         padding:"11px 16px", gap:8, alignItems:"center",
//                         borderBottom:`1px solid ${C.border}`,
//                         background: !p.available ? "#FFF7F7" : i % 2 === 0 ? "#fff" : C.bg,
//                         transition:"background 0.12s",
//                       }}
//                       onMouseEnter={e => p.available && (e.currentTarget.style.background = "#EEF2FF")}
//                       onMouseLeave={e => (e.currentTarget.style.background = !p.available ? "#FFF7F7" : i % 2 === 0 ? "#fff" : C.bg)}
//                     >
//                       {/* Policy Number */}
//                       <div style={{ fontSize:13, fontWeight:700,
//                         color: p.available ? C.accent : C.muted,
//                         display:"flex", alignItems:"center", gap:6 }}>
//                         {!p.available && <span title="Not found in Mock API" style={{ color:C.red }}>⚠</span>}
//                         {p.policy_number}
//                       </div>
 
//                       {/* Insured Name */}
//                       <div style={{ fontSize:12, color:C.text,
//                         overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
//                         {p.insured_name || "—"}
//                       </div>
 
//                       {/* Effective Date */}
//                       <div style={{ fontSize:12, color:C.muted }}>{p.effective_date || "—"}</div>
 
//                       {/* Expiration Date */}
//                       <div style={{ fontSize:12, color:C.muted }}>{p.expiration_date || "—"}</div>
 
//                       {/* State */}
//                       <div style={{ fontSize:12, fontWeight:700, color:C.text }}>{p.state_code || "—"}</div>
 
//                       {/* Class Codes */}
//                       <div style={{ fontSize:11, color:C.muted,
//                         overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
//                         {p.class_codes || "—"}
//                       </div>
 
//                       {/* Est Premium */}
//                       <div style={{ fontSize:12, fontWeight:600, color:C.text }}>
//                         {p.est_premium ? money(p.est_premium) : "—"}
//                       </div>
 
//                       {/* Payroll Frequency */}
//                       <div style={{ fontSize:11, color:C.muted }}>{p.payroll_frequency || "—"}</div>
//                     </div>
//                   ))}
//                 </div>
//               </div>
 
//               {/* Preview errors (404 policies) */}
//               {previewData.errors?.length > 0 && (
//                 <div style={{ padding:"12px 16px", background:"#FEF3C7", borderRadius:10,
//                   border:`1px solid ${C.amber}`, fontSize:12, color:"#92400E" }}>
//                   ⚠️ <strong>{previewData.errors.length} policy(ies) unavailable:</strong>
//                   <ul style={{ margin:"4px 0 0 16px", padding:0 }}>
//                     {previewData.errors.map((e, i) => <li key={i}>{e}</li>)}
//                   </ul>
//                 </div>
//               )}
//             </div>
//           )}
 
//           {/* ── STEP 2 DONE: Batch queued ── */}
//           {batchResult && (
//             <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
//               <div style={{ padding:"16px 20px", background:"#DCFCE7", borderRadius:12,
//                 border:`1px solid #86EFAC`, display:"flex", alignItems:"center", gap:14 }}>
//                 <span style={{ fontSize:28 }}>🚀</span>
//                 <div>
//                   <div style={{ fontSize:15, fontWeight:800, color:"#15803D" }}>
//                     {batchResult.total_queued} policies queued for audit!
//                   </div>
//                   <div style={{ fontSize:12, color:"#166534", marginTop:2 }}>
//                     Batch ID: {batchResult.batch_id} — Monitor progress on the AI Audit screen.
//                   </div>
//                 </div>
//               </div>
 
//               {/* Queued list with preview details */}
//               <div style={{ border:`1px solid ${C.border}`, borderRadius:12, overflow:"hidden" }}>
//                 <div style={{ display:"grid", gridTemplateColumns:"1.6fr 2fr 1fr 0.8fr 1fr",
//                   background:"#F8FAFD", borderBottom:`1px solid ${C.border}`,
//                   padding:"10px 16px", gap:8 }}>
//                   {["Policy Number","Insured Name","Case ID","State","Status"].map(h => (
//                     <div key={h} style={{ fontSize:10, fontWeight:700, color:C.muted,
//                       textTransform:"uppercase", letterSpacing:0.7 }}>{h}</div>
//                   ))}
//                 </div>
//                 <div style={{ maxHeight:300, overflowY:"auto" }}>
//                   {batchResult.cases.map((c, i) => {
//                     const detail = previewData?.policies.find(p => p.policy_number === c.policy_number);
//                     return (
//                       <div key={c.audit_case_id}
//                         style={{ display:"grid", gridTemplateColumns:"1.6fr 2fr 1fr 0.8fr 1fr",
//                           padding:"11px 16px", gap:8, alignItems:"center",
//                           borderBottom:`1px solid ${C.border}`,
//                           background: i % 2 === 0 ? "#fff" : C.bg }}>
//                         <div style={{ fontSize:13, fontWeight:700, color:C.accent }}>
//                           {c.policy_number}
//                         </div>
//                         <div style={{ fontSize:12, color:C.muted,
//                           overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
//                           {detail?.insured_name || "—"}
//                         </div>
//                         <div style={{ fontSize:13, color:C.text }}>#{c.audit_case_id}</div>
//                         <div style={{ fontSize:12, fontWeight:700, color:C.text }}>
//                           {detail?.state_code || "—"}
//                         </div>
//                         <span><StatusBadge status="pending" /></span>
//                       </div>
//                     );
//                   })}
//                 </div>
//               </div>
 
//               {batchResult.errors?.length > 0 && (
//                 <div style={{ padding:"12px 16px", background:"#FEF3C7", borderRadius:10,
//                   border:`1px solid ${C.amber}`, fontSize:12, color:"#92400E" }}>
//                   ⚠️ <strong>{batchResult.errors.length} failed to queue:</strong>
//                   <ul style={{ margin:"4px 0 0 16px", padding:0 }}>
//                     {batchResult.errors.map((e, i) => <li key={i}>{e}</li>)}
//                   </ul>
//                 </div>
//               )}
 
//               <button onClick={handleReset}
//                 style={{ alignSelf:"flex-start", background:C.bg,
//                   border:`1px solid ${C.border}`, borderRadius:8,
//                   padding:"7px 16px", fontSize:12, cursor:"pointer", color:C.muted }}>
//                 ↺ Run another batch
//               </button>
//             </div>
//           )}
//         </div>
//       )}
 
//       {/* How it works */}
//       <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
//         <SectionHeader title="How it works"
//           sub={apiMode ? "Two-step API batch audit pipeline" : "The 3-step file audit pipeline"} />
//         <div style={{ display:"flex", gap:16 }}>
//           {(apiMode ? [
//             { n:"1", title:"Preview",    desc:"Backend fetches all policies + configs from Mock API. Details shown in a table for review.", icon:"🔍" },
//             { n:"2", title:"Queue",      desc:"Confirmed policies are pushed to the Redis audit queue with configs pre-cached.", icon:"⚡" },
//             { n:"3", title:"Process",    desc:"Worker processes each policy — fetches payroll data only (config already cached). HITL when high-risk.", icon:"🤖" },
//           ] : [
//             { n:"1", title:"Upload",  desc:"Drop payroll Excel, policy XML, and audit metadata. Files are securely processed.", icon:"📂" },
//             { n:"2", title:"Analyze", desc:"LangGraph multi-agent pipeline: Ingestion → Specialist agents → Premium calculation → AI narrative.", icon:"🤖" },
//             { n:"3", title:"Review",  desc:"Auditor reviews variance report, HITL decisions, and AI explanation. Download final report.", icon:"📊" },
//           ]).map(s => (
//             <div key={s.n} style={{ flex:1, background:C.bg, borderRadius:12, padding:"18px 20px" }}>
//               <div style={{ width:32, height:32, borderRadius:"50%", background:C.accent,
//                 color:"#fff", display:"flex", alignItems:"center", justifyContent:"center",
//                 fontWeight:800, fontSize:14, marginBottom:12 }}>{s.n}</div>
//               <div style={{ fontSize:16 }}>{s.icon}</div>
//               <div style={{ fontSize:14, fontWeight:700, color:C.text, marginBottom:6 }}>{s.title}</div>
//               <div style={{ fontSize:12, color:C.muted, lineHeight:1.6 }}>{s.desc}</div>
//             </div>
//           ))}
//         </div>
//       </div>
//     </div>
//   );
// }

// function Administration({ setScreen, onDataCleared }) {
//   // ── Tab state ─────────────────────────────────────────────────────────────
//   const [activeTab, setActiveTab] = useState("configuration");  // "configuration" | "data"

//   // ── Data wipe state ───────────────────────────────────────────────────────
//   const [phase,      setPhase]      = useState("idle");
//   const [confirmTxt, setConfirmTxt] = useState("");
//   const [wipeResult, setWipeResult] = useState(null);
//   const [wipeErr,    setWipeErr]    = useState("");
//   const CONFIRM_PHRASE = "DELETE ALL DATA";

//   // ── HITL config state ─────────────────────────────────────────────────────
//   const [hitlEnabled,      setHitlEnabled]      = useState(true);
//   const [configLoading,    setConfigLoading]    = useState(true);
//   const [configSaving,     setConfigSaving]     = useState(false);
//   const [configSaveStatus, setConfigSaveStatus] = useState(null); // null | "saved" | "error"
//   const [configErr,        setConfigErr]        = useState("");

//   // Load config on mount
//   useEffect(() => {
//     (async () => {
//       setConfigLoading(true);
//       try {
//         const cfg = await getAuditConfig();
//         setHitlEnabled(cfg.hitl_enabled ?? true);
//       } catch (e) {
//         setConfigErr(e.message || "Failed to load config");
//       } finally {
//         setConfigLoading(false);
//       }
//     })();
//   }, []);

//   const handleHitlToggle = async (newValue) => {
//     setHitlEnabled(newValue);
//     setConfigSaving(true);
//     setConfigSaveStatus(null);
//     try {
//       await updateAuditConfig({ hitl_enabled: newValue });
//       setConfigSaveStatus("saved");
//       setTimeout(() => setConfigSaveStatus(null), 3000);
//     } catch (e) {
//       setConfigErr(e.message || "Failed to save config");
//       setConfigSaveStatus("error");
//       setHitlEnabled(!newValue);  // revert on error
//     } finally {
//       setConfigSaving(false);
//     }
//   };

//   // ── Data wipe handlers ────────────────────────────────────────────────────
//   const handleWipe = async () => {
//     setPhase("wiping");
//     setWipeErr("");
//     try {
//       const data = await clearAllAuditData();
//       setWipeResult(data);
//       setPhase("done");
//       onDataCleared?.();
//     } catch (err) {
//       setWipeErr(err.response?.data?.detail || err.message || "Unknown error");
//       setPhase("error");
//     }
//   };

//   const reset = () => {
//     setPhase("idle");
//     setConfirmTxt("");
//     setWipeResult(null);
//     setWipeErr("");
//   };
 
//   // ── Reusable tab button ──────────────────────────────────────────────────────
//   const TabBtn = ({ id, icon, label }) => (
//     <button onClick={() => setActiveTab(id)}
//       style={{
//         display:"flex", alignItems:"center", gap:8,
//         padding:"10px 20px", border:"none", cursor:"pointer",
//         fontWeight:700, fontSize:13, borderRadius:"10px 10px 0 0",
//         background: activeTab === id
//           ? C.card
//           : "transparent",
//         color: activeTab === id ? C.accent : C.muted,
//         borderBottom: activeTab === id ? `2px solid ${C.accent}` : "2px solid transparent",
//         transition:"all 0.15s",
//       }}>
//       <span style={{ fontSize:15 }}>{icon}</span> {label}
//     </button>
//   );

//   return (
//     <div style={{ display:"flex", flexDirection:"column", gap:0, maxWidth:900 }}>

//       {/* ── Page header ────────────────────────────────────────────── */}
//       <div style={{ background:C.card, border:`1px solid ${C.border}`,
//         borderRadius:14, padding:24, marginBottom:20 }}>
//         <div style={{ display:"flex", alignItems:"center", gap:14 }}>
//           <div style={{ width:44, height:44, borderRadius:12,
//             background:"linear-gradient(135deg,#7C3AED,#EF4444)",
//             display:"flex", alignItems:"center", justifyContent:"center", fontSize:22 }}>⚙</div>
//           <div>
//             <h2 style={{ margin:0, fontSize:20, fontWeight:800, color:C.text }}>Administration</h2>
//             <p style={{ margin:"3px 0 0", fontSize:13, color:C.muted }}>
//               Platform-level configuration and data management — Super Admin only.
//             </p>
//           </div>
//         </div>
//       </div>

//       {/* ── Tab bar ────────────────────────────────────────────────── */}
//       <div style={{ display:"flex", gap:4, borderBottom:`2px solid ${C.border}`,
//         marginBottom:24, paddingLeft:4 }}>
//         <TabBtn id="configuration" icon="⚙" label="Configuration" />
//         <TabBtn id="data"          icon="🗑" label="Data Management" />
//       </div>

//       {/* ══════════════════════════════════════════════════════════════
//           TAB: CONFIGURATION
//       ══════════════════════════════════════════════════════════════ */}
//       {activeTab === "configuration" && (
//         <div style={{ display:"flex", flexDirection:"column", gap:20 }}>

//           {/* HITL Global Toggle card */}
//           <div style={{ background:C.card, border:`1px solid ${C.border}`,
//             borderRadius:14, padding:28 }}>

//             {/* Card header */}
//             <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:20 }}>
//               <div style={{ width:40, height:40, borderRadius:10,
//                 background: hitlEnabled ? "linear-gradient(135deg,#1E6FD9,#0ABFBC)" : "#F3F4F6",
//                 display:"flex", alignItems:"center", justifyContent:"center", fontSize:20,
//                 transition:"background 0.3s" }}>👤</div>
//               <div>
//                 <div style={{ fontSize:16, fontWeight:800, color:C.text }}>
//                   Human-in-the-Loop (HITL) Review
//                 </div>
//                 <div style={{ fontSize:12, color:C.muted, marginTop:2 }}>
//                   Controls whether high-risk audits pause for human approval before finalising.
//                 </div>
//               </div>
//             </div>

//             {/* Loading state */}
//             {configLoading ? (
//               <div style={{ display:"flex", alignItems:"center", gap:10,
//                 padding:"14px 18px", background:C.bg, borderRadius:10 }}>
//                 <div style={{ width:18, height:18, border:`2px solid ${C.accent}`,
//                   borderTop:"2px solid transparent", borderRadius:"50%",
//                   animation:"spin 0.8s linear infinite" }} />
//                 <span style={{ fontSize:13, color:C.muted }}>Loading configuration…</span>
//               </div>
//             ) : (
//               <>
//                 {/* Toggle row */}
//                 <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between",
//                   padding:"18px 22px",
//                   background: hitlEnabled ? "#EFF6FF" : C.bg,
//                   border:`1.5px solid ${hitlEnabled ? C.accent : C.border}`,
//                   borderRadius:12, marginBottom:16, transition:"all 0.2s" }}>

//                   <div>
//                     <div style={{ fontSize:14, fontWeight:700, color:C.text }}>
//                       HITL Reviews Globally
//                       {" "}
//                       <span style={{
//                         fontSize:11, fontWeight:700, padding:"2px 10px", borderRadius:20,
//                         background: hitlEnabled ? "#DBEAFE" : "#F3F4F6",
//                         color:      hitlEnabled ? C.accent  : C.muted,
//                       }}>
//                         {hitlEnabled ? "ENABLED" : "DISABLED"}
//                       </span>
//                     </div>
//                     <div style={{ fontSize:12, color:C.muted, marginTop:4 }}>
//                       {hitlEnabled
//                         ? "High-risk audits will pause at the HITL checkpoint and await an auditor decision."
//                         : "All audits will bypass the HITL checkpoint and complete automatically."}
//                     </div>
//                   </div>

//                   {/* Toggle switch */}
//                   <div
//                     onClick={() => !configSaving && handleHitlToggle(!hitlEnabled)}
//                     style={{
//                       width:52, height:28, borderRadius:14, cursor: configSaving ? "default" : "pointer",
//                       background: hitlEnabled ? C.accent : "#D1D5DB",
//                       position:"relative", flexShrink:0, marginLeft:20,
//                       transition:"background 0.25s",
//                       opacity: configSaving ? 0.6 : 1,
//                     }}>
//                     <div style={{
//                       position:"absolute", top:3,
//                       left: hitlEnabled ? 26 : 3,
//                       width:22, height:22, borderRadius:"50%", background:"#fff",
//                       boxShadow:"0 1px 4px rgba(0,0,0,0.2)",
//                       transition:"left 0.25s",
//                     }} />
//                   </div>
//                 </div>

//                 {/* Save feedback */}
//                 {configSaving && (
//                   <div style={{ display:"flex", alignItems:"center", gap:8, fontSize:12,
//                     color:C.muted, marginBottom:10 }}>
//                     <div style={{ width:14, height:14, border:`2px solid ${C.accent}`,
//                       borderTop:"2px solid transparent", borderRadius:"50%",
//                       animation:"spin 0.8s linear infinite" }} />
//                     Saving…
//                   </div>
//                 )}
//                 {configSaveStatus === "saved" && (
//                   <div style={{ fontSize:12, color:C.green, fontWeight:700, marginBottom:10 }}>
//                     ✓ Configuration saved successfully
//                   </div>
//                 )}
//                 {configSaveStatus === "error" && (
//                   <div style={{ fontSize:12, color:C.red, fontWeight:700, marginBottom:10 }}>
//                     ✗ Save failed: {configErr}
//                   </div>
//                 )}
//               </>
//             )}

//             {/* Behaviour explanation */}
//             <div style={{ background:"#F8FAFD", border:`1px solid ${C.border}`,
//               borderRadius:10, padding:"14px 18px" }}>
//               <div style={{ fontSize:12, fontWeight:700, color:C.text, marginBottom:10 }}>
//                 How this setting affects the audit pipeline:
//               </div>
//               <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
//                 {[
//                   {
//                     icon:"✅", label:"HITL Enabled (default)",
//                     desc:"assess_risk sets hitl_required based on variance %, officer issues, and amount thresholds. High-risk audits pause at hitl_checkpoint.",
//                     active: hitlEnabled,
//                   },
//                   {
//                     icon:"⚡", label:"HITL Disabled",
//                     desc:"assess_risk forces hitl_required = False for every audit regardless of risk level. All audits flow directly to explanation_agent → generate_report → END.",
//                     active: !hitlEnabled,
//                   },
//                 ].map(({ icon, label, desc, active }) => (
//                   <div key={label} style={{
//                     display:"flex", gap:10, padding:"10px 12px",
//                     borderRadius:8, border:`1px solid ${active ? C.accent : C.border}`,
//                     background: active ? "#EFF6FF" : "transparent",
//                   }}>
//                     <span style={{ fontSize:16, flexShrink:0 }}>{icon}</span>
//                     <div>
//                       <div style={{ fontSize:12, fontWeight:700,
//                         color: active ? C.accent : C.muted }}>{label}</div>
//                       <div style={{ fontSize:11, color:C.muted, marginTop:2, lineHeight:1.5 }}>{desc}</div>
//                     </div>
//                   </div>
//                 ))}
//               </div>
//             </div>
//           </div>

//         </div>
//       )}

//       {/* ══════════════════════════════════════════════════════════════
//           TAB: DATA MANAGEMENT
//       ══════════════════════════════════════════════════════════════ */}
//       {activeTab === "data" && (
//         <div style={{ background:C.card, border:`2px solid #FECACA`, borderRadius:14, padding:28 }}>

//           {/* Header */}
//           <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:18 }}>
//             <div style={{ width:38, height:38, borderRadius:10, background:"#FEE2E2",
//               display:"flex", alignItems:"center", justifyContent:"center", fontSize:20 }}>🗑</div>
//             <div>
//               <div style={{ fontSize:16, fontWeight:800, color:"#991B1B" }}>Clear All Audit Data</div>
//               <div style={{ fontSize:12, color:C.muted, marginTop:1 }}>
//                 Permanently deletes all audit cases and related policy data for this tenant.
//               </div>
//             </div>
//           </div>

//           {/* What gets deleted */}
//           <div style={{ background:"#FFF7ED", border:`1px solid #FED7AA`,
//             borderRadius:10, padding:"14px 18px", marginBottom:20 }}>
//             <div style={{ fontSize:12, fontWeight:700, color:"#92400E", marginBottom:8 }}>
//               ⚠ The following data will be permanently erased:
//             </div>
//             <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"6px 24px" }}>
//               {["All Audit Cases","All Policy Records","Payroll Records","Variance Lines",
//                 "Agent Findings","HITL Reviews","Audit Reports","Policy Class Codes & Officers",
//               ].map(item => (
//                 <div key={item} style={{ display:"flex", alignItems:"center", gap:6, fontSize:12, color:"#78350F" }}>
//                   <span style={{ color:C.red, fontWeight:700 }}>✗</span> {item}
//                 </div>
//               ))}
//             </div>
//           </div>

//           {phase === "idle" && (
//             <button onClick={() => setPhase("confirm")}
//               style={{ background:C.red, color:"#fff", border:"none", borderRadius:10,
//                 padding:"11px 28px", fontSize:14, fontWeight:700, cursor:"pointer",
//                 display:"flex", alignItems:"center", gap:8 }}>
//               🗑 Clear All Data
//             </button>
//           )}

//           {phase === "confirm" && (
//             <div style={{ background:"#FFF1F2", border:`1px solid #FECACA`, borderRadius:12, padding:20 }}>
//               <div style={{ fontSize:14, fontWeight:700, color:"#991B1B", marginBottom:8 }}>
//                 Confirm Destructive Action
//               </div>
//               <div style={{ fontSize:13, color:C.text, marginBottom:14, lineHeight:1.6 }}>
//                 This action <strong>cannot be undone</strong>. Type{" "}
//                 <strong style={{ color:C.red }}>{CONFIRM_PHRASE}</strong> to continue:
//               </div>
//               <input value={confirmTxt} onChange={e => setConfirmTxt(e.target.value)}
//                 placeholder={CONFIRM_PHRASE}
//                 style={{ border:`2px solid ${confirmTxt === CONFIRM_PHRASE ? C.red : C.border}`,
//                   borderRadius:8, padding:"10px 14px", fontSize:13, width:"100%",
//                   outline:"none", boxSizing:"border-box", marginBottom:14,
//                   fontFamily:"monospace", color:C.text,
//                   background: confirmTxt === CONFIRM_PHRASE ? "#FFF1F2" : C.bg }} />
//               <div style={{ display:"flex", gap:10 }}>
//                 <button disabled={confirmTxt !== CONFIRM_PHRASE} onClick={handleWipe}
//                   style={{ background: confirmTxt === CONFIRM_PHRASE ? C.red : "#FCA5A5",
//                     color:"#fff", border:"none", borderRadius:8, padding:"10px 22px",
//                     fontSize:13, fontWeight:700,
//                     cursor: confirmTxt === CONFIRM_PHRASE ? "pointer" : "default" }}>
//                   ✗ Permanently Delete All Data
//                 </button>
//                 <button onClick={reset}
//                   style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:8,
//                     padding:"10px 22px", fontSize:13, fontWeight:600, cursor:"pointer", color:C.muted }}>
//                   Cancel
//                 </button>
//               </div>
//             </div>
//           )}

//           {phase === "wiping" && (
//             <div style={{ display:"flex", alignItems:"center", gap:14, padding:"16px 20px",
//               background:"#FFF7ED", border:`1px solid #FED7AA`, borderRadius:10 }}>
//               <div style={{ width:24, height:24, border:`3px solid ${C.amber}`,
//                 borderTop:"3px solid transparent", borderRadius:"50%",
//                 animation:"spin 0.8s linear infinite" }} />
//               <div>
//                 <div style={{ fontSize:14, fontWeight:700, color:"#92400E" }}>Wiping data…</div>
//                 <div style={{ fontSize:12, color:C.muted, marginTop:2 }}>
//                   Deleting all audit cases, policies, and related records from the database.
//                 </div>
//               </div>
//             </div>
//           )}

//           {phase === "done" && wipeResult && (
//             <div style={{ background:"#F0FDF4", border:`1px solid #86EFAC`, borderRadius:12, padding:20 }}>
//               <div style={{ fontSize:15, fontWeight:800, color:"#15803D", marginBottom:10 }}>
//                 ✓ Data cleared successfully
//               </div>
//               <div style={{ display:"flex", gap:12, flexWrap:"wrap", marginBottom:14 }}>
//                 {[
//                   { label:"Audit Cases", value: wipeResult.deleted_cases    ?? 0 },
//                   { label:"Policies",    value: wipeResult.deleted_policies  ?? 0 },
//                   { label:"Total Rows",  value: wipeResult.total_deleted     ?? 0 },
//                 ].map(({ label, value }) => (
//                   <div key={label} style={{ background:C.card, border:`1px solid ${C.border}`,
//                     borderRadius:8, padding:"10px 18px", textAlign:"center" }}>
//                     <div style={{ fontSize:22, fontWeight:800, color:C.text }}>{value}</div>
//                     <div style={{ fontSize:11, color:C.muted, fontWeight:600, textTransform:"uppercase" }}>{label}</div>
//                   </div>
//                 ))}
//               </div>
//               <div style={{ fontSize:12, color:C.muted, marginBottom:14 }}>
//                 Completed at {new Date().toLocaleTimeString()}. The UI has been refreshed.
//               </div>
//               <button onClick={reset}
//                 style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:8,
//                   padding:"8px 18px", fontSize:13, fontWeight:600, cursor:"pointer", color:C.muted }}>
//                 Close
//               </button>
//             </div>
//           )}

//           {phase === "error" && (
//             <div style={{ background:"#FFF1F2", border:`1px solid #FECACA`, borderRadius:12, padding:20 }}>
//               <div style={{ fontSize:14, fontWeight:800, color:"#991B1B", marginBottom:6 }}>
//                 ✗ Operation failed
//               </div>
//               <div style={{ fontSize:13, color:C.text, marginBottom:14,
//                 background:"#FEE2E2", padding:"10px 14px", borderRadius:8, fontFamily:"monospace" }}>
//                 {wipeErr}
//               </div>
//               <button onClick={reset}
//                 style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:8,
//                   padding:"8px 18px", fontSize:13, fontWeight:600, cursor:"pointer", color:C.muted }}>
//                 Dismiss
//               </button>
//             </div>
//           )}
//         </div>
//       )}

//       <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
//     </div>
//   );
// }

// // ── Reports Screen ────────────────────────────────────────────────────────────
// function ReportsScreen({ cases }) {
//   const completed = cases.filter(c => c.status === "completed");
//   return (
//     <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
//       <div style={{ display:"flex", gap:16 }}>
//         {[
//           { title:"Variance Summary Report",    desc:"Total EST Exposure & Earned Exposure delta vs. EST YTD Premium across all policies", icon:"📊", color:C.accent },
//           { title:"Audit Evidence Package",     desc:"Full evidence trail with narratives and source data",                                 icon:"📋", color:C.purple },
//           { title:"High Risk Policy Report",    desc:"All policies above 20% variance threshold",                                          icon:"⚠️", color:C.red    },
//           { title:"Class Code Analysis",        desc:"Misclassification rates by class code and composite rate",                           icon:"🔍", color:C.teal   },
//         ].map((r, i) => (
//           <div key={i} style={{ flex:1, background:C.card, border:`1px solid ${C.border}`,
//             borderRadius:14, padding:20, cursor:"pointer", transition:"all 0.15s" }}
//             onMouseEnter={e => { e.currentTarget.style.borderColor = r.color; e.currentTarget.style.transform = "translateY(-2px)"; }}
//             onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.transform = "none"; }}>
//             <div style={{ fontSize:32, marginBottom:12 }}>{r.icon}</div>
//             <div style={{ fontSize:14, fontWeight:700, color:C.text, marginBottom:6 }}>{r.title}</div>
//             <div style={{ fontSize:12, color:C.muted, lineHeight:1.5, marginBottom:14 }}>{r.desc}</div>
//             <button style={{ background:r.color, color:"#fff", border:"none", borderRadius:7,
//               padding:"7px 16px", fontSize:12, fontWeight:700, cursor:"pointer", width:"100%" }}>
//               Generate →
//             </button>
//           </div>
//         ))}
//       </div>
 
//       <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
//         <SectionHeader title="Completed Audits" sub="Download reports for finalised cases" />
//         {completed.length === 0 ? (
//           <div style={{ textAlign:"center", padding:40, color:C.muted, fontSize:14 }}>
//             No completed audits yet.
//           </div>
//         ) : (
//           <table style={{ width:"100%", borderCollapse:"collapse" }}>
//             <thead>
//               <tr style={{ borderBottom:`2px solid ${C.border}`, background:"#F8FAFD" }}>
//                 {["Policy Number","Risk","Variance %","Recommendation","Date","Actions"].map(h => (
//                   <th key={h} style={{ padding:"10px 14px", textAlign:"left", fontSize:11,
//                     color:C.muted, fontWeight:700, textTransform:"uppercase" }}>{h}</th>
//                 ))}
//               </tr>
//             </thead>
//             <tbody>
//               {completed.map(c => (
//                 <tr key={c.audit_case_id} style={{ borderBottom:`1px solid ${C.border}` }}>
//                   <td style={{ padding:"13px 14px", fontSize:13, fontWeight:700, color:C.accent }}>
//                     {c.policy_number}
//                   </td>
//                   <td style={{ padding:"13px 14px" }}><RiskBadge risk={c.risk_level} /></td>
//                   <td style={{ padding:"13px 14px", fontSize:13, fontWeight:700,
//                     color:(c.variance_pct || 0) > 10 ? C.red : C.green }}>
//                     {Number(c.variance_pct || 0).toFixed(1)}%
//                   </td>
//                   <td style={{ padding:"13px 14px", fontSize:12, color:C.muted, textTransform:"capitalize" }}>
//                     {c.recommendation?.replace("_"," ") || "—"}
//                   </td>
//                   <td style={{ padding:"13px 14px", fontSize:12, color:C.muted }}>
//                     {new Date(c.created_at).toLocaleDateString()}
//                   </td>
//                   <td style={{ padding:"13px 14px" }}>
//                     <button onClick={() => downloadReport(c.audit_case_id)}
//                       style={{ background:C.accent, color:"#fff", border:"none", borderRadius:6,
//                         padding:"5px 12px", fontSize:12, fontWeight:600, cursor:"pointer" }}>
//                       ⬇ Report
//                     </button>
//                   </td>
//                 </tr>
//               ))}
//             </tbody>
//           </table>
//         )}
//       </div>
//     </div>
//   );
// }
 
 
// // ═══════════════════════════════════════════════════════════════════════════════
// // MAIN APP SHELL
// // ═══════════════════════════════════════════════════════════════════════════════
// export default function WCAuditApp() {
//   const [screen,       setScreen]       = useState("dashboard");
//   const [selectedCase, setSelectedCase] = useState(null);
//   const [collapsed,    setCollapsed]    = useState(false);
//   const [notifOpen,    setNotifOpen]    = useState(false);
//   const [cases,        setCases]        = useState([]);
//   const [loadingCases, setLoadingCases] = useState(true);
//   const [activeCaseId, setActiveCaseId] = useState(null);
//   const [batchCaseIds, setBatchCaseIds] = useState([]);
//   const {
//     canViewReports,
//     canUpload,
//     canApproveHITL,
//     canViewAllTenants,
//     displayRole,
//     isSuperAdmin,
//     canViewAIAudit,
//     canViewVariance,
//     canViewDashboard,
//     canViewPolicies,
//     canViewAdministartion,
//   } = useWCRoles();

//   const allNavItems = [
//     { id:"dashboard", label:"Dashboard",        icon:"⊞" ,visible:canViewDashboard},
//     { id:"policies",  label:"Policies",          icon:"📋" ,visible:canViewPolicies},
//     { id:"variance",  label:"Variance Analysis", icon:"📈" ,visible:canViewVariance},
//     { id:"ai-audit",  label:"AI Audit",          icon:"🤖", visible:canViewAIAudit },
//     { id:"reports",   label:"Reports",           icon:"📊",  visible: canViewReports },
//     { id:"upload",    label:"Data Ingestion",       icon:"⬆",  visible: canUpload },
//     {id:"Administration", label:"Administration", icon:"⚙", visible:canViewAdministartion}
//   ];

//   const navItems = allNavItems.filter(item =>
//     item.visible === undefined || item.visible === true
//   );

//   useEffect(() => {
//     const visibleIds = new Set(navItems.map(n => n.id));
//     if (!visibleIds.has(screen) && screen !== "audit-detail") {
//       setScreen("dashboard");
//     }
//   }, [navItems, screen]);
 
//   const titles = {
//     dashboard:      { title:"Dashboard",         sub:"Workers' Compensation Policy Audit Overview" },
//     policies:       { title:"Policies",          sub:"Manage and review all active policy audits" },
//     variance:       { title:"Variance Analysis", sub:"EST Exposure vs. Earned Exposure and EST YTD Premium vs. Earned Premium explorer" },
//     "ai-audit":     { title:"AI Audit Engine",   sub:"Multi-agent LangGraph orchestration & analysis" },
//     reports:        { title:"Reports",           sub:"Generate and export audit documentation" },
//     upload:         { title:"Data Upload",       sub:"Ingest payroll submissions and policy files" },
//     "audit-detail": { title:"Policy Review",     sub:"Detailed audit workflow and HITL decisions" },
//     Administration: {title:"Adminstartion", sub:"To create users and to do configurations"}
//   };
//   const cur = titles[screen] || titles.dashboard;
 
//   const refreshCases = useCallback(async () => {
//     setLoadingCases(true);
//     try {
//       const data = await listAuditCases();
//       setCases(data);
//     } catch (err) {
//       console.error("[WCAuditApp] Failed to load cases", err);
//     } finally {
//       setLoadingCases(false);
//     }
//   }, []);
 
//   useEffect(() => { refreshCases(); }, [refreshCases]);
 
//   const notifications = [
//     ...cases.filter(c => c.status === "error").map(c => ({
//       id:c.audit_case_id, type:"alert",
//       msg:`Error in case ${c.policy_number}: ${c.errors || "unknown error"}`, time:"recent",
//     })),
//     ...cases.filter(c => c.hitl_required && c.status !== "completed").map(c => ({
//       id:`h-${c.audit_case_id}`, type:"warning",
//       msg:`HITL review required for ${c.policy_number}`, time:"pending",
//     })),
//     ...cases.filter(c => c.status === "completed").slice(0, 2).map(c => ({
//       id:`d-${c.audit_case_id}`, type:"info",
//       msg:`Audit completed for ${c.policy_number}`, time:"done",
//     })),
//   ].slice(0, 5);
 
//   return (
//     <div style={{ display:"flex", height:"100vh", fontFamily:"'DM Sans','Segoe UI',sans-serif",
//       background:C.bg, overflow:"hidden" }}>
 
//       {/* Sidebar */}
//       <div style={{ width:collapsed ? 68 : 240, background:C.navy, display:"flex",
//         flexDirection:"column", transition:"width 0.25s ease", flexShrink:0, overflow:"hidden" }}>
//         <div style={{ padding:"24px 20px 20px", display:"flex", alignItems:"center", gap:12,
//           borderBottom:"1px solid rgba(255,255,255,0.07)" }}>
//           <div style={{ width:36, height:36,
//             background:"linear-gradient(135deg, #1E6FD9, #0ABFBC)", borderRadius:10,
//             display:"flex", alignItems:"center", justifyContent:"center", fontSize:18, flexShrink:0 }}>
//             🛡
//           </div>
//           {!collapsed && (
//             <div>
//               <div style={{ color:"#fff", fontWeight:800, fontSize:14, lineHeight:1.2 }}>Workers' Comp</div>
//               <div style={{ color:"rgba(255,255,255,0.45)", fontSize:11, fontWeight:500 }}>Audit Platform</div>
//             </div>
//           )}
//         </div>
 
//         <nav style={{ flex:1, padding:"16px 10px", overflow:"hidden" }}>
//           {navItems.map(item => (
//             <button key={item.id} onClick={() => setScreen(item.id)}
//               style={{ display:"flex", alignItems:"center", gap:12, width:"100%",
//                 padding:"11px 12px", border:"none", borderRadius:10, cursor:"pointer", marginBottom:4,
//                 background: screen === item.id || (screen === "audit-detail" && item.id === "policies")
//                   ? "rgba(30,111,217,0.25)" : "transparent",
//                 color: screen === item.id || (screen === "audit-detail" && item.id === "policies")
//                   ? "#fff" : "rgba(255,255,255,0.55)",
//                 borderLeft: screen === item.id || (screen === "audit-detail" && item.id === "policies")
//                   ? `3px solid ${C.accentLt}` : "3px solid transparent",
//                 transition:"all 0.15s", textAlign:"left" }}>
//               <span style={{ fontSize:16, width:20, textAlign:"center", flexShrink:0 }}>{item.icon}</span>
//               {!collapsed && <span style={{ fontSize:13, fontWeight:600, whiteSpace:"nowrap" }}>{item.label}</span>}
//             </button>
//           ))}
//         </nav>
 
//         <div style={{ padding:"12px 10px", borderTop:"1px solid rgba(255,255,255,0.07)" }}>
//           <button onClick={() => setCollapsed(!collapsed)}
//             style={{ display:"flex", alignItems:"center", gap:12, width:"100%", padding:"10px 12px",
//               border:"none", borderRadius:10, cursor:"pointer", background:"transparent",
//               color:"rgba(255,255,255,0.4)", transition:"all 0.15s" }}
//             onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.06)"}
//             onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
//             <span style={{ fontSize:16 }}>{collapsed ? "▶" : "◀"}</span>
//             {!collapsed && <span style={{ fontSize:12 }}>Collapse</span>}
//           </button>
//         </div>
//       </div>
 
//       {/* Main area */}
//       <div style={{ flex:1, display:"flex", flexDirection:"column", overflow:"hidden" }}>
 
//         {/* Topbar */}
//         <div style={{ background:C.card, borderBottom:`1px solid ${C.border}`, padding:"0 28px",
//           height:64, display:"flex", alignItems:"center", justifyContent:"space-between", flexShrink:0 }}>
//           <div style={{ position:"relative" }}>
//             <input placeholder="Search policy number, insured name, class code..."
//               style={{ border:`1px solid ${C.border}`, borderRadius:10,
//                 padding:"8px 14px 8px 38px", fontSize:13, width:320, outline:"none",
//                 color:C.text, background:C.bg }} />
//             <span style={{ position:"absolute", left:12, top:"50%", transform:"translateY(-50%)",
//               color:C.muted, fontSize:14 }}>🔍</span>
//           </div>
//           <div style={{ display:"flex", alignItems:"center", gap:16 }}>
 
//             {/* Notifications */}
//             <div style={{ position:"relative" }}>
//               <button onClick={() => setNotifOpen(!notifOpen)}
//                 style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:10,
//                   width:38, height:38, cursor:"pointer", fontSize:16, position:"relative" }}>
//                 🔔
//                 {notifications.length > 0 && (
//                   <span style={{ position:"absolute", top:2, right:2, width:16, height:16,
//                     background:C.red, borderRadius:"50%", fontSize:9, color:"#fff",
//                     display:"flex", alignItems:"center", justifyContent:"center", fontWeight:700 }}>
//                     {notifications.length}
//                   </span>
//                 )}
//               </button>
//               {notifOpen && (
//                 <div style={{ position:"absolute", right:0, top:48, width:340, background:C.card,
//                   border:`1px solid ${C.border}`, borderRadius:12,
//                   boxShadow:"0 8px 32px rgba(0,0,0,0.12)", zIndex:100 }}>
//                   <div style={{ padding:"14px 18px", borderBottom:`1px solid ${C.border}`,
//                     fontWeight:700, fontSize:14, color:C.text }}>Notifications</div>
//                   {notifications.length === 0 ? (
//                     <div style={{ padding:"20px 18px", color:C.muted, fontSize:13 }}>No new notifications</div>
//                   ) : notifications.map((n, i) => (
//                     <div key={i} style={{ padding:"12px 18px", borderBottom:`1px solid ${C.border}`,
//                       display:"flex", gap:10 }}>
//                       <span>{n.type === "alert" ? "🔴" : n.type === "warning" ? "🟡" : "🔵"}</span>
//                       <div>
//                         <div style={{ fontSize:12, color:C.text, lineHeight:1.4 }}>{n.msg}</div>
//                         <div style={{ fontSize:11, color:C.muted, marginTop:3 }}>{n.time}</div>
//                       </div>
//                     </div>
//                   ))}
//                 </div>
//               )}
//             </div>
 
//             <button style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:10,
//               padding:"8px 16px", fontSize:13, cursor:"pointer", color:C.muted, fontWeight:600 }}>
//               ⬇ Export
//             </button>
 
//             <button onClick={() => setScreen("upload")}
//               style={{ background:C.accent, color:"#fff", border:"none", borderRadius:10,
//                 padding:"8px 18px", fontSize:13, fontWeight:700, cursor:"pointer" }}>
//               + New Audit
//             </button>
 
//             <div style={{ display:"flex", alignItems:"center", gap:10 }}>
//               <div style={{ width:36, height:36, borderRadius:"50%",
//                 background:"linear-gradient(135deg, #1E6FD9, #0ABFBC)",
//                 display:"flex", alignItems:"center", justifyContent:"center",
//                 color:"#fff", fontWeight:700, fontSize:14 }}>WC</div>
//               <div>
//                 <div style={{ fontSize:13, fontWeight:700, color:C.text }}>WC Auditor</div>
//                 <div style={{ fontSize:11, color:C.muted }}>Senior Analyst</div>
//               </div>
//             </div>
//           </div>
//         </div>
 
//         {/* Page header */}
//         <div style={{ background:C.card, borderBottom:`1px solid ${C.border}`,
//           padding:"16px 28px", flexShrink:0 }}>
//           <h1 style={{ margin:0, fontSize:20, fontWeight:800, color:C.text }}>{cur.title}</h1>
//           <p style={{ margin:"4px 0 0", fontSize:13, color:C.muted }}>{cur.sub}</p>
//         </div>
 
//         {/* Content */}
//         <div style={{ flex:1, overflowY:"auto", padding:24 }}>
//           {screen === "dashboard" && (
//             <Dashboard setScreen={setScreen} setSelectedCase={setSelectedCase} cases={cases} />
//           )}
//           {screen === "policies" && (
//             <PoliciesScreen setScreen={setScreen} setSelectedCase={setSelectedCase}
//               cases={cases} onRefresh={refreshCases} />
//           )}
//           {screen === "variance" && <VarianceAnalysis cases={cases} />}
//           {/* {screen === "ai-audit" && (
//             <AIAuditScreen cases={cases} onCaseCreated={refreshCases} activeCaseId={activeCaseId} />
//           )} */}

//           {screen === "ai-audit" && (
//          <AIAuditScreen
//            cases={cases}
//            onCaseCreated={refreshCases}
//            activeCaseId={activeCaseId}
//            batchCaseIds={batchCaseIds}
//          />
//        )}
//           {/* {screen === "reports" && <ReportsScreen cases={cases} />} */}
//           {screen === "reports"      && (
//             canViewReports
//               ? <ReportsScreen cases={cases} />
//               : <AccessDenied requiredRole="Provider or above" />
//           )}
//           {/* {screen === "upload" && (
//             <DataUpload onAuditStarted={(id) => {
//               setActiveCaseId(id);
//               refreshCases();
//               setScreen("ai-audit");
//             }} />
//           )} */}
//           {screen === "upload" && (
//          <DataUpload
//            onAuditStarted={(id) => {
//              setActiveCaseId(id);
//              refreshCases();
//              setScreen("ai-audit");
//            }}
//            onBatchStarted={(ids) => {
//              setBatchCaseIds(ids);
//              refreshCases();
//              setScreen("ai-audit");
//            }}
//          />
//        )}
//           {screen === "Administration" && (
//             isSuperAdmin
//               ? <Administration setScreen={setScreen} onDataCleared={refreshCases} />
//               : <AccessDenied requiredRole="Super Admin" />
//           )}
//           {screen === "audit-detail" && (
//             <AuditDetail auditCase={selectedCase} setScreen={setScreen}
//               onHITLDecision={refreshCases} />
//           )}
//         </div>
//       </div>
 
//       {/* Notification overlay */}
//       {notifOpen && (
//         <div onClick={() => setNotifOpen(false)}
//           style={{ position:"fixed", inset:0, zIndex:99 }} />
//       )}
//     </div>
//   );
// }


import { useState, useEffect, useRef, useCallback, Fragment } from "react";
import {
  AreaChart, Area, BarChart, Bar,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import {
  uploadAuditFiles,
  startAudit,
  listAuditCases,
  getAuditStatus,
  pollAuditStatus,
  submitHITLDecision,
  downloadReport,
  startBatchAuditFromAPI,
  clearAllAuditData,
  getAuditConfig,
  updateAuditConfig,
  previewAPIPolicies
} from "../../api/wcAuditAPI";
 

import { useWCRoles } from "../../hooks/useWCRoles";

// ── Color Palette ─────────────────────────────────────────────────────────────
const C = {
  navy:    "#0D1B2A",
  navyMid: "#132338",
  navyLt:  "#1A3050",
  accent:  "#1E6FD9",
  accentLt:"#3D8FFF",
  teal:    "#0ABFBC",
  amber:   "#F59E0B",
  red:     "#EF4444",
  green:   "#10B981",
  purple:  "#7C3AED",
  bg:      "#F0F4FA",
  card:    "#FFFFFF",
  border:  "#E2EAF4",
  text:    "#1A2B42",
  muted:   "#6B7E99",
};
 
// ── Formatters ────────────────────────────────────────────────────────────────
const fmt = (n) =>
  n == null ? "—" :
  n >= 1_000_000 ? `$${(n / 1_000_000).toFixed(1)}M` :
  `$${(n / 1_000).toFixed(0)}K`;
const pct   = (n) => `${n ?? 0}%`;
const money = (n) => n == null ? "—" : `$${Number(n).toLocaleString()}`;

function AccessDenied({ requiredRole }) {
  return (
    <div style={{ display:"flex", flexDirection:"column", alignItems:"center",
      justifyContent:"center", height:300, gap:16, color:C.muted }}>
      <span style={{ fontSize:48 }}>🔒</span>
      <div style={{ textAlign:"center" }}>
        <div style={{ fontSize:16, fontWeight:700, color:C.text, marginBottom:6 }}>
          Access Restricted
        </div>
        <div style={{ fontSize:13 }}>
          This section requires <strong>{requiredRole}</strong> access.
          Contact your administrator to request the appropriate role.
        </div>
      </div>
    </div>
  );
}
 
// ── Shared Atoms ──────────────────────────────────────────────────────────────
const RiskBadge = ({ risk }) => {
  const map = {
    high:   { bg:"#FEE2E2", color:"#DC2626", label:"High Risk" },
    High:   { bg:"#FEE2E2", color:"#DC2626", label:"High Risk" },
    medium: { bg:"#FEF3C7", color:"#D97706", label:"Medium" },
    Medium: { bg:"#FEF3C7", color:"#D97706", label:"Medium" },
    low:    { bg:"#D1FAE5", color:"#059669", label:"Low" },
    Low:    { bg:"#D1FAE5", color:"#059669", label:"Low" },
  };
  const s = map[risk] || map.Low;
  return (
    <span style={{ background:s.bg, color:s.color, padding:"2px 10px",
      borderRadius:20, fontSize:11, fontWeight:700, whiteSpace:"nowrap" }}>
      {s.label}
    </span>
  );
};
 
const StatusBadge = ({ status }) => {
  const map = {
    "Under Review": { bg:"#EDE9FE", color:"#7C3AED" },
    "Pending":       { bg:"#FEF9C3", color:"#B45309" },
    "pending":       { bg:"#FEF9C3", color:"#B45309" },
    "Completed":     { bg:"#DCFCE7", color:"#16A34A" },
    "completed":     { bg:"#DCFCE7", color:"#16A34A" },
    "In Progress":   { bg:"#DBEAFE", color:"#1D4ED8" },
    "running":       { bg:"#DBEAFE", color:"#1D4ED8" },
    "processing":    { bg:"#DBEAFE", color:"#1D4ED8" },
    "error":         { bg:"#FEE2E2", color:"#DC2626" },
    "hitl_pending":  { bg:"#EDE9FE", color:"#7C3AED" },
    "rejected":      { bg:"#FEE2E2", color:"#DC2626" },
  };
  const s = map[status] || { bg:"#F3F4F6", color:"#374151" };
  return (
    <span style={{ background:s.bg, color:s.color, padding:"2px 10px",
      borderRadius:20, fontSize:11, fontWeight:600 }}>
      {status}
    </span>
  );
};
 
const KpiCard = ({ label, value, sub, subColor = "#10B981", icon, accent }) => (
  <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14,
    padding:"20px 24px", flex:1, minWidth:180, position:"relative", overflow:"hidden" }}>
    <div style={{ position:"absolute", top:0, left:0, width:4, height:"100%",
      background:accent || C.accent, borderRadius:"14px 0 0 14px" }} />
    <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
      <div>
        <div style={{ fontSize:12, color:C.muted, fontWeight:600, textTransform:"uppercase",
          letterSpacing:1, marginBottom:6 }}>{label}</div>
        <div style={{ fontSize:28, fontWeight:800, color:C.text, lineHeight:1 }}>{value}</div>
        {sub && <div style={{ fontSize:12, color:subColor, fontWeight:600, marginTop:6 }}>{sub}</div>}
      </div>
      {icon && <div style={{ fontSize:28, opacity:0.15, color:accent || C.accent }}>{icon}</div>}
    </div>
  </div>
);
 
const SectionHeader = ({ title, sub, action, onAction }) => (
  <div style={{ display:"flex", justifyContent:"space-between",
    alignItems:"center", marginBottom:18 }}>
    <div>
      <h2 style={{ margin:0, fontSize:18, fontWeight:700, color:C.text }}>{title}</h2>
      {sub && <p style={{ margin:"4px 0 0", fontSize:13, color:C.muted }}>{sub}</p>}
    </div>
    {action && (
      <button onClick={onAction} style={{ background:C.accent, color:"#fff", border:"none",
        borderRadius:8, padding:"7px 16px", fontSize:13, fontWeight:600, cursor:"pointer" }}>
        {action}
      </button>
    )}
  </div>
);
 
// ── Chart data helpers ────────────────────────────────────────────────────────
function buildVarianceTrendData(cases) {
  const byMonth = {};
  cases
    .filter(c => c.created_at && c.overall_variance?.earned_premium != null)
    .forEach(c => {
      const d = new Date(c.created_at);
      // Sort key: "YYYY-MM" for correct chronological ordering
      const key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
      const label = d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
      if (!byMonth[key]) byMonth[key] = { date: label, variance: 0, premium: 0, estPremium: 0, count: 0, _key: key };
      byMonth[key].variance   += Math.abs(c.overall_variance?.variance || 0);
      byMonth[key].premium    += c.overall_variance?.earned_premium || 0;
      byMonth[key].estPremium += c.overall_variance?.est_premium || 0;
      byMonth[key].count      += 1;
    });
  return Object.values(byMonth).sort((a, b) => a._key.localeCompare(b._key));
  // No more slice(-10) — show all audit months
}
function buildMonthlyAuditData(cases) {
  const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"];
  const byMonth = {};
  cases.forEach(c => {
    if (!c.created_at) return;
    const m = MONTHS[new Date(c.created_at).getMonth()];
    if (!byMonth[m]) byMonth[m] = { month:m, completed:0, pending:0, highRisk:0 };
    if (c.status === "completed" || c.status === "rejected") byMonth[m].completed += 1;
    else if (["pending","processing","running","hitl_pending"].includes(c.status)) byMonth[m].pending += 1;
    if (c.risk_level === "high") byMonth[m].highRisk += 1;
  });
  return MONTHS.filter(m => byMonth[m]).map(m => byMonth[m]);
}
 
// ═══════════════════════════════════════════════════════════════════════════════
// SCREENS
// ═══════════════════════════════════════════════════════════════════════════════
 
// ── Dashboard ─────────────────────────────────────────────────────────────────
function Dashboard({ setScreen, setSelectedCase, cases }) {
  const [hovered, setHovered] = useState(null);
  console.log("intial cases data",cases);
  
  const high    = cases.filter(c => c.risk_level === "high").length;
  const done    = cases.filter(c => c.status === "completed").length;
  // const refunds = cases.filter(c => c.recommendation === "refund")
  //                      .reduce((s, c) => s + Math.abs(c.variance || 0), 0);

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
  console.log("cases variance perecntage more than 20", cases.filter(c=>(Math.abs(c.variance_pct)>20)));
  
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

        <KpiCard label="Refunds"  value={fmt(refunds)}              accent={C.green} icon="↩️" />
        <KpiCard label="Adittional Premium"  value={fmt(additionalPremium)}              accent={C.green} icon="↪️" />
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
 
 
// ── Policies Screen ───────────────────────────────────────────────────────────
function PoliciesScreen({ setScreen, setSelectedCase, cases, onRefresh }) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");
 
  const filtered = cases.filter(c =>
    (filter === "All" || c.risk_level?.toLowerCase() === filter.toLowerCase()) &&
    (c.policy_number?.toLowerCase().includes(search.toLowerCase()) ||
     String(c.audit_case_id).includes(search))
  );

  console.log("filtered data -->",cases);
  
 
  const high    = cases.filter(c => c.risk_level === "high").length;
  const pending = cases.filter(c => ["pending","running"].includes(c.status)).length;
  const done    = cases.filter(c => c.status === "completed").length;
 
  return (
    <div>
      <div style={{ display:"flex", gap:16, marginBottom:24, flexWrap:"wrap" }}>
        <KpiCard label="Total Policies"  value={cases.length} sub="Active policy terms"         accent={C.accent} />
        <KpiCard label="Pending Review"  value={pending}      sub="Awaiting auditor action"      accent={C.amber}  />
        <KpiCard label="High Risk"       value={high}         sub="Require immediate attention"  accent={C.red}    />
        <KpiCard label="Completed"       value={done}         sub="Fully audited"                accent={C.green}  />
      </div>
 
      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center",
          marginBottom:20, flexWrap:"wrap", gap:12 }}>
          <h2 style={{ margin:0, fontSize:18, fontWeight:700, color:C.text }}>Policy Management</h2>
          <div style={{ display:"flex", gap:10, alignItems:"center", flexWrap:"wrap" }}>
            <input value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Search policy # or case ID..."
              style={{ border:`1px solid ${C.border}`, borderRadius:8, padding:"8px 14px",
                fontSize:13, width:240, outline:"none", color:C.text }} />
            {["All","High","Medium","Low"].map(f => (
              <button key={f} onClick={() => setFilter(f)}
                style={{ background:filter === f ? C.accent : C.bg,
                  color:filter === f ? "#fff" : C.muted,
                  border:`1px solid ${filter === f ? C.accent : C.border}`,
                  borderRadius:20, padding:"5px 16px", fontSize:12, fontWeight:600, cursor:"pointer" }}>
                {f}
              </button>
            ))}
            <button onClick={onRefresh}
              style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:8,
                padding:"7px 14px", fontSize:12, cursor:"pointer", color:C.muted }}>
              ↻ Refresh
            </button>
          </div>
        </div>
 
        {cases.length === 0 ? (
          <div style={{ textAlign:"center", padding:60, color:C.muted, fontSize:14 }}>
            No audit cases found. Go to <strong>Data Upload</strong> to run your first audit.
          </div>
        ) : (
          <>
            <table style={{ width:"100%", borderCollapse:"collapse" }}>
              <thead>
                <tr style={{ borderBottom:`2px solid ${C.border}`, background:"#F8FAFD" }}>
                  {["Policy Number","Insured Name","St.","Variance","Earned Premium",
                    "Risk","Status","Agent Name","Actions"].map(h => (
                    <th key={h} style={{ textAlign:"left", padding:"10px 14px", fontSize:11,
                      fontWeight:700, color:C.muted, textTransform:"uppercase", letterSpacing:0.8 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map(c => (
                  <tr key={c.audit_case_id}
                    style={{ borderBottom:`1px solid ${C.border}`, transition:"background 0.1s" }}
                    onMouseEnter={e => e.currentTarget.style.background = "#F5F8FF"}
                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
 
                    {/* Policy Number */}
                    <td style={{ padding:"13px 14px", fontSize:13, fontWeight:700, color:C.accent,
                      cursor:"pointer" }}
                      onClick={() => { setSelectedCase(c); setScreen("audit-detail"); }}>
                      {c.policy_number}
                    </td>
 
                    {/* Insured Name — not returned by current API */}
                    <td style={{ padding:"13px 14px", fontSize:13, color:C.muted }}>{c.insured_name}</td>
 
                    {/* St. — not returned by current API */}
                    <td style={{ padding:"13px 14px", fontSize:13, fontWeight:700, color:C.muted }}>{c.class_code_variance[0]?.StateCode}</td>
 
                    {/* Variance with progress bar */}
                    <td style={{ padding:"13px 14px" }}>
                      <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                        <div style={{ width:50, height:6, borderRadius:3, background:C.border, overflow:"hidden" }}>
                          <div style={{ width:`${Math.min((c.variance_pct || 0) * 3, 100)}%`,
                            height:"100%",
                            background:(c.variance_pct || 0) >= 25 ? C.red :
                                       (c.variance_pct || 0) >= 10 ? C.amber : C.green }} />
                        </div>
                        <span style={{ fontSize:13, fontWeight:700,
                          color:(c.variance_pct || 0) >= 25 ? C.red :
                               (c.variance_pct || 0) >= 10 ? C.amber : C.green }}>
                          {c.variance_pct != null ? `${Number(c.variance_pct).toFixed(1)}%` : "—"}
                        </span>
                      </div>
                    </td>
 
                    {/* Earned Premium */}
                    <td style={{ padding:"13px 14px", fontSize:13, fontWeight:600, color:C.text }}>
                      {fmt(c.overall_variance?.earned_premium)}
                    </td>
 
                    {/* Risk */}
                    <td style={{ padding:"13px 14px" }}><RiskBadge risk={c.risk_level} /></td>
 
                    {/* Status */}
                    <td style={{ padding:"13px 14px" }}><StatusBadge status={c.status} /></td>
 
                    {/* Agent Name — not in API response */}
                    <td style={{ padding:"13px 14px", fontSize:12, color:C.muted }}>—</td>
 
                    {/* Actions */}
                    <td style={{ padding:"13px 14px" }}>
                      <div style={{ display:"flex", gap:6 }}>
                        <button onClick={() => { setSelectedCase(c); setScreen("audit-detail"); }}
                          style={{ background:C.accent, color:"#fff", border:"none", borderRadius:6,
                            padding:"5px 12px", fontSize:12, fontWeight:600, cursor:"pointer" }}>
                          Review
                        </button>
                        <button onClick={() => downloadReport(c.audit_case_id)}
                          style={{ background:C.bg, color:C.muted, border:`1px solid ${C.border}`,
                            borderRadius:6, padding:"5px 10px", fontSize:12, cursor:"pointer" }}>
                          ⬇
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <div style={{ textAlign:"center", padding:40, color:C.muted, fontSize:14 }}>
                No cases match your filter.
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
 
 
// ── Variance Analysis ─────────────────────────────────────────────────────────
function VarianceAnalysis({ cases }) {
  const [activeIdx, setActiveIdx] = useState(null);
 
  const completedCases = cases.filter(c =>
    ["completed","hitl_pending","pending"].includes(c.status) &&
    c.class_code_variance && c.class_code_variance.length > 0
  );
  const allCCVariance = completedCases.flatMap(c => c.class_code_variance || []);
  
  console.log("additional premium ",completedCases);
  
  // Aggregate per class code — include all exposure and premium fields
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
 
  // KPI derivations
  const totalExposureDelta = ccRows.reduce((s, r) => s + Math.abs(r.est_exposure - r.earned_exposure), 0);
  const estYtdImpact       = ccRows.filter(r => r.variance > 0).reduce((s, r) => s + r.variance, 0);
  const refundDue          = ccRows.filter(r => r.variance < 0).reduce((s, r) => s + Math.abs(r.variance), 0);
  const mismatches         = ccRows.filter(r => Math.abs(r.variance) > 500).length;
  const totalEstYtdPremium = ccRows.reduce(
  (s, r) => s + r.est_ytd_premium,
  0
);
 
  return (
    <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
 
      {/* KPI row */}
      <div style={{ display:"flex", gap:16 }}>
        <KpiCard label="Total Exposure Delta"    value={money(Math.round(totalExposureDelta))} sub="↑ Across all policies"      accent={C.red}    />
        <KpiCard label="EST YTD Premium Impact"  value={money(Math.round(totalEstYtdPremium))}       sub="Net additional owed"         accent={C.amber}  />
        <KpiCard label="Additional Premium"        value={money(Math.round(estYtdImpact))}        sub="Underpaid — owed to insurer"  accent={C.amber}  />
        <KpiCard label="Class Code Mismatches"   value={mismatches}                             sub="Require reclassification"   accent={C.purple} />
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
 
                      {/* Class Code */}
                      <td style={{ padding:"13px 14px", fontSize:13, fontWeight:700, color:C.accent }}>
                        {row.code}
                      </td>
 
                      {/* Description — using state code as description */}
                      <td style={{ padding:"13px 14px", fontSize:13, color:C.text }}>
                        {row.state}
                      </td>
 
                      {/* EST Exposure */}
                      <td style={{ padding:"13px 14px", fontSize:13, color:C.text }}>
                        {money(Math.round(row.est_exposure))}
                      </td>
 
                      {/* Earned Exposure */}
                      <td style={{ padding:"13px 14px", fontSize:13, color:C.text }}>
                        {money(Math.round(row.earned_exposure))}
                      </td>
 
                      {/* Delta (EST – Earned exposure) */}
                      <td style={{ padding:"13px 14px", fontWeight:700, fontSize:13,
                        color: delta > 0 ? C.red : C.green }}>
                        {delta > 0 ? "+" : ""}{money(Math.round(delta))}
                      </td>
 
                      {/* Net Rate — not available from API */}
                      <td style={{ padding:"13px 14px", fontSize:13, color:C.muted }}>—</td>
 
                      {/* EST YTD Premium */}
                      <td style={{ padding:"13px 14px", fontWeight:700, fontSize:13,
                        color: row.variance > 0 ? C.red : C.green }}>
                        {money(Math.round(row.est_ytd_premium))}
                      </td>
 
                      {/* Drill down */}
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
 
 
// ── Results + HITL Panel ──────────────────────────────────────────────────────
function ResultsAndHITLPanel({ status, onApprove }) {
  const [note,       setNote]       = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [decision,   setDecision]   = useState(null);
 
  const isHITL      = status.status === "hitl_pending";
  const isCompleted = status.status === "completed";
  const ov          = status.overall_variance || {};
 
  const riskColor = status.risk_level === "high"   ? C.red
                  : status.risk_level === "medium"  ? C.amber : C.green;
  const recColor  = status.recommendation === "additional_premium" ? C.amber
                  : status.recommendation === "refund"             ? C.green
                  : status.recommendation === "clarification"      ? C.purple : C.muted;
 
  const handleDecision = async (d) => {
    setDecision(d);
    setSubmitting(true);
    try {
      await onApprove(d, note);
    } finally {
      setSubmitting(false);
      setDecision(null);
    }
  };
 
  return (
    <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
 
      {/* HITL banner */}
      {isHITL && (
        <div style={{ padding:"14px 18px", borderRadius:12,
          background:"linear-gradient(135deg, #FEF3C7, #FDE68A)",
          border:`1px solid ${C.amber}`, display:"flex", alignItems:"center", gap:14 }}>
          <span style={{ fontSize:26 }}>⚠️</span>
          <div>
            <div style={{ fontSize:14, fontWeight:800, color:"#78350F" }}>
              Human Review Required — High-Risk Audit
            </div>
            <div style={{ fontSize:12, color:"#92400E", marginTop:2 }}>
              The AI pipeline has paused and is awaiting your approval before finalizing.
              Review the findings below then approve or reject.
            </div>
          </div>
        </div>
      )}
 
      {/* Metrics grid */}
      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:20 }}>
        <div style={{ fontSize:14, fontWeight:700, color:C.text, marginBottom:12 }}>
          Audit Results — Case #{status.audit_case_id}
        </div>
 
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10, marginBottom:14 }}>
          {[
            { label:"Overall Variance",
              value:money(Math.round(ov.variance || status.variance || 0)),
              color:(ov.variance || status.variance || 0) > 0 ? C.red : C.green },
            { label:"Variance %",
              value:`${Number(ov.variance_pct || status.variance_pct || 0).toFixed(2)}%`,
              color:Math.abs(ov.variance_pct || status.variance_pct || 0) > 10 ? C.red : C.green },
            { label:"Risk Level",        value:status.risk_level?.toUpperCase() || "—", color:riskColor },
            { label:"Recommendation",    value:status.recommendation?.replace(/_/g," ") || "—", color:recColor },
            { label:"Earned Premium",    value:money(Math.round(ov.earned_premium    || 0)), color:C.text },
            { label:"EST YTD Premium",   value:money(Math.round(ov.est_ytd_premium   || 0)), color:C.text },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ background:C.bg, borderRadius:10, padding:"11px 14px" }}>
              <div style={{ fontSize:10, color:C.muted, fontWeight:700, textTransform:"uppercase",
                letterSpacing:0.8, marginBottom:3 }}>{label}</div>
              <div style={{ fontSize:15, fontWeight:800, color }}>{value}</div>
            </div>
          ))}
        </div>
 
        {/* Flagged class codes */}
        {(status.class_code_variance || []).filter(r => r.is_flagged).length > 0 && (
          <div style={{ marginBottom:14 }}>
            <div style={{ fontSize:12, fontWeight:700, color:C.text, marginBottom:8 }}>
              Flagged Class Codes
            </div>
            {(status.class_code_variance || []).filter(r => r.is_flagged).map((row, i) => (
              <div key={i} style={{ display:"flex", justifyContent:"space-between",
                alignItems:"center", padding:"8px 12px", background:"#FEF2F2",
                borderRadius:8, marginBottom:6, border:`1px solid #FECACA` }}>
                <div style={{ fontSize:12, color:C.text }}>
                  <strong>Class {row.ClassCode}</strong> ({row.StateCode}) —{" "}
                  Variance: <strong style={{ color:C.red }}>{money(Math.round(row.variance))}</strong>
                  {" "}({Number(row.variance_pct).toFixed(1)}%)
                </div>
                <span style={{ fontSize:10, fontWeight:700, color:C.red,
                  background:"#FEE2E2", padding:"2px 8px", borderRadius:20 }}>⚠ Flag</span>
              </div>
            ))}
          </div>
        )}
 
        {/* HITL Approval Form */}
        {isHITL && (
          <div style={{ borderTop:`1px solid ${C.border}`, paddingTop:14 }}>
            <div style={{ fontSize:13, fontWeight:700, color:C.text, marginBottom:8 }}>
              Auditor Decision
            </div>
            <textarea value={note} onChange={e => setNote(e.target.value)}
              placeholder="Add notes, overrides, or justification for your decision (optional)…"
              style={{ width:"100%", border:`1px solid ${C.border}`, borderRadius:8, padding:"10px 12px",
                fontSize:13, color:C.text, resize:"vertical", minHeight:72, outline:"none",
                boxSizing:"border-box", marginBottom:12, fontFamily:"inherit" }} />
            <div style={{ display:"flex", gap:10 }}>
              <button disabled={submitting} onClick={() => handleDecision("approve")}
                style={{ flex:1, background:submitting && decision === "approve" ? "#86EFAC" : C.green,
                  color:"#fff", border:"none", borderRadius:10, padding:"12px 0",
                  fontSize:14, fontWeight:800, cursor:submitting ? "default" : "pointer",
                  display:"flex", alignItems:"center", justifyContent:"center", gap:8 }}>
                {submitting && decision === "approve" ? "⏳ Submitting…" : "✓ Approve & Finalize"}
              </button>
              <button disabled={submitting} onClick={() => handleDecision("reject")}
                style={{ flex:1, background:submitting && decision === "reject" ? "#FCA5A5" : C.red,
                  color:"#fff", border:"none", borderRadius:10, padding:"12px 0",
                  fontSize:14, fontWeight:800, cursor:submitting ? "default" : "pointer",
                  display:"flex", alignItems:"center", justifyContent:"center", gap:8 }}>
                {submitting && decision === "reject" ? "⏳ Submitting…" : "✗ Reject"}
              </button>
            </div>
          </div>
        )}
 
        {/* Download for completed */}
        {isCompleted && (
          <button onClick={() => downloadReport(status.audit_case_id)}
            style={{ width:"100%", background:C.accent, color:"#fff", border:"none", borderRadius:10,
              padding:"11px 0", fontSize:13, fontWeight:700, cursor:"pointer", marginTop:4 }}>
            ⬇ Download Audit Report
          </button>
        )}
      </div>
    </div>
  );
}
 
 
// // ── AI Audit Screen ───────────────────────────────────────────────────────────


// function AIAuditScreen({ cases, onCaseCreated, activeCaseId: propCaseId, batchCaseIds }) {
//   // ── Single-case watch (original behaviour) ─────────────────────
//   const [auditCaseId, setAuditCaseId] = useState(null);
//   const [status,      setStatus]      = useState(null);
//   const [logs,        setLogs]        = useState([]);
//   const [agentStatus, setAgentStatus] = useState({});
//   const stopPollRef = useRef(null);
 
//   // ── Batch mode state ────────────────────────────────────────────
//   // batchQueue: ordered list of case IDs still waiting for HITL or to finish
//   const [batchQueue,      setBatchQueue]      = useState([]);  // all case IDs in this batch
//   const [batchStatuses,   setBatchStatuses]   = useState({}); // caseId → status object
//   const [hitlQueuedIds,   setHitlQueuedIds]   = useState([]); // cases waiting for HITL
//   const [activeHITLCase,  setActiveHITLCase]  = useState(null); // currently displayed HITL
//   const batchPollsRef = useRef({});  // caseId → stop function
 
//   const isBatchMode = batchCaseIds && batchCaseIds.length > 0;
 
//   const AGENT_LOG_LABELS = {
//     ingestion_excel:      "Ingestion Agent     → payroll Excel parsed",
//     ingestion_xml:        "Policy Parser       → XML class codes loaded",
//     ingestion_audit_meta: "Metadata Agent      → audit dates & submission count loaded",
//     api_ingestion_node:   "API Ingestion       → payroll & policy config fetched from API",
//     officer_agent:        "Officer Agent       → officer payroll classification checked",
//     class_code_agent:     "Class Code Agent    → class code usage validated",
//     frequency_agent:      "Frequency Agent     → submission frequency analysed",
//     premium_agent:        "Premium Agent       → variance calculation complete",
//     risk_assessor:        "Risk Assessor       → risk level & recommendation assigned",
//     explanation_agent:    "Explanation Agent   → AI narrative generated",
//     hitl_checkpoint:      "HITL Checkpoint     → paused for human review",
//   };
 
//   // ── Single-case watcher (unchanged logic) ───────────────────────
//   const watchCase = useCallback((caseId) => {
//     setAuditCaseId(caseId);
//     setLogs([`[${new Date().toLocaleTimeString()}] 🚀 Workflow started — Case #${caseId}`]);
//     if (stopPollRef.current) stopPollRef.current();
//     const loggedAgents = new Set();
 
//     stopPollRef.current = pollAuditStatus(caseId, (s) => {
//       setStatus(s);
//       const ts = new Date().toLocaleTimeString();
//       const newAgentSt = {};
//       (s.agent_logs || []).forEach(log => {
//         if (!log.agent) return;
//         newAgentSt[log.agent] = log.status === "error" ? "error" : "complete";
//         if (!loggedAgents.has(log.agent)) {
//           loggedAgents.add(log.agent);
//           const label  = AGENT_LOG_LABELS[log.agent] ?? log.agent;
//           const prefix = log.status === "error" ? "✗" : log.status === "skipped" ? "⏭" : "✓";
//           setLogs(l => [...l, `[${ts}] ${prefix} ${label}`]);
//         }
//       });
//       setAgentStatus(prev => ({...prev, ...newAgentSt}));
//       if (s.status === "hitl_pending") {
//         setLogs(l => [...l,
//           `[${ts}] ⚠️  HITL required — case paused for human review`,
//           `[${ts}]    Risk: ${s.risk_level?.toUpperCase()}, Variance: ${Number(s.variance_pct || 0).toFixed(2)}%`,
//         ]);
//         onCaseCreated?.();
//       }
//       if (s.status === "completed") {
//         setLogs(l => [...l,
//           `[${ts}] 🎉 Audit complete`,
//           `[${ts}]    Variance: ${Number(s.variance_pct || 0).toFixed(2)}%  |  Risk: ${s.risk_level}  |  Rec: ${s.recommendation}`,
//         ]);
//         onCaseCreated?.();
//         stopPollRef.current?.();
//       }
//       if (s.status === "rejected") { setLogs(l => [...l, `[${ts}] ✗ Audit rejected`]); stopPollRef.current?.(); }
//       if (s.status === "error")    { setLogs(l => [...l, `[${ts}] ✗ Error: ${s.errors}`]); stopPollRef.current?.(); }
//     });
//   }, [onCaseCreated]);
 
//   // ── Batch: start polling each case ID ───────────────────────────
//   useEffect(() => {
//     if (!isBatchMode || batchCaseIds.length === 0) return;
//     setBatchQueue(batchCaseIds);
//     setBatchStatuses({});
//     setHitlQueuedIds([]);
//     setActiveHITLCase(null);
 
//     // Clear any previous batch polls
//     Object.values(batchPollsRef.current).forEach(stop => stop?.());
//     batchPollsRef.current = {};
 
//     batchCaseIds.forEach(caseId => {
//       const stop = pollAuditStatus(caseId, (s) => {
//         setBatchStatuses(prev => ({ ...prev, [caseId]: s }));
//         onCaseCreated?.();
 
//         if (s.status === "hitl_pending") {
//           setHitlQueuedIds(prev =>
//             prev.includes(caseId) ? prev : [...prev, caseId]
//           );
//           // Show the first waiting HITL case immediately
//           setActiveHITLCase(cur => cur ?? caseId);
//         }
 
//         if (["completed", "rejected", "error"].includes(s.status)) {
//           // Stop polling this case
//           batchPollsRef.current[caseId]?.();
//           delete batchPollsRef.current[caseId];
 
//           // Remove from HITL queue if it was there
//           setHitlQueuedIds(prev => {
//             const next = prev.filter(id => id !== caseId);
//             return next;
//           });
 
//           // If this was the active HITL case, advance to the next
//           setActiveHITLCase(cur => {
//             if (cur === caseId) {
//               const remaining = hitlQueuedIds.filter(id => id !== caseId);
//               return remaining[0] ?? null;
//             }
//             return cur;
//           });
//         }
//       });
//       batchPollsRef.current[caseId] = stop;
//     });
 
//     return () => {
//       Object.values(batchPollsRef.current).forEach(stop => stop?.());
//       batchPollsRef.current = {};
//     };
//   }, [JSON.stringify(batchCaseIds)]); // eslint-disable-line react-hooks/exhaustive-deps
 
//   // Advance activeHITLCase whenever hitlQueuedIds changes
//   useEffect(() => {
//     if (!activeHITLCase && hitlQueuedIds.length > 0) {
//       setActiveHITLCase(hitlQueuedIds[0]);
//     }
//   }, [hitlQueuedIds, activeHITLCase]);
 
//   // ── Cleanup on unmount ──────────────────────────────────────────
//   useEffect(() => {
//     return () => {
//       stopPollRef.current?.();
//       Object.values(batchPollsRef.current).forEach(stop => stop?.());
//     };
//   }, []);
 
//   useEffect(() => {
//     if (propCaseId && propCaseId !== auditCaseId) watchCase(propCaseId);
//   }, [propCaseId]); // eslint-disable-line react-hooks/exhaustive-deps
 
//   useEffect(() => {
//     if (propCaseId || isBatchMode) return;
//     const active = cases.find(c => ["running","pending","hitl_pending"].includes(c.status));
//     if (active && active.audit_case_id !== auditCaseId) watchCase(active.audit_case_id);
//   }, [cases]); // eslint-disable-line react-hooks/exhaustive-deps
 
//   const agentLabels = [
//     { keys:["ingestion_excel","ingestion_audit_meta","api_ingestion_node"], label:"Ingestion Agent",   sub:"Payroll + audit metadata" },
//     { keys:["ingestion_xml"],                          label:"Policy Parser",     sub:"XML class codes & rates" },
//     { keys:["officer_agent"],                          label:"Officer Agent",     sub:"Officer classification" },
//     { keys:["class_code_agent"],                       label:"Class Code Agent",  sub:"Class code validation" },
//     { keys:["frequency_agent"],                        label:"Frequency Agent",   sub:"Submission frequency" },
//     { keys:["premium_agent","risk_assessor"],          label:"Premium Agent",     sub:"Variance & risk scoring" },
//     { keys:["explanation_agent"],                      label:"Explanation Agent", sub:"AI narrative" },
//   ];
 
//   const resolveStepStatus = (keys) => {
//     let anyError = false, doneCount = 0;
//     for (const k of keys) {
//       if (agentStatus[k] === "error")    anyError = true;
//       if (agentStatus[k] === "complete") doneCount++;
//     }
//     if (anyError)                  return "error";
//     if (doneCount === keys.length) return "complete";
//     if (doneCount > 0)             return "partial";
//     return "pending";
//   };
 
//   // ── Batch summary helpers ────────────────────────────────────────
//   const batchDone      = Object.values(batchStatuses).filter(s => s.status === "completed").length;
//   const batchRejected  = Object.values(batchStatuses).filter(s => s.status === "rejected").length;
//   const batchError_cnt = Object.values(batchStatuses).filter(s => s.status === "error").length;
//   const batchRunning   = Object.values(batchStatuses).filter(s => ["pending","processing","running"].includes(s.status)).length;
//   const batchHITL      = hitlQueuedIds.length;
 
//   const activeHITLStatus = activeHITLCase ? batchStatuses[activeHITLCase] : null;
 
//   // ── HITL decision handler for batch mode ────────────────────────
//   const handleBatchHITL = async (decision, note) => {
//     if (!activeHITLCase) return;
//     try {
//       await submitHITLDecision(activeHITLCase, { decision, notes: note });
//       const fresh = await getAuditStatus(activeHITLCase);
//       setBatchStatuses(prev => ({ ...prev, [activeHITLCase]: fresh }));
//       onCaseCreated?.();
 
//       // Remove from HITL queue and advance
//       setHitlQueuedIds(prev => {
//         const next = prev.filter(id => id !== activeHITLCase);
//         setActiveHITLCase(next[0] ?? null);
//         return next;
//       });
//     } catch (err) {
//       alert("HITL submission failed: " + (err.response?.data?.detail || err.message));
//     }
//   };
 
//   // ════════════════════════════════════════════════════════════════
//   // RENDER
//   // ════════════════════════════════════════════════════════════════
//   return (
//     <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
 
//       {/* Header card */}
//       <div style={{ background:`linear-gradient(135deg, ${C.navy} 0%, ${C.navyLt} 100%)`,
//         borderRadius:14, padding:28, color:"#fff" }}>
//         <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
//           <div>
//             <h2 style={{ margin:"0 0 6px", fontSize:22, fontWeight:800 }}>🤖 AI Audit Engine</h2>
//             <p style={{ margin:0, opacity:0.7, fontSize:14 }}>
//               LangGraph-powered multi-agent orchestration for automated earned exposure &amp; premium variance detection
//             </p>
//           </div>
//           {/* Single-case badge */}
//           {!isBatchMode && auditCaseId && (
//             <div style={{ textAlign:"right" }}>
//               <div style={{ fontSize:12, opacity:0.6, marginBottom:4 }}>Monitoring Case</div>
//               <div style={{ fontSize:22, fontWeight:800 }}>#{auditCaseId}</div>
//               {status && <StatusBadge status={status.status} />}
//             </div>
//           )}
//           {/* Batch badge */}
//           {isBatchMode && (
//             <div style={{ textAlign:"right", minWidth:160 }}>
//               <div style={{ fontSize:12, opacity:0.6, marginBottom:4 }}>Batch Mode</div>
//               <div style={{ fontSize:22, fontWeight:800 }}>{batchCaseIds.length} policies</div>
//               <div style={{ fontSize:12, opacity:0.6, marginTop:4 }}>
//                 ✅ {batchDone} done · ⚠️ {batchHITL} HITL · ⚙️ {batchRunning} running
//               </div>
//             </div>
//           )}
//         </div>
//         {!auditCaseId && !isBatchMode && (
//           <div style={{ marginTop:16, padding:"12px 16px", background:"rgba(255,255,255,0.07)",
//             borderRadius:10, fontSize:13, opacity:0.8 }}>
//             Upload files in <strong>Data Upload</strong> to run an audit. The AI pipeline will
//             automatically appear here once started.
//           </div>
//         )}
//       </div>
 
//       {/* ══════════════════════════════════════
//           BATCH MODE: KPI bar + HITL queue
//       ══════════════════════════════════════ */}
//       {isBatchMode && (
//         <>
//           {/* Batch progress KPIs */}
//           <div style={{ display:"flex", gap:14 }}>
//             <KpiCard label="Total Queued"   value={batchCaseIds.length}  sub="From API batch"          accent={C.accent} />
//             <KpiCard label="Completed"      value={batchDone}            sub="Fully audited"           accent={C.green}  />
//             <KpiCard label="HITL Pending"   value={batchHITL}            sub="Awaiting your review"    accent={C.amber}  />
//             <KpiCard label="Running"        value={batchRunning}         sub="In pipeline"             accent={C.purple} />
//             {(batchRejected + batchError_cnt) > 0 && (
//               <KpiCard label="Issues"       value={batchRejected + batchError_cnt} sub="Rejected / Error" accent={C.red} />
//             )}
//           </div>
 
//           {/* HITL review queue banner */}
//           {hitlQueuedIds.length > 0 && (
//             <div style={{ background:"linear-gradient(135deg, #FEF3C7, #FDE68A)",
//               border:`1px solid ${C.amber}`, borderRadius:12, padding:"14px 20px",
//               display:"flex", alignItems:"center", gap:14 }}>
//               <span style={{ fontSize:28 }}>⚠️</span>
//               <div style={{ flex:1 }}>
//                 <div style={{ fontSize:14, fontWeight:800, color:"#78350F" }}>
//                   {hitlQueuedIds.length} policy(ies) require human review
//                 </div>
//                 <div style={{ fontSize:12, color:"#92400E", marginTop:2 }}>
//                   Reviewing case #{activeHITLCase} now
//                   {hitlQueuedIds.length > 1
//                     ? ` · ${hitlQueuedIds.length - 1} more in queue after this`
//                     : ""}
//                 </div>
//               </div>
//               {/* Queue pills */}
//               <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
//                 {hitlQueuedIds.map((id, i) => (
//                   <button key={id} onClick={() => setActiveHITLCase(id)}
//                     style={{ background: id === activeHITLCase ? C.amber : "rgba(0,0,0,0.1)",
//                       color: id === activeHITLCase ? "#fff" : "#78350F",
//                       border:"none", borderRadius:20, padding:"4px 12px",
//                       fontSize:12, fontWeight:700, cursor:"pointer" }}>
//                     #{id}{i === 0 && id === activeHITLCase ? " ← now" : ""}
//                   </button>
//                 ))}
//               </div>
//             </div>
//           )}
 
//           {/* Active HITL panel */}
//           {activeHITLCase && activeHITLStatus && (
//             <div style={{ background:C.card, border:`2px solid ${C.amber}`, borderRadius:14, padding:24 }}>
//               <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
//                 <div>
//                   <div style={{ fontSize:16, fontWeight:800, color:C.text }}>
//                     Reviewing: {activeHITLStatus.policy_number} — Case #{activeHITLCase}
//                   </div>
//                   <div style={{ fontSize:12, color:C.muted, marginTop:2 }}>
//                     Risk: <strong style={{ color:C.red }}>{activeHITLStatus.risk_level?.toUpperCase()}</strong>
//                     &nbsp;·&nbsp;Variance: <strong>{Number(activeHITLStatus.variance_pct || 0).toFixed(2)}%</strong>
//                     &nbsp;·&nbsp;Rec: <strong>{activeHITLStatus.recommendation?.replace(/_/g," ")}</strong>
//                   </div>
//                 </div>
//                 <div style={{ display:"flex", gap:8 }}>
//                   <RiskBadge risk={activeHITLStatus.risk_level} />
//                   <StatusBadge status={activeHITLStatus.status} />
//                 </div>
//               </div>
//               <ResultsAndHITLPanel
//                 status={activeHITLStatus}
//                 onApprove={handleBatchHITL}
//               />
//             </div>
//           )}
 
//           {/* Batch policy status grid */}
//           <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
//             <SectionHeader title="Batch Policy Progress"
//               sub="All policies queued in this API batch — click a HITL case to review it" />
//             <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(260px, 1fr))", gap:10 }}>
//               {batchCaseIds.map(caseId => {
//                 const s = batchStatuses[caseId];
//                 const isHITL = hitlQueuedIds.includes(caseId);
//                 const isActive = caseId === activeHITLCase;
//                 const border = isActive ? `2px solid ${C.amber}` : isHITL ? `1px solid ${C.amber}` : `1px solid ${C.border}`;
//                 const bg     = isActive ? "#FFFBEB" : isHITL ? "#FFFDE7" : C.bg;
//                 return (
//                   <div key={caseId}
//                     onClick={() => isHITL && setActiveHITLCase(caseId)}
//                     style={{ background:bg, border, borderRadius:10, padding:"12px 16px",
//                       cursor:isHITL ? "pointer" : "default", transition:"all 0.15s" }}>
//                     <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
//                       <div style={{ fontSize:13, fontWeight:700, color:C.accent }}>
//                         {s?.policy_number || `Case #${caseId}`}
//                       </div>
//                       <StatusBadge status={s?.status || "pending"} />
//                     </div>
//                     <div style={{ fontSize:11, color:C.muted, marginTop:4 }}>
//                       Case #{caseId}
//                       {s?.variance_pct != null && ` · Var: ${Number(s.variance_pct).toFixed(1)}%`}
//                     </div>
//                     {isHITL && (
//                       <div style={{ marginTop:6, fontSize:11, fontWeight:700, color:C.amber }}>
//                         ⚠️ Awaiting HITL {isActive ? "(reviewing now)" : "(click to review)"}
//                       </div>
//                     )}
//                   </div>
//                 );
//               })}
//             </div>
//           </div>
//         </>
//       )}
 
//       {/* ══════════════════════════════════════
//           SINGLE-CASE MODE (original layout)
//       ══════════════════════════════════════ */}
//       {!isBatchMode && (
//         <div style={{ display:"flex", gap:16 }}>
//           {/* Agent Pipeline */}
//           <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24, flex:1 }}>
//             <SectionHeader title="Agent Pipeline Status" sub="Real-time LangGraph orchestration" />
//             <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
//               {agentLabels.map((a, i) => {
//                 const st        = resolveStepStatus(a.keys);
//                 const bgColor   = st === "complete" ? "#F0FDF4" : st === "error" ? "#FEF2F2" : st === "partial" ? "#EEF2FF" : C.bg;
//                 const bdColor   = st === "complete" ? C.green   : st === "error" ? C.red     : st === "partial" ? C.accent  : C.border;
//                 const circleClr = st === "complete" ? C.green   : st === "error" ? C.red     : st === "partial" ? C.accent  : C.border;
//                 const badge     = st === "complete" ? { bg:"#DCFCE7", color:C.green,  text:"Done" }
//                                 : st === "error"    ? { bg:"#FEE2E2", color:C.red,    text:"Error" }
//                                 : st === "partial"  ? { bg:"#DBEAFE", color:C.accent, text:"Running" }
//                                 :                    { bg:"#F3F4F6", color:C.muted,   text:"Pending" };
//                 const subText   = st === "complete" ? a.sub
//                                 : st === "error"    ? "Error encountered"
//                                 : st === "partial"  ? "Processing…" : "Waiting…";
//                 return (
//                   <div key={a.keys.join()} style={{ display:"flex", alignItems:"center", gap:14,
//                     padding:"12px 16px", borderRadius:10, transition:"all 0.3s",
//                     background:bgColor, border:`1px solid ${bdColor}` }}>
//                     <div style={{ width:32, height:32, borderRadius:"50%", flexShrink:0,
//                       display:"flex", alignItems:"center", justifyContent:"center", fontSize:14,
//                       background:circleClr, color: st === "pending" ? C.muted : "#fff" }}>
//                       {st === "complete" ? "✓" : st === "error" ? "✗" : st === "partial" ? "⚙" : i + 1}
//                     </div>
//                     <div style={{ flex:1 }}>
//                       <div style={{ fontSize:13, fontWeight:700, color:C.text }}>{a.label}</div>
//                       <div style={{ fontSize:11, color:C.muted }}>{subText}</div>
//                     </div>
//                     <span style={{ fontSize:11, fontWeight:600, padding:"3px 10px", borderRadius:20,
//                       background:badge.bg, color:badge.color }}>{badge.text}</span>
//                   </div>
//                 );
//               })}
//             </div>
//           </div>
 
//           {/* Live log + results */}
//           <div style={{ flex:1, display:"flex", flexDirection:"column", gap:16 }}>
//             <div style={{ background:C.navy, borderRadius:14, padding:20, flex:1, minHeight:300 }}>
//               <div style={{ fontSize:13, fontWeight:700, color:"#64B5F6", marginBottom:12,
//                 fontFamily:"monospace" }}>▶ AUDIT LOG</div>
//               <div style={{ fontFamily:"'Courier New', monospace", fontSize:11.5, color:"#A8D8A8",
//                 lineHeight:1.8, overflowY:"auto", maxHeight:280 }}>
//                 {logs.length === 0
//                   ? <span style={{ color:"#546E7A" }}>// Upload files then start an audit to see live output</span>
//                   : logs.map((l, i) => <div key={i}>{l}</div>)}
//               </div>
//             </div>
 
//             {status && ["completed","hitl_pending"].includes(status.status) && (
//               <ResultsAndHITLPanel status={status} onApprove={async (decision, note) => {
//                 try {
//                   await submitHITLDecision(status.audit_case_id, { decision, notes: note });
//                   const fresh = await getAuditStatus(status.audit_case_id);
//                   setStatus(fresh);
//                   onCaseCreated?.();
//                   const ts = new Date().toLocaleTimeString();
//                   setLogs(l => [...l, `[${ts}] ✓ HITL decision submitted: ${decision}`]);
//                 } catch (err) {
//                   alert("HITL submission failed: " + (err.response?.data?.detail || err.message));
//                 }
//               }} />
//             )}
//           </div>
//         </div>
//       )}
//     </div>
//   );
// }

function AIAuditScreen({ cases, onCaseCreated, activeCaseId: propCaseId, batchCaseIds }) {
  // ── Single-case watch (original behaviour) ─────────────────────
  const [auditCaseId, setAuditCaseId] = useState(null);
  const [status,      setStatus]      = useState(null);
  const [logs,        setLogs]        = useState([]);
  const [agentStatus, setAgentStatus] = useState({});
  const stopPollRef = useRef(null);
 
  // ── Batch mode state ────────────────────────────────────────────
  // batchQueue: ordered list of case IDs still waiting for HITL or to finish
  const [batchQueue,      setBatchQueue]      = useState([]);  // all case IDs in this batch
  const [batchStatuses,   setBatchStatuses]   = useState({}); // caseId → status object
  const [hitlQueuedIds,   setHitlQueuedIds]   = useState([]); // cases waiting for HITL
  const [activeHITLCase,  setActiveHITLCase]  = useState(null); // currently displayed HITL
  const batchPollsRef = useRef({});  // caseId → stop function
  const [batchView,        setBatchView]        = useState("table");  // "card" | "table"
 
  const isBatchMode = batchCaseIds && batchCaseIds.length > 0;
 
  const AGENT_LOG_LABELS = {
    ingestion_excel:      "Ingestion Agent     → payroll Excel parsed",
    ingestion_xml:        "Policy Parser       → XML class codes loaded",
    ingestion_audit_meta: "Metadata Agent      → audit dates & submission count loaded",
    api_ingestion_node:   "API Ingestion       → payroll & policy config fetched from API",
    officer_agent:        "Officer Agent       → officer payroll classification checked",
    class_code_agent:     "Class Code Agent    → class code usage validated",
    frequency_agent:      "Frequency Agent     → submission frequency analysed",
    premium_agent:        "Premium Agent       → variance calculation complete",
    risk_assessor:        "Risk Assessor       → risk level & recommendation assigned",
    explanation_agent:    "Explanation Agent   → AI narrative generated",
    hitl_checkpoint:      "HITL Checkpoint     → paused for human review",
  };
 
  // ── Single-case watcher (unchanged logic) ───────────────────────
  const watchCase = useCallback((caseId) => {
    setAuditCaseId(caseId);
    setLogs([`[${new Date().toLocaleTimeString()}] 🚀 Workflow started — Case #${caseId}`]);
    if (stopPollRef.current) stopPollRef.current();
    const loggedAgents = new Set();
 
    stopPollRef.current = pollAuditStatus(caseId, (s) => {
      setStatus(s);
      const ts = new Date().toLocaleTimeString();
      const newAgentSt = {};
      (s.agent_logs || []).forEach(log => {
        if (!log.agent) return;
        newAgentSt[log.agent] = log.status === "error" ? "error" : "complete";
        if (!loggedAgents.has(log.agent)) {
          loggedAgents.add(log.agent);
          const label  = AGENT_LOG_LABELS[log.agent] ?? log.agent;
          const prefix = log.status === "error" ? "✗" : log.status === "skipped" ? "⏭" : "✓";
          setLogs(l => [...l, `[${ts}] ${prefix} ${label}`]);
        }
      });
      setAgentStatus(prev => ({...prev, ...newAgentSt}));
      if (s.status === "hitl_pending") {
        setLogs(l => [...l,
          `[${ts}] ⚠️  HITL required — case paused for human review`,
          `[${ts}]    Risk: ${s.risk_level?.toUpperCase()}, Variance: ${Number(s.variance_pct || 0).toFixed(2)}%`,
        ]);
        onCaseCreated?.();
      }
      if (s.status === "completed") {
        setLogs(l => [...l,
          `[${ts}] 🎉 Audit complete`,
          `[${ts}]    Variance: ${Number(s.variance_pct || 0).toFixed(2)}%  |  Risk: ${s.risk_level}  |  Rec: ${s.recommendation}`,
        ]);
        onCaseCreated?.();
        stopPollRef.current?.();
      }
      if (s.status === "rejected") { setLogs(l => [...l, `[${ts}] ✗ Audit rejected`]); stopPollRef.current?.(); }
      if (s.status === "error")    { setLogs(l => [...l, `[${ts}] ✗ Error: ${s.errors}`]); stopPollRef.current?.(); }
    });
  }, [onCaseCreated]);
 
  // ── Batch: start polling each case ID ───────────────────────────
  useEffect(() => {
    if (!isBatchMode || batchCaseIds.length === 0) return;
    setBatchQueue(batchCaseIds);
    setBatchStatuses({});
    setHitlQueuedIds([]);
    setActiveHITLCase(null);
 
    // Clear any previous batch polls
    Object.values(batchPollsRef.current).forEach(stop => stop?.());
    batchPollsRef.current = {};
 
    batchCaseIds.forEach(caseId => {
      const stop = pollAuditStatus(caseId, (s) => {
        setBatchStatuses(prev => ({ ...prev, [caseId]: s }));
        onCaseCreated?.();
 
        if (s.status === "hitl_pending") {
          setHitlQueuedIds(prev =>
            prev.includes(caseId) ? prev : [...prev, caseId]
          );
          // Show the first waiting HITL case immediately
          setActiveHITLCase(cur => cur ?? caseId);
        }
 
        if (["completed", "rejected", "error"].includes(s.status)) {
          // Stop polling this case
          batchPollsRef.current[caseId]?.();
          delete batchPollsRef.current[caseId];
 
          // Remove from HITL queue if it was there
          setHitlQueuedIds(prev => {
            const next = prev.filter(id => id !== caseId);
            return next;
          });
 
          // If this was the active HITL case, advance to the next
          setActiveHITLCase(cur => {
            if (cur === caseId) {
              const remaining = hitlQueuedIds.filter(id => id !== caseId);
              return remaining[0] ?? null;
            }
            return cur;
          });
        }
      });
      batchPollsRef.current[caseId] = stop;
    });
 
    return () => {
      Object.values(batchPollsRef.current).forEach(stop => stop?.());
      batchPollsRef.current = {};
    };
  }, [JSON.stringify(batchCaseIds)]); // eslint-disable-line react-hooks/exhaustive-deps
 
  // Advance activeHITLCase whenever hitlQueuedIds changes
  useEffect(() => {
    if (!activeHITLCase && hitlQueuedIds.length > 0) {
      setActiveHITLCase(hitlQueuedIds[0]);
    }
  }, [hitlQueuedIds, activeHITLCase]);
 
  // ── Cleanup on unmount ──────────────────────────────────────────
  useEffect(() => {
    return () => {
      stopPollRef.current?.();
      Object.values(batchPollsRef.current).forEach(stop => stop?.());
    };
  }, []);
 
  useEffect(() => {
    if (propCaseId && propCaseId !== auditCaseId) watchCase(propCaseId);
  }, [propCaseId]); // eslint-disable-line react-hooks/exhaustive-deps
 
  useEffect(() => {
    if (propCaseId || isBatchMode) return;
    const active = cases.find(c => ["running","pending","hitl_pending"].includes(c.status));
    if (active && active.audit_case_id !== auditCaseId) watchCase(active.audit_case_id);
  }, [cases]); // eslint-disable-line react-hooks/exhaustive-deps
 
  const agentLabels = [
    { keys:["ingestion_excel","ingestion_audit_meta","api_ingestion_node"], label:"Ingestion Agent",   sub:"Payroll + audit metadata" },
    { keys:["ingestion_xml"],                          label:"Policy Parser",     sub:"XML class codes & rates" },
    { keys:["officer_agent"],                          label:"Officer Agent",     sub:"Officer classification" },
    { keys:["class_code_agent"],                       label:"Class Code Agent",  sub:"Class code validation" },
    { keys:["frequency_agent"],                        label:"Frequency Agent",   sub:"Submission frequency" },
    { keys:["premium_agent","risk_assessor"],          label:"Premium Agent",     sub:"Variance & risk scoring" },
    { keys:["explanation_agent"],                      label:"Explanation Agent", sub:"AI narrative" },
  ];
 
  const resolveStepStatus = (keys) => {
    let anyError = false, doneCount = 0;
    for (const k of keys) {
      if (agentStatus[k] === "error")    anyError = true;
      if (agentStatus[k] === "complete") doneCount++;
    }
    if (anyError)                  return "error";
    if (doneCount === keys.length) return "complete";
    if (doneCount > 0)             return "partial";
    return "pending";
  };
 
  // ── Batch summary helpers ────────────────────────────────────────
  const batchDone      = Object.values(batchStatuses).filter(s => s.status === "completed").length;
  const batchRejected  = Object.values(batchStatuses).filter(s => s.status === "rejected").length;
  const batchError_cnt = Object.values(batchStatuses).filter(s => s.status === "error").length;
  const batchRunning   = Object.values(batchStatuses).filter(s => ["pending","processing","running"].includes(s.status)).length;
  const batchHITL      = hitlQueuedIds.length;
 
  const activeHITLStatus = activeHITLCase ? batchStatuses[activeHITLCase] : null;
 
  // ── HITL decision handler for batch mode ────────────────────────
  const handleBatchHITL = async (decision, note) => {
    if (!activeHITLCase) return;
    try {
      await submitHITLDecision(activeHITLCase, { decision, notes: note });
      const fresh = await getAuditStatus(activeHITLCase);
      setBatchStatuses(prev => ({ ...prev, [activeHITLCase]: fresh }));
      onCaseCreated?.();
 
      // Remove from HITL queue and advance
      setHitlQueuedIds(prev => {
        const next = prev.filter(id => id !== activeHITLCase);
        setActiveHITLCase(next[0] ?? null);
        return next;
      });
    } catch (err) {
      alert("HITL submission failed: " + (err.response?.data?.detail || err.message));
    }
  };
 
  // ════════════════════════════════════════════════════════════════
  // RENDER
  // ════════════════════════════════════════════════════════════════
  return (
    <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
 
      {/* Header card */}
      <div style={{ background:`linear-gradient(135deg, ${C.navy} 0%, ${C.navyLt} 100%)`,
        borderRadius:14, padding:28, color:"#fff" }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
          <div>
            <h2 style={{ margin:"0 0 6px", fontSize:22, fontWeight:800 }}>🤖 AI Audit Engine</h2>
            <p style={{ margin:0, opacity:0.7, fontSize:14 }}>
              LangGraph-powered multi-agent orchestration for automated earned exposure &amp; premium variance detection
            </p>
          </div>
          {/* Single-case badge */}
          {!isBatchMode && auditCaseId && (
            <div style={{ textAlign:"right" }}>
              <div style={{ fontSize:12, opacity:0.6, marginBottom:4 }}>Monitoring Case</div>
              <div style={{ fontSize:22, fontWeight:800 }}>#{auditCaseId}</div>
              {status && <StatusBadge status={status.status} />}
            </div>
          )}
          {/* Batch badge */}
          {isBatchMode && (
            <div style={{ textAlign:"right", minWidth:160 }}>
              <div style={{ fontSize:12, opacity:0.6, marginBottom:4 }}>Batch Mode</div>
              <div style={{ fontSize:22, fontWeight:800 }}>{batchCaseIds.length} policies</div>
              <div style={{ fontSize:12, opacity:0.6, marginTop:4 }}>
                ✅ {batchDone} done · ⚠️ {batchHITL} HITL · ⚙️ {batchRunning} running
              </div>
            </div>
          )}
        </div>
        {!auditCaseId && !isBatchMode && (
          <div style={{ marginTop:16, padding:"12px 16px", background:"rgba(255,255,255,0.07)",
            borderRadius:10, fontSize:13, opacity:0.8 }}>
            Upload files in <strong>Data Upload</strong> to run an audit. The AI pipeline will
            automatically appear here once started.
          </div>
        )}
      </div>
 
      {/* ══════════════════════════════════════
          BATCH MODE: KPI bar + HITL queue
      ══════════════════════════════════════ */}
      {isBatchMode && (
        <>
          {/* Batch progress KPIs */}
          <div style={{ display:"flex", gap:14 }}>
            <KpiCard label="Total Queued"   value={batchCaseIds.length}  sub="From API batch"          accent={C.accent} />
            <KpiCard label="Completed"      value={batchDone}            sub="Fully audited"           accent={C.green}  />
            <KpiCard label="HITL Pending"   value={batchHITL}            sub="Awaiting your review"    accent={C.amber}  />
            <KpiCard label="Running"        value={batchRunning}         sub="In pipeline"             accent={C.purple} />
            {(batchRejected + batchError_cnt) > 0 && (
              <KpiCard label="Issues"       value={batchRejected + batchError_cnt} sub="Rejected / Error" accent={C.red} />
            )}
          </div>
 
          {/* HITL review queue banner */}
          {hitlQueuedIds.length > 0 && (
            <div style={{ background:"linear-gradient(135deg, #FEF3C7, #FDE68A)",
              border:`1px solid ${C.amber}`, borderRadius:12, padding:"14px 20px",
              display:"flex", alignItems:"center", gap:14 }}>
              <span style={{ fontSize:28 }}>⚠️</span>
              <div style={{ flex:1 }}>
                <div style={{ fontSize:14, fontWeight:800, color:"#78350F" }}>
                  {hitlQueuedIds.length} policy(ies) require human review
                </div>
                <div style={{ fontSize:12, color:"#92400E", marginTop:2 }}>
                  Reviewing case #{activeHITLCase} now
                  {hitlQueuedIds.length > 1
                    ? ` · ${hitlQueuedIds.length - 1} more in queue after this`
                    : ""}
                </div>
              </div>
              {/* Queue pills */}
              <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
                {hitlQueuedIds.map((id, i) => (
                  <button key={id} onClick={() => setActiveHITLCase(id)}
                    style={{ background: id === activeHITLCase ? C.amber : "rgba(0,0,0,0.1)",
                      color: id === activeHITLCase ? "#fff" : "#78350F",
                      border:"none", borderRadius:20, padding:"4px 12px",
                      fontSize:12, fontWeight:700, cursor:"pointer" }}>
                    #{id}{i === 0 && id === activeHITLCase ? " ← now" : ""}
                  </button>
                ))}
              </div>
            </div>
          )}
 
          {/* Active HITL panel */}
          {activeHITLCase && activeHITLStatus && (
            <div style={{ background:C.card, border:`2px solid ${C.amber}`, borderRadius:14, padding:24 }}>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
                <div>
                  <div style={{ fontSize:16, fontWeight:800, color:C.text }}>
                    Reviewing: {activeHITLStatus.policy_number} — Case #{activeHITLCase}
                  </div>
                  <div style={{ fontSize:12, color:C.muted, marginTop:2 }}>
                    Risk: <strong style={{ color:C.red }}>{activeHITLStatus.risk_level?.toUpperCase()}</strong>
                    &nbsp;·&nbsp;Variance: <strong>{Number(activeHITLStatus.variance_pct || 0).toFixed(2)}%</strong>
                    &nbsp;·&nbsp;Rec: <strong>{activeHITLStatus.recommendation?.replace(/_/g," ")}</strong>
                  </div>
                </div>
                <div style={{ display:"flex", gap:8 }}>
                  <RiskBadge risk={activeHITLStatus.risk_level} />
                  <StatusBadge status={activeHITLStatus.status} />
                </div>
              </div>
              <ResultsAndHITLPanel
                status={activeHITLStatus}
                onApprove={handleBatchHITL}
              />
            </div>
          )}
 
          {/* Batch policy status grid — card / table toggle */}
          <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>

            {/* Header row with toggle */}
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:18 }}>
              <div>
                <h2 style={{ margin:0, fontSize:18, fontWeight:700, color:C.text }}>
                  Batch Policy Progress
                </h2>
                <p style={{ margin:"4px 0 0", fontSize:13, color:C.muted }}>
                  All policies queued in this API batch — click a HITL case to review it
                </p>
              </div>

              {/* View toggle pill */}
              <div style={{ display:"flex", background:C.bg, border:`1px solid ${C.border}`,
                borderRadius:10, overflow:"hidden", flexShrink:0 }}>
                {[
                  { key:"card",  icon:"⊞", label:"Cards"  },
                  { key:"table", icon:"☰", label:"Table"  },
                ].map(({ key, icon, label }) => (
                  <button key={key} onClick={() => setBatchView(key)}
                    style={{
                      display:"flex", alignItems:"center", gap:6,
                      padding:"7px 16px", border:"none", cursor:"pointer",
                      fontWeight:700, fontSize:12,
                      background: batchView === key
                        ? `linear-gradient(135deg, ${C.accent}, ${C.teal})`
                        : "transparent",
                      color: batchView === key ? "#fff" : C.muted,
                      transition:"all 0.15s",
                    }}>
                    <span style={{ fontSize:14 }}>{icon}</span>
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* ── CARD VIEW ── */}
            {batchView === "card" && (
              <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(260px, 1fr))", gap:10 }}>
                {batchCaseIds.map(caseId => {
                  const s        = batchStatuses[caseId];
                  const isHITL   = hitlQueuedIds.includes(caseId);
                  const isActive = caseId === activeHITLCase;
                  const varPct   = s?.variance_pct != null ? Number(s.variance_pct) : null;
                  const varColor = varPct == null ? C.muted
                                 : Math.abs(varPct) > 20 ? C.red
                                 : Math.abs(varPct) > 10 ? C.amber : C.green;
                  return (
                    <div key={caseId}
                      onClick={() => isHITL && setActiveHITLCase(caseId)}
                      style={{
                        background: isActive ? "#FFFBEB" : isHITL ? "#FFFDE7" : C.bg,
                        border: isActive ? `2px solid ${C.amber}`
                               : isHITL  ? `1px solid ${C.amber}`
                               : `1px solid ${C.border}`,
                        borderRadius:10, padding:"14px 16px",
                        cursor:isHITL ? "pointer" : "default",
                        transition:"all 0.15s", position:"relative",
                      }}
                      onMouseEnter={e => { if (!isHITL) e.currentTarget.style.background = "#F5F8FF"; }}
                      onMouseLeave={e => {
                        e.currentTarget.style.background =
                          isActive ? "#FFFBEB" : isHITL ? "#FFFDE7" : C.bg;
                      }}>

                      {/* Policy number + status */}
                      <div style={{ display:"flex", justifyContent:"space-between",
                        alignItems:"center", marginBottom:6 }}>
                        <div style={{ fontSize:13, fontWeight:800, color:C.accent }}>
                          {s?.policy_number || `Case #${caseId}`}
                        </div>
                        <StatusBadge status={s?.status || "pending"} />
                      </div>

                      {/* Case ID + risk */}
                      <div style={{ display:"flex", justifyContent:"space-between",
                        alignItems:"center", marginBottom:4 }}>
                        <div style={{ fontSize:11, color:C.muted }}>Case #{caseId}</div>
                        {s?.risk_level && <RiskBadge risk={s.risk_level} />}
                      </div>

                      {/* Variance bar */}
                      {varPct != null && (
                        <div style={{ marginTop:8 }}>
                          <div style={{ display:"flex", justifyContent:"space-between",
                            fontSize:11, color:C.muted, marginBottom:3 }}>
                            <span>Variance</span>
                            <span style={{ fontWeight:700, color:varColor }}>
                              {varPct > 0 ? "+" : ""}{varPct.toFixed(1)}%
                            </span>
                          </div>
                          <div style={{ background:C.border, borderRadius:4, height:4, overflow:"hidden" }}>
                            <div style={{
                              width:`${Math.min(Math.abs(varPct) * 2.5, 100)}%`,
                              height:"100%", background:varColor,
                              borderRadius:4, transition:"width 0.4s",
                            }} />
                          </div>
                        </div>
                      )}

                      {/* HITL indicator */}
                      {isHITL && (
                        <div style={{ marginTop:8, fontSize:11, fontWeight:700, color:C.amber,
                          display:"flex", alignItems:"center", gap:4 }}>
                          ⚠️ {isActive ? "Reviewing now" : "Click to review"}
                        </div>
                      )}

                      {/* Earned premium */}
                      {/* {s?.overall_variance?.earned_premium != null && (
                        <div style={{ marginTop:6, fontSize:11, color:C.muted }}>
                          Premium: <strong style={{ color:C.text }}>
                            {money(Math.round(s.overall_variance.earned_premium))}
                          </strong>
                        </div>
                      )} */}
                      {(() => {
                        const ov       = s?.overall_variance || {};
                        const isPend   = ["pending","processing","running"].includes(s?.status);
                        const premium  = isPend
                          ? (ov.earned_premium  || ov.est_ytd_premium || 0)
                          : (ov.earned_premium  || ov.est_ytd_premium || 0);
                        const label    = (isPend && !ov.earned_premium && ov.est_ytd_premium)
                          ? "Est. Premium"
                          : "Premium";
                        if (!premium) return null;
                        return (
                          <div style={{ marginTop:6, fontSize:11, color:C.muted }}>
                            {label}: <strong style={{ color:C.text }}>
                              {money(Math.round(premium))}
                            </strong>
                          </div>
                        );
                      })()}
                    </div>
                  );
                })}
              </div>
            )}

            {/* ── TABLE VIEW ── */}
            {batchView === "table" && (
              <div style={{ overflowX:"auto" }}>
                <table style={{ width:"100%", borderCollapse:"collapse" }}>
                  <thead>
                    <tr style={{ borderBottom:`2px solid ${C.border}`, background:"#F8FAFD" }}>
                      {["#","Policy Number","Case ID","Status","Risk","Variance %",
                        "Earned Premium","Recommendation","Action"].map(h => (
                        <th key={h} style={{ textAlign:"left", padding:"10px 14px", fontSize:11,
                          fontWeight:700, color:C.muted, textTransform:"uppercase",
                          letterSpacing:0.7, whiteSpace:"nowrap" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {batchCaseIds.map((caseId, idx) => {
                      const s        = batchStatuses[caseId];
                      const isHITL   = hitlQueuedIds.includes(caseId);
                      const isActive = caseId === activeHITLCase;
                      const varPct   = s?.variance_pct != null ? Number(s.variance_pct) : null;
                      const varColor = varPct == null ? C.muted
                                     : Math.abs(varPct) > 20 ? C.red
                                     : Math.abs(varPct) > 10 ? C.amber : C.green;
                      const rowBg    = isActive ? "#FFFBEB" : isHITL ? "#FFFDE7" : "transparent";
                      return (
                        <tr key={caseId}
                          onClick={() => isHITL && setActiveHITLCase(caseId)}
                          style={{
                            borderBottom:`1px solid ${C.border}`,
                            background:rowBg,
                            cursor:isHITL ? "pointer" : "default",
                            transition:"background 0.15s",
                          }}
                          onMouseEnter={e => {
                            if (!isHITL && !isActive) e.currentTarget.style.background = "#F5F8FF";
                          }}
                          onMouseLeave={e => {
                            e.currentTarget.style.background = rowBg;
                          }}>

                          {/* # */}
                          <td style={{ padding:"12px 14px", fontSize:12, color:C.muted,
                            fontWeight:600 }}>{idx + 1}</td>

                          {/* Policy Number */}
                          <td style={{ padding:"12px 14px", fontSize:13, fontWeight:800,
                            color:C.accent }}>
                            {s?.policy_number || "—"}
                            {isHITL && (
                              <span style={{ marginLeft:6, fontSize:10, fontWeight:700,
                                color:C.amber }}>
                                ⚠️ {isActive ? "reviewing" : "HITL"}
                              </span>
                            )}
                          </td>

                          {/* Case ID */}
                          <td style={{ padding:"12px 14px", fontSize:12, color:C.muted }}>
                            #{caseId}
                          </td>

                          {/* Status */}
                          <td style={{ padding:"12px 14px" }}>
                            <StatusBadge status={s?.status || "pending"} />
                          </td>

                          {/* Risk */}
                          <td style={{ padding:"12px 14px" }}>
                            {s?.risk_level ? <RiskBadge risk={s.risk_level} /> : <span style={{ color:C.muted }}>—</span>}
                          </td>

                          {/* Variance % with mini bar */}
                          <td style={{ padding:"12px 14px", minWidth:110 }}>
                            {varPct != null ? (
                              <div>
                                <div style={{ fontWeight:700, fontSize:13, color:varColor, marginBottom:3 }}>
                                  {varPct > 0 ? "+" : ""}{varPct.toFixed(1)}%
                                </div>
                                <div style={{ background:C.border, borderRadius:4, height:4, width:80 }}>
                                  <div style={{
                                    width:`${Math.min(Math.abs(varPct) * 2.5, 100)}%`,
                                    height:"100%", background:varColor, borderRadius:4,
                                  }} />
                                </div>
                              </div>
                            ) : <span style={{ color:C.muted }}>—</span>}
                          </td>

                          {/* Earned Premium */}
                          {/* <td style={{ padding:"12px 14px", fontSize:13, fontWeight:600,
                            color:C.text }}>
                            {s?.overall_variance?.earned_premium != null
                              ? money(Math.round(s.overall_variance.earned_premium))
                              : "—"}
                          </td> */}

                          <td style={{ padding:"12px 14px", fontSize:13, fontWeight:600,
                            color:C.text }}>
                            {(() => {
                              const ov      = s?.overall_variance || {};
                              const premium = ov.earned_premium || ov.est_ytd_premium || 0;
                              return premium ? money(Math.round(premium)) : "—";
                            })()}
                          </td>

                          {/* Recommendation */}
                          <td style={{ padding:"12px 14px", fontSize:12, color:C.muted }}>
                            {s?.recommendation
                              ? s.recommendation.replace(/_/g, " ")
                              : "—"}
                          </td>

                          {/* Action */}
                          <td style={{ padding:"12px 14px" }}>
                            {isHITL ? (
                              <button
                                onClick={e => { e.stopPropagation(); setActiveHITLCase(caseId); }}
                                style={{ background:C.amber, color:"#fff", border:"none",
                                  borderRadius:6, padding:"5px 12px", fontSize:11,
                                  fontWeight:700, cursor:"pointer", whiteSpace:"nowrap" }}>
                                Review ▲
                              </button>
                            ) : (
                              <span style={{ fontSize:12, color:C.muted }}>—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>

                {batchCaseIds.length === 0 && (
                  <div style={{ textAlign:"center", padding:40, color:C.muted, fontSize:14 }}>
                    No policies in this batch yet.
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
 
      {/* ══════════════════════════════════════
          SINGLE-CASE MODE (original layout)
      ══════════════════════════════════════ */}
      {!isBatchMode && (
        <div style={{ display:"flex", gap:16 }}>
          {/* Agent Pipeline */}
          <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24, flex:1 }}>
            <SectionHeader title="Agent Pipeline Status" sub="Real-time LangGraph orchestration" />
            <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
              {agentLabels.map((a, i) => {
                const st        = resolveStepStatus(a.keys);
                const bgColor   = st === "complete" ? "#F0FDF4" : st === "error" ? "#FEF2F2" : st === "partial" ? "#EEF2FF" : C.bg;
                const bdColor   = st === "complete" ? C.green   : st === "error" ? C.red     : st === "partial" ? C.accent  : C.border;
                const circleClr = st === "complete" ? C.green   : st === "error" ? C.red     : st === "partial" ? C.accent  : C.border;
                const badge     = st === "complete" ? { bg:"#DCFCE7", color:C.green,  text:"Done" }
                                : st === "error"    ? { bg:"#FEE2E2", color:C.red,    text:"Error" }
                                : st === "partial"  ? { bg:"#DBEAFE", color:C.accent, text:"Running" }
                                :                    { bg:"#F3F4F6", color:C.muted,   text:"Pending" };
                const subText   = st === "complete" ? a.sub
                                : st === "error"    ? "Error encountered"
                                : st === "partial"  ? "Processing…" : "Waiting…";
                return (
                  <div key={a.keys.join()} style={{ display:"flex", alignItems:"center", gap:14,
                    padding:"12px 16px", borderRadius:10, transition:"all 0.3s",
                    background:bgColor, border:`1px solid ${bdColor}` }}>
                    <div style={{ width:32, height:32, borderRadius:"50%", flexShrink:0,
                      display:"flex", alignItems:"center", justifyContent:"center", fontSize:14,
                      background:circleClr, color: st === "pending" ? C.muted : "#fff" }}>
                      {st === "complete" ? "✓" : st === "error" ? "✗" : st === "partial" ? "⚙" : i + 1}
                    </div>
                    <div style={{ flex:1 }}>
                      <div style={{ fontSize:13, fontWeight:700, color:C.text }}>{a.label}</div>
                      <div style={{ fontSize:11, color:C.muted }}>{subText}</div>
                    </div>
                    <span style={{ fontSize:11, fontWeight:600, padding:"3px 10px", borderRadius:20,
                      background:badge.bg, color:badge.color }}>{badge.text}</span>
                  </div>
                );
              })}
            </div>
          </div>
 
          {/* Live log + results */}
          <div style={{ flex:1, display:"flex", flexDirection:"column", gap:16 }}>
            <div style={{ background:C.navy, borderRadius:14, padding:20, flex:1, minHeight:300 }}>
              <div style={{ fontSize:13, fontWeight:700, color:"#64B5F6", marginBottom:12,
                fontFamily:"monospace" }}>▶ AUDIT LOG</div>
              <div style={{ fontFamily:"'Courier New', monospace", fontSize:11.5, color:"#A8D8A8",
                lineHeight:1.8, overflowY:"auto", maxHeight:280 }}>
                {logs.length === 0
                  ? <span style={{ color:"#546E7A" }}>// Upload files then start an audit to see live output</span>
                  : logs.map((l, i) => <div key={i}>{l}</div>)}
              </div>
            </div>
 
            {status && ["completed","hitl_pending"].includes(status.status) && (
              <ResultsAndHITLPanel status={status} onApprove={async (decision, note) => {
                try {
                  await submitHITLDecision(status.audit_case_id, { decision, notes: note });
                  const fresh = await getAuditStatus(status.audit_case_id);
                  setStatus(fresh);
                  onCaseCreated?.();
                  const ts = new Date().toLocaleTimeString();
                  setLogs(l => [...l, `[${ts}] ✓ HITL decision submitted: ${decision}`]);
                } catch (err) {
                  alert("HITL submission failed: " + (err.response?.data?.detail || err.message));
                }
              }} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
 
// ── Audit Detail ──────────────────────────────────────────────────────────────
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
 
    // ── Single fetch on mount only — no polling. ─────────────────────────────
    // The AI Audit screen handles live progress while a job runs.
    // This Review screen is read-only; it loads the full record once, then stops.
    // The only subsequent requests are explicit user actions:
    //   • HITL approve / reject  (handleHITL → POST + GET)
    //   • Narrative save         (future endpoint → POST + GET)
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
 
  // Derived fields for detail view
  const exposureDelta = (ov.est_exposure || 0) - (ov.earned_exposure || 0);
  const classCodes    = [...new Set((detail.class_code_variance || []).map(r => r.ClassCode))].join(", ") || "—";
 
  // Payroll calendar helpers
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
            // EE Officers on Payroll — "X of Y correctly assigned"
            const officerTotal   = detail.officer_count;
            const officerIssues  = detail.officer_issues_count ?? 0;
            const officerDisplay = officerTotal != null
              ? `${officerTotal - officerIssues} of ${officerTotal} correctly assigned`
              : "—";
 
            // Actual Payroll Submissions — "X of Y expected"
            const actualSubs    = detail.submitted_count;
            const expectedSubs  = detail.expected_submissions;
            const actualDisplay = actualSubs != null
              ? expectedSubs != null
                ? `${actualSubs} of ${expectedSubs} expected`
                : String(actualSubs)
              : "—";
 
            // Format last check date: "2026-02-20" or "02/20/2026" → "Feb 20, 2026"
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
              <div style={{
  background: C.card,
  border: `1px solid ${C.border}`,
  borderRadius: 14,
  padding: 24
}}>
  <SectionHeader
    title="Variance by Class Code"
    sub="Positive = Additional Premium | Negative = Refund"
  />

  <ResponsiveContainer width="100%" height={220}>
    <BarChart data={chartData}>
      <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
      
      <XAxis dataKey="code" />
      <YAxis />
      
      <Tooltip
        formatter={(value) => `$${value.toLocaleString()}`}
      />

      <Bar
        dataKey="variance"
        name="Variance"
        radius={[4,4,0,0]}
      >
        {chartData.map((entry, index) => (
          <Cell
            key={`cell-${index}`}
            fill={entry.variance > 0 ? C.red : C.green}
          />
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
              {canApproveHITL &&(<div style={{ display:"flex", gap:8 }}>
                <button style={{ background:C.green, color:"#fff", border:"none", borderRadius:8,
                  padding:"8px 20px", fontSize:13, fontWeight:700, cursor:"pointer" }}>
                  ✓ Approve Narrative
                </button>
                <button style={{ background:C.amber, color:"#fff", border:"none", borderRadius:8,
                  padding:"8px 20px", fontSize:13, fontWeight:700, cursor:"pointer" }}>
                  ✎ Edit &amp; Override
                </button>
              </div>)}
            </div>
          )}
 
          {/* ── Decision tab ── */}
          {tab === "decision" && (
            <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
 
              {/* 3 option cards */}
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
                      borderRadius:12, padding:20, textAlign:"left",
                      transition:"all 0.15s" }}
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
 
                {detail.hitl_required && (canApproveHITL

                 ? (
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
 
 
// // ── Data Upload ───────────────────────────────────────────────────────────────
// function DataUpload({ onAuditStarted }) {
//   const [payrollFile,  setPayrollFile]  = useState(null);
//   const [policyFile,   setPolicyFile]   = useState(null);
//   const [metaFile,     setMetaFile]     = useState(null);
//   const [policyNumber, setPolicyNumber] = useState("");
//   const [dragging,     setDragging]     = useState(null);
//   const [uploading,    setUploading]    = useState(false);
//   const [uploadResult, setUploadResult] = useState(null);
//   const [starting,     setStarting]     = useState(false);
//   const [started,      setStarted]      = useState(null);
//   const [error,        setError]        = useState(null);
 
//   const allReady = payrollFile && policyFile && metaFile && policyNumber.trim();
 
//   const handleUpload = async () => {
//     if (!allReady) return;
//     setUploading(true); setError(null);
//     try {
//       const result = await uploadAuditFiles(payrollFile, policyFile, metaFile);
//       setUploadResult(result);
//     } catch (err) {
//       setError(err.response?.data?.detail || err.message);
//     } finally {
//       setUploading(false);
//     }
//   };
 
//   const handleStart = async () => {
//     if (!uploadResult) return;
//     setStarting(true); setError(null);
//     try {
//       const result = await startAudit({
//         policy_number:        policyNumber.trim(),
//         payroll_file_path:    uploadResult.payroll_file_path,
//         policy_xml_path:      uploadResult.policy_xml_path,
//         audit_meta_file_path: uploadResult.audit_meta_file_path,
//       });
//       setStarted(result);
//       onAuditStarted?.(result.audit_case_id);
//     } catch (err) {
//       setError(err.response?.data?.detail || err.message);
//     } finally {
//       setStarting(false);
//     }
//   };
 
//   const FileDropZone = ({ label, file, setFile, accept, dragKey }) => (
//     <div
//       style={{ background:dragging === dragKey ? "#EEF2FF" : C.bg,
//         border:`2px dashed ${dragging === dragKey ? C.accent : C.border}`,
//         borderRadius:12, padding:"20px 24px", cursor:"pointer", transition:"all 0.2s",
//         display:"flex", alignItems:"center", gap:14 }}
//       onDragOver={e => { e.preventDefault(); setDragging(dragKey); }}
//       onDragLeave={() => setDragging(null)}
//       onDrop={e => { e.preventDefault(); setDragging(null); const f = e.dataTransfer.files[0]; if (f) setFile(f); }}
//       onClick={() => document.getElementById(`inp-${dragKey}`).click()}>
//       <span style={{ fontSize:28 }}>{file ? "✅" : "📂"}</span>
//       <div>
//         <div style={{ fontSize:13, fontWeight:700, color:C.text }}>{label}</div>
//         <div style={{ fontSize:12, color:C.muted }}>{file ? file.name : `Drop or click to select — ${accept}`}</div>
//       </div>
//       <input id={`inp-${dragKey}`} type="file" accept={accept} style={{ display:"none" }}
//         onChange={e => e.target.files[0] && setFile(e.target.files[0])} />
//     </div>
//   );
 
//   return (
//     <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
//       <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:28 }}>
//         <SectionHeader title="Run New Audit"
//           sub="Upload three source files, enter policy number, then start the AI pipeline" />
 
//         <div style={{ display:"flex", flexDirection:"column", gap:12, marginBottom:20 }}>
//           <FileDropZone label="Payroll Excel (.xlsx)"  file={payrollFile} setFile={setPayrollFile} accept=".xlsx" dragKey="payroll" />
//           <FileDropZone label="Policy XML (.xml)"      file={policyFile}  setFile={setPolicyFile}  accept=".xml"  dragKey="policy" />
//           <FileDropZone label="Audit Metadata (.xlsx)" file={metaFile}    setFile={setMetaFile}    accept=".xlsx" dragKey="meta" />
//         </div>
 
//         <div style={{ marginBottom:20 }}>
//           <label style={{ fontSize:12, fontWeight:700, color:C.muted, textTransform:"uppercase",
//             letterSpacing:0.8, display:"block", marginBottom:6 }}>Policy Number</label>
//           <input value={policyNumber} onChange={e => setPolicyNumber(e.target.value)}
//             placeholder="e.g. MWC0183363-05"
//             style={{ border:`1px solid ${C.border}`, borderRadius:8, padding:"10px 14px", fontSize:13,
//               width:"100%", outline:"none", color:C.text, boxSizing:"border-box", maxWidth:340 }} />
//         </div>
 
//         {error && (
//           <div style={{ padding:"10px 14px", background:"#FEE2E2", borderRadius:8,
//             border:`1px solid #FECACA`, fontSize:13, color:"#991B1B", marginBottom:16 }}>
//             ✗ {error}
//           </div>
//         )}
 
//         <div style={{ display:"flex", gap:12, alignItems:"center" }}>
//           {!uploadResult ? (
//             <button disabled={!allReady || uploading} onClick={handleUpload}
//               style={{ background:allReady ? C.accent : C.border, color:"#fff", border:"none",
//                 borderRadius:10, padding:"11px 28px", fontSize:14, fontWeight:700,
//                 cursor:allReady && !uploading ? "pointer" : "default",
//                 opacity:uploading ? 0.7 : 1 }}>
//               {uploading ? "⚙️ Uploading..." : "⬆ Upload Files"}
//             </button>
//           ) : !started ? (
//             <>
//               <div style={{ padding:"8px 16px", background:"#DCFCE7", borderRadius:8,
//                 fontSize:13, fontWeight:600, color:"#15803D" }}>
//                 ✓ Files uploaded — Session: {uploadResult.session_id}
//               </div>
//               <button disabled={starting} onClick={handleStart}
//                 style={{ background:C.green, color:"#fff", border:"none", borderRadius:10,
//                   padding:"11px 28px", fontSize:14, fontWeight:700,
//                   cursor:starting ? "default" : "pointer", opacity:starting ? 0.7 : 1 }}>
//                 {starting ? "⚙️ Starting..." : "▶ Start AI Audit"}
//               </button>
//             </>
//           ) : (
//             <div style={{ padding:"12px 20px", background:"#DCFCE7", borderRadius:10,
//               border:`1px solid #86EFAC`, fontSize:14, fontWeight:700, color:"#15803D" }}>
//               🚀 Audit started! Case #{started.audit_case_id} — Check AI Audit screen for live progress.
//             </div>
//           )}
//         </div>
//       </div>
 
//       <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
//         <SectionHeader title="How it works" sub="The 3-step audit pipeline" />
//         <div style={{ display:"flex", gap:16 }}>
//           {[
//             { n:"1", title:"Upload",  desc:"Drop payroll Excel, policy XML, and audit metadata. Files are securely processed.", icon:"📂" },
//             { n:"2", title:"Analyze", desc:"LangGraph multi-agent pipeline: Ingestion → Specialist agents → Premium calculation → AI narrative.", icon:"🤖" },
//             { n:"3", title:"Review",  desc:"Auditor reviews variance report, HITL decisions, and AI explanation. Download final report.", icon:"📊" },
//           ].map(s => (
//             <div key={s.n} style={{ flex:1, background:C.bg, borderRadius:12, padding:"18px 20px" }}>
//               <div style={{ width:32, height:32, borderRadius:"50%", background:C.accent,
//                 color:"#fff", display:"flex", alignItems:"center", justifyContent:"center",
//                 fontWeight:800, fontSize:14, marginBottom:12 }}>{s.n}</div>
//               <div style={{ fontSize:16 }}>{s.icon}</div>
//               <div style={{ fontSize:14, fontWeight:700, color:C.text, marginBottom:6 }}>{s.title}</div>
//               <div style={{ fontSize:12, color:C.muted, lineHeight:1.6 }}>{s.desc}</div>
//             </div>
//           ))}
//         </div>
//       </div>
//     </div>
//   );
// }



// function DataUpload({ onAuditStarted, onBatchStarted }) {
//   // ── File-upload state ────────────────────────────────────────────
//   const [payrollFile,  setPayrollFile]  = useState(null);
//   const [policyFile,   setPolicyFile]   = useState(null);
//   const [metaFile,     setMetaFile]     = useState(null);
//   const [policyNumber, setPolicyNumber] = useState("");
//   const [dragging,     setDragging]     = useState(null);
//   const [uploading,    setUploading]    = useState(false);
//   const [uploadResult, setUploadResult] = useState(null);
//   const [starting,     setStarting]     = useState(false);
//   const [started,      setStarted]      = useState(null);
//   const [error,        setError]        = useState(null);
 
//   // ── Batch-API state ──────────────────────────────────────────────
//   const [apiMode,        setApiMode]        = useState(false);   // toggles the tab
//   const [fetchingAPI,    setFetchingAPI]     = useState(false);
//   const [batchResult,    setBatchResult]     = useState(null);   // API response
//   const [batchError,     setBatchError]      = useState(null);
 
//   const allReady = payrollFile && policyFile && metaFile && policyNumber.trim();
 
//   // ── File upload handlers (unchanged) ────────────────────────────
//   const handleUpload = async () => {
//     if (!allReady) return;
//     setUploading(true); setError(null);
//     try {
//       const result = await uploadAuditFiles(payrollFile, policyFile, metaFile);
//       setUploadResult(result);
//     } catch (err) {
//       setError(err.response?.data?.detail || err.message);
//     } finally {
//       setUploading(false);
//     }
//   };
 
//   const handleStart = async () => {
//     if (!uploadResult) return;
//     setStarting(true); setError(null);
//     try {
//       const result = await startAudit({
//         policy_number:        policyNumber.trim(),
//         payroll_file_path:    uploadResult.payroll_file_path,
//         policy_xml_path:      uploadResult.policy_xml_path,
//         audit_meta_file_path: uploadResult.audit_meta_file_path,
//       });
//       setStarted(result);
//       onAuditStarted?.(result.audit_case_id);
//     } catch (err) {
//       setError(err.response?.data?.detail || err.message);
//     } finally {
//       setStarting(false);
//     }
//   };
 
//   // ── Batch API handler ────────────────────────────────────────────
//   const handleFetchFromAPI = async () => {
//     setFetchingAPI(true); setBatchError(null); setBatchResult(null);
//     try {
//       const result = await startBatchAuditFromAPI(); // no args → fetch all policies
//       setBatchResult(result);
//       onBatchStarted?.(result.cases.map(c => c.audit_case_id));
//     } catch (err) {
//       setBatchError(err.response?.data?.detail || err.message);
//     } finally {
//       setFetchingAPI(false);
//     }
//   };
 
//   const FileDropZone = ({ label, file, setFile, accept, dragKey }) => (
//     <div
//       style={{ background:dragging === dragKey ? "#EEF2FF" : C.bg,
//         border:`2px dashed ${dragging === dragKey ? C.accent : C.border}`,
//         borderRadius:12, padding:"20px 24px", cursor:"pointer", transition:"all 0.2s",
//         display:"flex", alignItems:"center", gap:14 }}
//       onDragOver={e => { e.preventDefault(); setDragging(dragKey); }}
//       onDragLeave={() => setDragging(null)}
//       onDrop={e => { e.preventDefault(); setDragging(null); const f = e.dataTransfer.files[0]; if (f) setFile(f); }}
//       onClick={() => document.getElementById(`inp-${dragKey}`).click()}>
//       <span style={{ fontSize:28 }}>{file ? "✅" : "📂"}</span>
//       <div>
//         <div style={{ fontSize:13, fontWeight:700, color:C.text }}>{label}</div>
//         <div style={{ fontSize:12, color:C.muted }}>{file ? file.name : `Drop or click to select — ${accept}`}</div>
//       </div>
//       <input id={`inp-${dragKey}`} type="file" accept={accept} style={{ display:"none" }}
//         onChange={e => e.target.files[0] && setFile(e.target.files[0])} />
//     </div>
//   );
 
//   return (
//     <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
 
//       {/* ── Source selector tabs ──────────────────────────────────── */}
//       <div style={{ display:"flex", gap:0, background:C.bg, borderRadius:12,
//         border:`1px solid ${C.border}`, overflow:"hidden", alignSelf:"flex-start" }}>
//         {[
//           { key:false, label:"📂  File Upload",  desc:"Upload Excel & XML files" },
//           { key:true,  label:"🔌  Fetch from API", desc:"Pull all policies from Mock API" },
//         ].map(tab => (
//           <button key={String(tab.key)} onClick={() => setApiMode(tab.key)}
//             style={{ padding:"12px 28px", border:"none", cursor:"pointer",
//               background: apiMode === tab.key
//                 ? `linear-gradient(135deg, ${C.accent}, ${C.teal})`
//                 : "transparent",
//               color: apiMode === tab.key ? "#fff" : C.muted,
//               fontWeight:700, fontSize:13, transition:"all 0.2s",
//               borderRight:`1px solid ${C.border}` }}>
//             {tab.label}
//           </button>
//         ))}
//       </div>
 
//       {/* ══════════════════════════════════════════════════════════════
//           FILE UPLOAD TAB  (original UI, unchanged)
//       ══════════════════════════════════════════════════════════════ */}
//       {!apiMode && (
//         <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:28 }}>
//           <SectionHeader title="Run New Audit"
//             sub="Upload three source files, enter policy number, then start the AI pipeline" />
 
//           <div style={{ display:"flex", flexDirection:"column", gap:12, marginBottom:20 }}>
//             <FileDropZone label="Payroll Excel (.xlsx)"  file={payrollFile} setFile={setPayrollFile} accept=".xlsx" dragKey="payroll" />
//             <FileDropZone label="Policy XML (.xml)"      file={policyFile}  setFile={setPolicyFile}  accept=".xml"  dragKey="policy" />
//             <FileDropZone label="Audit Metadata (.xlsx)" file={metaFile}    setFile={setMetaFile}    accept=".xlsx" dragKey="meta" />
//           </div>
 
//           <div style={{ marginBottom:20 }}>
//             <label style={{ fontSize:12, fontWeight:700, color:C.muted, textTransform:"uppercase",
//               letterSpacing:0.8, display:"block", marginBottom:6 }}>Policy Number</label>
//             <input value={policyNumber} onChange={e => setPolicyNumber(e.target.value)}
//               placeholder="e.g. MWC0183363-05"
//               style={{ border:`1px solid ${C.border}`, borderRadius:8, padding:"10px 14px", fontSize:13,
//                 width:"100%", outline:"none", color:C.text, boxSizing:"border-box", maxWidth:340 }} />
//           </div>
 
//           {error && (
//             <div style={{ padding:"10px 14px", background:"#FEE2E2", borderRadius:8,
//               border:`1px solid #FECACA`, fontSize:13, color:"#991B1B", marginBottom:16 }}>
//               ✗ {error}
//             </div>
//           )}
 
//           <div style={{ display:"flex", gap:12, alignItems:"center" }}>
//             {!uploadResult ? (
//               <button disabled={!allReady || uploading} onClick={handleUpload}
//                 style={{ background:allReady ? C.accent : C.border, color:"#fff", border:"none",
//                   borderRadius:10, padding:"11px 28px", fontSize:14, fontWeight:700,
//                   cursor:allReady && !uploading ? "pointer" : "default",
//                   opacity:uploading ? 0.7 : 1 }}>
//                 {uploading ? "⚙️ Uploading..." : "⬆ Upload Files"}
//               </button>
//             ) : !started ? (
//               <>
//                 <div style={{ padding:"8px 16px", background:"#DCFCE7", borderRadius:8,
//                   fontSize:13, fontWeight:600, color:"#15803D" }}>
//                   ✓ Files uploaded — Session: {uploadResult.session_id}
//                 </div>
//                 <button disabled={starting} onClick={handleStart}
//                   style={{ background:C.green, color:"#fff", border:"none", borderRadius:10,
//                     padding:"11px 28px", fontSize:14, fontWeight:700,
//                     cursor:starting ? "default" : "pointer", opacity:starting ? 0.7 : 1 }}>
//                   {starting ? "⚙️ Starting..." : "▶ Start AI Audit"}
//                 </button>
//               </>
//             ) : (
//               <div style={{ padding:"12px 20px", background:"#DCFCE7", borderRadius:10,
//                 border:`1px solid #86EFAC`, fontSize:14, fontWeight:700, color:"#15803D" }}>
//                 🚀 Audit started! Case #{started.audit_case_id} — Check AI Audit screen for live progress.
//               </div>
//             )}
//           </div>
//         </div>
//       )}
 
//       {/* ══════════════════════════════════════════════════════════════
//           API FETCH TAB  (new)
//       ══════════════════════════════════════════════════════════════ */}
//       {apiMode && (
//         <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:28 }}>
//           <SectionHeader
//             title="Fetch All Policies from API"
//             sub="Pulls every available policy from the Mock API and queues them for audit. No file upload needed." />
 
//           {/* Info banner */}
//           <div style={{ display:"flex", gap:16, marginBottom:24 }}>
//             {[
//               { icon:"🔌", title:"Mock API Source",  desc:"Reads payroll, policy config, and audit metadata directly from the API" },
//               { icon:"⚡", title:"Batch Processing", desc:"All policies are pushed to the Redis queue simultaneously" },
//               { icon:"🤖", title:"Same Pipeline",    desc:"Each policy runs the full LangGraph agent pipeline with HITL when required" },
//             ].map((item, i) => (
//               <div key={i} style={{ flex:1, background:C.bg, borderRadius:12, padding:"16px 18px",
//                 border:`1px solid ${C.border}` }}>
//                 <div style={{ fontSize:22, marginBottom:8 }}>{item.icon}</div>
//                 <div style={{ fontSize:13, fontWeight:700, color:C.text, marginBottom:4 }}>{item.title}</div>
//                 <div style={{ fontSize:12, color:C.muted, lineHeight:1.5 }}>{item.desc}</div>
//               </div>
//             ))}
//           </div>
 
//           {/* Error */}
//           {batchError && (
//             <div style={{ padding:"10px 14px", background:"#FEE2E2", borderRadius:8,
//               border:`1px solid #FECACA`, fontSize:13, color:"#991B1B", marginBottom:16 }}>
//               ✗ {batchError}
//             </div>
//           )}
 
//           {/* CTA or result */}
//           {!batchResult ? (
//             <button
//               disabled={fetchingAPI}
//               onClick={handleFetchFromAPI}
//               style={{ background:fetchingAPI ? C.border : `linear-gradient(135deg, ${C.accent}, ${C.teal})`,
//                 color:"#fff", border:"none", borderRadius:10, padding:"13px 32px",
//                 fontSize:15, fontWeight:800, cursor:fetchingAPI ? "default" : "pointer",
//                 display:"flex", alignItems:"center", gap:10, transition:"all 0.2s",
//                 opacity:fetchingAPI ? 0.7 : 1, boxShadow:fetchingAPI ? "none" : "0 4px 16px rgba(30,111,217,0.3)" }}>
//               {fetchingAPI
//                 ? <><span style={{ fontSize:18 }}>⚙️</span> Fetching &amp; Queuing Policies…</>
//                 : <><span style={{ fontSize:18 }}>🔌</span> Fetch All Policies from API</>
//               }
//             </button>
//           ) : (
//             <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
 
//               {/* Success summary */}
//               <div style={{ padding:"16px 20px", background:"#DCFCE7", borderRadius:12,
//                 border:`1px solid #86EFAC`, display:"flex", alignItems:"center", gap:14 }}>
//                 <span style={{ fontSize:28 }}>🚀</span>
//                 <div>
//                   <div style={{ fontSize:15, fontWeight:800, color:"#15803D" }}>
//                     {batchResult.total_queued} policies queued for audit!
//                   </div>
//                   <div style={{ fontSize:12, color:"#166534", marginTop:2 }}>
//                     Batch ID: {batchResult.batch_id} — Monitor progress on the AI Audit screen.
//                   </div>
//                 </div>
//               </div>
 
//               {/* Policy case list */}
//               <div style={{ background:C.bg, borderRadius:12, border:`1px solid ${C.border}`,
//                 overflow:"hidden" }}>
//                 <div style={{ padding:"12px 16px", borderBottom:`1px solid ${C.border}`,
//                   fontSize:12, fontWeight:700, color:C.muted, textTransform:"uppercase",
//                   letterSpacing:0.8, display:"flex", gap:0 }}>
//                   <span style={{ flex:2 }}>Policy Number</span>
//                   <span style={{ flex:1 }}>Case ID</span>
//                   <span style={{ flex:1 }}>Status</span>
//                 </div>
//                 <div style={{ maxHeight:260, overflowY:"auto" }}>
//                   {batchResult.cases.map((c, i) => (
//                     <div key={c.audit_case_id}
//                       style={{ display:"flex", padding:"11px 16px", alignItems:"center",
//                         borderBottom:`1px solid ${C.border}`,
//                         background: i % 2 === 0 ? "#fff" : C.bg }}>
//                       <span style={{ flex:2, fontSize:13, fontWeight:700, color:C.accent }}>
//                         {c.policy_number}
//                       </span>
//                       <span style={{ flex:1, fontSize:13, color:C.text }}>
//                         #{c.audit_case_id}
//                       </span>
//                       <span style={{ flex:1 }}>
//                         <StatusBadge status="pending" />
//                       </span>
//                     </div>
//                   ))}
//                 </div>
//               </div>
 
//               {/* API errors if any */}
//               {batchResult.errors?.length > 0 && (
//                 <div style={{ padding:"12px 16px", background:"#FEF3C7", borderRadius:10,
//                   border:`1px solid ${C.amber}`, fontSize:12, color:"#92400E" }}>
//                   ⚠️ <strong>{batchResult.errors.length} policy(ies) failed to queue:</strong>
//                   <ul style={{ margin:"6px 0 0 16px", padding:0 }}>
//                     {batchResult.errors.map((e, i) => <li key={i}>{e}</li>)}
//                   </ul>
//                 </div>
//               )}
 
//               {/* Reset */}
//               <button onClick={() => { setBatchResult(null); setBatchError(null); }}
//                 style={{ alignSelf:"flex-start", background:C.bg, border:`1px solid ${C.border}`,
//                   borderRadius:8, padding:"7px 16px", fontSize:12, cursor:"pointer", color:C.muted }}>
//                 ↺ Run another batch
//               </button>
//             </div>
//           )}
//         </div>
//       )}
 
//       {/* How it works */}
//       <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
//         <SectionHeader title="How it works" sub={apiMode ? "API batch audit pipeline" : "The 3-step file audit pipeline"} />
//         <div style={{ display:"flex", gap:16 }}>
//           {(apiMode ? [
//             { n:"1", title:"Discover",  desc:"Backend calls Mock API GET /policies to retrieve all policy numbers in your account.", icon:"🔌" },
//             { n:"2", title:"Queue All", desc:"Each policy gets its own DB row and is pushed to the Redis Stream with data_source='api'.", icon:"⚡" },
//             { n:"3", title:"Process",   desc:"Worker picks up policies one by one. Each runs the full agent pipeline with HITL if high-risk.", icon:"🤖" },
//           ] : [
//             { n:"1", title:"Upload",  desc:"Drop payroll Excel, policy XML, and audit metadata. Files are securely processed.", icon:"📂" },
//             { n:"2", title:"Analyze", desc:"LangGraph multi-agent pipeline: Ingestion → Specialist agents → Premium calculation → AI narrative.", icon:"🤖" },
//             { n:"3", title:"Review",  desc:"Auditor reviews variance report, HITL decisions, and AI explanation. Download final report.", icon:"📊" },
//           ]).map(s => (
//             <div key={s.n} style={{ flex:1, background:C.bg, borderRadius:12, padding:"18px 20px" }}>
//               <div style={{ width:32, height:32, borderRadius:"50%",
//                 background:`linear-gradient(135deg, ${C.accent}, ${C.teal})`,
//                 color:"#fff", display:"flex", alignItems:"center", justifyContent:"center",
//                 fontWeight:800, fontSize:14, marginBottom:12 }}>{s.n}</div>
//               <div style={{ fontSize:16 }}>{s.icon}</div>
//               <div style={{ fontSize:14, fontWeight:700, color:C.text, marginBottom:6 }}>{s.title}</div>
//               <div style={{ fontSize:12, color:C.muted, lineHeight:1.6 }}>{s.desc}</div>
//             </div>
//           ))}
//         </div>
//       </div>
//     </div>
//   );
// }


// ── SkippedPoliciesBanner ─────────────────────────────────────────────────────
// Displayed in the API Fetch tab after "Start Batch Audit" runs validation.
// Shows each policy that was excluded from the queue and exactly why.
function SkippedPoliciesBanner({ policies }) {
  const [expanded, setExpanded] = useState(false);
  if (!policies || policies.length === 0) return null;
  return (
    <div style={{ background:"#FFF7ED", border:"1px solid #FED7AA",
      borderRadius:12, padding:"14px 18px", display:"flex",
      alignItems:"flex-start", gap:12 }}>
      <span style={{ fontSize:20, flexShrink:0 }}>⚠️</span>
      <div style={{ flex:1 }}>
        <div style={{ fontWeight:700, fontSize:14, color:"#9A3412", marginBottom:4 }}>
          {policies.length} {policies.length === 1 ? "policy" : "policies"} skipped — will not be queued
        </div>
        <div style={{ fontSize:12, color:"#C2410C", marginBottom:8 }}>
          These records were excluded before submission because they are either unavailable
          in the Mock API or are missing required fields.
        </div>
        <button onClick={() => setExpanded(v => !v)}
          style={{ background:"#FED7AA", border:"none", borderRadius:6,
            padding:"4px 14px", fontSize:12, fontWeight:700,
            cursor:"pointer", color:"#9A3412" }}>
          {expanded ? "Hide Details ▲" : "View Details ▼"}
        </button>
        {expanded && (
          <div style={{ marginTop:12, display:"flex", flexDirection:"column", gap:6 }}>
            {policies.map((p, i) => (
              <div key={i} style={{ background:"#fff", border:"1px solid #FECACA",
                borderRadius:8, padding:"10px 14px",
                display:"flex", alignItems:"center", gap:14, flexWrap:"wrap" }}>
                <span style={{ fontSize:13, fontWeight:700, color:"#6B7E99", minWidth:130 }}>
                  {p.policy_number || <em style={{ color:"#EF4444" }}>No policy_number</em>}
                </span>
                <span style={{ fontSize:13, flex:1, color:"#1A2B42" }}>
                  {p.insured_name || <em style={{ color:"#9CA3AF" }}>Unknown insured</em>}
                </span>
                <span style={{ fontSize:11, background:"#FEE2E2", color:"#DC2626",
                  borderRadius:20, padding:"2px 10px", fontWeight:700, whiteSpace:"nowrap" }}>
                  {p._skipReason}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function DataUpload({ onAuditStarted, onBatchStarted }) {
  // ── File-upload state (unchanged) ─────────────────────────────────
  const [payrollFile,  setPayrollFile]  = useState(null);
  const [policyFile,   setPolicyFile]   = useState(null);
  const [metaFile,     setMetaFile]     = useState(null);
  const [policyNumber, setPolicyNumber] = useState("");
  const [dragging,     setDragging]     = useState(null);
  const [uploading,    setUploading]    = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [starting,     setStarting]     = useState(false);
  const [started,      setStarted]      = useState(null);
  const [error,        setError]        = useState(null);
 
  // ── API Batch state (two-step) ─────────────────────────────────────
  const [apiMode,       setApiMode]       = useState(true);
  // Step 1 — Preview
  const [previewing,    setPreviewing]    = useState(false);
  const [previewData,   setPreviewData]   = useState(null);   // PolicyPreviewResponse
  const [previewError,  setPreviewError]  = useState(null);
  // Step 2 — Start batch
  const [starting2,     setStarting2]     = useState(false);
  const [batchResult,   setBatchResult]   = useState(null);
  const [batchError,    setBatchError]    = useState(null);
  const [skippedPolicies, setSkippedPolicies] = useState([]);  // policies filtered out before queuing
 
  const allReady = payrollFile && policyFile && metaFile && policyNumber.trim();
  const money    = (n) => n == null ? "—" : `$${Number(n).toLocaleString(undefined, {minimumFractionDigits:0})}`;
 
  // ── File upload handlers (unchanged) ──────────────────────────────
  const handleUpload = async () => {
    if (!allReady) return;
    setUploading(true); setError(null);
    try {
      const result = await uploadAuditFiles(payrollFile, policyFile, metaFile);
      setUploadResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setUploading(false);
    }
  };
 
  const handleStart = async () => {
    if (!uploadResult) return;
    setStarting(true); setError(null);
    try {
      const result = await startAudit({
        policy_number:        policyNumber.trim(),
        payroll_file_path:    uploadResult.payroll_file_path,
        policy_xml_path:      uploadResult.policy_xml_path,
        audit_meta_file_path: uploadResult.audit_meta_file_path,
      });
      setStarted(result);
      onAuditStarted?.(result.audit_case_id);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setStarting(false);
    }
  };
 
  // ── Step 1: Preview policies ───────────────────────────────────────
  const handlePreview = async () => {
    setPreviewing(true); setPreviewError(null); setPreviewData(null); setBatchResult(null);
    try {
      const result = await previewAPIPolicies();  // GET /wc-audit/preview-api-policies
      setPreviewData(result);
    } catch (err) {
      setPreviewError(err.response?.data?.detail || err.message || "Preview failed");
    } finally {
      setPreviewing(false);
    }
  };
 
  // ── Required fields for a policy to be processable ────────────────
  const REQUIRED_FIELDS = ["policy_number", "insured_name", "state_code", "effective_date", "expiration_date"];
  // Backend returns "—" (em dash) for missing values — treat it the same as null/""
  const isMissing = (v) => !v || String(v).trim() === "" || String(v).trim() === "—";

  // ── Step 2: Start the batch (only valid + available policies) ──────
  const handleStartBatch = async () => {
    if (!previewData?.policies?.length) return;

    // Filter: must be available AND have all required fields non-empty
    const valid   = [];
    const skipped = [];

    previewData.policies.forEach(p => {
      if (!p.available) {
        skipped.push({ ...p, _skipReason: "Not found / unavailable in Mock API" });
        return;
      }
      const missingFields = REQUIRED_FIELDS.filter(f => isMissing(p[f]));
      if (missingFields.length > 0) {
        skipped.push({ ...p, _skipReason: `Missing required fields: ${missingFields.join(", ")}` });
      } else {
        valid.push(p.policy_number);
      }
    });

    setSkippedPolicies(skipped);

    // If nothing passed validation, stop here — do NOT hit the backend
    if (valid.length === 0) {
      setBatchError("No processable policies found. All records are either unavailable or missing required fields.");
      return;
    }

    setStarting2(true); setBatchError(null);
    try {
      // Pass only validated policy_numbers so backend queues exactly these
      const result = await startBatchAuditFromAPI(valid);
      setBatchResult(result);
      onBatchStarted?.(result.cases.map(c => c.audit_case_id));
    } catch (err) {
      setBatchError(err.response?.data?.detail || err.message || "Batch start failed");
    } finally {
      setStarting2(false);
    }
  };
 
  const handleReset = () => {
    setPreviewData(null); setPreviewError(null);
    setBatchResult(null); setBatchError(null);
    setSkippedPolicies([]);
  };
 
  const FileDropZone = ({ label, file, setFile, accept, dragKey }) => (
    <div
      style={{ background:dragging === dragKey ? "#EEF2FF" : C.bg,
        border:`2px dashed ${dragging === dragKey ? C.accent : C.border}`,
        borderRadius:12, padding:"20px 24px", cursor:"pointer", transition:"all 0.2s",
        display:"flex", alignItems:"center", gap:14 }}
      onDragOver={e => { e.preventDefault(); setDragging(dragKey); }}
      onDragLeave={() => setDragging(null)}
      onDrop={e => { e.preventDefault(); setDragging(null);
        const f = e.dataTransfer.files[0]; if (f) setFile(f); }}
      onClick={() => document.getElementById(`inp-${dragKey}`).click()}>
      <span style={{ fontSize:28 }}>{file ? "✅" : "📂"}</span>
      <div>
        <div style={{ fontSize:13, fontWeight:700, color:C.text }}>{label}</div>
        <div style={{ fontSize:12, color:C.muted }}>
          {file ? file.name : `Drop or click to select — ${accept}`}
        </div>
      </div>
      <input id={`inp-${dragKey}`} type="file" accept={accept} style={{ display:"none" }}
        onChange={e => e.target.files[0] && setFile(e.target.files[0])} />
    </div>
  );
 
  return (
    <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
 
      {/* ── Source selector tabs ──────────────────────────────────── */}
      <div style={{ display:"flex", gap:0, background:C.bg, borderRadius:12,
        border:`1px solid ${C.border}`, overflow:"hidden", alignSelf:"flex-start" }}>
        {[
          // { key:false, label:"📂  File Upload",    desc:"Upload Excel & XML files" },
          { key:true,  label:"🔌  Fetch from API", desc:"Pull all policies from Mock API" },
        ].map(tab => (
          <button key={String(tab.key)} onClick={() => { setApiMode(tab.key); handleReset(); }}
            style={{ padding:"12px 28px", border:"none", cursor:"pointer",
              background: apiMode === tab.key
                ? `linear-gradient(135deg, ${C.accent}, ${C.teal})`
                : "transparent",
              color: apiMode === tab.key ? "#fff" : C.muted,
              fontWeight:700, fontSize:13, transition:"all 0.2s",
              borderRight:`1px solid ${C.border}` }}>
            {tab.label}
          </button>
        ))}
      </div>
 
      {/* ══════════════════════════════════════════════════════════════
          FILE UPLOAD TAB
      ══════════════════════════════════════════════════════════════ */}
      {/* {!apiMode && (
        <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:28 }}>
          <SectionHeader title="Run New Audit"
            sub="Upload three source files, enter policy number, then start the AI pipeline" />
 
          <div style={{ display:"flex", flexDirection:"column", gap:12, marginBottom:20 }}>
            <FileDropZone label="Payroll Excel (.xlsx)"  file={payrollFile} setFile={setPayrollFile} accept=".xlsx" dragKey="payroll" />
            <FileDropZone label="Policy XML (.xml)"      file={policyFile}  setFile={setPolicyFile}  accept=".xml"  dragKey="policy" />
            <FileDropZone label="Audit Metadata (.xlsx)" file={metaFile}    setFile={setMetaFile}    accept=".xlsx" dragKey="meta" />
          </div>
 
          <div style={{ marginBottom:20 }}>
            <label style={{ fontSize:12, fontWeight:700, color:C.muted, textTransform:"uppercase",
              letterSpacing:0.8, display:"block", marginBottom:6 }}>Policy Number</label>
            <input value={policyNumber} onChange={e => setPolicyNumber(e.target.value)}
              placeholder="e.g. MWC0183363-05"
              style={{ border:`1px solid ${C.border}`, borderRadius:8, padding:"10px 14px", fontSize:13,
                width:"100%", outline:"none", color:C.text, boxSizing:"border-box", maxWidth:340 }} />
          </div>
 
          {error && (
            <div style={{ padding:"10px 14px", background:"#FEE2E2", borderRadius:8,
              border:`1px solid #FECACA`, fontSize:13, color:"#991B1B", marginBottom:16 }}>✗ {error}</div>
          )}
 
          <div style={{ display:"flex", gap:12, alignItems:"center" }}>
            {!uploadResult ? (
              <button disabled={!allReady || uploading} onClick={handleUpload}
                style={{ background:allReady ? C.accent : C.border, color:"#fff", border:"none",
                  borderRadius:10, padding:"11px 28px", fontSize:14, fontWeight:700,
                  cursor:allReady && !uploading ? "pointer" : "default", opacity:uploading ? 0.7 : 1 }}>
                {uploading ? "⚙️ Uploading..." : "⬆ Upload Files"}
              </button>
            ) : !started ? (
              <>
                <div style={{ padding:"8px 16px", background:"#DCFCE7", borderRadius:8,
                  fontSize:13, fontWeight:600, color:"#15803D" }}>
                  ✓ Files uploaded — Session: {uploadResult.session_id}
                </div>
                <button disabled={starting} onClick={handleStart}
                  style={{ background:C.green, color:"#fff", border:"none", borderRadius:10,
                    padding:"11px 28px", fontSize:14, fontWeight:700,
                    cursor:starting ? "default" : "pointer", opacity:starting ? 0.7 : 1 }}>
                  {starting ? "⚙️ Starting..." : "▶ Start AI Audit"}
                </button>
              </>
            ) : (
              <div style={{ padding:"12px 20px", background:"#DCFCE7", borderRadius:10,
                border:`1px solid #86EFAC`, fontSize:14, fontWeight:700, color:"#15803D" }}>
                🚀 Audit started! Case #{started.audit_case_id} — Check AI Audit screen for live progress.
              </div>
            )}
          </div>
        </div>
      )} */}
 
      {/* ══════════════════════════════════════════════════════════════
          API FETCH TAB — two-step: Preview → Start Batch
      ══════════════════════════════════════════════════════════════ */}
      {apiMode && (
        <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:28 }}>
 
          {/* ── IDLE: nothing loaded yet ── */}
          {!previewData && !batchResult && (
            <>
              <SectionHeader
                title="Fetch All Policies from API"
                sub="Preview available policies before starting the batch audit" />
 
              {/* Info cards */}
              <div style={{ display:"flex", gap:14, marginBottom:24 }}>
                {[
                  { icon:"🔍", title:"Preview First",    desc:"Loads all policy details from the Mock API so you can review before committing" },
                  { icon:"⚡", title:"Cache & Queue",    desc:"Policy configs are cached in Redis — worker only fetches payroll data" },
                  { icon:"🤖", title:"Full Pipeline",    desc:"Each policy runs the complete LangGraph pipeline with HITL when required" },
                ].map((item, i) => (
                  <div key={i} style={{ flex:1, background:C.bg, borderRadius:12,
                    padding:"16px 18px", border:`1px solid ${C.border}` }}>
                    <div style={{ fontSize:22, marginBottom:8 }}>{item.icon}</div>
                    <div style={{ fontSize:13, fontWeight:700, color:C.text, marginBottom:4 }}>{item.title}</div>
                    <div style={{ fontSize:12, color:C.muted, lineHeight:1.5 }}>{item.desc}</div>
                  </div>
                ))}
              </div>
 
              {previewError && (
                <div style={{ padding:"10px 14px", background:"#FEE2E2", borderRadius:8,
                  border:`1px solid #FECACA`, fontSize:13, color:"#991B1B", marginBottom:16 }}>
                  ✗ {previewError}
                </div>
              )}
 
              {/* Step 1 button */}
              <button disabled={previewing} onClick={handlePreview}
                style={{
                  background: previewing ? C.border : `linear-gradient(135deg, ${C.accent}, ${C.teal})`,
                  color:"#fff", border:"none", borderRadius:10, padding:"13px 32px",
                  fontSize:15, fontWeight:800, cursor:previewing ? "default" : "pointer",
                  display:"flex", alignItems:"center", gap:10, transition:"all 0.2s",
                  opacity:previewing ? 0.7 : 1,
                  boxShadow:previewing ? "none" : "0 4px 16px rgba(30,111,217,0.3)",
                }}>
                {previewing
                  ? <><span style={{ fontSize:18 }}>⚙️</span> Loading Policy Details…</>
                  : <><span style={{ fontSize:18 }}>🔍</span> Fetch Policies from API</>
                }
              </button>
            </>
          )}
 
          {/* ── STEP 1 DONE: Policy preview table ── */}
          {previewData && !batchResult && (
            <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
 
              {/* Summary bar */}
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center",
                flexWrap:"wrap", gap:12 }}>
                <div>
                  <h3 style={{ margin:0, fontSize:17, fontWeight:800, color:C.text }}>
                    Policy Preview — {previewData.total} Policies Found
                  </h3>
                  <div style={{ fontSize:12, color:C.muted, marginTop:3 }}>
                    Policy details loaded and cached. Review below, then start the batch.
                  </div>
                </div>
                <div style={{ display:"flex", gap:10 }}>
                  <button onClick={handleReset}
                    style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:8,
                      padding:"7px 14px", fontSize:12, cursor:"pointer", color:C.muted, fontWeight:600 }}>
                    ↺ Reload
                  </button>
                  <button onClick={handleStartBatch} disabled={starting2}
                    style={{
                      background: starting2 ? "#86EFAC" : C.green,
                      color:"#fff", border:"none", borderRadius:10,
                      padding:"10px 24px", fontSize:14, fontWeight:800,
                      cursor: starting2 ? "default" : "pointer",
                      display:"flex", alignItems:"center", gap:8,
                      boxShadow: starting2 ? "none" : "0 4px 14px rgba(16,185,129,0.35)",
                      transition:"all 0.2s",
                    }}>
                    {starting2
                      ? <><span>⚙️</span> Queuing…</>
                      : <><span>▶</span> Start Batch Audit ({previewData.policies.filter(p => p.available && REQUIRED_FIELDS.every(f => !isMissing(p[f]))).length} processable)</>
                    }
                  </button>
                </div>
              </div>
 
              {batchError && (
                <div style={{ padding:"10px 14px", background:"#FEE2E2", borderRadius:8,
                  border:`1px solid #FECACA`, fontSize:13, color:"#991B1B" }}>
                  ✗ {batchError}
                </div>
              )}
 
              {/* Skipped policies banner — shown after validation on Start Batch */}
              {skippedPolicies.length > 0 && !batchResult && (
                <SkippedPoliciesBanner policies={skippedPolicies} />
              )}

              {/* KPI chips */}
              <div style={{ display:"flex", gap:12 }}>
                {[
                  { label:"Will Process",  value: previewData.policies.filter(p => p.available && REQUIRED_FIELDS.every(f => !isMissing(p[f]))).length, color:C.green  },
                  { label:"Unavailable",   value: previewData.policies.filter(p => !p.available).length, color:C.red    },
                  { label:"Missing Data",  value: previewData.policies.filter(p => p.available && REQUIRED_FIELDS.some(f => isMissing(p[f]))).length, color:C.amber  },
                  { label:"States",        value: new Set(previewData.policies.map(p => p.state_code).filter(Boolean)).size, color:C.accent },
                ].map(({ label, value, color }) => (
                  <div key={label} style={{ background:C.bg, borderRadius:10,
                    padding:"10px 18px", border:`1px solid ${C.border}`, textAlign:"center" }}>
                    <div style={{ fontSize:20, fontWeight:800, color }}>{value}</div>
                    <div style={{ fontSize:11, color:C.muted, fontWeight:600 }}>{label}</div>
                  </div>
                ))}
              </div>
 
              {/* Policy detail table */}
              <div style={{ border:`1px solid ${C.border}`, borderRadius:12, overflow:"hidden" }}>
                {/* Table header */}
                <div style={{ display:"grid",
                  gridTemplateColumns:"1.6fr 2fr 1fr 1fr 0.8fr 1.2fr 1fr 0.7fr",
                  background:"#F8FAFD", borderBottom:`1px solid ${C.border}`,
                  padding:"10px 16px", gap:8 }}>
                  {["Policy Number","Insured Name","Eff. Date","Exp. Date","State","Class Codes","Est Premium","Freq"].map(h => (
                    <div key={h} style={{ fontSize:10, fontWeight:700, color:C.muted,
                      textTransform:"uppercase", letterSpacing:0.7 }}>{h}</div>
                  ))}
                </div>
 
                {/* Table rows */}
                <div style={{ maxHeight:380, overflowY:"auto" }}>
                  {previewData.policies.map((p, i) => (
                    <div key={p.policy_number}
                      style={{
                        display:"grid",
                        gridTemplateColumns:"1.6fr 2fr 1fr 1fr 0.8fr 1.2fr 1fr 0.7fr",
                        padding:"11px 16px", gap:8, alignItems:"center",
                        borderBottom:`1px solid ${C.border}`,
                        background: !p.available
                          ? "#FFF7F7"
                          : (p.available && REQUIRED_FIELDS.some(f => isMissing(p[f])))
                            ? "#FFFBEB"
                            : i % 2 === 0 ? "#fff" : C.bg,
                        transition:"background 0.12s",
                      }}
                      onMouseEnter={e => {
                        if (!p.available) return;
                        const hasMissing = REQUIRED_FIELDS.some(f => isMissing(p[f]));
                        e.currentTarget.style.background = hasMissing ? "#FEF3C7" : "#EEF2FF";
                      }}
                      onMouseLeave={e => {
                        const hasMissing = REQUIRED_FIELDS.some(f => isMissing(p[f]));
                        e.currentTarget.style.background = !p.available ? "#FFF7F7"
                          : hasMissing ? "#FFFBEB"
                          : i % 2 === 0 ? "#fff" : C.bg;
                      }}
                    >
                      {/* Policy Number */}
                      <div style={{ fontSize:13, fontWeight:700,
                        color: p.available ? C.accent : C.muted,
                        display:"flex", alignItems:"center", gap:6 }}>
                        {!p.available && <span title="Not found in Mock API" style={{ color:C.red }}>⚠</span>}
                        {p.available && REQUIRED_FIELDS.some(f => isMissing(p[f])) && (
                          <span title={`Missing: ${REQUIRED_FIELDS.filter(f => isMissing(p[f])).join(", ")}`}
                            style={{ color:C.amber }}>⚠</span>
                        )}
                        {p.policy_number}
                      </div>
 
                      {/* Insured Name */}
                      <div style={{ fontSize:12, color:C.text,
                        overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
                        {p.insured_name || "—"}
                      </div>
 
                      {/* Effective Date */}
                      <div style={{ fontSize:12, color:C.muted }}>{p.effective_date || "—"}</div>
 
                      {/* Expiration Date */}
                      <div style={{ fontSize:12, color:C.muted }}>{p.expiration_date || "—"}</div>
 
                      {/* State */}
                      <div style={{ fontSize:12, fontWeight:700, color:C.text }}>{p.state_code || "—"}</div>
 
                      {/* Class Codes */}
                      <div style={{ fontSize:11, color:C.muted,
                        overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
                        {p.class_codes || "—"}
                      </div>
 
                      {/* Est Premium */}
                      <div style={{ fontSize:12, fontWeight:600, color:C.text }}>
                        {p.est_premium ? money(p.est_premium) : "—"}
                      </div>
 
                      {/* Payroll Frequency */}
                      <div style={{ fontSize:11, color:C.muted }}>{p.payroll_frequency || "—"}</div>
                    </div>
                  ))}
                </div>
              </div>
 
              {/* Preview errors (404 policies) */}
              {previewData.errors?.length > 0 && (
                <div style={{ padding:"12px 16px", background:"#FEF3C7", borderRadius:10,
                  border:`1px solid ${C.amber}`, fontSize:12, color:"#92400E" }}>
                  ⚠️ <strong>{previewData.errors.length} policy(ies) unavailable:</strong>
                  <ul style={{ margin:"4px 0 0 16px", padding:0 }}>
                    {previewData.errors.map((e, i) => <li key={i}>{e}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}
 
          {/* ── STEP 2 DONE: Batch queued ── */}
          {batchResult && (
            <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
              <div style={{ padding:"16px 20px", background:"#DCFCE7", borderRadius:12,
                border:`1px solid #86EFAC`, display:"flex", alignItems:"center", gap:14 }}>
                <span style={{ fontSize:28 }}>🚀</span>
                <div>
                  <div style={{ fontSize:15, fontWeight:800, color:"#15803D" }}>
                    {batchResult.total_queued} policies queued for audit!
                  </div>
                  <div style={{ fontSize:12, color:"#166534", marginTop:2 }}>
                    Batch ID: {batchResult.batch_id} — Monitor progress on the AI Audit screen.
                  </div>
                </div>
              </div>
 
              {/* Queued list with preview details */}
              <div style={{ border:`1px solid ${C.border}`, borderRadius:12, overflow:"hidden" }}>
                <div style={{ display:"grid", gridTemplateColumns:"1.6fr 2fr 1fr 0.8fr 1fr",
                  background:"#F8FAFD", borderBottom:`1px solid ${C.border}`,
                  padding:"10px 16px", gap:8 }}>
                  {["Policy Number","Insured Name","Case ID","State","Status"].map(h => (
                    <div key={h} style={{ fontSize:10, fontWeight:700, color:C.muted,
                      textTransform:"uppercase", letterSpacing:0.7 }}>{h}</div>
                  ))}
                </div>
                <div style={{ maxHeight:300, overflowY:"auto" }}>
                  {batchResult.cases.map((c, i) => {
                    const detail = previewData?.policies.find(p => p.policy_number === c.policy_number);
                    return (
                      <div key={c.audit_case_id}
                        style={{ display:"grid", gridTemplateColumns:"1.6fr 2fr 1fr 0.8fr 1fr",
                          padding:"11px 16px", gap:8, alignItems:"center",
                          borderBottom:`1px solid ${C.border}`,
                          background: i % 2 === 0 ? "#fff" : C.bg }}>
                        <div style={{ fontSize:13, fontWeight:700, color:C.accent }}>
                          {c.policy_number}
                        </div>
                        <div style={{ fontSize:12, color:C.muted,
                          overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
                          {detail?.insured_name || "—"}
                        </div>
                        <div style={{ fontSize:13, color:C.text }}>#{c.audit_case_id}</div>
                        <div style={{ fontSize:12, fontWeight:700, color:C.text }}>
                          {detail?.state_code || "—"}
                        </div>
                        <span><StatusBadge status="pending" /></span>
                      </div>
                    );
                  })}
                </div>
              </div>
 
              {batchResult.errors?.length > 0 && (
                <div style={{ padding:"12px 16px", background:"#FEF3C7", borderRadius:10,
                  border:`1px solid ${C.amber}`, fontSize:12, color:"#92400E" }}>
                  ⚠️ <strong>{batchResult.errors.length} failed to queue:</strong>
                  <ul style={{ margin:"4px 0 0 16px", padding:0 }}>
                    {batchResult.errors.map((e, i) => <li key={i}>{e}</li>)}
                  </ul>
                </div>
              )}
 
              <button onClick={handleReset}
                style={{ alignSelf:"flex-start", background:C.bg,
                  border:`1px solid ${C.border}`, borderRadius:8,
                  padding:"7px 16px", fontSize:12, cursor:"pointer", color:C.muted }}>
                ↺ Run another batch
              </button>
            </div>
          )}
        </div>
      )}
 
      {/* How it works */}
      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
        <SectionHeader title="How it works"
          sub={apiMode ? "Two-step API batch audit pipeline" : "The 3-step file audit pipeline"} />
        <div style={{ display:"flex", gap:16 }}>
          {(apiMode ? [
            { n:"1", title:"Preview",    desc:"Backend fetches all policies + configs from Mock API. Details shown in a table for review.", icon:"🔍" },
            { n:"2", title:"Queue",      desc:"Confirmed policies are pushed to the Redis audit queue with configs pre-cached.", icon:"⚡" },
            { n:"3", title:"Process",    desc:"Worker processes each policy — fetches payroll data only (config already cached). HITL when high-risk.", icon:"🤖" },
          ] : [
            { n:"1", title:"Upload",  desc:"Drop payroll Excel, policy XML, and audit metadata. Files are securely processed.", icon:"📂" },
            { n:"2", title:"Analyze", desc:"LangGraph multi-agent pipeline: Ingestion → Specialist agents → Premium calculation → AI narrative.", icon:"🤖" },
            { n:"3", title:"Review",  desc:"Auditor reviews variance report, HITL decisions, and AI explanation. Download final report.", icon:"📊" },
          ]).map(s => (
            <div key={s.n} style={{ flex:1, background:C.bg, borderRadius:12, padding:"18px 20px" }}>
              <div style={{ width:32, height:32, borderRadius:"50%", background:C.accent,
                color:"#fff", display:"flex", alignItems:"center", justifyContent:"center",
                fontWeight:800, fontSize:14, marginBottom:12 }}>{s.n}</div>
              <div style={{ fontSize:16 }}>{s.icon}</div>
              <div style={{ fontSize:14, fontWeight:700, color:C.text, marginBottom:6 }}>{s.title}</div>
              <div style={{ fontSize:12, color:C.muted, lineHeight:1.6 }}>{s.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Administration({ setScreen, onDataCleared }) {
  // ── Tab state ─────────────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState("configuration");  // "configuration" | "data"

  // ── Data wipe state ───────────────────────────────────────────────────────
  const [phase,      setPhase]      = useState("idle");
  const [confirmTxt, setConfirmTxt] = useState("");
  const [wipeResult, setWipeResult] = useState(null);
  const [wipeErr,    setWipeErr]    = useState("");
  const CONFIRM_PHRASE = "DELETE ALL DATA";

  // ── HITL config state ─────────────────────────────────────────────────────
  const [hitlEnabled,      setHitlEnabled]      = useState(true);
  const [configLoading,    setConfigLoading]    = useState(true);
  const [configSaving,     setConfigSaving]     = useState(false);
  const [configSaveStatus, setConfigSaveStatus] = useState(null); // null | "saved" | "error"
  const [configErr,        setConfigErr]        = useState("");

  // Load config on mount
  useEffect(() => {
    (async () => {
      setConfigLoading(true);
      try {
        const cfg = await getAuditConfig();
        setHitlEnabled(cfg.hitl_enabled ?? true);
      } catch (e) {
        setConfigErr(e.message || "Failed to load config");
      } finally {
        setConfigLoading(false);
      }
    })();
  }, []);

  const handleHitlToggle = async (newValue) => {
    setHitlEnabled(newValue);
    setConfigSaving(true);
    setConfigSaveStatus(null);
    try {
      await updateAuditConfig({ hitl_enabled: newValue });
      setConfigSaveStatus("saved");
      setTimeout(() => setConfigSaveStatus(null), 3000);
    } catch (e) {
      setConfigErr(e.message || "Failed to save config");
      setConfigSaveStatus("error");
      setHitlEnabled(!newValue);  // revert on error
    } finally {
      setConfigSaving(false);
    }
  };

  // ── Data wipe handlers ────────────────────────────────────────────────────
  const handleWipe = async () => {
    setPhase("wiping");
    setWipeErr("");
    try {
      const data = await clearAllAuditData();
      setWipeResult(data);
      setPhase("done");
      onDataCleared?.();
    } catch (err) {
      setWipeErr(err.response?.data?.detail || err.message || "Unknown error");
      setPhase("error");
    }
  };

  const reset = () => {
    setPhase("idle");
    setConfirmTxt("");
    setWipeResult(null);
    setWipeErr("");
  };
 
  // ── Reusable tab button ──────────────────────────────────────────────────────
  const TabBtn = ({ id, icon, label }) => (
    <button onClick={() => setActiveTab(id)}
      style={{
        display:"flex", alignItems:"center", gap:8,
        padding:"10px 20px", border:"none", cursor:"pointer",
        fontWeight:700, fontSize:13, borderRadius:"10px 10px 0 0",
        background: activeTab === id
          ? C.card
          : "transparent",
        color: activeTab === id ? C.accent : C.muted,
        borderBottom: activeTab === id ? `2px solid ${C.accent}` : "2px solid transparent",
        transition:"all 0.15s",
      }}>
      <span style={{ fontSize:15 }}>{icon}</span> {label}
    </button>
  );

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:0, maxWidth:900 }}>

      {/* ── Page header ────────────────────────────────────────────── */}
      <div style={{ background:C.card, border:`1px solid ${C.border}`,
        borderRadius:14, padding:24, marginBottom:20 }}>
        <div style={{ display:"flex", alignItems:"center", gap:14 }}>
          <div style={{ width:44, height:44, borderRadius:12,
            background:"linear-gradient(135deg,#7C3AED,#EF4444)",
            display:"flex", alignItems:"center", justifyContent:"center", fontSize:22 }}>⚙</div>
          <div>
            <h2 style={{ margin:0, fontSize:20, fontWeight:800, color:C.text }}>Administration</h2>
            <p style={{ margin:"3px 0 0", fontSize:13, color:C.muted }}>
              Platform-level configuration and data management — Super Admin only.
            </p>
          </div>
        </div>
      </div>

      {/* ── Tab bar ────────────────────────────────────────────────── */}
      <div style={{ display:"flex", gap:4, borderBottom:`2px solid ${C.border}`,
        marginBottom:24, paddingLeft:4 }}>
        <TabBtn id="configuration" icon="⚙" label="Configuration" />
        <TabBtn id="data"          icon="🗑" label="Data Management" />
      </div>

      {/* ══════════════════════════════════════════════════════════════
          TAB: CONFIGURATION
      ══════════════════════════════════════════════════════════════ */}
      {activeTab === "configuration" && (
        <div style={{ display:"flex", flexDirection:"column", gap:20 }}>

          {/* HITL Global Toggle card */}
          <div style={{ background:C.card, border:`1px solid ${C.border}`,
            borderRadius:14, padding:28 }}>

            {/* Card header */}
            <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:20 }}>
              <div style={{ width:40, height:40, borderRadius:10,
                background: hitlEnabled ? "linear-gradient(135deg,#1E6FD9,#0ABFBC)" : "#F3F4F6",
                display:"flex", alignItems:"center", justifyContent:"center", fontSize:20,
                transition:"background 0.3s" }}>👤</div>
              <div>
                <div style={{ fontSize:16, fontWeight:800, color:C.text }}>
                  Human-in-the-Loop (HITL) Review
                </div>
                <div style={{ fontSize:12, color:C.muted, marginTop:2 }}>
                  Controls whether high-risk audits pause for human approval before finalising.
                </div>
              </div>
            </div>

            {/* Loading state */}
            {configLoading ? (
              <div style={{ display:"flex", alignItems:"center", gap:10,
                padding:"14px 18px", background:C.bg, borderRadius:10 }}>
                <div style={{ width:18, height:18, border:`2px solid ${C.accent}`,
                  borderTop:"2px solid transparent", borderRadius:"50%",
                  animation:"spin 0.8s linear infinite" }} />
                <span style={{ fontSize:13, color:C.muted }}>Loading configuration…</span>
              </div>
            ) : (
              <>
                {/* Toggle row */}
                <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between",
                  padding:"18px 22px",
                  background: hitlEnabled ? "#EFF6FF" : C.bg,
                  border:`1.5px solid ${hitlEnabled ? C.accent : C.border}`,
                  borderRadius:12, marginBottom:16, transition:"all 0.2s" }}>

                  <div>
                    <div style={{ fontSize:14, fontWeight:700, color:C.text }}>
                      HITL Reviews Globally
                      {" "}
                      <span style={{
                        fontSize:11, fontWeight:700, padding:"2px 10px", borderRadius:20,
                        background: hitlEnabled ? "#DBEAFE" : "#F3F4F6",
                        color:      hitlEnabled ? C.accent  : C.muted,
                      }}>
                        {hitlEnabled ? "ENABLED" : "DISABLED"}
                      </span>
                    </div>
                    <div style={{ fontSize:12, color:C.muted, marginTop:4 }}>
                      {hitlEnabled
                        ? "High-risk audits will pause at the HITL checkpoint and await an auditor decision."
                        : "All audits will bypass the HITL checkpoint and complete automatically."}
                    </div>
                  </div>

                  {/* Toggle switch */}
                  <div
                    onClick={() => !configSaving && handleHitlToggle(!hitlEnabled)}
                    style={{
                      width:52, height:28, borderRadius:14, cursor: configSaving ? "default" : "pointer",
                      background: hitlEnabled ? C.accent : "#D1D5DB",
                      position:"relative", flexShrink:0, marginLeft:20,
                      transition:"background 0.25s",
                      opacity: configSaving ? 0.6 : 1,
                    }}>
                    <div style={{
                      position:"absolute", top:3,
                      left: hitlEnabled ? 26 : 3,
                      width:22, height:22, borderRadius:"50%", background:"#fff",
                      boxShadow:"0 1px 4px rgba(0,0,0,0.2)",
                      transition:"left 0.25s",
                    }} />
                  </div>
                </div>

                {/* Save feedback */}
                {configSaving && (
                  <div style={{ display:"flex", alignItems:"center", gap:8, fontSize:12,
                    color:C.muted, marginBottom:10 }}>
                    <div style={{ width:14, height:14, border:`2px solid ${C.accent}`,
                      borderTop:"2px solid transparent", borderRadius:"50%",
                      animation:"spin 0.8s linear infinite" }} />
                    Saving…
                  </div>
                )}
                {configSaveStatus === "saved" && (
                  <div style={{ fontSize:12, color:C.green, fontWeight:700, marginBottom:10 }}>
                    ✓ Configuration saved successfully
                  </div>
                )}
                {configSaveStatus === "error" && (
                  <div style={{ fontSize:12, color:C.red, fontWeight:700, marginBottom:10 }}>
                    ✗ Save failed: {configErr}
                  </div>
                )}
              </>
            )}

            {/* Behaviour explanation */}
            <div style={{ background:"#F8FAFD", border:`1px solid ${C.border}`,
              borderRadius:10, padding:"14px 18px" }}>
              <div style={{ fontSize:12, fontWeight:700, color:C.text, marginBottom:10 }}>
                How this setting affects the audit pipeline:
              </div>
              <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                {[
                  {
                    icon:"✅", label:"HITL Enabled (default)",
                    desc:"assess_risk sets hitl_required based on variance %, officer issues, and amount thresholds. High-risk audits pause at hitl_checkpoint.",
                    active: hitlEnabled,
                  },
                  {
                    icon:"⚡", label:"HITL Disabled",
                    desc:"assess_risk forces hitl_required = False for every audit regardless of risk level. All audits flow directly to explanation_agent → generate_report → END.",
                    active: !hitlEnabled,
                  },
                ].map(({ icon, label, desc, active }) => (
                  <div key={label} style={{
                    display:"flex", gap:10, padding:"10px 12px",
                    borderRadius:8, border:`1px solid ${active ? C.accent : C.border}`,
                    background: active ? "#EFF6FF" : "transparent",
                  }}>
                    <span style={{ fontSize:16, flexShrink:0 }}>{icon}</span>
                    <div>
                      <div style={{ fontSize:12, fontWeight:700,
                        color: active ? C.accent : C.muted }}>{label}</div>
                      <div style={{ fontSize:11, color:C.muted, marginTop:2, lineHeight:1.5 }}>{desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════
          TAB: DATA MANAGEMENT
      ══════════════════════════════════════════════════════════════ */}
      {activeTab === "data" && (
        <div style={{ background:C.card, border:`2px solid #FECACA`, borderRadius:14, padding:28 }}>

          {/* Header */}
          <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:18 }}>
            <div style={{ width:38, height:38, borderRadius:10, background:"#FEE2E2",
              display:"flex", alignItems:"center", justifyContent:"center", fontSize:20 }}>🗑</div>
            <div>
              <div style={{ fontSize:16, fontWeight:800, color:"#991B1B" }}>Clear All Audit Data</div>
              <div style={{ fontSize:12, color:C.muted, marginTop:1 }}>
                Permanently deletes all audit cases and related policy data for this tenant.
              </div>
            </div>
          </div>

          {/* What gets deleted */}
          <div style={{ background:"#FFF7ED", border:`1px solid #FED7AA`,
            borderRadius:10, padding:"14px 18px", marginBottom:20 }}>
            <div style={{ fontSize:12, fontWeight:700, color:"#92400E", marginBottom:8 }}>
              ⚠ The following data will be permanently erased:
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"6px 24px" }}>
              {["All Audit Cases","All Policy Records","Payroll Records","Variance Lines",
                "Agent Findings","HITL Reviews","Audit Reports","Policy Class Codes & Officers",
              ].map(item => (
                <div key={item} style={{ display:"flex", alignItems:"center", gap:6, fontSize:12, color:"#78350F" }}>
                  <span style={{ color:C.red, fontWeight:700 }}>✗</span> {item}
                </div>
              ))}
            </div>
          </div>

          {phase === "idle" && (
            <button onClick={() => setPhase("confirm")}
              style={{ background:C.red, color:"#fff", border:"none", borderRadius:10,
                padding:"11px 28px", fontSize:14, fontWeight:700, cursor:"pointer",
                display:"flex", alignItems:"center", gap:8 }}>
              🗑 Clear All Data
            </button>
          )}

          {phase === "confirm" && (
            <div style={{ background:"#FFF1F2", border:`1px solid #FECACA`, borderRadius:12, padding:20 }}>
              <div style={{ fontSize:14, fontWeight:700, color:"#991B1B", marginBottom:8 }}>
                Confirm Destructive Action
              </div>
              <div style={{ fontSize:13, color:C.text, marginBottom:14, lineHeight:1.6 }}>
                This action <strong>cannot be undone</strong>. Type{" "}
                <strong style={{ color:C.red }}>{CONFIRM_PHRASE}</strong> to continue:
              </div>
              <input value={confirmTxt} onChange={e => setConfirmTxt(e.target.value)}
                placeholder={CONFIRM_PHRASE}
                style={{ border:`2px solid ${confirmTxt === CONFIRM_PHRASE ? C.red : C.border}`,
                  borderRadius:8, padding:"10px 14px", fontSize:13, width:"100%",
                  outline:"none", boxSizing:"border-box", marginBottom:14,
                  fontFamily:"monospace", color:C.text,
                  background: confirmTxt === CONFIRM_PHRASE ? "#FFF1F2" : C.bg }} />
              <div style={{ display:"flex", gap:10 }}>
                <button disabled={confirmTxt !== CONFIRM_PHRASE} onClick={handleWipe}
                  style={{ background: confirmTxt === CONFIRM_PHRASE ? C.red : "#FCA5A5",
                    color:"#fff", border:"none", borderRadius:8, padding:"10px 22px",
                    fontSize:13, fontWeight:700,
                    cursor: confirmTxt === CONFIRM_PHRASE ? "pointer" : "default" }}>
                  ✗ Permanently Delete All Data
                </button>
                <button onClick={reset}
                  style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:8,
                    padding:"10px 22px", fontSize:13, fontWeight:600, cursor:"pointer", color:C.muted }}>
                  Cancel
                </button>
              </div>
            </div>
          )}

          {phase === "wiping" && (
            <div style={{ display:"flex", alignItems:"center", gap:14, padding:"16px 20px",
              background:"#FFF7ED", border:`1px solid #FED7AA`, borderRadius:10 }}>
              <div style={{ width:24, height:24, border:`3px solid ${C.amber}`,
                borderTop:"3px solid transparent", borderRadius:"50%",
                animation:"spin 0.8s linear infinite" }} />
              <div>
                <div style={{ fontSize:14, fontWeight:700, color:"#92400E" }}>Wiping data…</div>
                <div style={{ fontSize:12, color:C.muted, marginTop:2 }}>
                  Deleting all audit cases, policies, and related records from the database.
                </div>
              </div>
            </div>
          )}

          {phase === "done" && wipeResult && (
            <div style={{ background:"#F0FDF4", border:`1px solid #86EFAC`, borderRadius:12, padding:20 }}>
              <div style={{ fontSize:15, fontWeight:800, color:"#15803D", marginBottom:10 }}>
                ✓ Data cleared successfully
              </div>
              <div style={{ display:"flex", gap:12, flexWrap:"wrap", marginBottom:14 }}>
                {[
                  { label:"Audit Cases", value: wipeResult.deleted_cases    ?? 0 },
                  { label:"Policies",    value: wipeResult.deleted_policies  ?? 0 },
                  { label:"Total Rows",  value: wipeResult.total_deleted     ?? 0 },
                ].map(({ label, value }) => (
                  <div key={label} style={{ background:C.card, border:`1px solid ${C.border}`,
                    borderRadius:8, padding:"10px 18px", textAlign:"center" }}>
                    <div style={{ fontSize:22, fontWeight:800, color:C.text }}>{value}</div>
                    <div style={{ fontSize:11, color:C.muted, fontWeight:600, textTransform:"uppercase" }}>{label}</div>
                  </div>
                ))}
              </div>
              <div style={{ fontSize:12, color:C.muted, marginBottom:14 }}>
                Completed at {new Date().toLocaleTimeString()}. The UI has been refreshed.
              </div>
              <button onClick={reset}
                style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:8,
                  padding:"8px 18px", fontSize:13, fontWeight:600, cursor:"pointer", color:C.muted }}>
                Close
              </button>
            </div>
          )}

          {phase === "error" && (
            <div style={{ background:"#FFF1F2", border:`1px solid #FECACA`, borderRadius:12, padding:20 }}>
              <div style={{ fontSize:14, fontWeight:800, color:"#991B1B", marginBottom:6 }}>
                ✗ Operation failed
              </div>
              <div style={{ fontSize:13, color:C.text, marginBottom:14,
                background:"#FEE2E2", padding:"10px 14px", borderRadius:8, fontFamily:"monospace" }}>
                {wipeErr}
              </div>
              <button onClick={reset}
                style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:8,
                  padding:"8px 18px", fontSize:13, fontWeight:600, cursor:"pointer", color:C.muted }}>
                Dismiss
              </button>
            </div>
          )}
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

// ── Reports Screen ────────────────────────────────────────────────────────────
function ReportsScreen({ cases }) {
  const completed = cases.filter(c => c.status === "completed");
  return (
    <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
      <div style={{ display:"flex", gap:16 }}>
        {[
          { title:"Variance Summary Report",    desc:"Total EST Exposure & Earned Exposure delta vs. EST YTD Premium across all policies", icon:"📊", color:C.accent },
          { title:"Audit Evidence Package",     desc:"Full evidence trail with narratives and source data",                                 icon:"📋", color:C.purple },
          { title:"High Risk Policy Report",    desc:"All policies above 20% variance threshold",                                          icon:"⚠️", color:C.red    },
          { title:"Class Code Analysis",        desc:"Misclassification rates by class code and composite rate",                           icon:"🔍", color:C.teal   },
        ].map((r, i) => (
          <div key={i} style={{ flex:1, background:C.card, border:`1px solid ${C.border}`,
            borderRadius:14, padding:20, cursor:"pointer", transition:"all 0.15s" }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = r.color; e.currentTarget.style.transform = "translateY(-2px)"; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.transform = "none"; }}>
            <div style={{ fontSize:32, marginBottom:12 }}>{r.icon}</div>
            <div style={{ fontSize:14, fontWeight:700, color:C.text, marginBottom:6 }}>{r.title}</div>
            <div style={{ fontSize:12, color:C.muted, lineHeight:1.5, marginBottom:14 }}>{r.desc}</div>
            <button style={{ background:r.color, color:"#fff", border:"none", borderRadius:7,
              padding:"7px 16px", fontSize:12, fontWeight:700, cursor:"pointer", width:"100%" }}>
              Generate →
            </button>
          </div>
        ))}
      </div>
 
      <div style={{ background:C.card, border:`1px solid ${C.border}`, borderRadius:14, padding:24 }}>
        <SectionHeader title="Completed Audits" sub="Download reports for finalised cases" />
        {completed.length === 0 ? (
          <div style={{ textAlign:"center", padding:40, color:C.muted, fontSize:14 }}>
            No completed audits yet.
          </div>
        ) : (
          <table style={{ width:"100%", borderCollapse:"collapse" }}>
            <thead>
              <tr style={{ borderBottom:`2px solid ${C.border}`, background:"#F8FAFD" }}>
                {["Policy Number","Risk","Variance %","Recommendation","Date","Actions"].map(h => (
                  <th key={h} style={{ padding:"10px 14px", textAlign:"left", fontSize:11,
                    color:C.muted, fontWeight:700, textTransform:"uppercase" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {completed.map(c => (
                <tr key={c.audit_case_id} style={{ borderBottom:`1px solid ${C.border}` }}>
                  <td style={{ padding:"13px 14px", fontSize:13, fontWeight:700, color:C.accent }}>
                    {c.policy_number}
                  </td>
                  <td style={{ padding:"13px 14px" }}><RiskBadge risk={c.risk_level} /></td>
                  <td style={{ padding:"13px 14px", fontSize:13, fontWeight:700,
                    color:(c.variance_pct || 0) > 10 ? C.red : C.green }}>
                    {Number(c.variance_pct || 0).toFixed(1)}%
                  </td>
                  <td style={{ padding:"13px 14px", fontSize:12, color:C.muted, textTransform:"capitalize" }}>
                    {c.recommendation?.replace("_"," ") || "—"}
                  </td>
                  <td style={{ padding:"13px 14px", fontSize:12, color:C.muted }}>
                    {new Date(c.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding:"13px 14px" }}>
                    <button onClick={() => downloadReport(c.audit_case_id)}
                      style={{ background:C.accent, color:"#fff", border:"none", borderRadius:6,
                        padding:"5px 12px", fontSize:12, fontWeight:600, cursor:"pointer" }}>
                      ⬇ Report
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
 
 
// ═══════════════════════════════════════════════════════════════════════════════
// MAIN APP SHELL
// ═══════════════════════════════════════════════════════════════════════════════
export default function WCAuditApp() {
  const [screen,       setScreen]       = useState("dashboard");
  const [selectedCase, setSelectedCase] = useState(null);
  const [collapsed,    setCollapsed]    = useState(false);
  const [notifOpen,    setNotifOpen]    = useState(false);
  const [cases,        setCases]        = useState([]);
  const [loadingCases, setLoadingCases] = useState(true);
  const [activeCaseId, setActiveCaseId] = useState(null);
  const [batchCaseIds, setBatchCaseIds] = useState([]);
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
    canViewAdministartion,
  } = useWCRoles();

  const allNavItems = [
    { id:"dashboard", label:"Dashboard",        icon:"⊞" ,visible:canViewDashboard},
    { id:"policies",  label:"Policies",          icon:"📋" ,visible:canViewPolicies},
    { id:"variance",  label:"Variance Analysis", icon:"📈" ,visible:canViewVariance},
    { id:"ai-audit",  label:"AI Audit",          icon:"🤖", visible:canViewAIAudit },
    { id:"reports",   label:"Reports",           icon:"📊",  visible: canViewReports },
    { id:"upload",    label:"Data Ingestion",       icon:"⬆",  visible: canUpload },
    {id:"Administration", label:"Administration", icon:"⚙", visible:canViewAdministartion}
  ];

  const navItems = allNavItems.filter(item =>
    item.visible === undefined || item.visible === true
  );

  useEffect(() => {
    const visibleIds = new Set(navItems.map(n => n.id));
    if (!visibleIds.has(screen) && screen !== "audit-detail") {
      setScreen("dashboard");
    }
  }, [navItems, screen]);
 
  const titles = {
    dashboard:      { title:"Dashboard",         sub:"Workers' Compensation Policy Audit Overview" },
    policies:       { title:"Policies",          sub:"Manage and review all active policy audits" },
    variance:       { title:"Variance Analysis", sub:"EST Exposure vs. Earned Exposure and EST YTD Premium vs. Earned Premium explorer" },
    "ai-audit":     { title:"AI Audit Engine",   sub:"Multi-agent LangGraph orchestration & analysis" },
    reports:        { title:"Reports",           sub:"Generate and export audit documentation" },
    upload:         { title:"Data Upload",       sub:"Ingest payroll submissions and policy files" },
    "audit-detail": { title:"Policy Review",     sub:"Detailed audit workflow and HITL decisions" },
    Administration: {title:"Adminstartion", sub:"To create users and to do configurations"}
  };
  const cur = titles[screen] || titles.dashboard;
 
  const refreshCases = useCallback(async () => {
    setLoadingCases(true);
    try {
      const data = await listAuditCases();
      setCases(data);
    } catch (err) {
      console.error("[WCAuditApp] Failed to load cases", err);
    } finally {
      setLoadingCases(false);
    }
  }, []);
 
  useEffect(() => { refreshCases(); }, [refreshCases]);
 
  const notifications = [
    ...cases.filter(c => c.status === "error").map(c => ({
      id:c.audit_case_id, type:"alert",
      msg:`Error in case ${c.policy_number}: ${c.errors || "unknown error"}`, time:"recent",
    })),
    ...cases.filter(c => c.hitl_required && c.status !== "completed").map(c => ({
      id:`h-${c.audit_case_id}`, type:"warning",
      msg:`HITL review required for ${c.policy_number}`, time:"pending",
    })),
    ...cases.filter(c => c.status === "completed").slice(0, 2).map(c => ({
      id:`d-${c.audit_case_id}`, type:"info",
      msg:`Audit completed for ${c.policy_number}`, time:"done",
    })),
  ].slice(0, 5);
 
  return (
    <div style={{ display:"flex", height:"100vh", fontFamily:"'DM Sans','Segoe UI',sans-serif",
      background:C.bg, overflow:"hidden" }}>
 
      {/* Sidebar */}
      <div style={{ width:collapsed ? 68 : 240, background:C.navy, display:"flex",
        flexDirection:"column", transition:"width 0.25s ease", flexShrink:0, overflow:"hidden" }}>
        <div style={{ padding:"24px 20px 20px", display:"flex", alignItems:"center", gap:12,
          borderBottom:"1px solid rgba(255,255,255,0.07)" }}>
          <div style={{ width:36, height:36,
            background:"linear-gradient(135deg, #1E6FD9, #0ABFBC)", borderRadius:10,
            display:"flex", alignItems:"center", justifyContent:"center", fontSize:18, flexShrink:0 }}>
            🛡
          </div>
          {!collapsed && (
            <div>
              <div style={{ color:"#fff", fontWeight:800, fontSize:14, lineHeight:1.2 }}>Workers' Comp</div>
              <div style={{ color:"rgba(255,255,255,0.45)", fontSize:11, fontWeight:500 }}>Audit Platform</div>
            </div>
          )}
        </div>
 
        <nav style={{ flex:1, padding:"16px 10px", overflow:"hidden" }}>
          {navItems.map(item => (
            <button key={item.id} onClick={() => setScreen(item.id)}
              style={{ display:"flex", alignItems:"center", gap:12, width:"100%",
                padding:"11px 12px", border:"none", borderRadius:10, cursor:"pointer", marginBottom:4,
                background: screen === item.id || (screen === "audit-detail" && item.id === "policies")
                  ? "rgba(30,111,217,0.25)" : "transparent",
                color: screen === item.id || (screen === "audit-detail" && item.id === "policies")
                  ? "#fff" : "rgba(255,255,255,0.55)",
                borderLeft: screen === item.id || (screen === "audit-detail" && item.id === "policies")
                  ? `3px solid ${C.accentLt}` : "3px solid transparent",
                transition:"all 0.15s", textAlign:"left" }}>
              <span style={{ fontSize:16, width:20, textAlign:"center", flexShrink:0 }}>{item.icon}</span>
              {!collapsed && <span style={{ fontSize:13, fontWeight:600, whiteSpace:"nowrap" }}>{item.label}</span>}
            </button>
          ))}
        </nav>
 
        <div style={{ padding:"12px 10px", borderTop:"1px solid rgba(255,255,255,0.07)" }}>
          <button onClick={() => setCollapsed(!collapsed)}
            style={{ display:"flex", alignItems:"center", gap:12, width:"100%", padding:"10px 12px",
              border:"none", borderRadius:10, cursor:"pointer", background:"transparent",
              color:"rgba(255,255,255,0.4)", transition:"all 0.15s" }}
            onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.06)"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
            <span style={{ fontSize:16 }}>{collapsed ? "▶" : "◀"}</span>
            {!collapsed && <span style={{ fontSize:12 }}>Collapse</span>}
          </button>
        </div>
      </div>
 
      {/* Main area */}
      <div style={{ flex:1, display:"flex", flexDirection:"column", overflow:"hidden" }}>
 
        {/* Topbar */}
        <div style={{ background:C.card, borderBottom:`1px solid ${C.border}`, padding:"0 28px",
          height:64, display:"flex", alignItems:"center", justifyContent:"space-between", flexShrink:0 }}>
          <div style={{ position:"relative" }}>
            <input placeholder="Search policy number, insured name, class code..."
              style={{ border:`1px solid ${C.border}`, borderRadius:10,
                padding:"8px 14px 8px 38px", fontSize:13, width:320, outline:"none",
                color:C.text, background:C.bg }} />
            <span style={{ position:"absolute", left:12, top:"50%", transform:"translateY(-50%)",
              color:C.muted, fontSize:14 }}>🔍</span>
          </div>
          <div style={{ display:"flex", alignItems:"center", gap:16 }}>
 
            {/* Notifications */}
            <div style={{ position:"relative" }}>
              <button onClick={() => setNotifOpen(!notifOpen)}
                style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:10,
                  width:38, height:38, cursor:"pointer", fontSize:16, position:"relative" }}>
                🔔
                {notifications.length > 0 && (
                  <span style={{ position:"absolute", top:2, right:2, width:16, height:16,
                    background:C.red, borderRadius:"50%", fontSize:9, color:"#fff",
                    display:"flex", alignItems:"center", justifyContent:"center", fontWeight:700 }}>
                    {notifications.length}
                  </span>
                )}
              </button>
              {notifOpen && (
                <div style={{ position:"absolute", right:0, top:48, width:340, background:C.card,
                  border:`1px solid ${C.border}`, borderRadius:12,
                  boxShadow:"0 8px 32px rgba(0,0,0,0.12)", zIndex:100 }}>
                  <div style={{ padding:"14px 18px", borderBottom:`1px solid ${C.border}`,
                    fontWeight:700, fontSize:14, color:C.text }}>Notifications</div>
                  {notifications.length === 0 ? (
                    <div style={{ padding:"20px 18px", color:C.muted, fontSize:13 }}>No new notifications</div>
                  ) : notifications.map((n, i) => (
                    <div key={i} style={{ padding:"12px 18px", borderBottom:`1px solid ${C.border}`,
                      display:"flex", gap:10 }}>
                      <span>{n.type === "alert" ? "🔴" : n.type === "warning" ? "🟡" : "🔵"}</span>
                      <div>
                        <div style={{ fontSize:12, color:C.text, lineHeight:1.4 }}>{n.msg}</div>
                        <div style={{ fontSize:11, color:C.muted, marginTop:3 }}>{n.time}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
 
            {/* <button style={{ background:C.bg, border:`1px solid ${C.border}`, borderRadius:10,
              padding:"8px 16px", fontSize:13, cursor:"pointer", color:C.muted, fontWeight:600 }}>
              ⬇ Export
            </button>
 
            <button onClick={() => setScreen("upload")}
              style={{ background:C.accent, color:"#fff", border:"none", borderRadius:10,
                padding:"8px 18px", fontSize:13, fontWeight:700, cursor:"pointer" }}>
              + New Audit
            </button> */}
 
            <div style={{ display:"flex", alignItems:"center", gap:10 }}>
              <div style={{ width:36, height:36, borderRadius:"50%",
                background:"linear-gradient(135deg, #1E6FD9, #0ABFBC)",
                display:"flex", alignItems:"center", justifyContent:"center",
                color:"#fff", fontWeight:700, fontSize:14 }}>WC</div>
              <div>
                <div style={{ fontSize:13, fontWeight:700, color:C.text }}>WC Auditor</div>
                <div style={{ fontSize:11, color:C.muted }}>Senior Analyst</div>
              </div>
            </div>
          </div>
        </div>
 
        {/* Page header */}
        <div style={{ background:C.card, borderBottom:`1px solid ${C.border}`,
          padding:"16px 28px", flexShrink:0 }}>
          <h1 style={{ margin:0, fontSize:20, fontWeight:800, color:C.text }}>{cur.title}</h1>
          <p style={{ margin:"4px 0 0", fontSize:13, color:C.muted }}>{cur.sub}</p>
        </div>
 
        {/* Content */}
        <div style={{ flex:1, overflowY:"auto", padding:24 }}>
          {screen === "dashboard" && (
            <Dashboard setScreen={setScreen} setSelectedCase={setSelectedCase} cases={cases} />
          )}
          {screen === "policies" && (
            <PoliciesScreen setScreen={setScreen} setSelectedCase={setSelectedCase}
              cases={cases} onRefresh={refreshCases} />
          )}
          {screen === "variance" && <VarianceAnalysis cases={cases} />}
          {/* {screen === "ai-audit" && (
            <AIAuditScreen cases={cases} onCaseCreated={refreshCases} activeCaseId={activeCaseId} />
          )} */}

          {screen === "ai-audit" && (
         <AIAuditScreen
           cases={cases}
           onCaseCreated={refreshCases}
           activeCaseId={activeCaseId}
           batchCaseIds={batchCaseIds}
         />
       )}
          {/* {screen === "reports" && <ReportsScreen cases={cases} />} */}
          {screen === "reports"      && (
            canViewReports
              ? <ReportsScreen cases={cases} />
              : <AccessDenied requiredRole="Provider or above" />
          )}
          {/* {screen === "upload" && (
            <DataUpload onAuditStarted={(id) => {
              setActiveCaseId(id);
              refreshCases();
              setScreen("ai-audit");
            }} />
          )} */}
          {screen === "upload" && (
         <DataUpload
           onAuditStarted={(id) => {
             setActiveCaseId(id);
             refreshCases();
             setScreen("ai-audit");
           }}
           onBatchStarted={(ids) => {
             setBatchCaseIds(ids);
             refreshCases();
             setScreen("ai-audit");
           }}
         />
       )}
          {screen === "Administration" && (
            isSuperAdmin
              ? <Administration setScreen={setScreen} onDataCleared={refreshCases} />
              : <AccessDenied requiredRole="Super Admin" />
          )}
          {screen === "audit-detail" && (
            <AuditDetail auditCase={selectedCase} setScreen={setScreen}
              onHITLDecision={refreshCases} />
          )}
        </div>
      </div>
 
      {/* Notification overlay */}
      {notifOpen && (
        <div onClick={() => setNotifOpen(false)}
          style={{ position:"fixed", inset:0, zIndex:99 }} />
      )}
    </div>
  );
}
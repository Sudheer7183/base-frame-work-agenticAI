// // frontend/react-admin/src/pages/WCAudit/carrier-portal/pages/PolicyList.tsx
// // Inline styles only — no Tailwind.

// import { useState, useMemo } from 'react'
// import { useNavigate } from 'react-router-dom'
// import { StatusBadge, RiskBadge, AuditBadge } from '../components/Badges'
// import { useCarrierPortalData } from '../CarrierPortalContext'
// import { C, cardStyle, tableThStyle, tableTdStyle } from '../styles'
// import type { PolicyStatus, RiskLevel } from '../types'

// const BASE = '/admin/wc-audit/carrier-portal'

// const fmt = (n: number) =>
//   new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)

// type SortKey =
//   | 'policyNumber' | 'insuredName' | 'state' | 'effectiveDate'
//   | 'policyStatus' | 'estPremium'  | 'variance' | 'variancePercent'
//   | 'risk'         | 'auditStatus'

// const RISK_ORDER:   Record<RiskLevel,    number> = { High: 0, Medium: 1, Low: 2 }
// const STATUS_ORDER: Record<PolicyStatus, number> = { Active: 0, 'Pending Cancel': 1, Cancelled: 2, Expired: 3 }

// export default function PolicyList() {
//   const navigate = useNavigate()
//   const { policies, targetVariance } = useCarrierPortalData()

//   const [search,       setSearch]       = useState('')
//   const [statusFilter, setStatusFilter] = useState<string>('All')
//   const [riskFilter,   setRiskFilter]   = useState<string>('All')
//   const [stateFilter,  setStateFilter]  = useState<string>('All')
//   const [sortKey,      setSortKey]      = useState<SortKey>('policyNumber')
//   const [sortDir,      setSortDir]      = useState<'asc' | 'desc'>('asc')

//   const stateOptions = useMemo(() => {
//     const states = Array.from(new Set(policies.map(p => p.state))).sort()
//     return ['All', ...states]
//   }, [policies])


//   const handleSort = (key: SortKey) => {
//     if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
//     else { setSortKey(key); setSortDir('asc') }
//   }

//   const filtered = useMemo(() => {
//     let result = policies.filter(p => {
//       const q = search.toLowerCase()
//       return (
//         (!q || p.policyNumber.toLowerCase().includes(q) || p.insuredName.toLowerCase().includes(q) || p.state.toLowerCase().includes(q)) &&
//         (statusFilter === 'All' || p.policyStatus === statusFilter) &&
//         (riskFilter   === 'All' || p.risk         === riskFilter) &&
//         (stateFilter  === 'All' || p.state        === stateFilter)
//       )
//     })
//     return [...result].sort((a, b) => {
//       let cmp = 0
//       switch (sortKey) {
//         case 'policyNumber':    cmp = a.policyNumber.localeCompare(b.policyNumber); break
//         case 'insuredName':     cmp = a.insuredName.localeCompare(b.insuredName);   break
//         case 'state':           cmp = a.state.localeCompare(b.state);               break
//         case 'effectiveDate':   cmp = a.effectiveDate.localeCompare(b.effectiveDate); break
//         case 'policyStatus':    cmp = STATUS_ORDER[a.policyStatus] - STATUS_ORDER[b.policyStatus]; break
//         case 'estPremium':      cmp = a.estPremium      - b.estPremium;      break
//         case 'variance':        cmp = a.variance        - b.variance;        break
//         case 'variancePercent': cmp = a.variancePercent - b.variancePercent; break
//         case 'risk':            cmp = RISK_ORDER[a.risk] - RISK_ORDER[b.risk]; break
//         case 'auditStatus':     cmp = a.auditStatus.localeCompare(b.auditStatus); break
//       }
//       return sortDir === 'asc' ? cmp : -cmp
//     })
//   }, [policies, search, statusFilter, riskFilter,stateFilter, sortKey, sortDir])

//   const thSort = (col: SortKey, label: string, right = false) => (
//     <th
//       key={col}
//       onClick={() => handleSort(col)}
//       style={{ ...tableThStyle, textAlign: right ? 'right' : 'left', cursor: 'pointer', userSelect: 'none' }}
//     >
//       {label}{' '}
//       <span style={{ opacity: 0.5 }}>
//         {sortKey === col ? (sortDir === 'asc' ? '▲' : '▼') : '⇅'}
//       </span>
//     </th>
//   )

//   const inputStyle: React.CSSProperties = {
//     padding: '8px 12px', fontSize: 13, border: `1px solid ${C.border}`,
//     borderRadius: 8, outline: 'none', background: '#fff', color: C.text,
//   }

//   const selectStyle: React.CSSProperties = {
//     ...inputStyle, cursor: 'pointer',
//   }

//   return (
//     <div style={{ minHeight: '100vh', background: C.bg }}>
//       <main style={{ maxWidth: 1600, margin: '0 auto', padding: '28px 28px', display: 'flex', flexDirection: 'column', gap: 20 }}>

//         {/* Breadcrumb */}
//         <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
//           <button
//             onClick={() => navigate(`${BASE}/dashboard`)}
//             style={{ background: 'none', border: 'none', color: C.muted, fontSize: 13, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
//           >
//             <svg width={16} height={16} fill="none" viewBox="0 0 24 24" stroke="currentColor">
//               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
//             </svg>
//             Dashboard
//           </button>
//           <span style={{ color: C.border }}>/</span>
//           <h1 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: C.text }}>All Policies</h1>
//         </div>

//         {/* Filters */}
//         <div style={{ ...cardStyle, display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 14 }}>
//           <input
//             type="text"
//             placeholder="Search by policy #, insured name,"
//             value={search}
//             onChange={e => setSearch(e.target.value)}
//             style={{ ...inputStyle, flex: 1, minWidth: 240 }}
//           />
//           <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
//             <label style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.8, color: C.muted }}>Status</label>
//             <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={selectStyle}>
//               {['All', 'Active', 'Pending Cancel', 'Cancelled', 'Expired'].map(s => <option key={s}>{s}</option>)}
//             </select>
//           </div>
//           <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
//             <label style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.8, color: C.muted }}>Risk</label>
//             <select value={riskFilter} onChange={e => setRiskFilter(e.target.value)} style={selectStyle}>
//               {['All', 'High', 'Medium', 'Low'].map(r => <option key={r}>{r}</option>)}
//             </select>
//           </div>
//           <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
//             <label style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.8, color: C.muted }}>State</label>
//             <select value={stateFilter} onChange={e => setStateFilter(e.target.value)} style={selectStyle}>
//               {stateOptions.map(s => <option key={s}>{s}</option>)}
//             </select>
//           </div>
//           <div style={{ marginLeft: 'auto', fontSize: 13, color: C.muted }}>
//             <span style={{ fontWeight: 700, color: C.text }}>{filtered.length}</span> of {policies.length} policies
//           </div>
//         </div>

//         {/* Table */}
//         <div style={{ ...cardStyle, padding: 0, overflow: 'hidden' }}>
//           <div style={{ overflowX: 'auto' }}>
//             <table style={{ width: '100%', borderCollapse: 'collapse' }}>
//               <thead>
//                 <tr>
//                   {thSort('policyNumber',    'Policy #')}
//                   {thSort('insuredName',     'Insured Name')}
//                   {thSort('state',           'St.')}
//                   {thSort('effectiveDate',   'Effective Date')}
//                   {thSort('policyStatus',    'Status')}
//                   {thSort('estPremium',      'Est. Premium',  true)}
//                   {thSort('variance',        'Variance $',    true)}
//                   {thSort('variancePercent', 'Var %',         true)}
//                   {thSort('risk',            'Risk')}
//                   {thSort('auditStatus',     'Audit Status')}
//                   <th style={tableThStyle}>Actions</th>
//                 </tr>
//               </thead>
//               <tbody>
//                 {filtered.length === 0 && (
//                   <tr>
//                     <td colSpan={11} style={{ textAlign: 'center', padding: 48, color: C.muted, fontSize: 14 }}>
//                       No policies match your filters.
//                     </td>
//                   </tr>
//                 )}
//                 {filtered.map((p, i) => (
//                   <tr key={`${p.policyNumber}-${i}`} style={{ background: i % 2 === 1 ? '#F8FAFD' : '#fff' }}>
//                     <td style={{ ...tableTdStyle, fontFamily: 'monospace', fontWeight: 700, color: C.navy }}>{p.policyNumber}</td>
//                     <td style={{ ...tableTdStyle, fontWeight: 600 }}>{p.insuredName}</td>
//                     <td style={{ ...tableTdStyle, textAlign: 'center' }}>{p.state}</td>
//                     <td style={tableTdStyle}>{p.effectiveDate || '—'}</td>
//                     <td style={tableTdStyle}><StatusBadge status={p.policyStatus} /></td>
//                     <td style={{ ...tableTdStyle, textAlign: 'right', fontWeight: 600 }}>{fmt(p.estPremium)}</td>
//                     <td style={{ ...tableTdStyle, textAlign: 'right', fontWeight: 700, color: p.variance >= 0 ? C.red : C.green }}>
//                       {p.variance >= 0 ? '+' : ''}{fmt(p.variance)}
//                     </td>
//                     <td style={{ ...tableTdStyle, textAlign: 'right', fontWeight: 700, color: Math.abs(p.variancePercent) > targetVariance.threshold ? C.red : C.text }}>
//                       {p.variancePercent > 0 ? '+' : ''}{p.variancePercent.toFixed(1)}%
//                     </td>
//                     <td style={tableTdStyle}><RiskBadge risk={p.risk} /></td>
//                     <td style={tableTdStyle}><AuditBadge status={p.auditStatus} /></td>
//                     <td style={tableTdStyle}>
//                       <button
//                         onClick={() => navigate(`${BASE}/policies/${encodeURIComponent(p.policyNumber)}`)}
//                         style={{
//                           background: C.navy, color: '#fff', border: 'none', borderRadius: 6,
//                           padding: '5px 12px', fontSize: 12, fontWeight: 600, cursor: 'pointer',
//                         }}
//                       >
//                         Review
//                       </button>
//                     </td>
//                   </tr>
//                 ))}
//               </tbody>
//             </table>
//           </div>
//         </div>

//       </main>
//     </div>
//   )
// }

// frontend/react-admin/src/pages/WCAudit/carrier-portal/pages/PolicyList.tsx
// Inline styles only — no Tailwind.

import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { StatusBadge, RiskBadge, AuditBadge } from '../components/Badges'
import { useCarrierPortalData } from '../CarrierPortalContext'
import { C, cardStyle, tableThStyle, tableTdStyle } from '../styles'
import type { PolicyStatus, RiskLevel } from '../types'

const BASE = '/admin/wc-audit/carrier-portal'

const fmt = (n: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)

type SortKey =
  | 'policyNumber' | 'insuredName' | 'state' | 'effectiveDate'
  | 'policyStatus' | 'estPremium'  | 'variance' | 'variancePercent'
  | 'risk'         | 'auditStatus'

const RISK_ORDER:   Record<RiskLevel,    number> = { High: 0, Medium: 1, Low: 2 }
const STATUS_ORDER: Record<PolicyStatus, number> = { Active: 0, 'Pending Cancel': 1, Cancelled: 2, Expired: 3 }

export default function PolicyList() {
  const navigate = useNavigate()
  const { policies, targetVariance } = useCarrierPortalData()

  const [search,       setSearch]       = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('All')
  const [riskFilter,   setRiskFilter]   = useState<string>('All')
  const [stateFilter,  setStateFilter]  = useState<string>('All')
  const [sortKey,      setSortKey]      = useState<SortKey>('policyNumber')
  const [sortDir,      setSortDir]      = useState<'asc' | 'desc'>('asc')

  const stateOptions = useMemo(() => {
    const states = Array.from(new Set(policies.map(p => p.state))).sort()
    return ['All', ...states]
  }, [policies])


  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  const filtered = useMemo(() => {
    let result = policies.filter(p => {
      const q = search.toLowerCase()
      return (
        (!q || p.policyNumber.toLowerCase().includes(q) || p.insuredName.toLowerCase().includes(q) || p.state.toLowerCase().includes(q)) &&
        (statusFilter === 'All' || p.policyStatus === statusFilter) &&
        (riskFilter   === 'All' || p.risk         === riskFilter) &&
        (stateFilter  === 'All' || p.state        === stateFilter)
      )
    })
    return [...result].sort((a, b) => {
      let cmp = 0
      switch (sortKey) {
        case 'policyNumber':    cmp = a.policyNumber.localeCompare(b.policyNumber); break
        case 'insuredName':     cmp = a.insuredName.localeCompare(b.insuredName);   break
        case 'state':           cmp = a.state.localeCompare(b.state);               break
        case 'effectiveDate':   cmp = a.effectiveDate.localeCompare(b.effectiveDate); break
        case 'policyStatus':    cmp = STATUS_ORDER[a.policyStatus] - STATUS_ORDER[b.policyStatus]; break
        case 'estPremium':      cmp = a.estPremium      - b.estPremium;      break
        case 'variance':        cmp = a.variance        - b.variance;        break
        case 'variancePercent': cmp = a.variancePercent - b.variancePercent; break
        case 'risk':            cmp = RISK_ORDER[a.risk] - RISK_ORDER[b.risk]; break
        case 'auditStatus':     cmp = a.auditStatus.localeCompare(b.auditStatus); break
      }
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [policies, search, statusFilter, riskFilter,stateFilter, sortKey, sortDir])

  const thSort = (col: SortKey, label: string, right = false) => (
    <th
      key={col}
      onClick={() => handleSort(col)}
      style={{ ...tableThStyle, textAlign: right ? 'right' : 'left', cursor: 'pointer', userSelect: 'none' }}
    >
      {label}{' '}
      <span style={{ opacity: 0.5 }}>
        {sortKey === col ? (sortDir === 'asc' ? '▲' : '▼') : '⇅'}
      </span>
    </th>
  )

  const inputStyle: React.CSSProperties = {
    padding: '8px 12px', fontSize: 13, border: `1px solid ${C.border}`,
    borderRadius: 8, outline: 'none', background: '#fff', color: C.text,
  }

  const selectStyle: React.CSSProperties = {
    ...inputStyle, cursor: 'pointer',
  }
  const formatDate = (dateStr: string) => {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
                .replace(/ /g, '-');
  };
  const lastAuditDate = useMemo(() => {
      if (!policies.length) return null;
      const latest = policies.reduce((max: any, p: any) =>
        new Date(p.completed_at) > new Date(max.completed_at) ? p : max
      );
      return latest.completed_at ? formatDate(latest.completed_at) : null;
  }, [policies]);
  return (
    <div style={{ minHeight: '100vh', background: C.bg }}>
      <main style={{ maxWidth: 1600, margin: '0 auto', padding: '28px 28px', display: 'flex', flexDirection: 'column', gap: 20 }}>

        {/* Breadcrumb */}
        {/* <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            onClick={() => navigate(`${BASE}/dashboard`)}
            style={{ background: 'none', border: 'none', color: C.muted, fontSize: 13, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
          >
            <svg width={16} height={16} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Dashboard
          </button>
          <span style={{ color: C.border }}>/</span>
          <h1 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: C.text }}>All Policies</h1>
        </div> */}

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <button
              onClick={() => navigate(`${BASE}/dashboard`)}
              style={{ background: 'none', border: 'none', color: C.muted, fontSize: 13, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
            >
              <svg width={16} height={16} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Dashboard
            </button>
            <span style={{ color: C.border }}>/</span>
            <h1 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: C.text }}>All Policies</h1>
          </div>

          <p style={{ margin: 0, fontSize: 13, color: C.muted }}>
             <strong style={{ color: C.text }}>Last Audit Run Date:{lastAuditDate ?? '—'}</strong>
          </p>
        </div>

        {/* Filters */}
        <div style={{ ...cardStyle, display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 14 }}>
          <input
            type="text"
            placeholder="Search by policy #, insured name,"
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ ...inputStyle, flex: 1, minWidth: 240 }}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <label style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.8, color: C.muted }}>Status</label>
            <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={selectStyle}>
              {['All', 'Active', 'Pending Cancel', 'Cancelled', 'Expired'].map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <label style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.8, color: C.muted }}>Risk</label>
            <select value={riskFilter} onChange={e => setRiskFilter(e.target.value)} style={selectStyle}>
              {['All', 'High', 'Medium', 'Low'].map(r => <option key={r}>{r}</option>)}
            </select>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <label style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.8, color: C.muted }}>State</label>
            <select value={stateFilter} onChange={e => setStateFilter(e.target.value)} style={selectStyle}>
              {stateOptions.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
          <div style={{ marginLeft: 'auto', fontSize: 13, color: C.muted }}>
            <span style={{ fontWeight: 700, color: C.text }}>{filtered.length}</span> of {policies.length} policies
          </div>
        </div>

        {/* Table */}
        <div style={{ ...cardStyle, padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {thSort('policyNumber',    'Policy #')}
                  {thSort('insuredName',     'Insured Name')}
                  {thSort('state',           'St.')}
                  {thSort('effectiveDate',   'Effective Date')}
                  {thSort('policyStatus',    'Status')}
                  {thSort('estPremium',      'Est. Premium',  true)}
                  {thSort('variance',        'Variance $',    true)}
                  {thSort('variancePercent', 'Var %',         true)}
                  {thSort('risk',            'Risk')}
                  {thSort('auditStatus',     'Audit Status')}
                  <th style={tableThStyle}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={11} style={{ textAlign: 'center', padding: 48, color: C.muted, fontSize: 14 }}>
                      No policies match your filters.
                    </td>
                  </tr>
                )}
                {filtered.map((p, i) => (
                  <tr key={`${p.policyNumber}-${i}`} style={{ background: i % 2 === 1 ? '#F8FAFD' : '#fff' }}>
                    <td style={{ ...tableTdStyle, fontFamily: 'monospace', fontWeight: 700, color: C.navy }}>{p.policyNumber}</td>
                    <td style={{ ...tableTdStyle, fontWeight: 600 }}>{p.insuredName}</td>
                    <td style={{ ...tableTdStyle, textAlign: 'center' }}>{p.state}</td>
                    <td style={tableTdStyle}>{p.effectiveDate || '—'}</td>
                    <td style={tableTdStyle}><StatusBadge status={p.policyStatus} /></td>
                    <td style={{ ...tableTdStyle, textAlign: 'right', fontWeight: 600 }}>{fmt(p.estPremium)}</td>
                    <td style={{ ...tableTdStyle, textAlign: 'right', fontWeight: 700, color: p.variance >= 0 ? C.red : C.green }}>
                      {p.variance >= 0 ? '+' : ''}{fmt(p.variance)}
                    </td>
                    <td style={{ ...tableTdStyle, textAlign: 'right', fontWeight: 700, color: Math.abs(p.variancePercent) > targetVariance.threshold ? C.red : C.text }}>
                      {p.variancePercent > 0 ? '+' : ''}{p.variancePercent.toFixed(1)}%
                    </td>
                    <td style={tableTdStyle}><RiskBadge risk={p.risk} /></td>
                    <td style={tableTdStyle}><AuditBadge status={p.auditStatus} /></td>
                    <td style={tableTdStyle}>
                      <button
                        onClick={() => navigate(`${BASE}/policies/${encodeURIComponent(p.policyNumber)}`)}
                        style={{
                          background: C.navy, color: '#fff', border: 'none', borderRadius: 6,
                          padding: '5px 12px', fontSize: 12, fontWeight: 600, cursor: 'pointer',
                        }}
                      >
                        Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </main>
    </div>
  )
}


import { useState, useMemo, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import { StatusBadge, RiskBadge, AuditBadge } from '../components/Badges'
import { useCarrierPortalData }  from '../CarrierPortalContext'
import { C, cardStyle, sectionHeadingStyle, tableThStyle, tableTdStyle } from '../styles'

const BASE = '/admin/wc-audit/carrier-portal'

const fmt = (n: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)

const fmtPct = (n: number) => `${n > 0 ? '+' : ''}${n.toFixed(1)}%`

const RADIAN = Math.PI / 180

const PieLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" fontSize={12}>
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

// ── State multi-select dropdown ──────────────────────────────────────────────
function StateMultiSelect({
  allStates,
  selected,
  onChange,
}: {
  allStates: string[]
  selected: Set<string>
  onChange: (next: Set<string>) => void
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const allSelected = selected.size === allStates.length

  const toggle = (state: string) => {
    const next = new Set(selected)
    next.has(state) ? next.delete(state) : next.add(state)
    if (next.size > 0) onChange(next)
  }

  const toggleAll = () => {
    onChange(allSelected ? new Set([allStates[0]]) : new Set(allStates))
  }

  const label = allSelected
    ? 'All States'
    : selected.size === 1
    ? [...selected][0]
    : `${selected.size} states`

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '5px 10px', fontSize: 12, fontWeight: 600,
          background: '#fff', border: `1px solid ${C.border}`, borderRadius: 8,
          color: C.text, cursor: 'pointer', whiteSpace: 'nowrap',
        }}
      >
        <svg width={13} height={13} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2a1 1 0 01-.293.707L13 13.414V19a1 1 0 01-.553.894l-4 2A1 1 0 017 21v-7.586L3.293 6.707A1 1 0 013 6V4z" />
        </svg>
        {label}
        <svg width={12} height={12} fill="none" viewBox="0 0 24 24" stroke="currentColor"
          style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s' }}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 4px)', right: 0, zIndex: 100,
          background: '#fff', border: `1px solid ${C.border}`, borderRadius: 10,
          boxShadow: '0 8px 24px rgba(0,0,0,0.12)', padding: '6px 0',
          minWidth: 160, maxHeight: 260, overflowY: 'auto',
        }}>
          {/* Select all */}
          <div
            onClick={toggleAll}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '6px 12px', cursor: 'pointer', fontSize: 12, fontWeight: 700,
              borderBottom: `1px solid ${C.border}`, color: C.text,
            }}
          >
            <span style={{
              width: 14, height: 14, borderRadius: 4, border: `1.5px solid ${C.border}`,
              background: allSelected ? C.navy : '#fff',
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            }}>
              {allSelected && (
                <svg width={9} height={9} viewBox="0 0 10 10" fill="none">
                  <path d="M1.5 5l2.5 2.5 4.5-4.5" stroke="#fff" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </span>
            All States
          </div>

          {/* Individual states */}
          {allStates.map(state => {
            const checked = selected.has(state)
            return (
              <div
                key={state}
                onClick={() => toggle(state)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: '6px 12px', cursor: 'pointer', fontSize: 12,
                  color: C.text, background: checked ? '#F0F4FF' : '#fff',
                }}
              >
                <span style={{
                  width: 14, height: 14, borderRadius: 4,
                  border: `1.5px solid ${checked ? C.navy : C.border}`,
                  background: checked ? C.navy : '#fff',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                }}>
                  {checked && (
                    <svg width={9} height={9} viewBox="0 0 10 10" fill="none">
                      <path d="M1.5 5l2.5 2.5 4.5-4.5" stroke="#fff" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </span>
                {state}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
// ─────────────────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const navigate = useNavigate()
  const { policies, bookSummary, statusDistribution, riskDistribution, stateRiskData, targetVariance } =
    useCarrierPortalData()

  // Derive state list from stateRiskData
  const allStates = useMemo(
    () => stateRiskData.map((d: any) => d.state as string),
    [stateRiskData],
  )

  const [selectedStates, setSelectedStates] = useState<Set<string>>(() => new Set(allStates))

  // Keep in sync if data reloads
  useEffect(() => {
    setSelectedStates(new Set(allStates))
  }, [allStates.join(',')])

  const filteredStateRiskData = useMemo(
    () => stateRiskData.filter((d: any) => selectedStates.has(d.state)),
    [stateRiskData, selectedStates],
  )

  const activePolicies = policies.filter(
    p => p.policyStatus === 'Active' || p.policyStatus === 'Pending Cancel',
  )

  const varPos = bookSummary.variance >= 0
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
      <main style={{ maxWidth: 1600, margin: '0 auto', padding: '28px 28px', display: 'flex', flexDirection: 'column', gap: 24 }}>

        {/* ── Title bar ── */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: C.text }}>Policy Book Dashboard</h1>
            <p style={{ margin: '4px 0 0', fontSize: 13, color: C.muted }}>
              Live audit data · {policies.length} cases loaded
            </p>
          </div>
          {/* <button
            onClick={() => navigate(`${BASE}/policies`)}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              background: C.navy, color: '#fff', border: 'none', borderRadius: 10,
              padding: '10px 20px', fontSize: 13, fontWeight: 700, cursor: 'pointer',
            }}
          >
            View All Policies
            <svg width={16} height={16} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </button> */}
          <span style={{ fontWeight: 800 }}>
            Last Audit Run Date: {lastAuditDate ?? '—'}
          </span>
        </div>

        {/* ── KPI cards ── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
          {[
            { label: 'Total Active Book Premium',      value: fmt(bookSummary.totalActiveBookPremium),   sub: 'Active & pending policies',   color: C.text },
            { label: 'Actual Earned Premium to Date',  value: fmt(bookSummary.totalActualEarnedPremium), sub: 'Audit-confirmed actual',        color: C.text },
            { label: 'Est. Earned Premium to Date',    value: fmt(bookSummary.totalEstEarnedPremium),    sub: 'Pro-rated estimated',          color: C.text },

            // { label: 'Actual Earned Premium to Date',  value: fmt(bookSummary.totalActualEarnedPremium), sub: 'Audit-confirmed actual',        color: C.text },
            {
              label: 'Variance – Actual vs. Estimated',
              value: (varPos ? '+' : '') + fmt(bookSummary.variance),
              sub: bookSummary.totalEstEarnedPremium > 0
                ? fmtPct((bookSummary.variance / bookSummary.totalEstEarnedPremium) * 100) + ' of est. earned'
                : '—',
              color: varPos ? C.green : C.red,
            },
          ].map(({ label, value, sub, color }) => (
            <div key={label} style={cardStyle}>
              <p style={{ margin: 0, fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.8, color: C.muted }}>{label}</p>
              <p style={{ margin: '8px 0 4px', fontSize: 22, fontWeight: 800, color }}>{value}</p>
              <p style={{ margin: 0, fontSize: 11, color: C.muted }}>{sub}</p>
            </div>
          ))}
        </div>

        {/* ── Charts row ── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>

          {/* Status Distribution */}
          <div style={cardStyle}>
            <p style={sectionHeadingStyle}>Policy Status Distribution</p>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={statusDistribution} cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                  labelLine={false} label={PieLabel} dataKey="value">
                  {statusDistribution.map(e => <Cell key={e.name} fill={e.color} />)}
                </Pie>
                <Tooltip formatter={(v: number) => [v, 'Policies']} />
                <Legend iconType="circle" iconSize={8} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 8 }}>
              {statusDistribution.map(s => (
                <div key={s.name} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  background: C.bg, borderRadius: 8, padding: '6px 12px',
                }}>
                  <span style={{ fontSize: 12, color: C.muted }}>{s.name}</span>
                  <span style={{ fontSize: 14, fontWeight: 700, color: C.text }}>{s.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Risk Distribution */}
          <div style={cardStyle}>
            <p style={sectionHeadingStyle}>Policy Risk Distribution</p>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={riskDistribution} cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                  labelLine={false} label={PieLabel} dataKey="value">
                  {riskDistribution.map(e => <Cell key={e.name} fill={e.color} />)}
                </Pie>
                <Tooltip formatter={(v: number) => [v, 'Policies']} />
                <Legend iconType="circle" iconSize={8} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ marginTop: 8, fontSize: 11, color: C.muted, textAlign: 'center' }}>Active &amp; Pending Cancel only</div>
            <div style={{ marginTop: 10, padding: '10px 14px', background: C.bg, borderRadius: 10, fontSize: 12, color: C.text, display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div><span style={{ fontWeight: 700, color: C.red }}>High</span> — &gt;{targetVariance.threshold}% variance AND missing payrolls</div>
              <div><span style={{ fontWeight: 700, color: C.amber }}>Medium</span> — Either condition present</div>
              <div><span style={{ fontWeight: 700, color: C.green }}>Low</span> — Neither condition</div>
            </div>
          </div>

          {/* State Risk — with multi-select filter */}
          <div style={cardStyle}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <p style={{ ...sectionHeadingStyle, margin: 0 }}>Policies by State &amp; Risk Profile</p>
              <StateMultiSelect
                allStates={allStates}
                selected={selectedStates}
                onChange={setSelectedStates}
              />
            </div>
            {filteredStateRiskData.length === 0 ? (
              <div style={{ height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center', color: C.muted, fontSize: 13 }}>
                No states selected.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={filteredStateRiskData} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                  <XAxis dataKey="state" tick={{ fontSize: 11 }} interval={0} angle={-45} textAnchor="end" />
                  <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
                  <Tooltip />
                  <Legend iconType="square" iconSize={10} />
                  <Bar dataKey="Low"    stackId="a" fill={C.green} radius={[0, 0, 0, 0]} />
                  <Bar dataKey="Medium" stackId="a" fill={C.amber} />
                  <Bar dataKey="High"   stackId="a" fill={C.red}   radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* ── Target Variance ── */}
        <div style={cardStyle}>
          <p style={sectionHeadingStyle}>Target Variance Policies — {targetVariance.threshold}% Threshold</p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

            {/* Over threshold */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 16,
              padding: 16, background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 12,
            }}>
              <div style={{
                width: 48, height: 48, borderRadius: '50%', background: '#FEE2E2', flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <svg width={22} height={22} fill="none" viewBox="0 0 24 24" stroke={C.red}>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                </svg>
              </div>
              <div>
                <p style={{ margin: 0, fontSize: 12, fontWeight: 600, color: '#991B1B' }}>
                  # of Policies Over {targetVariance.threshold}% Variance
                </p>
                <p style={{ margin: '4px 0', fontSize: 28, fontWeight: 800, color: '#991B1B' }}>
                  {targetVariance.over.count}
                </p>
                <p style={{ margin: 0, fontSize: 12, color: C.red }}>
                  $ Variance: {fmt(targetVariance.over.dollarVariance)}
                </p>
              </div>
            </div>

            {/* Under threshold */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 16,
              padding: 16, background: '#F0FDF4', border: '1px solid #BBF7D0', borderRadius: 12,
            }}>
              <div style={{
                width: 48, height: 48, borderRadius: '50%', background: '#D1FAE5', flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <svg width={22} height={22} fill="none" viewBox="0 0 24 24" stroke={C.green}>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p style={{ margin: 0, fontSize: 12, fontWeight: 600, color: '#065F46' }}>
                  # of Policies Under {targetVariance.threshold}% Variance
                </p>
                <p style={{ margin: '4px 0', fontSize: 28, fontWeight: 800, color: '#065F46' }}>
                  {targetVariance.under.count}
                </p>
                <p style={{ margin: 0, fontSize: 12, color: C.green }}>
                  $ Variance: {fmt(targetVariance.under.dollarVariance)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* ── Active Policy Table ── */}
        <div style={{ ...cardStyle, padding: 0, overflow: 'hidden' }}>
          <div style={{
            padding: '16px 20px', borderBottom: `1px solid ${C.border}`,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          }}>
            <div>
              <p style={{ margin: 0, fontWeight: 700, fontSize: 14, color: C.text }}>Active Policy Book</p>
              <p style={{ margin: '2px 0 0', fontSize: 12, color: C.muted }}>
                Showing {activePolicies.length} active &amp; pending policies
              </p>
            </div>
            {/* <button
              onClick={() => navigate(`${BASE}/policies`)}
              style={{ background: 'none', border: 'none', fontSize: 12, fontWeight: 700, color: C.accent, cursor: 'pointer' }}
            >
              View all {policies.length} policies →
            </button> */}
          <span style={{ fontWeight: 800 }}>
            Last Audit Run Date: {lastAuditDate ?? '—'}
          </span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {['Policy #', 'Insured Name', 'St.', 'Effective Date', 'Status',
                    'Est earned', 'Variance', 'Var %', 'Risk', 'Audit Status', 'Actions'].map(h => (
                    <th key={h} style={tableThStyle}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {activePolicies.map((p, i) => (
                  <tr key={p.policyNumber} style={{ background: i % 2 === 1 ? '#F8FAFD' : '#fff' }}>
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
                {activePolicies.length === 0 && (
                  <tr>
                    <td colSpan={11} style={{ textAlign: 'center', padding: 48, color: C.muted, fontSize: 14 }}>
                      No active policies found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

      </main>
    </div>
  )
}
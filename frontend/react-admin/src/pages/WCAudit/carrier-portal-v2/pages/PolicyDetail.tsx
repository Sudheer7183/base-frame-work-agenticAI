// frontend/react-admin/src/pages/WCAudit/carrier-portal/pages/PolicyDetail.tsx
// Matches the original uploaded design exactly. Inline styles — no Tailwind.

import { useParams, useNavigate } from 'react-router-dom'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ReferenceLine,
} from 'recharts'
import { StatusBadge, RiskBadge, AuditBadge } from '../components/Badges'
import { useCarrierPortalData } from '../CarrierPortalContext'
import { C, cardStyle, tableThStyle, tableTdStyle } from '../styles'
import dayjs from 'dayjs'
const BASE = '/admin/wc-audit/carrier-portal'

const fmt = (n: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)

const fmtFull = (n: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(n)

// ─── Custom bar chart tooltip ─────────────────────────────────────────────────
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  const diff = payload.length === 2 ? payload[1].value - payload[0].value : null
  return (
    <div style={{
      background: '#fff', border: `1px solid ${C.border}`, borderRadius: 10,
      padding: 12, boxShadow: '0 4px 16px rgba(0,0,0,0.1)', fontSize: 12,
    }}>
      <p style={{ fontWeight: 700, color: C.text, marginBottom: 6 }}>{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.fill, fontWeight: 600, margin: '2px 0' }}>
          {p.name}: {fmt(p.value)}
        </p>
      ))}
      {diff !== null && (
        <p style={{ marginTop: 4, fontWeight: 700, color: diff >= 0 ? C.red : C.green }}>
          Variance: {fmt(diff)}
        </p>
      )}
    </div>
  )
}

// ─── Reusable sub-components ──────────────────────────────────────────────────
const SectionLabel = ({ text }: { text: string }) => (
  <div style={{
    fontSize: 10, fontWeight: 700, textTransform: 'uppercase' as const,
    letterSpacing: 1.5, color: C.muted, marginBottom: 14,
  }}>
    {text}
  </div>
)

const MetricTile = ({ label, value, alert = false }: { label: string; value: string; alert?: boolean }) => (
  <div style={{
    padding: '10px 14px', borderRadius: 10,
    background: alert ? '#FEF2F2' : '#F8FAFD',
    border: alert ? '1px solid #FECACA' : `1px solid ${C.border}`,
  }}>
    <p style={{ margin: 0, fontSize: 11, color: C.muted, fontWeight: 500 }}>{label}</p>
    <p style={{ margin: '4px 0 0', fontSize: 15, fontWeight: 800, color: alert ? '#991B1B' : C.text }}>
      {value}
    </p>
  </div>
)

// ─── Main component ───────────────────────────────────────────────────────────
export default function PolicyDetail() {
  const { id }   = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { policies, targetVariance } = useCarrierPortalData()

  const policy = policies.find(p => p.policyNumber === decodeURIComponent(id ?? ''))
  console.log("policy data<-->", policy);
  
  if (!policy) {
    return (
      <div style={{ minHeight: '100vh', background: C.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: 15, color: C.muted }}>
            Policy <strong style={{ color: C.text }}>{id}</strong> not found.
          </p>
          <button
            onClick={() => navigate(`${BASE}/policies`)}
            style={{ marginTop: 14, background: 'none', border: 'none', color: C.accent, fontSize: 13, cursor: 'pointer' }}
          >
            ← Back to policies
          </button>
        </div>
      </div>
    )
  }

  const varAbove = Math.abs(policy.variancePercent) > targetVariance.threshold
  const varPos   = policy.variance >= 0

  // Payroll submission rate — guard divide-by-zero
  const submissionRate = policy.periodsExpected > 0
    ? Math.round((policy.actualPeriodsRecevied / policy.periodsReceived) * 100)
    : 0

  // Build a single-row chart dataset from overall premium figures
  // (API does not return monthly breakdown; we show one aggregate bar per premium type)
  // const chartData = [
  //   {
  //     period: 'Overall',
  //     estimatedPremium: policy.estEarnedPremium,
  //     earnedPremium:    policy.actualEarnedPremium,
  //   },
  // ]
  
  const chartData = (policy.monthlyTrend || []).map(m => ({
    period: dayjs(m.month).format('MMM YY'),                // or formatted later
    estimatedPremium: m.est,
    earnedPremium: m.earned,
    variance: m.variance,
  }))

  // Class code totals
  const totEstExp  = policy.classCodes.reduce((s, c) => s + c.estExposure,    0)
  const totEarnExp = policy.classCodes.reduce((s, c) => s + c.earnedExposure, 0)
  const totVar     = totEarnExp - totEstExp
  const totPrem    = policy.classCodes.reduce((s, c) => s + c.estYtdPremium,  0)
  const missingPayrolls = (policy.periodsReceived) - policy.actualPeriodsRecevied
  return (
    <div style={{ minHeight: '100vh', background: C.bg }}>
      <main style={{
        maxWidth: 1600, margin: '0 auto', padding: '28px 28px',
        display: 'flex', flexDirection: 'column', gap: 20,
      }}>

        {/* ── Breadcrumb ── */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: C.muted }}>
          <button onClick={() => navigate(`${BASE}/dashboard`)}
            style={{ background: 'none', border: 'none', color: C.muted, fontSize: 13, cursor: 'pointer' }}>
            Dashboard
          </button>
          <span style={{ color: C.border }}>/</span>
          <button onClick={() => navigate(`${BASE}/policies`)}
            style={{ background: 'none', border: 'none', color: C.muted, fontSize: 13, cursor: 'pointer' }}>
            Policies
          </button>
          <span style={{ color: C.border }}>/</span>
          <span style={{ color: C.text, fontWeight: 700 }}>{policy.policyNumber}</span>
        </div>

        {/* ── POLICY LEVEL #1 — Header card ── */}
        <div style={cardStyle}>
          {/* Top row: name + badges */}
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
            <div>
              <SectionLabel text="Policy Level #1" />
              <h1 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: C.text }}>{policy.insuredName}</h1>
              <p style={{ margin: '4px 0 0', fontFamily: 'monospace', fontSize: 16, fontWeight: 700, color: C.navy }}>
                {policy.policyNumber}
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', paddingTop: 4 }}>
              <StatusBadge status={policy.policyStatus} />
              <RiskBadge   risk={policy.risk} />
              <AuditBadge  status={policy.auditStatus} />
            </div>
          </div>

          {/* 6-column metric tiles */}
          <div style={{ marginTop: 20, display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 12 }}>
            <MetricTile label="State"              value={policy.state} />
            <MetricTile label="Effective Date"     value={policy.effectiveDate  || '—'} />
            <MetricTile label="Expiration Date"    value={policy.expirationDate || '—'} />
            <MetricTile label="Missing Payrolls"   value={String(missingPayrolls)} alert={missingPayrolls > 1} />
            <MetricTile label="Est Annual Premium" value={fmt(policy.estimated_premium)} />
            <MetricTile
              label="Variance %"
              value={`${policy.variancePercent > 0 ? '+' : ''}${policy.variancePercent.toFixed(1)}%`}
              alert={varAbove}
            />
          </div>
        </div>

        {/* ── Policy Summary table ── */}
        <div style={{ ...cardStyle, padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '12px 20px', borderBottom: `1px solid ${C.border}`, background: '#F8FAFD' }}>
            <p style={{ margin: 0, fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, color: C.muted }}>
              Policy Summary
            </p>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {[
                    ['Policy #', 'left'], ['Insured Name', 'left'], ['St.', 'center'],
                    ['Effective Date', 'left'], ['Policy Status', 'left'],
                    ['EST Annual Premium', 'right'], ['EST EARNED', 'right'],
                    ['ACTUAL EARNED', 'right'], ['Variance $', 'right'], ['Var %', 'right'],
                    ['Risk', 'left'], ['Audit Status', 'left'],
                  ].map(([h, align]) => (
                    <th key={h as string} style={{ ...tableThStyle, textAlign: align as any }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ ...tableTdStyle, fontFamily: 'monospace', fontWeight: 700, color: C.navy }}>{policy.policyNumber}</td>
                  <td style={{ ...tableTdStyle, fontWeight: 600 }}>{policy.insuredName}</td>
                  <td style={{ ...tableTdStyle, textAlign: 'center' }}>{policy.state}</td>
                  <td style={tableTdStyle}>{policy.effectiveDate || '—'}</td>
                  <td style={tableTdStyle}><StatusBadge status={policy.policyStatus} /></td>
                  <td style={{ ...tableTdStyle, textAlign: 'right', fontWeight: 600 }}>{fmt(policy.estimated_premium)}</td>
                  <td style={{ ...tableTdStyle, textAlign: 'right' }}>{fmt(policy.estEarnedPremium)}</td>
                  <td style={{ ...tableTdStyle, textAlign: 'right' }}>{fmt(policy.actualEarnedPremium)}</td>
                  <td style={{ ...tableTdStyle, textAlign: 'right', fontWeight: 700, color: varPos ? C.red : C.green }}>
                    {varPos ? '+' : ''}{fmt(policy.variance)}
                  </td>
                  <td style={{ ...tableTdStyle, textAlign: 'right', fontWeight: 700, color: varAbove ? C.red : C.text }}>
                    {policy.variancePercent > 0 ? '+' : ''}{policy.variancePercent.toFixed(1)}%
                  </td>
                  <td style={tableTdStyle}><RiskBadge risk={policy.risk} /></td>
                  <td style={tableTdStyle}><AuditBadge status={policy.auditStatus} /></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* ── Actual Earned Premium Vs EST Premium chart ── */}
        <div style={cardStyle}>
          {/* Chart header — KPI summary row matching the original design */}
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 16 }}>
            <div>
              <h2 style={{ margin: 0, fontSize: 16, fontWeight: 800, color: C.text }}>
                Actual Earned Premium Vs EST Earned Premium

              </h2>
              <p style={{ margin: '4px 0 0', fontSize: 12, color: C.muted }}>
                Overall comparison — actual audit figures vs. pro-rated estimate
              </p>
            </div>
            <div style={{ display: 'flex', gap: 28 }}>
              <div style={{ textAlign: 'right' }}>
                <p style={{ margin: 0, fontSize: 11, color: C.muted, fontWeight: 500 }}>Total Est. Earned</p>
                <p style={{ margin: '2px 0 0', fontWeight: 700, fontSize: 14, color: C.text }}>
                  {fmtFull(policy.estEarnedPremium)}
                </p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <p style={{ margin: 0, fontSize: 11, color: C.muted, fontWeight: 500 }}>Total Actual Earned</p>
                <p style={{ margin: '2px 0 0', fontWeight: 700, fontSize: 14, color: C.text }}>
                  {fmtFull(policy.actualEarnedPremium)}
                </p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <p style={{ margin: 0, fontSize: 11, color: C.muted, fontWeight: 500 }}>Net Variance</p>
                <p style={{ margin: '2px 0 0', fontWeight: 700, fontSize: 14, color: varPos ? C.red : C.green }}>
                  {varPos ? '+' : ''}{fmtFull(policy.variance)}
                </p>
              </div>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} margin={{ top: 8, right: 20, left: 10, bottom: 0 }} barCategoryGap="40%">
              <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
              <XAxis dataKey="period" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
              <Tooltip content={<CustomTooltip />} />
              <Legend iconType="square" iconSize={10} />
              <ReferenceLine y={0} stroke={C.border} />
              <Bar dataKey="estimatedPremium" name="Est Earned Premium"   fill={C.muted}  radius={[4, 4, 0, 0]} />
              <Bar dataKey="earnedPremium"    name="Actual Earned Premium" fill={C.navy}   radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>

          {/* Variance callout */}
          {varAbove && (
            <div style={{
              marginTop: 16, display: 'flex', alignItems: 'center', gap: 12,
              padding: 14, background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 10,
            }}>
              <svg width={20} height={20} fill="none" viewBox="0 0 24 24" stroke={C.red} style={{ flexShrink: 0 }}>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <p style={{ margin: 0, fontSize: 13, color: '#991B1B', fontWeight: 500 }}>
                Variance of{' '}
                <strong>{policy.variancePercent.toFixed(1)}%</strong>{' '}
                exceeds the {targetVariance.threshold}% threshold.
                {missingPayrolls > 1 &&
                  ` Also flagged for ${missingPayrolls} missing payrolls.`}
              </p>
            </div>
          )}
        </div>

        {/* ── POLICY LEVEL #2 — Class Codes table ── */}
        <div style={cardStyle}>
          <SectionLabel text="Policy Level #2" />
          <p style={{ margin: '0 0 14px', fontWeight: 800, fontSize: 14, color: C.text }}>Class Codes</p>

          <div style={{ overflowX: 'auto', borderRadius: 10, border: `1px solid ${C.border}` }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {[
                    ['Class Code', 'left'], ['Description', 'left'],
                    ['EST Exposure', 'right'], ['Actual Earned Exposure', 'right'],
                    ['Variance', 'right'], ['Net Rate', 'right'],
                    ['Est earned', 'right'], ['Action', 'left'],
                  ].map(([h, align]) => (
                    <th key={h as string} style={{ ...tableThStyle, textAlign: align as any }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {policy.classCodes.length === 0 ? (
                  <tr>
                    <td colSpan={8} style={{ textAlign: 'center', padding: 32, color: C.muted, fontSize: 13 }}>
                      No class code data available for this policy.
                    </td>
                  </tr>
                ) : (
                  policy.classCodes.map((cc, i) => {
                    const ccVar = cc.earnedExposure - cc.estExposure
                    return (
                      <tr key={cc.code} style={{ background: i % 2 === 1 ? '#F8FAFD' : '#fff' }}>
                        <td style={{ ...tableTdStyle, fontFamily: 'monospace', fontWeight: 700 }}>{cc.code}</td>
                        <td style={{ ...tableTdStyle, color: C.muted }}>{cc.description || cc.code}</td>
                        <td style={{ ...tableTdStyle, textAlign: 'right' }}>
                          {cc.estExposure.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td style={{ ...tableTdStyle, textAlign: 'right' }}>
                          {cc.earnedExposure.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td style={{ ...tableTdStyle, textAlign: 'right', fontWeight: 700, color: ccVar >= 0 ? C.red : C.green }}>
                          {ccVar >= 0 ? '+' : ''}
                          {ccVar.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td style={{ ...tableTdStyle, textAlign: 'right' }}>{cc.netRate.toFixed(4)}</td>
                        <td style={{ ...tableTdStyle, textAlign: 'right', fontWeight: 600 }}>{fmt(cc.estYtdPremium)}</td>
                        <td style={tableTdStyle}>
                          <button style={{
                            fontSize: 11, padding: '4px 10px', border: `1px solid ${C.border}`,
                            borderRadius: 6, color: C.muted, background: '#fff', cursor: 'pointer',
                          }}>
                            Review
                          </button>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>

              {/* Totals footer */}
              {policy.classCodes.length > 0 && (
                <tfoot>
                  <tr style={{ borderTop: `2px solid ${C.border}`, background: '#F8FAFD' }}>
                    <td style={{ ...tableTdStyle, fontWeight: 800 }} colSpan={2}>Totals</td>
                    <td style={{ ...tableTdStyle, textAlign: 'right', fontWeight: 800 }}>
                      {totEstExp.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td style={{ ...tableTdStyle, textAlign: 'right', fontWeight: 800 }}>
                      {totEarnExp.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td style={{ ...tableTdStyle, textAlign: 'right', fontWeight: 800, color: totVar >= 0 ? C.red : C.green }}>
                      {totVar >= 0 ? '+' : ''}
                      {totVar.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td style={tableTdStyle} />
                    <td style={{ ...tableTdStyle, textAlign: 'right', fontWeight: 800 }}>{fmt(totPrem)}</td>
                    <td style={tableTdStyle} />
                  </tr>
                </tfoot>
              )}
            </table>
          </div>
        </div>

        {/* ── Payroll ── */}
        <div style={cardStyle}>
          <SectionLabel text="Payroll As of date" />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
            {/* Periods Expected */}
            <div style={{ padding: 16, borderRadius: 12, background: '#F8FAFD', border: `1px solid ${C.border}` }}>
              <p style={{ margin: 0, fontSize: 11, color: C.muted, fontWeight: 500 }}>Periods Expected</p>
              <p style={{ margin: '6px 0 0', fontSize: 28, fontWeight: 800, color: C.text }}>
                {policy.periodsReceived}
              </p>
            </div>

            {/* Periods Received */}
            <div style={{
              padding: 16, borderRadius: 12,
              background: missingPayrolls > 0 ? '#FFFBEB' : '#F8FAFD',
              border: `1px solid ${missingPayrolls > 0 ? '#FCD34D' : C.border}`,
            }}>
              <p style={{ margin: 0, fontSize: 11, color: C.muted, fontWeight: 500 }}>Periods Received</p>
              <p style={{ margin: '6px 0 0', fontSize: 28, fontWeight: 800, color: missingPayrolls > 0 ? '#92400E' : C.text }}>
                {policy.actualPeriodsRecevied}
              </p>
            </div>

            {/* Missing Periods */}
            <div style={{
              padding: 16, borderRadius: 12,
              background: missingPayrolls > 0 ? '#FFFBEB' : '#F8FAFD',
              border: `1px solid ${missingPayrolls > 0 ? '#FCD34D' : C.border}`,
            }}>
              <p style={{ margin: 0, fontSize: 11, color: C.muted, fontWeight: 500 }}>Missing Periods</p>
              <p style={{ margin: '6px 0 0', fontSize: 28, fontWeight: 800, color: missingPayrolls > 0 ? '#92400E' : C.text }}>
                {missingPayrolls}
              </p>
            </div>

            {/* Submission Rate */}
            <div style={{ padding: 16, borderRadius: 12, background: '#F8FAFD', border: `1px solid ${C.border}` }}>
              <p style={{ margin: 0, fontSize: 11, color: C.muted, fontWeight: 500 }}>Submission Rate</p>
              <p style={{ margin: '6px 0 0', fontSize: 28, fontWeight: 800, color: C.text }}>
                {submissionRate}%
              </p>
            </div>
          </div>
        </div>

        {/* ── AI Narrative ── */}
        <div style={{ ...cardStyle, borderLeft: `4px solid ${C.navy}` }}>
          <SectionLabel text="AI Narrative" />
          <p style={{ margin: 0, fontSize: 13, color: C.text, lineHeight: 1.75 }}>
            {policy.aiNarrative ? (
              policy.aiNarrative
            ) : (
              <>
                Policy <strong>{policy.policyNumber}</strong> for{' '}
                <strong>{policy.insuredName}</strong>
                {policy.state !== '—' ? ` (${policy.state})` : ''} shows a{' '}
                <span style={{ color: varPos ? C.red : C.green, fontWeight: 700 }}>
                  {varPos ? 'positive' : 'negative'} variance of{' '}
                  {fmt(Math.abs(policy.variance))} ({Math.abs(policy.variancePercent).toFixed(1)}%)
                </span>{' '}
                compared to the estimated earned premium.{' '}
                {varAbove
                  ? `This exceeds the ${targetVariance.threshold}% carrier threshold and requires immediate auditor review. `
                  : `This is within the acceptable ${targetVariance.threshold}% carrier threshold. `}
                {missingPayrolls > 0
                  ? `There are ${missingPayrolls} missing payroll submission(s), which ${missingPayrolls > 1 ? 'significantly increases' : 'contributes to'} the risk score. `
                  : 'All payroll periods have been received. '}
                {policy.risk === 'High'
                  ? 'Classified as HIGH risk — immediate follow-up with insured is recommended.'
                  : policy.risk === 'Medium'
                  ? 'Classified as MEDIUM risk — monitor closely and initiate contact with insured.'
                  : 'Classified as LOW risk — routine review. No immediate action required.'}
              </>
            )}
          </p>
        </div>

      </main>
    </div>
  )
}

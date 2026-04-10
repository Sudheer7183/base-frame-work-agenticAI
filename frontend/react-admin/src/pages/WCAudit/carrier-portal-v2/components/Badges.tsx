// frontend/react-admin/src/pages/WCAudit/carrier-portal/components/Badges.tsx
// All badge components in one file — uses inline styles only, no Tailwind.

import type { AuditStatus, RiskLevel, PolicyStatus } from '../types'

// ─── StatusBadge ──────────────────────────────────────────────────────────────
const STATUS_CFG: Record<PolicyStatus, { bg: string; color: string; dot: string }> = {
  'Active':         { bg: '#D1FAE5', color: '#065F46', dot: '#10B981' },
  'Pending Cancel': { bg: '#FEF3C7', color: '#92400E', dot: '#F59E0B' },
  'Cancelled':      { bg: '#FEE2E2', color: '#991B1B', dot: '#EF4444' },
  'Expired':        { bg: '#F3F4F6', color: '#6B7280', dot: '#9CA3AF' },
}

export function StatusBadge({ status }: { status: PolicyStatus }) {
  const cfg = STATUS_CFG[status] ?? STATUS_CFG['Expired']
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600,
      background: cfg.bg, color: cfg.color,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: cfg.dot, flexShrink: 0 }} />
      {status}
    </span>
  )
}

// ─── RiskBadge ────────────────────────────────────────────────────────────────
const RISK_CFG: Record<RiskLevel, { bg: string; color: string; border: string }> = {
  Low:    { bg: '#D1FAE5', color: '#065F46', border: '#6EE7B7' },
  Medium: { bg: '#FEF3C7', color: '#92400E', border: '#FCD34D' },
  High:   { bg: '#FEE2E2', color: '#991B1B', border: '#FCA5A5' },
}

export function RiskBadge({ risk }: { risk: RiskLevel }) {
  const cfg = RISK_CFG[risk] ?? RISK_CFG['Low']
  return (
    <span style={{
      display: 'inline-block', padding: '3px 10px', borderRadius: 6, fontSize: 11, fontWeight: 700,
      background: cfg.bg, color: cfg.color,
      border: `1px solid ${cfg.border}`,
    }}>
      {risk}
    </span>
  )
}

// ─── AuditBadge ───────────────────────────────────────────────────────────────
const AUDIT_CFG: Record<AuditStatus, { bg: string; color: string }> = {
  'In Progress': { bg: '#DBEAFE', color: '#1D4ED8' },
  'Complete':    { bg: '#D1FAE5', color: '#065F46' },
  'Pending':     { bg: '#F3F4F6', color: '#6B7280' },
  'N/A':         { bg: '#F9FAFB', color: '#9CA3AF' },
}

export function AuditBadge({ status }: { status: AuditStatus }) {
  const cfg = AUDIT_CFG[status] ?? AUDIT_CFG['N/A']
  return (
    <span style={{
      display: 'inline-block', padding: '3px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600,
      background: cfg.bg, color: cfg.color,
    }}>
      {status}
    </span>
  )
}

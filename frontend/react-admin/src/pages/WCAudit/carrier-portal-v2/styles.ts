// frontend/react-admin/src/pages/WCAudit/carrier-portal/styles.ts
// Matches the existing WCAuditApp colour palette — no Tailwind needed.

export const C = {
  navy:    '#0D1B2A',
  navyMid: '#132338',
  navyLt:  '#1A3050',
  accent:  '#1E6FD9',
  accentLt:'#3D8FFF',
  teal:    '#0ABFBC',
  amber:   '#F59E0B',
  red:     '#EF4444',
  green:   '#10B981',
  bg:      '#F0F4FA',
  card:    '#FFFFFF',
  border:  '#E2EAF4',
  text:    '#1A2B42',
  muted:   '#6B7E99',
} as const

// ─── Common reusable style objects ────────────────────────────────────────────

export const cardStyle: React.CSSProperties = {
  background: C.card,
  border: `1px solid ${C.border}`,
  borderRadius: 14,
  padding: 20,
}

export const sectionHeadingStyle: React.CSSProperties = {
  margin: 0,
  fontSize: 13,
  fontWeight: 700,
  color: C.text,
  marginBottom: 12,
}

export const tableThStyle: React.CSSProperties = {
  padding: '10px 14px',
  textAlign: 'left' as const,
  fontSize: 11,
  color: C.muted,
  fontWeight: 700,
  textTransform: 'uppercase' as const,
  letterSpacing: 0.8,
  background: '#F8FAFD',
  borderBottom: `2px solid ${C.border}`,
}

export const tableTdStyle: React.CSSProperties = {
  padding: '13px 14px',
  fontSize: 13,
  color: C.text,
  borderBottom: `1px solid ${C.border}`,
}

export const badgeBase: React.CSSProperties = {
  display: 'inline-block',
  padding: '3px 10px',
  borderRadius: 20,
  fontSize: 11,
  fontWeight: 600,
}

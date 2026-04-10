// frontend/react-admin/src/pages/WCAudit/carrier-portal/components/Header.tsx
// Inline styles only — no Tailwind.

import { NavLink } from 'react-router-dom'
import { C } from '../styles'

const BASE = '/admin/wc-audit/carrier-portal'

export default function Header() {
  const navLinkStyle = (isActive: boolean): React.CSSProperties => ({
    padding: '8px 16px',
    borderRadius: 8,
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer',
    border: 'none',
    background: isActive ? 'rgba(255,255,255,0.15)' : 'transparent',
    color: isActive ? '#fff' : 'rgba(255,255,255,0.6)',
    textDecoration: 'none',
    transition: 'all 0.15s',
  })

  return (
    <header style={{ background: C.navy, color: '#fff', boxShadow: '0 2px 8px rgba(0,0,0,0.25)' }}>
      <div style={{
        maxWidth: 1600, margin: '0 auto', padding: '0 28px',
        height: 64, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 38, height: 38, borderRadius: 10,
            background: 'rgba(255,255,255,0.1)',
            border: '1px solid rgba(255,255,255,0.2)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width={20} height={20} fill="none" viewBox="0 0 24 24" stroke="rgba(255,255,255,0.8)">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
              />
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 2, color: 'rgba(255,255,255,0.5)', fontWeight: 600 }}>
              Carrier Portal
            </div>
            <div style={{ fontSize: 15, fontWeight: 800, lineHeight: 1.2 }}>Audit AI</div>
          </div>
        </div>

        {/* Nav */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <NavLink to={`${BASE}/dashboard`} style={({ isActive }) => navLinkStyle(isActive)}>
            Dashboard
          </NavLink>
          <NavLink to={`${BASE}/policies`} style={({ isActive }) => navLinkStyle(isActive)}>
            Policies
          </NavLink>
          {/* <NavLink
            to="/admin/wc-audit"
            style={{
              ...navLinkStyle(false),
              marginLeft: 12,
              border: '1px solid rgba(255,255,255,0.2)',
            }}
          >
            ← Audit Platform
          </NavLink> */}
        </nav>
      </div>
    </header>
  )
}

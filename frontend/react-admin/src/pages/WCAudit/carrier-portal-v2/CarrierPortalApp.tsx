// frontend/react-admin/src/pages/WCAudit/carrier-portal/CarrierPortalApp.tsx

import { Routes, Route, Navigate }   from 'react-router-dom'
import { CarrierPortalContext }       from './CarrierPortalContext'
import { useCarrierPolicies }         from "./hooks/useCarrierPolicies"
import Header    from './components/Header'
import Dashboard from './pages/Dashboard'
import PolicyList   from './pages/PolicyList'
import PolicyDetail from './pages/PolicyDetail'
import { C } from './styles'

function LoadingScreen() {
  return (
    <div style={{ minHeight: '100vh', background: C.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{
          width: 40, height: 40,
          border: `4px solid ${C.border}`,
          borderTopColor: C.accent,
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          margin: '0 auto 14px',
        }} />
        <p style={{ color: C.muted, fontSize: 13, fontWeight: 500 }}>Loading audit data…</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    </div>
  )
}

function ErrorScreen({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div style={{ minHeight: '100vh', background: C.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{
        background: C.card, border: `1px solid #FECACA`, borderRadius: 16,
        padding: 32, maxWidth: 400, textAlign: 'center',
      }}>
        <div style={{
          width: 48, height: 48, borderRadius: '50%', background: '#FEE2E2',
          display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px',
        }}>
          <svg width={24} height={24} fill="none" viewBox="0 0 24 24" stroke="#EF4444">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <p style={{ fontWeight: 700, color: '#991B1B', fontSize: 14, marginBottom: 8 }}>Failed to load audit data</p>
        <p style={{ color: C.muted, fontSize: 12, marginBottom: 20 }}>{message}</p>
        <button
          onClick={onRetry}
          style={{
            background: C.navy, color: '#fff', border: 'none', borderRadius: 8,
            padding: '9px 22px', fontSize: 13, fontWeight: 700, cursor: 'pointer',
          }}
        >
          Retry
        </button>
      </div>
    </div>
  )
}

export default function CarrierPortalApp() {
  const data = useCarrierPolicies()

  return (
    <CarrierPortalContext.Provider value={data}>
      <div style={{ minHeight: '100vh', fontFamily: "'DM Sans', 'Segoe UI', sans-serif", background: C.bg }}>
        <Header />
        {data.loading ? (
          <LoadingScreen />
        ) : data.error ? (
          <ErrorScreen message={data.error} onRetry={data.refresh} />
        ) : (
          <Routes>
            <Route index               element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard"    element={<Dashboard />} />
            <Route path="policies"     element={<PolicyList />} />
            <Route path="policies/:id" element={<PolicyDetail />} />
            <Route path="*"            element={<Navigate to="dashboard" replace />} />
          </Routes>
        )}
      </div>
    </CarrierPortalContext.Provider>
  )
}

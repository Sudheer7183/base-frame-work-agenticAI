// import React from 'react';
// import { AuthProvider, ProtectedRoute, useAuth } from './auth';
// import LoginPage from './LoginPage';
// import TenantAdminInterface from './tenant-admin';

// function AppContent() {
//   const { user, loading } = useAuth();

//   if (loading) {
//     return (
//       <div style={{
//         display: 'flex',
//         justifyContent: 'center',
//         alignItems: 'center',
//         minHeight: '100vh',
//         background: '#f5f7fb'
//       }}>
//         <div style={{ textAlign: 'center' }}>
//           <div style={{
//             width: '48px',
//             height: '48px',
//             border: '4px solid #e5e7eb',
//             borderTopColor: '#3b82f6',
//             borderRadius: '50%',
//             animation: 'spin 1s linear infinite',
//             margin: '0 auto 16px'
//           }}></div>
//           <p style={{ color: '#6b7280' }}>Loading...</p>
//         </div>
//       </div>
//     );
//   }

//   if (!user) {
//     return <LoginPage />;
//   }

//   return (
//     <ProtectedRoute requireAdmin={true}>
//       <TenantAdminInterface />
//     </ProtectedRoute>
//   );
// }

// export default function App() {
//   return (
//     <AuthProvider>
//       <AppContent />
//       <style>{`
//         @keyframes spin {
//           to { transform: rotate(360deg); }
//         }
//       `}</style>
//     </AuthProvider>
//   );
// }


import React, { useState } from 'react';
import { AuthProvider, ProtectedRoute, useAuth } from './auth';
import LoginPage from './LoginPage';
import TenantAdminInterface from './tenant-admin';
import AgentList from './AgentList';
import { Database, Bot } from 'lucide-react';

function AppContent() {
  const { user, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('tenants');

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: '#f5f7fb'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '48px',
            height: '48px',
            border: '4px solid #e5e7eb',
            borderTopColor: '#3b82f6',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }}></div>
          <p style={{ color: '#6b7280' }}>Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  return (
    <ProtectedRoute requireAdmin={true}>
      <div style={{ minHeight: '100vh', background: '#f5f7fb' }}>
        {/* Tab Navigation */}
        <div style={{
          background: 'white',
          borderBottom: '1px solid #e5e7eb',
          padding: '0 24px'
        }}>
          <div style={{
            maxWidth: '1400px',
            margin: '0 auto',
            display: 'flex',
            gap: '32px'
          }}>
            <button
              onClick={() => setActiveTab('tenants')}
              style={{
                padding: '16px 0',
                background: 'none',
                border: 'none',
                borderBottom: activeTab === 'tenants' ? '2px solid #3b82f6' : '2px solid transparent',
                color: activeTab === 'tenants' ? '#3b82f6' : '#6b7280',
                fontWeight: 500,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '14px'
              }}
            >
              <Database size={18} />
              Tenants
            </button>
            <button
              onClick={() => setActiveTab('agents')}
              style={{
                padding: '16px 0',
                background: 'none',
                border: 'none',
                borderBottom: activeTab === 'agents' ? '2px solid #3b82f6' : '2px solid transparent',
                color: activeTab === 'agents' ? '#3b82f6' : '#6b7280',
                fontWeight: 500,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '14px'
              }}
            >
              <Bot size={18} />
              Agents
            </button>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'tenants' && <TenantAdminInterface />}
        {activeTab === 'agents' && <AgentList />}
      </div>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </AuthProvider>
  );
}
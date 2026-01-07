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


// import React, { useState } from 'react';
// import { AuthProvider, ProtectedRoute, useAuth } from './auth';
// import LoginPage from './LoginPage';
// import TenantAdminInterface from './tenant-admin';
// import AgentList from './AgentList';
// import { Database, Bot } from 'lucide-react';

// function AppContent() {
//   const { user, loading } = useAuth();
//   const [activeTab, setActiveTab] = useState('tenants');

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
//       <div style={{ minHeight: '100vh', background: '#f5f7fb' }}>
//         {/* Tab Navigation */}
//         <div style={{
//           background: 'white',
//           borderBottom: '1px solid #e5e7eb',
//           padding: '0 24px'
//         }}>
//           <div style={{
//             maxWidth: '1400px',
//             margin: '0 auto',
//             display: 'flex',
//             gap: '32px'
//           }}>
//             <button
//               onClick={() => setActiveTab('tenants')}
//               style={{
//                 padding: '16px 0',
//                 background: 'none',
//                 border: 'none',
//                 borderBottom: activeTab === 'tenants' ? '2px solid #3b82f6' : '2px solid transparent',
//                 color: activeTab === 'tenants' ? '#3b82f6' : '#6b7280',
//                 fontWeight: 500,
//                 cursor: 'pointer',
//                 display: 'flex',
//                 alignItems: 'center',
//                 gap: '8px',
//                 fontSize: '14px'
//               }}
//             >
//               <Database size={18} />
//               Tenants
//             </button>
//             <button
//               onClick={() => setActiveTab('agents')}
//               style={{
//                 padding: '16px 0',
//                 background: 'none',
//                 border: 'none',
//                 borderBottom: activeTab === 'agents' ? '2px solid #3b82f6' : '2px solid transparent',
//                 color: activeTab === 'agents' ? '#3b82f6' : '#6b7280',
//                 fontWeight: 500,
//                 cursor: 'pointer',
//                 display: 'flex',
//                 alignItems: 'center',
//                 gap: '8px',
//                 fontSize: '14px'
//               }}
//             >
//               <Bot size={18} />
//               Agents
//             </button>
//           </div>
//         </div>

//         {/* Tab Content */}
//         {activeTab === 'tenants' && <TenantAdminInterface />}
//         {activeTab === 'agents' && <AgentList />}
//       </div>
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

// import React, { useState } from 'react';
// import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
// import { AuthProvider, ProtectedRoute, useAuth } from './auth';
// import LoginPage from './LoginPage';
// import TenantAdminInterface from './tenant-admin';
// import AgentList from './AgentList';
// import { Database, Bot, Users } from 'lucide-react';

// // Import new SSO invitation pages
// import InviteUserPage from './pages/InviteUserPage';
// import AcceptInvitationPage from './pages/AcceptInvitationPage';
// import UserManagementTable from './components/UserManagementTable';
// import AgentBuilder from './components/AgentBuilder/AgentBuilder';

// function MainLayout({ children }: { children: React.ReactNode }) {
//   const navigate = useNavigate();
//   const location = useLocation();
  
//   // Determine active tab from current location
//   const getActiveTab = () => {
//     const path = location.pathname;
//     if (path.includes('/users')) return 'users';
//     if (path.includes('/agents')) return 'agents';
//     return 'tenants';
//   };

//   const activeTab = getActiveTab();

//   const handleTabChange = (tab: string, path: string) => {
//     navigate(path);
//   };

//   return (
//     <div style={{ minHeight: '100vh', background: '#f5f7fb' }}>
//       {/* Tab Navigation */}
//       <div style={{
//         background: 'white',
//         borderBottom: '1px solid #e5e7eb',
//         padding: '0 24px'
//       }}>
//         <div style={{
//           maxWidth: '1400px',
//           margin: '0 auto',
//           display: 'flex',
//           gap: '32px'
//         }}>
//           <button
//             onClick={() => handleTabChange('tenants', '/admin/tenants')}
//             style={{
//               padding: '16px 0',
//               background: 'none',
//               border: 'none',
//               borderBottom: activeTab === 'tenants' ? '2px solid #3b82f6' : '2px solid transparent',
//               color: activeTab === 'tenants' ? '#3b82f6' : '#6b7280',
//               fontWeight: 500,
//               cursor: 'pointer',
//               display: 'flex',
//               alignItems: 'center',
//               gap: '8px',
//               fontSize: '14px',
//               transition: 'all 0.2s ease'
//             }}
//             onMouseEnter={(e) => e.currentTarget.style.opacity = '0.7'}
//             onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
//           >
//             <Database size={18} />
//             Tenants
//           </button>
          
//           <button
//             onClick={() => handleTabChange('users', '/admin/users')}
//             style={{
//               padding: '16px 0',
//               background: 'none',
//               border: 'none',
//               borderBottom: activeTab === 'users' ? '2px solid #3b82f6' : '2px solid transparent',
//               color: activeTab === 'users' ? '#3b82f6' : '#6b7280',
//               fontWeight: 500,
//               cursor: 'pointer',
//               display: 'flex',
//               alignItems: 'center',
//               gap: '8px',
//               fontSize: '14px',
//               transition: 'all 0.2s ease'
//             }}
//             onMouseEnter={(e) => e.currentTarget.style.opacity = '0.7'}
//             onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
//           >
//             <Users size={18} />
//             Users
//           </button>
          
//           <button
//             onClick={() => handleTabChange('agents', '/admin/agents')}
//             style={{
//               padding: '16px 0',
//               background: 'none',
//               border: 'none',
//               borderBottom: activeTab === 'agents' ? '2px solid #3b82f6' : '2px solid transparent',
//               color: activeTab === 'agents' ? '#3b82f6' : '#6b7280',
//               fontWeight: 500,
//               cursor: 'pointer',
//               display: 'flex',
//               alignItems: 'center',
//               gap: '8px',
//               fontSize: '14px',
//               transition: 'all 0.2s ease'
//             }}
//             onMouseEnter={(e) => e.currentTarget.style.opacity = '0.7'}
//             onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
//           >
//             <Bot size={18} />
//             Agents
//           </button>
//         </div>
//       </div>

//       {/* Content */}
//       {children}
//     </div>
//   );
// }

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

//   return (
//     <Routes>
//       {/* Public Routes - No Authentication Required */}
//       <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/admin/tenants" replace />} />
//       <Route path="/accept-invitation" element={<AcceptInvitationPage />} />

//       {/* Protected Admin Routes */}
//       <Route
//         path="/admin/*"
//         element={
//           !user ? (
//             <Navigate to="/login" replace />
//           ) : (
//             <ProtectedRoute requireAdmin={true}>
//               <MainLayout>
//                 <Routes>
//                   <Route path="tenants" element={<TenantAdminInterface />} />
//                   <Route path="users" element={<UserManagementTable />} />
//                   <Route path="users/invite" element={<InviteUserPage />} />
//                   <Route path="agents" element={<AgentList />} />
//                   <Route index element={<Navigate to="tenants" replace />} />
//                   <Route path="/agents/create" element={<AgentBuilder />} />
//                   <Route path="/agents/:id/edit" element={<AgentBuilder agentId={:id} />} />
//                 </Routes>
//               </MainLayout>
//             </ProtectedRoute>
//           )
//         }
//       />
      
//       {/* Default Redirects */}
//       <Route path="/" element={<Navigate to={user ? "/admin/tenants" : "/login"} replace />} />
//       <Route path="*" element={<Navigate to={user ? "/admin/tenants" : "/login"} replace />} />
//     </Routes>
//   );
// }

// export default function App() {
//   return (
//     <AuthProvider>
//       <BrowserRouter>
//         <AppContent />
//         <style>{`
//           @keyframes spin {
//             to { transform: rotate(360deg); }
//           }
//         `}</style>
//       </BrowserRouter>
//     </AuthProvider>
//   );
// }


import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { AuthProvider, ProtectedRoute, useAuth } from './auth';
import LoginPage from './LoginPage';
import TenantAdminInterface from './tenant-admin';
import AgentList from './AgentList';
import { Database, Bot, Users } from 'lucide-react';

// Import new SSO invitation pages
import InviteUserPage from './pages/InviteUserPage';
import AcceptInvitationPage from './pages/AcceptInvitationPage';
import UserManagementTable from './components/UserManagementTable';

import AgentBuilder from './components/AgentBuilder/AgentBuilder';
import { Layout } from './components/Layout';
function MainLayout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Determine active tab from current location
  const getActiveTab = () => {
    const path = location.pathname;
    if (path.includes('/users')) return 'users';
    if (path.includes('/agents')) return 'agents';
    return 'tenants';
  };

  const activeTab = getActiveTab();

  const handleTabChange = (tab: string, path: string) => {
    navigate(path);
  };

  return (
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
            onClick={() => handleTabChange('tenants', '/admin/tenants')}
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
              fontSize: '14px',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.opacity = '0.7'}
            onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
          >
            <Database size={18} />
            Tenants
          </button>
          
          <button
            onClick={() => handleTabChange('users', '/admin/users')}
            style={{
              padding: '16px 0',
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'users' ? '2px solid #3b82f6' : '2px solid transparent',
              color: activeTab === 'users' ? '#3b82f6' : '#6b7280',
              fontWeight: 500,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.opacity = '0.7'}
            onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
          >
            <Users size={18} />
            Users
          </button>
          
          <button
            onClick={() => handleTabChange('agents', '/admin/agents')}
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
              fontSize: '14px',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.opacity = '0.7'}
            onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
          >
            <Bot size={18} />
            Agents
          </button>
        </div>
      </div>

      {/* Content */}
      {children}
    </div>
  );
}

function AppContent() {
  const { user, loading } = useAuth();

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

  return (
    <Routes>
      {/* Public Routes - No Authentication Required */}
      <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/admin/tenants" replace />} />
      <Route path="/accept-invitation" element={<AcceptInvitationPage />} />

      {/* Protected Admin Routes */}
      <Route
        path="/admin/*"
        element={
          !user ? (
            <Navigate to="/login" replace />
          ) : (
            <ProtectedRoute requireAdmin={true}>
              <MainLayout>
                <Layout>
                <Routes>
                  <Route path="tenants" element={<TenantAdminInterface />} />
                  <Route path="users" element={<UserManagementTable />} />
                  <Route path="users/invite" element={<InviteUserPage />} />
                  <Route path="agents" element={<AgentList />} />
                  <Route path="agents/create" element={<AgentBuilder />} />
                  <Route path="agents/:id/edit" element={<AgentBuilder />} />
                  <Route index element={<Navigate to="tenants" replace />} />
                </Routes>
                </Layout>
              </MainLayout>
            </ProtectedRoute>
          )
        }
      />
      
      {/* Default Redirects */}
      <Route path="/" element={<Navigate to={user ? "/admin/tenants" : "/login"} replace />} />
      <Route path="*" element={<Navigate to={user ? "/admin/tenants" : "/login"} replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppContent />
        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </BrowserRouter>
    </AuthProvider>
  );
}
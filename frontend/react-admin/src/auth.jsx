import { useState, useEffect, createContext, useContext } from 'react';

// Auth Context
const AuthContext = createContext(null);

// Keycloak Configuration
const KEYCLOAK_CONFIG = {
  url: 'http://localhost:8080',
  realm: 'agentic',
  clientId: 'agentic-frontend'
};

const API_BASE_URL = 'http://localhost:8000';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);
  const [refreshToken, setRefreshToken] = useState(null);

  useEffect(() => {
    // Check for existing tokens on mount
    const storedToken = localStorage.getItem('access_token');
    const storedRefresh = localStorage.getItem('refresh_token');
    
    if (storedToken && storedRefresh) {
      setToken(storedToken);
      setRefreshToken(storedRefresh);
      fetchUserProfile(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUserProfile = async (accessToken) => {
    console.log('Fetching user profile with token:', accessToken?.substring(0, 20) + '...');
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/users/me`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('User profile response status:', response.status);

      if (response.ok) {
        const userData = await response.json();
        console.log('User data received:', userData);
        setUser(userData);
      } else if (response.status === 401) {
        console.log('Token expired, attempting refresh...');
        // Token expired, try to refresh
        await refreshAccessToken();
      } else {
        console.error('Failed to fetch user profile:', response.status);
        // Don't logout on backend errors, decode token instead
        const decodedUser = decodeTokenPayload(accessToken);
        if (decodedUser) {
          console.log('Using decoded token data:', decodedUser);
          setUser(decodedUser);
        } else {
          logout();
        }
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
      // Fallback: decode token to get user info
      const decodedUser = decodeTokenPayload(accessToken);
      if (decodedUser) {
        console.log('Using decoded token data after error:', decodedUser);
        setUser(decodedUser);
      } else {
        logout();
      }
    } finally {
      setLoading(false);
    }
  };

  // Decode JWT token to extract user information
  const decodeTokenPayload = (token) => {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      
      const payload = JSON.parse(jsonPayload);
      console.log('Decoded token payload:', payload);
      
      // Extract user info from Keycloak token
      return {
        id: payload.sub,
        email: payload.email || payload.preferred_username,
        name: payload.name || payload.preferred_username,
        username: payload.preferred_username,
        roles: payload.realm_access?.roles || [],
        tenant:payload.tenant || " "
        // Add any other fields from the token you need
      };
    } catch (error) {
      console.error('Error decoding token:', error);
      return null;
    }
  };

  // const login = async (email, password) => {
  //   console.log('Attempting login for:', email);
    
  //   try {
  //     // Get token from Keycloak
  //     const formData = new URLSearchParams();
  //     formData.append('client_id', KEYCLOAK_CONFIG.clientId);
  //     formData.append('grant_type', 'password');
  //     formData.append('username', email);
  //     formData.append('password', password);
      
  //     const response = await fetch(
  //       `${KEYCLOAK_CONFIG.url}/realms/${KEYCLOAK_CONFIG.realm}/protocol/openid-connect/token`,
  //       {
  //         method: 'POST',
  //         headers: {
  //           'Content-Type': 'application/x-www-form-urlencoded'
  //         },
  //         body: formData.toString()
  //       }
  //     );

  //     console.log('Keycloak response status:', response.status);

  //     if (!response.ok) {
  //       const error = await response.json();
  //       console.error('Keycloak error:', error);
  //       throw new Error(error.error_description || 'Login failed');
  //     }

  //     const data = await response.json();
  //     console.log('Login successful, tokens received',data);
      
  //     // Store tokens
  //     localStorage.setItem('access_token', data.access_token);
  //     localStorage.setItem('refresh_token', data.refresh_token);
  //     localStorage.setItem('current_tenant',data.tenant)
      
  //     setToken(data.access_token);
  //     setRefreshToken(data.refresh_token);
      
  //     // First, decode the token to get basic user info immediately
  //     const decodedUser = decodeTokenPayload(data.access_token);
  //     if (decodedUser) {
  //       console.log('Setting user from decoded token:', decodedUser);
  //       setUser(decodedUser);
  //     }
      
  //     // Then try to fetch full profile (optional, don't block login if this fails)
  //     fetchUserProfile(data.access_token).catch(err => {
  //       console.warn('Failed to fetch full profile, but login successful:', err);
  //     });
      
  //     return { success: true };
  //   } catch (error) {
  //     console.error('Login error:', error);
  //     return { success: false, error: error.message };
  //   }
  // };

  const login = async (email, password) => {
    console.log('Attempting login for:', email);
    
    try {
      // Get token from Keycloak
      const formData = new URLSearchParams();
      formData.append('client_id', KEYCLOAK_CONFIG.clientId);
      formData.append('grant_type', 'password');
      formData.append('username', email);
      formData.append('password', password);
      
      const response = await fetch(
        `${KEYCLOAK_CONFIG.url}/realms/${KEYCLOAK_CONFIG.realm}/protocol/openid-connect/token`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          body: formData.toString()
        }
      );

      console.log('Keycloak response status:', response.status);

      if (!response.ok) {
        const error = await response.json();
        console.error('Keycloak error:', error);
        throw new Error(error.error_description || 'Login failed');
      }

      const data = await response.json();
      console.log('Login successful, tokens received', data);
      
      // Store tokens
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      
      // ❌ REMOVE THESE LINES - data doesn't have tenant property
      // localStorage.setItem('current_tenant', data.tenant)
      
      setToken(data.access_token);
      setRefreshToken(data.refresh_token);
      
      // Decode the token to get basic user info immediately
      const decodedUser = decodeTokenPayload(data.access_token);
      if (decodedUser) {
        console.log('Setting user from decoded token:', decodedUser);
        setUser(decodedUser);
        
        // ✅ EXTRACT TENANT FROM DECODED TOKEN, NOT FROM RESPONSE
        if (decodedUser.tenant) {
          const tenantInfo = {
            slug: decodedUser.tenant,
            name: decodedUser.tenant || 'Default Tenant',
          };
          localStorage.setItem('current_tenant', JSON.stringify(tenantInfo)); // ✅ Store as JSON
          console.log('✅ Tenant set from token:', tenantInfo);
        } else {
          console.warn('⚠️ No tenant in token!');
        }
      }
      
      // Then try to fetch full profile (optional, don't block login if this fails)
      fetchUserProfile(data.access_token).catch(err => {
        console.warn('Failed to fetch full profile, but login successful:', err);
      });
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error.message };
    }
  };

  // const refreshAccessToken = async () => {
  //   const storedRefresh = localStorage.getItem('refresh_token');
    
  //   if (!storedRefresh) {
  //     logout();
  //     return;
  //   }

  //   try {
  //     const formData = new URLSearchParams();
  //     formData.append('client_id', KEYCLOAK_CONFIG.clientId);
  //     formData.append('grant_type', 'refresh_token');
  //     formData.append('refresh_token', storedRefresh);
      
  //     const response = await fetch(
  //       `${KEYCLOAK_CONFIG.url}/realms/${KEYCLOAK_CONFIG.realm}/protocol/openid-connect/token`,
  //       {
  //         method: 'POST',
  //         headers: {
  //           'Content-Type': 'application/x-www-form-urlencoded'
  //         },
  //         body: formData.toString()
  //       }
  //     );

  //     if (!response.ok) {
  //       throw new Error('Token refresh failed');
  //     }

  //     const data = await response.json();
      
  //     localStorage.setItem('access_token', data.access_token);
  //     localStorage.setItem('refresh_token', data.refresh_token);
  //     localStorage.setItem("current_tenant",data.tenant)
  //     setToken(data.access_token);
  //     setRefreshToken(data.refresh_token);
      
  //     // Decode new token
  //     const decodedUser = decodeTokenPayload(data.access_token);
  //     if (decodedUser) {
  //       setUser(decodedUser);
  //     }
      
  //     return data.access_token;
  //   } catch (error) {
  //     console.error('Token refresh error:', error);
  //     logout();
  //     return null;
  //   }
  // };


  const refreshAccessToken = async () => {
  const storedRefresh = localStorage.getItem('refresh_token');
  
  if (!storedRefresh) {
    logout();
    return;
  }

  try {
    const formData = new URLSearchParams();
    formData.append('client_id', KEYCLOAK_CONFIG.clientId);
    formData.append('grant_type', 'refresh_token');
    formData.append('refresh_token', storedRefresh);
    
    const response = await fetch(
      `${KEYCLOAK_CONFIG.url}/realms/${KEYCLOAK_CONFIG.realm}/protocol/openid-connect/token`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData.toString()
      }
    );

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    
    // ✅ REMOVE THIS LINE
    // localStorage.setItem("current_tenant", data.tenant)
    
    setToken(data.access_token);
    setRefreshToken(data.refresh_token);
    
    // ✅ DECODE NEW TOKEN AND UPDATE TENANT
    const decodedUser = decodeTokenPayload(data.access_token);
    if (decodedUser) {
      setUser(decodedUser);
      
      // Extract tenant from token
      if (decodedUser.tenant) {
        const tenantInfo = {
          slug: decodedUser.tenant,
          name: decodedUser.tenant,
        };
        localStorage.setItem('current_tenant', JSON.stringify(tenantInfo));
      }
    }
    
    return data.access_token;
  } catch (error) {
    console.error('Token refresh error:', error);
    logout();
    return null;
  }
};

  const logout = async () => {
    console.log('Logging out...');
    
    try {
      // Optional: Call Keycloak logout endpoint
      const storedRefresh = localStorage.getItem('refresh_token');
      
      if (storedRefresh) {
        const formData = new URLSearchParams();
        formData.append('client_id', KEYCLOAK_CONFIG.clientId);
        formData.append('refresh_token', storedRefresh);
        
        await fetch(
          `${KEYCLOAK_CONFIG.url}/realms/${KEYCLOAK_CONFIG.realm}/protocol/openid-connect/logout`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData.toString()
          }
        );
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local state
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setToken(null);
      setRefreshToken(null);
      setUser(null);
    }
  };

  const hasRole = (role) => {
    const userRoles = user?.roles || [];
    console.log('Checking role:', role, 'in user roles:', userRoles);
    return userRoles.includes(role);
  };

  const isAdmin = () => {
    // Check for common admin role names
    const adminRoles = ['ADMIN', 'SUPER_ADMIN', 'admin', 'super_admin', 'realm-admin'];
    const hasAdminRole = adminRoles.some(role => hasRole(role));
    console.log('Is admin check:', hasAdminRole, 'User roles:', user?.roles);
    return hasAdminRole;
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      loading, 
      login, 
      logout, 
      hasRole, 
      isAdmin,
      token,
      refreshAccessToken
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Protected Route Component
export const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const { user, loading, isAdmin } = useAuth();

  console.log('ProtectedRoute - loading:', loading, 'user:', user, 'requireAdmin:', requireAdmin);

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
            border: '4px solid #e2e8f0',
            borderTopColor: '#3b82f6',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }}></div>
          <p style={{ color: '#64748b' }}>Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    console.log('No user, redirecting to login');
    return null;
  }

  if (requireAdmin && !isAdmin()) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: '#f5f7fb'
      }}>
        <div style={{
          background: 'white',
          padding: '32px',
          borderRadius: '12px',
          textAlign: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          maxWidth: '400px'
        }}>
          <div style={{
            width: '64px',
            height: '64px',
            background: '#fef2f2',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
            fontSize: '32px'
          }}>🔒</div>
          <h2 style={{ color: '#ef4444', marginBottom: '8px', fontSize: '20px' }}>
            Access Denied
          </h2>
          <p style={{ color: '#6b7280', marginBottom: '16px' }}>
            Admin privileges required to access this page
          </p>
          <p style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '16px' }}>
            Your roles: {user?.roles?.join(', ') || 'None'}
          </p>
          <button
            onClick={() => window.location.href = '/'}
            style={{
              padding: '10px 20px',
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500'
            }}
          >
            Go to Home
          </button>
        </div>
      </div>
    );
  }

  return children;
};

// API client with automatic token refresh

const decodeTokenPayload = (token) => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    
    const payload = JSON.parse(jsonPayload);
    console.log('Decoded token payload:', payload);
    
    // Extract user info from Keycloak token
    return {
      id: payload.sub,
      email: payload.email || payload.preferred_username,
      name: payload.name || payload.preferred_username,
      username: payload.preferred_username,
      roles: payload.realm_access?.roles || [],
      // Extract tenant information from token
      tenant_slug: payload.tenant, // This is what Keycloak sends
      tenant_name: payload.tenant_name, // If Keycloak includes this
    };
  } catch (error) {
    console.error('Error decoding token:', error);
    return null;
  }
};

// export const apiClient = {
//   async request(url, options = {}) {
//     const accessToken = localStorage.getItem('access_token');
    
//     const headers = {
//       'Content-Type': 'application/json',
//       ...options.headers
//     };

//     console.log('current teneant token',localStorage.getItem("current_tenant"));
    
//     const tenant = JSON.parse(localStorage.getItem("current_tenant"));

//     if (tenant?.slug) {
//       headers["X-Tenant-ID"] = tenant.slug;
//     }
    
//     if (accessToken) {
//       headers['Authorization'] = `Bearer ${accessToken}`;
//     }
    
//     let response = await fetch(url, {
//       ...options,
//       headers
//     });
    
//     // If unauthorized, try to refresh token
//     if (response.status === 401) {
//       // Get auth context to refresh token
//       const refreshToken = localStorage.getItem('refresh_token');
      
//       if (refreshToken) {
//         const formData = new URLSearchParams();
//         formData.append('client_id', KEYCLOAK_CONFIG.clientId);
//         formData.append('grant_type', 'refresh_token');
//         formData.append('refresh_token', refreshToken);
        
//         const tokenResponse = await fetch(
//           `${KEYCLOAK_CONFIG.url}/realms/${KEYCLOAK_CONFIG.realm}/protocol/openid-connect/token`,
//           {
//             method: 'POST',
//             headers: {
//               'Content-Type': 'application/x-www-form-urlencoded'
//             },
//             body: formData.toString()
//           }
//         );

//         if (tokenResponse.ok) {
//           console.log("I am here");
          
//           const data = await tokenResponse.json();
//           console.log("data from the token",data);
          
//           localStorage.setItem('access_token', data.access_token);
//           localStorage.setItem('refresh_token', data.refresh_token);
//           localStorage.setItem("current_tenant",data.tenant)
//           const decodedUser = decodeTokenPayload(data.access_token);
//         if (decodedUser) {
//           console.log('Setting user from decoded token:', decodedUser);
//           setUser(decodedUser);
          
//           // Set tenant from token
//           if (decodedUser.tenant_slug) {
//             const tenantInfo = {
//               slug: decodedUser.tenant_slug,
//               name: decodedUser.tenant_name || decodedUser.tenant_slug,
//             };
//             setCurrentTenant(tenantInfo);
//             // localStorage.setItem('current_tenant', JSON.stringify(tenantInfo));
//             console.log('Tenant set from token:', tenantInfo);
//           }
//         }

//           // Retry with new token
//           headers['Authorization'] = `Bearer ${data.access_token}`;
//           response = await fetch(url, {
//             ...options,
//             headers
//           });
//         } else {
//           // Refresh failed, redirect to login
//           window.location.href = '/login';
//           throw new Error('Unauthorized');
//         }
//       } else {
//         window.location.href = '/login';
//         throw new Error('Unauthorized');
//       }
//     }
    
//     if (!response.ok) {
//       const error = await response.json().catch(() => ({ detail: 'Request failed' }));
//       throw new Error(error.detail || 'Request failed');
//     }
    
//     return response.json();
//   },
  
//   get(url) {
//     return this.request(url);
//   },
  
//   post(url, data) {
//     return this.request(url, {
//       method: 'POST',
//       body: JSON.stringify(data)
//     });
//   },
  
//   patch(url, data) {
//     return this.request(url, {
//       method: 'PATCH',
//       body: JSON.stringify(data)
//     });
//   },
  
//   delete(url) {
//     return this.request(url, {
//       method: 'DELETE'
//     });
//   }
// };

export const apiClient = {
  async request(url, options = {}) {
    const accessToken = localStorage.getItem('access_token');
    
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    console.log('current tenant token', localStorage.getItem("current_tenant"));
    
    // ✅ SAFELY PARSE TENANT
    const tenantString = localStorage.getItem("current_tenant");
    let tenant = null;
    
    if (tenantString && tenantString !== 'undefined' && tenantString !== 'null') {
      try {
        tenant = JSON.parse(tenantString);
      } catch (e) {
        console.error('Failed to parse tenant:', e);
      }
    }

    // Add tenant header if available
    if (tenant?.slug) {
      headers["X-Tenant-ID"] = tenant.slug;
      console.log('✅ Adding X-Tenant-ID:', tenant.slug);
    } else {
      console.warn('⚠️ No tenant available for request');
    }
    
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }
    
    console.log('📡 Request to:', url);
    
    let response = await fetch(url, {
      ...options,
      headers
    });
    
    console.log('📥 Response:', response.status);
    
    // If unauthorized, try to refresh token
    if (response.status === 401) {
      console.log('⚠️ 401 Unauthorized, attempting token refresh...');
      
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (refreshToken) {
        const formData = new URLSearchParams();
        formData.append('client_id', KEYCLOAK_CONFIG.clientId);
        formData.append('grant_type', 'refresh_token');
        formData.append('refresh_token', refreshToken);
        
        const tokenResponse = await fetch(
          `${KEYCLOAK_CONFIG.url}/realms/${KEYCLOAK_CONFIG.realm}/protocol/openid-connect/token`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData.toString()
          }
        );

        if (tokenResponse.ok) {
          console.log('✅ Token refreshed successfully');
          
          const data = await tokenResponse.json();
          
          // ✅ ONLY UPDATE LOCALSTORAGE, NOT REACT STATE
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
          
          // ✅ UPDATE TENANT FROM NEW TOKEN
          const decodedUser = decodeTokenPayload(data.access_token);
          if (decodedUser?.tenant_slug) {
            const tenantInfo = {
              slug: decodedUser.tenant_slug,
              name: decodedUser.tenant_name || decodedUser.tenant_slug,
            };
            localStorage.setItem('current_tenant', JSON.stringify(tenantInfo));
            console.log('✅ Updated tenant from refreshed token:', tenantInfo);
            
            // Update headers for retry
            headers['X-Tenant-ID'] = tenantInfo.slug;
          }

          // Retry with new token
          headers['Authorization'] = `Bearer ${data.access_token}`;
          
          response = await fetch(url, {
            ...options,
            headers
          });
          
          console.log('📥 Retry response:', response.status);
        } else {
          console.error('❌ Token refresh failed, redirecting to login');
          window.location.href = '/login';
          throw new Error('Unauthorized');
        }
      } else {
        console.error('❌ No refresh token, redirecting to login');
        window.location.href = '/login';
        throw new Error('Unauthorized');
      }
    }
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || 'Request failed');
    }
    
    return response.json();
  },
  
  get(url) {
    return this.request(url);
  },
  
  post(url, data) {
    return this.request(url, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  
  patch(url, data) {
    return this.request(url, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  },
  
  delete(url) {
    return this.request(url, {
      method: 'DELETE'
    });
  }
};

// Add CSS for spinner animation
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(style);
}
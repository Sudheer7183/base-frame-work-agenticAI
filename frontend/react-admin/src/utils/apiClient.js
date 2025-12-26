/**
 * API Client Utility
 * 
 * File: frontend/react-admin/src/utils/apiClient.js
 * Purpose: Centralized API request handler with auth and tenant headers
 */

const API_BASE_URL = 'http://localhost:8000';

class ApiClient {
  /**
   * Make authenticated API request
   */
  async request(endpoint, options = {}) {
    // Get token from localStorage
    const accessToken = localStorage.getItem('access_token');
    
    if (!accessToken) {
      throw new Error('No authentication token found. Please login.');
    }
    
    // Get tenant from localStorage
    const tenantString = localStorage.getItem('current_tenant');
    let tenant = null;
    
    if (tenantString && tenantString !== 'undefined' && tenantString !== 'null') {
      try {
        tenant = JSON.parse(tenantString);
      } catch (e) {
        console.warn('Failed to parse tenant:', e);
      }
    }
    
    // Build headers
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
      ...options.headers
    };
    
    // Add tenant header if available
    if (tenant?.slug) {
      headers['X-Tenant-ID'] = tenant.slug;
    }
    
    // Build full URL
    const url = endpoint.startsWith('http') 
      ? endpoint 
      : `${API_BASE_URL}${endpoint}`;
    
    console.log('API Request:', {
      url,
      method: options.method || 'GET',
      hasAuth: !!headers['Authorization'],
      tenant: tenant?.slug || 'none'
    });
    
    // Make request
    const response = await fetch(url, {
      ...options,
      headers
    });
    
    console.log('API Response:', {
      status: response.status,
      ok: response.ok
    });
    
    // Handle errors
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      if (response.status === 401) {
        // Token expired
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        throw new Error('Authentication expired. Please login again.');
      }
      
      throw new Error(
        errorData.detail || 
        errorData.error?.message || 
        `Request failed with status ${response.status}`
      );
    }
    
    return response.json();
  }
  
  // Convenience methods
  get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }
  
  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
  
  patch(endpoint, data) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  }
  
  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
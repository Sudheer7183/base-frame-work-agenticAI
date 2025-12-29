/**
 * Agent Builder API Client (with Tenant Support)
 * API calls for agent builder functionality
 * 
 * File: frontend/react-admin/src/api/agentBuilderAPI.js
 */

import axios from 'axios';

const API_BASE_URL ='http://localhost:8000/api/v1';

// Create axios instance with auth
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token AND tenant ID to requests
apiClient.interceptors.request.use((config) => {
  // Add Authorization token
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  // Add Tenant ID header (CRITICAL for multi-tenant architecture)
  const tenantId = localStorage.getItem('current_tenant') || 
                   localStorage.getItem('tenant_id') ||
                   sessionStorage.getItem('tenantId') ||
                   sessionStorage.getItem('tenant_id');
  
  if (tenantId) {
    const tenantjson= JSON.parse(tenantId)
    const tenant_slug=tenantjson.slug
    console.log('tenant slug value decoded',tenant_slug);
    
    config.headers['X-Tenant-ID'] = tenant_slug;
  } else {
    // Fallback: Try to get from decoded token
    try {
      if (token) {
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.tenant_id) {
          config.headers['X-Tenant-ID'] = payload.tenant_id;
        }
      }
    } catch (e) {
      console.warn('Could not extract tenant from token');
    }
  }
  
  return config;
});

export const agentBuilderAPI = {
  // ========================================================================
  // AGENT OPERATIONS
  // ========================================================================
  
  /**
   * Create a complete agent with all configurations
   */
  async createCompleteAgent(agentData) {
    const response = await apiClient.post('/agent-builder/agents/complete', agentData);
    return response.data;
  },
  
  /**
   * Get complete agent with all configurations
   */
  async getCompleteAgent(agentId) {
    const response = await apiClient.get(`/agent-builder/agents/${agentId}/complete`);
    return response.data;
  },
  
  /**
   * List all agents with summary
   */
  async listAgents(filters = {}) {
    const params = new URLSearchParams(filters);
    const response = await apiClient.get(`/agent-builder/agents?${params}`);
    return response.data;
  },
  
  /**
   * Update agent builder configuration
   */
  async updateAgent(agentId, updates) {
    const response = await apiClient.put(
      `/agent-builder/agents/${agentId}/builder-config`,
      updates
    );
    return response.data;
  },
  
  /**
   * Delete agent
   */
  async deleteAgent(agentId) {
    const response = await apiClient.delete(`/agents/${agentId}`);
    return response.data;
  },
  
  // ========================================================================
  // UI HELPERS
  // ========================================================================
  
  /**
   * Get dropdown options for UI
   */
  async getDropdownOptions() {
    const response = await apiClient.get('/agent-builder/ui/options');
    return response.data;
  },
  
  /**
   * Get available tools
   */
  async getAvailableTools(category = null) {
    const params = category ? `?category=${category}` : '';
    const response = await apiClient.get(`/agent-builder/ui/tools${params}`);
    return response.data;
  },
  
  // ========================================================================
  // VALIDATION
  // ========================================================================
  
  /**
   * Validate agent configuration
   */
  async validateConfig(config) {
    const response = await apiClient.post('/agent-builder/validate', config);
    return response.data;
  },
  
  // ========================================================================
  // DATABASE CONNECTIONS
  // ========================================================================
  
  /**
   * Create database connection
   */
  async createDatabaseConnection(connection) {
    const response = await apiClient.post('/agent-builder/database-connections', connection);
    return response.data;
  },
  
  /**
   * List database connections
   */
  async listDatabaseConnections() {
    const response = await apiClient.get('/agent-builder/database-connections');
    return response.data;
  },
  
  /**
   * Test database connection
   */
  async testDatabaseConnection(connectionId) {
    const response = await apiClient.post(
      `/agent-builder/database-connections/${connectionId}/test`
    );
    return response.data;
  },
  
  /**
   * Delete database connection
   */
  async deleteDatabaseConnection(connectionId) {
    const response = await apiClient.delete(
      `/agent-builder/database-connections/${connectionId}`
    );
    return response.data;
  },
  
  // ========================================================================
  // API CONFIGURATIONS
  // ========================================================================
  
  /**
   * Create API configuration
   */
  async createAPIConfiguration(config) {
    const response = await apiClient.post('/agent-builder/api-configurations', config);
    return response.data;
  },
  
  /**
   * List API configurations
   */
  async listAPIConfigurations() {
    const response = await apiClient.get('/agent-builder/api-configurations');
    return response.data;
  },
  
  /**
   * Delete API configuration
   */
  async deleteAPIConfiguration(configId) {
    const response = await apiClient.delete(`/agent-builder/api-configurations/${configId}`);
    return response.data;
  },
  
  // ========================================================================
  // TOOL REGISTRY
  // ========================================================================
  
  /**
   * Create tool
   */
  async createTool(tool) {
    const response = await apiClient.post('/agent-builder/tools', tool);
    return response.data;
  },
  
  /**
   * Get tool details
   */
  async getTool(toolId) {
    const response = await apiClient.get(`/agent-builder/tools/${toolId}`);
    return response.data;
  },
  
  /**
   * Update tool
   */
  async updateTool(toolId, updates) {
    const response = await apiClient.put(`/agent-builder/tools/${toolId}`, updates);
    return response.data;
  },
  
  /**
   * Delete tool
   */
  async deleteTool(toolId) {
    const response = await apiClient.delete(`/agent-builder/tools/${toolId}`);
    return response.data;
  },
  
  // ========================================================================
  // AGENT VARIABLES
  // ========================================================================
  
  /**
   * Create agent variable
   */
  async createVariable(agentId, variable) {
    const response = await apiClient.post(
      `/agent-builder/agents/${agentId}/variables`,
      variable
    );
    return response.data;
  },
  
  /**
   * List agent variables
   */
  async listVariables(agentId) {
    const response = await apiClient.get(`/agent-builder/agents/${agentId}/variables`);
    return response.data;
  },
  
  /**
   * Update variable
   */
  async updateVariable(agentId, variableId, updates) {
    const response = await apiClient.put(
      `/agent-builder/agents/${agentId}/variables/${variableId}`,
      updates
    );
    return response.data;
  },
  
  /**
   * Delete variable
   */
  async deleteVariable(agentId, variableId) {
    const response = await apiClient.delete(
      `/agent-builder/agents/${agentId}/variables/${variableId}`
    );
    return response.data;
  },
  
  // ========================================================================
  // EXECUTION TRIGGERS
  // ========================================================================
  
  /**
   * Create execution trigger
   */
  async createTrigger(agentId, trigger) {
    const response = await apiClient.post(
      `/agent-builder/agents/${agentId}/triggers`,
      trigger
    );
    return response.data;
  },
  
  /**
   * List execution triggers
   */
  async listTriggers(agentId) {
    const response = await apiClient.get(`/agent-builder/agents/${agentId}/triggers`);
    return response.data;
  },
  
  /**
   * Toggle trigger enabled/disabled
   */
  async toggleTrigger(triggerId) {
    const response = await apiClient.patch(`/agent-builder/triggers/${triggerId}/toggle`);
    return response.data;
  },
  
  /**
   * Delete trigger
   */
  async deleteTrigger(triggerId) {
    const response = await apiClient.delete(`/agent-builder/triggers/${triggerId}`);
    return response.data;
  },
  
  // ========================================================================
  // AGENT TEMPLATES
  // ========================================================================
  
  /**
   * List agent templates
   */
  async listTemplates(category = null) {
    const params = category ? `?category=${category}` : '';
    const response = await apiClient.get(`/agent-builder/templates${params}`);
    return response.data;
  },
  
  /**
   * Get template details
   */
  async getTemplate(templateId) {
    const response = await apiClient.get(`/agent-builder/templates/${templateId}`);
    return response.data;
  },
  
  /**
   * Create agent from template
   */
  async createFromTemplate(templateId, customization) {
    const response = await apiClient.post(
      `/agent-builder/templates/${templateId}/create`,
      customization
    );
    return response.data;
  },
  
  // ========================================================================
  // AGENT EXECUTION
  // ========================================================================
  
  /**
   * Execute agent
   */
  async executeAgent(agentId, input) {
    const response = await apiClient.post(`/agents/${agentId}/execute`, {
      input_data: input,
    });
    return response.data;
  },
  
  /**
   * Get execution status
   */
  async getExecutionStatus(executionId) {
    const response = await apiClient.get(`/executions/${executionId}`);
    return response.data;
  },
  
  /**
   * Get execution logs
   */
  async getExecutionLogs(agentId, limit = 10) {
    const response = await apiClient.get(
      `/agents/${agentId}/executions?limit=${limit}`
    );
    return response.data;
  },
};

export default agentBuilderAPI;
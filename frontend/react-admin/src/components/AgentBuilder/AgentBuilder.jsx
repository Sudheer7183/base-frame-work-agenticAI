/**
 * Agent Builder UI Component
 * 
 * Comprehensive UI for creating and configuring agents with:
 * - LLM configuration
 * - Tool selection
 * - Database/API integration
 * - Trigger configuration
 * - HITL settings
 * - Output configuration
 * 
 * File: frontend/react-admin/src/components/AgentBuilder/AgentBuilder.jsx
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  Button,
  Typography,
  Paper,
  Grid,
  Alert,
  CircularProgress,
  Snackbar
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

// import BasicInfoStep from './steps/BasicInfoStep';
// import LLMConfigStep from './steps/LLMConfigStep';
// import ToolConfigStep from './steps/ToolConfigStep';
// import IntegrationStep from './steps/IntegrationStep';
// import TriggerStep from './steps/TriggerStep';
// import HITLConfigStep from './steps/HITLConfigStep';
// import OutputConfigStep from './steps/OutputConfigStep';

import { BasicInfoStep } from './steps';
import { LLMConfigStep } from './steps';
import { ToolConfigStep } from './steps';
import { IntegrationStep } from './steps';
import { TriggerStep } from './steps';
import { HITLConfigStep } from './steps';
import { OutputConfigStep } from './steps';

// import ReviewStep from './steps/ReviewStep';
import { ReviewStep } from './steps';

import { agentBuilderAPI } from '../../api/agentBuilderAPI';



const steps = [
  'Basic Info',
  'LLM Configuration',
  'Tools',
  'Integrations',
  'Triggers',
  'HITL',
  'Output',
  'Review'
];

const AgentBuilder = ({ agentId = null, onComplete }) => {
  // ========================================================================
  // STATE
  // ========================================================================
  
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [dropdownOptions, setDropdownOptions] = useState(null);
  const [availableTools, setAvailableTools] = useState([]);
  const [validationResult, setValidationResult] = useState(null);
  
  // Form data state
  const [formData, setFormData] = useState({
    // Basic Info
    name: '',
    description: '',
    workflow: 'simple',
    template_id: null,
    
    // LLM Configuration
    llm_config: {
      provider: 'openai',
      model: 'gpt-4',
      temperature: 0.7,
      max_tokens: 2000,
      api_endpoint: '',
      api_key_ref: ''
    },
    
    // Input Configuration
    input_config: {
      schema_definition: {},
      preprocessing_steps: [],
      validation_rules: {}
    },
    
    // Tool Configuration
    enabled_tools: [],
    tool_timeout_seconds: 300,
    max_tool_calls: 10,
    
    // Database Integration
    db_connection_id: null,
    db_queries: [],
    db_write_enabled: false,
    
    // API Integration
    api_endpoints: [],
    api_auth_method: null,
    api_rate_limit: null,
    
    // Data Sources
    data_sources: [],
    data_refresh_interval: null,
    
    // Output Configuration
    output_config: {
      format: 'json',
      destination: {},
      schema_definition: {},
      transformation: {}
    },
    
    // Trigger Configuration
    trigger_config: {
      trigger_type: 'manual',
      config: {},
      schedule_cron: '',
      event_listeners: []
    },
    
    // HITL Configuration
    hitl_config: {
      enabled: false,
      trigger_conditions: {},
      approval_required: false,
      timeout_minutes: 60,
      escalation_rules: {}
    },
    
    // Workflow Control
    workflow_control: {
      max_execution_time_seconds: 3600,
      retry_policy: {
        max_retries: 3,
        backoff_multiplier: 2
      },
      error_handling_strategy: 'fail',
      conditional_branches: [],
      loop_configuration: {},
      parallel_execution_enabled: false
    },
    
    // Monitoring
    logging_level: 'INFO',
    metrics_enabled: true,
    alert_rules: [],
    
    // Variables & Triggers
    variables: [],
    triggers: []
  });
  
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  
  // ========================================================================
  // EFFECTS
  // ========================================================================
  
  useEffect(() => {
    loadDropdownOptions();
    loadAvailableTools();
    
    if (agentId) {
      loadExistingAgent(agentId);
    }
  }, [agentId]);
  
  // ========================================================================
  // DATA LOADING
  // ========================================================================
  
  const loadDropdownOptions = async () => {
    try {
      const options = await agentBuilderAPI.getDropdownOptions();
      setDropdownOptions(options);
    } catch (error) {
      console.error('Error loading dropdown options:', error);
      showSnackbar('Error loading options', 'error');
    }
  };
  
  const loadAvailableTools = async () => {
    try {
      const tools = await agentBuilderAPI.getAvailableTools();
      setAvailableTools(tools);
    } catch (error) {
      console.error('Error loading tools:', error);
      showSnackbar('Error loading tools', 'error');
    }
  };
  
  const loadExistingAgent = async (id) => {
    setLoading(true);
    try {
      const agent = await agentBuilderAPI.getCompleteAgent(id);
      
      // Populate form with existing data
      setFormData({
        name: agent.agent.name,
        description: agent.agent.description,
        workflow: agent.agent.workflow,
        // ... map all other fields from agent.builder_config
      });
      
      showSnackbar('Agent loaded successfully', 'success');
    } catch (error) {
      console.error('Error loading agent:', error);
      showSnackbar('Error loading agent', 'error');
    } finally {
      setLoading(false);
    }
  };
  
  // ========================================================================
  // HANDLERS
  // ========================================================================
  
  const handleNext = async () => {
    // Validate current step
    const isValid = await validateCurrentStep();
    
    if (isValid) {
      setActiveStep((prev) => prev + 1);
    }
  };
  
  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };
  
  const handleUpdateFormData = (updates) => {
    setFormData((prev) => ({
      ...prev,
      ...updates
    }));
  };
  
  const handleUpdateNestedData = (path, value) => {
    setFormData((prev) => {
      const newData = { ...prev };
      const keys = path.split('.');
      let current = newData;
      
      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }
      
      current[keys[keys.length - 1]] = value;
      return newData;
    });
  };
  
  const validateCurrentStep = async () => {
    // Perform step-specific validation
    const currentStepData = getCurrentStepData();
    
    try {
      const result = await agentBuilderAPI.validateConfig({
        agent_config: {
          name: formData.name,
          workflow: formData.workflow
        },
        builder_config: currentStepData
      });
      
      setValidationResult(result);
      
      if (!result.is_valid) {
        showSnackbar(`Validation failed: ${result.errors[0]?.message}`, 'error');
        return false;
      }
      
      if (result.warnings.length > 0) {
        showSnackbar(`Warning: ${result.warnings[0]?.message}`, 'warning');
      }
      
      return true;
    } catch (error) {
      console.error('Validation error:', error);
      return true; // Allow proceeding even if validation API fails
    }
  };
  
  const getCurrentStepData = () => {
    switch (activeStep) {
      case 0:
        return { name: formData.name, description: formData.description, workflow: formData.workflow };
      case 1:
        return { llm_config: formData.llm_config };
      case 2:
        return { enabled_tools: formData.enabled_tools };
      case 3:
        return { 
          db_connection_id: formData.db_connection_id,
          api_endpoints: formData.api_endpoints
        };
      case 4:
        return { trigger_config: formData.trigger_config };
      case 5:
        return { hitl_config: formData.hitl_config };
      case 6:
        return { output_config: formData.output_config };
      default:
        return formData;
    }
  };
  
  const handleSave = async (asDraft = true) => {
    setSaving(true);
    
    try {
      // Prepare data for API
      const agentData = {
        name: formData.name,
        description: formData.description,
        workflow: formData.workflow,
        template_id: formData.template_id,
        builder_config: {
          agent_id: agentId || 0, // Will be set by backend for new agents
          llm_config: formData.llm_config,
          input_config: formData.input_config,
          enabled_tools: formData.enabled_tools,
          tool_timeout_seconds: formData.tool_timeout_seconds,
          max_tool_calls: formData.max_tool_calls,
          db_connection_id: formData.db_connection_id,
          db_queries: formData.db_queries,
          db_write_enabled: formData.db_write_enabled,
          api_endpoints: formData.api_endpoints,
          api_auth_method: formData.api_auth_method,
          api_rate_limit: formData.api_rate_limit,
          data_sources: formData.data_sources,
          data_refresh_interval: formData.data_refresh_interval,
          output_config: formData.output_config,
          trigger_config: formData.trigger_config,
          hitl_config: formData.hitl_config,
          workflow_control: formData.workflow_control,
          logging_level: formData.logging_level,
          metrics_enabled: formData.metrics_enabled,
          alert_rules: formData.alert_rules
        },
        variables: formData.variables,
        triggers: formData.triggers
      };
      
      let result;
      if (agentId) {
        // Update existing agent
        result = await agentBuilderAPI.updateAgent(agentId, agentData);
      } else {
        // Create new agent
        result = await agentBuilderAPI.createCompleteAgent(agentData);
      }
      
      showSnackbar(
        asDraft ? 'Agent saved as draft' : 'Agent created successfully',
        'success'
      );
      
      if (onComplete) {
        onComplete(result);
      }
      
      return result;
    } catch (error) {
      console.error('Error saving agent:', error);
      showSnackbar(`Error saving agent: ${error.message}`, 'error');
      throw error;
    } finally {
      setSaving(false);
    }
  };
  
  const handleTestAgent = async () => {
    try {
      showSnackbar('Testing agent...', 'info');
      
      // Save first if not saved
      if (!agentId) {
        const result = await handleSave(true);
        // Use the newly created agent ID for testing
        // Test logic would go here
      }
      
      // TODO: Implement test execution
      showSnackbar('Test not yet implemented', 'warning');
    } catch (error) {
      console.error('Error testing agent:', error);
      showSnackbar('Error testing agent', 'error');
    }
  };
  
  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({
      open: true,
      message,
      severity
    });
  };
  
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };
  
  // ========================================================================
  // RENDER
  // ========================================================================
  
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }
  
  return (
    <Box sx={{ width: '100%', p: 3 }}>
      {/* Header */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          {agentId ? 'Edit Agent' : 'Create New Agent'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Configure your agent with comprehensive options for LLM, tools, integrations, and more
        </Typography>
      </Paper>
      
      {/* Stepper */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Stepper activeStep={activeStep} alternativeLabel>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>
      
      {/* Validation Alerts */}
      {validationResult && !validationResult.is_valid && (
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="subtitle2">Validation Errors:</Typography>
          {validationResult.errors.map((error, idx) => (
            <Typography key={idx} variant="body2">
              • {error.field}: {error.message}
            </Typography>
          ))}
        </Alert>
      )}
      
      {validationResult && validationResult.warnings.length > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <Typography variant="subtitle2">Warnings:</Typography>
          {validationResult.warnings.map((warning, idx) => (
            <Typography key={idx} variant="body2">
              • {warning.field}: {warning.message}
            </Typography>
          ))}
        </Alert>
      )}
      
      {/* Step Content */}
      <Paper elevation={2} sx={{ p: 3, mb: 3, minHeight: '400px' }}>
        {activeStep === 0 && (
          <BasicInfoStep
            data={formData}
            onUpdate={handleUpdateFormData}
            dropdownOptions={dropdownOptions}
          />
        )}
        
        {activeStep === 1 && (
          <LLMConfigStep
            data={formData.llm_config}
            onUpdate={(llm_config) => handleUpdateFormData({ llm_config })}
            dropdownOptions={dropdownOptions}
          />
        )}
        
        {activeStep === 2 && (
          <ToolConfigStep
            data={{
              enabled_tools: formData.enabled_tools,
              tool_timeout_seconds: formData.tool_timeout_seconds,
              max_tool_calls: formData.max_tool_calls
            }}
            onUpdate={handleUpdateFormData}
            availableTools={availableTools}
          />
        )}
        
        {activeStep === 3 && (
          <IntegrationStep
            data={{
              db_connection_id: formData.db_connection_id,
              db_queries: formData.db_queries,
              db_write_enabled: formData.db_write_enabled,
              api_endpoints: formData.api_endpoints,
              api_auth_method: formData.api_auth_method,
              data_sources: formData.data_sources
            }}
            onUpdate={handleUpdateFormData}
          />
        )}
        
        {activeStep === 4 && (
          <TriggerStep
            data={formData.trigger_config}
            onUpdate={(trigger_config) => handleUpdateFormData({ trigger_config })}
            dropdownOptions={dropdownOptions}
          />
        )}
        
        {activeStep === 5 && (
          <HITLConfigStep
            data={formData.hitl_config}
            onUpdate={(hitl_config) => handleUpdateFormData({ hitl_config })}
          />
        )}
        
        {activeStep === 6 && (
          <OutputConfigStep
            data={formData.output_config}
            onUpdate={(output_config) => handleUpdateFormData({ output_config })}
            dropdownOptions={dropdownOptions}
          />
        )}
        
        {activeStep === 7 && (
          <ReviewStep
            data={formData}
            dropdownOptions={dropdownOptions}
          />
        )}
      </Paper>
      
      {/* Navigation Buttons */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Grid container spacing={2} justifyContent="space-between">
          <Grid item>
            <Button
              disabled={activeStep === 0}
              onClick={handleBack}
              variant="outlined"
            >
              Back
            </Button>
          </Grid>
          
          <Grid item>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="outlined"
                onClick={() => handleSave(true)}
                disabled={saving}
                startIcon={<SaveIcon />}
              >
                {saving ? 'Saving...' : 'Save as Draft'}
              </Button>
              
              {activeStep === steps.length - 1 ? (
                <>
                  <Button
                    variant="outlined"
                    onClick={handleTestAgent}
                    startIcon={<PlayArrowIcon />}
                  >
                    Test Agent
                  </Button>
                  <Button
                    variant="contained"
                    onClick={() => handleSave(false)}
                    disabled={saving}
                    startIcon={<CheckCircleIcon />}
                  >
                    Create Agent
                  </Button>
                </>
              ) : (
                <Button
                  variant="contained"
                  onClick={handleNext}
                >
                  Next
                </Button>
              )}
            </Box>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AgentBuilder;

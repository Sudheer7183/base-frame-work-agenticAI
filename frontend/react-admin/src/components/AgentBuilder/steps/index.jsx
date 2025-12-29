/**
 * Agent Builder Step Components
 * Individual step components for the agent builder wizard
 * 
 * File: frontend/react-admin/src/components/AgentBuilder/steps/index.js
 */

import React from 'react';
import {
  Box,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormControlLabel,
  Switch,
  Typography,
  Grid,
  Chip,
  IconButton,
  Button,
  Card,
  CardContent,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Slider,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Checkbox
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InfoIcon from '@mui/icons-material/Info';

// ============================================================================
// 1. BASIC INFO STEP
// ============================================================================

export const BasicInfoStep = ({ data, onUpdate, dropdownOptions }) => {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Basic Agent Information
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Provide basic information about your agent
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            required
            label="Agent Name"
            value={data.name}
            onChange={(e) => onUpdate({ name: e.target.value })}
            helperText="Unique name for your agent"
          />
        </Grid>
        
        <Grid item xs={12}>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Description"
            value={data.description}
            onChange={(e) => onUpdate({ description: e.target.value })}
            helperText="Describe what this agent does"
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <FormControl fullWidth>
            <InputLabel>Workflow Type</InputLabel>
            <Select
              value={data.workflow}
              onChange={(e) => onUpdate({ workflow: e.target.value })}
              label="Workflow Type"
            >
              {dropdownOptions?.workflow_types?.map((type) => (
                <MenuItem key={type.value} value={type.value}>
                  {type.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
      </Grid>
    </Box>
  );
};

// ============================================================================
// 2. LLM CONFIGURATION STEP
// ============================================================================

export const LLMConfigStep = ({ data, onUpdate, dropdownOptions }) => {
  const selectedProvider = data.provider;
  const availableModels = dropdownOptions?.llm_models?.[selectedProvider] || [];
  
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        LLM Configuration
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Configure the Language Model for your agent
      </Typography>
      
      <Grid container spacing={3}>
        {/* Provider Selection */}
        <Grid item xs={12} md={6}>
          <FormControl fullWidth>
            <InputLabel>LLM Provider</InputLabel>
            <Select
              value={data.provider}
              onChange={(e) => onUpdate({ ...data, provider: e.target.value, model: '' })}
              label="LLM Provider"
            >
              {dropdownOptions?.llm_providers?.map((provider) => (
                <MenuItem key={provider.value} value={provider.value}>
                  {provider.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        {/* Model Selection */}
        <Grid item xs={12} md={6}>
          <FormControl fullWidth>
            <InputLabel>Model</InputLabel>
            <Select
              value={data.model}
              onChange={(e) => onUpdate({ ...data, model: e.target.value })}
              label="Model"
              disabled={!selectedProvider}
            >
              {availableModels.map((model) => (
                <MenuItem key={model} value={model}>
                  {model}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        {/* Temperature */}
        <Grid item xs={12}>
          <Typography gutterBottom>
            Temperature: {data.temperature}
            <Tooltip title="Controls randomness. Lower = more focused, Higher = more creative">
              <IconButton size="small">
                <InfoIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Typography>
          <Slider
            value={data.temperature}
            onChange={(e, value) => onUpdate({ ...data, temperature: value })}
            min={0}
            max={2}
            step={0.1}
            marks={[
              { value: 0, label: '0' },
              { value: 0.7, label: '0.7' },
              { value: 1.5, label: '1.5' },
              { value: 2, label: '2' }
            ]}
          />
        </Grid>
        
        {/* Max Tokens */}
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            type="number"
            label="Max Tokens"
            value={data.max_tokens}
            onChange={(e) => onUpdate({ ...data, max_tokens: parseInt(e.target.value) })}
            helperText="Maximum tokens in response"
          />
        </Grid>
        
        {/* API Endpoint (Optional) */}
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="API Endpoint (Optional)"
            value={data.api_endpoint}
            onChange={(e) => onUpdate({ ...data, api_endpoint: e.target.value })}
            helperText="Custom API endpoint URL (leave blank for default)"
            placeholder="https://api.example.com/v1"
          />
        </Grid>
        
        {/* API Key Reference */}
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="API Key Reference"
            value={data.api_key_ref}
            onChange={(e) => onUpdate({ ...data, api_key_ref: e.target.value })}
            helperText="Reference to secure API key storage"
            placeholder="OPENAI_API_KEY"
          />
        </Grid>
      </Grid>
    </Box>
  );
};

// ============================================================================
// 3. TOOL CONFIGURATION STEP
// ============================================================================

export const ToolConfigStep = ({ data, onUpdate, availableTools }) => {
  const [selectedCategory, setSelectedCategory] = React.useState('all');
  
  const categories = ['all', ...new Set(availableTools.map(t => t.category))];
  
  const filteredTools = selectedCategory === 'all'
    ? availableTools
    : availableTools.filter(t => t.category === selectedCategory);
  
  const handleToggleTool = (tool) => {
    const isEnabled = data.enabled_tools.some(t => t.tool_id === tool.id);
    
    if (isEnabled) {
      onUpdate({
        enabled_tools: data.enabled_tools.filter(t => t.tool_id !== tool.id)
      });
    } else {
      onUpdate({
        enabled_tools: [
          ...data.enabled_tools,
          {
            tool_id: tool.id,
            tool_name: tool.name,
            enabled: true,
            configuration: {},
            timeout_override: null
          }
        ]
      });
    }
  };
  
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Tool Configuration
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Select tools that your agent can use
      </Typography>
      
      <Grid container spacing={3}>
        {/* Global Tool Settings */}
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            type="number"
            label="Tool Timeout (seconds)"
            value={data.tool_timeout_seconds}
            onChange={(e) => onUpdate({ tool_timeout_seconds: parseInt(e.target.value) })}
          />
        </Grid>
        
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            type="number"
            label="Max Tool Calls"
            value={data.max_tool_calls}
            onChange={(e) => onUpdate({ max_tool_calls: parseInt(e.target.value) })}
          />
        </Grid>
        
        {/* Category Filter */}
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel>Filter by Category</InputLabel>
            <Select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              label="Filter by Category"
            >
              {categories.map((cat) => (
                <MenuItem key={cat} value={cat}>
                  {cat === 'all' ? 'All Categories' : cat}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        {/* Available Tools List */}
        <Grid item xs={12}>
          <Typography variant="subtitle1" gutterBottom>
            Available Tools ({data.enabled_tools.length} selected)
          </Typography>
          <List>
            {filteredTools.map((tool) => {
              const isEnabled = data.enabled_tools.some(t => t.tool_id === tool.id);
              
              return (
                <Card key={tool.id} sx={{ mb: 1 }}>
                  <CardContent>
                    <Grid container alignItems="center">
                      <Grid item xs>
                        <Typography variant="subtitle1">
                          {tool.display_name}
                          {tool.is_premium && (
                            <Chip label="Premium" size="small" color="warning" sx={{ ml: 1 }} />
                          )}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {tool.description}
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                          <Chip label={tool.tool_type} size="small" sx={{ mr: 0.5 }} />
                          <Chip label={tool.category} size="small" />
                        </Box>
                      </Grid>
                      <Grid item>
                        <Checkbox
                          checked={isEnabled}
                          onChange={() => handleToggleTool(tool)}
                        />
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              );
            })}
          </List>
        </Grid>
      </Grid>
    </Box>
  );
};

// ============================================================================
// 4. INTEGRATION STEP
// ============================================================================

export const IntegrationStep = ({ data, onUpdate }) => {
  const [newEndpoint, setNewEndpoint] = React.useState({ url: '', method: 'GET' });
  
  const handleAddEndpoint = () => {
    if (newEndpoint.url) {
      onUpdate({
        api_endpoints: [...data.api_endpoints, newEndpoint]
      });
      setNewEndpoint({ url: '', method: 'GET' });
    }
  };
  
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Integrations
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Configure database and API integrations
      </Typography>
      
      <Grid container spacing={3}>
        {/* Database Connection */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>Database Connection</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Database Connection</InputLabel>
                    <Select
                      value={data.db_connection_id || ''}
                      onChange={(e) => onUpdate({ db_connection_id: e.target.value })}
                      label="Database Connection"
                    >
                      <MenuItem value="">None</MenuItem>
                      {/* Database connections would be loaded dynamically */}
                      <MenuItem value={1}>Production DB</MenuItem>
                      <MenuItem value={2}>Analytics DB</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={data.db_write_enabled}
                        onChange={(e) => onUpdate({ db_write_enabled: e.target.checked })}
                      />
                    }
                    label="Enable Write Operations"
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>
        
        {/* API Endpoints */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>API Endpoints</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={8}>
                  <TextField
                    fullWidth
                    label="API Endpoint URL"
                    value={newEndpoint.url}
                    onChange={(e) => setNewEndpoint({ ...newEndpoint, url: e.target.value })}
                    placeholder="https://api.example.com/endpoint"
                  />
                </Grid>
                <Grid item xs={3}>
                  <FormControl fullWidth>
                    <InputLabel>Method</InputLabel>
                    <Select
                      value={newEndpoint.method}
                      onChange={(e) => setNewEndpoint({ ...newEndpoint, method: e.target.value })}
                      label="Method"
                    >
                      <MenuItem value="GET">GET</MenuItem>
                      <MenuItem value="POST">POST</MenuItem>
                      <MenuItem value="PUT">PUT</MenuItem>
                      <MenuItem value="DELETE">DELETE</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={1}>
                  <Button
                    variant="contained"
                    onClick={handleAddEndpoint}
                    fullWidth
                    sx={{ height: '56px' }}
                  >
                    <AddIcon />
                  </Button>
                </Grid>
                
                <Grid item xs={12}>
                  {data.api_endpoints.map((endpoint, idx) => (
                    <Chip
                      key={idx}
                      label={`${endpoint.method} ${endpoint.url}`}
                      onDelete={() => {
                        onUpdate({
                          api_endpoints: data.api_endpoints.filter((_, i) => i !== idx)
                        });
                      }}
                      sx={{ m: 0.5 }}
                    />
                  ))}
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>
      </Grid>
    </Box>
  );
};

// ============================================================================
// 5. TRIGGER STEP
// ============================================================================

export const TriggerStep = ({ data, onUpdate, dropdownOptions }) => {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Execution Triggers
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Configure when and how your agent will be triggered
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel>Trigger Type</InputLabel>
            <Select
              value={data.trigger_type}
              onChange={(e) => onUpdate({ ...data, trigger_type: e.target.value })}
              label="Trigger Type"
            >
              {dropdownOptions?.trigger_types?.map((type) => (
                <MenuItem key={type.value} value={type.value}>
                  {type.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        {data.trigger_type === 'scheduled' && (
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Cron Expression"
              value={data.schedule_cron}
              onChange={(e) => onUpdate({ ...data, schedule_cron: e.target.value })}
              helperText="Example: 0 9 * * * (every day at 9 AM)"
              placeholder="0 9 * * *"
            />
          </Grid>
        )}
        
        {data.trigger_type === 'webhook' && (
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Webhook URL"
              value={data.config.webhook_url || ''}
              onChange={(e) => onUpdate({
                ...data,
                config: { ...data.config, webhook_url: e.target.value }
              })}
              helperText="URL that will trigger this agent"
            />
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

// ============================================================================
// 6. HITL CONFIGURATION STEP
// ============================================================================

export const HITLConfigStep = ({ data, onUpdate }) => {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Human-in-the-Loop (HITL) Configuration
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Configure human approval and intervention settings
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <FormControlLabel
            control={
              <Switch
                checked={data.enabled}
                onChange={(e) => onUpdate({ ...data, enabled: e.target.checked })}
              />
            }
            label="Enable HITL"
          />
        </Grid>
        
        {data.enabled && (
          <>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={data.approval_required}
                    onChange={(e) => onUpdate({ ...data, approval_required: e.target.checked })}
                  />
                }
                label="Require Approval Before Execution"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Timeout (minutes)"
                value={data.timeout_minutes}
                onChange={(e) => onUpdate({ ...data, timeout_minutes: parseInt(e.target.value) })}
                helperText="Time to wait for human response"
              />
            </Grid>
          </>
        )}
      </Grid>
    </Box>
  );
};

// ============================================================================
// 7. OUTPUT CONFIGURATION STEP
// ============================================================================

export const OutputConfigStep = ({ data, onUpdate, dropdownOptions }) => {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Output Configuration
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Configure how agent output will be formatted and delivered
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel>Output Format</InputLabel>
            <Select
              value={data.format}
              onChange={(e) => onUpdate({ ...data, format: e.target.value })}
              label="Output Format"
            >
              {dropdownOptions?.output_formats?.map((format) => (
                <MenuItem key={format.value} value={format.value}>
                  {format.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        {data.format === 'database' && (
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Target Table"
              value={data.destination.table || ''}
              onChange={(e) => onUpdate({
                ...data,
                destination: { ...data.destination, table: e.target.value }
              })}
              placeholder="table_name"
            />
          </Grid>
        )}
        
        {data.format === 'api' && (
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="API Endpoint"
              value={data.destination.url || ''}
              onChange={(e) => onUpdate({
                ...data,
                destination: { ...data.destination, url: e.target.value }
              })}
              placeholder="https://api.example.com/endpoint"
            />
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

// ============================================================================
// 8. REVIEW STEP
// ============================================================================

export const ReviewStep = ({ data, dropdownOptions }) => {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Review Configuration
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Review your agent configuration before creating
      </Typography>
      
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Basic Info
              </Typography>
              <Typography variant="body2">Name: {data.name}</Typography>
              <Typography variant="body2">Workflow: {data.workflow}</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                LLM Configuration
              </Typography>
              <Typography variant="body2">Provider: {data.llm_config.provider}</Typography>
              <Typography variant="body2">Model: {data.llm_config.model}</Typography>
              <Typography variant="body2">Temperature: {data.llm_config.temperature}</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Tools ({data.enabled_tools.length} enabled)
              </Typography>
              {data.enabled_tools.map((tool, idx) => (
                <Chip key={idx} label={tool.tool_name} sx={{ m: 0.5 }} />
              ))}
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Trigger & Output
              </Typography>
              <Typography variant="body2">Trigger: {data.trigger_config.trigger_type}</Typography>
              <Typography variant="body2">Output Format: {data.output_config.format}</Typography>
              <Typography variant="body2">HITL: {data.hitl_config.enabled ? 'Enabled' : 'Disabled'}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default {
  BasicInfoStep,
  LLMConfigStep,
  ToolConfigStep,
  IntegrationStep,
  TriggerStep,
  HITLConfigStep,
  OutputConfigStep,
  ReviewStep
};

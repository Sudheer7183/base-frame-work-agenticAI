/**
 * Invite User Page - FINAL FIXED VERSION
 * 
 * File: frontend/react-admin/src/pages/InviteUserPage.jsx
 * Uses: apiClient for consistent API calls
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { apiClient } from '../utils/apiClient';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  FormControl,
  FormControlLabel,
  Checkbox,
  Alert,
  AlertTitle,
  Chip,
  Select,
  MenuItem,
  InputLabel,
  CircularProgress,
  Paper,
  Divider
} from '@mui/material';
import {
  Email as EmailIcon,
  Send as SendIcon,
  ArrowBack as ArrowBackIcon,
  Info as InfoIcon,
  Person as PersonIcon,
  Security as SecurityIcon
} from '@mui/icons-material';

const InviteUserPage = () => {
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    roles: ['USER'],
    send_email: true,
    custom_message: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const availableRoles = [
    { value: 'USER', label: 'User', description: 'Standard access to platform features' },
    { value: 'ADMIN', label: 'Admin', description: 'Manage users and tenant settings' },
    { value: 'VIEWER', label: 'Viewer', description: 'Read-only access' }
  ];

  const handleChange = (field) => (event) => {
    setFormData(prev => ({ ...prev, [field]: event.target.value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const handleRoleChange = (event) => {
    const value = event.target.value;
    setFormData(prev => ({ ...prev, roles: typeof value === 'string' ? [value] : value }));
  };

  const handleCheckboxChange = (field) => (event) => {
    setFormData(prev => ({ ...prev, [field]: event.target.checked }));
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }
    
    if (!formData.roles || formData.roles.length === 0) {
      newErrors.roles = 'At least one role must be selected';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    
    try {
      // Use apiClient for consistent API calls
      const data = await apiClient.post('/api/v1/users/invite', formData);
      
      console.log('Invitation created:', data);
      
      toast.success(
        formData.send_email 
          ? `Invitation sent to ${formData.email}!`
          : `User invitation created for ${formData.email}`
      );
      
      // Reset form
      setFormData({
        email: '',
        full_name: '',
        roles: ['USER'],
        send_email: true,
        custom_message: ''
      });
      
      // Navigate back
      setTimeout(() => {
        navigate('/admin/users');
      }, 1500);
      
    } catch (error) {
      console.error('Invitation error:', error);
      toast.error(error.message || 'Failed to send invitation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
      <Box sx={{ mb: 3 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/admin/users')}
          sx={{ mb: 2 }}
        >
          Back to Users
        </Button>
        
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <EmailIcon fontSize="large" />
          Invite New User
        </Typography>
        
        <Typography variant="body2" color="text.secondary">
          Send an invitation email to a new user. They'll access the platform after SSO login.
        </Typography>
      </Box>

      <Alert severity="info" icon={<InfoIcon />} sx={{ mb: 3 }}>
        <AlertTitle>How SSO Invitations Work</AlertTitle>
        <Typography variant="body2">
          1. Enter user's corporate email<br />
          2. They receive invitation email<br />
          3. They login via SSO<br />
          4. Account automatically activated
        </Typography>
      </Alert>

      <Card>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <Box sx={{ mb: 3 }}>
              <TextField
                fullWidth
                required
                label="Email Address"
                type="email"
                value={formData.email}
                onChange={handleChange('email')}
                error={!!errors.email}
                helperText={errors.email || "User's corporate email"}
                placeholder="john.doe@company.com"
                InputProps={{
                  startAdornment: <EmailIcon sx={{ mr: 1, color: 'action.active' }} />
                }}
              />
            </Box>

            <Box sx={{ mb: 3 }}>
              <TextField
                fullWidth
                label="Full Name (Optional)"
                value={formData.full_name}
                onChange={handleChange('full_name')}
                placeholder="John Doe"
                helperText="Pre-filled in their profile"
                InputProps={{
                  startAdornment: <PersonIcon sx={{ mr: 1, color: 'action.active' }} />
                }}
              />
            </Box>

            <Box sx={{ mb: 3 }}>
              <FormControl fullWidth error={!!errors.roles}>
                <InputLabel>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <SecurityIcon fontSize="small" />
                    Roles *
                  </Box>
                </InputLabel>
                <Select
                  multiple
                  value={formData.roles}
                  onChange={handleRoleChange}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  {availableRoles.map((role) => (
                    <MenuItem key={role.value} value={role.value}>
                      <Box>
                        <Typography variant="body1">{role.label}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {role.description}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
                {errors.roles && (
                  <Typography variant="caption" color="error" sx={{ mt: 0.5 }}>
                    {errors.roles}
                  </Typography>
                )}
              </FormControl>
            </Box>

            <Box sx={{ mb: 3 }}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Custom Message (Optional)"
                value={formData.custom_message}
                onChange={handleChange('custom_message')}
                placeholder="Welcome to our team!"
                helperText={`Personal message in email (${formData.custom_message.length}/500)`}
                inputProps={{ maxLength: 500 }}
              />
            </Box>

            <Divider sx={{ my: 3 }} />

            <Box sx={{ mb: 3 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.send_email}
                    onChange={handleCheckboxChange('send_email')}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1">Send invitation email</Typography>
                    <Typography variant="caption" color="text.secondary">
                      User will receive email with activation instructions
                    </Typography>
                  </Box>
                }
              />
            </Box>

            {formData.email && (
              <Paper variant="outlined" sx={{ p: 2, mb: 3, bgcolor: 'grey.50' }}>
                <Typography variant="subtitle2" gutterBottom>
                  Invitation Preview
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>To:</strong> {formData.email}<br />
                  <strong>Roles:</strong> {formData.roles.join(', ')}<br />
                  {formData.full_name && (
                    <>
                      <strong>Name:</strong> {formData.full_name}<br />
                    </>
                  )}
                  <strong>Expires:</strong> 7 days from now
                </Typography>
              </Paper>
            )}

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button
                variant="outlined"
                onClick={() => navigate('/admin/users')}
                disabled={loading}
              >
                Cancel
              </Button>
              
              <Button
                type="submit"
                variant="contained"
                startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
                disabled={loading}
              >
                {loading ? 'Sending...' : 'Send Invitation'}
              </Button>
            </Box>
          </form>
        </CardContent>
      </Card>

      <Alert severity="warning" sx={{ mt: 3 }}>
        <AlertTitle>Important Notes</AlertTitle>
        <ul style={{ margin: 0, paddingLeft: 20 }}>
          <li>Invitations expire after 7 days</li>
          <li>Users must use corporate SSO to accept</li>
          <li>You can resend or cancel from user list</li>
        </ul>
      </Alert>
    </Box>
  );
};

export default InviteUserPage;
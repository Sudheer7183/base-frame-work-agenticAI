/**
 * Accept Invitation Page
 * 
 * File: frontend/react-admin/src/pages/AcceptInvitationPage.jsx
 * Purpose: Landing page for users to accept invitations via SSO
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'react-toastify';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
  AlertTitle,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Email as EmailIcon,
  Business as BusinessIcon,
  Security as SecurityIcon,
  Login as LoginIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';

const AcceptInvitationPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const [loading, setLoading] = useState(true);
  const [invitation, setInvitation] = useState(null);
  const [error, setError] = useState(null);
  const [ssoProviders, setSsoProviders] = useState([]);

  const invitationToken = searchParams.get('token');

  useEffect(() => {
    if (!invitationToken) {
      setError('Invalid invitation link - no token provided');
      setLoading(false);
      return;
    }

    fetchInvitationDetails();
    fetchSsoProviders();
  }, [invitationToken]);

  const fetchInvitationDetails = async () => {
    try {
      // In a real implementation, you'd have an endpoint to verify the token
      // and get invitation details without requiring authentication
      // For now, we'll simulate this
      
      setLoading(false);
      
      // Simulated invitation data
      // In production, call: GET /api/v1/auth/invitation/{token}
      setInvitation({
        email: 'john.doe@company.com',
        tenant_name: 'Acme Corporation',
        invited_by: 'Jane Smith',
        invited_by_email: 'jane.smith@company.com',
        roles: ['USER'],
        invited_at: new Date(),
        expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
      });
      
    } catch (err) {
      console.error('Failed to fetch invitation:', err);
      setError('Failed to load invitation details');
      setLoading(false);
    }
  };

  const fetchSsoProviders = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/auth/sso/providers');
      
      if (response.ok) {
        const data = await response.json();
        setSsoProviders(data.providers || []);
      }
    } catch (err) {
      console.error('Failed to fetch SSO providers:', err);
      // Continue anyway, we'll show default providers
    }
  };

  const handleSsoLogin = (provider) => {
    // Redirect to SSO login with invitation token
    const keycloakUrl = 'http://localhost:8080';
    const realm = 'agentic';
    const clientId = 'agentic-api';
    const redirectUri = encodeURIComponent(`${window.location.origin}/auth/callback`);
    const state = encodeURIComponent(JSON.stringify({ invitation_token: invitationToken }));
    
    // Build authorization URL
    let authUrl = `${keycloakUrl}/realms/${realm}/protocol/openid-connect/auth?` +
      `client_id=${clientId}&` +
      `redirect_uri=${redirectUri}&` +
      `response_type=code&` +
      `scope=openid email profile&` +
      `state=${state}`;
    
    // Add identity provider hint if available
    if (provider && provider.alias) {
      authUrl += `&kc_idp_hint=${provider.alias}`;
    }
    
    // Redirect to Keycloak
    window.location.href = authUrl;
  };

  const isExpired = () => {
    if (!invitation?.expires_at) return false;
    return new Date() > new Date(invitation.expires_at);
  };

  const formatDate = (date) => {
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        flexDirection: 'column',
        gap: 2
      }}>
        <CircularProgress size={60} />
        <Typography variant="h6" color="text.secondary">
          Loading your invitation...
        </Typography>
      </Box>
    );
  }

  if (error || !invitation) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        p: 3
      }}>
        <Card sx={{ maxWidth: 500 }}>
          <CardContent>
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <ErrorIcon sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                Invalid Invitation
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {error || 'This invitation link is invalid or has expired.'}
              </Typography>
            </Box>
            
            <Button
              fullWidth
              variant="outlined"
              onClick={() => navigate('/')}
            >
              Go to Home
            </Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

  if (isExpired()) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        p: 3
      }}>
        <Card sx={{ maxWidth: 500 }}>
          <CardContent>
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <ScheduleIcon sx={{ fontSize: 80, color: 'warning.main', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                Invitation Expired
              </Typography>
              <Typography variant="body2" color="text.secondary">
                This invitation expired on {formatDate(invitation.expires_at)}.
              </Typography>
            </Box>
            
            <Alert severity="info" sx={{ mb: 2 }}>
              Please contact {invitation.invited_by} ({invitation.invited_by_email}) to request a new invitation.
            </Alert>
            
            <Button
              fullWidth
              variant="outlined"
              onClick={() => navigate('/')}
            >
              Go to Home
            </Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
    <Box sx={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      p: 3
    }}>
      <Card sx={{ maxWidth: 600, width: '100%' }}>
        <CardContent sx={{ p: 4 }}>
          {/* Header */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Box sx={{ 
              bgcolor: 'success.light', 
              borderRadius: '50%', 
              width: 80, 
              height: 80, 
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              margin: '0 auto',
              mb: 2
            }}>
              <EmailIcon sx={{ fontSize: 40, color: 'success.dark' }} />
            </Box>
            
            <Typography variant="h4" gutterBottom fontWeight="bold">
              You're Invited!
            </Typography>
            
            <Typography variant="body1" color="text.secondary">
              {invitation.invited_by} has invited you to join their team
            </Typography>
          </Box>

          {/* Invitation Details */}
          <Paper variant="outlined" sx={{ p: 3, mb: 3, bgcolor: 'grey.50' }}>
            <List dense>
              <ListItem>
                <ListItemIcon>
                  <BusinessIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="Organization"
                  secondary={invitation.tenant_name}
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <EmailIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="Your Email"
                  secondary={invitation.email}
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <SecurityIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="Access Level"
                  secondary={
                    <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                      {invitation.roles.map(role => (
                        <Chip key={role} label={role} size="small" color="primary" variant="outlined" />
                      ))}
                    </Box>
                  }
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <ScheduleIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="Expires"
                  secondary={formatDate(invitation.expires_at)}
                />
              </ListItem>
            </List>
          </Paper>

          {/* Instructions */}
          <Alert severity="info" sx={{ mb: 3 }}>
            <AlertTitle>Next Steps</AlertTitle>
            <Typography variant="body2">
              Click the button below to login with your corporate Single Sign-On (SSO). 
              Your account will be automatically activated after you login.
            </Typography>
          </Alert>

          <Divider sx={{ my: 3 }} />

          {/* SSO Login Buttons */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom sx={{ mb: 2 }}>
              Sign in to accept this invitation:
            </Typography>
            
            {ssoProviders.length > 0 ? (
              ssoProviders.filter(p => p.enabled).map(provider => (
                <Button
                  key={provider.alias}
                  fullWidth
                  variant="contained"
                  size="large"
                  startIcon={<LoginIcon />}
                  endIcon={<ArrowForwardIcon />}
                  onClick={() => handleSsoLogin(provider)}
                  sx={{ 
                    mb: 1.5,
                    textTransform: 'none',
                    justifyContent: 'space-between',
                    px: 3
                  }}
                >
                  {provider.display_name || `Login with ${provider.name}`}
                </Button>
              ))
            ) : (
              <Button
                fullWidth
                variant="contained"
                size="large"
                startIcon={<LoginIcon />}
                endIcon={<ArrowForwardIcon />}
                onClick={() => handleSsoLogin(null)}
                sx={{ 
                  mb: 1.5,
                  textTransform: 'none',
                  justifyContent: 'space-between',
                  px: 3
                }}
              >
                Login with Single Sign-On
              </Button>
            )}
          </Box>

          {/* Footer Note */}
          <Box sx={{ mt: 4, pt: 3, borderTop: 1, borderColor: 'divider' }}>
            <Typography variant="caption" color="text.secondary" align="center" display="block">
              By accepting this invitation, you agree to the terms and conditions of {invitation.tenant_name}.
              If you didn't expect this invitation, you can safely ignore this email.
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default AcceptInvitationPage;
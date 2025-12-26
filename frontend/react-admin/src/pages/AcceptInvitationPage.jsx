/**
 * Accept Invitation Page - FIXED VERSION
 * 
 * File: frontend/react-admin/src/pages/AcceptInvitationPage.jsx
 * 
 * FIXES:
 * 1. Actually fetch invitation details from backend
 * 2. Pass invitation_token correctly in SSO redirect
 * 3. Handle errors properly
 * 4. Use correct Keycloak configuration
 */

import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  AlertTitle,
  Chip,
  CircularProgress,
  Divider
} from '@mui/material';
import {
  Email as EmailIcon,
  Business as BusinessIcon,
  Security as SecurityIcon,
  AccessTime as AccessTimeIcon,
  Login as LoginIcon,
  ArrowForward as ArrowForwardIcon,
  Error as ErrorIcon
} from '@mui/icons-material';

const AcceptInvitationPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const invitationToken = searchParams.get('token');
  
  const [loading, setLoading] = useState(true);
  const [invitation, setInvitation] = useState(null);
  const [error, setError] = useState(null);
  const [ssoProviders, setSsoProviders] = useState([]);

  useEffect(() => {
    if (!invitationToken) {
      setError('No invitation token provided');
      setLoading(false);
      return;
    }

    fetchInvitationDetails();
    fetchSsoProviders();
  }, [invitationToken]);

  const fetchInvitationDetails = async () => {
    try {
      setLoading(true);
      
      // ✅ FIX 1: Actually call backend to get invitation details
      const response = await fetch(
        `http://127.0.0.1:8000/api/v1/auth/invitation/${invitationToken}`
      );
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Invitation not found or has expired');
        }
        if (response.status === 410) {
          throw new Error('This invitation has already been accepted');
        }
        throw new Error('Failed to load invitation details');
      }
      
      const data = await response.json();
      setInvitation(data);
      setLoading(false);
      
    } catch (err) {
      console.error('Failed to fetch invitation:', err);
      setError(err.message || 'Failed to load invitation details');
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
      // Continue anyway with default
    }
  };

  const handleSsoLogin = (provider) => {
    try {
      // ✅ FIX 2: Use correct Keycloak configuration
      const keycloakUrl = 'http://localhost:8080';
      const realm = 'agentic';
      const clientId = 'agentic-frontend';  // ← FIXED: Use frontend client
      const redirectUri = `${window.location.origin}/auth/callback`;
      
      // ✅ FIX 3: Properly encode state with invitation token
      const stateData = {
        invitation_token: invitationToken,
        return_url: window.location.origin
      };
      
      const state = btoa(JSON.stringify(stateData));
      
      // Build Keycloak auth URL
      let authUrl = `${keycloakUrl}/realms/${realm}/protocol/openid-connect/auth?` +
        `client_id=${clientId}&` +
        `redirect_uri=${encodeURIComponent(redirectUri)}&` +
        `response_type=code&` +
        `scope=openid%20email%20profile&` +
        `state=${encodeURIComponent(state)}`;
      
      // If specific provider requested, hint Keycloak to use it
      if (provider && provider.alias) {
        authUrl += `&kc_idp_hint=${provider.alias}`;
      }
      
      console.log('Redirecting to SSO:', authUrl);
      console.log('State:', stateData);
      
      // Redirect to Keycloak
      window.location.href = authUrl;
      
    } catch (err) {
      console.error('SSO login error:', err);
      setError('Failed to initiate SSO login');
    }
  };

  const isExpired = () => {
    if (!invitation || !invitation.expires_at) return false;
    return new Date(invitation.expires_at) < new Date();
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Loading state
  if (loading) {
    return (
      <Box sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <Card sx={{ p: 4, maxWidth: 400 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
            <CircularProgress size={60} />
            <Typography variant="h6" color="text.secondary">
              Loading invitation...
            </Typography>
          </Box>
        </Card>
      </Box>
    );
  }

  // Error state
  if (error || !invitation) {
    return (
      <Box sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        p: 3
      }}>
        <Card sx={{ maxWidth: 500, width: '100%' }}>
          <CardContent sx={{ textAlign: 'center', p: 4 }}>
            <ErrorIcon sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
            <Typography variant="h4" gutterBottom color="error">
              Invalid Invitation
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              {error || 'This invitation link is invalid or has expired.'}
            </Typography>
            <Alert severity="info" sx={{ mt: 3, textAlign: 'left' }}>
              <AlertTitle>What can I do?</AlertTitle>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                <li>Contact your administrator to send a new invitation</li>
                <li>Check if you used the correct link from your email</li>
                <li>Make sure the invitation hasn't expired</li>
              </ul>
            </Alert>
            <Button
              variant="contained"
              onClick={() => navigate('/')}
              sx={{ mt: 3 }}
            >
              Go to Home
            </Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

  // Expired invitation
  if (isExpired()) {
    return (
      <Box sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        p: 3
      }}>
        <Card sx={{ maxWidth: 500, width: '100%' }}>
          <CardContent sx={{ textAlign: 'center', p: 4 }}>
            <AccessTimeIcon sx={{ fontSize: 80, color: 'warning.main', mb: 2 }} />
            <Typography variant="h4" gutterBottom color="warning.main">
              Invitation Expired
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              This invitation expired on {formatDate(invitation.expires_at)}.
            </Typography>
            <Alert severity="info" sx={{ mt: 3, textAlign: 'left' }}>
              <AlertTitle>Request a New Invitation</AlertTitle>
              Please contact <strong>{invitation.invited_by_email}</strong> or your administrator
              to send you a new invitation.
            </Alert>
            <Button
              variant="contained"
              onClick={() => navigate('/')}
              sx={{ mt: 3 }}
            >
              Go to Home
            </Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

  // Valid invitation - show acceptance page
  return (
    <Box sx={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      p: 3
    }}>
      <Card sx={{ maxWidth: 600, width: '100%' }}>
        <CardContent sx={{ p: 4 }}>
          {/* Header */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Box sx={{
              width: 80,
              height: 80,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px'
            }}>
              <EmailIcon sx={{ fontSize: 40, color: 'white' }} />
            </Box>
            <Typography variant="h4" gutterBottom fontWeight="bold">
              You're Invited!
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {invitation.invited_by} has invited you to join their team
            </Typography>
          </Box>

          {/* Invitation Details */}
          <Box sx={{ bgcolor: 'grey.50', borderRadius: 2, p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <BusinessIcon color="action" />
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Organization
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {invitation.tenant_name}
                </Typography>
              </Box>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <EmailIcon color="action" />
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Your Email
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {invitation.email}
                </Typography>
              </Box>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <SecurityIcon color="action" />
              <Box sx={{ flex: 1 }}>
                <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                  Access Level
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {invitation.roles.map((role) => (
                    <Chip
                      key={role}
                      label={role}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  ))}
                </Box>
              </Box>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <AccessTimeIcon color="action" />
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Expires
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {formatDate(invitation.expires_at)}
                </Typography>
              </Box>
            </Box>
          </Box>

          {/* Instructions */}
          <Alert severity="info" icon={<LoginIcon />} sx={{ mb: 3 }}>
            <AlertTitle>Next Steps</AlertTitle>
            <Typography variant="body2">
              Click the button below to login with your corporate Single Sign-On (SSO).
              Your account will be automatically activated after you login.
            </Typography>
          </Alert>

          <Divider sx={{ my: 3 }} />

          {/* SSO Login Button */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom sx={{ mb: 2 }}>
              Sign in to accept this invitation:
            </Typography>
            
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
                px: 3,
                py: 1.5,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #5568d3 0%, #6941a0 100%)',
                }
              }}
            >
              Login with Single Sign-On
            </Button>
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
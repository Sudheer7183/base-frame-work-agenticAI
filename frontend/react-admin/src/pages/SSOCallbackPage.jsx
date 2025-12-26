/**
 * SSO Callback Page
 * 
 * File: frontend/react-admin/src/pages/SSOCallbackPage.jsx
 * 
 * Purpose: Handle OAuth callback from Keycloak after SSO login
 * This page receives the authorization code and exchanges it for tokens
 */

import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box,
  CircularProgress,
  Typography,
  Alert,
  AlertTitle,
  Card,
  CardContent
} from '@mui/material';

const SSOCallbackPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [status, setStatus] = useState('Processing authentication...');
  const [error, setError] = useState(null);

  useEffect(() => {
    handleCallback();
  }, []);

  const handleCallback = async () => {
    try {
      // Extract parameters from URL
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const errorParam = searchParams.get('error');
      const errorDescription = searchParams.get('error_description');
      
      // Check for OAuth errors
      if (errorParam) {
        throw new Error(errorDescription || errorParam);
      }
      
      if (!code) {
        throw new Error('No authorization code received from SSO provider');
      }
      
      console.log('SSO Callback - Code received');
      console.log('State:', state);
      
      // Decode state to get invitation token
      let invitationToken = null;
      if (state) {
        try {
          const stateData = JSON.parse(atob(state));
          invitationToken = stateData.invitation_token;
          console.log('Invitation token from state:', invitationToken);
        } catch (e) {
          console.warn('Could not parse state:', e);
        }
      }
      
      setStatus('Exchanging authorization code for access token...');
      
      // Build callback URL
      let callbackUrl = `/api/v1/auth/sso/callback?code=${encodeURIComponent(code)}`;
      
      if (invitationToken) {
        callbackUrl += `&invitation_token=${encodeURIComponent(invitationToken)}`;
      }
      
      console.log('Calling backend:', callbackUrl);
      
      // Call backend SSO callback
      const response = await fetch(callbackUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Backend response status:', response.status);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('Backend error:', errorData);
        
        throw new Error(
          errorData.detail || 
          `Authentication failed (${response.status})`
        );
      }
      
      const data = await response.json();
      console.log('Authentication successful:', data);
      
      setStatus('Login successful! Redirecting...');
      
      // Store authentication tokens
      localStorage.setItem('access_token', data.access_token);
      
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }
      
      // Store tenant information
      if (data.user?.tenant) {
        localStorage.setItem('current_tenant', JSON.stringify({
          slug: data.user.tenant,
          name: data.user.tenant
        }));
      }
      
      // Store user info (optional)
      if (data.user) {
        localStorage.setItem('user', JSON.stringify(data.user));
      }
      
      // Redirect to application
      setTimeout(() => {
        if (data.invitation_accepted) {
          // New user - show welcome message
          navigate('/admin/tenants', {
            state: {
              message: data.message || 'Welcome! Your account has been activated.',
              type: 'success'
            }
          });
        } else {
          // Existing user
          navigate('/admin/tenants', {
            state: {
              message: data.message || 'Welcome back!',
              type: 'success'
            }
          });
        }
      }, 1000);
      
    } catch (err) {
      console.error('SSO callback error:', err);
      setError(err.message || 'Authentication failed');
      
      // Redirect to login page after 3 seconds
      setTimeout(() => {
        navigate('/login', {
          state: {
            error: err.message || 'Authentication failed. Please try again.'
          }
        });
      }, 3000);
    }
  };

  // Error state
  if (error) {
    return (
      <Box sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: '#f5f7fb',
        p: 3
      }}>
        <Card sx={{ maxWidth: 500, width: '100%' }}>
          <CardContent>
            <Alert severity="error">
              <AlertTitle>Authentication Failed</AlertTitle>
              <Typography variant="body2" paragraph>
                {error}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Redirecting to login page...
              </Typography>
            </Alert>
          </CardContent>
        </Card>
      </Box>
    );
  }

  // Loading state
  return (
    <Box sx={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: '#f5f7fb'
    }}>
      <Card sx={{ p: 4, minWidth: 400 }}>
        <CardContent>
          <Box sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 3
          }}>
            <CircularProgress size={60} thickness={4} />
            
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" gutterBottom>
                Completing Sign In
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {status}
              </Typography>
            </Box>
            
            <Box sx={{
              width: '100%',
              height: 4,
              background: '#e0e0e0',
              borderRadius: 2,
              overflow: 'hidden'
            }}>
              <Box sx={{
                width: '60%',
                height: '100%',
                background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                animation: 'progress 2s ease-in-out infinite',
                '@keyframes progress': {
                  '0%': { transform: 'translateX(-100%)' },
                  '100%': { transform: 'translateX(250%)' }
                }
              }} />
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SSOCallbackPage;
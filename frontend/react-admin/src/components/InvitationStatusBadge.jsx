/**
 * Invitation Status Badge Component
 * 
 * File: frontend/react-admin/src/components/InvitationStatusBadge.jsx
 * Purpose: Reusable badge to display invitation status with appropriate colors
 */

import React from 'react';
import { Chip, Tooltip } from '@mui/material';
import {
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Cancel as CancelIcon,
  HourglassEmpty as HourglassIcon
} from '@mui/icons-material';

const InvitationStatusBadge = ({ status, expiresAt, size = 'small', showIcon = true }) => {
  
  const getStatusConfig = () => {
    switch (status?.toLowerCase()) {
      case 'pending':
        return {
          label: 'Invitation Sent',
          color: 'warning',
          icon: <ScheduleIcon fontSize={size} />,
          tooltip: 'User invited, waiting for acceptance'
        };
      
      case 'accepted':
        return {
          label: 'Active',
          color: 'success',
          icon: <CheckCircleIcon fontSize={size} />,
          tooltip: 'Invitation accepted, user is active'
        };
      
      case 'expired':
        return {
          label: 'Invitation Expired',
          color: 'error',
          icon: <ErrorIcon fontSize={size} />,
          tooltip: 'Invitation has expired'
        };
      
      case 'cancelled':
        return {
          label: 'Cancelled',
          color: 'default',
          icon: <CancelIcon fontSize={size} />,
          tooltip: 'Invitation was cancelled'
        };
      
      default:
        return {
          label: status || 'Unknown',
          color: 'default',
          icon: <HourglassIcon fontSize={size} />,
          tooltip: 'Unknown status'
        };
    }
  };

  const config = getStatusConfig();

  // Check if pending invitation is near expiry
  const isNearExpiry = () => {
    if (status?.toLowerCase() !== 'pending' || !expiresAt) {
      return false;
    }
    
    const now = new Date();
    const expiry = new Date(expiresAt);
    const hoursRemaining = (expiry - now) / (1000 * 60 * 60);
    
    return hoursRemaining < 24 && hoursRemaining > 0;
  };

  // Get tooltip with expiry info
  const getTooltip = () => {
    if (status?.toLowerCase() === 'pending' && expiresAt) {
      const expiry = new Date(expiresAt);
      const now = new Date();
      
      if (now > expiry) {
        return 'Invitation has expired';
      }
      
      const daysRemaining = Math.ceil((expiry - now) / (1000 * 60 * 60 * 24));
      
      if (daysRemaining === 0) {
        const hoursRemaining = Math.ceil((expiry - now) / (1000 * 60 * 60));
        return `Expires in ${hoursRemaining} hour${hoursRemaining !== 1 ? 's' : ''}`;
      }
      
      return `Expires in ${daysRemaining} day${daysRemaining !== 1 ? 's' : ''}`;
    }
    
    return config.tooltip;
  };

  return (
    <Tooltip title={getTooltip()} arrow>
      <Chip
        label={config.label}
        color={config.color}
        size={size}
        icon={showIcon ? config.icon : undefined}
        variant={isNearExpiry() ? 'filled' : 'outlined'}
        sx={{
          fontWeight: 500,
          ...(isNearExpiry() && {
            animation: 'pulse 2s infinite',
            '@keyframes pulse': {
              '0%, 100%': { opacity: 1 },
              '50%': { opacity: 0.7 }
            }
          })
        }}
      />
    </Tooltip>
  );
};

export default InvitationStatusBadge;
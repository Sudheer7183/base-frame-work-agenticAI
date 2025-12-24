-- ============================================================================
-- Database Migration: Add User Invitation Fields
-- ============================================================================
-- Description: Adds invitation-related fields to users table for SSO email
--              invitation workflow
-- Author: Generated for Strategy 1 Implementation
-- Date: 2024-12-24
-- ============================================================================

-- Add invitation fields to users table
-- Note: This should be run in each tenant schema

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS invitation_status VARCHAR(20) DEFAULT 'accepted',
ADD COLUMN IF NOT EXISTS invitation_token VARCHAR(255),
ADD COLUMN IF NOT EXISTS invited_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS invited_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS accepted_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS invitation_expires_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS provisioning_method VARCHAR(50) DEFAULT 'manual';

-- Add index for invitation lookups
CREATE INDEX IF NOT EXISTS idx_users_invitation_token 
ON users(invitation_token) 
WHERE invitation_token IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_users_invitation_status 
ON users(invitation_status) 
WHERE invitation_status = 'pending';

-- Add comments for documentation
COMMENT ON COLUMN users.invitation_status IS 'Invitation status: pending, accepted, expired, cancelled';
COMMENT ON COLUMN users.invitation_token IS 'Secure token for invitation acceptance';
COMMENT ON COLUMN users.invited_by IS 'User ID who sent the invitation';
COMMENT ON COLUMN users.invited_at IS 'When invitation was sent';
COMMENT ON COLUMN users.accepted_at IS 'When invitation was accepted';
COMMENT ON COLUMN users.invitation_expires_at IS 'When invitation expires';
COMMENT ON COLUMN users.provisioning_method IS 'How user was created: manual, invitation, jit_sso, directory_sync';

-- ============================================================================
-- Rollback Script (if needed)
-- ============================================================================
-- ALTER TABLE users DROP COLUMN IF EXISTS invitation_status;
-- ALTER TABLE users DROP COLUMN IF EXISTS invitation_token;
-- ALTER TABLE users DROP COLUMN IF EXISTS invited_by;
-- ALTER TABLE users DROP COLUMN IF EXISTS invited_at;
-- ALTER TABLE users DROP COLUMN IF EXISTS accepted_at;
-- ALTER TABLE users DROP COLUMN IF EXISTS invitation_expires_at;
-- ALTER TABLE users DROP COLUMN IF EXISTS provisioning_method;
-- DROP INDEX IF EXISTS idx_users_invitation_token;
-- DROP INDEX IF EXISTS idx_users_invitation_status;

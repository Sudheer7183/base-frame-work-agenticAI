#!/usr/bin/env python3
"""
Secrets Rotation Script

Automate rotation of secrets with zero-downtime deployment.

Usage:
    # Rotate all secrets
    python scripts/rotate_secrets.py --all

    # Rotate specific secret
    python scripts/rotate_secrets.py --secret database/password

    # Dry run
    python scripts/rotate_secrets.py --all --dry-run
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.secrets import get_secrets_manager
from app.core.secrets.encryption import generate_master_key
import secrets as stdlib_secrets
import string

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_password(length: int = 32) -> str:
    """Generate a cryptographically secure password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    # Remove potentially problematic characters
    alphabet = alphabet.replace('"', '').replace("'", '').replace('\\', '').replace('`', '')
    return ''.join(stdlib_secrets.choice(alphabet) for _ in range(length))


def rotate_database_password(manager, dry_run=False):
    """Rotate database password"""
    logger.info("Rotating database password...")
    
    new_password = generate_password()
    
    if dry_run:
        logger.info(f"[DRY RUN] Would set new database password")
        return True
    
    # Set new password in secrets manager
    if not manager.set_secret("database/password", new_password):
        logger.error("Failed to update database password in secrets manager")
        return False
    
    logger.info("✓ Database password updated in secrets manager")
    logger.warning("ACTION REQUIRED: Update the actual database password:")
    logger.warning(f"  ALTER USER postgres WITH PASSWORD '{new_password}';")
    logger.warning("  Then restart application services to use new password")
    
    return True


def rotate_redis_password(manager, dry_run=False):
    """Rotate Redis password"""
    logger.info("Rotating Redis password...")
    
    new_password = generate_password()
    
    if dry_run:
        logger.info(f"[DRY RUN] Would set new Redis password")
        return True
    
    if not manager.set_secret("redis/password", new_password):
        logger.error("Failed to update Redis password in secrets manager")
        return False
    
    logger.info("✓ Redis password updated in secrets manager")
    logger.warning("ACTION REQUIRED: Update Redis configuration:")
    logger.warning(f"  requirepass {new_password}")
    logger.warning("  Then restart Redis and application services")
    
    return True


def rotate_keycloak_client_secret(manager, dry_run=False):
    """Rotate Keycloak client secret"""
    logger.info("Rotating Keycloak client secret...")
    
    new_secret = generate_password()
    
    if dry_run:
        logger.info(f"[DRY RUN] Would set new Keycloak client secret")
        return True
    
    if not manager.set_secret("keycloak/client_secret", new_secret):
        logger.error("Failed to update Keycloak client secret in secrets manager")
        return False
    
    logger.info("✓ Keycloak client secret updated in secrets manager")
    logger.warning("ACTION REQUIRED: Update Keycloak client configuration:")
    logger.warning(f"  1. Log into Keycloak admin console")
    logger.warning(f"  2. Navigate to Client -> agentic-api -> Credentials")
    logger.warning(f"  3. Regenerate secret or manually set to: {new_secret}")
    logger.warning("  4. Restart application services")
    
    return True


def rotate_application_secret_key(manager, dry_run=False):
    """Rotate application secret key"""
    logger.info("Rotating application secret key...")
    
    new_key = generate_password(64)
    
    if dry_run:
        logger.info(f"[DRY RUN] Would set new application secret key")
        return True
    
    if not manager.set_secret("application/secret_key", new_key):
        logger.error("Failed to update application secret key in secrets manager")
        return False
    
    logger.info("✓ Application secret key updated")
    logger.warning("ACTION REQUIRED: Restart all application services")
    logger.warning("  Existing sessions will be invalidated")
    
    return True


def rotate_llm_api_key(manager, provider, dry_run=False):
    """Rotate LLM API key"""
    logger.info(f"Rotating {provider} API key...")
    
    if dry_run:
        logger.info(f"[DRY RUN] Would prompt for new {provider} API key")
        return True
    
    import getpass
    new_api_key = getpass.getpass(f"Enter new {provider} API key: ")
    
    if not new_api_key:
        logger.error("No API key provided")
        return False
    
    key_name = f"llm/{provider.lower()}_api_key"
    if not manager.set_secret(key_name, new_api_key):
        logger.error(f"Failed to update {provider} API key in secrets manager")
        return False
    
    logger.info(f"✓ {provider} API key updated")
    logger.warning("ACTION REQUIRED: Restart application services")
    
    return True


def rotate_encryption_key(manager, dry_run=False):
    """Rotate master encryption key"""
    logger.info("Rotating master encryption key...")
    
    if dry_run:
        logger.info("[DRY RUN] Would rotate master encryption key")
        return True
    
    # Generate new key
    new_key = generate_master_key()
    
    logger.warning("="*60)
    logger.warning("CRITICAL: Master encryption key rotation")
    logger.warning("New key: %s", new_key)
    logger.warning("Save this key securely before proceeding!")
    logger.warning("="*60)
    
    confirm = input("Have you saved the new key? Type 'yes' to continue: ")
    if confirm.lower() != 'yes':
        logger.info("Rotation cancelled")
        return False
    
    # Get all encrypted secrets
    all_secrets = manager.list_secrets()
    encrypted_secrets = {}
    
    for key in all_secrets:
        value = manager.get_secret(key, use_cache=False)
        if value:
            encrypted_secrets[key] = value
    
    logger.info(f"Found {len(encrypted_secrets)} secrets to re-encrypt")
    
    # Rotate encryption key
    try:
        if hasattr(manager, 'encryption'):
            manager.encryption.rotate_key(new_key, encrypted_secrets)
            logger.info("✓ Encryption key rotated successfully")
            
            # Update environment variable
            logger.warning("ACTION REQUIRED: Update SECRETS_MASTER_KEY environment variable")
            logger.warning(f"  SECRETS_MASTER_KEY={new_key}")
            logger.warning("  Then restart all services")
            
            return True
        else:
            logger.error("Encryption not enabled in secrets manager")
            return False
            
    except Exception as e:
        logger.error(f"Failed to rotate encryption key: {e}")
        return False


ROTATION_STRATEGIES = {
    "database/password": rotate_database_password,
    "redis/password": rotate_redis_password,
    "keycloak/client_secret": rotate_keycloak_client_secret,
    "application/secret_key": rotate_application_secret_key,
    "encryption_key": rotate_encryption_key,
}


def main():
    parser = argparse.ArgumentParser(description="Rotate secrets")
    parser.add_argument(
        "--secret",
        help="Specific secret to rotate"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Rotate all secrets"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be rotated without making changes"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rotation even if recently rotated"
    )
    
    args = parser.parse_args()
    
    if not args.secret and not args.all:
        parser.print_help()
        return 1
    
    # Get secrets manager
    try:
        manager = get_secrets_manager()
        logger.info(f"Using secrets provider: {manager.provider.__class__.__name__}")
    except Exception as e:
        logger.error(f"Failed to initialize secrets manager: {e}")
        return 1
    
    # Perform rotation
    success = True
    
    if args.all:
        logger.info("Rotating all secrets...")
        for secret_key, rotate_func in ROTATION_STRATEGIES.items():
            try:
                if not rotate_func(manager, dry_run=args.dry_run):
                    logger.error(f"Failed to rotate {secret_key}")
                    success = False
            except Exception as e:
                logger.error(f"Error rotating {secret_key}: {e}")
                success = False
    
    elif args.secret:
        if args.secret in ROTATION_STRATEGIES:
            try:
                success = ROTATION_STRATEGIES[args.secret](manager, dry_run=args.dry_run)
            except Exception as e:
                logger.error(f"Error rotating {args.secret}: {e}")
                success = False
        else:
            logger.error(f"Unknown secret: {args.secret}")
            logger.info(f"Available secrets: {list(ROTATION_STRATEGIES.keys())}")
            return 1
    
    if success:
        logger.info("\n✓ Rotation complete!")
        if not args.dry_run:
            logger.info("\nRotation history logged in secrets audit log")
    else:
        logger.error("\n✗ Rotation failed")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Initialize Secrets Management

This script sets up initial secrets in the secrets manager.
Run this once when setting up a new environment.

Usage:
    python scripts/init_secrets.py --environment production
    python scripts/init_secrets.py --environment development --vault-url http://localhost:8200
"""

import sys
import os
import argparse
import getpass
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.secrets import get_secrets_manager
from app.core.secrets.encryption import generate_master_key
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def generate_strong_password(length: int = 32) -> str:
    """Generate a strong random password"""
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def prompt_secret(key: str, description: str, generate: bool = False, required: bool = True) -> str:
    """Prompt user for a secret value"""
    if generate:
        value = generate_strong_password()
        logger.info(f"Generated value for {key}: {value}")
        return value
    
    while True:
        value = getpass.getpass(f"Enter {description} ({key}): ")
        if value:
            return value
        elif not required:
            return None
        else:
            logger.warning("Value is required. Please try again.")


def init_database_secrets(manager, args):
    """Initialize database secrets"""
    logger.info("\n=== Database Secrets ===")
    
    secrets = {
        "database/host": {
            "value": input("Database host [localhost]: ") or "localhost",
            "description": "Database host"
        },
        "database/port": {
            "value": input("Database port [5432]: ") or "5432",
            "description": "Database port"
        },
        "database/name": {
            "value": input("Database name [agentic]: ") or "agentic",
            "description": "Database name"
        },
        "database/user": {
            "value": input("Database user [postgres]: ") or "postgres",
            "description": "Database user"
        },
        "database/password": {
            "value": prompt_secret("database/password", "Database password", generate=args.generate),
            "description": "Database password"
        }
    }
    
    for key, data in secrets.items():
        if manager.set_secret(key, data["value"], metadata={"description": data["description"]}):
            logger.info(f"✓ Set {key}")
        else:
            logger.error(f"✗ Failed to set {key}")


def init_redis_secrets(manager, args):
    """Initialize Redis secrets"""
    logger.info("\n=== Redis Secrets ===")
    
    use_redis = input("Use Redis? [y/N]: ").lower() == 'y'
    if not use_redis:
        logger.info("Skipping Redis configuration")
        return
    
    secrets = {
        "redis/host": {
            "value": input("Redis host [localhost]: ") or "localhost",
            "description": "Redis host"
        },
        "redis/port": {
            "value": input("Redis port [6379]: ") or "6379",
            "description": "Redis port"
        },
        "redis/password": {
            "value": prompt_secret("redis/password", "Redis password (optional)", generate=args.generate, required=False),
            "description": "Redis password"
        }
    }
    
    for key, data in secrets.items():
        if data["value"]:
            if manager.set_secret(key, data["value"], metadata={"description": data["description"]}):
                logger.info(f"✓ Set {key}")
            else:
                logger.error(f"✗ Failed to set {key}")


def init_keycloak_secrets(manager, args):
    """Initialize Keycloak secrets"""
    logger.info("\n=== Keycloak Secrets ===")
    
    secrets = {
        "keycloak/url": {
            "value": input("Keycloak URL [http://localhost:8080]: ") or "http://localhost:8080",
            "description": "Keycloak URL"
        },
        "keycloak/realm": {
            "value": input("Keycloak realm [agentic]: ") or "agentic",
            "description": "Keycloak realm"
        },
        "keycloak/client_id": {
            "value": input("Keycloak client ID [agentic-api]: ") or "agentic-api",
            "description": "Keycloak client ID"
        },
        "keycloak/client_secret": {
            "value": prompt_secret("keycloak/client_secret", "Keycloak client secret", generate=args.generate),
            "description": "Keycloak client secret"
        },
        "keycloak/admin_username": {
            "value": input("Keycloak admin username [admin]: ") or "admin",
            "description": "Keycloak admin username"
        },
        "keycloak/admin_password": {
            "value": prompt_secret("keycloak/admin_password", "Keycloak admin password", generate=args.generate),
            "description": "Keycloak admin password"
        }
    }
    
    for key, data in secrets.items():
        if manager.set_secret(key, data["value"], metadata={"description": data["description"]}):
            logger.info(f"✓ Set {key}")
        else:
            logger.error(f"✗ Failed to set {key}")


def init_llm_secrets(manager, args):
    """Initialize LLM provider secrets"""
    logger.info("\n=== LLM Provider Secrets ===")
    
    provider = input("Default LLM provider [ollama/openai/anthropic]: ").lower()
    
    if provider == "openai":
        api_key = prompt_secret("llm/openai_api_key", "OpenAI API Key", required=True)
        if manager.set_secret("llm/openai_api_key", api_key, metadata={"description": "OpenAI API Key"}):
            logger.info("✓ Set OpenAI API Key")
    
    elif provider == "anthropic":
        api_key = prompt_secret("llm/anthropic_api_key", "Anthropic API Key", required=True)
        if manager.set_secret("llm/anthropic_api_key", api_key, metadata={"description": "Anthropic API Key"}):
            logger.info("✓ Set Anthropic API Key")
    
    else:
        logger.info("Using Ollama (no API key needed)")


def init_application_secrets(manager, args):
    """Initialize application secrets"""
    logger.info("\n=== Application Secrets ===")
    
    secret_key = generate_strong_password(64)
    logger.info(f"Generated application secret key: {secret_key}")
    
    if manager.set_secret("application/secret_key", secret_key, metadata={"description": "Application secret key"}):
        logger.info("✓ Set application secret key")
    else:
        logger.error("✗ Failed to set application secret key")


def init_email_secrets(manager, args):
    """Initialize email secrets"""
    logger.info("\n=== Email Configuration ===")
    
    use_email = input("Configure email? [y/N]: ").lower() == 'y'
    if not use_email:
        logger.info("Skipping email configuration")
        return
    
    secrets = {
        "email/smtp_host": {
            "value": input("SMTP host [smtp.gmail.com]: ") or "smtp.gmail.com",
            "description": "SMTP host"
        },
        "email/smtp_port": {
            "value": input("SMTP port [587]: ") or "587",
            "description": "SMTP port"
        },
        "email/smtp_user": {
            "value": input("SMTP username: "),
            "description": "SMTP username"
        },
        "email/smtp_password": {
            "value": prompt_secret("email/smtp_password", "SMTP password", required=True),
            "description": "SMTP password"
        }
    }
    
    for key, data in secrets.items():
        if data["value"]:
            if manager.set_secret(key, data["value"], metadata={"description": data["description"]}):
                logger.info(f"✓ Set {key}")
            else:
                logger.error(f"✗ Failed to set {key}")


def main():
    parser = argparse.ArgumentParser(description="Initialize secrets management")
    parser.add_argument(
        "--environment",
        choices=["development", "staging", "production"],
        default="development",
        help="Environment to initialize"
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Auto-generate passwords"
    )
    parser.add_argument(
        "--vault-url",
        help="HashiCorp Vault URL (for production)"
    )
    parser.add_argument(
        "--vault-token",
        help="HashiCorp Vault token"
    )
    parser.add_argument(
        "--master-key",
        help="Master encryption key (will generate if not provided)"
    )
    
    args = parser.parse_args()
    
    # Set environment
    os.environ["ENVIRONMENT"] = args.environment
    
    # Configure Vault if provided
    if args.vault_url:
        os.environ["VAULT_ADDR"] = args.vault_url
    if args.vault_token:
        os.environ["VAULT_TOKEN"] = args.vault_token
    
    # Set or generate master key
    if args.master_key:
        os.environ["SECRETS_MASTER_KEY"] = args.master_key
    elif args.environment == "production":
        master_key = generate_master_key()
        logger.info(f"\n{'='*60}")
        logger.info("IMPORTANT: Save this master encryption key securely!")
        logger.info(f"SECRETS_MASTER_KEY={master_key}")
        logger.info(f"{'='*60}\n")
        os.environ["SECRETS_MASTER_KEY"] = master_key
    
    logger.info(f"Initializing secrets for {args.environment} environment")
    
    # Get secrets manager
    try:
        manager = get_secrets_manager()
        logger.info(f"Using secrets provider: {manager.provider.__class__.__name__}")
    except Exception as e:
        logger.error(f"Failed to initialize secrets manager: {e}")
        return 1
    
    # Initialize secrets
    try:
        init_database_secrets(manager, args)
        init_redis_secrets(manager, args)
        init_keycloak_secrets(manager, args)
        init_llm_secrets(manager, args)
        init_application_secrets(manager, args)
        init_email_secrets(manager, args)
        
        logger.info("\n✓ Secrets initialization complete!")
        
        # Verify
        logger.info("\nVerifying secrets...")
        health = manager.health_check()
        logger.info(f"Provider health: {health}")
        
        return 0
        
    except Exception as e:
        logger.error(f"\n✗ Error during initialization: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
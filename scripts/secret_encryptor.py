#!/usr/bin/env python3
"""
Encrypt Secrets in .env File

This script encrypts all sensitive values in your .env file using the master key.
After running, your .env will have encrypted values instead of plain text.

Usage:
    python encrypt_env_secrets.py
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
# sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


from app.core.secrets.encryption import SecretEncryption
import os


def encrypt_env_file():
    """Encrypt secrets in .env file"""
    
    env_file = Path("backend/.env") if Path("backend/.env").exists() else Path(".env")
    
    if not env_file.exists():
        print(f"❌ Error: {env_file} not found!")
        return False
    
    print("="*80)
    print("ENCRYPT .ENV SECRETS")
    print("="*80)
    print()
    
    # Step 1: Check for master key
    print("Step 1: Checking for master key...")
    
    # Read current .env
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    master_key = None
    for line in lines:
        if line.strip().startswith('SECRETS_MASTER_KEY='):
            master_key = line.split('=', 1)[1].strip()
            break
    
    if not master_key:
        print("⚠️  No SECRETS_MASTER_KEY found in .env")
        print("Generating new master key...")
        master_key = SecretEncryption.generate_key()
        print(f"✓ Generated master key: {master_key[:20]}...")
        print()
        print("⚠️  IMPORTANT: Save this master key securely!")
        print("⚠️  Without it, you cannot decrypt your secrets!")
        print()
    else:
        print(f"✓ Found master key: {master_key[:20]}...")
    
    print()
    
    # Step 2: Initialize encryption
    print("Step 2: Initializing encryption...")
    try:
        encryption = SecretEncryption(master_key=master_key)
        print("✓ Encryption initialized")
    except Exception as e:
        print(f"❌ Failed to initialize encryption: {e}")
        return False
    
    print()
    
    # Step 3: Identify secrets to encrypt
    print("Step 3: Identifying secrets to encrypt...")
    
    # These are the keys that should be encrypted
    SECRET_KEYS = [
        'DB_PASSWORD',
        'REDIS_PASSWORD',
        'SECRET_KEY',
        'JWT_SECRET_KEY',
        'KEYCLOAK_CLIENT_SECRET',
        'KEYCLOAK_ADMIN_PASSWORD',
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'SMTP_USER',
        'SMTP_PASSWORD',
        'SENTRY_DSN',
    ]
    
    secrets_found = []
    for line in lines:
        for key in SECRET_KEYS:
            if line.strip().startswith(f'{key}=') and not line.strip().startswith('#'):
                secrets_found.append(key)
                break
    
    print(f"✓ Found {len(secrets_found)} secrets to encrypt:")
    for key in secrets_found:
        print(f"  - {key}")
    
    print()
    
    # Step 4: Encrypt secrets
    print("Step 4: Encrypting secrets...")
    
    new_lines = []
    encrypted_count = 0
    
    for line in lines:
        # Keep comments and empty lines as-is
        if not line.strip() or line.strip().startswith('#'):
            new_lines.append(line)
            continue
        
        # Check if this line contains a secret
        should_encrypt = False
        key_name = None
        for key in SECRET_KEYS:
            if line.strip().startswith(f'{key}='):
                should_encrypt = True
                key_name = key
                break
        
        if should_encrypt and '=' in line:
            # Parse key=value
            parts = line.split('=', 1)
            key = parts[0].strip()
            value = parts[1].strip()
            
            # Skip if empty or already encrypted (starts with gAAAAA)
            if not value or value.startswith('gAAAAA'):
                new_lines.append(line)
                if value.startswith('gAAAAA'):
                    print(f"  ⊙ {key} - Already encrypted, skipping")
                else:
                    print(f"  ⊙ {key} - Empty, skipping")
                continue
            
            # Encrypt the value
            try:
                encrypted_value = encryption.encrypt(value)
                new_line = f"{key}={encrypted_value}\n"
                new_lines.append(new_line)
                encrypted_count += 1
                print(f"  ✓ {key} - Encrypted ({len(value)} chars → {len(encrypted_value)} chars)")
            except Exception as e:
                print(f"  ✗ {key} - Encryption failed: {e}")
                new_lines.append(line)  # Keep original if encryption fails
        else:
            # Not a secret, keep as-is
            new_lines.append(line)
    
    print()
    print(f"✓ Encrypted {encrypted_count} secrets")
    print()
    
    # Step 5: Add master key if not present
    if not any('SECRETS_MASTER_KEY=' in line for line in new_lines):
        print("Step 5: Adding master key to .env...")
        # Find a good place to add it (after SECRETS_PROVIDER)
        insert_index = 0
        for i, line in enumerate(new_lines):
            if 'SECRETS_PROVIDER=' in line:
                insert_index = i + 1
                break
        
        new_lines.insert(insert_index, f"SECRETS_MASTER_KEY={master_key}\n")
        print("✓ Master key added to .env")
        print()
    
    # Step 6: Backup and save
    print("Step 6: Saving encrypted .env file...")
    
    # Backup original
    backup_file = env_file.parent / f"{env_file.name}.backup"
    with open(backup_file, 'w') as f:
        f.writelines(lines)
    print(f"✓ Original backed up to: {backup_file}")
    
    # Save encrypted version
    with open(env_file, 'w') as f:
        f.writelines(new_lines)
    print(f"✓ Encrypted .env saved to: {env_file}")
    
    print()
    print("="*80)
    print("ENCRYPTION COMPLETE!")
    print("="*80)
    print()
    print("Summary:")
    print(f"  • Encrypted {encrypted_count} secrets")
    print(f"  • Backup saved to: {backup_file}")
    print(f"  • Master key: {master_key[:20]}...")
    print()
    print("⚠️  IMPORTANT:")
    print("  • Keep SECRETS_MASTER_KEY secure!")
    print("  • Without it, secrets cannot be decrypted")
    print("  • Backup the master key in a secure location")
    print()
    print("Next steps:")
    print("  1. Test your application: uvicorn app.main:app --reload")
    print("  2. Verify secrets load correctly")
    print("  3. Store master key in password manager")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = encrypt_env_file()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Encryption cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
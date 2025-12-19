#!/usr/bin/env python3
"""
Keycloak User Setup and Testing Script
Fixes common user issues and tests authentication
"""

import httpx
import json
from typing import Optional

KEYCLOAK_URL = "http://localhost:8080"
REALM = "agentic"
ADMIN_USER = "admin"
ADMIN_PASS = "admin"
CLIENT_ID = "agentic-api"
CLIENT_SECRET = "your-client-secret-here-change-in-production"


class KeycloakTester:
    def __init__(self):
        self.admin_token = None
    
    def get_admin_token(self):
        """Get admin token for Keycloak admin API"""
        print("🔑 Getting admin token...")
        
        response = httpx.post(
            f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
            data={
                "client_id": "admin-cli",
                "username": ADMIN_USER,
                "password": ADMIN_PASS,
                "grant_type": "password"
            }
        )
        
        if response.status_code == 200:
            self.admin_token = response.json()["access_token"]
            print("✅ Admin token obtained")
            return True
        else:
            print(f"❌ Failed to get admin token: {response.text}")
            return False
    
    def get_user_by_email(self, email: str):
        """Get user details by email"""
        response = httpx.get(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/users",
            params={"email": email, "exact": "true"},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if response.status_code == 200:
            users = response.json()
            return users[0] if users else None
        return None
    
    def fix_user_account(self, user_id: str, email: str):
        """Fix user account - remove required actions and enable"""
        print(f"🔧 Fixing account for {email}...")
        
        # Update user to remove required actions
        update_data = {
            "emailVerified": True,
            "enabled": True,
            "requiredActions": []  # Clear all required actions
        }
        
        response = httpx.put(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if response.status_code in (200, 204):
            print(f"✅ Account fixed for {email}")
            return True
        else:
            print(f"❌ Failed to fix account: {response.text}")
            return False
    
    def test_user_login(self, username: str, password: str):
        """Test user login and get token"""
        print(f"\n🧪 Testing login for {username}...")
        
        response = httpx.post(
            f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "password",
                "username": username,
                "password": password
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Login successful!")
            print(f"   Access Token: {token_data['access_token'][:50]}...")
            print(f"   Expires In: {token_data['expires_in']} seconds")
            print(f"   Refresh Token: {token_data.get('refresh_token', 'N/A')[:50]}...")
            return token_data
        else:
            print(f"❌ Login failed:")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.json()}")
            return None
    
    def decode_token(self, token: str):
        """Decode JWT token (without verification for debugging)"""
        import base64
        
        parts = token.split('.')
        if len(parts) != 3:
            print("❌ Invalid token format")
            return
        
        # Decode payload (add padding if needed)
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        decoded = base64.urlsafe_b64decode(payload)
        token_data = json.loads(decoded)
        
        print("\n📋 Token Claims:")
        print(f"   Subject (sub): {token_data.get('sub')}")
        print(f"   Email: {token_data.get('email')}")
        print(f"   Username: {token_data.get('preferred_username')}")
        print(f"   Tenant: {token_data.get('tenant', 'N/A')}")
        print(f"   Roles: {token_data.get('realm_access', {}).get('roles', [])}")
        print(f"   Expires: {token_data.get('exp')}")
    
    def run_full_test(self):
        """Run complete test suite"""
        print("=" * 70)
        print("KEYCLOAK SETUP & TEST")
        print("=" * 70)
        
        # Step 1: Get admin token
        if not self.get_admin_token():
            print("\n❌ Cannot proceed without admin access")
            return
        
        # Step 2: Test users to fix
        test_users = [
            ("admin@test.com", "Test123!"),
            ("user@test.com", "Test123!"),
            ("demo-admin@test.com", "Test123!"),
        ]
        
        print("\n" + "=" * 70)
        print("FIXING USER ACCOUNTS")
        print("=" * 70)
        
        for email, _ in test_users:
            user = self.get_user_by_email(email)
            if user:
                print(f"\n📧 Found user: {email}")
                print(f"   ID: {user['id']}")
                print(f"   Enabled: {user.get('enabled')}")
                print(f"   Email Verified: {user.get('emailVerified')}")
                print(f"   Required Actions: {user.get('requiredActions', [])}")
                
                self.fix_user_account(user['id'], email)
            else:
                print(f"\n⚠️  User not found: {email}")
        
        # Step 3: Test logins
        print("\n" + "=" * 70)
        print("TESTING USER LOGINS")
        print("=" * 70)
        
        for username, password in test_users:
            token_data = self.test_user_login(username, password)
            
            if token_data:
                self.decode_token(token_data['access_token'])
        
        print("\n" + "=" * 70)
        print("✅ TEST COMPLETE")
        print("=" * 70)


if __name__ == "__main__":
    tester = KeycloakTester()
    tester.run_full_test()
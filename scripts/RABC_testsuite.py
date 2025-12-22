# import requests
# import json
# from typing import Dict, Optional
# from dataclasses import dataclass
# from enum import Enum


# class Role(str, Enum):
#     SUPER_ADMIN = "SUPER_ADMIN"
#     ADMIN = "ADMIN"
#     USER = "USER"
#     VIEWER = "VIEWER"


# @dataclass
# class TestUser:
#     name: str
#     username: str
#     password: str
#     email: str
#     expected_roles: list
#     token: Optional[str] = None


# # Test configuration
# KEYCLOAK_URL = "http://localhost:8080"
# REALM = "agentic"
# CLIENT_ID = "agentic-api"
# CLIENT_SECRET = "your-client-secret-here-change-in-production"
# API_BASE = "http://localhost:8000"

# # Define test users
# TEST_USERS = {
#     "super_admin": TestUser(
#         name="super_admin",
#         username="admin@test.com",
#         password="Test123!",
#         email="admin@test.com",
#         expected_roles=[Role.SUPER_ADMIN, Role.ADMIN, Role.USER]
#     ),
#     "admin": TestUser(
#         name="admin",
#         username="admin@test.com",
#         password="Test123!",
#         email="admin@test.com",
#         expected_roles=[Role.ADMIN, Role.USER]
#     ),
#     "user": TestUser(
#         name="user",
#         username="user@test.com",
#         password="Test123!",
#         email="user@test.com",
#         expected_roles=[Role.USER]
#     ),
#     "viewer": TestUser(
#         name="viewer",
#         username="viewer@test.com",  # only if this user exists
#         password="Test123!",
#         email="viewer@test.com",
#         expected_roles=[Role.VIEWER]
#     ),
# }


# # Test endpoints with expected results
# ENDPOINTS = [
#     {
#         "name": "health",
#         "method": "GET",
#         "path": "/api/v1/health",
#         "required_role": None,
#         "expectations": {
#             "anonymous": 200,
#             "super_admin": 200,
#             "admin": 200,
#             "user": 200,
#             "viewer": 200
#         }
#     },
#     {
#         "name": "get_current_user",
#         "method": "GET",
#         "path": "/api/v1/users/me",
#         "required_role": Role.USER,
#         "expectations": {
#             "anonymous": 401,
#             "super_admin": 200,
#             "admin": 200,
#             "user": 200,
#             "viewer": 401  # Viewer can't access user endpoints
#         }
#     },
#     {
#         "name": "list_users",
#         "method": "GET",
#         "path": "/api/v1/users",
#         "required_role": Role.ADMIN,
#         "expectations": {
#             "anonymous": 401,
#             "super_admin": 200,
#             "admin": 200,
#             "user": 403,
#             "viewer": 401
#         }
#     },
#     {
#         "name": "create_user",
#         "method": "POST",
#         "path": "/api/v1/users/create",
#         "required_role": Role.ADMIN,
#         "data": {
#             "email": "newuser@test.com",
#             "username": "newuser",
#             "password": "NewUser123!",
#             "roles": ["USER"]
#         },
#         "expectations": {
#             "anonymous": 401,
#             "super_admin": 201,
#             "admin": 201,
#             "user": 403,
#             "viewer": 401
#         }
#     },
#     {
#         "name": "list_agents",
#         "method": "GET",
#         "path": "/api/v1/agents",
#         "required_role": Role.USER,
#         "expectations": {
#             "anonymous": 401,
#             "super_admin": 200,
#             "admin": 200,
#             "user": 200,
#             "viewer": 401
#         }
#     },
#     {
#         "name": "create_agent",
#         "method": "POST",
#         "path": "/api/v1/agents",
#         "required_role": Role.ADMIN,
#         "data": {
#             "name": "Test Agent",
#             "description": "Test agent",
#             "workflow": "approval",
#             "config": {},
#             "active": True
#         },
#         "expectations": {
#             "anonymous": 401,
#             "super_admin": 201,
#             "admin": 201,
#             "user": 403,
#             "viewer": 401
#         }
#     },
#     {
#         "name": "list_tenants",
#         "method": "GET",
#         "path": "/platform/tenants",
#         "required_role": Role.SUPER_ADMIN,
#         "expectations": {
#             "anonymous": 401,
#             "super_admin": 200,
#             "admin": 403,
#             "user": 403,
#             "viewer": 403
#         }
#     },
#     {
#         "name": "create_tenant",
#         "method": "POST",
#         "path": "/platform/tenants",
#         "required_role": Role.SUPER_ADMIN,
#         "data": {
#             "slug": "test-tenant",
#             "name": "Test Tenant",
#             "admin_email": "admin@test-tenant.com"
#         },
#         "expectations": {
#             "anonymous": 401,
#             "super_admin": 201,
#             "admin": 403,
#             "user": 403,
#             "viewer": 403
#         }
#     },
#     {
#         "name": "list_hitl",
#         "method": "GET",
#         "path": "/api/v1/hitl/pending",
#         "required_role": Role.USER,
#         "expectations": {
#             "anonymous": 401,
#             "super_admin": 200,
#             "admin": 200,
#             "user": 200,
#             "viewer": 401
#         }
#     },
# ]


# def get_token(user: TestUser) -> Optional[str]:
#     """Get OAuth2 token for user"""
#     try:
#         response = requests.post(
#             f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token",
#             data={
#                 "client_id": CLIENT_ID,
#                 "client_secret": CLIENT_SECRET,
#                 "grant_type": "password",
#                 "username": user.username,
#                 "password": user.password
#             }
#         )
        
#         if response.status_code == 200:
#             return response.json()["access_token"]
#         else:
#             print(f"  ✗ Token error: {response.json()}")
#             return None
            
#     except Exception as e:
#         print(f"  ✗ Exception: {e}")
#         return None


# def test_endpoint(
#     endpoint: dict,
#     user_name: str,
#     token: Optional[str]
# ) -> tuple[int, bool]:
#     """Test an endpoint with a user"""
#     headers = {}
    
#     if token:
#         headers["Authorization"] = f"Bearer {token}"
    
#     exempt_paths = ["/api/v1/health", "/health", "/docs", "/openapi.json"]

#     # Add tenant header for tenant-specific endpoints
#     if endpoint["path"] not in exempt_paths:
#         # Use X-Tenant-ID as requested by your current Resolver code
#         headers["X-Tenant-ID"] = "demo"
    
#     try:
#         if endpoint["method"] == "GET":
#             response = requests.get(
#                 f"{API_BASE}{endpoint['path']}",
#                 headers=headers,
#                 timeout=5
#             )
#         elif endpoint["method"] == "POST":
#             response = requests.post(
#                 f"{API_BASE}{endpoint['path']}",
#                 json=endpoint.get("data", {}),
#                 headers=headers,
#                 timeout=5
#             )
#         else:
#             return 0, False
        
#         expected = endpoint["expectations"][user_name]
#         success = response.status_code == expected
        
#         return response.status_code, success
        
#     except requests.exceptions.RequestException as e:
#         print(f"      ✗ Request error: {e}")
#         return 0, False


# def main():
#     """Run RBAC tests"""
    
#     print("\n" + "="*70)
#     print("RBAC TEST SUITE")
#     print("="*70)
    
#     # Step 1: Authenticate all users
#     print("🔐 Authenticating test users...")
#     print("-"*70)
    
#     for user in TEST_USERS.values():
#         token = get_token(user)
#         if token:
#             user.token = token
#             print(f"✅ {user.name:15} - {user.email}")
#         else:
#             print(f"❌ {user.name:15} - FAILED")
    
#     # Step 2: Test endpoints
#     print("\n🧪 Testing endpoints...")
#     print("-"*70)
    
#     results = {
#         "total": 0,
#         "passed": 0,
#         "failed": 0,
#         "failures": []
#     }
    
#     for endpoint in ENDPOINTS:
#         print(f"\n📍 {endpoint['name']}")
#         print(f"   {endpoint['method']} {endpoint['path']}")
#         print(f"   Required Role: {endpoint.get('required_role', 'None')}")
#         print()
        
#         # Test anonymous
#         status, success = test_endpoint(endpoint, "anonymous", None)
#         expected = endpoint["expectations"]["anonymous"]
#         results["total"] += 1
        
#         if success:
#             results["passed"] += 1
#             print(f"   ✅ anonymous:     {status} (expected {expected})")
#         else:
#             results["failed"] += 1
#             results["failures"].append(
#                 f"{endpoint['name']} [anonymous]: got {status}, expected {expected}"
#             )
#             print(f"   ❌ anonymous:     {status} (expected {expected})")
        
#         # Test authenticated users
#         for user_name, user in TEST_USERS.items():
#             if user.token or endpoint["expectations"][user_name] == 401:
#                 status, success = test_endpoint(
#                     endpoint,
#                     user_name,
#                     user.token
#                 )
#                 expected = endpoint["expectations"][user_name]
#                 results["total"] += 1
                
#                 if success:
#                     results["passed"] += 1
#                     print(f"   ✅ {user_name:12} {status} (expected {expected})")
#                 else:
#                     results["failed"] += 1
#                     results["failures"].append(
#                         f"{endpoint['name']} [{user_name}]: got {status}, expected {expected}"
#                     )
#                     print(f"   ❌ {user_name:12} {status} (expected {expected})")
    
#     # Summary
#     print("\n" + "="*70)
#     print("TEST SUMMARY")
#     print("="*70)
#     print()
#     print(f"Total Tests: {results['total']}")
#     print(f"✅ Passed: {results['passed']}")
#     print(f"❌ Failed: {results['failed']}")
#     print(f"Success Rate: {results['passed']/results['total']*100:.1f}%")
    
#     if results["failures"]:
#         print(f"\n❌ Failed Tests:")
#         for failure in results["failures"]:
#             print(f"   - {failure}")


# if __name__ == "__main__":
#     main()


# import requests
# import jwt  # pip install PyJWT
# from typing import Optional, Dict, Any
# from dataclasses import dataclass
# from enum import Enum

# class Role(str, Enum):
#     SUPER_ADMIN = "SUPER_ADMIN"
#     ADMIN = "ADMIN"
#     USER = "USER"
#     VIEWER = "VIEWER"

# @dataclass
# class TestUser:
#     name: str
#     username: str
#     password: str
#     expected_roles: list
#     token: Optional[str] = None
#     tenant_claim: Optional[str] = None

# # --- Configuration ---
# KEYCLOAK_URL = "http://localhost:8080"
# REALM = "agentic"
# CLIENT_ID = "agentic-api"
# CLIENT_SECRET = "your-client-secret-here-change-in-production"
# API_BASE = "http://localhost:8000"

# TEST_USERS = {
#     "super_admin": TestUser("super_admin", "admin@test.com", "Test123!", [Role.SUPER_ADMIN]),
#     "admin": TestUser("admin", "admin@test.com", "Test123!", [Role.ADMIN]),
#     "user": TestUser("user", "user@test.com", "Test123!", [Role.USER]),
# }

# def login_and_get_tenant(user: TestUser):
#     """Logs in the user and extracts the tenant claim from the JWT."""
#     try:
#         response = requests.post(
#             f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token",
#             data={
#                 "client_id": CLIENT_ID,
#                 "client_secret": CLIENT_SECRET,
#                 "grant_type": "password",
#                 "username": user.username,
#                 "password": user.password
#             },
#             timeout=5
#         )
        
#         if response.status_code == 200:
#             data = response.json()
#             user.token = data["access_token"]
            
#             # Decode token to get the tenant claim you mapped in Keycloak
#             payload = jwt.decode(user.token, options={"verify_signature": False})
#             user.tenant_claim = payload.get("tenant")
#             return True
#         return False
#     except Exception as e:
#         print(f"Error authenticating {user.name}: {e}")
#         return False

# def run_test(endpoint: dict, user_key: str):
#     user = TEST_USERS.get(user_key)
#     token = user.token if user else None
    
#     headers = {}
#     if token:
#         headers["Authorization"] = f"Bearer {token}"
    
#     # Logic: Use the tenant found in the user's token, or fallback to 'demo'
#     # This ensures the Header matches the Token Claim
#     tenant_to_use = user.tenant_claim if (user and user.tenant_claim) else "demo"
    
#     exempt_paths = ["/api/v1/health", "/health"]
#     if endpoint["path"] not in exempt_paths:
#         headers["X-Tenant-ID"] = tenant_to_use

#     try:
#         if endpoint["method"] == "GET":
#             res = requests.get(f"{API_BASE}{endpoint['path']}", headers=headers, timeout=5)
#         else:
#             res = requests.post(f"{API_BASE}{endpoint['path']}", headers=headers, json=endpoint.get("data", {}), timeout=5)
        
#         expected = endpoint["expectations"][user_key]
#         return res.status_code, res.status_code == expected
#     except Exception:
#         return 0, False

# # ... (Include your ENDPOINTS list here from previous messages) ...

# def main():
#     print("🔐 Step 1: Automated Login & Tenant Extraction")
#     for name, user in TEST_USERS.items():
#         if login_and_get_tenant(user):
#             print(f"✅ {name}: Token acquired. Tenant in token: '{user.tenant_claim}'")
#         else:
#             print(f"❌ {name}: Login failed.")

#     print("\n🧪 Step 2: Running Validations")
#     # Loop through ENDPOINTS and call run_test (similar to your previous main)

# if __name__ == "__main__":
#     main()


import requests
import jwt  # Ensure PyJWT is installed (pip install PyJWT)
import json
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# 1. CONFIGURATION & MODELS
# ============================================================================

class Role(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    USER = "USER"
    VIEWER = "VIEWER"

@dataclass
class TestUser:
    name: str
    username: str
    password: str
    expected_roles: List[Role]
    token: Optional[str] = None
    tenant_claim: Optional[str] = None

# Update these with your actual Keycloak/API settings
KEYCLOAK_URL = "http://localhost:8080"
REALM = "agentic"
CLIENT_ID = "agentic-api"
CLIENT_SECRET = "your-client-secret-here-change-in-production"
API_BASE = "http://localhost:8000"

# Define the users to be tested
TEST_USERS = {
    "super_admin": TestUser("super_admin", "admin@test.com", "Test123!", [Role.SUPER_ADMIN]),
    "admin":       TestUser("admin",       "admin@test.com", "Test123!", [Role.ADMIN]),
    "user":        TestUser("user",        "user@test.com",  "Test123!", [Role.USER]),
    "viewer":      TestUser("viewer",      "viewer@test.com","Test123!", [Role.VIEWER]),
}

# Define the RBAC Test Matrix
ENDPOINTS = [
    {
        "name": "health",
        "method": "GET",
        "path": "/api/v1/health",
        "expectations": {"anonymous": 200, "super_admin": 200, "admin": 200, "user": 200, "viewer": 200}
    },
    {
        "name": "get_current_user",
        "method": "GET",
        "path": "/api/v1/users/me",
        "expectations": {"anonymous": 401, "super_admin": 200, "admin": 200, "user": 200, "viewer": 200}
    },
    {
        "name": "list_users",
        "method": "GET",
        "path": "/api/v1/users",
        "expectations": {"anonymous": 401, "super_admin": 200, "admin": 200, "user": 403, "viewer": 403}
    },
    {
        "name": "create_agent",
        "method": "POST",
        "path": "/api/v1/agents",
        "data": {"name": "RBAC Test Agent", "workflow": "approval", "active": True},
        "expectations": {"anonymous": 401, "super_admin": 201, "admin": 201, "user": 403, "viewer": 401}
    },
    {
        "name": "list_tenants",
        "method": "GET",
        "path": "/platform/tenants",
        "expectations": {"anonymous": 401, "super_admin": 200, "admin": 403, "user": 403, "viewer": 403}
    },
    {
        "name": "list_hitl",
        "method": "GET",
        "path": "/api/v1/hitl/pending",
        "expectations": {"anonymous": 401, "super_admin": 200, "admin": 200, "user": 200, "viewer": 401}
    },
]

# ============================================================================
# 2. CORE LOGIC
# ============================================================================

def authenticate_users():
    """Step 1: Get tokens and extract tenant claims from JWT."""
    print("\n" + "="*70)
    print("🔐 STEP 1: AUTHENTICATION & JWT INSPECTION")
    print("="*70)
    
    for name, user in TEST_USERS.items():
        try:
            response = requests.post(
                f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token",
                data={
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "grant_type": "password",
                    "username": user.username,
                    "password": user.password
                },
                timeout=5
            )
            
            if response.status_code == 200:
                user.token = response.json()["access_token"]
                # Decode the JWT to see what tenant Keycloak thinks this user belongs to
                payload = jwt.decode(user.token, options={"verify_signature": False})
                user.tenant_claim = payload.get("tenant")
                
                print(f"✅ {name:12} | Tenant: '{user.tenant_claim}' | Roles: {payload.get('realm_access', {}).get('roles', [])}")
            else:
                print(f"❌ {name:12} | Login Failed (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ {name:12} | Error: {e}")

def run_rbac_tests():
    """Step 2: Execute the test matrix against the API."""
    print("\n" + "="*70)
    print("🧪 STEP 2: RBAC ENDPOINT VALIDATION")
    print("="*70)
    
    stats = {"passed": 0, "total": 0}

    for ep in ENDPOINTS:
        print(f"\n📍 Endpoint: {ep['name']} ({ep['method']} {ep['path']})")
        
        # Test 1: Anonymous Access
        status, success = perform_request(ep, "anonymous", None)
        log_and_track(stats, "anonymous", status, ep['expectations']['anonymous'], success)

        # Test 2: Authenticated Access for each user
        for user_key, user_obj in TEST_USERS.items():
            if user_obj.token:
                status, success = perform_request(ep, user_key, user_obj)
                log_and_track(stats, user_key, status, ep['expectations'][user_key], success)

    print("\n" + "="*70)
    print(f"📊 FINAL RESULT: {stats['passed']}/{stats['total']} TESTS PASSED")
    print(f"   Success Rate: {(stats['passed']/stats['total'])*100:.1f}%")
    print("="*70 + "\n")

def perform_request(endpoint: dict, user_key: str, user_obj: Optional[TestUser]):
    """Wraps the actual HTTP call with the correct headers."""
    headers = {}
    
    # 1. Add Auth Token
    if user_obj and user_obj.token:
        headers["Authorization"] = f"Bearer {user_obj.token}"
    
    # 2. Add Tenant Header (Isolation Enforcement)
    # We use the tenant claim found in the user's token to ensure alignment.
    exempt_paths = ["/api/v1/health", "/health", "/docs"]
    if endpoint["path"] not in exempt_paths:
        tenant_id = user_obj.tenant_claim if (user_obj and user_obj.tenant_claim) else "demo"
        headers["X-Tenant-ID"] = tenant_id

    url = f"{API_BASE}{endpoint['path']}"
    try:
        if endpoint["method"] == "GET":
            r = requests.get(url, headers=headers, timeout=5)
        else:
            r = requests.post(url, headers=headers, json=endpoint.get("data", {}), timeout=5)
        
        expected = endpoint["expectations"][user_key]
        return r.status_code, r.status_code == expected
    except Exception:
        return 0, False

def log_and_track(stats, user, got, expected, success):
    stats["total"] += 1
    if success: stats["passed"] += 1
    icon = "✅" if success else "❌"
    print(f"   {icon} {user:12} | Got: {got} | Expected: {expected}")

if __name__ == "__main__":
    authenticate_users()
    run_rbac_tests()
#!/bin/bash
# API Testing Script for Multi-Tenant Platform
# Tests all major endpoints without authentication

TENANT_ID="testcompany"
BASE_URL="http://localhost:8000"

echo "======================================"
echo "Multi-Tenant API Testing"
echo "======================================"
echo ""

# Test 1: Health Check
echo "1. Testing Health Check..."
curl -s "${BASE_URL}/health" | jq .
echo ""

# Test 2: List Tenants (Platform Level)
echo "2. Listing All Tenants..."
curl -s "${BASE_URL}/platform/tenants" | jq .
echo ""

# Test 3: Get Specific Tenant
echo "3. Getting Tenant Details..."
curl -s "${BASE_URL}/platform/tenants/testcompany" | jq .
echo ""

# Test 4: List Agents (Requires Tenant Header)
echo "4. Listing Agents in Tenant..."
curl -s -H "X-Tenant-ID: ${TENANT_ID}" \
  "${BASE_URL}/api/v1/agents" | jq .
echo ""

# Test 5: Create New Agent
echo "5. Creating New Agent..."
curl -s -X POST \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Support Agent",
    "description": "Handles customer inquiries with approval workflow",
    "workflow": "approval",
    "config": {
      "model": "gpt-4",
      "temperature": 0.7,
      "hitl": {
        "enabled": true,
        "threshold": 0.8
      }
    },
    "active": true
  }' \
  "${BASE_URL}/api/v1/agents" | jq .
echo ""

# Test 6: Get Agent Details
echo "6. Getting Agent Details (ID: 1)..."
curl -s -H "X-Tenant-ID: ${TENANT_ID}" \
  "${BASE_URL}/api/v1/agents/1" | jq .
echo ""

# Test 7: List HITL Records
echo "7. Listing HITL Records..."
curl -s -H "X-Tenant-ID: ${TENANT_ID}" \
  "${BASE_URL}/api/v1/hitl/pending" | jq .
echo ""

# Test 8: Execute Agent (Will create HITL record if threshold not met)
echo "8. Executing Agent..."
curl -s -X POST \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, I need help with my order",
    "user_id": "test123"
  }' \
  "${BASE_URL}/api/v1/agents/1/execute" | jq .
echo ""

echo "======================================"
echo "✅ API Tests Complete!"
echo "======================================"
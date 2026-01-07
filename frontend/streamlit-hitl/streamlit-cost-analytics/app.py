"""
Cost Analytics Dashboard - API-Based Version
Uses backend API endpoints instead of direct database queries

File: frontend/streamlit-cost-analytics/app.py
"""

import streamlit as st
import requests
import jwt
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Dict, Any

# =============================================================================
# Configuration
# =============================================================================

KEYCLOAK_CONFIG = {
    "url": "http://localhost:8080",
    "realm": "agentic",
    "client_id": "agentic-api",
    "client_secret": "your-client-secret-here-change-in-production"
}

API_BASE_URL = "http://localhost:8000"

# =============================================================================
# Session State Initialization
# =============================================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = {}

# =============================================================================
# Authentication Functions
# =============================================================================

def decode_token(token):
    """Decode JWT token to extract user and tenant info"""
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email") or payload.get("preferred_username"),
            "username": payload.get("preferred_username"),
            "tenant": payload.get("tenant"),
            "roles": payload.get("realm_access", {}).get("roles", [])
        }
    except Exception as e:
        st.error(f"Failed to decode token: {e}")
        return None


def login(username, password):
    """Login via Keycloak"""
    try:
        token_url = f"{KEYCLOAK_CONFIG['url']}/realms/{KEYCLOAK_CONFIG['realm']}/protocol/openid-connect/token"
        
        data = {
            "client_id": KEYCLOAK_CONFIG["client_id"],
            "client_secret": KEYCLOAK_CONFIG["client_secret"],
            "grant_type": "password",
            "username": username,
            "password": password
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            tokens = response.json()
            user_info = decode_token(tokens["access_token"])
            
            if user_info:
                st.session_state.access_token = tokens["access_token"]
                st.session_state.refresh_token = tokens["refresh_token"]
                st.session_state.user_info = user_info
                st.session_state.authenticated = True
                return True, "Login successful!"
            else:
                return False, "Failed to decode user information"
        else:
            error_data = response.json()
            return False, error_data.get("error_description", "Login failed")
            
    except Exception as e:
        return False, f"Login error: {str(e)}"


def logout():
    """Logout and clear session"""
    st.session_state.clear()
    st.rerun()


def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False)


def get_current_tenant():
    """Get current tenant from session"""
    if is_authenticated():
        return st.session_state.user_info.get("tenant")
    return None


# =============================================================================
# API Request Functions
# =============================================================================

def make_api_request(endpoint: str, method: str = "GET", params: Dict = None) -> Optional[Dict]:
    """
    Make authenticated API request to backend
    
    Args:
        endpoint: API endpoint (e.g., '/api/v1/cost-analytics/summary')
        method: HTTP method
        params: Query parameters
        
    Returns:
        Response JSON or None if error
    """
    if not is_authenticated():
        st.error("Not authenticated")
        return None
    
    token = st.session_state.access_token
    tenant = get_current_tenant()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    if tenant:
        headers["X-Tenant-ID"] = tenant
    
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        st.write(f"🔍 **API Request:** `{method} {endpoint}`")  # Debug
        st.write(f"📋 **Params:** {params}")  # Debug
        st.write(f"🏢 **Tenant:** {tenant}")  # Debug
        
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=params)
        else:
            response = requests.request(method, url, headers=headers, json=params)
        
        st.write(f"📥 **Response Status:** {response.status_code}")  # Debug
        
        if response.status_code == 401:
            st.error("Session expired. Please login again.")
            logout()
            return None
        
        if response.status_code != 200:
            error_detail = response.json().get('detail', 'Unknown error')
            st.error(f"API Error ({response.status_code}): {error_detail}")
            st.write(f"**Full Response:**")
            st.json(response.json())
            return None
        
        data = response.json()
        st.write(f"✅ **Response Data:**")  # Debug
        st.json(data)  # Debug
        
        return data
        
    except Exception as e:
        st.error(f"API request failed: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None


# =============================================================================
# Data Loading Functions (Using API)
# =============================================================================

@st.cache_data(ttl=300)
def load_cost_summary(_dummy, start_date: datetime, end_date: datetime):
    """Load cost summary from API"""
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }
    
    data = make_api_request("/api/v1/cost-analytics/summary", params=params)
    
    if data:
        return {
            "total_cost": data.get("total_cost", 0),
            "total_tokens": data.get("total_tokens", 0),
            "total_executions": data.get("total_executions", 0),
            "avg_cost_per_execution": data.get("avg_cost_per_execution", 0),
            "avg_tokens_per_execution": data.get("avg_tokens_per_execution", 0)
        }
    
    return None


@st.cache_data(ttl=300)
def load_daily_costs(_dummy, start_date: datetime, end_date: datetime):
    """Load daily costs from API"""
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }
    
    data = make_api_request("/api/v1/cost-analytics/daily-costs", params=params)
    
    if data and isinstance(data, list):
        return pd.DataFrame(data)
    
    return pd.DataFrame()


@st.cache_data(ttl=300)
def load_model_breakdown(_dummy, start_date: datetime, end_date: datetime):
    """Load model breakdown from API"""
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }
    
    data = make_api_request("/api/v1/cost-analytics/model-breakdown", params=params)
    
    if data and isinstance(data, list):
        return pd.DataFrame(data)
    
    return pd.DataFrame()


@st.cache_data(ttl=300)
def load_agent_costs(_dummy, start_date: datetime, end_date: datetime):
    """Load agent costs from API"""
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }
    
    data = make_api_request("/api/v1/cost-analytics/agent-costs", params=params)
    
    if data and isinstance(data, list):
        return pd.DataFrame(data)
    
    return pd.DataFrame()


# =============================================================================
# UI Components
# =============================================================================

def show_login_page():
    """Show login page"""
    st.title("🔐 Cost Analytics Dashboard")
    st.subheader("Please login to continue")
    
    with st.form("login_form"):
        username = st.text_input("Username / Email", value="testadmin")
        password = st.text_input("Password", type="password", value="Test123!")
        submit = st.form_submit_button("Login")
        
        if submit:
            if username and password:
                with st.spinner("Authenticating..."):
                    success, message = login(username, password)
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.warning("Please enter both username and password")
    
    # Debug info
    with st.expander("ℹ️ Test Credentials"):
        st.code("""
Username: testadmin
Password: Test123!

OR

Username: demo-admin
Password: DemoAdmin123!
        """)


def show_dashboard():
    """Show main dashboard"""
    st.title("📊 Cost Analytics Dashboard")
    
    user_info = st.session_state.user_info
    tenant = get_current_tenant()
    
    # Sidebar
    with st.sidebar:
        st.subheader("👤 User Info")
        st.write(f"**Email:** {user_info.get('email', 'N/A')}")
        st.write(f"**Tenant:** {tenant or 'N/A'}")
        st.write(f"**Roles:** {', '.join(user_info.get('roles', []))}")
        
        st.divider()
        
        # Date range selector
        st.subheader("📅 Date Range")
        date_range = st.selectbox(
            "Select Period",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "This Month"]
        )
        
        if date_range == "Last 7 Days":
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
        elif date_range == "Last 30 Days":
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
        elif date_range == "Last 90 Days":
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
        else:  # This Month
            end_date = datetime.now()
            start_date = datetime(end_date.year, end_date.month, 1)
        
        st.write(f"**From:** {start_date.strftime('%Y-%m-%d')}")
        st.write(f"**To:** {end_date.strftime('%Y-%m-%d')}")
        
        st.divider()
        
        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    
    # Check tenant
    if not tenant:
        st.error("❌ No tenant associated with your account. Please contact administrator.")
        st.info("**Note:** Make sure your Keycloak user has a 'tenant' attribute set.")
        return
    
    # Main content
    st.subheader(f"📊 Analytics for Tenant: **{tenant}**")
    
    # Create a unique key for cache busting
    cache_key = f"{tenant}_{datetime.now().strftime('%Y%m%d%H%M')}"
    
    # Debug section
    with st.expander("🔍 Debug Information", expanded=True):
        st.write("**API Base URL:**", API_BASE_URL)
        st.write("**Current Tenant:**", tenant)
        st.write("**Date Range:**", f"{start_date} to {end_date}")
        st.write("**Token Present:**", "✅ Yes" if st.session_state.access_token else "❌ No")
        
        # Test API connection
        if st.button("Test API Connection"):
            with st.spinner("Testing..."):
                health = make_api_request("/api/v1/cost-analytics/health")
                if health:
                    st.success("✅ API is reachable!")
                else:
                    st.error("❌ Cannot reach API")
    
    st.divider()
    
    # Load data
    with st.spinner("Loading cost data..."):
        summary = load_cost_summary(cache_key, start_date, end_date)
    
    if summary is None:
        st.error("❌ Failed to load cost summary")
        st.info("**Possible reasons:**")
        st.write("1. No agent executions have been run yet")
        st.write("2. Backend API is not running")
        st.write("3. Tenant schema doesn't have computational_audit tables")
        st.write("4. Authentication/authorization issue")
        return
    
    # Check if we have any data
    if summary["total_executions"] == 0:
        st.warning("⚠️ No execution data found for the selected period")
        st.info("""
        **Why is there no data?**
        
        The computational audit system tracks costs from **agent executions**. You need to:
        
        1. ✅ Verify migration completed: `alembic current` should show `57ec5ea850a8`
        2. ✅ Verify pricing data seeded: Check `public.model_pricing` table
        3. ✅ Verify tenant tables exist: Check `tenant_demo.computational_audit_usage`
        4. ✅ **Run some agent executions** to generate cost data
        
        **To test:**
        ```bash
        # Run an agent execution via API
        curl -X POST http://localhost:8000/api/v1/agents/1/execute \\
          -H "Authorization: Bearer YOUR_TOKEN" \\
          -H "X-Tenant-ID: demo" \\
          -H "Content-Type: application/json" \\
          -d '{"message": "Hello, test execution"}'
        ```
        
        After running agent executions, refresh this page to see cost data.
        """)
        
        # Show what data we DO have
        st.subheader("📋 Current Status")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Cost", f"${summary['total_cost']:.4f}")
        with col2:
            st.metric("Total Tokens", f"{summary['total_tokens']:,}")
        with col3:
            st.metric("Executions", f"{summary['total_executions']:,}")
        
        return
    
    # Display metrics
    st.subheader("📈 Summary Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Cost",
            f"${summary['total_cost']:.4f}",
            help="Total LLM costs"
        )
    
    with col2:
        st.metric(
            "Total Tokens",
            f"{summary['total_tokens']:,}",
            help="Total tokens used"
        )
    
    with col3:
        st.metric(
            "Executions",
            f"{summary['total_executions']:,}",
            help="Number of executions"
        )
    
    with col4:
        st.metric(
            "Avg Cost/Exec",
            f"${summary['avg_cost_per_execution']:.4f}",
            help="Average cost per execution"
        )
    
    st.divider()
    
    # Daily costs chart
    st.subheader("📈 Daily Cost Trends")
    daily_df = load_daily_costs(cache_key, start_date, end_date)
    
    if not daily_df.empty:
        fig = px.line(
            daily_df,
            x="date",
            y="cost",
            markers=True,
            title="Daily Costs",
            labels={"date": "Date", "cost": "Cost (USD)"}
        )
        fig.update_traces(line_color='#1f77b4', line_width=3)
        st.plotly_chart(fig, use_container_width=True)
        
        # Show data table
        with st.expander("📊 View Data Table"):
            st.dataframe(daily_df, use_container_width=True)
    else:
        st.info("No daily cost data available")
    
    st.divider()
    
    # Model breakdown
    st.subheader("🤖 Model Breakdown")
    model_df = load_model_breakdown(cache_key, start_date, end_date)
    
    if not model_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(
                model_df,
                values="cost",
                names="model",
                title="Cost Distribution by Model",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                model_df,
                x="model",
                y="cost",
                color="provider",
                title="Cost by Model & Provider",
                labels={"cost": "Cost (USD)", "model": "Model"}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Data table
        st.dataframe(
            model_df.style.format({
                "cost": "${:.4f}",
                "tokens": "{:,.0f}",
                "calls": "{:,.0f}"
            }),
            use_container_width=True
        )
    else:
        st.info("No model usage data available")
    
    st.divider()
    
    # Agent costs
    st.subheader("🤖 Agent Performance")
    agent_df = load_agent_costs(cache_key, start_date, end_date)
    
    if not agent_df.empty:
        fig = px.bar(
            agent_df,
            x="agent_name",
            y="cost",
            title="Cost by Agent",
            labels={"cost": "Cost (USD)", "agent_name": "Agent"},
            color="cost",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(
            agent_df.style.format({
                "cost": "${:.4f}",
                "tokens": "{:,.0f}",
                "executions": "{:,.0f}",
                "avg_cost_per_execution": "${:.4f}"
            }),
            use_container_width=True
        )
    else:
        st.info("No agent cost data available")


# =============================================================================
# Main App
# =============================================================================

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Cost Analytics",
        page_icon="📊",
        layout="wide"
    )
    
    if not is_authenticated():
        show_login_page()
    else:
        show_dashboard()


if __name__ == "__main__":
    main()
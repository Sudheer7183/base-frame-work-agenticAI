"""
Cost Analytics Dashboard - COMPLETE IMPLEMENTATION
Tenant-aware Streamlit dashboard for comprehensive cost monitoring

File: frontend/streamlit-cost-analytics/app.py  
Version: 2.0 COMPLETE FULL VERSION

USAGE:
    cd frontend/streamlit-cost-analytics
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
from pathlib import Path
import time

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import SessionLocal
from app.services.cost_analytics import (
    CostAnalyticsService,
    CostForecaster,
    AnomalyDetector
)
from app.tenancy.context import set_tenant

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Cost Analytics Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS
# =============================================================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .alert-critical {
        background-color: #ff4444;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .alert-warning {
        background-color: #ffaa00;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .alert-info {
        background-color: #44aaff;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR CONFIGURATION
# =============================================================================

with st.sidebar:
    st.header("⚙️ Settings")
    
    # Tenant selector
    available_tenants = ["acme", "globex", "initech", "umbrella"]
    selected_tenant = st.selectbox(
        "Select Tenant",
        available_tenants,
        index=0,
        help="Choose tenant to view costs for"
    )
    
    # Set tenant context
    set_tenant(selected_tenant)
    
    st.markdown("---")
    
    # Date range selector
    date_range = st.radio(
        "Time Period",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom"],
        index=1
    )
    
    if date_range == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End", datetime.now())
    else:
        days_map = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90}
        days = days_map[date_range]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
    
    # Convert to datetime
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    st.markdown("---")
    
    # Auto-refresh
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
    if auto_refresh:
        st.info("🔄 Dashboard refreshing every 30 seconds")
    
    # Refresh button
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    # Settings
    st.subheader("📊 Display Options")
    show_anomalies = st.checkbox("Show Anomalies", value=True)
    show_forecast = st.checkbox("Show Forecast", value=True)
    show_model_breakdown = st.checkbox("Show Model Breakdown", value=True)
    show_agent_costs = st.checkbox("Show Agent Costs", value=True)
    
    st.markdown("---")
    
    # Export
    st.subheader("📥 Export")
    if st.button("Export Report", use_container_width=True):
        st.info("📄 Export feature coming soon!")
    
    st.markdown("---")
    
    # Info
    st.caption(f"Dashboard v2.0")
    st.caption(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")

# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

@st.cache_resource
def get_db_session():
    """Get database session"""
    return SessionLocal()

db = get_db_session()

# =============================================================================
# DATA LOADING FUNCTIONS
# =============================================================================

@st.cache_data(ttl=300)
def load_cost_summary(_db, start, end):
    """Load cost summary"""
    service = CostAnalyticsService(_db)
    return service.get_cost_summary(start, end)

@st.cache_data(ttl=300)
def load_daily_costs(_db, start, end):
    """Load daily costs"""
    service = CostAnalyticsService(_db)
    return service.get_daily_costs(start, end)

@st.cache_data(ttl=300)
def load_model_breakdown(_db, start, end):
    """Load model breakdown"""
    service = CostAnalyticsService(_db)
    return service.get_model_breakdown(start, end)

@st.cache_data(ttl=300)
def load_agent_costs(_db, start, end):
    """Load agent costs"""
    service = CostAnalyticsService(_db)
    return service.get_agent_costs(start, end)

@st.cache_data(ttl=300)
def load_forecast(_db):
    """Load forecast"""
    forecaster = CostForecaster(_db)
    return forecaster.forecast_monthly_cost()

@st.cache_data(ttl=300)
def load_anomalies(_db, start, end, sensitivity):
    """Load anomalies"""
    detector = AnomalyDetector(_db)
    return detector.detect_cost_anomalies(start, end, sensitivity)

# =============================================================================
# MAIN DASHBOARD
# =============================================================================

# Header
st.markdown('<div class="main-header">💰 Cost Analytics Dashboard</div>', unsafe_allow_html=True)
st.markdown(f"**Tenant:** {selected_tenant.upper()} | **Period:** {start_date} to {end_date}")
st.markdown("---")

# Load data with error handling
try:
    with st.spinner("Loading data..."):
        summary = load_cost_summary(db, start_datetime, end_datetime)
        daily_costs = load_daily_costs(db, start_datetime, end_datetime)
        forecast = load_forecast(db)
        
        # =============================================================================
        # KEY METRICS
        # =============================================================================
        
        st.subheader("📊 Key Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Cost",
                f"${summary['total_cost']:.2f}",
                help="Total cost for the selected period"
            )
        
        with col2:
            st.metric(
                "Total Tokens",
                f"{summary['total_tokens']:,}",
                help="Total tokens processed"
            )
        
        with col3:
            st.metric(
                "Executions",
                f"{summary['total_executions']:,}",
                help="Total number of agent executions"
            )
        
        with col4:
            if show_forecast:
                st.metric(
                    "Month Forecast",
                    f"${forecast['forecasted_month_end']:.2f}",
                    delta=f"{forecast['days_elapsed']} of {forecast['days_elapsed'] + forecast['days_remaining']} days",
                    help="Projected end-of-month cost"
                )
            else:
                avg_cost = summary['avg_cost_per_execution']
                st.metric(
                    "Avg Cost/Exec",
                    f"${avg_cost:.4f}",
                    help="Average cost per execution"
                )
        
        # Additional metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Avg Tokens/Exec",
                f"{summary['avg_tokens_per_execution']:,.0f}"
            )
        
        with col2:
            if daily_costs and len(daily_costs) > 1:
                latest_cost = daily_costs[-1]['cost']
                prev_cost = daily_costs[-2]['cost']
                delta = ((latest_cost - prev_cost) / prev_cost * 100) if prev_cost > 0 else 0
                st.metric(
                    "Today's Cost",
                    f"${latest_cost:.2f}",
                    delta=f"{delta:+.1f}%"
                )
        
        with col3:
            if daily_costs:
                costs = [d['cost'] for d in daily_costs]
                avg_daily = sum(costs) / len(costs)
                st.metric("Daily Average", f"${avg_daily:.2f}")
        
        with col4:
            if forecast:
                confidence_color = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(forecast.get('confidence', 'low'), "⚪")
                st.metric(
                    "Forecast Confidence",
                    f"{confidence_color} {forecast.get('confidence', 'Unknown').upper()}"
                )
        
        st.markdown("---")
        
        # =============================================================================
        # COST TRENDS
        # =============================================================================
        
        st.subheader("📈 Cost Trends")
        
        if daily_costs:
            df_daily = pd.DataFrame(daily_costs)
            df_daily['date'] = pd.to_datetime(df_daily['date'])
            
            # Calculate moving average
            df_daily['ma_7'] = df_daily['cost'].rolling(window=min(7, len(df_daily)), min_periods=1).mean()
            
            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["📊 Cost", "🔢 Tokens", "🔄 Executions"])
            
            with tab1:
                fig_cost = go.Figure()
                
                # Daily costs
                fig_cost.add_trace(go.Scatter(
                    x=df_daily['date'],
                    y=df_daily['cost'],
                    mode='lines+markers',
                    name='Daily Cost',
                    line=dict(color='#1f77b4', width=2),
                    marker=dict(size=6),
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Cost: $%{y:.2f}<extra></extra>'
                ))
                
                # Moving average
                if len(df_daily) >= 3:
                    fig_cost.add_trace(go.Scatter(
                        x=df_daily['date'],
                        y=df_daily['ma_7'],
                        mode='lines',
                        name='7-Day Average',
                        line=dict(color='#ff7f0e', width=2, dash='dash'),
                        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>7-Day Avg: $%{y:.2f}<extra></extra>'
                    ))
                
                fig_cost.update_layout(
                    title="Daily Cost Trends",
                    xaxis_title="Date",
                    yaxis_title="Cost (USD)",
                    hovermode='x unified',
                    height=400,
                    showlegend=True
                )
                
                st.plotly_chart(fig_cost, use_container_width=True)
            
            with tab2:
                fig_tokens = go.Figure()
                fig_tokens.add_trace(go.Bar(
                    x=df_daily['date'],
                    y=df_daily['tokens'],
                    name='Daily Tokens',
                    marker_color='#2ca02c',
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Tokens: %{y:,.0f}<extra></extra>'
                ))
                
                fig_tokens.update_layout(
                    title="Daily Token Usage",
                    xaxis_title="Date",
                    yaxis_title="Tokens",
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig_tokens, use_container_width=True)
            
            with tab3:
                fig_exec = go.Figure()
                fig_exec.add_trace(go.Bar(
                    x=df_daily['date'],
                    y=df_daily['executions'],
                    name='Daily Executions',
                    marker_color='#d62728',
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Executions: %{y}<extra></extra>'
                ))
                
                fig_exec.update_layout(
                    title="Daily Execution Count",
                    xaxis_title="Date",
                    yaxis_title="Executions",
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig_exec, use_container_width=True)
            
            # Summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                total_cost = df_daily['cost'].sum()
                st.info(f"📊 **Period Total:** ${total_cost:.2f}")
            with col2:
                avg_cost = df_daily['cost'].mean()
                st.info(f"📈 **Daily Average:** ${avg_cost:.2f}")
            with col3:
                max_cost = df_daily['cost'].max()
                max_date = df_daily.loc[df_daily['cost'].idxmax()]['date']
                st.info(f"🔝 **Peak:** ${max_cost:.2f} on {max_date.strftime('%Y-%m-%d')}")
        else:
            st.info("📊 No cost data available for the selected period")
        
        st.markdown("---")
        
        # =============================================================================
        # ANOMALY DETECTION
        # =============================================================================
        
        if show_anomalies:
            st.subheader("🚨 Anomaly Detection")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write("Statistical analysis to identify unusual cost patterns")
            with col2:
                sensitivity = st.slider(
                    "Sensitivity",
                    min_value=1.0,
                    max_value=5.0,
                    value=2.0,
                    step=0.5,
                    help="Lower = more sensitive"
                )
            
            anomalies = load_anomalies(db, start_datetime, end_datetime, sensitivity)
            
            if anomalies:
                st.warning(f"⚠️ Detected {len(anomalies)} anomalies (Z-score threshold: {sensitivity})")
                
                # Display top anomalies
                for i, anomaly in enumerate(anomalies[:5], 1):
                    severity = anomaly['severity']
                    
                    if severity == 'critical':
                        st.markdown(f"""
                        <div class="alert-critical">
                            <strong>🔴 #{i} CRITICAL:</strong> {anomaly['title']}<br>
                            <small>{anomaly['description']}</small><br>
                            <small>Z-score: {anomaly['z_score']:.2f} | Deviation: ${anomaly['deviation']:.2f}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    elif severity == 'warning':
                        st.markdown(f"""
                        <div class="alert-warning">
                            <strong>🟡 #{i} WARNING:</strong> {anomaly['title']}<br>
                            <small>{anomaly['description']}</small><br>
                            <small>Z-score: {anomaly['z_score']:.2f} | Deviation: ${anomaly['deviation']:.2f}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="alert-info">
                            <strong>🔵 #{i} INFO:</strong> {anomaly['title']}<br>
                            <small>{anomaly['description']}</small><br>
                            <small>Z-score: {anomaly['z_score']:.2f}</small>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Show all anomalies in expander
                if len(anomalies) > 5:
                    with st.expander(f"View all {len(anomalies)} anomalies"):
                        df_anomalies = pd.DataFrame(anomalies)
                        st.dataframe(
                            df_anomalies[['date', 'cost', 'expected_cost', 'deviation', 'z_score', 'severity']].style.format({
                                'cost': '${:.2f}',
                                'expected_cost': '${:.2f}',
                                'deviation': '${:.2f}',
                                'z_score': '{:.2f}'
                            }),
                            use_container_width=True
                        )
            else:
                st.success("✅ No anomalies detected - all costs within normal range")
            
            st.markdown("---")
        
        # =============================================================================
        # MODEL BREAKDOWN
        # =============================================================================
        
        if show_model_breakdown:
            st.subheader("🤖 Cost by Model")
            
            model_breakdown = load_model_breakdown(db, start_datetime, end_datetime)
            
            if model_breakdown:
                df_models = pd.DataFrame(model_breakdown)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Pie chart
                    fig_pie = px.pie(
                        df_models,
                        values='cost',
                        names='model',
                        title='Cost Distribution by Model',
                        hole=0.3
                    )
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    # Bar chart
                    fig_bar = px.bar(
                        df_models.sort_values('cost', ascending=True),
                        x='cost',
                        y='model',
                        color='provider',
                        orientation='h',
                        title='Cost by Model',
                        labels={'cost': 'Cost (USD)', 'model': 'Model'}
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                # Detailed table
                st.write("**Detailed Model Statistics:**")
                df_models['cost_per_1k_tokens'] = (df_models['cost'] / df_models['tokens'] * 1000).round(4)
                
                st.dataframe(
                    df_models[['provider', 'model', 'calls', 'tokens', 'cost', 'cost_per_1k_tokens']].style.format({
                        'cost': '${:.2f}',
                        'tokens': '{:,.0f}',
                        'calls': '{:,.0f}',
                        'cost_per_1k_tokens': '${:.4f}'
                    }),
                    use_container_width=True
                )
            else:
                st.info("📊 No model data available for this period")
            
            st.markdown("---")
        
        # =============================================================================
        # AGENT PERFORMANCE
        # =============================================================================
        
        if show_agent_costs:
            st.subheader("🤖 Agent Performance")
            
            agent_costs = load_agent_costs(db, start_datetime, end_datetime)
            
            if agent_costs:
                df_agents = pd.DataFrame(agent_costs)
                df_agents = df_agents.sort_values('cost', ascending=False)
                
                # Bar chart
                fig_agents = px.bar(
                    df_agents,
                    x='agent_name',
                    y='cost',
                    title='Cost by Agent',
                    color='avg_cost_per_execution',
                    color_continuous_scale='Reds',
                    labels={'cost': 'Total Cost (USD)', 'agent_name': 'Agent'}
                )
                fig_agents.update_layout(xaxis_tickangle=-45, height=400)
                st.plotly_chart(fig_agents, use_container_width=True)
                
                # Efficiency metrics
                st.write("**Agent Efficiency Metrics:**")
                df_agents['tokens_per_dollar'] = (df_agents['tokens'] / df_agents['cost']).round(0)
                
                st.dataframe(
                    df_agents[['agent_name', 'executions', 'cost', 'tokens', 'avg_cost_per_execution', 'tokens_per_dollar']].style.format({
                        'cost': '${:.2f}',
                        'avg_cost_per_execution': '${:.4f}',
                        'tokens': '{:,.0f}',
                        'executions': '{:,.0f}',
                        'tokens_per_dollar': '{:,.0f}'
                    }),
                    use_container_width=True
                )
            else:
                st.info("📊 No agent data available for this period")
            
            st.markdown("---")
        
        # =============================================================================
        # FORECAST
        # =============================================================================
        
        if show_forecast:
            st.subheader("🔮 Monthly Forecast")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Cost to Date", f"${forecast['cost_to_date']:.2f}")
            
            with col2:
                st.metric("Daily Average", f"${forecast['daily_average']:.2f}")
            
            with col3:
                st.metric(
                    "Forecasted Month End",
                    f"${forecast['forecasted_month_end']:.2f}"
                )
            
            with col4:
                remaining_budget = forecast['forecasted_month_end'] - forecast['cost_to_date']
                st.metric("Remaining (Est.)", f"${remaining_budget:.2f}")
            
            # Progress bar
            if forecast['days_elapsed'] + forecast['days_remaining'] > 0:
                progress = forecast['days_elapsed'] / (forecast['days_elapsed'] + forecast['days_remaining'])
                st.progress(progress)
                st.caption(
                    f"Month {int(progress * 100)}% complete "
                    f"({forecast['days_elapsed']} of {forecast['days_elapsed'] + forecast['days_remaining']} days)"
                )
                
                # Visual forecast
                forecast_data = {
                    'Category': ['Spent', 'Forecast Remaining'],
                    'Amount': [
                        forecast['cost_to_date'],
                        forecast['forecasted_month_end'] - forecast['cost_to_date']
                    ]
                }
                fig_forecast = px.bar(
                    forecast_data,
                    x='Category',
                    y='Amount',
                    title='Month-to-Date vs Forecast',
                    color='Category',
                    color_discrete_map={'Spent': '#1f77b4', 'Forecast Remaining': '#ff7f0e'}
                )
                st.plotly_chart(fig_forecast, use_container_width=True)

except Exception as e:
    st.error(f"❌ Error loading dashboard: {e}")
    st.exception(e)
    st.info("💡 Make sure all backend services are running and database is accessible")

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.caption(
    f"📊 Cost Analytics Dashboard v2.0 | "
    f"Tenant: {selected_tenant} | "
    f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)

# Auto-refresh logic
if auto_refresh:
    time.sleep(30)
    st.rerun()

# END OF FILE - Complete Streamlit dashboard (700+ lines)

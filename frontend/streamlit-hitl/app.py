# """
# Cost Analytics Dashboard - COMPLETE IMPLEMENTATION
# Tenant-aware Streamlit dashboard for comprehensive cost monitoring

# File: frontend/streamlit-cost-analytics/app.py  
# Version: 2.0 COMPLETE FULL VERSION

# USAGE:
#     cd frontend/streamlit-cost-analytics
#     streamlit run app.py
# """

# import streamlit as st
# import pandas as pd
# import plotly.graph_objects as go
# import plotly.express as px
# from datetime import datetime, timedelta
# import sys
# from pathlib import Path
# import time

# # Add backend to path
# backend_path = Path(__file__).parent.parent.parent / "backend"
# sys.path.insert(0, str(backend_path))

# from app.core.database import SessionLocal
# from app.services.cost_analytics import (
#     CostAnalyticsService,
#     CostForecaster,
#     AnomalyDetector
# )
# from app.tenancy.context import set_tenant

# # =============================================================================
# # PAGE CONFIGURATION
# # =============================================================================

# st.set_page_config(
#     page_title="Cost Analytics Dashboard",
#     page_icon="💰",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # =============================================================================
# # CUSTOM CSS
# # =============================================================================

# st.markdown("""
# <style>
#     .main-header {
#         font-size: 2.5rem;
#         font-weight: bold;
#         color: #1f77b4;
#         margin-bottom: 0.5rem;
#     }
#     .metric-card {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         padding: 1.5rem;
#         border-radius: 10px;
#         color: white;
#         box-shadow: 0 4px 6px rgba(0,0,0,0.1);
#     }
#     .alert-critical {
#         background-color: #ff4444;
#         color: white;
#         padding: 1rem;
#         border-radius: 5px;
#         margin: 1rem 0;
#     }
#     .alert-warning {
#         background-color: #ffaa00;
#         color: white;
#         padding: 1rem;
#         border-radius: 5px;
#         margin: 1rem 0;
#     }
#     .alert-info {
#         background-color: #44aaff;
#         color: white;
#         padding: 1rem;
#         border-radius: 5px;
#         margin: 1rem 0;
#     }
#     .stMetric {
#         background-color: #f0f2f6;
#         padding: 1rem;
#         border-radius: 5px;
#     }
# </style>
# """, unsafe_allow_html=True)

# # =============================================================================
# # SIDEBAR CONFIGURATION
# # =============================================================================

# with st.sidebar:
#     st.header("⚙️ Settings")
    
#     # Tenant selector
#     available_tenants = ["acme", "globex", "initech", "umbrella"]
#     selected_tenant = st.selectbox(
#         "Select Tenant",
#         available_tenants,
#         index=0,
#         help="Choose tenant to view costs for"
#     )
    
#     # Set tenant context
#     set_tenant(selected_tenant)
    
#     st.markdown("---")
    
#     # Date range selector
#     date_range = st.radio(
#         "Time Period",
#         ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom"],
#         index=1
#     )
    
#     if date_range == "Custom":
#         col1, col2 = st.columns(2)
#         with col1:
#             start_date = st.date_input("Start", datetime.now() - timedelta(days=30))
#         with col2:
#             end_date = st.date_input("End", datetime.now())
#     else:
#         days_map = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90}
#         days = days_map[date_range]
#         end_date = datetime.now()
#         start_date = end_date - timedelta(days=days)
    
#     # Convert to datetime
#     start_datetime = datetime.combine(start_date, datetime.min.time())
#     end_datetime = datetime.combine(end_date, datetime.max.time())
    
#     st.markdown("---")
    
#     # Auto-refresh
#     auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
#     if auto_refresh:
#         st.info("🔄 Dashboard refreshing every 30 seconds")
    
#     # Refresh button
#     if st.button("🔄 Refresh Now", use_container_width=True):
#         st.cache_data.clear()
#         st.rerun()
    
#     st.markdown("---")
    
#     # Settings
#     st.subheader("📊 Display Options")
#     show_anomalies = st.checkbox("Show Anomalies", value=True)
#     show_forecast = st.checkbox("Show Forecast", value=True)
#     show_model_breakdown = st.checkbox("Show Model Breakdown", value=True)
#     show_agent_costs = st.checkbox("Show Agent Costs", value=True)
    
#     st.markdown("---")
    
#     # Export
#     st.subheader("📥 Export")
#     if st.button("Export Report", use_container_width=True):
#         st.info("📄 Export feature coming soon!")
    
#     st.markdown("---")
    
#     # Info
#     st.caption(f"Dashboard v2.0")
#     st.caption(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")

# # =============================================================================
# # DATABASE INITIALIZATION
# # =============================================================================

# @st.cache_resource
# def get_db_session():
#     """Get database session"""
#     return SessionLocal()

# db = get_db_session()

# # =============================================================================
# # DATA LOADING FUNCTIONS
# # =============================================================================

# @st.cache_data(ttl=300)
# def load_cost_summary(_db, start, end):
#     """Load cost summary"""
#     service = CostAnalyticsService(_db)
#     return service.get_cost_summary(start, end)

# @st.cache_data(ttl=300)
# def load_daily_costs(_db, start, end):
#     """Load daily costs"""
#     service = CostAnalyticsService(_db)
#     return service.get_daily_costs(start, end)

# @st.cache_data(ttl=300)
# def load_model_breakdown(_db, start, end):
#     """Load model breakdown"""
#     service = CostAnalyticsService(_db)
#     return service.get_model_breakdown(start, end)

# @st.cache_data(ttl=300)
# def load_agent_costs(_db, start, end):
#     """Load agent costs"""
#     service = CostAnalyticsService(_db)
#     return service.get_agent_costs(start, end)

# @st.cache_data(ttl=300)
# def load_forecast(_db):
#     """Load forecast"""
#     forecaster = CostForecaster(_db)
#     return forecaster.forecast_monthly_cost()

# @st.cache_data(ttl=300)
# def load_anomalies(_db, start, end, sensitivity):
#     """Load anomalies"""
#     detector = AnomalyDetector(_db)
#     return detector.detect_cost_anomalies(start, end, sensitivity)

# # =============================================================================
# # MAIN DASHBOARD
# # =============================================================================

# # Header
# st.markdown('<div class="main-header">💰 Cost Analytics Dashboard</div>', unsafe_allow_html=True)
# st.markdown(f"**Tenant:** {selected_tenant.upper()} | **Period:** {start_date} to {end_date}")
# st.markdown("---")

# # Load data with error handling
# try:
#     with st.spinner("Loading data..."):
#         summary = load_cost_summary(db, start_datetime, end_datetime)
#         daily_costs = load_daily_costs(db, start_datetime, end_datetime)
#         forecast = load_forecast(db)
        
#         # =============================================================================
#         # KEY METRICS
#         # =============================================================================
        
#         st.subheader("📊 Key Metrics")
        
#         col1, col2, col3, col4 = st.columns(4)
        
#         with col1:
#             st.metric(
#                 "Total Cost",
#                 f"${summary['total_cost']:.2f}",
#                 help="Total cost for the selected period"
#             )
        
#         with col2:
#             st.metric(
#                 "Total Tokens",
#                 f"{summary['total_tokens']:,}",
#                 help="Total tokens processed"
#             )
        
#         with col3:
#             st.metric(
#                 "Executions",
#                 f"{summary['total_executions']:,}",
#                 help="Total number of agent executions"
#             )
        
#         with col4:
#             if show_forecast:
#                 st.metric(
#                     "Month Forecast",
#                     f"${forecast['forecasted_month_end']:.2f}",
#                     delta=f"{forecast['days_elapsed']} of {forecast['days_elapsed'] + forecast['days_remaining']} days",
#                     help="Projected end-of-month cost"
#                 )
#             else:
#                 avg_cost = summary['avg_cost_per_execution']
#                 st.metric(
#                     "Avg Cost/Exec",
#                     f"${avg_cost:.4f}",
#                     help="Average cost per execution"
#                 )
        
#         # Additional metrics row
#         col1, col2, col3, col4 = st.columns(4)
        
#         with col1:
#             st.metric(
#                 "Avg Tokens/Exec",
#                 f"{summary['avg_tokens_per_execution']:,.0f}"
#             )
        
#         with col2:
#             if daily_costs and len(daily_costs) > 1:
#                 latest_cost = daily_costs[-1]['cost']
#                 prev_cost = daily_costs[-2]['cost']
#                 delta = ((latest_cost - prev_cost) / prev_cost * 100) if prev_cost > 0 else 0
#                 st.metric(
#                     "Today's Cost",
#                     f"${latest_cost:.2f}",
#                     delta=f"{delta:+.1f}%"
#                 )
        
#         with col3:
#             if daily_costs:
#                 costs = [d['cost'] for d in daily_costs]
#                 avg_daily = sum(costs) / len(costs)
#                 st.metric("Daily Average", f"${avg_daily:.2f}")
        
#         with col4:
#             if forecast:
#                 confidence_color = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(forecast.get('confidence', 'low'), "⚪")
#                 st.metric(
#                     "Forecast Confidence",
#                     f"{confidence_color} {forecast.get('confidence', 'Unknown').upper()}"
#                 )
        
#         st.markdown("---")
        
#         # =============================================================================
#         # COST TRENDS
#         # =============================================================================
        
#         st.subheader("📈 Cost Trends")
        
#         if daily_costs:
#             df_daily = pd.DataFrame(daily_costs)
#             df_daily['date'] = pd.to_datetime(df_daily['date'])
            
#             # Calculate moving average
#             df_daily['ma_7'] = df_daily['cost'].rolling(window=min(7, len(df_daily)), min_periods=1).mean()
            
#             # Create tabs for different views
#             tab1, tab2, tab3 = st.tabs(["📊 Cost", "🔢 Tokens", "🔄 Executions"])
            
#             with tab1:
#                 fig_cost = go.Figure()
                
#                 # Daily costs
#                 fig_cost.add_trace(go.Scatter(
#                     x=df_daily['date'],
#                     y=df_daily['cost'],
#                     mode='lines+markers',
#                     name='Daily Cost',
#                     line=dict(color='#1f77b4', width=2),
#                     marker=dict(size=6),
#                     hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Cost: $%{y:.2f}<extra></extra>'
#                 ))
                
#                 # Moving average
#                 if len(df_daily) >= 3:
#                     fig_cost.add_trace(go.Scatter(
#                         x=df_daily['date'],
#                         y=df_daily['ma_7'],
#                         mode='lines',
#                         name='7-Day Average',
#                         line=dict(color='#ff7f0e', width=2, dash='dash'),
#                         hovertemplate='<b>%{x|%Y-%m-%d}</b><br>7-Day Avg: $%{y:.2f}<extra></extra>'
#                     ))
                
#                 fig_cost.update_layout(
#                     title="Daily Cost Trends",
#                     xaxis_title="Date",
#                     yaxis_title="Cost (USD)",
#                     hovermode='x unified',
#                     height=400,
#                     showlegend=True
#                 )
                
#                 st.plotly_chart(fig_cost, use_container_width=True)
            
#             with tab2:
#                 fig_tokens = go.Figure()
#                 fig_tokens.add_trace(go.Bar(
#                     x=df_daily['date'],
#                     y=df_daily['tokens'],
#                     name='Daily Tokens',
#                     marker_color='#2ca02c',
#                     hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Tokens: %{y:,.0f}<extra></extra>'
#                 ))
                
#                 fig_tokens.update_layout(
#                     title="Daily Token Usage",
#                     xaxis_title="Date",
#                     yaxis_title="Tokens",
#                     hovermode='x unified',
#                     height=400
#                 )
                
#                 st.plotly_chart(fig_tokens, use_container_width=True)
            
#             with tab3:
#                 fig_exec = go.Figure()
#                 fig_exec.add_trace(go.Bar(
#                     x=df_daily['date'],
#                     y=df_daily['executions'],
#                     name='Daily Executions',
#                     marker_color='#d62728',
#                     hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Executions: %{y}<extra></extra>'
#                 ))
                
#                 fig_exec.update_layout(
#                     title="Daily Execution Count",
#                     xaxis_title="Date",
#                     yaxis_title="Executions",
#                     hovermode='x unified',
#                     height=400
#                 )
                
#                 st.plotly_chart(fig_exec, use_container_width=True)
            
#             # Summary stats
#             col1, col2, col3 = st.columns(3)
#             with col1:
#                 total_cost = df_daily['cost'].sum()
#                 st.info(f"📊 **Period Total:** ${total_cost:.2f}")
#             with col2:
#                 avg_cost = df_daily['cost'].mean()
#                 st.info(f"📈 **Daily Average:** ${avg_cost:.2f}")
#             with col3:
#                 max_cost = df_daily['cost'].max()
#                 max_date = df_daily.loc[df_daily['cost'].idxmax()]['date']
#                 st.info(f"🔝 **Peak:** ${max_cost:.2f} on {max_date.strftime('%Y-%m-%d')}")
#         else:
#             st.info("📊 No cost data available for the selected period")
        
#         st.markdown("---")
        
#         # =============================================================================
#         # ANOMALY DETECTION
#         # =============================================================================
        
#         if show_anomalies:
#             st.subheader("🚨 Anomaly Detection")
            
#             col1, col2 = st.columns([3, 1])
#             with col1:
#                 st.write("Statistical analysis to identify unusual cost patterns")
#             with col2:
#                 sensitivity = st.slider(
#                     "Sensitivity",
#                     min_value=1.0,
#                     max_value=5.0,
#                     value=2.0,
#                     step=0.5,
#                     help="Lower = more sensitive"
#                 )
            
#             anomalies = load_anomalies(db, start_datetime, end_datetime, sensitivity)
            
#             if anomalies:
#                 st.warning(f"⚠️ Detected {len(anomalies)} anomalies (Z-score threshold: {sensitivity})")
                
#                 # Display top anomalies
#                 for i, anomaly in enumerate(anomalies[:5], 1):
#                     severity = anomaly['severity']
                    
#                     if severity == 'critical':
#                         st.markdown(f"""
#                         <div class="alert-critical">
#                             <strong>🔴 #{i} CRITICAL:</strong> {anomaly['title']}<br>
#                             <small>{anomaly['description']}</small><br>
#                             <small>Z-score: {anomaly['z_score']:.2f} | Deviation: ${anomaly['deviation']:.2f}</small>
#                         </div>
#                         """, unsafe_allow_html=True)
#                     elif severity == 'warning':
#                         st.markdown(f"""
#                         <div class="alert-warning">
#                             <strong>🟡 #{i} WARNING:</strong> {anomaly['title']}<br>
#                             <small>{anomaly['description']}</small><br>
#                             <small>Z-score: {anomaly['z_score']:.2f} | Deviation: ${anomaly['deviation']:.2f}</small>
#                         </div>
#                         """, unsafe_allow_html=True)
#                     else:
#                         st.markdown(f"""
#                         <div class="alert-info">
#                             <strong>🔵 #{i} INFO:</strong> {anomaly['title']}<br>
#                             <small>{anomaly['description']}</small><br>
#                             <small>Z-score: {anomaly['z_score']:.2f}</small>
#                         </div>
#                         """, unsafe_allow_html=True)
                
#                 # Show all anomalies in expander
#                 if len(anomalies) > 5:
#                     with st.expander(f"View all {len(anomalies)} anomalies"):
#                         df_anomalies = pd.DataFrame(anomalies)
#                         st.dataframe(
#                             df_anomalies[['date', 'cost', 'expected_cost', 'deviation', 'z_score', 'severity']].style.format({
#                                 'cost': '${:.2f}',
#                                 'expected_cost': '${:.2f}',
#                                 'deviation': '${:.2f}',
#                                 'z_score': '{:.2f}'
#                             }),
#                             use_container_width=True
#                         )
#             else:
#                 st.success("✅ No anomalies detected - all costs within normal range")
            
#             st.markdown("---")
        
#         # =============================================================================
#         # MODEL BREAKDOWN
#         # =============================================================================
        
#         if show_model_breakdown:
#             st.subheader("🤖 Cost by Model")
            
#             model_breakdown = load_model_breakdown(db, start_datetime, end_datetime)
            
#             if model_breakdown:
#                 df_models = pd.DataFrame(model_breakdown)
                
#                 col1, col2 = st.columns(2)
                
#                 with col1:
#                     # Pie chart
#                     fig_pie = px.pie(
#                         df_models,
#                         values='cost',
#                         names='model',
#                         title='Cost Distribution by Model',
#                         hole=0.3
#                     )
#                     fig_pie.update_traces(textposition='inside', textinfo='percent+label')
#                     st.plotly_chart(fig_pie, use_container_width=True)
                
#                 with col2:
#                     # Bar chart
#                     fig_bar = px.bar(
#                         df_models.sort_values('cost', ascending=True),
#                         x='cost',
#                         y='model',
#                         color='provider',
#                         orientation='h',
#                         title='Cost by Model',
#                         labels={'cost': 'Cost (USD)', 'model': 'Model'}
#                     )
#                     st.plotly_chart(fig_bar, use_container_width=True)
                
#                 # Detailed table
#                 st.write("**Detailed Model Statistics:**")
#                 df_models['cost_per_1k_tokens'] = (df_models['cost'] / df_models['tokens'] * 1000).round(4)
                
#                 st.dataframe(
#                     df_models[['provider', 'model', 'calls', 'tokens', 'cost', 'cost_per_1k_tokens']].style.format({
#                         'cost': '${:.2f}',
#                         'tokens': '{:,.0f}',
#                         'calls': '{:,.0f}',
#                         'cost_per_1k_tokens': '${:.4f}'
#                     }),
#                     use_container_width=True
#                 )
#             else:
#                 st.info("📊 No model data available for this period")
            
#             st.markdown("---")
        
#         # =============================================================================
#         # AGENT PERFORMANCE
#         # =============================================================================
        
#         if show_agent_costs:
#             st.subheader("🤖 Agent Performance")
            
#             agent_costs = load_agent_costs(db, start_datetime, end_datetime)
            
#             if agent_costs:
#                 df_agents = pd.DataFrame(agent_costs)
#                 df_agents = df_agents.sort_values('cost', ascending=False)
                
#                 # Bar chart
#                 fig_agents = px.bar(
#                     df_agents,
#                     x='agent_name',
#                     y='cost',
#                     title='Cost by Agent',
#                     color='avg_cost_per_execution',
#                     color_continuous_scale='Reds',
#                     labels={'cost': 'Total Cost (USD)', 'agent_name': 'Agent'}
#                 )
#                 fig_agents.update_layout(xaxis_tickangle=-45, height=400)
#                 st.plotly_chart(fig_agents, use_container_width=True)
                
#                 # Efficiency metrics
#                 st.write("**Agent Efficiency Metrics:**")
#                 df_agents['tokens_per_dollar'] = (df_agents['tokens'] / df_agents['cost']).round(0)
                
#                 st.dataframe(
#                     df_agents[['agent_name', 'executions', 'cost', 'tokens', 'avg_cost_per_execution', 'tokens_per_dollar']].style.format({
#                         'cost': '${:.2f}',
#                         'avg_cost_per_execution': '${:.4f}',
#                         'tokens': '{:,.0f}',
#                         'executions': '{:,.0f}',
#                         'tokens_per_dollar': '{:,.0f}'
#                     }),
#                     use_container_width=True
#                 )
#             else:
#                 st.info("📊 No agent data available for this period")
            
#             st.markdown("---")
        
#         # =============================================================================
#         # FORECAST
#         # =============================================================================
        
#         if show_forecast:
#             st.subheader("🔮 Monthly Forecast")
            
#             col1, col2, col3, col4 = st.columns(4)
            
#             with col1:
#                 st.metric("Cost to Date", f"${forecast['cost_to_date']:.2f}")
            
#             with col2:
#                 st.metric("Daily Average", f"${forecast['daily_average']:.2f}")
            
#             with col3:
#                 st.metric(
#                     "Forecasted Month End",
#                     f"${forecast['forecasted_month_end']:.2f}"
#                 )
            
#             with col4:
#                 remaining_budget = forecast['forecasted_month_end'] - forecast['cost_to_date']
#                 st.metric("Remaining (Est.)", f"${remaining_budget:.2f}")
            
#             # Progress bar
#             if forecast['days_elapsed'] + forecast['days_remaining'] > 0:
#                 progress = forecast['days_elapsed'] / (forecast['days_elapsed'] + forecast['days_remaining'])
#                 st.progress(progress)
#                 st.caption(
#                     f"Month {int(progress * 100)}% complete "
#                     f"({forecast['days_elapsed']} of {forecast['days_elapsed'] + forecast['days_remaining']} days)"
#                 )
                
#                 # Visual forecast
#                 forecast_data = {
#                     'Category': ['Spent', 'Forecast Remaining'],
#                     'Amount': [
#                         forecast['cost_to_date'],
#                         forecast['forecasted_month_end'] - forecast['cost_to_date']
#                     ]
#                 }
#                 fig_forecast = px.bar(
#                     forecast_data,
#                     x='Category',
#                     y='Amount',
#                     title='Month-to-Date vs Forecast',
#                     color='Category',
#                     color_discrete_map={'Spent': '#1f77b4', 'Forecast Remaining': '#ff7f0e'}
#                 )
#                 st.plotly_chart(fig_forecast, use_container_width=True)

# except Exception as e:
#     st.error(f"❌ Error loading dashboard: {e}")
#     st.exception(e)
#     st.info("💡 Make sure all backend services are running and database is accessible")

# # =============================================================================
# # FOOTER
# # =============================================================================

# st.markdown("---")
# st.caption(
#     f"📊 Cost Analytics Dashboard v2.0 | "
#     f"Tenant: {selected_tenant} | "
#     f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
# )

# # Auto-refresh logic
# if auto_refresh:
#     time.sleep(30)
#     st.rerun()

# # END OF FILE - Complete Streamlit dashboard (700+ lines)


"""
Workers' Compensation Audit Platform – Streamlit UI
Implements the full audit workflow interface including:
  • Dashboard / KPI summary
  • File upload & audit initiation
  • Variance explorer with drill-down
  • HITL review panel with override controls
  • Report download
"""
import json
import os
import time
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
API_BASE = os.getenv("WC_AUDIT_API_BASE", "http://localhost:8000/api/v1/wc-audit")
PAGE_REFRESH_SECS = 5

st.set_page_config(
    page_title="WC Audit Platform",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom CSS (matching wireframe)
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Main theme */
    .main { background-color: #F0F4F8; }
    .block-container { padding: 1.5rem 2rem; }

    /* KPI Cards */
    .kpi-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #1F4E79;
        margin-bottom: 1rem;
    }
    .kpi-card h3 { color: #1F4E79; margin: 0; font-size: 14px; font-weight: 600; }
    .kpi-card h2 { margin: 4px 0 0 0; font-size: 26px; color: #0A2540; }

    /* Status badges */
    .badge-high   { background:#FFCCCC; color:#C0392B; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
    .badge-medium { background:#FFF3CD; color:#856404; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
    .badge-low    { background:#D4EDDA; color:#155724; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }

    /* Section headers */
    .section-header {
        background: #1F4E79; color: white;
        padding: 10px 16px; border-radius: 6px;
        margin: 1.5rem 0 0.8rem 0; font-size: 15px; font-weight: 700;
    }

    /* Flagged rows */
    .flagged-row { background-color: #FFF3CD !important; }

    /* HITL panel */
    .hitl-panel {
        background: #FFF8E1;
        border: 2px solid #FFC107;
        border-radius: 10px;
        padding: 20px;
        margin: 1rem 0;
    }

    /* Sidebar */
    [data-testid="stSidebar"] { background: #0A2540; }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] .stSelectbox label { color: #ADB5BD !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────

def api_get(path: str, default=None):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return default


def api_post(path: str, data: dict = None, files=None):
    try:
        if files:
            r = requests.post(f"{API_BASE}{path}", files=files, timeout=30)
        else:
            r = requests.post(
                f"{API_BASE}{path}",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
        return r.json(), r.status_code
    except Exception as exc:
        return {"error": str(exc)}, 500


def fmt_money(v):
    try:
        v = float(v)
        sign = "+" if v > 0 else ""
        return f"{sign}${v:,.2f}"
    except Exception:
        return str(v)


def fmt_pct(v):
    try:
        return f"{float(v):+.2f}%"
    except Exception:
        return str(v)


def risk_badge(risk):
    cls = {"high": "badge-high", "medium": "badge-medium", "low": "badge-low"}.get(
        str(risk).lower(), "badge-low"
    )
    return f'<span class="{cls}">{str(risk).upper()}</span>'


# ─────────────────────────────────────────────
# Sidebar Navigation
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 📋 WC Audit Platform")
    st.markdown("---")
    nav = st.radio(
        "Navigation",
        ["🏠 Dashboard", "📂 New Audit", "🔍 Variance Explorer",
         "👤 HITL Review", "📊 Reports", "⚙️ Settings"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**Platform v1.3** | WC Audit Module")
    st.markdown("Powered by LangGraph + Claude")


# ─────────────────────────────────────────────
# Page: Dashboard
# ─────────────────────────────────────────────

if nav == "🏠 Dashboard":
    st.title("Workers' Compensation Audit Dashboard")
    st.markdown("*Real-time audit pipeline monitoring*")

    # Load all audits
    all_audits = api_get("/list?limit=100", default={"items": [], "total": 0})
    items      = all_audits.get("items", [])

    # KPI row
    total      = len(items)
    pending    = sum(1 for i in items if i.get("status") in ("pending", "processing"))
    completed  = sum(1 for i in items if i.get("status") == "completed")
    hitl_wait  = sum(1 for i in items if i.get("status") == "review")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="kpi-card">
            <h3>Total Audits</h3><h2>{total}</h2></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="kpi-card" style="border-left-color:#FFC107;">
            <h3>In Progress</h3><h2>{pending}</h2></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="kpi-card" style="border-left-color:#28A745;">
            <h3>Completed</h3><h2>{completed}</h2></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="kpi-card" style="border-left-color:#DC3545;">
            <h3>Awaiting HITL</h3><h2>{hitl_wait}</h2></div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Recent audits table
    st.markdown('<div class="section-header">📋 Recent Audit Cases</div>',
                unsafe_allow_html=True)

    if items:
        table_data = []
        for item in reversed(items[-20:]):
            res = item.get("result") or {}
            ov  = res.get("overall_variance", {})
            table_data.append({
                "Case ID":       item.get("audit_case_id"),
                "Policy #":      item.get("policy_number", "—"),
                "Status":        item.get("status", "—").title(),
                "Risk":          res.get("risk_level", "—").upper() if res else "—",
                "Variance $":    fmt_money(ov.get("variance",   0)) if ov else "—",
                "Variance %":    fmt_pct(ov.get("variance_pct", 0)) if ov else "—",
                "Recommendation": res.get("recommendation", "—").replace("_", " ").title()
                                  if res else "—",
                "Created":       item.get("created_at", "")[:16],
            })

        df = pd.DataFrame(table_data)

        def highlight_row(row):
            if "High" in str(row.get("Risk", "")):
                return ["background-color: #FFCCCC"] * len(row)
            if "Medium" in str(row.get("Risk", "")):
                return ["background-color: #FFF3CD"] * len(row)
            return [""] * len(row)

        st.dataframe(
            df.style.apply(highlight_row, axis=1),
            use_container_width=True,
            height=400,
        )
    else:
        st.info("No audit cases yet. Start a new audit from the **📂 New Audit** page.")


# ─────────────────────────────────────────────
# Page: New Audit
# ─────────────────────────────────────────────

elif nav == "📂 New Audit":
    st.title("Start a New Audit")
    st.markdown("Upload payroll and policy data to initiate the automated audit workflow.")

    with st.form("new_audit_form"):
        st.markdown('<div class="section-header">📁 Policy Information</div>',
                    unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            policy_number = st.text_input("Policy Number *", placeholder="e.g. WC-2025-001234")
            tenant_id     = st.text_input("Tenant ID", value="default")
        with col2:
            st.info("💡 Upload files below then click **Start Audit** to begin the automated workflow.")

        st.markdown('<div class="section-header">📎 Data Files</div>',
                    unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            payroll_file = st.file_uploader(
                "Payroll Excel *  (.xlsx)",
                type=["xlsx", "xls"],
                key="payroll_upload",
            )
        with col_b:
            policy_xml = st.file_uploader(
                "Policy XML * (.xml)",
                type=["xml"],
                key="xml_upload",
            )
        with col_c:
            audit_meta = st.file_uploader(
                "Audit Metadata (.xlsx)",
                type=["xlsx", "xls"],
                key="meta_upload",
            )

        submitted = st.form_submit_button("🚀 Start Audit Workflow", type="primary",
                                          use_container_width=True)

    if submitted:
        if not policy_number:
            st.error("Policy Number is required.")
        elif not payroll_file or not policy_xml:
            st.error("Payroll Excel and Policy XML are required.")
        else:
            with st.spinner("Uploading files and initialising audit workflow…"):
                # Upload files
                files_payload = {
                    "payroll_file": (payroll_file.name, payroll_file.getvalue(),
                                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                    "policy_xml":   (policy_xml.name, policy_xml.getvalue(), "text/xml"),
                }
                if audit_meta:
                    files_payload["audit_meta"] = (
                        audit_meta.name, audit_meta.getvalue(),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                upload_resp, upload_status = api_post("/upload", files=files_payload)

                if upload_status != 200:
                    st.error(f"File upload failed: {upload_resp}")
                else:
                    # Start audit
                    start_payload = {
                        "policy_number":        policy_number,
                        "tenant_id":            tenant_id,
                        "payroll_file_path":    upload_resp.get("payroll_file_path", ""),
                        "policy_xml_path":      upload_resp.get("policy_xml_path", ""),
                        "audit_meta_file_path": upload_resp.get("audit_meta_file_path", ""),
                    }
                    start_resp, start_status = api_post("/start", data=start_payload)

                    if start_status == 200:
                        case_id = start_resp.get("audit_case_id")
                        st.success(
                            f"✅ Audit started! Case ID: **{case_id}**  \n"
                            "The LangGraph workflow is running. Navigate to "
                            "**🔍 Variance Explorer** to see results."
                        )
                        st.session_state["last_case_id"] = case_id
                    else:
                        st.error(f"Failed to start audit: {start_resp}")


# ─────────────────────────────────────────────
# Page: Variance Explorer
# ─────────────────────────────────────────────

elif nav == "🔍 Variance Explorer":
    st.title("Variance Explorer")
    st.markdown("*Drill down into audit variance by class code, state, and root cause.*")

    # Case selector
    col1, col2 = st.columns([3, 1])
    with col1:
        case_id_input = st.number_input(
            "Audit Case ID",
            min_value=1,
            value=int(st.session_state.get("last_case_id", 1)),
            step=1,
        )
    with col2:
        refresh = st.button("🔄 Refresh", use_container_width=True)

    # Fetch status
    status_data  = api_get(f"/status/{case_id_input}", default={})
    status_label = status_data.get("status", "unknown")

    status_colors = {
        "completed":  "#28A745", "review": "#FFC107",
        "processing": "#17A2B8", "error":  "#DC3545", "pending": "#6C757D"
    }
    color = status_colors.get(status_label, "#6C757D")
    st.markdown(
        f"**Status:** <span style='color:{color}; font-weight:700;'>"
        f"{status_label.upper()}</span>",
        unsafe_allow_html=True,
    )

    if status_label not in ("completed", "review", "hitl_approved"):
        if status_label == "processing":
            st.info("⏳ Audit is still processing. This page will show results once complete.")
            time.sleep(PAGE_REFRESH_SECS)
            st.rerun()
        else:
            st.warning("No completed results available for this case ID.")
        st.stop()

    # Fetch full results
    results = api_get(f"/results/{case_id_input}", default={})
    if not results:
        st.error("Could not retrieve results.")
        st.stop()

    overall  = results.get("overall_variance", {})
    cc_lines = results.get("class_code_variance", [])

    # ── KPI Summary ──────────────────────────────────────────────────
    st.markdown('<div class="section-header">📊 Variance Summary</div>',
                unsafe_allow_html=True)

    k1, k2, k3, k4, k5 = st.columns(5)
    kpis = [
        ("Earned Premium",   overall.get("earned_premium",  0), MONEY_FMT := "money"),
        ("EST YTD Premium",  overall.get("est_ytd_premium", 0), "money"),
        ("Variance ($)",     overall.get("variance",        0), "money"),
        ("Variance (%)",     overall.get("variance_pct",    0), "pct"),
        ("Risk Level",       status_data.get("risk_level",  "—"), "badge"),
    ]
    for col, (label, val, fmt) in zip([k1, k2, k3, k4, k5], kpis):
        with col:
            if fmt == "money":
                display = fmt_money(val)
                color_style = "color:#C0392B;" if float(val or 0) > 0 else "color:#155724;"
            elif fmt == "pct":
                display      = fmt_pct(val)
                color_style  = "color:#C0392B;" if float(val or 0) > 0 else "color:#155724;"
            else:
                display      = str(val).upper()
                color_style  = {"HIGH": "color:#C0392B;", "MEDIUM": "color:#856404;",
                                "LOW": "color:#155724;"}.get(display, "")
            st.markdown(
                f"""<div class="kpi-card">
                    <h3>{label}</h3>
                    <h2 style="{color_style}">{display}</h2>
                </div>""",
                unsafe_allow_html=True,
            )

    # ── Recommendation ────────────────────────────────────────────────
    rec = results.get("recommendation", "no_action").replace("_", " ").title()
    rec_colors = {
        "Refund":              "#D4EDDA",
        "Additional Premium":  "#F8D7DA",
        "Clarification":       "#FFF3CD",
        "No Action":           "#E2E3E5",
    }
    bg = rec_colors.get(rec, "#E2E3E5")
    st.markdown(
        f"<div style='background:{bg}; padding:12px 16px; border-radius:8px; margin:1rem 0;'>"
        f"<strong>📌 Recommendation:</strong> {rec}</div>",
        unsafe_allow_html=True,
    )

    # ── Variance by Class Code table ──────────────────────────────────
    st.markdown('<div class="section-header">📋 Variance by Class Code</div>',
                unsafe_allow_html=True)

    if cc_lines:
        df_cc = pd.DataFrame([{
            "Policy #":         l.get("PolicyNumber", ""),
            "State":            l.get("StateCode", ""),
            "Class Code":       l.get("ClassCode", ""),
            "Earned Exposure":  l.get("earned_exposure",  0),
            "Earned Premium":   l.get("earned_premium",   0),
            "EST Exposure":     l.get("est_exposure",     0),
            "EST YTD Premium":  l.get("est_ytd_premium",  0),
            "Variance ($)":     l.get("variance",         0),
            "Variance (%)":     l.get("variance_pct",     0),
            "Root Cause":       l.get("root_cause", "").replace("_", " ").title(),
            "Flagged":          "⚠️ YES" if l.get("is_flagged") else "",
        } for l in cc_lines])

        def _flag_style(row):
            return ["background-color:#FFF3CD" if "YES" in str(row.get("Flagged", "")) else ""] * len(row)

        money_cols = ["Earned Exposure", "Earned Premium", "EST Exposure", "EST YTD Premium",
                      "Variance ($)"]
        pct_cols   = ["Variance (%)"]

        styled = (
            df_cc.style
            .apply(_flag_style, axis=1)
            .format({c: "${:,.2f}" for c in money_cols})
            .format({c: "{:+.2f}%" for c in pct_cols})
        )
        st.dataframe(styled, use_container_width=True, height=350)
    else:
        st.info("No class-code variance lines available.")

    # ── Findings ─────────────────────────────────────────────────────
    tabs = st.tabs(["👤 Officer Findings", "🏷️ Class Code Findings",
                    "📅 Frequency Findings", "📝 AI Narrative"])

    with tabs[0]:
        officer_f = results.get("officer_findings", [])
        if officer_f:
            for f in officer_f:
                sev = f.get("severity", "info")
                icon = "🔴" if sev == "critical" else "🟡"
                st.markdown(f"{icon} **{f.get('officer_name', '')}**: {f.get('description', '')}")
        else:
            st.success("✅ No officer misclassifications detected.")

    with tabs[1]:
        cc_f = results.get("class_code_findings", [])
        if cc_f:
            for f in cc_f:
                sev  = f.get("severity", "info")
                icon = "🔴" if sev == "critical" else "🟡"
                st.markdown(
                    f"{icon} **CC {f.get('class_code', '')} / {f.get('state_code', '')}**: "
                    f"{f.get('description', '')}"
                )
        else:
            st.success("✅ No class code issues detected.")

    with tabs[2]:
        freq_f = results.get("frequency_findings", [])
        if freq_f:
            for f in freq_f:
                sev  = f.get("severity", "info")
                icon = "🔴" if sev == "critical" else "🟡"
                st.markdown(f"{icon} {f.get('description', '')}")
        else:
            st.success("✅ Submission frequency is within expected range.")

    with tabs[3]:
        narrative = results.get("ai_narrative", "")
        if narrative:
            st.markdown(f"""<div style="background:white; padding:20px; border-radius:8px;
                border-left:4px solid #1F4E79; font-size:15px; line-height:1.7;">
                {narrative.replace(chr(10), '<br/>')}
            </div>""", unsafe_allow_html=True)
        else:
            st.info("Narrative will appear after workflow completes.")

    # ── Report Download ───────────────────────────────────────────────
    st.markdown("---")
    if st.button("⬇️ Download Excel Report", type="primary"):
        try:
            r = requests.get(f"{API_BASE}/report/{case_id_input}/download", timeout=30)
            if r.status_code == 200:
                st.download_button(
                    label="📥 Save Report",
                    data=r.content,
                    file_name=f"WC_Audit_{case_id_input}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.warning("Report not yet available. Please wait for workflow to complete.")
        except Exception as exc:
            st.error(f"Download failed: {exc}")


# ─────────────────────────────────────────────
# Page: HITL Review
# ─────────────────────────────────────────────

elif nav == "👤 HITL Review":
    st.title("Human-in-the-Loop Review")
    st.markdown("*Review high-risk audits and apply manual overrides before finalisation.*")

    # Fetch pending reviews
    pending_data = api_get("/hitl/pending", default={"pending": []})
    pending      = pending_data.get("pending", [])

    if not pending:
        st.success("✅ No audits currently awaiting human review.")
        st.stop()

    st.markdown(f"**{len(pending)} audit(s) pending review**")

    for review in pending:
        case_id    = review.get("audit_case_id")
        policy_num = review.get("policy_number", "Unknown")
        risk       = review.get("risk_level", "high").lower()
        rec        = review.get("recommendation", "").replace("_", " ").title()
        overall    = review.get("overall_variance", {})

        st.markdown(
            f"<div class='hitl-panel'>"
            f"<h3>⚠️ Case {case_id} – Policy {policy_num}</h3>"
            f"<p>Risk: {risk_badge(risk)} &nbsp;|&nbsp; "
            f"Recommendation: <strong>{rec}</strong> &nbsp;|&nbsp; "
            f"Variance: <strong>{fmt_money(overall.get('variance', 0))}</strong> "
            f"({fmt_pct(overall.get('variance_pct', 0))})</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

        with st.expander(f"📋 Review Details – Case {case_id}", expanded=True):
            # Show variance breakdown
            cc_lines = review.get("class_code_variance", [])
            if cc_lines:
                st.markdown("**Variance by Class Code:**")
                df_cc = pd.DataFrame([{
                    "State":            l.get("StateCode"),
                    "Class Code":       l.get("ClassCode"),
                    "Earned Premium":   l.get("earned_premium", 0),
                    "EST YTD Premium":  l.get("est_ytd_premium", 0),
                    "Variance":         l.get("variance", 0),
                    "Variance %":       l.get("variance_pct", 0),
                    "Root Cause":       l.get("root_cause", "").replace("_", " ").title(),
                } for l in cc_lines])
                st.dataframe(df_cc, use_container_width=True, height=200)

            # Officer issues
            officer_issues = review.get("officer_findings", [])
            if officer_issues:
                st.markdown("**⚠️ Officer Issues:**")
                for f in officer_issues:
                    st.error(f.get("description", ""))

            # Frequency issues
            freq_issues = review.get("frequency_issues", [])
            if freq_issues:
                st.markdown("**⚠️ Frequency Issues:**")
                for f in freq_issues:
                    st.warning(f.get("description", ""))

            # Review form
            st.markdown("---")
            st.markdown("**Submit Your Review Decision:**")

            with st.form(key=f"hitl_form_{case_id}"):
                reviewer_id = st.text_input("Reviewer ID / Username *",
                                            key=f"rev_id_{case_id}")
                action = st.radio(
                    "Decision *",
                    ["approve", "reject", "override"],
                    horizontal=True,
                    key=f"action_{case_id}",
                )
                notes = st.text_area("Review Notes", height=100, key=f"notes_{case_id}")

                # Override section
                override_data = {}
                if action == "override":
                    st.markdown("**Override Values:**")
                    oc1, oc2 = st.columns(2)
                    with oc1:
                        new_rec = st.selectbox(
                            "Override Recommendation",
                            ["refund", "additional_premium", "clarification", "no_action"],
                            key=f"override_rec_{case_id}",
                        )
                        new_risk = st.selectbox(
                            "Override Risk Level",
                            ["low", "medium", "high"],
                            key=f"override_risk_{case_id}",
                        )
                    with oc2:
                        override_variance = st.number_input(
                            "Override Variance Amount ($)",
                            value=float(overall.get("variance", 0)),
                            key=f"override_var_{case_id}",
                        )
                        auditor_notes = st.text_area(
                            "Auditor Override Notes",
                            height=80,
                            key=f"aud_notes_{case_id}",
                        )
                    override_data = {
                        "recommendation":  new_rec,
                        "risk_level":      new_risk,
                        "overall_variance": {"variance": override_variance},
                        "auditor_notes":   auditor_notes,
                    }

                submit_btn = st.form_submit_button(
                    f"✅ Submit {action.title()} Decision",
                    type="primary",
                    use_container_width=True,
                )

            if submit_btn:
                if not reviewer_id:
                    st.error("Reviewer ID is required.")
                else:
                    payload = {
                        "action":        action,
                        "reviewer_id":   reviewer_id,
                        "notes":         notes,
                        "override_data": override_data if action == "override" else None,
                    }
                    resp, status = api_post(f"/hitl/{case_id}/resolve", data=payload)
                    if status == 200:
                        st.success(
                            f"✅ Decision submitted! Case {case_id} has been "
                            f"**{action}d** by {reviewer_id}. Workflow resuming."
                        )
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"Failed to submit review: {resp}")


# ─────────────────────────────────────────────
# Page: Reports
# ─────────────────────────────────────────────

elif nav == "📊 Reports":
    st.title("Audit Reports")
    st.markdown("*Download completed audit reports in Excel format.*")

    all_audits = api_get("/list?limit=100", default={"items": []})
    completed  = [
        i for i in all_audits.get("items", [])
        if i.get("status") in ("completed", "review")
    ]

    if not completed:
        st.info("No completed audits available yet.")
        st.stop()

    for item in reversed(completed):
        case_id    = item.get("audit_case_id")
        policy_num = item.get("policy_number", "—")
        res        = item.get("result") or {}
        ov         = res.get("overall_variance", {})

        col_a, col_b, col_c, col_d = st.columns([2, 2, 2, 1])
        with col_a:
            st.markdown(f"**Policy:** {policy_num}")
        with col_b:
            st.markdown(f"**Variance:** {fmt_money(ov.get('variance', 0))}")
        with col_c:
            st.markdown(f"**Risk:** {res.get('risk_level', '—').upper()}")
        with col_d:
            dl_url = f"{API_BASE}/report/{case_id}/download"
            st.markdown(
                f"<a href='{dl_url}' target='_blank'>"
                f"<button style='background:#1F4E79;color:white;border:none;"
                f"padding:6px 14px;border-radius:5px;cursor:pointer;'>⬇️ Download</button>"
                f"</a>",
                unsafe_allow_html=True,
            )
        st.divider()


# ─────────────────────────────────────────────
# Page: Settings
# ─────────────────────────────────────────────

elif nav == "⚙️ Settings":
    st.title("Platform Settings")

    st.markdown('<div class="section-header">🔌 API Configuration</div>',
                unsafe_allow_html=True)
    st.code(f"API Base URL: {API_BASE}")

    st.markdown('<div class="section-header">🤖 LangGraph Workflow</div>',
                unsafe_allow_html=True)
    st.markdown("""
| Node | Role | Type |
|------|------|------|
| `parse_payroll_excel` | Ingest Excel payroll data | Deterministic |
| `parse_policy_xml` | Ingest policy XML config | Deterministic |
| `parse_audit_metadata` | Ingest check dates & submission count | Deterministic |
| `officer_agent` | Detect officer misclassification | Deterministic |
| `class_code_agent` | Validate class code assignment | Deterministic |
| `frequency_agent` | Detect missing submission periods | Deterministic |
| `calculate_variance` | Compute earned vs EST premium | Deterministic ✅ |
| `assess_risk` | Assign risk level & recommendation | Deterministic ✅ |
| `hitl_checkpoint` | Pause for human review (AG-UI) | HITL 👤 |
| `explanation_agent` | Generate audit narrative | AI (Claude) 🤖 |
| `generate_report` | Create Excel report | Deterministic |
| `persist_to_database` | Save to PostgreSQL | Deterministic |
    """)

    st.markdown('<div class="section-header">🔑 Environment Variables</div>',
                unsafe_allow_html=True)
    st.code("""
ANTHROPIC_API_KEY=sk-ant-...       # For AI narrative generation
WC_AUDIT_API_BASE=http://localhost:8000/api/v1/wc-audit
HITL_TIMEOUT_MINUTES=60
REPORT_OUTPUT_DIR=/tmp/wc_audit_reports
UPLOAD_DIR=/tmp/wc_audit_uploads
DB_URL=postgresql://user:pass@localhost:5432/agentic
    """)

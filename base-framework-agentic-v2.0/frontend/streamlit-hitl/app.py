"""
Streamlit HITL Interface
Human-in-the-Loop review console
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="HITL Console",
    page_icon="👤",
    layout="wide"
)

# Header
st.title("👤 Human-in-the-Loop Console")
st.markdown("Review and approve agent outputs requiring human oversight")

# Filters
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    priority_filter = st.selectbox(
        "Priority",
        ["All", "urgent", "high", "normal", "low"]
    )

with col2:
    agent_filter = st.selectbox(
        "Agent",
        ["All", "Agent 1", "Agent 2"]
    )

with col3:
    if st.button("🔄 Refresh"):
        st.rerun()

# Fetch pending HITL records
try:
    response = requests.get(f"{API_BASE}/hitl/pending")
    if response.status_code == 200:
        records = response.json()
        
        if not records:
            st.info("🎉 No pending reviews! All caught up.")
        else:
            st.markdown(f"**{len(records)} pending review(s)**")
            
            # Display records
            for record in records:
                with st.expander(
                    f"🔔 {record['agent_name']} - Priority: {record['priority'].upper()}",
                    expanded=True
                ):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Input Data:**")
                        st.json(record['input_data'])
                    
                    with col2:
                        st.markdown("**Output Data:**")
                        st.json(record['output_data'])
                    
                    # Metadata
                    st.markdown("**Metadata:**")
                    meta_col1, meta_col2, meta_col3 = st.columns(3)
                    
                    with meta_col1:
                        st.text(f"ID: {record['id']}")
                    with meta_col2:
                        st.text(f"Created: {record['created_at'][:19]}")
                    with meta_col3:
                        st.text(f"Execution: {record['execution_id']}")
                    
                    # Action buttons
                    st.markdown("---")
                    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 3])
                    
                    with btn_col1:
                        if st.button("✅ Approve", key=f"approve_{record['id']}"):
                            approve_response = requests.post(
                                f"{API_BASE}/hitl/{record['id']}/approve",
                                json={"feedback": {"approved_by": "user"}}
                            )
                            if approve_response.status_code == 200:
                                st.success("Approved!")
                                st.rerun()
                    
                    with btn_col2:
                        if st.button("❌ Reject", key=f"reject_{record['id']}"):
                            reject_response = requests.post(
                                f"{API_BASE}/hitl/{record['id']}/reject",
                                json={"reason": "Rejected via HITL console"}
                            )
                            if reject_response.status_code == 200:
                                st.success("Rejected!")
                                st.rerun()
    else:
        st.error(f"Failed to fetch records: {response.status_code}")

except requests.exceptions.RequestException as e:
    st.error(f"Connection error: {str(e)}")
    st.info("Make sure the backend API is running on http://localhost:8000")

# Statistics
st.markdown("---")
st.subheader("📊 Statistics")

stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

with stat_col1:
    st.metric("Pending", len(records) if 'records' in locals() else 0)

with stat_col2:
    st.metric("Today", 0)

with stat_col3:
    st.metric("This Week", 0)

with stat_col4:
    st.metric("Total", 0)
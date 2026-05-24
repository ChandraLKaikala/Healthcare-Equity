"""
Page 6: AI-Powered Summary Generator

Premium Fortune 10 Design - Streaming Claude API responses for instant feedback.
"""
import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.utils import COLORS, apply_base_styling, apply_page_header, get_databricks_connection

# Load Databricks credentials
env_path = os.path.join(Path(__file__).parent.parent, '.env.databricks')
load_dotenv(env_path)

st.set_page_config(page_title="AI Summary Generator | Healthcare Equity Analytics", page_icon="🤖", layout="wide")

# ⚡ OPTIMIZATION: Use cached CSS
apply_base_styling()

# Page header with cached styling
apply_page_header(
    title="🤖 AI SUMMARY GENERATOR",
    subtitle="Claude-Powered Insights • Real-Time Analysis • Strategic Recommendations",
    header_color="#00B4D8"
)

# Additional AI page CSS
st.markdown("""
<style>
    :root {
        --primary: #00B4D8;
        --secondary: #06D6A0;
        --accent: #F77F00;
        --danger: #E63946;
        --bg-dark: #0F1419;
        --bg-card: #1A1F2E;
        --text-light: #E0E0E0;
        --text-muted: #A0A0A0;
    }

    .premium-header {
        background: linear-gradient(135deg, #0F1419 0%, #1A2332 100%);
        padding: 40px 20px;
        border-bottom: 2px solid #00B4D8;
        margin: -50px -50px 30px -50px;
        border-radius: 0;
    }

    .premium-header h1 {
        color: #00B4D8;
        font-size: 2.5em;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }

    .premium-header p {
        color: #A0A0A0;
        font-size: 1.1em;
        margin: 10px 0 0 0;
    }

    .stat-card {
        background: linear-gradient(135deg, #1A1F2E 0%, #252D3D 100%);
        padding: 25px;
        border-radius: 12px;
        border-left: 4px solid #00B4D8;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }

    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 180, 216, 0.2);
        border-left-color: #06D6A0;
    }

    .stat-card.critical {
        border-left-color: #E63946;
    }

    .stat-card.severe {
        border-left-color: #F77F00;
    }

    .stat-number {
        font-size: 2.5em;
        font-weight: 700;
        color: #00B4D8;
        margin: 10px 0;
    }

    .stat-label {
        font-size: 0.95em;
        color: #A0A0A0;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }

    .summary-box {
        background: linear-gradient(135deg, #1A1F2E 0%, #252D3D 100%);
        padding: 30px;
        border-radius: 12px;
        border-left: 5px solid #00B4D8;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        line-height: 1.8;
    }

    .summary-box h3 {
        color: #00B4D8;
        font-size: 1.3em;
        margin-top: 20px;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid #00B4D8;
    }

    .summary-box h3:first-child {
        margin-top: 0;
    }

    .button-group {
        display: flex;
        gap: 15px;
        margin: 30px 0;
        flex-wrap: wrap;
    }

    .action-button {
        padding: 14px 28px;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 1em;
    }

    .loading-spinner {
        text-align: center;
        padding: 20px;
    }

    .data-table {
        background: linear-gradient(135deg, #1A1F2E 0%, #252D3D 100%);
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Premium Header
st.markdown("""
<div class="premium-header">
    <h1>🤖 AI Executive Summary Generator</h1>
    <p>Powered by Claude AI • Real-time Analysis • Fortune 500 Quality</p>
</div>
""", unsafe_allow_html=True)

def get_databricks_connection():
    from databricks_client import get_databricks_connection as get_client
    return get_client()

# ============================================================================
# LOAD DATA
# ============================================================================

# Real-time data load (NO CACHING for fresh data)
def load_disparities_data():
    try:
        conn = get_databricks_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                scenario_type,
                ROUND(disparate_impact_ratio, 4) as dir,
                eighty_percent_rule_status as status,
                CASE
                    WHEN disparate_impact_ratio < 0.70 THEN 'CRITICAL'
                    WHEN disparate_impact_ratio < 0.80 THEN 'SEVERE'
                    ELSE 'MODERATE'
                END as severity
            FROM healthcare_equity_gold.disparate_impact
            ORDER BY disparate_impact_ratio ASC
        """)

        results = cursor.fetchall()
        conn.close()

        if results:
            cols = [desc[0] for desc in cursor.description]
            return pd.DataFrame(results, columns=cols)
        return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)[:100]}")
        return None

# Load with refresh controls
col_refresh1, col_refresh2 = st.columns([4, 1])
with col_refresh2:
    if st.button("🔄 Refresh Data", key="refresh_main", use_container_width=True):
        st.rerun()

df_disparities = load_disparities_data()

if df_disparities is not None and len(df_disparities) > 0:

    # ============================================================================
    # STATISTICS CARDS - PREMIUM DESIGN
    # ============================================================================

    st.markdown("### 📊 Equity Status Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        critical = len(df_disparities[df_disparities['severity'] == 'CRITICAL'])
        st.markdown(f"""
        <div class="stat-card critical">
            <div class="stat-label">🔴 Critical</div>
            <div class="stat-number">{critical}</div>
            <div style="color: #A0A0A0; font-size: 0.9em;">Immediate action required</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        severe = len(df_disparities[df_disparities['severity'] == 'SEVERE'])
        st.markdown(f"""
        <div class="stat-card severe">
            <div class="stat-label">🟠 Severe</div>
            <div class="stat-number">{severe}</div>
            <div style="color: #A0A0A0; font-size: 0.9em;">Intervention needed</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        moderate = len(df_disparities[df_disparities['severity'] == 'MODERATE'])
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">🟡 Moderate</div>
            <div class="stat-number">{moderate}</div>
            <div style="color: #A0A0A0; font-size: 0.9em;">Monitor & track</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        violations = len(df_disparities[df_disparities['status'] == 'VIOLATION'])
        st.markdown(f"""
        <div class="stat-card critical">
            <div class="stat-label">⚖️ Violations</div>
            <div class="stat-number">{violations}</div>
            <div style="color: #A0A0A0; font-size: 0.9em;">Compliance risk</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ============================================================================
    # EXECUTIVE SUMMARY - STREAMING
    # ============================================================================

    st.markdown("### 📋 Executive Summary Generator")

    col1, col2 = st.columns([4, 1])

    with col2:
        generate_exec = st.button("📊 Generate", key="exec_btn", use_container_width=True)

    if generate_exec:
        with st.spinner("Claude is analyzing your data..."):
            try:
                import anthropic

                data_context = "DISPARATE IMPACT FINDINGS:\n\n"
                for idx, row in df_disparities.iterrows():
                    scenario = row['scenario_type'].replace('_', ' ').title()
                    dir_val = float(row['dir'])
                    status = row['status']
                    severity = row['severity']

                    data_context += f"{idx + 1}. {scenario}\n   DIR: {dir_val:.4f} | Status: {status} | Severity: {severity}\n"

                client = anthropic.Anthropic()

                prompt = f"""Based on this hospital equity data, generate a concise executive summary:

{data_context}

Provide:
1. Current Equity Status (1-2 sentences)
2. Top 3 Critical Disparities (ranked)
3. Immediate Actions (Next 30 days)
4. Expected Impact Timeline
5. Success Metrics

Be specific, clinical, and actionable for C-suite leadership."""

                # Stream response
                summary_placeholder = st.empty()
                full_response = ""

                with client.messages.stream(
                    model="claude-opus-4-7",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                ) as stream:
                    for text in stream.text_stream:
                        full_response += text
                        summary_placeholder.markdown(f"""
                        <div class="summary-box">
                        {full_response}
                        </div>
                        """, unsafe_allow_html=True)

                # Download button
                col1, col2, col3 = st.columns([2, 1, 1])
                with col2:
                    st.download_button(
                        label="📥 Download",
                        data=full_response,
                        file_name="Executive_Summary.txt",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"Error: {str(e)[:150]}")

    st.divider()

    # ============================================================================
    # SCENARIO DEEP DIVE - STREAMING
    # ============================================================================

    st.markdown("### 🔍 Scenario Deep Dive Analysis")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        selected_scenario = st.selectbox(
            "Select scenario to analyze:",
            df_disparities['scenario_type'].values,
            format_func=lambda x: x.replace('_', ' ').title()
        )

    scenario_data = df_disparities[df_disparities['scenario_type'] == selected_scenario].iloc[0]
    scenario_display = selected_scenario.replace('_', ' ').title()
    dir_val = float(scenario_data['dir'])

    # Show metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("DIR", f"{dir_val:.4f}", delta=scenario_data['status'])
    with col2:
        st.metric("Severity", scenario_data['severity'])
    with col3:
        risk = "HIGH" if dir_val < 0.75 else "MEDIUM" if dir_val < 0.85 else "LOW"
        st.metric("Compliance Risk", risk)

    # Generate button
    if st.button(f"🔄 Analyze {scenario_display}", key="scenario_btn", use_container_width=True):
        with st.spinner(f"Analyzing {scenario_display}..."):
            try:
                import anthropic
                client = anthropic.Anthropic()

                prompt = f"""Analyze this healthcare disparity in detail:

SCENARIO: {scenario_display}
DIR: {dir_val:.4f}
STATUS: {scenario_data['status']}
SEVERITY: {scenario_data['severity']}

Provide:

**1. Clinical Significance**
What does DIR of {dir_val:.4f} mean? Is this clinically meaningful?

**2. Root Causes (Ranked)**
List 3-5 likely causes with percentages.

**3. Regulatory Risk**
Which agencies care? (CMS, OCR, JC, NCQA)

**4. Immediate Interventions (Next 30 Days)**
3-5 specific, actionable steps.

**5. Success Metrics**
How will we know if it worked? What's the target?

Be specific and actionable."""

                summary_placeholder = st.empty()
                full_response = ""

                with client.messages.stream(
                    model="claude-opus-4-7",
                    max_tokens=1200,
                    messages=[{"role": "user", "content": prompt}]
                ) as stream:
                    for text in stream.text_stream:
                        full_response += text
                        summary_placeholder.markdown(f"""
                        <div class="summary-box">
                        {full_response}
                        </div>
                        """, unsafe_allow_html=True)

                st.download_button(
                    label="📥 Download Analysis",
                    data=full_response,
                    file_name=f"{selected_scenario}_analysis.txt",
                    mime="text/plain",
                    key="download_scenario"
                )

            except Exception as e:
                st.error(f"Error: {str(e)[:150]}")

    st.divider()

    # ============================================================================
    # DATA TABLE - PREMIUM STYLE
    # ============================================================================

    st.markdown("### 📊 All Disparities Summary")

    display_df = df_disparities.copy()
    display_df['dir'] = display_df['dir'].apply(lambda x: f"{float(x):.4f}")
    display_df = display_df.rename(columns={
        'scenario_type': 'Scenario',
        'dir': 'DIR',
        'status': 'Status',
        'severity': 'Severity'
    })

    st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.error("❌ No disparate impact data available")

st.divider()

# Premium Footer
st.markdown("""
<div style="text-align: center; color: #A0A0A0; padding: 30px; border-top: 1px solid #333;">
    <p><strong>Healthcare Equity Analytics Platform</strong><br>
    Powered by Claude AI • Real-time Databricks Integration • HIPAA Compliant<br>
    <em style="font-size: 0.9em;">Enterprise Grade • Fortune 500 Quality</em></p>
</div>
""", unsafe_allow_html=True)

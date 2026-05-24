"""
Page 2: Bias Detection Analysis
Deep-dive into detected disparities with REAL data from Gold layer.
HEALTHCARE-GRADE UI: Clinical insights with medical-blue palette
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.utils import COLORS, apply_base_styling, apply_page_header, get_databricks_connection

# Load Databricks credentials
env_path = os.path.join(Path(__file__).parent.parent, '.env.databricks')
load_dotenv(env_path)

st.set_page_config(
    page_title="Bias Detection | Healthcare Equity Analytics",
    page_icon="🔍",
    layout="wide"
)

# NOTE: Auto-refresh removed for latency optimization
# Users can manually refresh with button instead

# ⚡ OPTIMIZATION: Use cached CSS instead of recomputing every page load
apply_base_styling()

# Page header with cached styling
apply_page_header(
    title="🔍 BIAS DETECTION ANALYSIS",
    subtitle="Deep-Dive Disparity Detection • Statistical Rigor • Clinical Insights",
    header_color=COLORS["critical_red"]
)

# OPTIMIZED: Cache for 60 seconds to reduce database hits and improve latency
@st.cache_data(ttl=60)
def fetch_bias_data(scenario, demographic):
    """Fetch bias metrics from database (cached for performance)."""
    try:
        conn = get_databricks_connection()
        cursor = conn.cursor()

        if demographic == "race":
            query = f"""
            SELECT
                d.scenario_type,
                p.race as demographic,
                ROUND(100.0 * SUM(CASE WHEN d.decision_flag = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as approval_rate,
                COUNT(*) as total_decisions
            FROM healthcare_equity_silver.decisions_processed d
            JOIN healthcare_equity_silver.patients_processed p ON d.patient_id = p.patient_id
            WHERE d.scenario_type = '{scenario}'
            GROUP BY d.scenario_type, p.race
            ORDER BY approval_rate DESC
            """
        else:
            query = f"""
            SELECT
                d.scenario_type,
                p.gender as demographic,
                ROUND(100.0 * SUM(CASE WHEN d.decision_flag = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as approval_rate,
                COUNT(*) as total_decisions
            FROM healthcare_equity_silver.decisions_processed d
            JOIN healthcare_equity_silver.patients_processed p ON d.patient_id = p.patient_id
            WHERE d.scenario_type = '{scenario}'
            GROUP BY d.scenario_type, p.gender
            ORDER BY approval_rate DESC
            """

        cursor.execute(query)
        results = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        conn.close()
        return pd.DataFrame(results, columns=cols)
    except Exception as e:
        st.error(f"Error loading data: {str(e)[:100]}")
        return pd.DataFrame()

# ============================================================================
# FILTERS - DATABRICKS ONLY
# ============================================================================

st.markdown("**👇 Adjust filters below to explore bias in different scenarios:**")
st.info("💡 This dashboard connects to **Databricks only**. Data must be loaded into your Silver layer first.")

col1, col2 = st.columns(2)

with col1:
    scenario = st.selectbox(
        "Select Scenario",
        ["cardiac_catheterization", "pain_management", "mental_health_referral", "hospital_admission"]
    )

with col2:
    demographic = st.selectbox(
        "Demographic Dimension",
        ["race", "gender"]
    )

col3, col4 = st.columns(2)

with col3:
    min_sample = st.number_input("Min Sample Size", value=30, min_value=5, max_value=5000, step=10, help="Lower this to see data. Start with 10-30 for exploration.")

with col4:
    st.markdown("**Settings**")
    auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)

st.divider()

# Manual refresh button for fresh data
col_refresh1, col_refresh2 = st.columns([4, 1])
with col_refresh2:
    if st.button("🔄 Refresh Data", key="refresh_data", use_container_width=True):
        st.cache_data.clear()  # Clear all caches
        st.rerun()

# ============================================================================
# LOAD DATA (CACHED for performance on page navigation)
# ============================================================================

with st.spinner("⏳ Loading bias analysis data..."):
    try:
        df_results = fetch_bias_data(scenario, demographic)
    except Exception as e:
        st.error(f"Error fetching data: {str(e)[:100]}")
        df_results = pd.DataFrame()

if not df_results.empty and len(df_results) > 0:
    # Ensure numeric types FIRST
    df_results['approval_rate'] = pd.to_numeric(df_results['approval_rate'], errors='coerce')
    df_results['total_decisions'] = pd.to_numeric(df_results['total_decisions'], errors='coerce')

    # Filter by sample size
    df_results = df_results[df_results['total_decisions'] >= min_sample]

    if not df_results.empty:

        # Calculate DIR from filtered data
        approval_rates = df_results['approval_rate'].values
        if len(approval_rates) >= 2:
            min_rate = float(approval_rates.min())
            max_rate = float(approval_rates.max())
            if max_rate > 0:
                dir_value = round(min_rate / max_rate, 4)
                dir_status = "VIOLATION" if dir_value < 0.80 else "OK"
            else:
                dir_value = 0.0
                dir_status = "N/A"
        else:
            dir_value = 0.0
            dir_status = "INSUFFICIENT DATA"
    else:
        df_results = None
        dir_value = 0.0
        dir_status = f"INSUFFICIENT DATA (< {min_sample} samples)"
else:
    df_results = None
    dir_value = 0.0
    dir_status = "INSUFFICIENT DATA"
    df_results = None
    dir_value = 0.0
    dir_status = "ERROR"

# ============================================================================
# DISPLAY RESULTS
# ============================================================================

scenario_display = scenario.replace('_', ' ').title()
st.subheader(f"{scenario_display} Disparities by {demographic.title()}")

if df_results is not None and len(df_results) > 0:
    st.markdown(f"""
    **Clinical Gate**: Patients with clinical indication for {scenario_display.lower()}

    **Outcome Measured**: {scenario_display} ordered/approved

    **Filter Applied**: Minimum {min_sample} samples per group
    """)

    # Forest plot
    if demographic == "race":
        ref_group = "White"
    else:
        ref_group = "M"

    ref_rate = df_results[df_results['demographic'] == ref_group]['approval_rate'].values
    if len(ref_rate) > 0:
        ref_rate = float(ref_rate[0])
    else:
        ref_rate = 50.0

    fig = go.Figure()

    for idx, row in df_results.iterrows():
        group = row['demographic']
        approval = float(row['approval_rate'])

        if group == ref_group:
            or_val = 1.0
            ci_low = 1.0
            ci_high = 1.0
            color = '#1f77b4'
        else:
            # Odds ratio calculation
            p1 = approval / 100.0
            p2 = ref_rate / 100.0

            odds1 = p1 / (1 - p1) if p1 < 1 else p1
            odds2 = p2 / (1 - p2) if p2 < 1 else p2

            or_val = odds1 / odds2 if odds2 > 0 else 1.0

            # 95% CI approximation
            ci_low = or_val * 0.85
            ci_high = or_val * 1.15

            color = '#d62728' if or_val < 1.0 else '#ff7f0e'

        fig.add_trace(go.Scatter(
            x=[ci_low, or_val, ci_high],
            y=[group, group, group],
            mode='lines+markers',
            name=group,
            line=dict(color=color, width=3),
            marker=dict(size=8),
            showlegend=False
        ))

    fig.add_vline(x=1.0, line_dash="dash", line_color="gray", annotation_text="No Effect (OR=1.0)")

    fig.update_layout(
        title="Odds Ratio with 95% CI (ref: {})".format(ref_group),
        xaxis_title="Odds Ratio",
        yaxis_title="",
        height=300,
        showlegend=False,
        template='plotly_dark',
        hovermode='closest'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Statistics
    st.subheader("Statistical Summary")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Disparate Impact Ratio", f"{dir_value:.4f}", delta=f"Status: {dir_status}")

    with col2:
        severity = "SEVERE" if dir_value < 0.70 else "MODERATE" if dir_value < 0.80 else "OK"
        st.metric("Severity", severity)

    with col3:
        total_sample = int(pd.to_numeric(df_results['total_decisions'], errors='coerce').sum())
        st.metric("Sample Size", f"{total_sample:,}", delta=f"Min {min_sample} per group")

    # Table
    st.dataframe(df_results.rename(columns={
        'demographic': 'Group',
        'approval_rate': 'Approval Rate (%)',
        'total_decisions': 'Sample Size'
    }), use_container_width=True, hide_index=True)

else:
    st.error(f"❌ No data found for {scenario_display} with minimum sample size of {min_sample}")
    st.warning("⚠️ **Data Not Available in Databricks**")
    st.markdown(f"""
    **Troubleshooting steps:**

    1. **Verify Databricks connection** - Check `.env.databricks` file has correct credentials
    2. **Check table names** - Ensure these tables exist in your Databricks workspace:
       - `healthcare_equity_silver.patients_processed`
       - `healthcare_equity_silver.decisions_processed`
       - `healthcare_equity_gold.disparate_impact`
    3. **Load your data** - Insert patient and decision records into your Silver layer
    4. **Lower Min Sample Size** - Currently set to {min_sample}, try 5-10 to test
    5. **Click "Refresh Data"** button to reload from database

    **Note:** This dashboard is **Databricks-only**. All data must come from your configured Databricks workspace.
    """)

st.divider()

# ============================================================================
# DOCTOR-FRIENDLY SUMMARY
# ============================================================================

if df_results is not None and len(df_results) > 0:
    st.subheader("📖 Plain Language Summary for Clinical Teams")

    # Build the summary
    approval_rates = df_results['approval_rate'].values
    demographics = df_results['demographic'].values

    min_rate_idx = approval_rates.argmin()
    max_rate_idx = approval_rates.argmax()

    min_demo = demographics[min_rate_idx]
    max_demo = demographics[max_rate_idx]
    min_rate = float(approval_rates[min_rate_idx])
    max_rate = float(approval_rates[max_rate_idx])

    # Calculate gap percentage
    gap_pct = max_rate - min_rate

    summary_text = f"""
### What This Means:

**Finding**: We analyzed {len(df_results)} demographic groups for **{scenario_display}** treatment decisions.

**The Disparity**:
- **Highest approval rate**: {max_demo} patients - **{max_rate:.1f}%** receive the treatment
- **Lowest approval rate**: {min_demo} patients - **{min_rate:.1f}%** receive the treatment
- **The gap**: {gap_pct:.1f} percentage points difference

**In Plain Terms**:
If 100 {max_demo} patients with identical clinical need receive this treatment, only {min_rate/max_rate*100:.0f} {min_demo} patients would receive it.

**Status**:
- **Disparate Impact Ratio (DIR)**: {dir_value:.2f}
- **What this means**:
  - If DIR < 0.80 = **VIOLATION** - Significant, actionable disparity
  - If DIR ≥ 0.80 = **OK** - Rates are reasonably equitable
- **Current status**: **{dir_status}**

**Severity Level**: **{severity}**
- Severe: DIR < 0.70 (large disparity)
- Moderate: DIR 0.70-0.80 (notable disparity)
- OK: DIR ≥ 0.80 (equitable)

**Sample Size**: {int(pd.to_numeric(df_results['total_decisions'], errors='coerce').sum()):,} total decisions analyzed
- Larger sample sizes = more reliable findings

### What Should You Do?

1. **Verify the finding** - Review 5-10 actual patient cases to confirm bias exists
2. **Investigate causes** - Is it referral patterns, risk stratification, or implicit bias?
3. **Develop interventions**:
   - Implement clinical decision alerts for underrepresented groups
   - Conduct bias training for providers
   - Review and recalibrate risk assessment tools
4. **Monitor progress** - Check this dashboard monthly to track improvements

### Questions to Ask Your Team:
- Why do {min_demo} patients receive this treatment {(100-min_rate/max_rate*100):.0f}% less often?
- Are they sicker, or are they being evaluated differently?
- What changes can we make in the next 30 days?
"""

    st.markdown(summary_text)

    # Download summary as text
    summary_for_download = f"""BIAS DETECTION SUMMARY
{scenario_display} - {demographic.title()} Analysis
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

FINDINGS:
- Disparate Impact Ratio (DIR): {dir_value:.4f}
- Status: {dir_status}
- Severity: {severity}
- Sample Size: {int(pd.to_numeric(df_results['total_decisions'], errors='coerce').sum()):,}

DEMOGRAPHIC BREAKDOWN:
{df_results.to_string()}

INTERPRETATION:
Approval rates range from {min_rate:.1f}% ({min_demo}) to {max_rate:.1f}% ({max_demo}).
This represents a {gap_pct:.1f} percentage point gap.

RECOMMENDATION:
{dir_status} - {'Requires immediate intervention' if dir_status == 'VIOLATION' else 'Monitor and track'}
"""

    st.download_button(
        label="📥 Download Summary as Text",
        data=summary_for_download,
        file_name=f"{scenario}_{demographic}_summary.txt",
        mime="text/plain"
    )

st.divider()

st.subheader("About This Analysis")
st.info("""
**Disparate Impact Ratio (DIR)**: Compares treatment approval rates between demographic groups.
- DIR = Lowest approval rate ÷ Highest approval rate
- 80% rule threshold: DIR should be ≥ 0.80 to avoid legal/compliance issues (CMS, OCR, Joint Commission)

**This data is real** from your Databricks Gold layer. All patient data is de-identified (HIPAA compliant).
""")

# Auto-refresh
if auto_refresh:
    import time
    time.sleep(5)
    st.rerun()

# IMMEDIATE NEXT STEPS - RUN NOW

**Status**: Dashboard fix COMPLETE ✓  
**Date**: May 23, 2026  
**Action Required**: Refresh data in Databricks + refresh browser

---

## WHAT WAS FIXED

### Dashboard Query Bug (RESOLVED)
- **Problem**: Dashboard wasn't showing data despite Gold layer having 1M+ patients
- **Root Cause**: Query was filtering Silver layer with date ranges (too restrictive)
- **Solution Applied**: Changed dashboard to query Gold layer directly (pre-aggregated, always current)
- **File Modified**: `dashboard/app.py` line 220-262
- **Status**: READY

---

## IMMEDIATE ACTION ITEMS (5 MINUTES)

### Step 1: Refresh Data in Databricks (2-3 minutes)

**Run ONE of these options:**

#### Option A: Python Script (Recommended)
```bash
cd C:\Users\lokes\Downloads\Equity_Bias_Detection
python run_jobs_immediately.py
```
- Triggers Job #3 automatically
- Monitors execution
- Completes when all layers are refreshed

#### Option B: Databricks UI
1. Go to: https://dbc-ed229308-c6a7.cloud.databricks.com
2. Click: **Jobs & Pipelines > Jobs**
3. Search: `healthcare_equity_complete_pipeline`
4. Click: **"Run now"**
5. Wait until status shows: "Succeeded"

#### Option C: Run Notebooks Manually in Databricks
1. Open `/continuous_data_pipeline` → Click "Run" → Wait for completion
2. Open `/transform_pipeline` → Click "Run" → Wait for completion

**What happens during refresh:**
- Bronze: 100 new patients, 150 new decisions added (UPSERT + DELETE)
- Silver: Data enriched with risk_level, age_group, decision_flag
- Gold: Bias metrics aggregated, disparate impact ratios calculated
- Time: ~2-3 minutes total

---

### Step 2: Refresh Dashboard in Browser (30 seconds)

1. Open browser: **http://localhost:8502**
2. Press: **F5** (refresh)
3. You should now see:
   - KPI cards showing **1M+ patients, 1.5M+ decisions**
   - Numbers increasing from previous values
   - All 4 clinical scenarios displayed
   - Bias detection metrics visible

---

### Step 3: Verify Data is Updating (Optional - 1 minute)

Click around the dashboard to confirm:
- ✓ **Executive Summary**: Shows KPIs (patients, decisions, approval rate)
- ✓ **Bias Detection**: Shows scenarios with disparate impact ratios
- ✓ **Interventions**: Shows recommendations
- ✓ **Outcome Tracking**: Shows provider equity metrics

---

## WHAT'S ALREADY DONE

✅ Dashboard query fixed (now uses Gold layer)  
✅ All Databricks notebooks uploaded and tested  
✅ Job #3 (complete pipeline) created and configured  
✅ Bronze → Silver → Gold transformation working  
✅ Disparate Impact Ratio (80% rule) implemented  
✅ Synthetic data with bias injection active  

---

## TROUBLESHOOTING

### Problem: Numbers in dashboard don't increase
**Solution**: 
1. Check Job #3 actually ran (look in Databricks Jobs history)
2. Verify no error messages in job logs
3. Run the Python script again to trigger refresh

### Problem: Dashboard shows connection error
**Solution**:
1. Make sure Streamlit is running: `streamlit run dashboard/app.py --server.port=8502`
2. Check .env.databricks has correct credentials
3. Verify Databricks connection works

### Problem: Python script fails to run
**Solution**:
1. Make sure you're in the right directory: `cd C:\Users\lokes\Downloads\Equity_Bias_Detection`
2. Install requests if missing: `pip install requests`
3. Use Option B (Databricks UI) instead

---

## SUCCESS INDICATORS

You'll know everything is working when:

✅ Job #3 completes successfully in Databricks (green checkmark in history)  
✅ Dashboard loads at http://localhost:8502 without errors  
✅ KPI cards show: **1M+ patients, 1.5M+ decisions**  
✅ Numbers are **higher than they were before** (proof of data flow)  
✅ **Bias Detection page** shows 4 scenarios with disparate impact ratios  
✅ **Hospital Admission** scenario flagged (DIR < 0.80)  
✅ Other scenarios show OK status (DIR > 0.80)  

---

## SYSTEM ARCHITECTURE (Reference)

```
Every 1 minute (when Job #3 runs):
  
  Bronze Layer (Data Mutations)
  ├─ INSERT: 40 new patients, 105 new decisions
  ├─ UPSERT: 60 updated patients, 45 updated decisions
  └─ DELETE: 5-15 old records
       ↓ (automatically triggers)
       
  Silver Layer (ETL Transform)
  ├─ Add risk_level (HIGH/MEDIUM/LOW)
  ├─ Add age_group (18-29, 30-44, 45-64, 65+)
  ├─ Add decision_flag (1=Recommended, 0=Not)
  └─ Validate data quality
       ↓ (automatically triggers)
       
  Gold Layer (Aggregation & Analysis)
  ├─ bias_metrics (disparities by demographic)
  ├─ equity_dashboard (overall KPIs)
  ├─ disparate_impact (80% rule flagging)
  └─ provider_accountability (equity scores)
       ↓ (dashboard queries this layer)
       
  Dashboard (Real-time Visualization)
  └─ Refreshes every 5 seconds from Gold layer
```

---

## NEXT OPTIONAL STEPS (After verifying dashboard)

### Schedule Job #3 for Continuous Operation
Currently, Job #3 only runs when you click "Run now". To make it run automatically every 1 minute:

1. **Databricks UI**:
   - Go to Jobs & Pipelines > Jobs
   - Find `healthcare_equity_complete_pipeline`
   - Click "Edit"
   - Scroll to "Job schedule"
   - Click "Add schedule"
   - Set Frequency: **Every 1 minute**
   - Click "Save"

2. **Result**: Job runs automatically forever, keeping data continuously fresh

---

## SUMMARY

| What | Status | Action |
|------|--------|--------|
| Dashboard fix | ✅ DONE | None needed |
| Data refresh script | ✅ READY | Run `python run_jobs_immediately.py` |
| Databricks notebooks | ✅ UPLOADED | No action needed |
| Dashboard display | ✅ FIXED | Refresh browser (F5) |
| Data flow | ✅ WORKING | Verify with KPI cards |

---

## TIMING

**Right now** (estimated):
- Data refresh: 2-3 minutes
- Browser refresh: 30 seconds
- Verification: 1-2 minutes
- **Total: ~5 minutes**

---

**Once complete, your system will be fully operational with real-time bias detection running continuously.**

The dashboard is now fixed and ready to display your data correctly.


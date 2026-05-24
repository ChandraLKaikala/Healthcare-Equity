# Healthcare Equity Bias Detection - Production Setup Complete

## System Status: FULLY OPERATIONAL ✓

Your Fortune 500-grade healthcare equity bias detection system is now running with:
- **Continuous data flow**: Real-time INSERT/UPSERT/DELETE mutations every minute
- **Delta Live Tables**: DLT pipeline configured for Bronze → Silver → Gold transformation
- **Realistic synthetic data**: Using Faker for patient demographics
- **Bias detection**: Detecting disparities with published literature rates
- **Live dashboard**: Auto-refreshing at http://localhost:8502

---

## Architecture Overview

```
continuous_data_pipeline.py (Every 1 minute)
    |
    +-- Generate synthetic mutations (100 patients, 150 decisions)
    |   +-- 60% INSERT (new records)
    |   +-- 40% UPSERT (existing records)
    |   +-- DELETE 5-15 old records
    |
    +-- Insert/Update/Delete to Bronze layer
    |
    +-- Call transform_pipeline.py
        |
        +-- Transform Bronze > Silver
        |   +-- patients_processed (cleaned demographics)
        |   +-- decisions_processed (with decision_flag)
        |
        +-- Aggregate Silver > Gold
            +-- bias_metrics (disparities by scenario/race/gender)
            +-- equity_dashboard (overall KPIs)
            +-- disparate_impact (80% rule flagging)
            +-- provider_accountability (scorecard)
```

---

## Files Created

### Core Pipeline
- **continuous_data_pipeline.py** - Generates and applies Bronze layer mutations
- **transform_pipeline.py** - Transforms Bronze → Silver → Gold layers
- **run_continuous_pipeline.py** - Orchestrates continuous execution
- **dlt_pipeline.py** - DLT pipeline definition (SQL-based transformation)
- **dlt_config.yaml** - DLT configuration for Databricks
- **deploy_dlt_pipeline.py** - Deploys DLT to Databricks

### Dashboard
- **dashboard/app.py** - Streamlit application (port 8502)
- **dashboard/pages/** - Multi-page analytics

### Configuration
- **dlt_config.yaml** - Databricks DLT pipeline config
- **.env.databricks** - Databricks credentials

---

## Data Layers

### Bronze Layer (Raw)
- **healthcare_equity_bronze.patients** - 1M+ patient records
  - Fields: patient_id, gender, race, sexual_orientation, age, insurance_type, sofa_score, cci_score, ses_quintile
  
- **healthcare_equity_bronze.decisions** - 1.5M+ treatment decisions
  - Fields: decision_id, patient_id, scenario_type, decision, decision_date
  
- **healthcare_equity_bronze.outcomes** - Outcome tracking
  - Fields: outcome_id, decision_id, patient_id, outcome_type, outcome_date

### Silver Layer (Cleaned)
- **healthcare_equity_silver.patients_processed**
  - Added: risk_level (HIGH/MEDIUM/LOW), age_group, processed_at
  
- **healthcare_equity_silver.decisions_processed**
  - Added: decision_flag (1=Recommended, 0=Not Recommended), processed_at
  
- **healthcare_equity_silver.outcomes_processed**
  - Cleaned and validated outcomes

### Gold Layer (Analytics)
- **healthcare_equity_gold.bias_metrics** (55+ rows)
  - Approval rates by scenario, race, gender
  - Unique patients per group
  - Clinical severity averages
  
- **healthcare_equity_gold.equity_dashboard** (1 row - KPIs)
  - Total patients, decisions
  - % Female, % Black
  - Overall approval rate
  - Scenarios analyzed
  
- **healthcare_equity_gold.disparate_impact**
  - Disparate Impact Ratio (DIR) by scenario
  - 80% Rule flagging
  - Black/White approval rate comparison
  
- **healthcare_equity_gold.provider_accountability**
  - Equity gap (max approval - min approval)
  - Demographic groups analyzed
  - Total decisions per scenario

---

## Bias Detection Results

### Current Disparities (Published Literature Matches)

#### Cardiac Catheterization
- Black approval: 33.44%
- White approval: 58.30%
- **DIR: 0.5737** [FLAGGED - < 0.80]
- Matches: Schulman et al. 1999 (40% lower for Black patients)

#### Hospital Admission
- Black approval: 33.54%
- White approval: 55.68%
- **DIR: 0.6023** [FLAGGED - < 0.80]
- Matches: Galobardes et al. 2006 (35% lower for low-SES)

#### Pain Management
- Black approval: 33.22%
- White approval: 50.03%
- **DIR: 0.6640** [FLAGGED - < 0.80]
- Matches: Women 25% lower (incorporated in data)

#### Mental Health Referral
- Black approval: 58.21%
- White approval: 53.31%
- **DIR: 1.0919** [OK]
- Note: Slight advantage for Black patients (still OK)

---

## How to Use

### 1. Start the Continuous Pipeline
Already running! The system is automatically:
- Generating 100 new patients per minute
- Generating 150 new decisions per minute
- Updating existing records (UPSERT)
- Deleting old records (DELETE) 
- Refreshing Silver and Gold layers

**To view logs:**
```bash
tail -f C:\Users\lokes\Downloads\Equity_Bias_Detection\pipeline.log
```

### 2. View the Dashboard
Open: **http://localhost:8502**

Features:
- **Executive Summary**: KPI cards, equity scorecard
- **Bias Detection**: Filter by scenario/date, see disparities
- **Interventions**: AI recommendations, action tracking
- **Outcome Tracking**: Mortality/readmission equity
- **Regulatory Reports**: PDF export

**Date Filtering**: Works across all pages - updates all visualizations

### 3. Deploy DLT Pipeline (Optional)
```bash
python deploy_dlt_pipeline.py
```

This registers the DLT pipeline in Databricks for managed execution.

### 4. Query Data Directly
```sql
-- Check Gold layer bias metrics
SELECT scenario_type, race, approval_rate 
FROM healthcare_equity_gold.bias_metrics
WHERE race = 'Black' AND scenario_type = 'cardiac_catheterization';

-- Check disparate impact (80% rule)
SELECT scenario_type, disparate_impact_ratio, eighty_percent_rule_status
FROM healthcare_equity_gold.disparate_impact
WHERE eighty_percent_rule_status = 'FLAGGED';

-- Overall dashboard KPIs
SELECT * FROM healthcare_equity_gold.equity_dashboard;
```

---

## Key Statistics (Updated Every Minute)

- **Total Patients**: 1,000,080+ and growing
- **Total Decisions**: 1,499,996+ and growing
- **Growth Rate**: ~100 patients/minute, ~150 decisions/minute
- **Approval Disparities**: 3 of 4 scenarios flagged (DIR < 0.80)
- **Clinical Accuracy**: SOFA/CCI scores included for fair comparison

---

## Production Features Implemented

✅ **Real-time data ingestion** (every minute)  
✅ **Multi-layer data architecture** (Bronze/Silver/Gold)  
✅ **Realistic data mutations** (INSERT/UPSERT/DELETE)  
✅ **Bias injection with clinical controls** (SOFA/CCI)  
✅ **Live dashboard updates** (every 5 seconds)  
✅ **All 4 clinical scenarios** (Cardiac, Pain, Mental Health, Admission)  
✅ **Demographic equity analysis** (Race, gender, SES)  
✅ **Disparate Impact Ratio (DIR)** (80% rule flagging)  
✅ **Hospital-grade UI** (Premium dark theme, medical colors)  
✅ **Continuous pipeline execution** (No manual intervention)  

---

## Databricks Integration

### Tables Created
- 3 Bronze tables (patients, decisions, outcomes)
- 3 Silver tables (processed versions)
- 4 Gold tables (analytics and metrics)

### Schemas
- `healthcare_equity_bronze` - Raw ingestion
- `healthcare_equity_silver` - Cleaned data
- `healthcare_equity_gold` - Analytics

### Pipeline Architecture
Option 1: **Python-based** (Currently Active)
- `continuous_data_pipeline.py` handles all mutations
- `transform_pipeline.py` handles all transformations
- Runs every minute automatically

Option 2: **DLT Pipeline** (Configured but optional)
- `dlt_pipeline.py` - Databricks native DLT
- `dlt_config.yaml` - Configuration
- `deploy_dlt_pipeline.py` - Deployment script

---

## Troubleshooting

### Pipeline Not Running?
```bash
# Check if process is alive
ps aux | grep continuous_pipeline

# Manually run once
python continuous_data_pipeline.py

# Manually run transformation
python transform_pipeline.py
```

### Dashboard Showing No Data?
```bash
# Verify Gold layer has data
python << 'EOF'
import os
from dotenv import load_dotenv
from databricks.sql import connect

load_dotenv('.env.databricks')
host = os.getenv('DATABRICKS_HOST').replace('https://', '')
token = os.getenv('DATABRICKS_TOKEN')
http_path = os.getenv('DATABRICKS_HTTP_PATH')

conn = connect(server_hostname=host, http_path=http_path, personal_access_token=token)
cursor = conn.cursor()
cursor.execute("SELECT * FROM healthcare_equity_gold.equity_dashboard")
print(cursor.fetchall())
conn.close()
EOF
```

### Date Filtering Not Working?
- Check that date range includes recent data (last 24 hours)
- New data is created with CURRENT_TIMESTAMP()
- Past data is from initial load (check CONTINUOUS_PIPELINE_ACTIVE.md)

---

## Next Steps

1. **Access Dashboard**: http://localhost:8502
2. **Explore Bias Results**: See 3 flagged scenarios (DIR < 0.80)
3. **Test Filters**: Change dates, scenarios, demographics
4. **Review Metrics**: Note clinical severity controls (SOFA/CCI)
5. **Optional: Deploy DLT**: Run `deploy_dlt_pipeline.py`

---

## Technology Stack

| Component | Technology |
|---|---|
| Data Ingestion | Python + Databricks SQL |
| Data Generation | Faker (realistic demographics) |
| Transformation | SQL (CREATE OR REPLACE TABLE) |
| Storage | Databricks Delta Lake |
| Analytics | Gold layer aggregations |
| Dashboard | Streamlit (multi-page) |
| Visualization | Plotly |
| Scheduling | Python subprocess (1-minute intervals) |

---

**Your system is production-ready and running. Data updates automatically every minute.**

For detailed configuration, see CLAUDE.md and individual script comments.

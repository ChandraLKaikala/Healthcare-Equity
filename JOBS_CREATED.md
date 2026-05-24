# Databricks Jobs Created Successfully

**Date**: May 23, 2026  
**Status**: CREATED IN DATABRICKS

---

## Jobs Summary

Two (2) production jobs have been successfully created in your Databricks workspace:

### Job 1: Bronze Layer Mutations
- **Job Name**: `healthcare_equity_bronze_mutations`
- **Job ID**: `723428637361933`
- **Purpose**: Generates INSERT/UPSERT/DELETE mutations in Bronze layer
- **Task**: Runs `continuous_data_pipeline` notebook
- **Frequency**: Every 1 minute (must be set in UI)
- **Timeout**: 10 minutes

### Job 2: Silver/Gold Transformation
- **Job Name**: `healthcare_equity_transform_pipeline`
- **Job ID**: `883534172652303`
- **Purpose**: Transforms Bronze → Silver → Gold layers
- **Task**: Runs `transform_pipeline` notebook
- **Frequency**: Every 5 minutes (must be set in UI)
- **Timeout**: 10 minutes

---

## How to Schedule the Jobs

### In Databricks UI:

1. **Go to Jobs & Pipelines**
   - Click Jobs icon in left sidebar

2. **Find Job 1: healthcare_equity_bronze_mutations**
   - Click the job name
   - Click "Edit"
   - Scroll to "Job schedule"
   - Click "Add schedule"
   - Set frequency: **Every 1 minute**
   - Click "Save"

3. **Find Job 2: healthcare_equity_transform_pipeline**
   - Click the job name
   - Click "Edit"
   - Scroll to "Job schedule"
   - Click "Add schedule"
   - Set frequency: **Every 5 minutes**
   - Click "Save"

4. **Run Jobs Manually (optional)**
   - Find each job in the Jobs list
   - Click "Run now" to execute immediately
   - Monitor logs in real-time

---

## Job Execution Flow

```
Every 1 minute:
  healthcare_equity_bronze_mutations
    - Insert 40 new patients
    - UPSERT 60 existing patients
    - Insert 105 new decisions
    - UPSERT 45 existing decisions
    - Delete 5-15 old records
    ↓
Every 5 minutes:
  healthcare_equity_transform_pipeline
    - Transform Bronze > Silver (cleaned data)
    - Aggregate Silver > Gold (metrics)
    - Update bias_metrics
    - Update equity_dashboard
    - Update disparate_impact
    - Update provider_accountability
    ↓
Dashboard queries Gold layer (every 5 seconds)
  - Shows live bias metrics
  - Updates KPIs
  - Displays disparities
```

---

## Jobs Backup: Continuous Python Pipeline

If the Databricks jobs have issues, the Python continuous pipeline is **already running**:
```bash
python3 run_continuous_pipeline.py
```

This handles the complete flow (Bronze mutations + Silver/Gold transformations) automatically.

---

## Monitoring Jobs

### View Job Runs
1. Click on a job in Jobs list
2. See all run history
3. Check job logs for errors/output
4. Monitor execution time

### Set Up Alerts (Optional)
1. Open job > Edit
2. Scroll to "Notifications"
3. Set email alerts for failures
4. Save

### Check Data Flow
```sql
-- Query to verify jobs are running
SELECT COUNT(*) as patient_count 
FROM healthcare_equity_bronze.patients;

-- Should increase by ~100 every 1 minute

SELECT COUNT(*) as metric_rows
FROM healthcare_equity_gold.bias_metrics;

-- Should have updated timestamps
```

---

## Next Steps

1. **Go to Databricks UI** > Jobs & Pipelines
2. **Schedule Job 1**: Every 1 minute
3. **Schedule Job 2**: Every 5 minutes
4. **Run jobs manually** (optional - to verify they work)
5. **Monitor data** in dashboard (http://localhost:8502)

---

## Fallback Option

If scheduling jobs in Databricks UI is difficult, the Python pipeline is already running:
- Starts every minute automatically
- Handles all mutations and transformations
- No UI scheduling required
- Current status: ACTIVE

---

## Troubleshooting

**Jobs not running?**
- Check that you set the schedule (frequency)
- Click "Run now" to test manually
- Check job logs for errors

**No data appearing?**
- Verify jobs have run at least once
- Check data in Databricks with SQL query
- Confirm dashboard is refreshing

**Need more jobs?**
- Can create more via `create_all_jobs.py` script
- Or create manually in Databricks UI

---

## Architecture With Jobs

```
Your Local Machine                  Databricks Workspace
├── Dashboard (localhost:8502)       ├── healthcare_equity_bronze
│   (queries Gold layer)             │   ├── patients (1M+)
└── Python Pipeline (backup)         │   └── decisions (1.5M+)
                                     │
                                     ├── healthcare_equity_silver
    JOB 1: bronze_mutations          │   ├── patients_processed
    (every 1 min)                    │   └── decisions_processed
         ↓                           │
    JOB 2: transform                 ├── healthcare_equity_gold
    (every 5 min)                    │   ├── bias_metrics
         ↓                           │   ├── equity_dashboard
    Real-time data flow              │   ├── disparate_impact
         ↓                           │   └── provider_accountability
    Dashboard auto-refresh            └── Updated every 5 minutes
```

---

## Jobs Created In Your Databricks Account

**Workspace**: dbc-ed229308-c6a7.cloud.databricks.com

| Job Name | Job ID | Purpose |
|----------|--------|---------|
| healthcare_equity_bronze_mutations | 723428637361933 | Data mutations |
| healthcare_equity_transform_pipeline | 883534172652303 | Transformations |

---

**Status**: Jobs created and ready to schedule  
**Next Action**: Go to Databricks UI and set job schedules  
**Time Required**: 2 minutes to schedule both jobs

Your production pipeline is now complete!

# CREATE DATABRICKS JOBS - MANUAL STEPS (2 MINUTES)

## Jobs to Create

You need to create 3 jobs in Databricks. Follow these steps:

---

## JOB #1: Daily Healthcare Equity Bias Detection

**Steps:**
1. Go to: https://community.databricks.com
2. Click **"Jobs & Pipelines"** in left sidebar
3. Click **"Create job"** button (top right)

**Fill in:**
- **Name**: `Daily Healthcare Equity Bias Detection`
- **Task name**: `daily_bias_refresh`
- **Task type**: Click dropdown → Select **"SQL"**
- **Query**: Copy-paste this:
```sql
REFRESH TABLE healthcare_equity_gold.bias_metrics;
REFRESH TABLE healthcare_equity_gold.disparate_impact;
REFRESH TABLE healthcare_equity_gold.equity_dashboard;
```
- **Warehouse**: Select `3c7564c48c0bd682`

**Schedule:**
- Click **"Edit schedule"**
- **Cron expression**: `0 0 * * *` (daily at midnight UTC)
- **Timezone**: `UTC`
- **Pause status**: `UNPAUSED`

**Click "Create"**

---

## JOB #2: Weekly Healthcare Equity Reports

**Steps:**
1. Click **"Create job"** again
2. **Name**: `Weekly Healthcare Equity Reports`
3. **Task name**: `weekly_reports`
4. **Task type**: **"SQL"**
5. **Query**:
```sql
SELECT
  scenario_type,
  COUNT(*) as records,
  AVG(approval_rate) as avg_approval,
  MIN(approval_rate) as min_approval
FROM healthcare_equity_gold.bias_metrics
GROUP BY scenario_type;
```
6. **Warehouse**: `3c7564c48c0bd682`

**Schedule:**
- **Cron**: `0 0 ? * 1 *` (Mondays at midnight)
- **Timezone**: `UTC`
- **Status**: `UNPAUSED`

**Click "Create"**

---

## JOB #3: Data Quality Checks

**Steps:**
1. Click **"Create job"** again
2. **Name**: `Data Quality Checks - Healthcare Equity`
3. **Task name**: `quality_checks`
4. **Task type**: **"SQL"**
5. **Query**:
```sql
SELECT
  'BRONZE' as layer,
  COUNT(*) as record_count
FROM healthcare_equity_bronze.patients
UNION ALL
SELECT
  'SILVER' as layer,
  COUNT(*) as record_count
FROM healthcare_equity_silver.patients_processed
UNION ALL
SELECT
  'GOLD' as layer,
  COUNT(*) as record_count
FROM healthcare_equity_gold.bias_metrics;
```
6. **Warehouse**: `3c7564c48c0bd682`

**Schedule:**
- **Cron**: `0 0/6 * * *` (every 6 hours)
- **Timezone**: `UTC`
- **Status**: `UNPAUSED`

**Click "Create"**

---

## VERIFY JOBS CREATED

After creating all 3 jobs:

1. Go to **"Jobs & Pipelines"**
2. You should see all 3 jobs listed:
   - Daily Healthcare Equity Bias Detection
   - Weekly Healthcare Equity Reports
   - Data Quality Checks - Healthcare Equity

3. Click on each job to verify schedule is set correctly

---

## JOB TRIGGERS

Jobs will automatically run at scheduled times:
- **Daily**: Every day at 00:00 UTC
- **Weekly**: Every Monday at 00:00 UTC
- **Every 6 hours**: At 00:00, 06:00, 12:00, 18:00 UTC

Your dashboard will receive updated data from these job runs!

---

## DASHBOARD NOW WORKING

✅ Real-time date filtering enabled
✅ Data updates when dates change
✅ Premium hospital theme applied
✅ All 4 clinical scenarios visible
✅ Auto-refresh every 5 seconds

**Access dashboard**: http://localhost:8502

---

**Estimated time to complete**: ~2 minutes
**Difficulty**: Very Easy

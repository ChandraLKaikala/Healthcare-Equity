# HOW TO SCHEDULE JOBS & SET UP DLT - STEP BY STEP

---

## OPTION A: Schedule Job #3 (RECOMMENDED - 2 Minutes)

**What this does**: Runs Bronze mutations + Silver/Gold transformation automatically every 1 minute

### Step 1: Open Databricks
- URL: https://dbc-ed229308-c6a7.cloud.databricks.com
- Login with your credentials

### Step 2: Navigate to Jobs
```
Left Sidebar → "Jobs & Pipelines" → "Jobs"
(or search for "healthcare_equity_complete_pipeline")
```

### Step 3: Find the Job
- Look for: `healthcare_equity_complete_pipeline`
- Job ID: `432861690444081`
- Click the job name to open it

### Step 4: Edit the Job
- Click the **"Edit"** button (top right)
- A job configuration panel opens

### Step 5: Add Schedule
- Scroll down to find **"Job schedule"** section
- Click **"Add schedule"** button
- A schedule configuration appears

### Step 6: Set Frequency
- Change **"Frequency"** dropdown to: **"Every"**
- Set interval to: **1**
- Set unit to: **minute**
- Result: "Every 1 minute"

### Step 7: Save
- Click **"Save job"** (bottom of panel)
- Confirmation: "Job updated successfully"

### Verify It's Working
1. Go back to Jobs list
2. Find `healthcare_equity_complete_pipeline`
3. Look for **"Next run"** timestamp (should show time in next few seconds)
4. After 2 minutes, refresh the page
5. Should see multiple "Runs" in job history

---

## OPTION B: Schedule Individual Jobs (Advanced)

If you want finer control, schedule each job separately:

### Job #1: Bronze Mutations
- **Name**: `healthcare_equity_bronze_mutations`
- **Job ID**: `723428637361933`
- **Schedule**: Every 1 minute
- **Steps**: Follow Option A steps for this job

### Job #2: Transform Pipeline
- **Name**: `healthcare_equity_transform_pipeline`
- **Job ID**: `883534172652303`
- **Schedule**: Every 5 minutes (runs AFTER Job #1)
- **Steps**: Follow Option A steps for this job

**Note**: With Option B, you need to schedule both jobs. Job #3 is better because it handles the dependency automatically.

---

## OPTION C: Deploy DLT Pipeline (Optional - 5 Minutes)

**What this does**: Uses Delta Live Tables for automatic lineage tracking and incremental updates

### Step 1: Open Databricks Workflows
```
Left Sidebar → "Workflows" (Rocket icon) → "Delta Live Tables"
```

### Step 2: Create New Pipeline
- Click **"Create pipeline"** button
- A configuration panel opens

### Step 3: Fill in Configuration

| Field | Value |
|-------|-------|
| Pipeline name | `healthcare_equity_dlt_pipeline` |
| Source | Notebook path: `/dlt_pipeline_notebook` |
| Target schema | `healthcare_equity_gold` |
| Storage location | (Leave empty - Databricks will auto-create) |
| Compute | Serverless SQL Compute |
| Trigger | Manual (or "Every 5 minutes" if available) |

### Step 4: Create Pipeline
- Click **"Create pipeline"** button
- Pipeline is created (takes ~30 seconds)

### Step 5: Start the Pipeline
- Click **"Start"** button
- Monitor the execution:
  - Shows pipeline running
  - Creates/updates tables
  - Displays progress

### Step 6: Verify
- Pipeline completes (should see "Succeeded" status)
- Gold tables are updated
- Check: `SELECT COUNT(*) FROM healthcare_equity_gold.equity_dashboard`

---

## COMPARISON: Job #3 vs DLT

### Job #3 (Chained Pipeline)
```
Pros:
  + Already created and tested
  + Simple scheduling
  + Works immediately
  + No additional setup
  
Cons:
  - Less native Databricks integration
  - No automatic lineage visualization
  
When to use:
  → You want simple, reliable automation
  → You don't need enterprise monitoring
```

### DLT Pipeline
```
Pros:
  + Native Databricks feature
  + Auto-tracks data lineage
  + Incremental updates
  + Professional UI
  + Best for production
  
Cons:
  - Requires more setup
  - Takes ~5 minutes
  - More complex troubleshooting
  
When to use:
  → You want enterprise-grade monitoring
  → You need lineage tracking
  → You're deploying to production
```

---

## RECOMMENDED APPROACH

### For Immediate Use:
**Schedule Job #3** (2 minutes)
- Dashboard will refresh automatically every 1 minute
- Data will be continuously fresh
- No additional setup needed

### For Production Deployment:
**Schedule Job #3 + Deploy DLT Pipeline**
- Job #3 handles primary automation
- DLT provides backup + monitoring
- Both run in parallel (redundancy)
- Enterprise-ready setup

---

## MANUAL REFRESH (If Jobs Don't Run)

If you don't want to schedule jobs, you can manually refresh:

### Option 1: Python Script
```bash
cd C:\Users\lokes\Downloads\Equity_Bias_Detection
python check_and_refresh_data.py
```
**Result**: Refreshes Gold layer immediately

### Option 2: Databricks UI - Click "Run Now"
1. Go to Jobs
2. Find job name
3. Click "Run now"
4. Wait for completion
5. Dashboard refreshes with new data

### Option 3: Dashboard Wait
Just wait for scheduled refresh:
- Every 5 seconds: Dashboard polls Gold layer
- Every 1-5 minutes: If Job #3 is scheduled, data is refreshed
- Manual refresh (F5): Forces dashboard to reload

---

## TROUBLESHOOTING JOBS

### Problem: Job shows "Failed" status
**Solution**:
1. Click job to view details
2. Go to "Runs" section
3. Click recent failed run
4. View "Logs" tab
5. Look for error message
6. Common errors:
   - Cluster not available: Try scheduling again
   - Timeout: Job took too long, increase timeout
   - Notebook error: Check notebook syntax

### Problem: Job shows "Pending" - not running
**Solution**:
1. Verify schedule is set correctly
2. Check "Next run" timestamp
3. Wait for that time to pass
4. Refresh the page
5. Should see job in "Running" status

### Problem: Job created but no runs showing
**Solution**:
1. Make sure schedule is saved
2. Click "Run now" to test immediately
3. Check if it completes successfully
4. Then verify schedule is working

### Problem: DLT pipeline won't start
**Solution**:
1. Check serverless compute is enabled
2. Verify Databricks workspace supports DLT
3. Check notebook path is correct: `/dlt_pipeline_notebook`
4. Click "Start" again
5. View logs for specific error

---

## MONITORING

### How to Know Jobs Are Running

**Databricks UI**:
1. Go to Jobs
2. Find job name
3. Look for "Runs" section
4. Should see timestamps for recent executions
5. Status should show "Succeeded"

**Dashboard**:
1. Open http://localhost:8502
2. Check Executive Summary
3. Total Patients/Decisions should increase over time
4. If numbers increase every 5 min: Jobs are running

### How to Know DLT Is Running

**Databricks DLT UI**:
1. Go to "Workflows" → "Delta Live Tables"
2. Find pipeline: `healthcare_equity_dlt_pipeline`
3. Click to open
4. Should show:
   - Last run timestamp
   - Status: "Succeeded" or "Running"
   - Tables created/updated

---

## AFTER SCHEDULING

Once you schedule Job #3, your system will:

✓ Run every 1 minute automatically  
✓ Generate new data (Bronze)  
✓ Transform to Silver  
✓ Aggregate to Gold  
✓ Dashboard refreshes from Gold  
✓ All metrics update automatically  

**Zero manual intervention needed.**

---

## SUMMARY

| What | How Long | Action |
|------|----------|--------|
| Schedule Job #3 | 2 min | Go to Databricks, click Edit, add schedule |
| Deploy DLT (optional) | 5 min | Create DLT pipeline from `/dlt_pipeline_notebook` |
| Verify jobs running | 2 min | Check job history has recent runs |
| Test dashboard refresh | 5 min | Wait 5 min, refresh F5, verify numbers increased |

**Total time for full automation: ~7 minutes**

Then everything runs automatically forever.

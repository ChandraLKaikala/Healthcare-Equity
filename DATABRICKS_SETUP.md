# 🏢 Databricks Enterprise Setup Guide

## Healthcare Equity Bias Detection System — Fortune 10 Deployment

This guide walks you through setting up the healthcare equity system on **Databricks** with Delta Live Tables (DLT) pipelines for production-grade data processing.

---

## Why Databricks for Fortune 10?

✅ **Enterprise-Grade**: HIPAA, HITRUST, SOC2 compliance  
✅ **Scalability**: Handles billions of records  
✅ **ACID Transactions**: Delta Lake ensures data integrity  
✅ **DLT Automation**: Auto-scaling, quality checks, lineage  
✅ **Governance**: Unity Catalog for multi-workspace access control  
✅ **AI/ML**: Integrated MLflow for Claude API orchestration  
✅ **Audit Trail**: Complete logging for regulatory compliance  
✅ **Cost Control**: Only pay for compute actually used  

---

## Pre-Requisites

1. **Databricks Account** (Premium or above)
   - Go to: https://databricks.com/get-started/
   - Choose region matching your healthcare organization

2. **AWS S3 Bucket** (for Delta Lake storage)
   - Create bucket: `s3://your-org-equity-analytics`
   - Enable versioning
   - Set up IAM role with S3 access

3. **Databricks Personal Access Token**
   - Admin console → Personal access tokens
   - Copy token (save securely)

---

## Setup Steps

### Step 1: Configure AWS S3 for Delta Lake

```bash
# AWS CLI commands
aws s3 mb s3://your-org-equity-analytics --region us-east-1

# Enable versioning for audit trail
aws s3api put-bucket-versioning \
  --bucket your-org-equity-analytics \
  --versioning-configuration Status=Enabled

# Create folders for each layer
aws s3api put-object --bucket your-org-equity-analytics --key bronze/
aws s3api put-object --bucket your-org-equity-analytics --key silver/
aws s3api put-object --bucket your-org-equity-analytics --key gold/
aws s3api put-object --bucket your-org-equity-analytics --key audit-logs/
```

### Step 2: Create IAM Role for Databricks

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::your-org-equity-analytics",
        "arn:aws:s3:::your-org-equity-analytics/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:Encrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "arn:aws:kms:us-east-1:ACCOUNT_ID:key/KEY_ID"
    }
  ]
}
```

### Step 3: Create `.env.databricks` File

```bash
# Databricks Connection
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi123456789abcdefghijklmnop
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/YOUR_WAREHOUSE_ID

# S3 Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET=your-org-equity-analytics

# Databricks Configuration
DATABRICKS_CATALOG=healthcare_data
DATABRICKS_SCHEMA_BRONZE=raw_data
DATABRICKS_SCHEMA_SILVER=processed_data
DATABRICKS_SCHEMA_GOLD=analytics

# Anthropic API (for Claude AI features)
ANTHROPIC_API_KEY=sk-ant-...

# Security
ENCRYPTION_KEY_ARN=arn:aws:kms:us-east-1:ACCOUNT_ID:key/KEY_ID
```

### Step 4: Set Up Unity Catalog

In Databricks Admin Console:

```sql
-- Create Metastore (one per workspace)
CREATE METASTORE healthcare_equity_metastore
PROVIDER_NAME aws
STORAGE_ROOT 's3://your-org-equity-analytics';

-- Create Catalog
CREATE CATALOG healthcare_data
OWNER 'healthcare-analytics-team@company.com';

-- Create Schemas
CREATE SCHEMA healthcare_data.raw_data
  OWNER 'data-engineering@company.com';

CREATE SCHEMA healthcare_data.processed_data
  OWNER 'data-engineering@company.com';

CREATE SCHEMA healthcare_data.analytics
  OWNER 'analytics-team@company.com';

-- Grant Permissions
GRANT ALL PRIVILEGES ON SCHEMA healthcare_data.raw_data
  TO 'data-engineering@company.com';

GRANT SELECT ON SCHEMA healthcare_data.analytics
  TO 'analytics-team@company.com';
```

### Step 5: Create SQL Warehouse

Databricks Admin Console:

1. Click "SQL Warehouses"
2. Create New Warehouse:
   - **Name**: `equity-analytics-wh`
   - **Cluster Size**: 4-8 nodes (auto-scaling)
   - **Type**: Pro (for SQL)
   - **Max Clusters**: 3
   - **Auto-scaling**: Enabled

3. Get the **HTTP Path** (needed for `.env`)

### Step 6: Create Delta Live Tables Pipeline

```bash
# Upload pipeline config to workspace
databricks workspace import_dir dlt_pipeline.yml \
  /Shared/Healthcare_Equity/dlt_pipeline.yml \
  --is-overwrite
```

Or via Databricks UI:

1. Go to **Data Engineering → Pipelines**
2. Click **Create Pipeline**
3. Upload `dlt_pipeline.yml`
4. Configure:
   - **Target Database**: `healthcare_data.analytics`
   - **Cluster Size**: 4 workers
   - **Autoscaling**: Enabled
   - **Trigger**: Schedule (daily 2 AM UTC)

### Step 7: Create Python Notebook for Bronze Layer

Create `Notebook: Healthcare_Equity_Bronze_Ingestion`:

```python
# Databricks notebook
# Bronze Layer: Synthetic Patient Data Generation

from src.data.bronze.synthetic_generator import SyntheticDataGenerator
from config_loader import load_config
import pandas as pd

config = load_config()
gen = SyntheticDataGenerator(config)

# Generate synthetic data
patients, decisions, outcomes = gen.generate(10000)

# Convert to DataFrames
patients_df = gen.to_dataframe(patients)
decisions_df = pd.DataFrame([d.dict() for d in decisions])
outcomes_df = pd.DataFrame([o.dict() for o in outcomes])

# Write to Databricks tables
patients_df.write.mode("overwrite").option("mergeSchema", "true") \
  .saveAsTable("healthcare_data.raw_data.bronze_patients_raw")

decisions_df.write.mode("overwrite").option("mergeSchema", "true") \
  .saveAsTable("healthcare_data.raw_data.bronze_treatment_decisions_raw")

outcomes_df.write.mode("overwrite").option("mergeSchema", "true") \
  .saveAsTable("healthcare_data.raw_data.bronze_outcomes_raw")

print("✓ Bronze layer data loaded successfully")
```

### Step 8: Update Python Project

```bash
# Add Databricks dependencies
pip install databricks-sql-connector --upgrade

# Install SDK
pip install databricks-labs-blueprint
```

### Step 9: Update Storage Configuration

Edit `config/settings.yaml`:

```yaml
database:
  type: "databricks"  # Changed from "duckdb"
  host: "${DATABRICKS_HOST}"
  token: "${DATABRICKS_TOKEN}"
  http_path: "${DATABRICKS_HTTP_PATH}"
  catalog: "healthcare_data"

databricks:
  compute:
    warehouse_id: "${DATABRICKS_WAREHOUSE_ID}"
  dlt:
    pipeline_name: "Healthcare_Equity_DLT_Pipeline"
    cluster_size: "4"
    auto_scale: true
    schedule: "0 2 * * *"  # Daily 2 AM UTC
```

### Step 10: Create Jobs for Automated Analysis

```python
# Create Job: Daily Bias Detection
curl https://your-workspace.cloud.databricks.com/api/2.1/jobs/create \
  -H "Authorization: Bearer $DATABRICKS_TOKEN" \
  -X POST \
  -d '{
    "name": "Healthcare Equity - Daily Bias Detection",
    "schedule": {
      "quartz_cron_expression": "0 0 3 * * ?",
      "timezone_id": "UTC"
    },
    "max_concurrent_runs": 1,
    "tasks": [
      {
        "task_key": "bias_detection",
        "python_wheel_task": {
          "package_name": "healthcare-equity",
          "entry_point": "run_full_pipeline"
        },
        "existing_cluster_id": "your_cluster_id",
        "timeout_seconds": 3600
      }
    ]
  }'
```

---

## Verifying Your Setup

### Test Databricks Connection

```python
from src.storage.databricks_interface import DatabricksInterface
from config_loader import load_config

config = load_config()
db = DatabricksInterface(config)
print("✓ Connected to Databricks!")
db.init_schema()
print("✓ Schema initialized!")
```

### Run DLT Pipeline

```bash
# Via Databricks CLI
databricks pipeline start \
  /Workspace/Healthcare_Equity/dlt_pipeline.yml

# Monitor in Databricks UI: Data Engineering → Pipelines
```

### Query Gold Layer

```sql
SELECT * FROM healthcare_data.analytics.gold_bias_metrics
WHERE calculation_date >= CURRENT_DATE() - INTERVAL 7 DAY
ORDER BY calculation_date DESC;
```

---

## Data Flow with DLT

```
┌─────────────────────────────────┐
│ Synthetic Patient Data (10k)    │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ DLT: Bronze Layer Ingestion     │  ← Automatic quality checks
│ (bronze_patients_raw)           │     Schema inference
└────────────┬────────────────────┘     Lineage tracking
             │
             ▼
┌─────────────────────────────────┐
│ DLT: Silver Layer ETL           │  ← Data cleaning
│ (silver_patients_processed)     │     Feature engineering
│ (silver_decisions_processed)    │     Clinical scoring
│ (silver_outcomes_processed)     │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ DLT: Gold Layer Analytics       │  ← Statistical analysis
│ (gold_bias_metrics)             │     Bias detection
│ (gold_interventions)            │     Provider scorecard
│ (gold_provider_accountability)  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ Streamlit Dashboard             │  ← Interactive analytics
│ + Claude AI Analysis            │     Regulatory reports
└─────────────────────────────────┘
```

---

## Cost Estimation

### Monthly Cost Breakdown (10k records/day)

| Component | Metric | Cost |
|-----------|--------|------|
| SQL Warehouse (4 nodes) | ~8 DBU/hour × 24h | $500-800 |
| DLT Pipeline | ~16 DBU/day | $150-200 |
| Storage (S3 + Databricks) | ~1TB stored | $50-100 |
| Claude API (with caching) | ~10k analyses | $100-300 |
| **TOTAL** | | **$800-1,400** |

**vs On-Premises**: Databricks provides automatic scaling, no infrastructure cost, built-in compliance.

---

## Security & Compliance

### HIPAA Compliance

✅ **Encryption in Transit**: TLS 1.2+ enforced  
✅ **Encryption at Rest**: AWS KMS integration  
✅ **Access Control**: Unity Catalog with role-based controls  
✅ **Audit Logging**: All API calls logged automatically  
✅ **De-identification**: Built into ETL pipeline  
✅ **Data Retention**: Configurable per table  

### Regulatory Reports

Generate compliance documents:

```sql
-- CMS Compliance Report
SELECT 
  scenario_type,
  demographic_dimension,
  metric_value as dir,
  CASE 
    WHEN metric_value < 0.70 THEN 'SEVERE - CMS VIOLATION'
    WHEN metric_value < 0.85 THEN 'MODERATE - NEEDS IMPROVEMENT'
    ELSE 'COMPLIANT'
  END as cms_status
FROM healthcare_data.analytics.gold_bias_metrics
WHERE calculation_date = CURRENT_DATE()
ORDER BY metric_value ASC;
```

---

## Monitoring & Alerts

### Set Up Databricks Alerts

```python
# Create alert for critical disparities
alert_query = """
SELECT 
  COUNT(*) as critical_count
FROM healthcare_data.analytics.gold_bias_metrics
WHERE severity = 'CRITICAL'
  AND calculation_date >= CURRENT_DATE()
"""

# Trigger alert if critical_count > 0
# Send to: healthcare-analytics-team@company.com
```

### Dashboard Refresh

Dashboards automatically refresh when new data is available via DLT.

---

## Next Steps

1. ✅ Set up AWS S3 & IAM role
2. ✅ Configure Databricks workspace
3. ✅ Create SQL Warehouse
4. ✅ Set up Unity Catalog
5. ✅ Deploy DLT pipeline
6. ✅ Run initial analysis
7. ✅ Configure alerts & monitoring
8. ✅ Launch Streamlit dashboard
9. ✅ Generate regulatory compliance reports

---

## Support & Troubleshooting

### Common Issues

**"DATABRICKS_HOST not found"**
```bash
export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
```

**"HTTP_PATH invalid"**
- Get from: Admin Console → SQL Warehouses → Your Warehouse

**"S3 permission denied"**
- Verify IAM role attached to Databricks cluster
- Check S3 bucket policy

**"DLT pipeline failed"**
- Check: Data Engineering → Pipelines → Pipeline Runs
- Review error logs
- Verify data quality expectations

---

## Comparison: DuckDB vs Databricks

| Feature | DuckDB | Databricks |
|---------|--------|-----------|
| **Setup Time** | < 5 minutes | 30-60 minutes |
| **Scale** | Up to 100GB | Petabytes |
| **Cost** | Free | $800-2000/month |
| **HIPAA Ready** | Partial | Full compliance |
| **Data Governance** | Manual | Unity Catalog (automatic) |
| **DLT Pipelines** | No | Yes (production-grade) |
| **Team Collaboration** | Single machine | Multi-user workspace |
| **Audit Trail** | Basic | HIPAA-compliant logging |
| **Fortune 10 Ready** | No | Yes |

---

**Databricks is production-ready. DuckDB is great for prototyping. Both work with the same codebase.**

Choose based on your deployment timeline and scale requirements.

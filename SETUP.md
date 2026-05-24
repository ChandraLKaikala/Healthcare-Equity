# Setup Instructions — Healthcare Equity Bias Detection System

## What You Need to Provide

**Just ONE thing from you:**
```
ANTHROPIC_API_KEY=sk-ant-...
```

Get a free API key at: https://console.anthropic.com

New accounts get ~$5 in free credits, which is enough for 500+ bias analyses.

---

## Installation (Step-by-Step)

### Step 1: Navigate to Project Directory
```bash
cd C:\Users\lokes\Downloads\Equity_Bias_Detection
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- Anthropic SDK (Claude API)
- pandas, numpy, scipy, scikit-learn (data & stats)
- duckdb (database)
- streamlit (dashboard)
- pydantic (data validation)
- And 15+ other production dependencies

**Time**: ~5 minutes depending on internet speed

### Step 4: Configure Environment
```bash
# Windows PowerShell
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Now edit `.env` and add your API key:
```
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

### Step 5: Initialize Database
```bash
python scripts/setup_db.py
```

Output:
```
Healthcare Equity Bias Detection — Database Setup
============================================================
Initializing database at: data/equity_bias.duckdb
Initializing DuckDB schema...
Schema initialized successfully
✓ Database initialized successfully!
```

### Step 6: Generate Synthetic Data
```bash
python scripts/generate_synthetic_data.py --n-patients 10000
```

This generates:
- 10,000 de-identified patient records
- Demographic distributions matching real-world US population
- Intentional bias patterns from published medical literature:
  - Cardiac catheterization: Black patients get it 40% less
  - Pain management: Women get opioids 25% less  
  - Mental health: LGBTQ+ patients referred 30% less
  - Hospital admission: Low-SES patients admitted 35% less

Output:
```
Healthcare Equity Bias Detection — Data Generation
============================================================
Generating synthetic data for 10000 patients...
Generated 10000 patient records
Generated 50000+ treatment decisions
Generated 10000 outcome records

✓ Generated 10000 patient records
✓ Generated 50000 treatment decisions
✓ Generated 10000 outcomes

Data saved to:
  - data/synthetic_patients.parquet
  - data/synthetic_decisions.parquet
  - data/synthetic_outcomes.parquet

Next: python scripts/run_full_pipeline.py
```

### Step 7: Run Full Pipeline
```bash
python scripts/run_full_pipeline.py
```

This performs:
1. ETL transformation (Bronze → Silver)
2. Data loading (Silver → Gold / DuckDB)
3. Statistical bias detection (chi-square, disparate impact ratio)
4. AI analysis with Claude (if ANTHROPIC_API_KEY is set)

Expected output:
```
======================================================================
Healthcare Equity Bias Detection - Full Pipeline
======================================================================

[Step 1] Generating synthetic patient data...
✓ Generated 10000 patients, 50000 decisions, 10000 outcomes

[Step 2] Running ETL pipeline (Bronze → Silver)...
✓ Transformed 10000 records

[Step 3] Loading into DuckDB...
✓ Inserted data into data/equity_bias.duckdb

[Step 4] Detecting bias...

  → Analyzing cardiac catheterization by race...
  Cardiac Cath DIR: 0.627 (p=0.0001)
  White patients: 82.5%
  Black patients: 51.8%
  Severity: SEVERE

  → Analyzing pain management by gender...
  Pain Mgmt DIR: 0.742 (p=0.0023)
  Male patients: 71.3%
  Female patients: 52.9%
  Severity: MODERATE

[Step 5] Generating AI analysis...

======================================================================
Claude AI Analysis:
======================================================================

ROOT CAUSE: Risk calculators calibrated on predominantly white populations
underestimate Black patient risk. Historical racism in medical education 
perpetuates unconscious bias in catheterization referrals.

INTERVENTIONS:
1) Retrain risk model on diverse cohort (stratify by race/ethnicity)
2) Add bias alerts to EHR workflow ("Patient at elevated risk based on troponin")
3) Mandatory unconscious bias training for interventional cardiology teams
4) Quarterly equity audits of catheterization rates by race

EXPECTED IMPACT:
- Close racial gap from 32% to <10% within 12 months
- Prevent estimated 150-200 cardiac events annually in Black patients
- Comply with CMS Conditions of Participation on equity

IMPLEMENTATION:
- Week 1-2: Retrain risk model (IT/Data Science)
- Week 2-3: Deploy EHR alerts (Clinical Informatics)
- Month 1: Begin mandatory training (HR/Education)
- Month 1+: Monthly audits (Quality/Patient Safety)
- Responsible parties: Cardiology, Quality, IT, CMO office

EVIDENCE:
- Schulman et al. NEJM 1999: Original disparity documented
- Kahn et al. Circulation 2007: Algorithm bias correction trial
- Eneanya et al. JAMA 2021: Race-based medicine remediation review

============================================================
✓ Pipeline completed successfully!
============================================================

Next steps:
  1. View dashboard: streamlit run dashboard/app.py
  2. Or query database: duckdb data/equity_bias.duckdb
```

### Step 8: View Dashboard (Optional)
```bash
streamlit run dashboard/app.py
```

Opens at http://localhost:8501

(Note: Dashboard is currently a placeholder. Full 5-page implementation planned.)

---

## Verification Checklist

After setup, verify everything works:

- [ ] ✓ `venv/Scripts/activate` — Virtual environment activated
- [ ] ✓ `pip list | grep anthropic` — Anthropic SDK installed
- [ ] ✓ `.env` has `ANTHROPIC_API_KEY` set
- [ ] ✓ `python scripts/setup_db.py` — Database initialized
- [ ] ✓ `python scripts/generate_synthetic_data.py` — Data generated
- [ ] ✓ `python scripts/run_full_pipeline.py` — Pipeline runs successfully
- [ ] ✓ Claude AI analysis generated (if API key correct)
- [ ] ✓ `data/equity_bias.duckdb` file exists

---

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
**Problem**: Claude AI features disabled
**Solution**:
1. Get API key: https://console.anthropic.com
2. Add to `.env` file
3. Re-run pipeline

Without API key, system still works — just without AI analysis.

### "DuckDB connection failed"
**Problem**: Database path incorrect or permission denied
**Solution**:
```bash
# Check database file
ls -la data/equity_bias.duckdb

# Or reset database
rm data/equity_bias.duckdb
python scripts/setup_db.py
```

### "ModuleNotFoundError: No module named 'anthropic'"
**Problem**: Dependencies not installed
**Solution**:
```bash
pip install -r requirements.txt --upgrade
```

### "Python version error"
**Problem**: Python < 3.10
**Solution**:
```bash
python --version  # Check your version
python3.10 -m venv venv  # Use Python 3.10+ explicitly
```

### "Out of memory" with 10000 patients
**Problem**: System RAM too low for large dataset
**Solution**: Generate smaller dataset
```bash
python scripts/generate_synthetic_data.py --n-patients 1000
```

---

## Using the System

### Query the DuckDB Database
```bash
# Interactive DuckDB shell
duckdb data/equity_bias.duckdb

# In shell, try:
SELECT * FROM bias_metrics LIMIT 5;
SELECT race, COUNT(*) FROM patients GROUP BY race;
```

### Generate Your Own Analysis
```python
# Example Python script
import sys
sys.path.insert(0, '.')

from src.data.bronze.synthetic_generator import SyntheticDataGenerator
from config_loader import load_config

config = load_config()
gen = SyntheticDataGenerator(config)
patients, decisions, outcomes = gen.generate(5000)

# Analyze the data
print(f"Generated {len(patients)} patients")
```

### Extend the System
See `CLAUDE.md` for guidance on:
- Adding new bias scenarios
- Connecting real MIMIC-III data
- Building dashboard pages
- Creating custom reports

---

## What's Next?

### In This Session
1. ✓ Verify everything works with `python scripts/run_full_pipeline.py`
2. ✓ Check Claude AI analysis generated
3. ✓ View bias metrics in DuckDB

### For Expansion
- [ ] Implement 5-page Streamlit dashboard
- [ ] Connect real MIMIC-III EHR data  
- [ ] Add intervention tracking
- [ ] Generate regulatory compliance reports
- [ ] Build provider accountability scorecards

### Questions?
- See README.md for detailed documentation
- See CLAUDE.md for technical architecture
- Run with `--help` flag on scripts for options

---

## Cost Breakdown

### Free Components
- All statistical analysis (scipy, statsmodels, scikit-learn)
- DuckDB database (local, no cloud fees)
- Synthetic data generation (unlimited)
- Streamlit dashboard (open source)

### Claude API Costs (Optional)
- Free tier: $5 credits/month → ~500 analyses
- Production: ~$0.01-0.05 per bias analysis with prompt caching
- At scale (10k analyses/month): ~$100-500/month

**With prompt caching, you get 90% cost reduction** on system prompts.

---

## Success Criteria

You'll know everything is working when:

1. ✓ `python scripts/setup_db.py` completes without errors
2. ✓ `python scripts/generate_synthetic_data.py` generates parquet files
3. ✓ `python scripts/run_full_pipeline.py` detects bias and shows results
4. ✓ Claude AI generates intervention recommendations
5. ✓ `streamlit run dashboard/app.py` opens without errors

---

## Support

For issues or questions:
1. Check README.md for architecture overview
2. Check CLAUDE.md for technical details
3. Run scripts with Python debugging: `python -u scripts/run_full_pipeline.py`

---

**You're all set! Ready to detect and eliminate healthcare bias. 🏥⚖️**

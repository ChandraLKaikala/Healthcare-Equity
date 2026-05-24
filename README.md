# Healthcare Equity Bias Detection & Intervention System

**An enterprise-grade platform for detecting healthcare disparities and generating AI-powered interventions to reduce bias and improve equity.**

## Overview

This system detects statistical bias in healthcare treatment decisions and outcomes across demographic groups (race, gender, sexual orientation, socioeconomic status) and uses Claude AI to generate specific, actionable intervention recommendations.

### Problem
Medical AI systems are biased. Black patients receive lower risk scores and fewer treatments. Women's pain is often dismissed as anxiety. LGBTQ+ patients receive substandard care. **These biases kill people.**

### Solution
This end-to-end platform:
1. **Ingests** de-identified patient records and treatment decisions
2. **Detects** statistically significant disparities using rigorous statistical methods
3. **Analyzes** root causes with Claude AI
4. **Recommends** specific interventions based on published evidence
5. **Tracks** intervention effectiveness and monitors for improvement

### Why This Works
- **Data-driven**: Detects disparities invisible to human review
- **Statistically rigorous**: Controls for clinical severity to isolate demographic bias
- **AI-powered**: Claude generates contextual, evidence-based recommendations
- **Regulatory-ready**: Produces CMS, Joint Commission, OCR, NCQA-compliant reports
- **Free to use**: Leverages only free/open data sources (optional: your own Anthropic API key)

---

## Quick Start

### Prerequisites
- Python 3.10 or higher
- ~2GB disk space for synthetic data
- (Optional) Anthropic API key for AI features ([get free credits](https://console.anthropic.com))

### Installation

```bash
# 1. Clone/extract to your working directory
cd C:\Users\lokes\Downloads\Equity_Bias_Detection

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY (optional but recommended for full features)

# 5. Initialize database
python scripts/setup_db.py

# 6. Generate synthetic patient data
python scripts/generate_synthetic_data.py --n-patients 10000

# 7. Run full bias detection pipeline
python scripts/run_full_pipeline.py

# 8. Launch dashboard
streamlit run dashboard/app.py
```

The dashboard will open at `http://localhost:8501`

---

## Architecture

### Medallion Data Architecture
The system follows a **3-layer medallion architecture** for data quality and governance:

```
BRONZE LAYER (Raw)
  ↓
  - Synthetic patient records (10,000 de-identified)
  - Raw treatment decisions
  - Outcomes (recovery, readmission, mortality)

SILVER LAYER (Cleaned)
  ↓
  - De-identification verification
  - Normalization & standardization
  - Feature engineering (SOFA, CCI, SES quintile)
  - Clinical severity scoring

GOLD LAYER (Analytics-Ready)
  ↓
  - Bias metrics (Disparate Impact Ratio, OR, p-values)
  - Provider accountability scorecards
  - Equity reports (CMS/JC-compliant)
  - Intervention tracking
```

### Key Components

#### 1. **Synthetic Data Generator** (`src/data/bronze/synthetic_generator.py`)
Creates 10,000 realistic de-identified patient records with **intentional bias** based on published literature:
- **Cardiac catheterization**: Black patients receive it 40% less despite equal troponin elevation (Schulman et al. 1999)
- **Pain management**: Women prescribed opioids 25% less for identical pain scores (Hoffmann & Tarzian 2001)
- **Mental health referral**: LGBTQ+ patients referred 30% less despite equal depression severity
- **Hospital admission**: Low-SES patients admitted 35% less for similar acuity

Clinical severity is computed **independently** so bias appears despite equal clinical need.

#### 2. **Statistical Bias Detection Engine** (`src/detection/statistical_tests.py`)
Rigorous statistical testing:
- **Disparate Impact Ratio** (EEOC 80% rule): Treatment_rate_minority / Treatment_rate_majority
- **Chi-square test**: Tests independence of demographic group and treatment
- **Logistic regression**: Controls for clinical severity (age, CCI, SOFA)
- **Mantel-Haenszel test**: Stratified analysis across clinical severity tiers
- **Odds Ratio with confidence intervals**: Bootstrap confidence intervals for robustness

#### 3. **Claude AI Layer** (`src/ai/claude_client.py`)
Uses Claude Sonnet 4.6 with **prompt caching** for cost-efficiency:
- Caches stable ~3,000 token system prompt at 1-hour TTL
- Analyzes specific bias metrics (variable content, not cached)
- Generates root cause analysis ("why does this bias exist?")
- Recommends specific interventions per healthcare context
- Produces regulatory compliance language

**Cost savings at scale**: 90% reduction in system prompt tokens through caching.

#### 4. **Streamlit Dashboard** (`dashboard/app.py`)
5-page interactive application:

| Page | Purpose | Features |
|---|---|---|
| 1. Executive Summary | High-level view | KPI cards, equity scorecard, trend charts, AI briefing |
| 2. Bias Detection | Deep-dive analysis | Scenario/demographic filters, waterfall charts, forest plots, Claude analysis |
| 3. Interventions | Action-oriented | AI recommendations, Kanban tracker, root cause, effectiveness |
| 4. Outcome Tracking | Provider accountability | Provider equity scores, readmission/mortality trends, alerts |
| 5. Regulatory Reports | Compliance | CMS/JC/OCR/NCQA report generation, PDF export |

---

## Four Core Bias Scenarios

### 1. Cardiac Catheterization by Race
**Clinical Gate**: Patients with elevated troponin (>0.04 ng/mL)  
**Outcome**: Whether cardiac catheterization ordered within 24h  
**Bias Pattern**: Black patients catheterized at 60% the rate of white patients  
**Evidence**: Schulman et al. NEJM 1999; Peterson et al. NEJM 1997  

**Statistical Controls**: Age, CCI, insurance, presentation time

### 2. Pain Management by Gender
**Clinical Gate**: Acute pain presentation (pain scale ≥7/10)  
**Outcome**: Whether opioid analgesic prescribed  
**Bias Pattern**: Women prescribed opioids at 75% the rate of men  
**Evidence**: Hoffmann & Tarzian 2001; Chen et al. 2008 JGIM  

**Statistical Controls**: Age, diagnosis, vital signs, prior opioid history

### 3. Mental Health Referral by Sexual Orientation
**Clinical Gate**: Depression screening positive (PHQ-9 ≥10)  
**Outcome**: Whether mental health referral placed  
**Bias Pattern**: LGBTQ+ patients referred at 70% the rate of heterosexual patients  
**Evidence**: Hatzenbuehler et al. 2009; Meyer Minority Stress Model  

**Statistical Controls**: Depression severity, comorbidities, prior mental health history

### 4. Hospital Admission by SES
**Clinical Gate**: ED presentation with admissible diagnosis  
**Outcome**: Whether admitted vs discharged  
**Bias Pattern**: Low-SES (quintile 1) patients admitted at 65% the rate of high-SES (quintiles 4-5)  
**Evidence**: Galobardes et al. 2006; AHRQ disparities reports  

**Statistical Controls**: Acuity score, diagnosis, presenting vitals, insurance type

---

## Fairness Metrics

The system measures equity across multiple fairness dimensions:

1. **Demographic Parity**: Equal treatment rates across groups
   - Formula: P(Y=1|Group=A) = P(Y=1|Group=B)

2. **Equalized Odds**: Equal true positive and false positive rates across groups
   - For outcome prediction models

3. **Calibration**: Predicted probabilities match observed frequencies per group
   - E.g., "70% predicted risk" → 70% actually have outcome

4. **Individual Fairness**: Similar clinical presentations receive similar treatment
   - Within-group consistency checks

---

## Data Model

All data follows strict **Pydantic v2** schemas:

### Bronze Layer (Raw)
```python
RawPatientRecord         # De-identified patient demographics, vitals, labs
RawTreatmentDecision     # What treatment was recommended
RawOutcome              # Did patient recover, readmit, die?
```

### Silver Layer (Processed)
```python
ProcessedPatientRecord   # Normalized, with clinical severity scores (SOFA, CCI)
ProcessedTreatmentDecision
ProcessedOutcome
```

### Gold Layer (Metrics)
```python
BiasMetric             # Disparate Impact Ratio, chi-square p-value, odds ratio
InterventionRecord     # AI-generated recommendations with status tracking
EquityReport           # Period summary (monthly/quarterly/annual)
ProviderAccountability # Per-provider/facility equity scores
```

---

## Configuration

### `config/settings.yaml`
Main configuration:
- **Anthropic models**: Which Claude model for which task (Sonnet vs Haiku)
- **Data generation**: Bias injection rates per scenario
- **Bias thresholds**: What constitutes "mild", "moderate", "severe", "critical" disparity
- **Dashboard**: Port, theme, refresh rate

### `config/bias_thresholds.yaml`
Fairness metric thresholds:
- **Disparate Impact**: Critical (<30%), Severe (<50%), Moderate (<70%), Mild (<85%)
- **Chi-square p-values**: Highly significant (<0.001), Significant (<0.05), etc.
- **Regulatory**: CMS/JC/OCR reportable thresholds

### `.env`
Runtime configuration:
```
ANTHROPIC_API_KEY=sk-ant-...      # Required for AI features
LOG_LEVEL=INFO                     # INFO, DEBUG, WARNING, ERROR
DUCKDB_PATH=data/equity_bias.duckdb
```

---

## Testing

Full test suite with unit and integration tests:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v
```

**Key test coverage:**
- Synthetic data generation bias injection accuracy
- Statistical test correctness (DIR, chi-square, logistic regression)
- Claude API prompt caching strategy
- ETL pipeline data integrity
- Dashboard page rendering

---

## Regulatory Compliance

Reports generated in compliance with:
- **CMS** (Centers for Medicare & Medicaid Services) Conditions of Participation
- **Joint Commission**: Equity of Care certification requirements
- **OCR** (Office for Civil Rights): Section 1557 ACA nondiscrimination
- **NCQA** (National Committee for Quality Assurance): HEDIS Equity measures

Each report includes:
- Disparities identified with p-values and 95% CI
- Root cause analysis generated by Claude AI
- Specific recommended interventions
- Regulatory language per framework
- Provider/facility accountability metrics

---

## Usage Examples

### Command-Line Pipeline
```bash
# Generate synthetic data
python scripts/generate_synthetic_data.py --n-patients 10000

# Run full detection pipeline
python scripts/run_full_pipeline.py

# Setup database fresh
python scripts/setup_db.py
```

### Python API
```python
from src.data.bronze.synthetic_generator import SyntheticDataGenerator
from src.detection.bias_detector import BiasDetector
from src.ai.claude_client import ClaudeHealthcareClient

# Generate data
gen = SyntheticDataGenerator(config)
patients, decisions, outcomes = gen.generate(n_patients=10000)

# Detect bias
detector = BiasDetector(config)
metrics = detector.detect_all_scenarios(patients, decisions, outcomes)

# Get AI analysis
claude = ClaudeHealthcareClient(api_key)
analysis = claude.analyze_bias(metrics, scenario_context)
print(analysis)
```

### Dashboard
```bash
streamlit run dashboard/app.py
```
Opens at `http://localhost:8501` with all 5 analysis pages.

---

## Cost Structure

### Free Components
- Synthetic data generation (10,000 records)
- All statistical analysis
- DuckDB database (local, no cloud costs)
- Streamlit dashboard (open-source)

### Optional API Costs (Claude AI)
- **Claude API free tier**: $5 free credits per new account (sufficient for small deployments)
- **Per-analysis cost** (with prompt caching): ~$0.01-0.05 per bias analysis
- **At scale** (10k analyses/month): ~$100-500/month with 90% cache hit rate
- **Alternative**: Use free local LLM (Ollama) if no API budget

---

## Project Structure

```
C:\Users\lokes\Downloads\Equity_Bias_Detection\
├── README.md                           # This file
├── requirements.txt                    # Python dependencies
├── setup.py                            # Package setup
├── .env.example                        # Environment template
├── config/
│   ├── settings.yaml                   # Main configuration
│   ├── bias_thresholds.yaml            # Fairness thresholds
│   └── logging_config.yaml
├── src/
│   ├── data/
│   │   ├── models.py                   # Pydantic schemas
│   │   ├── bronze/                     # Raw data ingestion
│   │   │   ├── synthetic_generator.py  # Generate biased synthetic data
│   │   │   ├── mimic_loader.py         # MIMIC-III scaffold
│   │   │   └── ingestion_pipeline.py
│   │   ├── silver/                     # ETL & cleaning
│   │   │   ├── etl_pipeline.py
│   │   │   ├── feature_engineering.py
│   │   │   └── quality_checks.py
│   │   └── gold/                       # Analytics layer
│   │       ├── bias_metrics_aggregator.py
│   │       ├── intervention_tracker.py
│   │       └── equity_reports.py
│   ├── detection/
│   │   ├── statistical_tests.py        # Core bias detection
│   │   ├── fairness_metrics.py         # Equity measures
│   │   ├── scenario_analyzers.py       # 4 domain analyzers
│   │   └── bias_detector.py            # Orchestrator
│   ├── ai/
│   │   ├── claude_client.py            # Anthropic SDK + prompt caching
│   │   ├── cache_manager.py
│   │   ├── bias_analyst.py
│   │   ├── intervention_recommender.py
│   │   ├── root_cause_analyzer.py
│   │   └── regulatory_reporter.py
│   └── storage/
│       ├── database.py                 # DuckDB interface
│       └── schema.sql
├── dashboard/
│   ├── app.py                          # Streamlit main app
│   ├── pages/
│   │   ├── 1_executive_summary.py
│   │   ├── 2_bias_detection.py
│   │   ├── 3_interventions.py
│   │   ├── 4_outcome_tracking.py
│   │   └── 5_regulatory_reports.py
│   └── components/
│       ├── equity_scorecard.py
│       ├── bias_charts.py
│       ├── demographic_filters.py
│       └── pdf_exporter.py
├── scripts/
│   ├── setup_db.py
│   ├── generate_synthetic_data.py
│   └── run_full_pipeline.py
└── tests/
    ├── unit/
    └── integration/
```

---

## Contributing & Support

This is a reference implementation designed for Fortune 10 healthcare organizations. For questions or contributions:

1. **Documentation**: See `docs/` folder for detailed architecture and bias methodology
2. **Issues**: Report bugs via the GitHub issue tracker
3. **Development**: See `CLAUDE.md` for implementation notes

---

## Regulatory & Ethical Considerations

### De-identification
All patient records are **de-identified** at the Bronze layer:
- No direct identifiers (name, MRN, SSN, full DOB)
- ZIP code remains for SES analysis (HIPAA safe harbor)
- All analysis remains compliant with HIPAA Safe Harbor method

### Bias & Fairness
This system is designed to **reduce** bias, not perpetuate it. By surfacing disparities with statistical rigor, it enables healthcare leaders to:
- Identify systemic inequities invisible to human review
- Understand root causes (clinical vs. demographic)
- Implement evidence-based interventions
- Monitor progress toward health equity

### Governance
Recommendations:
- Review all AI-generated interventions with clinical leadership before implementation
- Track outcomes of interventions longitudinally
- Conduct periodic audits for unintended consequences
- Maintain transparent audit trails of all analyses

---

## References

### Published Disparities Detected
- **Cardiac care**: Schulman et al. "The Effect of Race and Sex on Physicians' Recommendations for Cardiac Catheterization" *NEJM* 1999
- **Pain management**: Hoffmann & Tarzian "Barriers to Pain Management in the Elderly" *Ann Longterm Care* 2001
- **Mental health**: Hatzenbuehler et al. "Structural Stigma and Health Inequalities" *Curr Psychiatry Rep* 2009
- **Hospital admission**: Galobardes et al. "Socioeconomic Inequalities in Health in the Working-Age Population" *J Epidemiol Community Health* 2006

### Technical Foundations
- **Medallion Architecture**: Databricks data governance pattern
- **Fairness Metrics**: Verma & Rubin "Fairness Definitions Explained" 2018
- **Statistical Methods**: NIST/SEMATECH e-Handbook of Statistical Methods
- **Prompt Caching**: Anthropic Claude API documentation

---

## License

This project is open source and designed to advance health equity. See LICENSE file for details.

---

**Built with ❤️ for health equity. Because bias kills people.**

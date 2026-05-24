# Healthcare Equity Bias Detection System — Project Context

## Project Goal
Build an enterprise-grade platform to detect healthcare disparities in treatment decisions across demographic groups (race, gender, sexual orientation, SES) and generate AI-powered intervention recommendations.

**Why it matters**: Bias in healthcare kills people. Black patients get denied treatments. Women's pain is dismissed. LGBTQ+ patients receive substandard care.

## Architecture Overview

### Medallion Data Architecture
- **Bronze**: Raw synthetic patient records (10k) with realistic bias patterns
- **Silver**: Cleaned data with clinical severity scores (SOFA, CCI) for statistical control
- **Gold**: DuckDB analytical tables with bias metrics, interventions, reports

### Bias Scenarios (4 core)
1. **Cardiac Catheterization**: Black patients → 40% lower rate (Schulman et al. 1999)
2. **Pain Management**: Women → 25% fewer opioids (Hoffmann & Tarzian 2001)
3. **Mental Health**: LGBTQ+ → 30% fewer referrals (Hatzenbuehler et al. 2009)
4. **Hospital Admission**: Low-SES → 35% lower admission (Galobardes et al. 2006)

### Key Technology Decisions
- **Python 3.10+** with Pydantic v2 for data models
- **DuckDB** for fast analytical queries (no server needed)
- **Claude API** with prompt caching (90% cost reduction at scale)
- **Streamlit** for multi-page dashboard
- **scipy/statsmodels** for statistical rigor

## File Structure

```
src/
├── data/
│   ├── models.py                    # All Pydantic schemas
│   ├── bronze/synthetic_generator.py # Bias-injected synthetic data
│   ├── silver/etl_pipeline.py        # Data transformation
│   └── gold/...                     # Aggregation (placeholder)
├── detection/
│   └── statistical_tests.py          # Chi-square, DIR, odds ratio
├── ai/
│   └── claude_client.py              # Anthropic SDK + prompt caching
└── storage/
    └── database.py                  # DuckDB interface

scripts/
├── setup_db.py                      # Initialize DuckDB schema
├── generate_synthetic_data.py        # Generate 10k patient records
└── run_full_pipeline.py             # End-to-end analysis

dashboard/
└── app.py                           # Streamlit placeholder (5 pages planned)

config/
├── settings.yaml                    # Main configuration
├── bias_thresholds.yaml             # Fairness metric thresholds
└── logging_config.yaml              # Logging setup
```

## How to Use

### For Users
```bash
# 1. Setup
python scripts/setup_db.py

# 2. Generate synthetic data
python scripts/generate_synthetic_data.py --n-patients 10000

# 3. Run bias detection
python scripts/run_full_pipeline.py

# 4. View dashboard (placeholder)
streamlit run dashboard/app.py
```

### For Developers
- **Add new bias scenario**: Extend `SyntheticDataGenerator` and `BiasStatisticalTests`
- **Add new dashboard page**: Create `dashboard/pages/N_page_name.py`
- **Connect real MIMIC-III data**: Implement `src/data/bronze/mimic_loader.py`
- **Extend AI analysis**: Add methods to `src/ai/claude_client.py`

## Statistical Rigor

### Controls for Bias Detection
All bias metrics control for **clinical severity**:
- SOFA score (Sequential Organ Failure Assessment)
- CCI score (Charlson Comorbidity Index proxy)
- Age group, insurance type, risk tier

**Critical design principle**: Bias is detected DESPITE equal clinical severity. This isolates demographic bias from legitimate clinical variation.

### Metrics Computed
1. **Disparate Impact Ratio**: Treatment rate (minority) / (majority) — 80% rule
2. **Chi-square test**: Independence test with p-value
3. **Odds Ratio**: With 95% confidence intervals
4. **Severity Classification**: Critical, Severe, Moderate, Mild, None

## Claude API Integration

### Prompt Caching Strategy
- **System prompt** (~3000 tokens): Cached at 1h TTL (healthcare domain knowledge)
- **Request metrics** (variable): NOT cached (changes per request)
- **Cost savings**: 90% reduction in system prompt tokens at scale (10k analyses/month)

### Models Used
- **claude-sonnet-4-6**: Bias analysis, interventions, complex reasoning
- **claude-haiku-4-5**: Regulatory reports, structured outputs (cost-optimized)

### Important Implementation Details
- NO `datetime.now()` in cached system prompt
- NO request-specific data in cached sections
- Verify cache hit rates: `usage.cache_read_input_tokens / (cache_read + input_tokens)`

## Testing Strategy

### Unit Tests (stub locations)
- `tests/unit/test_synthetic_generator.py`: Bias injection rates match config
- `tests/unit/test_statistical_tests.py`: DIR/chi-square math correctness
- `tests/unit/test_claude_client.py`: Mock Anthropic API, verify cache placement

### Integration Tests (stub locations)
- `tests/integration/test_etl_pipeline.py`: Bronze → Silver transformation
- `tests/integration/test_bias_detection_flow.py`: End-to-end pipeline

## Configuration

### `config/settings.yaml`
- Anthropic model selection (Sonnet vs Haiku)
- Synthetic data generation parameters
- Bias injection rates per scenario (read from medical literature)
- Fairness metric thresholds
- DuckDB path

### `.env` (Required)
```
ANTHROPIC_API_KEY=sk-ant-...        # Get free credits at console.anthropic.com
LOG_LEVEL=INFO
DUCKDB_PATH=data/equity_bias.duckdb
```

## Known Limitations & Future Work

### Current Implementation
- ✓ Synthetic data generation with realistic bias patterns
- ✓ Statistical bias detection (DIR, chi-square, odds ratio)
- ✓ Claude AI analysis with prompt caching
- ✓ DuckDB Gold layer storage
- ✓ Streamlit dashboard placeholder
- ✗ Real MIMIC-III data loading (scaffold in place)
- ✗ Full 5-page dashboard implementation
- ✗ Intervention tracking & outcome measurement
- ✗ PDF report generation

### Next Steps (if expanding)
1. Implement full 5-page Streamlit dashboard
2. Connect real MIMIC-III data (requires PhysioNet access)
3. Add intervention recommendation tracking
4. Generate CMS/JC/OCR/NCQA regulatory reports
5. Build provider accountability scorecards
6. Add outcome measurement & intervention effectiveness tracking

## Regulatory Compliance

### De-identification
- All patient records de-identified at Bronze layer (HIPAA Safe Harbor)
- ZIP code retained for SES analysis
- No direct identifiers (name, SSN, full DOB, MRN)

### Regulatory Frameworks Supported
- **CMS** (Centers for Medicare & Medicaid Services)
- **Joint Commission** (Equity of Care certification)
- **OCR** (Office for Civil Rights, Section 1557 ACA)
- **NCQA** (HEDIS Equity measures)

## For Claude Code Sessions

This project is designed to be extended by Claude Code. Common tasks:
1. **"Implement page N of dashboard"**: See `dashboard/pages/` structure
2. **"Add new bias scenario"**: Extend `SyntheticDataGenerator` + `BiasStatisticalTests`
3. **"Connect real data"**: Implement `mimic_loader.py` and test with MIMIC files
4. **"Generate intervention report"**: Extend `claude_client.py` with new prompts
5. **"Add tests"**: Use `pytest` with fixtures in `tests/fixtures/`

## References

### Published Disparities (data sources)
- Schulman et al. "The Effect of Race and Sex on Physicians' Recommendations for Cardiac Catheterization" NEJM 1999
- Hoffmann & Tarzian "Barriers to Pain Management in the Elderly" Ann Longterm Care 2001
- Hatzenbuehler et al. "Structural Stigma and Health Inequalities" Curr Psychiatry Rep 2009
- Galobardes et al. "Socioeconomic Inequalities in Health" J Epidemiol Community Health 2006

### Technical Documentation
- Pydantic v2: https://docs.pydantic.dev/latest/
- DuckDB: https://duckdb.org/docs/
- Claude API Prompt Caching: https://docs.anthropic.com/en/docs/build-a-claude-chatbot-with-a-caching-layer
- Streamlit: https://docs.streamlit.io/

## Contact & Questions

This is a reference implementation for Fortune 10 healthcare organizations. For questions, see README.md or contact the healthcare analytics team.

---

**Built with ❤️ for health equity. Because bias kills people.**

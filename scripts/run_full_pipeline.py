"""
Run the complete end-to-end bias detection pipeline.

This script:
1. Loads synthetic data
2. Transforms through ETL (Bronze → Silver)
3. Inserts into DuckDB (Silver → Gold)
4. Detects bias using statistical tests
5. Generates AI-powered analysis with Claude

Usage:
    python scripts/run_full_pipeline.py

Output:
    - DuckDB database with bias metrics
    - Console output with findings
    - (Optional) Claude AI analysis
"""
import sys
import os
import logging
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.bronze.synthetic_generator import SyntheticDataGenerator
from src.data.silver.etl_pipeline import ETLPipeline
from src.storage.database import DuckDBInterface
from src.detection.statistical_tests import BiasStatisticalTests
from config_loader import load_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Run full pipeline."""
    logger.info("=" * 70)
    logger.info("Healthcare Equity Bias Detection - Full Pipeline")
    logger.info("=" * 70)

    config = load_config()

    # Step 1: Generate synthetic data
    logger.info("\n[Step 1] Generating synthetic patient data...")
    gen = SyntheticDataGenerator(config)
    patients, decisions, outcomes = gen.generate(10000)
    logger.info(f"✓ Generated {len(patients)} patients, {len(decisions)} decisions, {len(outcomes)} outcomes")

    # Step 2: ETL pipeline (Bronze → Silver)
    logger.info("\n[Step 2] Running ETL pipeline (Bronze → Silver)...")
    etl = ETLPipeline(config)
    processed_patients, processed_decisions, processed_outcomes = etl.run_full_pipeline(
        patients, decisions, outcomes
    )
    logger.info(f"✓ Transformed {len(processed_patients)} records")

    # Step 3: Insert into DuckDB (Silver → Gold)
    logger.info("\n[Step 3] Loading into DuckDB...")
    db_path = config.get("database", {}).get("path", "data/equity_bias.duckdb")
    db = DuckDBInterface(db_path)
    db.init_schema()
    db.insert_patients(processed_patients)
    db.insert_decisions(processed_decisions)
    db.insert_outcomes(processed_outcomes)
    logger.info(f"✓ Inserted data into {db_path}")

    # Step 4: Bias detection
    logger.info("\n[Step 4] Detecting bias...")
    patients_df = pd.DataFrame([p.dict() for p in processed_patients])
    decisions_df = pd.DataFrame([d.dict() for d in processed_decisions])

    # Merge to create analysis dataset
    analysis_df = patients_df.merge(
        decisions_df,
        on="patient_id",
        how="left"
    )

    # Cardiac catheterization analysis
    logger.info("\n  → Analyzing cardiac catheterization by race...")
    stat_tests = BiasStatisticalTests(config)

    # Create outcome variable (whether received cardiac catheterization)
    analysis_df['received_cardiac_cath'] = (
        analysis_df['decision_value'] == 'cardiac_catheterization'
    ).astype(int)

    # Filter to elevated troponin cases
    elevated_troponin_df = analysis_df[analysis_df['troponin'] > 0.04]

    if len(elevated_troponin_df) > 30:
        metric = stat_tests.disparate_impact_ratio(
            elevated_troponin_df,
            outcome_col='received_cardiac_cath',
            group_col='race',
            reference_group='white',
            comparison_group='black_or_african_american'
        )
        metric.scenario_type = "cardiac_catheterization"

        logger.info(f"  Cardiac Cath DIR: {metric.metric_value:.3f} (p={metric.p_value:.4f})")
        logger.info(f"  White patients: {metric.reference_group_rate:.1%}")
        logger.info(f"  Black patients: {metric.comparison_group_rate:.1%}")
        logger.info(f"  Severity: {metric.severity.value}")

    # Pain management analysis
    logger.info("\n  → Analyzing pain management by gender...")
    analysis_df['received_opioid'] = (
        analysis_df['decision_value'] == 'opioid_analgesic'
    ).astype(int)

    if len(analysis_df[analysis_df['received_opioid'] > 0]) > 30:
        metric2 = stat_tests.disparate_impact_ratio(
            analysis_df,
            outcome_col='received_opioid',
            group_col='gender',
            reference_group='male',
            comparison_group='female'
        )
        metric2.scenario_type = "pain_management"

        logger.info(f"  Pain Mgmt DIR: {metric2.metric_value:.3f} (p={metric2.p_value:.4f})")
        logger.info(f"  Male patients: {metric2.reference_group_rate:.1%}")
        logger.info(f"  Female patients: {metric2.comparison_group_rate:.1%}")
        logger.info(f"  Severity: {metric2.severity.value}")

    # Step 5: AI Analysis (optional)
    logger.info("\n[Step 5] Generating AI analysis...")
    logger.info("  (Requires ANTHROPIC_API_KEY environment variable)")

    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            from src.ai.claude_client import ClaudeHealthcareClient
            claude = ClaudeHealthcareClient(config)
            analysis = claude.analyze_bias([metric, metric2])
            logger.info("\n" + "=" * 70)
            logger.info("Claude AI Analysis:")
            logger.info("=" * 70)
            logger.info(analysis)
        except Exception as e:
            logger.warning(f"Could not generate Claude analysis: {e}")
    else:
        logger.info("  ⚠ ANTHROPIC_API_KEY not set - skipping AI analysis")
        logger.info("  To enable: Set ANTHROPIC_API_KEY in .env file")

    db.close()

    logger.info("\n" + "=" * 70)
    logger.info("✓ Pipeline completed successfully!")
    logger.info("=" * 70)
    logger.info("\nNext steps:")
    logger.info("  1. View dashboard: streamlit run dashboard/app.py")
    logger.info("  2. Or query database: duckdb data/equity_bias.duckdb")


if __name__ == "__main__":
    main()

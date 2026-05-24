"""
Generate synthetic patient data with intentional bias patterns.

Supports two modes:
1. LOCAL: Python-based generation (good for small datasets <1M records)
2. SPARK: Databricks Spark SQL generation (for massive scale millions/billions)

Usage:
    # Local generation (10k records)
    python scripts/generate_synthetic_data.py --n-patients 10000 --mode local

    # Databricks Spark generation (1 million records, safe for free tier)
    python scripts/generate_synthetic_data.py --n-patients 1000000 --mode spark

    # Databricks Spark generation (100 million records)
    python scripts/generate_synthetic_data.py --n-patients 100000000 --mode spark
"""
import sys
import os
import logging
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config_loader import load_config
from dotenv import load_dotenv

load_dotenv('.env.databricks')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_local(n_patients: int, output_dir: str):
    """Generate synthetic data locally (Python-based, good for <1M records)."""
    from src.data.bronze.synthetic_generator import SyntheticDataGenerator

    logger.info(f"Generating {n_patients:,} synthetic patients locally...")

    config = load_config()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gen = SyntheticDataGenerator(config)
    patients, decisions, outcomes = gen.generate(n_patients)

    import pandas as pd

    patients_df = pd.DataFrame([p.dict() for p in patients])
    decisions_df = pd.DataFrame([d.dict() for d in decisions])
    outcomes_df = pd.DataFrame([o.dict() for o in outcomes])

    patients_file = output_dir / f"synthetic_patients_{n_patients}.parquet"
    decisions_file = output_dir / f"synthetic_decisions_{n_patients}.parquet"
    outcomes_file = output_dir / f"synthetic_outcomes_{n_patients}.parquet"

    patients_df.to_parquet(patients_file, index=False)
    decisions_df.to_parquet(decisions_file, index=False)
    outcomes_df.to_parquet(outcomes_file, index=False)

    logger.info(f"Saved {len(patients_df):,} patients to {patients_file}")
    logger.info(f"Saved {len(decisions_df):,} decisions to {decisions_file}")
    logger.info(f"Saved {len(outcomes_df):,} outcomes to {outcomes_file}")

    return True


def generate_spark(n_patients: int):
    """Generate synthetic data directly in Databricks using Spark SQL (millions/billions scale)."""
    from databricks.sql import connect

    logger.info(f"Generating {n_patients:,} synthetic patients in Databricks Spark...")

    # Connect to Databricks
    host = os.getenv('DATABRICKS_HOST')
    token = os.getenv('DATABRICKS_TOKEN')
    http_path = os.getenv('DATABRICKS_HTTP_PATH')
    # Use 'main' catalog for Community Edition (default doesn't exist)
    catalog = 'main'

    logger.info(f"Connecting to Databricks: {host}")

    conn = connect(
        server_hostname=host.replace('https://', ''),
        http_path=http_path,
        personal_access_token=token
    )

    cursor = conn.cursor()

    # Create bronze schema if not exists
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {catalog}.healthcare_equity_bronze")

    # Generate patients at scale using Spark SQL
    logger.info("Creating bronze_patients_raw table...")
    cursor.execute(f"""
    CREATE OR REPLACE TABLE {catalog}.healthcare_equity_bronze.bronze_patients_raw AS
    WITH RECURSIVE cnt(x) AS (
        SELECT 1
        UNION ALL
        SELECT x+1 FROM cnt WHERE x < {n_patients}
    )
    SELECT
        CONCAT('PAT', LPAD(x, 8, '0')) as patient_id,
        CASE WHEN rand() < 0.5 THEN 'M' ELSE 'F' END as gender,
        CASE
            WHEN rand() < 0.12 THEN 'Black'
            WHEN rand() < 0.19 THEN 'Hispanic'
            WHEN rand() < 0.05 THEN 'AIAN'
            WHEN rand() < 0.03 THEN 'Asian'
            ELSE 'White'
        END as race,
        CASE WHEN rand() < 0.05 THEN 'LGBTQ' ELSE 'Heterosexual' END as sexual_orientation,
        (18 + int(rand() * 75)) as age,
        CASE
            WHEN rand() < 0.2 THEN 'Medicaid'
            WHEN rand() < 0.3 THEN 'Medicare'
            WHEN rand() < 0.4 THEN 'Commercial'
            ELSE 'Uninsured'
        END as insurance_type,
        CASE WHEN rand() < 0.3 THEN 1 ELSE 0 END as has_comorbidity,
        int(rand() * 5) as cci_score,
        int(rand() * 24) as sofa_score,
        int(rand() * 5 + 1) as ses_quintile,
        CASE
            WHEN int(rand() * 24) >= 20 THEN 'CRITICAL'
            WHEN int(rand() * 24) >= 15 THEN 'HIGH'
            WHEN int(rand() * 24) >= 10 THEN 'MEDIUM'
            ELSE 'LOW'
        END as risk_tier,
        current_timestamp() as admission_date
    FROM cnt
    """)

    logger.info(f"Created bronze_patients_raw with {n_patients:,} records")

    # Generate treatment decisions
    logger.info("Creating bronze_treatment_decisions_raw table...")
    cursor.execute(f"""
    CREATE OR REPLACE TABLE {catalog}.healthcare_equity_bronze.bronze_treatment_decisions_raw AS
    WITH RECURSIVE cnt(x) AS (
        SELECT 1
        UNION ALL
        SELECT x+1 FROM cnt WHERE x < {int(n_patients * 1.5)}
    )
    SELECT
        CONCAT('DEC', LPAD(x, 8, '0')) as decision_id,
        CONCAT('PAT', LPAD(int(rand() * {n_patients}) + 1, 8, '0')) as patient_id,
        CASE
            WHEN rand() < 0.25 THEN 'cardiac_catheterization'
            WHEN rand() < 0.50 THEN 'pain_management'
            WHEN rand() < 0.75 THEN 'mental_health_referral'
            ELSE 'hospital_admission'
        END as scenario_type,
        CASE WHEN rand() < 0.5 THEN 'Recommended' ELSE 'Not Recommended' END as decision,
        current_timestamp() as decision_date
    FROM cnt
    """)

    logger.info(f"Created bronze_treatment_decisions_raw with {int(n_patients * 1.5):,} records")

    # Generate outcomes
    logger.info("Creating bronze_outcomes_raw table...")
    cursor.execute(f"""
    CREATE OR REPLACE TABLE {catalog}.healthcare_equity_bronze.bronze_outcomes_raw AS
    WITH RECURSIVE cnt(x) AS (
        SELECT 1
        UNION ALL
        SELECT x+1 FROM cnt WHERE x < {int(n_patients * 0.8)}
    )
    SELECT
        CONCAT('OUT', LPAD(x, 8, '0')) as outcome_id,
        CONCAT('PAT', LPAD(int(rand() * {n_patients}) + 1, 8, '0')) as patient_id,
        CONCAT('DEC', LPAD(int(rand() * {int(n_patients * 1.5)}) + 1, 8, '0')) as decision_id,
        CASE WHEN rand() < 0.85 THEN 'Success' WHEN rand() < 0.95 THEN 'Complication' ELSE 'Failure' END as outcome_type,
        CASE WHEN rand() < 0.92 THEN 0 ELSE 1 END as thirty_day_readmission,
        CASE WHEN rand() < 0.97 THEN 0 ELSE 1 END as in_hospital_mortality,
        current_timestamp() as outcome_date
    FROM cnt
    """)

    logger.info(f"Created bronze_outcomes_raw with {int(n_patients * 0.8):,} records")

    cursor.close()
    conn.close()

    logger.info(f"SUCCESS: Generated {n_patients:,} synthetic records in Databricks")
    return True


def main():
    """Generate synthetic data."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic patient data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Local generation (10k patients)
  python scripts/generate_synthetic_data.py --n-patients 10000 --mode local

  # Databricks Spark generation (1M patients - safe for free tier)
  python scripts/generate_synthetic_data.py --n-patients 1000000 --mode spark

  # Databricks Spark generation (100M patients)
  python scripts/generate_synthetic_data.py --n-patients 100000000 --mode spark
        """
    )
    parser.add_argument("--n-patients", type=int, default=1000000,
                        help="Number of patients to generate (default: 1M)")
    parser.add_argument("--mode", type=str, default="spark", choices=["local", "spark"],
                        help="Generation mode: 'local' (Python) or 'spark' (Databricks)")
    parser.add_argument("--output-dir", type=str, default="data",
                        help="Output directory (local mode only)")
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("Healthcare Equity Bias Detection — Synthetic Data Generation")
    logger.info("=" * 70)
    logger.info(f"Mode: {args.mode.upper()}")
    logger.info(f"Records: {args.n_patients:,}")

    try:
        if args.mode == "local":
            success = generate_local(args.n_patients, args.output_dir)
        else:  # spark
            success = generate_spark(args.n_patients)

        if success:
            logger.info("=" * 70)
            logger.info("Data generation complete!")
            logger.info("=" * 70)
            return 0
    except Exception as e:
        logger.error(f"Error generating data: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""
Comprehensive system test script.

Tests all components end-to-end:
1. Configuration loading
2. Synthetic data generation
3. ETL pipeline
4. DuckDB storage
5. Statistical bias detection
6. Claude AI integration
"""
import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'


def test_configuration():
    """Test configuration loading."""
    logger.info(f"{BLUE}[TEST 1] Configuration Loading{RESET}")
    try:
        from config_loader import load_config, load_bias_thresholds
        config = load_config()
        thresholds = load_bias_thresholds()

        assert "anthropic" in config, "Missing anthropic config"
        assert "data" in config, "Missing data config"
        assert "bias_detection" in config, "Missing bias_detection config"
        assert "database" in config, "Missing database config"

        logger.info(f"{GREEN}✓ Configuration loaded successfully{RESET}")
        return True
    except Exception as e:
        logger.error(f"{RED}✗ Configuration test failed: {e}{RESET}")
        return False


def test_api_key():
    """Test API key is configured."""
    logger.info(f"{BLUE}[TEST 2] API Key Configuration{RESET}")
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        if not api_key.startswith("sk-ant-"):
            raise ValueError("API key does not look valid (should start with sk-ant-)")

        # Mask the key for display
        masked_key = api_key[:20] + "..." + api_key[-10:]
        logger.info(f"{GREEN}✓ API key configured: {masked_key}{RESET}")
        return True
    except Exception as e:
        logger.error(f"{RED}✗ API key test failed: {e}{RESET}")
        return False


def test_synthetic_data_generation():
    """Test synthetic data generation."""
    logger.info(f"{BLUE}[TEST 3] Synthetic Data Generation{RESET}")
    try:
        from src.data.bronze.synthetic_generator import SyntheticDataGenerator
        from config_loader import load_config

        config = load_config()
        gen = SyntheticDataGenerator(config)

        logger.info("  Generating 100 patient records (sample)...")
        patients, decisions, outcomes = gen.generate(100)

        assert len(patients) == 100, f"Expected 100 patients, got {len(patients)}"
        assert len(decisions) > 0, "No decisions generated"
        assert len(outcomes) == 100, f"Expected 100 outcomes, got {len(outcomes)}"

        logger.info(f"{GREEN}✓ Generated 100 patients, {len(decisions)} decisions, {len(outcomes)} outcomes{RESET}")
        return True
    except Exception as e:
        logger.error(f"{RED}✗ Data generation test failed: {e}{RESET}")
        return False


def test_etl_pipeline():
    """Test ETL transformation."""
    logger.info(f"{BLUE}[TEST 4] ETL Pipeline{RESET}")
    try:
        from src.data.bronze.synthetic_generator import SyntheticDataGenerator
        from src.data.silver.etl_pipeline import ETLPipeline
        from config_loader import load_config

        config = load_config()
        gen = SyntheticDataGenerator(config)
        patients, decisions, outcomes = gen.generate(50)

        etl = ETLPipeline(config)
        processed_patients, processed_decisions, processed_outcomes = etl.run_full_pipeline(
            patients, decisions, outcomes
        )

        assert len(processed_patients) == 50, f"ETL lost patients"

        logger.info(f"{GREEN}✓ ETL pipeline transformed 50 records successfully{RESET}")
        return True
    except Exception as e:
        logger.error(f"{RED}✗ ETL test failed: {e}{RESET}")
        return False


def test_duckdb():
    """Test DuckDB storage."""
    logger.info(f"{BLUE}[TEST 5] DuckDB Storage{RESET}")
    try:
        from src.storage.database import DuckDBInterface
        import tempfile

        # Use temp database for testing
        with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as f:
            temp_db = f.name

        db = DuckDBInterface(temp_db)
        db.init_schema()

        # Verify tables exist
        tables = db.conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()
        table_names = [t[0] for t in tables]

        assert "patients" in table_names, "patients table not created"
        assert "treatment_decisions" in table_names, "treatment_decisions table not created"
        assert "bias_metrics" in table_names, "bias_metrics table not created"

        db.close()
        os.unlink(temp_db)

        logger.info(f"{GREEN}✓ DuckDB initialized with {len(table_names)} tables{RESET}")
        return True
    except Exception as e:
        logger.error(f"{RED}✗ DuckDB test failed: {e}{RESET}")
        return False


def test_statistical_tests():
    """Test bias detection statistics."""
    logger.info(f"{BLUE}[TEST 6] Statistical Bias Detection{RESET}")
    try:
        from src.detection.statistical_tests import BiasStatisticalTests
        from config_loader import load_config
        import pandas as pd
        import numpy as np

        config = load_config()
        stat_tests = BiasStatisticalTests(config)

        # Create sample data
        np.random.seed(42)
        df = pd.DataFrame({
            'race': np.random.choice(['white', 'black'], 200),
            'treatment_received': np.random.choice([0, 1], 200),
        })

        # Inject bias manually
        df.loc[df['race'] == 'black', 'treatment_received'] = np.random.binomial(1, 0.6, sum(df['race'] == 'black'))
        df.loc[df['race'] == 'white', 'treatment_received'] = np.random.binomial(1, 0.85, sum(df['race'] == 'white'))

        # Calculate DIR
        metric = stat_tests.disparate_impact_ratio(
            df,
            outcome_col='treatment_received',
            group_col='race',
            reference_group='white',
            comparison_group='black'
        )

        logger.info(f"  DIR: {metric.metric_value:.3f}, p-value: {metric.p_value:.4f}, Severity: {metric.severity.value}")
        logger.info(f"{GREEN}✓ Statistical tests working correctly{RESET}")
        return True
    except Exception as e:
        logger.error(f"{RED}✗ Statistical test failed: {e}{RESET}")
        return False


def test_claude_api():
    """Test Claude API integration."""
    logger.info(f"{BLUE}[TEST 7] Claude API Integration{RESET}")
    try:
        from src.ai.claude_client import ClaudeHealthcareClient
        from src.models import BiasMetric, SeverityLevel
        from config_loader import load_config
        from datetime import datetime

        config = load_config()
        claude = ClaudeHealthcareClient(config)

        # Create test metric
        test_metric = BiasMetric(
            scenario_type="cardiac_catheterization",
            demographic_dimension="race",
            reference_group="white",
            comparison_group="black_or_african_american",
            metric_name="disparate_impact_ratio",
            metric_value=0.62,
            confidence_interval_lower=0.55,
            confidence_interval_upper=0.69,
            p_value=0.0001,
            is_significant=True,
            severity=SeverityLevel.SEVERE,
            sample_size=500,
            reference_group_rate=0.85,
            comparison_group_rate=0.53,
            calculation_date=datetime.utcnow()
        )

        logger.info("  Calling Claude API for bias analysis...")
        analysis = claude.analyze_bias([test_metric])

        assert len(analysis) > 100, "Claude response too short"
        assert "ROOT CAUSE" in analysis or "root cause" in analysis.lower(), "Missing root cause analysis"

        logger.info(f"{GREEN}✓ Claude API working. Generated {len(analysis)} character analysis{RESET}")
        return True
    except Exception as e:
        logger.error(f"{RED}✗ Claude API test failed: {e}{RESET}")
        return False


def main():
    """Run all tests."""
    logger.info("=" * 70)
    logger.info("Healthcare Equity Bias Detection — System Test Suite")
    logger.info("=" * 70)

    tests = [
        ("Configuration", test_configuration),
        ("API Key", test_api_key),
        ("Data Generation", test_synthetic_data_generation),
        ("ETL Pipeline", test_etl_pipeline),
        ("DuckDB Storage", test_duckdb),
        ("Statistical Tests", test_statistical_tests),
        ("Claude API", test_claude_api),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"Unexpected error in {name}: {e}")
            results.append((name, False))
        logger.info("")

    # Summary
    logger.info("=" * 70)
    logger.info("Test Summary:")
    logger.info("=" * 70)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
        logger.info(f"  {name}: {status}")

    logger.info("")
    logger.info(f"Results: {GREEN}{passed}/{total} tests passed{RESET}")

    if passed == total:
        logger.info(f"{GREEN}{'=' * 70}{RESET}")
        logger.info(f"{GREEN}✓ All tests passed! System is ready.{RESET}")
        logger.info(f"{GREEN}{'=' * 70}{RESET}")
        return 0
    else:
        logger.error(f"{RED}Some tests failed. Fix issues before proceeding.{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

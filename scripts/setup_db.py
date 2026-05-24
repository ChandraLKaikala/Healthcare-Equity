"""
Initialize DuckDB database schema.

Run this script once to set up the database:
    python scripts/setup_db.py
"""
import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import DuckDBInterface
from config_loader import load_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Initialize database."""
    logger.info("Healthcare Equity Bias Detection — Database Setup")
    logger.info("=" * 60)

    config = load_config()
    db_path = config.get("database", {}).get("path", "data/equity_bias.duckdb")

    logger.info(f"Initializing database at: {db_path}")

    db = DuckDBInterface(db_path)
    db.init_schema()
    db.close()

    logger.info("✓ Database initialized successfully!")
    logger.info("Next steps:")
    logger.info("  1. python scripts/generate_synthetic_data.py")
    logger.info("  2. python scripts/run_full_pipeline.py")
    logger.info("  3. streamlit run dashboard/app.py")


if __name__ == "__main__":
    main()

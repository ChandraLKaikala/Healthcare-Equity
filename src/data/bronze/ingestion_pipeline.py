"""
Bronze Layer Ingestion Pipeline.

Orchestrates raw data ingestion from various sources (synthetic, MIMIC-III, etc.)
"""
import logging
from typing import List, Tuple, Optional
import os

from .synthetic_generator import SyntheticDataGenerator
from .mimic_loader import MIMICIIILoader
from ..models import RawPatientRecord, RawTreatmentDecision, RawOutcome

logger = logging.getLogger(__name__)


class IngestPipeline:
    """Orchestrates data ingestion for Bronze layer."""

    def __init__(self, config: dict):
        self.config = config
        self.synthetic_gen = SyntheticDataGenerator(config)
        mimic_path = os.getenv("MIMIC_DATA_PATH")
        self.mimic_loader = MIMICIIILoader(mimic_path) if mimic_path else None

    def ingest(
        self,
        source: str = "synthetic",
        n_patients: int = 10000,
    ) -> Tuple[List[RawPatientRecord], List[RawTreatmentDecision], List[RawOutcome]]:
        """
        Ingest data from specified source.

        Args:
            source: "synthetic" or "mimic"
            n_patients: Number of patients (for synthetic)

        Returns:
            Tuple of (patients, decisions, outcomes)
        """
        if source == "synthetic":
            return self.synthetic_gen.generate(n_patients)
        elif source == "mimic":
            if not self.mimic_loader:
                raise ValueError("MIMIC_DATA_PATH not set in environment")
            logger.info("Loading MIMIC-III data...")
            patients_df = self.mimic_loader.load_patients()
            admissions_df = self.mimic_loader.load_admissions()
            labs_df = self.mimic_loader.load_labevents()
            procedures_df = self.mimic_loader.load_procedures()

            return self.mimic_loader.convert_to_raw_records(
                patients_df, admissions_df, labs_df, procedures_df
            )
        else:
            raise ValueError(f"Unknown data source: {source}")

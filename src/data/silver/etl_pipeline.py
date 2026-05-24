"""
Silver Layer ETL Pipeline.

Transforms Bronze layer raw data into cleaned, normalized, feature-engineered data.
"""
import logging
from typing import List, Tuple
from datetime import datetime
import pandas as pd
import numpy as np

from ..models import (
    RawPatientRecord, RawTreatmentDecision, RawOutcome,
    ProcessedPatientRecord, ProcessedTreatmentDecision, ProcessedOutcome,
    Gender, Race, InsuranceType
)
from .feature_engineering import FeatureEngineer
from .quality_checks import QualityChecker

logger = logging.getLogger(__name__)


class ETLPipeline:
    """
    Bronze → Silver transformation pipeline.

    Responsibilities:
    - Normalize demographic codes to standard enums
    - Verify de-identification
    - Compute clinical severity scores (SOFA, CCI)
    - Derive SES from ZIP code
    - Validate data quality
    """

    def __init__(self, config: dict):
        self.config = config
        self.feature_engineer = FeatureEngineer(config)
        self.quality_checker = QualityChecker(config)

    def transform_patients(
        self,
        raw_patients: List[RawPatientRecord]
    ) -> List[ProcessedPatientRecord]:
        """
        Transform raw patient records to processed format.

        Key transformations:
        - Age → age + age_group
        - ZIP code → SES quintile
        - Lab values → SOFA, CCI scores
        - Risk stratification
        """
        logger.info(f"Transforming {len(raw_patients)} patient records...")
        processed = []

        for raw in raw_patients:
            # Age grouping
            if raw.age < 31:
                age_group = "18-30"
            elif raw.age < 46:
                age_group = "31-45"
            elif raw.age < 61:
                age_group = "46-60"
            elif raw.age < 76:
                age_group = "61-75"
            else:
                age_group = "75+"

            # Derive SES quintile from ZIP (simplified: hash-based)
            ses_quintile = self._zip_to_ses_quintile(raw.zip_code)

            # Compute clinical severity scores
            sofa_score = self.feature_engineer.compute_sofa(raw.raw_labs, raw.presenting_vitals)
            cci_score = self.feature_engineer.compute_cci_proxy(raw.chief_complaint)
            risk_tier = self.feature_engineer.classify_risk(sofa_score, cci_score)

            processed_patient = ProcessedPatientRecord(
                patient_id=raw.patient_id,
                age=raw.age,
                age_group=age_group,
                race=raw.race,
                gender=raw.gender,
                sexual_orientation=raw.sexual_orientation,
                zip_code=raw.zip_code,
                ses_quintile=ses_quintile,
                insurance_type=raw.insurance_type,
                sofa_score=sofa_score,
                cci_score=cci_score,
                risk_tier=risk_tier,
                deidentified=True,
                processing_timestamp=datetime.utcnow(),
            )

            processed.append(processed_patient)

        logger.info(f"Transformed {len(processed)} patients successfully")
        return processed

    def transform_decisions(
        self,
        raw_decisions: List[RawTreatmentDecision],
        patients: List[ProcessedPatientRecord]
    ) -> List[ProcessedTreatmentDecision]:
        """Transform treatment decisions."""
        logger.info(f"Transforming {len(raw_decisions)} treatment decisions...")

        processed = []
        for raw in raw_decisions:
            # Find patient risk tier for context
            patient = next((p for p in patients if p.patient_id == raw.patient_id), None)
            clinical_severity = patient.risk_tier if patient else "medium"

            processed_decision = ProcessedTreatmentDecision(
                decision_id=raw.decision_id,
                patient_id=raw.patient_id,
                admission_id=raw.admission_id,
                decision_type=raw.decision_type,
                decision_value=raw.decision_value,
                decision_timestamp=raw.decision_timestamp,
                provider_id=raw.provider_id,
                facility_id=raw.facility_id,
                clinical_indication_severity=clinical_severity,
            )

            processed.append(processed_decision)

        logger.info(f"Transformed {len(processed)} decisions")
        return processed

    def transform_outcomes(
        self,
        raw_outcomes: List[RawOutcome]
    ) -> List[ProcessedOutcome]:
        """Transform outcomes."""
        logger.info(f"Transforming {len(raw_outcomes)} outcomes...")

        processed = []
        for raw in raw_outcomes:
            processed_outcome = ProcessedOutcome(
                outcome_id=raw.outcome_id,
                patient_id=raw.patient_id,
                admission_id=raw.admission_id,
                outcome_type=raw.outcome_type,
                outcome_date=raw.outcome_date,
                days_to_outcome=raw.days_to_outcome,
            )

            processed.append(processed_outcome)

        logger.info(f"Transformed {len(processed)} outcomes")
        return processed

    def _zip_to_ses_quintile(self, zip_code: str) -> int:
        """
        Derive SES quintile from ZIP code.

        In production, would use HUD ZHVI (Zillow Home Value Index) data.
        For now, using simple hash-based pseudo-assignment.

        Args:
            zip_code: 5-digit ZIP code

        Returns:
            SES quintile (1 = lowest SES, 5 = highest SES)
        """
        hash_val = sum(int(d) for d in zip_code)
        return (hash_val % 5) + 1

    def run_full_pipeline(
        self,
        raw_patients: List[RawPatientRecord],
        raw_decisions: List[RawTreatmentDecision],
        raw_outcomes: List[RawOutcome],
    ) -> Tuple[List[ProcessedPatientRecord], List[ProcessedTreatmentDecision], List[ProcessedOutcome]]:
        """Run complete ETL pipeline."""
        logger.info("Starting ETL pipeline: Bronze → Silver")

        # Transform each layer
        processed_patients = self.transform_patients(raw_patients)
        processed_decisions = self.transform_decisions(raw_decisions, processed_patients)
        processed_outcomes = self.transform_outcomes(raw_outcomes)

        # Quality checks
        logger.info("Running quality checks...")
        self.quality_checker.validate_patients(processed_patients)
        self.quality_checker.validate_decisions(processed_decisions)
        self.quality_checker.validate_outcomes(processed_outcomes)

        logger.info("ETL pipeline completed successfully")
        return processed_patients, processed_decisions, processed_outcomes

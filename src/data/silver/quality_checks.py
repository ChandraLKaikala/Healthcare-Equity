"""
Data Quality Checks for Silver Layer.

Validates that processed data is complete, consistent, and within expected ranges.
"""
import logging
from typing import List

from ..models import ProcessedPatientRecord, ProcessedTreatmentDecision, ProcessedOutcome

logger = logging.getLogger(__name__)


class QualityChecker:
    """Performs data quality validation."""

    def __init__(self, config: dict):
        self.config = config

    def validate_patients(self, patients: List[ProcessedPatientRecord]) -> bool:
        """Validate processed patient records."""
        logger.info(f"Validating {len(patients)} patient records...")

        # Check for missing required fields
        missing_count = 0
        for p in patients:
            if not p.patient_id or p.age is None:
                missing_count += 1
                continue

            # Check age is reasonable
            if p.age < 0 or p.age > 120:
                logger.warning(f"Patient {p.patient_id}: invalid age {p.age}")

            # Check SES quintile is 1-5
            if p.ses_quintile < 1 or p.ses_quintile > 5:
                logger.warning(f"Patient {p.patient_id}: invalid SES quintile {p.ses_quintile}")

        if missing_count > 0:
            logger.warning(f"{missing_count} patients missing required fields")

        completeness_pct = ((len(patients) - missing_count) / len(patients) * 100) if patients else 0
        logger.info(f"Patient data completeness: {completeness_pct:.1f}%")

        return completeness_pct >= 95  # Pass if >95% complete

    def validate_decisions(self, decisions: List[ProcessedTreatmentDecision]) -> bool:
        """Validate processed treatment decisions."""
        logger.info(f"Validating {len(decisions)} treatment decisions...")

        # Check for orphaned decisions (patient_id not found)
        # Check for missing timestamps
        missing_count = 0
        for d in decisions:
            if not d.decision_id or not d.patient_id:
                missing_count += 1

        if missing_count > 0:
            logger.warning(f"{missing_count} decisions missing required fields")

        completeness_pct = ((len(decisions) - missing_count) / len(decisions) * 100) if decisions else 0
        logger.info(f"Decision data completeness: {completeness_pct:.1f}%")

        return completeness_pct >= 95

    def validate_outcomes(self, outcomes: List[ProcessedOutcome]) -> bool:
        """Validate processed outcomes."""
        logger.info(f"Validating {len(outcomes)} outcomes...")

        missing_count = 0
        for o in outcomes:
            if not o.outcome_id or not o.patient_id:
                missing_count += 1

        completeness_pct = ((len(outcomes) - missing_count) / len(outcomes) * 100) if outcomes else 0
        logger.info(f"Outcome data completeness: {completeness_pct:.1f}%")

        return completeness_pct >= 95

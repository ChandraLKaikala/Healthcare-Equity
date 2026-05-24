"""
Feature Engineering for Clinical Data.

Computes clinical severity scores (SOFA, Charlson Comorbidity Index, etc.)
that serve as statistical controls when detecting bias.

These scores MUST be computed independently from demographic characteristics,
otherwise they would mask real biases.
"""
import logging
from typing import Dict, Optional

from ..models import RiskTier

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Computes clinical features and severity scores."""

    def __init__(self, config: Dict):
        self.config = config

    def compute_sofa(self, labs: Dict[str, float], vitals: Dict[str, float]) -> Optional[float]:
        """
        Compute Sequential Organ Failure Assessment (SOFA) score.

        SOFA is a severity scale with point assignments for dysfunction in 6 organ systems:
        1. Respiration (PaO2/FiO2)
        2. Coagulation (Platelets)
        3. Liver (Bilirubin)
        4. Cardiovascular (hypotension)
        5. Central Nervous System (GCS)
        6. Renal (Creatinine)

        Score ranges 0-24 (higher = more severe).

        For this implementation, we use available labs to estimate.
        """
        if not labs or not vitals:
            return None

        sofa = 0.0

        # Respiratory component (using estimated based on vital signs)
        rr = vitals.get("respiratory_rate", 16)
        if rr > 20:
            sofa += 1
        if rr > 25:
            sofa += 1

        # Cardiovascular component (using blood pressure)
        systolic = vitals.get("systolic_bp", 120)
        if systolic < 90:
            sofa += 1
        if systolic < 70:
            sofa += 2

        # Renal component (using creatinine as proxy)
        creatinine = labs.get("creatinine", 0.7)
        if creatinine > 1.2:
            sofa += 1
        if creatinine > 2.0:
            sofa += 2

        # Liver component (using glucose as proxy for hepatic function)
        glucose = labs.get("glucose", 100)
        if glucose > 200:
            sofa += 1
        if glucose > 400:
            sofa += 2

        # Coagulation (using hemoglobin as proxy)
        hemoglobin = labs.get("hemoglobin", 12)
        if hemoglobin < 10:
            sofa += 1
        if hemoglobin < 8:
            sofa += 2

        return min(sofa, 24.0)  # Cap at 24

    def compute_cci_proxy(self, chief_complaint: str) -> float:
        """
        Compute Charlson Comorbidity Index (CCI) proxy.

        CCI predicts 10-year mortality based on comorbid conditions.
        Score: 0-37+ (higher = worse prognosis).

        We use chief complaint as a proxy since full diagnosis codes aren't available.
        In production, would parse actual diagnosis codes (ICD-10).
        """
        cci = 0.0

        # Map complaint keywords to CCI points
        complaint_lower = chief_complaint.lower()

        if any(word in complaint_lower for word in ["chest pain", "heart", "cardiac"]):
            cci += 2  # Myocardial infarction history

        if any(word in complaint_lower for word in ["shortness of breath", "breathing"]):
            cci += 1  # Pulmonary disease

        if any(word in complaint_lower for word in ["diabetes", "glucose"]):
            cci += 1  # Diabetes

        if any(word in complaint_lower for word in ["kidney", "renal", "creatinine"]):
            cci += 2  # Renal disease

        if any(word in complaint_lower for word in ["fever", "infection", "sepsis"]):
            cci += 1  # Infection

        return cci

    def classify_risk(self, sofa_score: Optional[float], cci_score: float) -> RiskTier:
        """
        Classify patient into risk tier based on severity scores.

        Risk classification is crucial: it's the clinical variable we CONTROL for
        when detecting bias. Ensuring risk tiers are assigned independently from
        demographics is essential.

        Risk Tier definitions:
        - LOW: SOFA ≤3, CCI ≤2
        - MEDIUM: SOFA 4-8 or CCI 3-5
        - HIGH: SOFA 9-15 or CCI 6-10
        - CRITICAL: SOFA ≥16 or CCI >10
        """
        if sofa_score is None:
            sofa_score = 0.0

        if sofa_score >= 16 or cci_score > 10:
            return RiskTier.CRITICAL
        elif sofa_score >= 9 or cci_score >= 6:
            return RiskTier.HIGH
        elif sofa_score >= 4 or cci_score >= 3:
            return RiskTier.MEDIUM
        else:
            return RiskTier.LOW

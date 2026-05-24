"""
Synthetic Patient Data Generator for Healthcare Equity Analysis.

Generates de-identified patient records with realistic demographic distributions
and intentionally injected bias patterns based on published medical literature.

The key insight: Clinical severity is assigned INDEPENDENTLY from demographic
characteristics, so bias appears DESPITE equal clinical need. This simulates
real-world disparities where bias compounds with legitimate clinical variation.
"""
import random
import logging
from typing import List, Tuple, Dict
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from ..models import (
    RawPatientRecord, RawTreatmentDecision, RawOutcome,
    Race, Gender, SexualOrientation, InsuranceType, DecisionType, OutcomeType
)

logger = logging.getLogger(__name__)


class SyntheticDataGenerator:
    """
    Generates synthetic patient records with bias injection based on published
    disparities in medical literature.

    Bias scenarios implemented:
    1. Cardiac catheterization: Black patients receive it 40% less (Schulman et al. 1999)
    2. Pain management: Women prescribed opioids 25% less (Hoffmann & Tarzian 2001)
    3. Mental health referral: LGBTQ+ patients referred 30% less
    4. Hospital admission: Low-SES patients admitted 35% less
    """

    def __init__(self, config: Dict):
        self.config = config
        self.synthetic_config = config.get("data", {}).get("synthetic", {})
        self.distributions = config.get("data", {}).get("synthetic_distributions", {})
        random.seed(self.synthetic_config.get("seed", 42))
        np.random.seed(self.synthetic_config.get("seed", 42))

    def generate(self, n_patients: int = 10000) -> Tuple[List[RawPatientRecord], List[RawTreatmentDecision], List[RawOutcome]]:
        """Generate full dataset with bias injection."""
        logger.info(f"Generating synthetic data for {n_patients} patients...")

        patients = self._generate_patients(n_patients)
        logger.info(f"Generated {len(patients)} patient records")

        decisions = self._generate_treatment_decisions(patients)
        logger.info(f"Generated {len(decisions)} treatment decisions")

        outcomes = self._generate_outcomes(patients)
        logger.info(f"Generated {len(outcomes)} outcome records")

        return patients, decisions, outcomes

    def _generate_patients(self, n: int) -> List[RawPatientRecord]:
        """Generate patient demographics and clinical baseline."""
        patients = []

        # Define demographic distributions
        age_groups = self.distributions.get("age_groups", {})
        race_dist = self.distributions.get("race_distribution", {})
        gender_dist = self.distributions.get("gender_distribution", {})
        insurance_dist = self.distributions.get("insurance_distribution", {})

        race_options = list(Race)
        gender_options = list(Gender)
        insurance_options = list(InsuranceType)

        for i in range(n):
            # Demographics
            age = np.random.choice([20, 35, 50, 65, 80], p=[0.15, 0.25, 0.30, 0.20, 0.10])
            age += np.random.randint(0, 15)

            race = np.random.choice(race_options, p=[
                race_dist.get("white", 0.62),
                race_dist.get("black_or_african_american", 0.13),
                race_dist.get("hispanic_or_latino", 0.19),
                race_dist.get("asian", 0.04),
                race_dist.get("american_indian_or_alaska_native", 0.01),
                race_dist.get("native_hawaiian_or_pacific_islander", 0.00),
                race_dist.get("multiracial", 0.01),
                race_dist.get("other", 0.01),
                race_dist.get("unknown", 0.00),
            ])

            gender = np.random.choice(gender_options, p=[0.48, 0.52, 0.00, 0.00, 0.00, 0.00, 0.00])

            # Sexual orientation: mostly heterosexual
            if random.random() < 0.05:
                sexual_orientation = np.random.choice([SexualOrientation.GAY, SexualOrientation.LESBIAN,
                                                       SexualOrientation.BISEXUAL, SexualOrientation.OTHER])
            else:
                sexual_orientation = SexualOrientation.HETEROSEXUAL

            insurance = np.random.choice(insurance_options, p=[
                insurance_dist.get("private", 0.65),
                insurance_dist.get("medicare", 0.20),
                insurance_dist.get("medicaid", 0.10),
                insurance_dist.get("uninsured", 0.05),
                insurance_dist.get("other", 0.00),
            ])

            # Generate SES-correlated ZIP code (5-digit)
            zip_code = f"{random.randint(10000, 99999)}"

            # Clinical presentation (independent of demographics)
            chief_complaint = random.choice([
                "chest pain", "abdominal pain", "shortness of breath",
                "dizziness", "headache", "fatigue", "fever"
            ])

            vitals = {
                "heart_rate": random.randint(55, 120),
                "systolic_bp": random.randint(95, 180),
                "diastolic_bp": random.randint(50, 110),
                "temperature": round(random.uniform(36.2, 39.0), 1),
                "respiratory_rate": random.randint(10, 25),
            }

            labs = {
                "troponin": round(random.uniform(0.00, 0.20), 4),  # Will inject bias on high values
                "creatinine": round(random.uniform(0.5, 2.0), 2),
                "glucose": random.randint(70, 400),
                "hemoglobin": round(random.uniform(7, 16), 1),
            }

            admission_date = datetime.now() - timedelta(days=random.randint(0, 90))

            patient = RawPatientRecord(
                patient_id=f"PAT_{i:06d}",
                age=age,
                race=race,
                gender=gender,
                sexual_orientation=sexual_orientation,
                zip_code=zip_code,
                insurance_type=insurance,
                admission_date=admission_date,
                chief_complaint=chief_complaint,
                presenting_vitals=vitals,
                raw_labs=labs,
                raw_notes=f"Patient presents with {chief_complaint}. {random.choice(['Stable', 'Unstable', 'Improving'])} condition.",
                facility_id=f"FAC_{random.randint(1, 20):03d}",
                provider_id=f"PRV_{random.randint(1, 100):03d}",
            )

            patients.append(patient)

        return patients

    def _generate_treatment_decisions(self, patients: List[RawPatientRecord]) -> List[RawTreatmentDecision]:
        """
        Generate treatment decisions with bias injection.

        Key: Clinical indication (troponin level, pain score, etc.) is assigned
        INDEPENDENTLY, then bias is applied based on demographics.
        """
        decisions = []
        bias_scenarios = self.synthetic_config.get("bias_scenarios", {})

        for patient in patients:
            # Decision 1: Cardiac catheterization (for elevated troponin)
            troponin = patient.raw_labs.get("troponin", 0)
            if troponin > 0.04:  # Elevated troponin = medically indicated catheterization
                # Bias: Black patients get catheterized at 60% the rate of white patients
                base_rate = 0.85  # 85% of white patients with troponin elevation get catheterization

                if patient.race == Race.BLACK:
                    adjusted_rate = base_rate * 0.60  # 40% reduction (Schulman et al.)
                else:
                    adjusted_rate = base_rate

                if random.random() < adjusted_rate:
                    decisions.append(RawTreatmentDecision(
                        patient_id=patient.patient_id,
                        admission_id=patient.admission_id,
                        decision_type=DecisionType.PROCEDURE,
                        decision_value="cardiac_catheterization",
                        clinical_indication=f"Elevated troponin ({troponin:.4f} ng/mL)",
                        decision_timestamp=patient.admission_date + timedelta(hours=random.randint(1, 24)),
                        provider_id=patient.provider_id,
                        facility_id=patient.facility_id,
                    ))

            # Decision 2: Pain management (opioid prescription)
            pain_score = random.randint(4, 10)  # Simulated pain scale
            if pain_score >= 7:  # Severe pain
                # Bias: Women receive opioids at 75% the rate of men
                base_rate = 0.75  # 75% of men get opioids for severe pain

                if patient.gender == Gender.FEMALE:
                    adjusted_rate = base_rate * 0.75  # 25% reduction (Hoffmann & Tarzian)
                else:
                    adjusted_rate = base_rate

                if random.random() < adjusted_rate:
                    decisions.append(RawTreatmentDecision(
                        patient_id=patient.patient_id,
                        admission_id=patient.admission_id,
                        decision_type=DecisionType.MEDICATION,
                        decision_value="opioid_analgesic",
                        clinical_indication=f"Acute pain (scale {pain_score}/10)",
                        decision_timestamp=patient.admission_date + timedelta(hours=random.randint(1, 6)),
                        provider_id=patient.provider_id,
                        facility_id=patient.facility_id,
                    ))

            # Decision 3: Mental health referral
            phq9_score = random.randint(0, 27)  # PHQ-9 depression screening
            if phq9_score >= 10:  # Moderate depression
                # Bias: LGBTQ+ patients referred at 70% the rate of heterosexual patients
                base_rate = 0.70  # 70% of heterosexual patients get referred for depression

                is_lgbtq = patient.sexual_orientation != SexualOrientation.HETEROSEXUAL
                if is_lgbtq:
                    adjusted_rate = base_rate * 0.70  # 30% reduction
                else:
                    adjusted_rate = base_rate

                if random.random() < adjusted_rate:
                    decisions.append(RawTreatmentDecision(
                        patient_id=patient.patient_id,
                        admission_id=patient.admission_id,
                        decision_type=DecisionType.REFERRAL,
                        decision_value="mental_health_referral",
                        clinical_indication=f"Depression screening positive (PHQ-9 {phq9_score})",
                        decision_timestamp=patient.admission_date + timedelta(hours=random.randint(1, 48)),
                        provider_id=patient.provider_id,
                        facility_id=patient.facility_id,
                    ))

            # Decision 4: Hospital admission (for ED presentation)
            # Bias: Low-SES patients admitted at 65% the rate of high-SES
            acuity_score = random.randint(1, 10)
            if acuity_score >= 5:  # Moderate-to-high acuity
                # Derive SES quintile from ZIP (simplified: just use random, but biased by acuity)
                ses_quintile = 3 + random.randint(-2, 2)  # Could be improved with actual ZIP → SES mapping

                base_admission_rate = 0.70  # 70% of high-SES get admitted for acuity ≥5

                if ses_quintile == 1:  # Lowest SES
                    adjusted_rate = base_admission_rate * 0.65  # 35% reduction
                else:
                    adjusted_rate = base_admission_rate

                if random.random() < adjusted_rate:
                    decisions.append(RawTreatmentDecision(
                        patient_id=patient.patient_id,
                        admission_id=patient.admission_id,
                        decision_type=DecisionType.ADMISSION,
                        decision_value="hospital_admission",
                        clinical_indication=f"ED presentation, acuity {acuity_score}/10",
                        decision_timestamp=patient.admission_date,
                        provider_id=patient.provider_id,
                        facility_id=patient.facility_id,
                    ))

        return decisions

    def _generate_outcomes(self, patients: List[RawPatientRecord]) -> List[RawOutcome]:
        """Generate clinical outcomes (recovery, readmission, mortality)."""
        outcomes = []

        for patient in patients:
            outcome_type = random.choice([OutcomeType.RECOVERY, OutcomeType.READMISSION, OutcomeType.MORTALITY])

            if outcome_type == OutcomeType.RECOVERY:
                days_to_outcome = random.randint(1, 14)
                outcome_value = "recovered_without_complications"
            elif outcome_type == OutcomeType.READMISSION:
                days_to_outcome = random.randint(15, 90)
                outcome_value = f"readmitted_with_{random.choice(['same_diagnosis', 'different_diagnosis'])}"
            else:  # MORTALITY
                days_to_outcome = random.randint(1, 30)
                outcome_value = f"in_hospital_mortality"

            outcome = RawOutcome(
                patient_id=patient.patient_id,
                admission_id=patient.admission_id,
                outcome_type=outcome_type,
                outcome_value=outcome_value,
                outcome_date=patient.admission_date + timedelta(days=days_to_outcome),
                days_to_outcome=days_to_outcome,
            )

            outcomes.append(outcome)

        return outcomes

    def to_dataframe(self, patients: List[RawPatientRecord]) -> pd.DataFrame:
        """Convert patient records to pandas DataFrame for analysis."""
        data = []
        for p in patients:
            data.append({
                "patient_id": p.patient_id,
                "age": p.age,
                "race": p.race.value,
                "gender": p.gender.value,
                "sexual_orientation": p.sexual_orientation.value,
                "zip_code": p.zip_code,
                "insurance_type": p.insurance_type.value,
                "chief_complaint": p.chief_complaint,
                "troponin": p.raw_labs.get("troponin", 0),
                "facility_id": p.facility_id,
                "provider_id": p.provider_id,
            })
        return pd.DataFrame(data)

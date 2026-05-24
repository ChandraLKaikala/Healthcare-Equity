"""
DuckDB Database Interface for Gold Layer.

DuckDB is an embedded analytical database perfect for this use case:
- Fast OLAP queries for bias analysis
- In-process, no server needed
- Excellent pandas integration
- Perfect for data medallion architecture
"""
import logging
import duckdb
from typing import List, Dict, Optional
from pathlib import Path

from ..models import (
    ProcessedPatientRecord, ProcessedTreatmentDecision, ProcessedOutcome,
    BiasMetric, InterventionRecord, EquityReport
)

logger = logging.getLogger(__name__)


class DuckDBInterface:
    """Interface to DuckDB for Gold layer analytics."""

    def __init__(self, db_path: str = "data/equity_bias.duckdb"):
        """Initialize DuckDB connection."""
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        logger.info(f"Connected to DuckDB at {db_path}")

    def init_schema(self):
        """Initialize database schema."""
        logger.info("Initializing DuckDB schema...")

        # Silver layer tables
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id VARCHAR PRIMARY KEY,
                age INTEGER,
                age_group VARCHAR,
                race VARCHAR,
                gender VARCHAR,
                sexual_orientation VARCHAR,
                zip_code VARCHAR,
                ses_quintile INTEGER,
                insurance_type VARCHAR,
                sofa_score DOUBLE,
                cci_score DOUBLE,
                risk_tier VARCHAR,
                deidentified BOOLEAN,
                processing_timestamp TIMESTAMP
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS treatment_decisions (
                decision_id VARCHAR PRIMARY KEY,
                patient_id VARCHAR,
                admission_id VARCHAR,
                decision_type VARCHAR,
                decision_value VARCHAR,
                decision_timestamp TIMESTAMP,
                provider_id VARCHAR,
                facility_id VARCHAR,
                clinical_indication_severity VARCHAR
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS outcomes (
                outcome_id VARCHAR PRIMARY KEY,
                patient_id VARCHAR,
                admission_id VARCHAR,
                outcome_type VARCHAR,
                outcome_date TIMESTAMP,
                days_to_outcome INTEGER
            )
        """)

        # Gold layer tables
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS bias_metrics (
                metric_id VARCHAR PRIMARY KEY,
                scenario_type VARCHAR,
                demographic_dimension VARCHAR,
                reference_group VARCHAR,
                comparison_group VARCHAR,
                metric_name VARCHAR,
                metric_value DOUBLE,
                confidence_interval_lower DOUBLE,
                confidence_interval_upper DOUBLE,
                p_value DOUBLE,
                is_significant BOOLEAN,
                severity VARCHAR,
                sample_size INTEGER,
                reference_group_rate DOUBLE,
                comparison_group_rate DOUBLE,
                calculation_date TIMESTAMP,
                calculation_period VARCHAR
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS interventions (
                intervention_id VARCHAR PRIMARY KEY,
                scenario_type VARCHAR,
                bias_metric_id VARCHAR,
                facility_id VARCHAR,
                provider_id VARCHAR,
                intervention_type VARCHAR,
                intervention_description VARCHAR,
                root_cause_analysis VARCHAR,
                status VARCHAR,
                recommended_date TIMESTAMP,
                implemented_date TIMESTAMP,
                pre_bias_score DOUBLE,
                post_bias_score DOUBLE,
                is_effective BOOLEAN,
                ai_generated BOOLEAN,
                ai_model VARCHAR,
                ai_confidence DOUBLE
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS equity_reports (
                report_id VARCHAR PRIMARY KEY,
                facility_id VARCHAR,
                reporting_period VARCHAR,
                report_type VARCHAR,
                total_disparities_detected INTEGER,
                critical_disparities INTEGER,
                moderate_disparities INTEGER,
                interventions_recommended INTEGER,
                interventions_implemented INTEGER,
                intervention_effectiveness_pct DOUBLE,
                executive_summary VARCHAR,
                regulatory_framework VARCHAR,
                compliance_status VARCHAR,
                generated_date TIMESTAMP,
                generated_by_ai BOOLEAN
            )
        """)

        self.conn.commit()
        logger.info("Schema initialized successfully")

    def insert_patients(self, patients: List[ProcessedPatientRecord]):
        """Insert processed patient records."""
        data = []
        for p in patients:
            data.append({
                "patient_id": p.patient_id,
                "age": p.age,
                "age_group": p.age_group,
                "race": p.race.value,
                "gender": p.gender.value,
                "sexual_orientation": p.sexual_orientation.value,
                "zip_code": p.zip_code,
                "ses_quintile": p.ses_quintile,
                "insurance_type": p.insurance_type.value,
                "sofa_score": p.sofa_score,
                "cci_score": p.cci_score,
                "risk_tier": p.risk_tier.value,
                "deidentified": p.deidentified,
                "processing_timestamp": p.processing_timestamp,
            })

        self.conn.from_df(
            __import__("pandas").DataFrame(data)
        ).insert_into("patients")
        logger.info(f"Inserted {len(patients)} patient records")

    def insert_decisions(self, decisions: List[ProcessedTreatmentDecision]):
        """Insert processed treatment decisions."""
        data = []
        for d in decisions:
            data.append({
                "decision_id": d.decision_id,
                "patient_id": d.patient_id,
                "admission_id": d.admission_id,
                "decision_type": d.decision_type.value,
                "decision_value": d.decision_value,
                "decision_timestamp": d.decision_timestamp,
                "provider_id": d.provider_id,
                "facility_id": d.facility_id,
                "clinical_indication_severity": d.clinical_indication_severity.value,
            })

        self.conn.from_df(
            __import__("pandas").DataFrame(data)
        ).insert_into("treatment_decisions")
        logger.info(f"Inserted {len(decisions)} treatment decisions")

    def insert_outcomes(self, outcomes: List[ProcessedOutcome]):
        """Insert processed outcomes."""
        data = []
        for o in outcomes:
            data.append({
                "outcome_id": o.outcome_id,
                "patient_id": o.patient_id,
                "admission_id": o.admission_id,
                "outcome_type": o.outcome_type.value,
                "outcome_date": o.outcome_date,
                "days_to_outcome": o.days_to_outcome,
            })

        self.conn.from_df(
            __import__("pandas").DataFrame(data)
        ).insert_into("outcomes")
        logger.info(f"Inserted {len(outcomes)} outcomes")

    def insert_bias_metrics(self, metrics: List[BiasMetric]):
        """Insert computed bias metrics."""
        data = []
        for m in metrics:
            data.append({
                "metric_id": m.metric_id,
                "scenario_type": m.scenario_type,
                "demographic_dimension": m.demographic_dimension,
                "reference_group": m.reference_group,
                "comparison_group": m.comparison_group,
                "metric_name": m.metric_name,
                "metric_value": m.metric_value,
                "confidence_interval_lower": m.confidence_interval_lower,
                "confidence_interval_upper": m.confidence_interval_upper,
                "p_value": m.p_value,
                "is_significant": m.is_significant,
                "severity": m.severity.value,
                "sample_size": m.sample_size,
                "reference_group_rate": m.reference_group_rate,
                "comparison_group_rate": m.comparison_group_rate,
                "calculation_date": m.calculation_date,
                "calculation_period": m.calculation_period,
            })

        if data:
            self.conn.from_df(
                __import__("pandas").DataFrame(data)
            ).insert_into("bias_metrics")
            logger.info(f"Inserted {len(metrics)} bias metrics")

    def query_patients_by_demographic(self, demographic: str, value: str):
        """Query patients by demographic characteristic."""
        result = self.conn.execute(
            f"SELECT * FROM patients WHERE {demographic} = '{value}'"
        ).fetchall()
        return result

    def query_cardiac_cath_disparities(self):
        """Query cardiac catheterization disparities by race."""
        query = """
        SELECT
            p.race,
            COUNT(*) as total_with_elevated_troponin,
            SUM(CASE WHEN td.decision_value = 'cardiac_catheterization' THEN 1 ELSE 0 END) as received_catheterization,
            CAST(SUM(CASE WHEN td.decision_value = 'cardiac_catheterization' THEN 1 ELSE 0 END) as DOUBLE) /
            COUNT(*) as catheterization_rate
        FROM patients p
        LEFT JOIN treatment_decisions td ON p.patient_id = td.patient_id
        WHERE p.sofa_score >= 3  -- Clinical severity control
        GROUP BY p.race
        ORDER BY catheterization_rate DESC
        """
        return self.conn.execute(query).fetchall()

    def close(self):
        """Close database connection."""
        self.conn.close()
        logger.info("Database connection closed")

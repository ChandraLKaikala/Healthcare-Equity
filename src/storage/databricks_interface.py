"""
Databricks SQL Interface for Healthcare Equity System.

Replaces DuckDB for production Fortune 10 deployment.
Uses Databricks SQL Warehouse for fast analytical queries.
Integrates with Delta Live Tables (DLT) for data orchestration.
"""
import logging
import os
from typing import List, Optional
import pandas as pd
from databricks import sql

from ..models import (
    ProcessedPatientRecord, ProcessedTreatmentDecision, ProcessedOutcome,
    BiasMetric, InterventionRecord, EquityReport
)

logger = logging.getLogger(__name__)


class DatabricksInterface:
    """
    Databricks SQL interface for production healthcare equity analytics.

    Features:
    - Unity Catalog for multi-workspace governance
    - Delta tables with ACID transactions
    - Automatic schema evolution
    - Integrated with DLT pipelines
    - Built-in audit logging for HIPAA compliance
    """

    def __init__(self, config: dict):
        """
        Initialize Databricks connection.

        Requires environment variables:
        - DATABRICKS_HOST: Workspace URL (e.g., https://xxx.cloud.databricks.com)
        - DATABRICKS_TOKEN: Personal access token
        """
        self.config = config

        host = os.getenv("DATABRICKS_HOST")
        token = os.getenv("DATABRICKS_TOKEN")

        if not host or not token:
            raise ValueError(
                "DATABRICKS_HOST and DATABRICKS_TOKEN environment variables required. "
                "Get these from your Databricks workspace settings."
            )

        self.host = host
        self.token = token
        self.catalog = config.get("databricks", {}).get("catalog", "healthcare_data")
        self.conn = None
        self._connect()

    def _connect(self):
        """Establish connection to Databricks SQL Warehouse."""
        try:
            http_path = os.getenv("DATABRICKS_HTTP_PATH")
            if not http_path:
                raise ValueError("DATABRICKS_HTTP_PATH environment variable required")

            self.conn = sql.connect(
                server_hostname=self.host.replace("https://", ""),
                http_path=http_path,
                auth_type="pat",
                personal_access_token=self.token
            )

            logger.info(f"Connected to Databricks workspace: {self.host}")
        except Exception as e:
            logger.error(f"Failed to connect to Databricks: {e}")
            raise

    def init_schema(self):
        """Initialize database schema using Unity Catalog."""
        logger.info("Initializing Databricks schema...")

        cursor = self.conn.cursor()

        # Create databases (schemas) if they don't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.catalog}.raw_data")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.catalog}.processed_data")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.catalog}.analytics")

        # Create Bronze layer tables
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.catalog}.raw_data.bronze_patients (
                patient_id STRING NOT NULL,
                age INT,
                age_group STRING,
                race STRING,
                gender STRING,
                sexual_orientation STRING,
                zip_code STRING,
                insurance_type STRING,
                admission_date TIMESTAMP,
                chief_complaint STRING,
                presenting_vitals MAP<STRING, DOUBLE>,
                raw_labs MAP<STRING, DOUBLE>,
                raw_notes STRING,
                facility_id STRING,
                provider_id STRING
            )
            USING DELTA
            TBLPROPERTIES (
                'delta.enableChangeDataFeed' = 'true',
                'classification' = 'ehr_data',
                'retention_days' = '90'
            )
        """)

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.catalog}.raw_data.bronze_treatment_decisions (
                decision_id STRING NOT NULL,
                patient_id STRING NOT NULL,
                decision_type STRING,
                decision_value STRING,
                clinical_indication STRING,
                decision_timestamp TIMESTAMP,
                provider_id STRING,
                facility_id STRING,
                PRIMARY KEY(decision_id)
            )
            USING DELTA
            TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
        """)

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.catalog}.raw_data.bronze_outcomes (
                outcome_id STRING NOT NULL,
                patient_id STRING NOT NULL,
                outcome_type STRING,
                outcome_value STRING,
                outcome_date TIMESTAMP,
                days_to_outcome INT,
                PRIMARY KEY(outcome_id)
            )
            USING DELTA
        """)

        # Create Silver layer tables
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.catalog}.processed_data.silver_patients (
                patient_id STRING NOT NULL,
                age INT,
                age_group STRING,
                race STRING,
                gender STRING,
                sexual_orientation STRING,
                zip_code STRING,
                ses_quintile INT,
                insurance_type STRING,
                sofa_score DOUBLE,
                cci_score DOUBLE,
                risk_tier STRING,
                deidentified BOOLEAN,
                processing_timestamp TIMESTAMP
            )
            USING DELTA
            TBLPROPERTIES (
                'delta.enableChangeDataFeed' = 'true',
                'classification' = 'processed_ehr',
                'retention_days' = '365'
            )
        """)

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.catalog}.processed_data.silver_decisions (
                decision_id STRING NOT NULL,
                patient_id STRING NOT NULL,
                decision_type STRING,
                decision_value STRING,
                decision_timestamp TIMESTAMP,
                provider_id STRING,
                facility_id STRING,
                clinical_indication_severity STRING,
                PRIMARY KEY(decision_id)
            )
            USING DELTA
        """)

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.catalog}.processed_data.silver_outcomes (
                outcome_id STRING NOT NULL,
                patient_id STRING NOT NULL,
                outcome_type STRING,
                outcome_date TIMESTAMP,
                days_to_outcome INT,
                PRIMARY KEY(outcome_id)
            )
            USING DELTA
        """)

        # Create Gold layer tables
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.catalog}.analytics.gold_bias_metrics (
                metric_id STRING NOT NULL,
                scenario_type STRING,
                demographic_dimension STRING,
                reference_group STRING,
                comparison_group STRING,
                metric_name STRING,
                metric_value DOUBLE,
                confidence_interval_lower DOUBLE,
                confidence_interval_upper DOUBLE,
                p_value DOUBLE,
                is_significant BOOLEAN,
                severity STRING,
                sample_size INT,
                reference_group_rate DOUBLE,
                comparison_group_rate DOUBLE,
                calculation_date TIMESTAMP,
                calculation_period STRING,
                PRIMARY KEY(metric_id)
            )
            USING DELTA
            TBLPROPERTIES (
                'delta.enableChangeDataFeed' = 'true',
                'classification' = 'analytics',
                'retention_days' = '2555'
            )
        """)

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.catalog}.analytics.gold_interventions (
                intervention_id STRING NOT NULL,
                scenario_type STRING,
                bias_metric_id STRING,
                facility_id STRING,
                provider_id STRING,
                intervention_type STRING,
                intervention_description STRING,
                root_cause_analysis STRING,
                status STRING,
                recommended_date TIMESTAMP,
                implemented_date TIMESTAMP,
                pre_bias_score DOUBLE,
                post_bias_score DOUBLE,
                is_effective BOOLEAN,
                ai_generated BOOLEAN,
                ai_model STRING,
                ai_confidence DOUBLE,
                PRIMARY KEY(intervention_id)
            )
            USING DELTA
            TBLPROPERTIES (
                'delta.enableChangeDataFeed' = 'true',
                'ai_generated' = 'true'
            )
        """)

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.catalog}.analytics.gold_provider_accountability (
                provider_id STRING NOT NULL,
                facility_id STRING,
                equity_score DOUBLE,
                cardiac_catheterization_disparity DOUBLE,
                pain_management_disparity DOUBLE,
                mental_health_referral_disparity DOUBLE,
                hospital_admission_disparity DOUBLE,
                score_change_vs_prior_period DOUBLE,
                required_interventions ARRAY<STRING>,
                last_updated TIMESTAMP,
                PRIMARY KEY(provider_id, facility_id)
            )
            USING DELTA
            TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
        """)

        cursor.close()
        logger.info("Schema initialized successfully")

    def insert_patients(self, patients: List[ProcessedPatientRecord]):
        """Insert processed patient records into Silver layer."""
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

        df = pd.DataFrame(data)

        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM {self.catalog}.processed_data.silver_patients")  # Clear for demo

        # Use Databricks API to insert
        for _, row in df.iterrows():
            cursor.execute(
                f"""INSERT INTO {self.catalog}.processed_data.silver_patients
                   VALUES ('{row['patient_id']}', {row['age']}, '{row['age_group']}',
                           '{row['race']}', '{row['gender']}', '{row['sexual_orientation']}',
                           '{row['zip_code']}', {row['ses_quintile']}, '{row['insurance_type']}',
                           {row['sofa_score']}, {row['cci_score']}, '{row['risk_tier']}',
                           {row['deidentified']}, '{row['processing_timestamp']}')"""
            )

        cursor.close()
        logger.info(f"Inserted {len(patients)} patient records into Databricks")

    def insert_bias_metrics(self, metrics: List[BiasMetric]):
        """Insert computed bias metrics into Gold layer."""
        cursor = self.conn.cursor()

        for m in metrics:
            cursor.execute(f"""
                INSERT INTO {self.catalog}.analytics.gold_bias_metrics
                VALUES ('{m.metric_id}', '{m.scenario_type}', '{m.demographic_dimension}',
                        '{m.reference_group}', '{m.comparison_group}', '{m.metric_name}',
                        {m.metric_value}, {m.confidence_interval_lower},
                        {m.confidence_interval_upper}, {m.p_value}, {m.is_significant},
                        '{m.severity.value}', {m.sample_size}, {m.reference_group_rate},
                        {m.comparison_group_rate}, '{m.calculation_date}',
                        '{m.calculation_period}')
            """)

        cursor.close()
        logger.info(f"Inserted {len(metrics)} bias metrics")

    def query_bias_metrics(self, scenario_type: Optional[str] = None) -> pd.DataFrame:
        """Query bias metrics from Gold layer."""
        cursor = self.conn.cursor()

        if scenario_type:
            query = f"""
                SELECT * FROM {self.catalog}.analytics.gold_bias_metrics
                WHERE scenario_type = '{scenario_type}'
                ORDER BY calculation_date DESC
            """
        else:
            query = f"""
                SELECT * FROM {self.catalog}.analytics.gold_bias_metrics
                ORDER BY calculation_date DESC
            """

        result = cursor.execute(query).fetchall()
        cursor.close()

        return pd.DataFrame(result)

    def close(self):
        """Close Databricks connection."""
        if self.conn:
            self.conn.close()
            logger.info("Databricks connection closed")

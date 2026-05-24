#!/usr/bin/env python3
"""
Databricks Delta Live Tables (DLT) Pipeline Notebook
This notebook defines the complete data transformation from Bronze → Silver → Gold

To use in Databricks:
1. Create a new notebook
2. Copy this content
3. Create a DLT pipeline that uses this notebook
4. Set trigger to run every 5 minutes
"""

# IMPORTANT: This code is designed for Databricks notebooks
# The imports and magic commands work in Databricks environment

# %md
# # Healthcare Equity DLT Pipeline
# Transforms Bronze → Silver → Gold layers automatically

# COMMAND

import dlt
from pyspark.sql.functions import (
    col, when, round as spark_round, count, sum as spark_sum,
    min as spark_min, max as spark_max, current_timestamp, expr
)

# COMMAND

# %md
# ## Bronze Layer Sources
# Reading raw data that's continuously updated by continuous_data_pipeline.py

# COMMAND

@dlt.view
def bronze_patients():
    """Read raw patients from Bronze - auto-triggers on new data"""
    return spark.read.format("delta").table("healthcare_equity_bronze.patients")

@dlt.view
def bronze_decisions():
    """Read raw decisions from Bronze - auto-triggers on new data"""
    return spark.read.format("delta").table("healthcare_equity_bronze.decisions")

@dlt.view
def bronze_outcomes():
    """Read raw outcomes from Bronze"""
    return spark.read.format("delta").table("healthcare_equity_bronze.outcomes")

# COMMAND

# %md
# ## Silver Layer - Data Cleaning & Transformation
# Applies data quality checks and adds derived fields

# COMMAND

@dlt.table(
    comment="Processed patient records with clinical risk levels",
    table_properties={"delta.enableChangeDataFeed": "true"}
)
@dlt.expect_or_drop("valid_patient_id", "patient_id IS NOT NULL AND patient_id > 0")
def patients_processed():
    """
    Transform Bronze patients to Silver
    - Adds risk_level based on SOFA score
    - Adds age_group categorization
    - Tracks processing timestamp
    - Drops invalid records
    """
    return (
        dlt.read("bronze_patients")
        .select(
            col("patient_id"),
            col("gender"),
            col("race"),
            col("sexual_orientation"),
            col("age"),
            col("insurance_type"),
            col("sofa_score"),
            col("cci_score"),
            col("ses_quintile"),
            when(col("sofa_score") >= 15, "HIGH")
                .when(col("sofa_score") >= 10, "MEDIUM")
                .otherwise("LOW")
                .alias("risk_level"),
            when(col("age") < 30, "18-29")
                .when(col("age") < 45, "30-44")
                .when(col("age") < 65, "45-64")
                .otherwise("65+")
                .alias("age_group"),
            current_timestamp().alias("processed_at")
        )
    )

@dlt.table(
    comment="Processed decision records with binary decision flag",
    table_properties={"delta.enableChangeDataFeed": "true"}
)
@dlt.expect_or_drop("valid_decision", "decision_id IS NOT NULL AND decision_id > 0")
@dlt.expect_or_drop("valid_decision_value", "decision IN ('Recommended', 'Not Recommended')")
def decisions_processed():
    """
    Transform Bronze decisions to Silver
    - Adds decision_flag (1 for Recommended, 0 for Not Recommended)
    - Validates decision values
    - Tracks processing timestamp
    """
    return (
        dlt.read("bronze_decisions")
        .select(
            col("decision_id"),
            col("patient_id"),
            col("scenario_type"),
            col("decision"),
            when(col("decision") == "Recommended", 1)
                .otherwise(0)
                .alias("decision_flag"),
            col("decision_date"),
            current_timestamp().alias("processed_at")
        )
    )

@dlt.table(
    comment="Processed outcomes",
    table_properties={"delta.enableChangeDataFeed": "true"}
)
def outcomes_processed():
    """Transform Bronze outcomes to Silver"""
    return (
        dlt.read("bronze_outcomes")
        .select(
            col("outcome_id"),
            col("decision_id"),
            col("patient_id"),
            col("outcome_type"),
            col("outcome_date"),
            current_timestamp().alias("processed_at")
        )
    )

# COMMAND

# %md
# ## Gold Layer - Analytics & Aggregations
# Creates metrics, dashboards, and analysis tables

# COMMAND

@dlt.table(
    comment="Bias metrics aggregated by scenario, race, and gender",
    table_properties={"delta.enableChangeDataFeed": "true"}
)
def bias_metrics():
    """
    Aggregate bias metrics by scenario, race, and gender
    - Counts total decisions and approvals
    - Calculates approval rates
    - Includes clinical severity metrics
    - Auto-updates when Silver layer changes
    """
    decisions = dlt.read("decisions_processed")
    patients = dlt.read("patients_processed")

    return (
        decisions.join(
            patients,
            on="patient_id",
            how="inner"
        )
        .groupBy(
            col("scenario_type"),
            col("race"),
            col("gender")
        )
        .agg(
            count(col("decision_id")).cast("int").alias("total_decisions"),
            spark_sum(col("decision_flag")).cast("int").alias("approved_count"),
            spark_round(spark_sum(col("decision_flag")) / count(col("decision_id")) * 100, 2)
                .alias("approval_rate"),
            count(col("patient_id")).cast("int").alias("unique_patients"),
            spark_round(expr("avg(sofa_score)"), 2).alias("avg_severity"),
            spark_min(col("decision_date")).alias("first_decision_date"),
            spark_max(col("decision_date")).alias("last_decision_date"),
            current_timestamp().alias("calculated_at")
        )
    )

@dlt.table(
    comment="Overall equity dashboard KPIs",
    table_properties={"delta.enableChangeDataFeed": "true"}
)
def equity_dashboard():
    """
    Overall dashboard metrics - single row with all KPIs
    - Total patients and decisions
    - Demographic percentages
    - Overall approval rate
    - Number of scenarios analyzed
    """
    decisions = dlt.read("decisions_processed")
    patients = dlt.read("patients_processed")

    joined = patients.join(decisions, on="patient_id", how="left")

    return joined.select(
        count(col("patient_id")).cast("int").alias("total_patients"),
        count(col("decision_id")).cast("int").alias("total_decisions"),
        spark_round(expr("avg(sofa_score)"), 2).alias("avg_clinical_severity"),
        spark_round(spark_sum(when(col("gender") == "F", 1).otherwise(0)) /
                  count(col("patient_id")) * 100, 2).alias("pct_female"),
        spark_round(spark_sum(when(col("race") == "Black", 1).otherwise(0)) /
                  count(col("patient_id")) * 100, 2).alias("pct_black"),
        spark_round(spark_sum(col("decision_flag")) / count(col("decision_id")) * 100, 2)
            .alias("overall_approval_rate"),
        count(col("scenario_type")).cast("int").alias("scenarios_analyzed"),
        current_timestamp().alias("last_updated")
    )

@dlt.table(
    comment="Disparate Impact Ratio (DIR) analysis - 80% rule flagging",
    table_properties={"delta.enableChangeDataFeed": "true"}
)
def disparate_impact():
    """
    Calculate DIR for fairness analysis
    - Compares approval rates between Black and White patients
    - Flags scenarios where DIR < 0.80 (80% rule violation)
    - Auto-updates as bias_metrics change
    """
    metrics = dlt.read("bias_metrics")

    return metrics.groupBy("scenario_type").agg(
        spark_round(
            expr("max(case when race='Black' then approval_rate else null end)"),
            2
        ).alias("black_approval_rate"),
        spark_round(
            expr("max(case when race='White' then approval_rate else null end)"),
            2
        ).alias("white_approval_rate")
    ).select(
        col("scenario_type"),
        col("black_approval_rate"),
        col("white_approval_rate"),
        spark_round(col("black_approval_rate") / col("white_approval_rate"), 4)
            .alias("disparate_impact_ratio"),
        when(spark_round(col("black_approval_rate") / col("white_approval_rate"), 4) < 0.80, "FLAGGED")
            .otherwise("OK")
            .alias("eighty_percent_rule_status"),
        current_timestamp().alias("calculated_at")
    )

@dlt.table(
    comment="Provider accountability scorecard",
    table_properties={"delta.enableChangeDataFeed": "true"}
)
def provider_accountability():
    """
    Provider-level equity scorecard
    - Equity gap (difference between highest and lowest approval rates)
    - Demographic groups analyzed per scenario
    - Total decisions analyzed
    """
    metrics = dlt.read("bias_metrics")

    return (
        metrics.groupBy(col("scenario_type"))
        .agg(
            count(col("race")).cast("int").alias("demographic_groups_analyzed"),
            spark_round(expr("avg(approval_rate)"), 2).alias("avg_approval_rate"),
            spark_round(expr("max(approval_rate)"), 2).alias("highest_approval_rate"),
            spark_round(expr("min(approval_rate)"), 2).alias("lowest_approval_rate"),
            spark_round(expr("max(approval_rate) - min(approval_rate)"), 2)
                .alias("equity_gap"),
            spark_sum(col("total_decisions")).cast("int").alias("total_decisions_analyzed"),
            current_timestamp().alias("calculated_at")
        )
    )

# COMMAND

# %md
# ## Data Quality Monitoring

# COMMAND

@dlt.expectation(name="bronze_patients_quality")
def bronze_patients_have_valid_ids():
    """All patients must have valid IDs"""
    return spark.read.format("delta").table("healthcare_equity_bronze.patients") \
        .filter(col("patient_id").isNotNull() & (col("patient_id") > 0))

@dlt.expectation(name="bronze_decisions_complete")
def bronze_decisions_linked_to_patients():
    """All decisions must reference valid patients"""
    decisions = spark.read.format("delta").table("healthcare_equity_bronze.decisions")
    patients = spark.read.format("delta").table("healthcare_equity_bronze.patients")

    valid_decisions = decisions.join(
        patients.select("patient_id"),
        on="patient_id",
        how="inner"
    )

    return valid_decisions.count() == decisions.count()

# COMMAND

print("DLT Pipeline Definition Complete")
print("This notebook defines the complete transformation pipeline:")
print("  Bronze Layer (raw data) → Silver Layer (cleaned) → Gold Layer (analytics)")
print("\nWhen Bronze is updated, Silver automatically refreshes.")
print("When Silver is updated, Gold automatically refreshes.")
print("All done by DLT - no manual intervention needed!")

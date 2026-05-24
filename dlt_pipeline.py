#!/usr/bin/env python3
"""
Databricks Delta Live Tables (DLT) Pipeline
Handles Bronze → Silver → Gold transformation automatically
"""
import dlt
from pyspark.sql.functions import (
    col, when, round, count, sum, min as spark_min, max as spark_max,
    case, expr, current_timestamp
)

# ============================================================================
# BRONZE LAYER (Raw Data - No Transformations)
# These tables are populated by continuous_data_pipeline.py
# ============================================================================

@dlt.view
def bronze_patients_view():
    """Read raw patients from Bronze layer"""
    return spark.read.format("delta").table("healthcare_equity_bronze.patients")

@dlt.view
def bronze_decisions_view():
    """Read raw decisions from Bronze layer"""
    return spark.read.format("delta").table("healthcare_equity_bronze.decisions")

# ============================================================================
# SILVER LAYER (Cleaned & Transformed Data)
# ============================================================================

@dlt.table(
    comment="Processed patient records with risk classification",
    table_properties={"delta.enableChangeDataFeed": "true"}
)
def patients_processed():
    """Transform Bronze patients to Silver with risk levels and age groups"""
    return (
        dlt.read("bronze_patients_view")
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
        .filter(col("patient_id").isNotNull())
    )

@dlt.table(
    comment="Processed decision records with approval flag",
    table_properties={"delta.enableChangeDataFeed": "true"}
)
def decisions_processed():
    """Transform Bronze decisions to Silver with decision flags"""
    return (
        dlt.read("bronze_decisions_view")
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
        .filter(col("decision_id").isNotNull() & col("patient_id").isNotNull())
    )

@dlt.table(
    comment="Outcome records",
    table_properties={"delta.enableChangeDataFeed": "true"}
)
def outcomes_processed():
    """Transform Bronze outcomes to Silver"""
    return (
        spark.read.format("delta")
        .table("healthcare_equity_bronze.outcomes")
        .select(
            col("outcome_id"),
            col("decision_id"),
            col("patient_id"),
            col("outcome_type"),
            col("outcome_date"),
            current_timestamp().alias("processed_at")
        )
        .filter(col("outcome_id").isNotNull())
    )

# ============================================================================
# GOLD LAYER (Aggregated Metrics & Analytics)
# ============================================================================

@dlt.table(
    comment="Bias metrics aggregated by scenario, race, and gender",
    table_properties={"delta.enableChangeDataFeed": "true"}
)
def bias_metrics():
    """Aggregate bias metrics by scenario, race, and gender"""
    return (
        dlt.read("decisions_processed")
        .join(
            dlt.read("patients_processed"),
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
            sum(col("decision_flag")).cast("int").alias("approved_count"),
            round(sum(col("decision_flag")) / count(col("decision_id")) * 100, 2)
                .alias("approval_rate"),
            count(col("patient_id")).cast("int").alias("unique_patients"),
            round(expr("avg(sofa_score)"), 2).alias("avg_severity"),
            spark_min(col("decision_date")).alias("first_decision_date"),
            spark_max(col("decision_date")).alias("last_decision_date"),
            current_timestamp().alias("calculated_at")
        )
    )

@dlt.table(
    comment="Overall equity dashboard metrics",
    table_properties={"delta.enableChangeDataFeed": "true"}
)
def equity_dashboard():
    """Create overall dashboard metrics"""
    decisions = dlt.read("decisions_processed")
    patients = dlt.read("patients_processed")

    joined = patients.join(decisions, on="patient_id", how="left")

    return joined.select(
        count(col("patient_id")).cast("int").alias("total_patients"),
        count(col("decision_id")).cast("int").alias("total_decisions"),
        round(expr("avg(sofa_score)"), 2).alias("avg_clinical_severity"),
        round(sum(when(col("gender") == "F", 1).otherwise(0)) /
              count(col("patient_id")) * 100, 2).alias("pct_female"),
        round(sum(when(col("race") == "Black", 1).otherwise(0)) /
              count(col("patient_id")) * 100, 2).alias("pct_black"),
        round(sum(col("decision_flag")) / count(col("decision_id")) * 100, 2)
            .alias("overall_approval_rate"),
        count(col("scenario_type")).cast("int").alias("scenarios_analyzed"),
        current_timestamp().alias("last_updated")
    )

@dlt.table(
    comment="Disparate Impact Ratio (DIR) analysis",
    table_properties={"delta.enableChangeDataFeed": "true"}
)
def disparate_impact():
    """Calculate Disparate Impact Ratio (DIR) for fairness analysis"""
    metrics = dlt.read("bias_metrics")

    white_approval = metrics.filter(col("race") == "White").groupBy("scenario_type").avg("approval_rate")
    black_approval = metrics.filter(col("race") == "Black").groupBy("scenario_type").avg("approval_rate")

    return (
        black_approval.join(white_approval, on="scenario_type", how="left")
        .select(
            col("scenario_type"),
            col("avg(approval_rate)").alias("black_approval_rate"),
            col("avg(approval_rate)").alias("white_approval_rate"),
            round(col("avg(approval_rate)") / col("avg(approval_rate)"), 4)
                .alias("disparate_impact_ratio"),
            when(round(col("avg(approval_rate)") / col("avg(approval_rate)"), 4) < 0.8, "FLAGGED")
                .otherwise("OK")
                .alias("80_percent_rule"),
            current_timestamp().alias("calculated_at")
        )
    )

@dlt.table(
    comment="Provider accountability scorecard",
    table_properties={"delta.enableChangeDataFeed": "true"}
)
def provider_accountability():
    """Provider-level equity scorecard"""
    return (
        dlt.read("bias_metrics")
        .groupBy(col("scenario_type"))
        .agg(
            count(col("race")).cast("int").alias("demographic_groups_analyzed"),
            round(expr("avg(approval_rate)"), 2).alias("avg_approval_rate"),
            round(expr("max(approval_rate)"), 2).alias("highest_approval_rate"),
            round(expr("min(approval_rate)"), 2).alias("lowest_approval_rate"),
            round(expr("max(approval_rate) - min(approval_rate)"), 2)
                .alias("equity_gap"),
            sum(col("total_decisions")).cast("int").alias("total_decisions_analyzed"),
            current_timestamp().alias("calculated_at")
        )
    )

# ============================================================================
# EXPECTATIONS & Data Quality
# ============================================================================

@dlt.expect_or_drop("valid_patient_id", col("patient_id") > 0)
@dlt.expect_or_drop("valid_decision_id", col("decision_id") > 0)
def decisions_with_quality():
    """Decisions with data quality expectations"""
    return dlt.read("decisions_processed")

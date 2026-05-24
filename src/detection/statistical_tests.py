"""
Statistical tests for healthcare bias detection.

Implements: chi-square, logistic regression, disparate impact ratio, odds ratio
"""
import logging
from typing import List, Tuple
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency
from sklearn.linear_model import LogisticRegression

from ..models import BiasMetric, SeverityLevel, Race

logger = logging.getLogger(__name__)


class BiasStatisticalTests:
    """Statistical methods for detecting healthcare disparities."""

    def __init__(self, config: dict):
        self.config = config
        self.significance_threshold = config.get("bias_detection", {}).get("significance_threshold", 0.05)
        self.disparate_impact_threshold = config.get("bias_detection", {}).get("disparate_impact_threshold", 0.80)
        self.severity_thresholds = config.get("bias_detection", {}).get("severity_thresholds", {})

    def disparate_impact_ratio(
        self,
        df: pd.DataFrame,
        outcome_col: str,
        group_col: str,
        reference_group: str,
        comparison_group: str
    ) -> BiasMetric:
        """
        Calculate Disparate Impact Ratio (EEOC 80% rule).

        DIR = (Outcome rate for comparison group) / (Outcome rate for reference group)
        DIR < 0.80 indicates potential adverse impact
        """
        ref_data = df[df[group_col] == reference_group]
        comp_data = df[df[group_col] == comparison_group]

        ref_rate = ref_data[outcome_col].sum() / len(ref_data) if len(ref_data) > 0 else 0
        comp_rate = comp_data[outcome_col].sum() / len(comp_data) if len(comp_data) > 0 else 0

        dir_value = comp_rate / ref_rate if ref_rate > 0 else 0

        # Chi-square test
        contingency = np.array([
            [comp_data[outcome_col].sum(), len(comp_data) - comp_data[outcome_col].sum()],
            [ref_data[outcome_col].sum(), len(ref_data) - ref_data[outcome_col].sum()]
        ])
        chi2, p_value, dof, expected = chi2_contingency(contingency)

        is_significant = p_value < self.significance_threshold
        severity = self._classify_severity(dir_value)

        # Confidence interval (normal approximation)
        se = np.sqrt((comp_rate * (1 - comp_rate) / len(comp_data)) +
                     (ref_rate * (1 - ref_rate) / len(ref_data))) if len(comp_data) > 0 and len(ref_data) > 0 else 0
        ci_lower = dir_value - 1.96 * se
        ci_upper = dir_value + 1.96 * se

        return BiasMetric(
            scenario_type="unknown",
            demographic_dimension=group_col,
            reference_group=reference_group,
            comparison_group=comparison_group,
            metric_name="disparate_impact_ratio",
            metric_value=dir_value,
            confidence_interval_lower=ci_lower,
            confidence_interval_upper=ci_upper,
            p_value=p_value,
            is_significant=is_significant,
            severity=severity,
            sample_size=len(df),
            reference_group_rate=ref_rate,
            comparison_group_rate=comp_rate
        )

    def _classify_severity(self, dir_value: float) -> SeverityLevel:
        """Classify bias severity based on DIR."""
        thresholds = self.severity_thresholds
        critical = thresholds.get("critical", 0.30)
        severe = thresholds.get("severe", 0.50)
        moderate = thresholds.get("moderate", 0.70)
        mild = thresholds.get("mild", 0.85)

        if dir_value < critical:
            return SeverityLevel.CRITICAL
        elif dir_value < severe:
            return SeverityLevel.SEVERE
        elif dir_value < moderate:
            return SeverityLevel.MODERATE
        elif dir_value < mild:
            return SeverityLevel.MILD
        else:
            return SeverityLevel.NONE

    def chi_square_test(
        self,
        df: pd.DataFrame,
        outcome_col: str,
        group_col: str,
        reference_group: str,
        comparison_group: str
    ) -> Tuple[float, float]:
        """Chi-square test for independence."""
        ref_data = df[df[group_col] == reference_group]
        comp_data = df[df[group_col] == comparison_group]

        contingency = np.array([
            [comp_data[outcome_col].sum(), len(comp_data) - comp_data[outcome_col].sum()],
            [ref_data[outcome_col].sum(), len(ref_data) - ref_data[outcome_col].sum()]
        ])

        chi2, p_value, dof, expected = chi2_contingency(contingency)
        return chi2, p_value

    def odds_ratio(
        self,
        df: pd.DataFrame,
        outcome_col: str,
        group_col: str,
        reference_group: str,
        comparison_group: str
    ) -> Tuple[float, float, float]:
        """Calculate odds ratio with 95% CI."""
        ref_data = df[df[group_col] == reference_group]
        comp_data = df[df[group_col] == comparison_group]

        a = comp_data[outcome_col].sum()
        b = len(comp_data) - a
        c = ref_data[outcome_col].sum()
        d = len(ref_data) - c

        or_value = (a * d) / (b * c) if (b * c) > 0 else 0
        log_or = np.log(or_value) if or_value > 0 else 0
        se_log_or = np.sqrt((1/max(a, 0.5)) + (1/max(b, 0.5)) + (1/max(c, 0.5)) + (1/max(d, 0.5)))

        ci_lower = np.exp(log_or - 1.96 * se_log_or)
        ci_upper = np.exp(log_or + 1.96 * se_log_or)

        return or_value, ci_lower, ci_upper

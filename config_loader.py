"""
Load configuration from YAML files.
"""
import yaml
import os
from pathlib import Path


def load_config():
    """Load configuration from config/settings.yaml"""
    config_path = Path(__file__).parent / "config" / "settings.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config


def load_bias_thresholds():
    """Load bias threshold definitions."""
    threshold_path = Path(__file__).parent / "config" / "bias_thresholds.yaml"

    if not threshold_path.exists():
        raise FileNotFoundError(f"Bias thresholds file not found: {threshold_path}")

    with open(threshold_path, "r") as f:
        thresholds = yaml.safe_load(f)

    return thresholds

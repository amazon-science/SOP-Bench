# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Tests for configuration module."""

import os
import pytest
from pathlib import Path
from amazon_sop_bench.config import Config, get_config, set_config, reset_config


def test_config_defaults():
    """Test that config has sensible defaults."""
    config = Config()
    assert config.aws_region == "us-west-2"
    assert config.temperature == 0.5
    assert config.max_tokens == 8192
    assert config.save_traces is True
    assert config.log_level == "INFO"


def test_config_from_env(monkeypatch):
    """Test loading config from environment variables."""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("TEMPERATURE", "0.7")
    monkeypatch.setenv("MAX_TOKENS", "4096")
    
    config = Config()
    assert config.aws_region == "us-east-1"
    assert config.temperature == 0.7
    assert config.max_tokens == 4096


def test_config_validation():
    """Test that config validates parameters."""
    # Invalid temperature
    with pytest.raises(ValueError, match="Temperature must be between"):
        Config(temperature=1.5)
    
    # Invalid max_tokens
    with pytest.raises(ValueError, match="max_tokens must be positive"):
        Config(max_tokens=-100)
    
    # Invalid log_level
    with pytest.raises(ValueError, match="log_level must be one of"):
        Config(log_level="INVALID")


def test_config_output_dir_creation(tmp_path):
    """Test that output directory is created."""
    output_dir = tmp_path / "test_output"
    config = Config(output_dir=output_dir)
    
    assert output_dir.exists()
    assert output_dir.is_dir()


def test_global_config():
    """Test global config management."""
    reset_config()
    
    # Get default config
    config1 = get_config()
    assert config1.aws_region == "us-west-2"
    
    # Should return same instance
    config2 = get_config()
    assert config1 is config2
    
    # Set custom config
    custom_config = Config(aws_region="eu-west-1")
    set_config(custom_config)
    
    config3 = get_config()
    assert config3.aws_region == "eu-west-1"
    assert config3 is custom_config
    
    # Reset
    reset_config()
    config4 = get_config()
    assert config4 is not custom_config

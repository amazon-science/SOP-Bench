# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
from amazon_sop_bench.config import Config


@pytest.fixture
def test_config():
    """Provide a test configuration with safe defaults."""
    return Config(
        aws_region="us-west-2",
        aws_model_id="test-model-id",
        aws_role_arn=None,
        temperature=0.5,
        max_tokens=1000,
        output_dir=Path("./test_results"),
        save_traces=False,
        log_level="DEBUG",
    )


@pytest.fixture
def fixtures_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_sop_text():
    """Sample SOP text for testing."""
    return """
    Standard Operating Procedure for Content Flagging
    
    1. Calculate Bot Probability Index using user behavior data
    2. Calculate Content Severity Index based on violation types
    3. Calculate User Trust Score using historical data
    4. Determine Final Decision based on all scores
    """


@pytest.fixture
def sample_task():
    """Sample task input for testing."""
    return {
        "task_id": "test_001",
        "user_id": "user_123",
        "content_id": "content_456",
        "device_type": "mobile",
    }


@pytest.fixture
def sample_tools():
    """Sample tool specifications for testing."""
    return [
        {
            "name": "calculateBotProbabilityIndex",
            "description": "Calculate bot probability based on user behavior",
            "parameters": {
                "userid": {"type": "string", "required": True},
                "is_possible_bot": {"type": "float", "required": True},
            },
        },
        {
            "name": "calculateContentSeverityIndex",
            "description": "Calculate content severity score",
            "parameters": {
                "content_id": {"type": "string", "required": True},
                "violation_type": {"type": "string", "required": True},
            },
        },
    ]

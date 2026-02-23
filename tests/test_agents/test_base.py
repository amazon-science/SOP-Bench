# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Tests for base agent class."""

import pytest
from amazon_sop_bench.agents import BaseAgent, AgentResult


class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    def execute(self, sop, task, tools):
        """Simple mock implementation."""
        return AgentResult(
            output={"result": "success"},
            tool_calls=[{"tool": "mock_tool", "params": {}}],
            reasoning_trace="Mock reasoning",
            execution_time=1.0,
            success=True,
        )


def test_base_agent_initialization():
    """Test agent initialization."""
    agent = MockAgent(model_id="test-model")
    assert agent.model_id == "test-model"
    assert isinstance(agent.config, dict)


def test_base_agent_execute():
    """Test agent execute method."""
    agent = MockAgent()
    result = agent.execute(
        sop="Test SOP",
        task={"input": "test"},
        tools=[{"name": "test_tool"}]
    )
    
    assert isinstance(result, AgentResult)
    assert result.success is True
    assert result.output == {"result": "success"}
    assert len(result.tool_calls) == 1


def test_base_agent_repr():
    """Test agent string representation."""
    agent = MockAgent(model_id="test-model")
    assert "MockAgent" in repr(agent)
    assert "test-model" in repr(agent)


def test_agent_result_dataclass():
    """Test AgentResult dataclass."""
    result = AgentResult(
        output="test output",
        tool_calls=[],
        reasoning_trace="test reasoning",
        execution_time=2.5,
        success=True,
        error=None,
    )
    
    assert result.output == "test output"
    assert result.tool_calls == []
    assert result.execution_time == 2.5
    assert result.success is True

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""
Amazon SOP-Bench: Benchmark for evaluating LLM agents on Standard Operating Procedures.

This package provides:
- 10 industrial benchmark datasets across diverse domains
- Agent execution framework with base abstractions
- Comprehensive evaluation metrics and reporting
- Optional SOP generation tools

Quick Start:
    >>> from amazon_sop_bench import evaluate, list_benchmarks
    >>> 
    >>> # List available benchmarks
    >>> benchmarks = list_benchmarks()
    >>> 
    >>> # Run evaluation
    >>> results = evaluate(
    ...     benchmark_name="content_flagging",
    ...     agent_type="react"
    ... )
    >>> print(f"Task Success Rate: {results['task_success_rate']:.1%}")

For CLI usage:
    $ sop-bench list
    $ sop-bench evaluate --benchmark content_flagging --agent react
"""

from amazon_sop_bench.__version__ import __version__, __version_info__
from amazon_sop_bench.config import Config, get_config, set_config
from amazon_sop_bench.agents import BaseAgent, AgentResult, FunctionCallingAgent, ReActAgent
from amazon_sop_bench.tools import BaseTool, ToolSpec, ToolCall

# Import common types
from amazon_sop_bench.types import (
    AgentType,
    BenchmarkDomain,
    Task,
    BenchmarkMetadata,
    Benchmark,
    TaskResult,
    EvaluationResults,
)

# Benchmarks module is now implemented
from amazon_sop_bench.benchmarks import list_benchmarks, load_benchmark

# Evaluation module is now implemented
from amazon_sop_bench.evaluation import evaluate

__all__ = [
    "__version__",
    "__version_info__",
    "Config",
    "get_config",
    "set_config",
    "BaseAgent",
    "AgentResult",
    "BaseTool",
    "ToolSpec",
    "ToolCall",
    "AgentType",
    "BenchmarkDomain",
    "Task",
    "BenchmarkMetadata",
    "Benchmark",
    "TaskResult",
    "EvaluationResults",
    # "list_benchmarks",
    # "load_benchmark",
    # "evaluate",
]

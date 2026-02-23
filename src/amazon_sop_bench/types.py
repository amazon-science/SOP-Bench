# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Common type definitions for amazon-sop-bench."""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum


class AgentType(str, Enum):
    """Supported agent types."""
    FUNCTION_CALLING = "function_calling"
    REACT = "react"
    REFLECTION = "reflection"


class BenchmarkDomain(str, Enum):
    """Benchmark domains."""
    CONTENT_MODERATION = "content_moderation"
    CUSTOMER_SUPPORT = "customer_support"
    SUPPLY_CHAIN = "supply_chain"
    TRANSPORTATION = "transportation"
    RETAIL = "retail"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    AUTONOMOUS_DRIVING = "autonomous_driving"
    MEDIA = "media"
    LOGISTICS = "logistics"


@dataclass
class Task:
    """
    A single task in a benchmark.
    
    Attributes:
        task_id: Unique identifier for the task
        inputs: Input parameters for the task
        expected_output: Ground truth output
        metadata: Optional additional information
    """
    task_id: str
    inputs: Dict[str, Any]
    expected_output: Any
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BenchmarkMetadata:
    """
    Metadata for a benchmark.
    
    Attributes:
        name: Benchmark name (e.g., "content_flagging")
        domain: Domain category
        description: Brief description of the benchmark
        num_tasks: Number of tasks in the benchmark
        num_tools: Number of tools available
        complexity_score: LLM-assessed complexity (1-10)
        human_complexity: Human-assessed complexity (1-10)
        sop_path: Path to SOP text file
        tools_path: Path to tools implementation
        toolspecs_path: Path to tool specifications
        test_data_path: Path to test dataset
        output_columns: List of column names that represent expected outputs
    """
    name: str
    domain: str
    description: str
    num_tasks: int
    num_tools: int
    complexity_score: float
    human_complexity: Optional[float] = None
    sop_path: Optional[Path] = None
    tools_path: Optional[Path] = None
    toolspecs_path: Optional[Path] = None
    test_data_path: Optional[Path] = None
    input_columns: List[str] = None
    output_columns: List[str] = None
    
    def __post_init__(self):
        """Initialize output_columns to empty list if None."""
        if self.output_columns is None:
            self.output_columns = []


@dataclass
class Benchmark:
    """
    Complete benchmark with all components.
    
    Attributes:
        metadata: Benchmark metadata
        sop_text: Natural language SOP instructions
        tools: List of available tools
        tasks: List of test tasks
    """
    metadata: BenchmarkMetadata
    sop_text: str
    tools: List[Any]  # Will be List[BaseTool] once tools module is complete
    tasks: List[Task]


@dataclass
class TaskResult:
    """
    Result of executing a single task.
    
    Attributes:
        task_id: Task identifier
        success: Whether the task completed successfully
        predicted_output: Output produced by the agent
        expected_output: Ground truth output
        tool_calls: List of tool calls made
        execution_time: Time taken (seconds)
        error: Error message if failed
        reasoning_trace: Agent's reasoning steps
    """
    task_id: str
    success: bool
    predicted_output: Any
    expected_output: Any
    tool_calls: List[Dict[str, Any]]
    execution_time: float
    error: Optional[str] = None
    reasoning_trace: Optional[str] = None


@dataclass
class EvaluationResults:
    """
    Aggregated evaluation results for a benchmark.
    
    Attributes:
        benchmark_name: Name of the benchmark
        agent_type: Type of agent used
        model_id: Model identifier
        num_tasks: Total number of tasks
        num_completed: Number of tasks completed
        num_correct: Number of tasks with correct output
        task_success_rate: Percentage of correct tasks (TSR)
        execution_completion_rate: Percentage of completed tasks (ECR)
        conditional_task_success_rate: TSR among completed tasks (C-TSR)
        tool_accuracy: Percentage of correct tool calls
        avg_execution_time: Average time per task
        task_results: Individual task results
        error_distribution: Categorization of errors
    """
    benchmark_name: str
    agent_type: str
    model_id: str
    num_tasks: int
    num_completed: int
    num_correct: int
    task_success_rate: float
    execution_completion_rate: float
    conditional_task_success_rate: float
    tool_accuracy: Dict[str, float]
    avg_execution_time: float
    task_results: List[TaskResult]
    error_distribution: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary for serialization."""
        return {
            "benchmark": self.benchmark_name,
            "agent": self.agent_type,
            "model": self.model_id,
            "num_tasks": self.num_tasks,
            "num_completed": self.num_completed,
            "num_correct": self.num_correct,
            "task_success_rate": self.task_success_rate,
            "execution_completion_rate": self.execution_completion_rate,
            "conditional_task_success_rate": self.conditional_task_success_rate,
            "tool_accuracy": self.tool_accuracy,
            "avg_execution_time": self.avg_execution_time,
            "error_distribution": self.error_distribution,
        }

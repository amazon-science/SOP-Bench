# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Evaluation framework module.

This module provides functionality for evaluating agent performance on benchmarks,
calculating metrics, and generating reports.
"""

from typing import Optional, Union, Dict, Any
from pathlib import Path

from amazon_sop_bench.evaluation.evaluator import Evaluator
from amazon_sop_bench.evaluation.metrics import MetricsCalculator
from amazon_sop_bench.evaluation.reporter import ResultReporter
from amazon_sop_bench.evaluation.parser import OutputParser
from amazon_sop_bench.agents.base import BaseAgent
from amazon_sop_bench.types import EvaluationResults


def evaluate(
    benchmark_name: str,
    agent_type: str = "react",
    agent: Optional[BaseAgent] = None,
    max_tasks: Optional[int] = None,
    output_dir: Optional[Path] = None,
    resume: bool = False,
    max_workers: int = 1,
    model_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run evaluation with simple interface.
    
    Args:
        benchmark_name: Name of benchmark to evaluate
        agent_type: Type of agent ("react" or "function_calling")
        agent: Optional custom agent instance
        max_tasks: Optional limit on number of tasks
        output_dir: Optional output directory for results
        resume: Whether to resume from existing results if available
        max_workers: Number of parallel worker threads (default: 1, use 1 for parallelization)
        model_id: Optional model ID to override default
        
    Returns:
        Dictionary with evaluation results
        
    Example:
        >>> from amazon_sop_bench import evaluate
        >>> results = evaluate("content_flagging", "react")
        >>> print(f"TSR: {results['task_success_rate']:.1%}")
    """
    # Create agent if not provided
    if agent is None:
        if agent_type == "react":
            try:
                from amazon_sop_bench.agents import ReActAgent
                agent = ReActAgent(model_id=model_id) if model_id else ReActAgent()
            except ImportError:
                raise ImportError(
                    "ReAct agent requires langchain and langchain-aws. "
                    "Install with: pip install langchain langchain-aws"
                )
        elif agent_type == "function_calling":
            try:
                from amazon_sop_bench.agents import FunctionCallingAgent
                agent = FunctionCallingAgent(model_id=model_id) if model_id else FunctionCallingAgent()
            except ImportError:
                raise ImportError(
                    "Function-Calling agent requires boto3. "
                    "Install with: pip install boto3"
                )
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
    
    # Run evaluation
    evaluator = Evaluator(
        benchmark_name, 
        agent, 
        max_tasks=max_tasks, 
        output_dir=output_dir, 
        resume=resume,
        max_workers=max_workers
    )
    results = evaluator.run()
    
    # Generate report
    reporter = ResultReporter()
    # Use the evaluator's output directory if no explicit output_dir was provided
    report_output_dir = output_dir if output_dir else evaluator.output_dir
    reporter.generate_full_report(results, report_output_dir)
    
    # Return as dictionary for convenience
    return results.to_dict()


__all__ = [
    "Evaluator",
    "MetricsCalculator",
    "ResultReporter",
    "OutputParser",
    "evaluate",
]

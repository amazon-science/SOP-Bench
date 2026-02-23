# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Main evaluator for running agents on benchmarks."""

import time
import json
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from amazon_sop_bench.types import TaskResult, EvaluationResults, Task, Benchmark
from amazon_sop_bench.agents.base import BaseAgent, AgentResult
from amazon_sop_bench.benchmarks import load_benchmark
from amazon_sop_bench.evaluation.parser import OutputParser
from amazon_sop_bench.evaluation.metrics import MetricsCalculator
from amazon_sop_bench.evaluation.reporter import ResultReporter
from amazon_sop_bench.config import get_config
from amazon_sop_bench.utils.logging import get_logger

logger = get_logger(__name__)

# Optional rich import for progress bars
try:
    from rich.progress import Progress, TaskID
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    logger.warning("Rich not available - no progress bars")


class Evaluator:
    """
    Main evaluator for running agents on benchmarks.
    
    Orchestrates the complete evaluation process:
    1. Load benchmark
    2. Run agent on each task
    3. Parse outputs and compare to ground truth
    4. Calculate metrics
    5. Generate reports
    
    Example:
        >>> evaluator = Evaluator("content_flagging", agent)
        >>> results = evaluator.run()
        >>> print(f"TSR: {results.task_success_rate:.1%}")
    """
    
    def __init__(
        self,
        benchmark_name: str,
        agent: BaseAgent,
        max_tasks: Optional[int] = None,
        output_dir: Optional[Path] = None,
        resume: bool = False,
        max_workers: int = 1
    ):
        """
        Initialize evaluator.
        
        Args:
            benchmark_name: Name of benchmark to evaluate on
            agent: Agent instance to evaluate
            max_tasks: Optional limit on number of tasks (for testing)
            output_dir: Optional custom output directory (overrides config)
            resume: Whether to resume from existing results if available
            max_workers: Number of parallel worker threads (default: 1, use 1 for parallelization)
        """
        self.benchmark_name = benchmark_name
        self.agent = agent
        self.max_tasks = max_tasks
        self.resume = resume
        self.max_workers = max_workers
        self.config = get_config()
        
        # Override output_dir if provided
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.config.output_dir
        
        # Initialize components
        self.parser = OutputParser()
        self.metrics_calculator = MetricsCalculator()
        self.reporter = ResultReporter()
        
        # Load existing results if resuming
        self.existing_results = {}
        if resume:
            self.existing_results = self._load_existing_results()
        
        # Load benchmark
        logger.info(f"Loading benchmark: {benchmark_name}")
        self.benchmark = load_benchmark(benchmark_name)
        
        # Limit tasks if specified
        if max_tasks and max_tasks < len(self.benchmark.tasks):
            self.benchmark.tasks = self.benchmark.tasks[:max_tasks]
            logger.info(f"Limited to {max_tasks} tasks for evaluation")
        
        logger.info(
            f"Initialized evaluator for {benchmark_name} with {len(self.benchmark.tasks)} tasks"
        )
    
    def run(self) -> EvaluationResults:
        """
        Run complete evaluation.
        
        Returns:
            EvaluationResults with all metrics and task results
        """
        start_time = time.time()
        logger.info(f"Starting evaluation of {self.benchmark_name} with {self.agent}")
        
        # Run agent on all tasks
        task_results = self._run_all_tasks()
        
        # Calculate metrics
        logger.info("Calculating metrics")
        metrics = self.metrics_calculator.calculate_all_metrics(task_results)
        
        # Create evaluation results
        execution_time = time.time() - start_time
        
        results = EvaluationResults(
            benchmark_name=self.benchmark_name,
            agent_type=self.agent.__class__.__name__,
            model_id=getattr(self.agent, 'model_id', 'unknown'),
            num_tasks=metrics["num_tasks"],
            num_completed=metrics["num_completed"],
            num_correct=metrics["num_correct"],
            task_success_rate=metrics["task_success_rate"],
            execution_completion_rate=metrics["execution_completion_rate"],
            conditional_task_success_rate=metrics["conditional_task_success_rate"],
            tool_accuracy=metrics["tool_accuracy"],
            avg_execution_time=metrics["avg_execution_time"],
            task_results=task_results,
            error_distribution=metrics["error_distribution"],
        )
        
        logger.info(
            f"Evaluation completed in {execution_time:.2f} seconds. "
            f"TSR: {results.task_success_rate:.1%}, "
            f"ECR: {results.execution_completion_rate:.1%}"
        )
        
        return results
    
    def _run_all_tasks(self) -> List[TaskResult]:
        """
        Run agent on all tasks with progress tracking.
        Uses ThreadPoolExecutor for parallel execution while maintaining order.
        
        Returns:
            List of TaskResult objects in the same order as input tasks
        """
        task_results = []
        total_tasks = len(self.benchmark.tasks)
        
        # Check for resume functionality with smart gap detection
        tasks_to_execute = []
        preserved_count = 0
        missing_count = 0
        new_count = 0
        
        if self.resume and self.existing_results:
            # Find the highest task_id that was attempted (convert to int for proper comparison)
            attempted_task_ids = [int(task_id) for task_id in self.existing_results.keys()]
            max_attempted_index = max(attempted_task_ids) if attempted_task_ids else -1
            existing_task_ids_set = set(self.existing_results.keys())
            
            logger.info(f"Resume mode: found results for {len(self.existing_results)} tasks up to index {max_attempted_index}")
            
            # Smart gap detection: categorize each task
            for task in self.benchmark.tasks:
                task_id_int = int(task.task_id)
                
                if task_id_int <= max_attempted_index:
                    # Task is within the attempted range
                    if task.task_id in existing_task_ids_set:
                        # Task has existing results - preserve them
                        task_results.append(self.existing_results[task.task_id])
                        preserved_count += 1
                    else:
                        # Task is missing within attempted range - add to execution queue
                        tasks_to_execute.append(task)
                        missing_count += 1
                        # Add placeholder in results list to maintain order
                        task_results.append(None)
                else:
                    # Task is beyond max attempted index - add to execution queue
                    tasks_to_execute.append(task)
                    new_count += 1
                    # Add placeholder in results list to maintain order
                    task_results.append(None)
            
            logger.info(f"Smart resume: {preserved_count} preserved, {missing_count} missing (gaps), {new_count} new tasks")
            if missing_count > 0:
                missing_task_ids = [task.task_id for task in tasks_to_execute if int(task.task_id) <= max_attempted_index]
                logger.info(f"Detected missing tasks within attempted range: {missing_task_ids}")
        else:
            # No resume or no existing results - execute all tasks
            tasks_to_execute = list(self.benchmark.tasks)
            new_count = len(tasks_to_execute)
            # Initialize results list with placeholders
            task_results = [None] * total_tasks
        
        logger.info(f"Running agent on {len(tasks_to_execute)} tasks ({missing_count} missing + {new_count} new) with {self.max_workers} workers")
        
        if len(tasks_to_execute) == 0:
            logger.info(f"No tasks to execute - all {total_tasks} tasks already completed")
            return task_results
        
        # Execute tasks and insert results into placeholders
        # We need to maintain order, so we'll create a mapping from task to index
        task_to_index = {}
        for i, task in enumerate(self.benchmark.tasks):
            task_to_index[task.task_id] = i
        
        completed_count = 0
        
        if RICH_AVAILABLE:
            # Use Rich progress bar with parallel execution
            with Progress() as progress:
                progress_task = progress.add_task(
                    f"Evaluating {self.benchmark_name}",
                    total=len(tasks_to_execute)
                )
                
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # Submit all tasks and collect futures with their corresponding tasks
                    future_to_task = {executor.submit(self.run_single_task, task): task for task in tasks_to_execute}
                    
                    for future in as_completed(future_to_task):
                        task = future_to_task[future]
                        result = future.result()
                        
                        # Insert result at correct position
                        result_index = task_to_index[task.task_id]
                        task_results[result_index] = result
                        
                        completed_count += 1
                        progress.update(progress_task, advance=1)
                        
                        # Log progress every 10 tasks
                        if completed_count % 10 == 0:
                            logger.info(f"Completed {completed_count}/{len(tasks_to_execute)} tasks ({missing_count} missing + {new_count} new)")
        else:
            # Simple progress logging with parallel execution
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks and collect futures with their corresponding tasks
                future_to_task = {executor.submit(self.run_single_task, task): task for task in tasks_to_execute}
                
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    result = future.result()
                    
                    # Insert result at correct position
                    result_index = task_to_index[task.task_id]
                    task_results[result_index] = result
                    
                    completed_count += 1
                    
                    # Log progress every 10 tasks
                    if completed_count % 10 == 0:
                        logger.info(f"Completed {completed_count}/{len(tasks_to_execute)} tasks ({missing_count} missing + {new_count} new)")
        
        logger.info(f"Completed all tasks: {missing_count} missing + {new_count} new + {preserved_count} preserved = {total_tasks} total")
        
        return task_results
    
    def run_single_task(self, task: Task) -> TaskResult:
        """
        Run agent on a single task.
        
        Args:
            task: Task to run
            
        Returns:
            TaskResult with execution details
        """
        start_time = time.time()
        logger.debug(f"Running task {task.task_id}")
        
        try:
            # Execute agent
            agent_result = self.agent.execute(
                sop=self.benchmark.sop_text,
                task=task.inputs,
                tools=self.benchmark.tools
            )
            
            execution_time = time.time() - start_time
            
            # Check if agent execution failed
            if not agent_result.success:
                logger.error(
                    f"Task {task.task_id} - Agent execution failed: {agent_result.error}"
                )
            
            # Parse output using OutputParser
            # For multi-field outputs, use reasoning trace which contains tool results
            raw_output = agent_result.output if agent_result.output else ""
            
            # Determine expected columns from expected_output or benchmark metadata
            expected_columns = None
            if isinstance(task.expected_output, dict):
                expected_columns = list(task.expected_output.keys())
            elif hasattr(self.benchmark.metadata, 'output_columns') and self.benchmark.metadata.output_columns:
                expected_columns = self.benchmark.metadata.output_columns
            
            # Try parsing from reasoning trace first for multi-field
            if expected_columns and len(expected_columns) > 1 and agent_result.reasoning_trace:
                parsed_output = self.parser.parse_decision(
                    agent_result.reasoning_trace,
                    expected_columns
                )
            else:
                # For single-field, parse from output
                parsed_output = self.parser.parse_decision(raw_output, expected_columns)
            
            # Extract predicted output for storage and comparison
            # Parser guarantees: multi-field has "decisions" dict, single-field has "decision" value
            if isinstance(task.expected_output, dict):
                # Multi-field: extract decisions dict
                predicted_value = parsed_output.get("decisions", {})
            else:
                # Single-field: extract decision value
                predicted_value = parsed_output.get("decision")
            
            # Compare predicted value with expected output (use same format for both)
            is_correct = self.parser.compare_decisions(
                predicted_value,
                task.expected_output
            )
            
            # Create TaskResult
            task_result = TaskResult(
                task_id=task.task_id,
                success=agent_result.success,
                predicted_output=predicted_value,
                expected_output=task.expected_output,
                tool_calls=agent_result.tool_calls,
                execution_time=execution_time,
                error=agent_result.error,
                reasoning_trace=agent_result.reasoning_trace,
            )
            
            # Override success if output doesn't match
            if agent_result.success and not is_correct:
                task_result.success = False
                if isinstance(task.expected_output, dict):
                    task_result.error = f"Output mismatch (multi-field): predicted {predicted_value}, expected {task.expected_output} (format: {parsed_output.get('format')})"
                else:
                    task_result.error = f"Output mismatch: predicted '{parsed_output.get('decision')}', expected '{task.expected_output}' (format: {parsed_output.get('format')})"
                logger.warning(f"Task {task.task_id} output mismatch - Parser format: {parsed_output.get('format')}, Predicted: '{predicted_value}', Expected: '{task.expected_output}'")
            
            logger.debug(
                f"Task {task.task_id} completed: "
                f"success={task_result.success}, "
                f"time={execution_time:.2f}s"
            )
            
            # Save trace immediately if enabled
            if self.config.save_traces:
                self._save_trace_if_enabled(task_result)
            
            return task_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error running task {task.task_id}: {e}")
            
            return TaskResult(
                task_id=task.task_id,
                success=False,
                predicted_output=None,
                expected_output=task.expected_output,
                tool_calls=[],
                execution_time=execution_time,
                error=str(e),
                reasoning_trace=None,
            )
    
    def _get_base_name(self) -> str:
        """Build a base filename that includes benchmark, agent, and model."""
        agent_type = self.agent.__class__.__name__
        model_id = getattr(self.agent, 'model_id', 'unknown')
        model_suffix = ResultReporter._sanitize_model_id(model_id)
        return f"{self.benchmark_name}_{agent_type}_{model_suffix}"

    def _save_trace_if_enabled(self, task_result: TaskResult) -> None:
        """
        Save trace file for a task if tracing is enabled.
        
        Uses the reporter's save_traces method for consistent formatting.
        
        Args:
            task_result: TaskResult containing trace information
        """
        
        # Use reporter to save trace (incremental mode)
        trace_dir = self.output_dir / f"{self._get_base_name()}_traces"
        self.reporter.save_traces(task_result, trace_dir)
    
    def _load_existing_results(self) -> Dict[str, TaskResult]:
        """
        Load existing results from output files if they exist.
        
        Returns:
            Dictionary mapping task_id to TaskResult for completed tasks
        """
        existing_results = {}
        agent_type = self.agent.__class__.__name__
        
        # First, check what trace files exist - these are the source of truth for actual executions
        model_id = getattr(self.agent, 'model_id', 'unknown')
        model_suffix = ResultReporter._sanitize_model_id(model_id)
        trace_dir = self.output_dir / f"{self.benchmark_name}_{agent_type}_{model_suffix}_traces"
        
        # Also check legacy path (without model suffix) for backward compatibility
        legacy_trace_dir = self.output_dir / f"{self.benchmark_name}_{agent_type}_traces"
        if not trace_dir.exists() and legacy_trace_dir.exists():
            logger.info(f"Using legacy trace dir: {legacy_trace_dir}")
            trace_dir = legacy_trace_dir
        actually_executed_task_ids = set()
        
        if trace_dir.exists():
            trace_files = list(trace_dir.glob("trace_*.txt"))
            for trace_file in trace_files:
                try:
                    task_id = trace_file.stem.replace("trace_", "")
                    actually_executed_task_ids.add(task_id)
                except Exception as e:
                    logger.warning(f"Failed to parse task ID from {trace_file.name}: {e}")
        
        # Try to load from CSV file for accurate metrics, but only for tasks that were actually executed
        detailed_file = self.output_dir / f"{self.benchmark_name}_{agent_type}_{model_suffix}_detailed.csv"
        
        # Also check legacy path for backward compatibility
        legacy_detailed_file = self.output_dir / f"{self.benchmark_name}_{agent_type}_detailed.csv"
        if not detailed_file.exists() and legacy_detailed_file.exists():
            logger.info(f"Using legacy detailed CSV: {legacy_detailed_file}")
            detailed_file = legacy_detailed_file
        
        if detailed_file.exists() and actually_executed_task_ids:
            try:
                import csv
                
                logger.info(f"Found existing detailed results file: {detailed_file}")
                
                with open(detailed_file, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        task_id = row['task_id']
                        
                        # Only load results for tasks that have corresponding trace files (were actually executed)
                        if task_id not in actually_executed_task_ids:
                            continue
                        
                        # Only load successfully completed tasks (no token errors, parsing errors, etc.)
                        # Skip tasks that failed due to expired tokens or other errors
                        if (row['success'].lower() == 'true' or 
                            (row['success'].lower() == 'false' and 
                             row['predicted_output'] != 'unknown' and 
                             'expired' not in row.get('error', '').lower())):
                            
                            # Convert tool_calls from string to list if needed
                            tool_calls = []
                            if row.get('num_tool_calls') and row['num_tool_calls'].isdigit():
                                # We don't have detailed tool call info in CSV, just count
                                tool_calls = [{"name": "tool_call", "args": {}}] * int(row['num_tool_calls'])
                            
                            task_result = TaskResult(
                                task_id=task_id,
                                success=row['success'].lower() == 'true',
                                predicted_output=row.get('predicted_output'),
                                expected_output=row['expected_output'],
                                tool_calls=tool_calls,
                                execution_time=float(row.get('execution_time', 0.0)),
                                error=row.get('error'),
                                reasoning_trace=None  # Not stored in CSV
                            )
                            existing_results[task_id] = task_result
                
                logger.info(f"Loaded {len(existing_results)} existing task results from CSV file")
                
                # For any executed tasks not found in CSV, parse from trace files
                csv_task_ids = set(existing_results.keys())
                missing_from_csv = actually_executed_task_ids - csv_task_ids
                
                if missing_from_csv:
                    logger.warning(f"Found {len(missing_from_csv)} trace files not in CSV, parsing traces for accurate results")
                    for task_id in missing_from_csv:
                        # Parse the trace file to get accurate results
                        trace_file = trace_dir / f"trace_{task_id}.txt"
                        parsed_result = self._parse_trace_file(trace_file)
                        if parsed_result:
                            existing_results[task_id] = parsed_result
                
                return existing_results
                
            except Exception as e:
                logger.warning(f"Failed to load existing results from {detailed_file}: {e}")
        
        # Fallback: Use trace files and parse them for accurate results
        if trace_dir.exists():
            trace_files = list(trace_dir.glob("trace_*.txt"))
            if trace_files:
                logger.info(f"Found {len(trace_files)} existing trace files in {trace_dir}, parsing for accurate results")
                
                for trace_file in trace_files:
                    try:
                        task_id = trace_file.stem.replace("trace_", "")
                        parsed_result = self._parse_trace_file(trace_file)
                        if parsed_result:
                            existing_results[task_id] = parsed_result
                    except Exception as e:
                        logger.warning(f"Failed to parse trace file {trace_file.name}: {e}")
                
                logger.info(f"Loaded {len(existing_results)} existing task results from trace files")
                return existing_results
        
        return existing_results
    
    def _parse_trace_file(self, trace_file: Path) -> Optional[TaskResult]:
        """
        Parse a trace file to extract accurate TaskResult information.
        
        Args:
            trace_file: Path to the trace file
            
        Returns:
            TaskResult if successfully parsed, None otherwise
        """
        try:
            with open(trace_file, 'r') as f:
                content = f.read()
            
            # Extract information from trace file header
            lines = content.split('\n')
            task_id = None
            success = False
            predicted_output = None
            expected_output = None
            execution_time = 0.0
            error = None
            
            for line in lines:
                if line.startswith('Task ID: '):
                    task_id = line.replace('Task ID: ', '').strip()
                elif line.startswith('Success: '):
                    success = line.replace('Success: ', '').strip().lower() == 'true'
                elif line.startswith('Predicted: '):
                    predicted_output = line.replace('Predicted: ', '').strip()
                elif line.startswith('Expected: '):
                    expected_output = line.replace('Expected: ', '').strip()
                elif line.startswith('Execution Time: '):
                    time_str = line.replace('Execution Time: ', '').replace('s', '').strip()
                    try:
                        execution_time = float(time_str)
                    except ValueError:
                        execution_time = 0.0
                elif line.startswith('Error: '):
                    error = line.replace('Error: ', '').strip()
                    if error == 'None':
                        error = None
            
            if task_id:
                return TaskResult(
                    task_id=task_id,
                    success=success,
                    predicted_output=predicted_output,
                    expected_output=expected_output,
                    tool_calls=[],  # Not stored in trace header
                    execution_time=execution_time,
                    error=error,
                    reasoning_trace=None  # Don't reload full trace for metrics
                )
            
        except Exception as e:
            logger.warning(f"Failed to parse trace file {trace_file}: {e}")
        
        return None
    
    def regenerate_results_from_traces(self, max_tasks: Optional[int] = None) -> EvaluationResults:
        """
        Regenerate evaluation results from existing trace files.
        This is useful when CSV/JSON files are missing but trace files exist.
        
        Args:
            max_tasks: Optional limit on number of tasks to include
            
        Returns:
            EvaluationResults reconstructed from trace files
        """
        agent_type = self.agent.__class__.__name__
        model_id = getattr(self.agent, 'model_id', 'unknown')
        model_suffix = ResultReporter._sanitize_model_id(model_id)
        trace_dir = self.output_dir / f"{self.benchmark_name}_{agent_type}_{model_suffix}_traces"
        
        # Fallback to legacy path
        if not trace_dir.exists():
            legacy_dir = self.output_dir / f"{self.benchmark_name}_{agent_type}_traces"
            if legacy_dir.exists():
                trace_dir = legacy_dir
        
        if not trace_dir.exists():
            raise FileNotFoundError(f"No trace directory found: {trace_dir}")
        
        trace_files = list(trace_dir.glob("trace_*.txt"))
        if not trace_files:
            raise FileNotFoundError(f"No trace files found in: {trace_dir}")
        
        logger.info(f"Regenerating results from {len(trace_files)} trace files")
        
        # Parse all trace files
        task_results = []
        for trace_file in sorted(trace_files, key=lambda x: int(x.stem.replace("trace_", ""))):
            parsed_result = self._parse_trace_file(trace_file)
            if parsed_result:
                task_results.append(parsed_result)
            else:
                logger.warning(f"Failed to parse trace file: {trace_file}")
        
        # Limit results if specified
        if max_tasks and max_tasks < len(task_results):
            task_results = task_results[:max_tasks]
            logger.info(f"Limited to {max_tasks} tasks for regeneration")
        
        # Calculate metrics
        logger.info("Calculating metrics from trace data")
        metrics = self.metrics_calculator.calculate_all_metrics(task_results)
        
        # Create evaluation results
        results = EvaluationResults(
            benchmark_name=self.benchmark_name,
            agent_type=agent_type,
            model_id=getattr(self.agent, 'model_id', 'unknown'),
            num_tasks=metrics["num_tasks"],
            num_completed=metrics["num_completed"],
            num_correct=metrics["num_correct"],
            task_success_rate=metrics["task_success_rate"],
            execution_completion_rate=metrics["execution_completion_rate"],
            conditional_task_success_rate=metrics["conditional_task_success_rate"],
            tool_accuracy=metrics["tool_accuracy"],
            avg_execution_time=metrics["avg_execution_time"],
            task_results=task_results,
            error_distribution=metrics["error_distribution"],
        )
        
        logger.info(
            f"Regenerated results: TSR: {results.task_success_rate:.1%}, "
            f"ECR: {results.execution_completion_rate:.1%}"
        )
        
        return results
    
    def regenerate_output_files(self, max_tasks: Optional[int] = None):
        """
        Regenerate CSV and JSON output files from existing trace files.
        
        Args:
            max_tasks: Optional limit on number of tasks to include
        """
        results = self.regenerate_results_from_traces(max_tasks)
        
        # Generate report files
        self.reporter.generate_full_report(results, self.output_dir)
        
        logger.info("Successfully regenerated output files from trace files")

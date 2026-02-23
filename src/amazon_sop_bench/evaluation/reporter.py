# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Result reporter for formatting and saving evaluation results."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

from amazon_sop_bench.types import EvaluationResults, TaskResult
from amazon_sop_bench.config import get_config
from amazon_sop_bench.utils.logging import get_logger

logger = get_logger(__name__)

# Optional rich import for pretty console output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    logger.warning("Rich not available - basic console output only")


class ResultReporter:
    """
    Reporter for formatting and saving evaluation results.
    
    Supports multiple output formats:
    - JSON (structured data)
    - CSV (for analysis)
    - Console (pretty-printed summary)
    - Execution traces (for debugging)
    
    Based on existing reporting logic from SOPBenchmarkGenerator.
    
    Example:
        >>> reporter = ResultReporter()
        >>> reporter.save_json(results, "results.json")
        >>> reporter.print_summary(results)
    """
    
    def __init__(self):
        """Initialize result reporter."""
        self.config = get_config()
        self.console = Console() if RICH_AVAILABLE else None
    
    def save_json(
        self,
        results: EvaluationResults,
        output_path: Path
    ) -> None:
        """
        Save results to JSON file.
        
        Args:
            results: EvaluationResults to save
            output_path: Path to save JSON file
        """
        logger.info(f"Saving results to JSON: {output_path}")
        
        # Convert to dictionary
        results_dict = results.to_dict()
        
        # Add metadata
        results_dict["metadata"] = {
            "generated_by": "amazon-sop-bench",
            "version": "0.1.0",
            "timestamp": pd.Timestamp.now().isoformat(),
        }
        
        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results_dict, f, indent=2, default=str)
        
        logger.info(f"Results saved to {output_path}")
    
    def save_csv(
        self,
        results: EvaluationResults,
        output_path: Path
    ) -> None:
        """
        Save detailed results to CSV file.
        
        Args:
            results: EvaluationResults to save
            output_path: Path to save CSV file
        """
        logger.info(f"Saving detailed results to CSV: {output_path}")
        
        # Create DataFrame from task results
        rows = []
        for task_result in results.task_results:
            row = {
                "task_id": task_result.task_id,
                "success": task_result.success,
                "predicted_output": task_result.predicted_output,
                "expected_output": task_result.expected_output,
                "execution_time": task_result.execution_time,
                "error": task_result.error,
                "num_tool_calls": len(task_result.tool_calls),
            }
            
            # Add tool call details
            for i, tool_call in enumerate(task_result.tool_calls):
                row[f"tool_{i+1}_name"] = tool_call.get("tool", "")
                row[f"tool_{i+1}_success"] = tool_call.get("success", False)
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        
        logger.info(f"Detailed results saved to {output_path}")
    
    def print_summary(self, results: EvaluationResults) -> None:
        """
        Print formatted summary to console.
        
        Args:
            results: EvaluationResults to display
        """
        if RICH_AVAILABLE:
            self._print_rich_summary(results)
        else:
            self._print_basic_summary(results)
    
    def _print_rich_summary(self, results: EvaluationResults) -> None:
        """Print summary using Rich formatting."""
        console = self.console
        
        # Main results panel
        summary_text = f"""[bold]Benchmark:[/bold] {results.benchmark_name}
[bold]Agent:[/bold] {results.agent_type}
[bold]Model:[/bold] {results.model_id}

[bold green]Results:[/bold green]
  Task Success Rate:     {results.task_success_rate:.1%} ({results.num_correct}/{results.num_tasks})
  Execution Completion:  {results.execution_completion_rate:.1%} ({results.num_completed}/{results.num_tasks})
  Conditional TSR:       {results.conditional_task_success_rate:.1%} ({results.num_correct}/{results.num_completed})
  
[bold blue]Performance:[/bold blue]
  Average Execution Time: {results.avg_execution_time:.2f}s per task"""
        
        console.print(Panel(summary_text, title="✓ Evaluation Complete", border_style="green"))
        
        # Tool accuracy table
        if results.tool_accuracy:
            table = Table(title="Tool Accuracy")
            table.add_column("Tool", style="cyan")
            table.add_column("Accuracy", justify="right", style="green")
            
            for tool_name, accuracy in results.tool_accuracy.items():
                if tool_name != "overall":
                    table.add_row(tool_name, f"{accuracy:.1%}")
            
            if "overall" in results.tool_accuracy:
                table.add_row("Overall", f"{results.tool_accuracy['overall']:.1%}", style="bold")
            
            console.print(table)
        
        # Error distribution
        if results.error_distribution and any(results.error_distribution.values()):
            error_table = Table(title="Error Distribution")
            error_table.add_column("Error Type", style="red")
            error_table.add_column("Count", justify="right")
            
            for error_type, count in results.error_distribution.items():
                if count > 0:
                    error_table.add_row(error_type.replace("_", " ").title(), str(count))
            
            console.print(error_table)
    
    def _print_basic_summary(self, results: EvaluationResults) -> None:
        """Print basic summary without Rich formatting."""
        print("\n" + "="*50)
        print("EVALUATION COMPLETE")
        print("="*50)
        print(f"Benchmark: {results.benchmark_name}")
        print(f"Agent: {results.agent_type}")
        print(f"Model: {results.model_id}")
        print()
        print("Results:")
        print(f"  Task Success Rate:     {results.task_success_rate:.1%} ({results.num_correct}/{results.num_tasks})")
        print(f"  Execution Completion:  {results.execution_completion_rate:.1%} ({results.num_completed}/{results.num_tasks})")
        print(f"  Conditional TSR:       {results.conditional_task_success_rate:.1%} ({results.num_correct}/{results.num_completed})")
        print()
        print("Performance:")
        print(f"  Average Execution Time: {results.avg_execution_time:.2f}s per task")
        
        # Tool accuracy
        if results.tool_accuracy:
            print()
            print("Tool Accuracy:")
            for tool_name, accuracy in results.tool_accuracy.items():
                print(f"  {tool_name}: {accuracy:.1%}")
        
        # Error distribution
        if results.error_distribution and any(results.error_distribution.values()):
            print()
            print("Error Distribution:")
            for error_type, count in results.error_distribution.items():
                if count > 0:
                    print(f"  {error_type.replace('_', ' ').title()}: {count}")
        
        print("="*50)
    
    @staticmethod
    def _sanitize_model_id(model_id: str) -> str:
        """
        Convert a model_id into a short, filesystem-safe string.

        Examples:
            "us.anthropic.claude-sonnet-4-5-20250929-v1:0" → "claude-sonnet-4-5"
            "us.meta.llama3-3-70b-instruct-v1:0"          → "llama3-3-70b"
            "openai.gpt-oss-120b-1:0"                     → "gpt-oss-120b-1"
            "us.deepseek.r1-v1:0"                         → "r1"
        """
        if not model_id or model_id == "unknown":
            return "unknown"
        # Remove provider prefixes (us.anthropic., us.meta., openai., etc.)
        name = model_id
        for prefix in ("us.anthropic.", "us.meta.", "us.deepseek.", "meta.", "anthropic.", "openai.", "deepseek."):
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        # Remove version suffix like "-v1:0", "-v2:0", "-20250929-v1:0" etc.
        # Strip from the last occurrence of a date-like pattern or version tag
        import re
        # Remove trailing version like -v1:0, -v2:0
        name = re.sub(r'-v\d+:\d+$', '', name)
        # Remove date stamps like -20250929, -20241022
        name = re.sub(r'-\d{8,}', '', name)
        # Remove "-instruct" suffix
        name = name.replace("-instruct", "")
        # Replace any remaining filesystem-unsafe chars
        name = name.replace(":", "-").replace("/", "-")
        return name

    def save_traces(
        self,
        task_result: TaskResult,
        output_dir: Path
    ) -> None:
        """
        Save execution trace for a single task.
        
        Traces are saved incrementally as each task completes during evaluation.
        
        Args:
            task_result: TaskResult to save trace for
            output_dir: Directory to save trace file
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        self._save_single_trace(task_result, output_dir)
    
    def _save_single_trace(self, task_result: 'TaskResult', output_dir: Path) -> None:
        """
        Save a single trace file.
        
        Args:
            task_result: TaskResult to save trace for
            output_dir: Directory to save trace file
        """
        if not task_result.reasoning_trace:
            return
        
        try:
            trace_file = output_dir / f"trace_{task_result.task_id}.txt"
            with open(trace_file, 'w') as f:
                f.write(f"Task ID: {task_result.task_id}\n")
                f.write(f"Success: {task_result.success}\n")
                f.write(f"Predicted: {task_result.predicted_output}\n")
                f.write(f"Expected: {task_result.expected_output}\n")
                f.write(f"Execution Time: {task_result.execution_time:.2f}s\n")
                f.write(f"Tool Calls: {len(task_result.tool_calls)}\n")
                if task_result.error:
                    f.write(f"Error: {task_result.error}\n")
                f.write("\n" + "="*50 + "\n")
                f.write("REASONING TRACE:\n")
                f.write("="*50 + "\n")
                f.write(task_result.reasoning_trace)
            
            logger.debug(f"Saved trace for task {task_result.task_id} to {trace_file}")
        except Exception as e:
            logger.warning(f"Failed to save trace for task {task_result.task_id}: {e}")
    
    def generate_full_report(
        self,
        results: EvaluationResults,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Path]:
        """
        Generate complete report in all formats.
        
        Args:
            results: EvaluationResults to report
            output_dir: Optional output directory (defaults to config)
            
        Returns:
            Dictionary mapping format names to file paths
        """
        if output_dir is None:
            output_dir = self.config.output_dir
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate base filename including model identifier for uniqueness
        # Sanitize model_id to be filesystem-safe (e.g. "us.meta.llama3-3-70b-instruct-v1:0" → "llama3-3-70b")
        model_suffix = self._sanitize_model_id(results.model_id)
        base_name = f"{results.benchmark_name}_{results.agent_type}_{model_suffix}"
        
        # Save all formats
        files = {}
        
        # JSON
        json_path = output_dir / f"{base_name}_results.json"
        self.save_json(results, json_path)
        files["json"] = json_path
        
        # CSV
        csv_path = output_dir / f"{base_name}_detailed.csv"
        self.save_csv(results, csv_path)
        files["csv"] = csv_path
        
        # Traces are saved incrementally during evaluation, not here
        # Just record the directory path if traces were enabled
        if self.config.save_traces:
            traces_dir = output_dir / f"{base_name}_traces"
            if traces_dir.exists():
                files["traces"] = traces_dir
        
        # Console summary
        self.print_summary(results)
        
        logger.info(f"Full report generated in: {output_dir}")
        
        return files

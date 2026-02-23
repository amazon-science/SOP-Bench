# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Metrics calculator for evaluation results."""

from typing import List, Dict, Any
from amazon_sop_bench.types import TaskResult
from amazon_sop_bench.utils.logging import get_logger

logger = get_logger(__name__)


class MetricsCalculator:
    """
    Calculator for evaluation metrics.
    
    Implements metrics from the SOP-Bench paper:
    - Task Success Rate (TSR): Overall success rate (TSR = ECR × C-TSR)
    - Execution Completion Rate (ECR): Percentage of tasks that completed without errors
    - Conditional Task Success Rate (C-TSR): Accuracy of completed tasks only
    - Tool Accuracy: Correctness of tool calls
    
    Note: TSR = ECR × C-TSR
    
    Based on existing evaluation logic from SOPBenchmarkGenerator.
    """
    
    def __init__(self):
        """Initialize metrics calculator."""
        self.logger = logger
    
    def calculate_all_metrics(
        self,
        task_results: List[TaskResult]
    ) -> Dict[str, Any]:
        """
        Calculate all evaluation metrics.
        
        Args:
            task_results: List of TaskResult objects
            
        Returns:
            Dictionary with all calculated metrics
            
        Example:
            >>> calculator = MetricsCalculator()
            >>> metrics = calculator.calculate_all_metrics(results)
            >>> print(f"TSR: {metrics['task_success_rate']:.1%}")
        """
        if not task_results:
            logger.warning("No task results provided")
            return self._empty_metrics()
        
        logger.info(f"Calculating metrics for {len(task_results)} task results")
        
        # Calculate core metrics
        tsr = self.calculate_task_success_rate(task_results)
        ecr = self.calculate_execution_completion_rate(task_results)
        c_tsr = self.calculate_conditional_tsr(task_results)
        tool_accuracy = self.calculate_tool_accuracy(task_results)
        avg_time = self.calculate_avg_execution_time(task_results)
        error_dist = self.analyze_error_distribution(task_results)
        
        metrics = {
            "task_success_rate": tsr,
            "execution_completion_rate": ecr,
            "conditional_task_success_rate": c_tsr,
            "tool_accuracy": tool_accuracy,
            "avg_execution_time": avg_time,
            "error_distribution": error_dist,
            "num_tasks": len(task_results),
            "num_completed": sum(1 for r in task_results 
                               if r.success or (r.error and "output mismatch" in r.error.lower())),
            "num_correct": sum(1 for r in task_results if self._is_task_correct(r)),
        }
        
        logger.info(f"Metrics calculated: TSR={tsr:.1%}, ECR={ecr:.1%}, C-TSR={c_tsr:.1%}")
        
        return metrics
    
    def calculate_task_success_rate(self, task_results: List[TaskResult]) -> float:
        """
        Calculate Task Success Rate (TSR).
        
        TSR = number of correct tasks / total tasks
        
        Args:
            task_results: List of TaskResult objects
            
        Returns:
            TSR as float between 0 and 1
        """
        if not task_results:
            return 0.0
        
        total = len(task_results)
        # Use the same logic as C-TSR for consistency
        correct = sum(1 for r in task_results if self._is_task_correct(r))
        
        tsr = correct / total
        logger.debug(f"TSR: {correct}/{total} = {tsr:.2%}")
        
        return tsr
    
    def calculate_execution_completion_rate(self, task_results: List[TaskResult]) -> float:
        """
        Calculate Execution Completion Rate (ECR).
        
        ECR = number of tasks that executed without runtime errors / total tasks
        
        Note: This counts tasks where the agent executed successfully, regardless of
        whether the final answer was correct. A task is "completed" if the agent
        ran without crashing, even if it gave the wrong answer.
        
        Args:
            task_results: List of TaskResult objects
            
        Returns:
            ECR as float between 0 and 1
        """
        if not task_results:
            return 0.0
        
        total = len(task_results)
        # Count tasks that executed without runtime errors
        # (exclude tasks that failed due to output mismatch - those still "completed")
        completed = sum(1 for r in task_results 
                       if r.success or (r.error and "output mismatch" in r.error.lower()))
        
        ecr = completed / total
        logger.debug(f"ECR: {completed}/{total} = {ecr:.2%}")
        
        return ecr
    
    def calculate_conditional_tsr(self, task_results: List[TaskResult]) -> float:
        """
        Calculate Conditional Task Success Rate (C-TSR).
        
        C-TSR = number of correct tasks / number of completed tasks
        
        Note: Uses the same definition of "completed" as ECR - tasks that executed
        without runtime errors, regardless of whether the answer was correct.
        
        Args:
            task_results: List of TaskResult objects
            
        Returns:
            C-TSR as float between 0 and 1
        """
        if not task_results:
            return 0.0
        
        # Use same definition of "completed" as ECR
        completed = [r for r in task_results 
                    if r.success or (r.error and "output mismatch" in r.error.lower())]
        
        if not completed:
            return 0.0
        
        # Count correct answers among completed tasks
        correct = sum(1 for r in completed if self._is_task_correct(r))
        c_tsr = correct / len(completed)
        
        logger.debug(f"C-TSR: {correct}/{len(completed)} = {c_tsr:.2%}")
        
        return c_tsr
    
    def _is_task_correct(self, result: TaskResult) -> bool:
        """
        Check if a task result is correct.
        
        Trusts the success flag set by the evaluator, which uses proper fuzzy matching
        via the OutputParser.compare_decisions() method. This avoids inconsistency
        between the evaluator's comparison logic and metrics calculation.
        
        Args:
            result: TaskResult object
            
        Returns:
            True if task was marked as successful by the evaluator
        """
        # Trust the success flag - it was already set by the evaluator using
        # proper fuzzy matching via parser.compare_decisions()
        return result.success
    
    def calculate_tool_accuracy(self, task_results: List[TaskResult]) -> Dict[str, float]:
        """
        Calculate tool accuracy metrics.
        
        Args:
            task_results: List of TaskResult objects
            
        Returns:
            Dictionary with tool accuracy metrics
        """
        tool_stats = {}
        
        for result in task_results:
            for tool_call in result.tool_calls:
                tool_name = tool_call.get("tool", "unknown")
                success = tool_call.get("success", False)
                
                if tool_name not in tool_stats:
                    tool_stats[tool_name] = {"total": 0, "correct": 0}
                
                tool_stats[tool_name]["total"] += 1
                if success:
                    tool_stats[tool_name]["correct"] += 1
        
        # Calculate accuracy per tool
        tool_accuracy = {}
        for tool_name, stats in tool_stats.items():
            if stats["total"] > 0:
                accuracy = stats["correct"] / stats["total"]
                tool_accuracy[tool_name] = accuracy
        
        # Calculate overall tool accuracy
        if tool_stats:
            total_calls = sum(s["total"] for s in tool_stats.values())
            correct_calls = sum(s["correct"] for s in tool_stats.values())
            tool_accuracy["overall"] = correct_calls / total_calls if total_calls > 0 else 0.0
        
        logger.debug(f"Tool accuracy calculated for {len(tool_stats)} tools")
        
        return tool_accuracy
    
    def calculate_avg_execution_time(self, task_results: List[TaskResult]) -> float:
        """
        Calculate average execution time per task.
        
        Args:
            task_results: List of TaskResult objects
            
        Returns:
            Average execution time in seconds
        """
        if not task_results:
            return 0.0
        
        total_time = sum(r.execution_time for r in task_results)
        avg_time = total_time / len(task_results)
        
        logger.debug(f"Average execution time: {avg_time:.2f} seconds")
        
        return avg_time
    
    def analyze_error_distribution(self, task_results: List[TaskResult]) -> Dict[str, int]:
        """
        Analyze distribution of error types.
        
        Args:
            task_results: List of TaskResult objects
            
        Returns:
            Dictionary mapping error types to counts
        """
        error_dist = {
            "output_mismatch": 0,
            "parsing_error": 0,
            "tool_selection_error": 0,
            "parameter_error": 0,
            "execution_error": 0,
            "timeout_error": 0,
            "unknown_error": 0,
        }
        
        for result in task_results:
            if not result.success and result.error:
                error_msg = result.error.lower()
                
                # Check for output mismatch (agent completed but answer was wrong)
                if "output mismatch" in error_msg:
                    error_dist["output_mismatch"] += 1
                # Check for parsing errors (couldn't extract decision from output)
                elif "parsing" in error_msg or "could not parse" in error_msg or "failed to extract" in error_msg:
                    error_dist["parsing_error"] += 1
                # Check for tool errors
                elif "tool" in error_msg and ("not found" in error_msg or "invalid" in error_msg):
                    error_dist["tool_selection_error"] += 1
                # Check for parameter errors
                elif "parameter" in error_msg or "missing" in error_msg or "required" in error_msg:
                    error_dist["parameter_error"] += 1
                # Check for timeout errors
                elif "timeout" in error_msg:
                    error_dist["timeout_error"] += 1
                # Check for execution errors
                elif "execution" in error_msg or "runtime" in error_msg:
                    error_dist["execution_error"] += 1
                # Everything else
                else:
                    error_dist["unknown_error"] += 1
        
        logger.debug(f"Error distribution: {error_dist}")
        
        return error_dist
    
    def _is_correct(self, result: TaskResult) -> bool:
        """
        Check if a task result is correct.
        Handles both single-value and multi-field (dict) comparisons.
        For multi-field, ALL fields must match for True result.
        
        Args:
            result: TaskResult object
            
        Returns:
            True if predicted output matches expected output
        """
        # Handle multi-field dict outputs
        if isinstance(result.expected_output, dict):
            # Expected is dict - this is a multi-field SOP
            if not isinstance(result.predicted_output, dict):
                return False
            
            # Compare each field - ALL must match
            for field_name, expected_value in result.expected_output.items():
                # Get predicted value for this field (case-insensitive lookup)
                predicted_value = None
                for pred_key, pred_val in result.predicted_output.items():
                    if pred_key.lower() == field_name.lower():
                        predicted_value = pred_val
                        break
                
                # If field not found or doesn't match, return False
                if predicted_value is None:
                    return False
                
                # Compare values (normalize to lowercase strings)
                pred_str = str(predicted_value).lower().strip()
                exp_str = str(expected_value).lower().strip()
                
                if pred_str != exp_str:
                    return False
            
            # All fields matched
            return True
        
        # Single-value comparison
        if isinstance(result.predicted_output, dict):
            predicted = str(result.predicted_output.get("decision", "")).lower().strip()
        else:
            predicted = str(result.predicted_output).lower().strip()
        
        expected = str(result.expected_output).lower().strip()
        
        return predicted == expected
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure."""
        return {
            "task_success_rate": 0.0,
            "execution_completion_rate": 0.0,
            "conditional_task_success_rate": 0.0,
            "tool_accuracy": {},
            "avg_execution_time": 0.0,
            "error_distribution": {
                "output_mismatch": 0,
                "parsing_error": 0,
                "tool_selection_error": 0,
                "parameter_error": 0,
                "execution_error": 0,
                "timeout_error": 0,
                "unknown_error": 0,
            },
            "num_tasks": 0,
            "num_completed": 0,
            "num_correct": 0,
        }

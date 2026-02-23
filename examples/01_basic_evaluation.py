#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""
Basic Evaluation Example

This example demonstrates the simplest way to evaluate an agent on a benchmark.
Perfect for getting started with SOP-Bench.

Usage:
    python 01_basic_evaluation.py
"""

from amazon_sop_bench import evaluate

def main():
    """Run a basic evaluation."""
    
    print("=" * 60)
    print("SOP-Bench: Basic Evaluation Example")
    print("=" * 60)
    print()
    
    # Evaluate the function-calling agent on content_flagging benchmark
    # Using max_tasks=1 for a quick test
    print("Running evaluation...")
    print("Benchmark: content_flagging")
    print("Agent: function_calling")
    print("Tasks: 1 (quick test)")
    print()
    
    results = evaluate(
        benchmark_name="content_flagging",
        agent_type="function_calling",
        max_tasks=1  # Just test one task
    )
    
    # Display results
    print("=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Task Success Rate (TSR):        {results['task_success_rate']:.1%}")
    print(f"Execution Completion Rate (ECR): {results['execution_completion_rate']:.1%}")
    print(f"Tool Accuracy:                   {results['tool_accuracy']:.1%}")
    print(f"Total Tasks:                     {results['num_tasks']}")
    print(f"Successful Tasks:                {results['num_successful']}")
    print()
    
    # Explain metrics
    print("=" * 60)
    print("Understanding the Metrics")
    print("=" * 60)
    print("• Task Success Rate (TSR): Percentage of tasks with correct decisions")
    print("• Execution Completion Rate (ECR): Percentage of tasks that completed without errors")
    print("• Tool Accuracy: Percentage of tool calls that were correct")
    print()
    print("Note: TSR = ECR × C-TSR (Conditional Task Success Rate)")
    print()
    
    # Next steps
    print("=" * 60)
    print("Next Steps")
    print("=" * 60)
    print("1. Run on all tasks: Remove max_tasks parameter")
    print("2. Try different agent: agent_type='react'")
    print("3. Try different benchmark: benchmark_name='customer_service'")
    print("4. Save traces: save_traces=True")
    print()
    print("Example:")
    print("  results = evaluate(")
    print("      benchmark_name='content_flagging',")
    print("      agent_type='react',")
    print("      save_traces=True")
    print("  )")
    print()

if __name__ == "__main__":
    main()

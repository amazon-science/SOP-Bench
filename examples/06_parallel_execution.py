#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""
Parallel Execution Example

This example demonstrates how to speed up evaluation using parallel workers.

Usage:
    python 06_parallel_execution.py
    python 06_parallel_execution.py --max-workers 10
"""

from amazon_sop_bench import evaluate
import time
import argparse

def run_evaluation(max_workers=None):
    """Run evaluation with specified number of workers."""
    
    benchmark_name = "content_flagging"
    agent_type = "function_calling"
    max_tasks = 20  # Evaluate 20 tasks
    
    print("=" * 60)
    print("SOP-Bench: Parallel Execution Example")
    print("=" * 60)
    print()
    print(f"Benchmark: {benchmark_name}")
    print(f"Agent: {agent_type}")
    print(f"Tasks: {max_tasks}")
    print(f"Workers: {max_workers if max_workers else 1} (sequential)" if max_workers != 1 else "Workers: 1 (sequential)")
    print()
    
    # Run evaluation and measure time
    start_time = time.time()
    
    results = evaluate(
        benchmark_name=benchmark_name,
        agent_type=agent_type,
        max_tasks=max_tasks,
        max_workers=max_workers  # None = sequential, >1 = parallel
    )
    
    elapsed_time = time.time() - start_time
    
    # Display results
    print("=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Task Success Rate: {results['task_success_rate']:.1%}")
    print(f"Execution Time: {elapsed_time:.2f} seconds")
    print(f"Time per Task: {elapsed_time / max_tasks:.2f} seconds")
    print()
    
    return elapsed_time

def main():
    """Compare sequential vs parallel execution."""
    
    parser = argparse.ArgumentParser(description="Parallel execution example")
    parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help="Number of parallel workers (default: sequential)"
    )
    args = parser.parse_args()
    
    if args.max_workers:
        # Run with specified workers
        run_evaluation(max_workers=args.max_workers)
    else:
        # Compare sequential vs parallel
        print("Comparing Sequential vs Parallel Execution")
        print("=" * 60)
        print()
        
        # Sequential
        print("Running Sequential Evaluation...")
        sequential_time = run_evaluation(max_workers=1)
        
        print()
        print("-" * 60)
        print()
        
        # Parallel with 5 workers
        print("Running Parallel Evaluation (5 workers)...")
        parallel_time = run_evaluation(max_workers=5)
        
        # Show speedup
        print()
        print("=" * 60)
        print("Comparison")
        print("=" * 60)
        print(f"Sequential time: {sequential_time:.2f}s")
        print(f"Parallel time (5 workers): {parallel_time:.2f}s")
        print(f"Speedup: {sequential_time / parallel_time:.2f}x")
        print()
        
        # Tips
        print("=" * 60)
        print("Tips for Parallel Execution")
        print("=" * 60)
        print("• Start with 3-5 workers to avoid throttling")
        print("• Increase to 10 workers if no throttling occurs")
        print("• Reduce workers if you get throttling exceptions")
        print("• Monitor AWS Bedrock quotas and limits")
        print("• Sequential is fine for small evaluations (<10 tasks)")
        print()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""
Save Traces Example

This example shows how to save execution traces for debugging agent behavior.

Usage:
    python 07_save_traces.py
"""

from amazon_sop_bench import evaluate
from pathlib import Path
import json

def main():
    """Run evaluation with trace saving enabled."""
    
    print("=" * 60)
    print("SOP-Bench: Save Traces Example")
    print("=" * 60)
    print()
    
    benchmark_name = "content_flagging"
    agent_type = "function_calling"
    max_tasks = 3  # Just a few tasks for demonstration
    
    print(f"Benchmark: {benchmark_name}")
    print(f"Agent: {agent_type}")
    print(f"Tasks: {max_tasks}")
    print(f"Save traces: Yes")
    print()
    
    # Run evaluation with trace saving
    print("Running evaluation...")
    results = evaluate(
        benchmark_name=benchmark_name,
        agent_type=agent_type,
        max_tasks=max_tasks,
        save_traces=True  # Enable trace saving
    )
    
    print()
    print("=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Task Success Rate: {results['task_success_rate']:.1%}")
    print(f"Tool Accuracy: {results['tool_accuracy']:.1%}")
    print()
    
    # Show where traces are saved
    traces_dir = Path(f"results/{benchmark_name}_{agent_type}_traces")
    
    print("=" * 60)
    print("Trace Files")
    print("=" * 60)
    print(f"Location: {traces_dir}")
    print()
    
    if traces_dir.exists():
        trace_files = list(traces_dir.glob("*.json"))
        print(f"Found {len(trace_files)} trace files:")
        print()
        
        for i, trace_file in enumerate(trace_files[:5], 1):  # Show first 5
            print(f"{i}. {trace_file.name}")
            
            # Load and show summary
            with open(trace_file) as f:
                trace = json.load(f)
            
            print(f"   Task ID: {trace.get('task_id', 'N/A')}")
            print(f"   Success: {trace.get('success', 'N/A')}")
            print(f"   Tool calls: {len(trace.get('tool_calls', []))}")
            print()
        
        if len(trace_files) > 5:
            print(f"... and {len(trace_files) - 5} more trace files")
            print()
        
        # Show example trace content
        if trace_files:
            print("=" * 60)
            print("Example Trace Content")
            print("=" * 60)
            
            with open(trace_files[0]) as f:
                trace = json.load(f)
            
            print(f"Task ID: {trace.get('task_id')}")
            print(f"Success: {trace.get('success')}")
            print()
            
            if 'tool_calls' in trace and trace['tool_calls']:
                print("Tool Calls:")
                for i, call in enumerate(trace['tool_calls'][:3], 1):
                    print(f"  {i}. {call.get('tool', 'unknown')}")
                    print(f"     Parameters: {call.get('parameters', {})}")
                    print()
            
            if 'reasoning' in trace:
                print("Reasoning:")
                reasoning = trace['reasoning']
                if len(reasoning) > 200:
                    print(f"  {reasoning[:200]}...")
                else:
                    print(f"  {reasoning}")
                print()
            
            if 'output' in trace:
                print("Output:")
                output = trace['output']
                if len(output) > 200:
                    print(f"  {output[:200]}...")
                else:
                    print(f"  {output}")
                print()
    else:
        print("[Warning] Traces directory not found")
        print("This might happen if evaluation failed or no tasks were run")
        print()
    
    # Tips
    print("=" * 60)
    print("Using Traces for Debugging")
    print("=" * 60)
    print("1. Check 'success' field to identify failed tasks")
    print("2. Review 'tool_calls' to verify correct tool usage")
    print("3. Examine 'reasoning' to understand agent's logic")
    print("4. Compare 'output' with expected decision")
    print("5. Look for patterns in failed tasks")
    print()
    print("Trace files are JSON format - easy to parse programmatically")
    print()

if __name__ == "__main__":
    main()

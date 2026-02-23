#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""
Batch Evaluation Example

This example shows how to evaluate multiple benchmarks and compare results.

Usage:
    python 05_batch_evaluation.py
"""

from amazon_sop_bench import list_benchmarks, evaluate
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
import json
from pathlib import Path

def main():
    """Run batch evaluation across multiple benchmarks."""
    
    console = Console()
    
    console.print("\n[bold cyan]SOP-Bench: Batch Evaluation[/bold cyan]\n")
    
    # Configuration
    agent_type = "function_calling"
    max_tasks = 10  # Limit tasks for faster testing
    output_file = "batch_results.json"
    
    console.print(f"[bold]Configuration:[/bold]")
    console.print(f"  Agent: {agent_type}")
    console.print(f"  Max tasks per benchmark: {max_tasks}")
    console.print(f"  Output file: {output_file}")
    console.print()
    
    # Get all benchmarks
    benchmarks = list_benchmarks()
    console.print(f"Found {len(benchmarks)} benchmarks")
    console.print()
    
    # Run evaluations
    all_results = {}
    
    with Progress() as progress:
        task = progress.add_task(
            "[cyan]Evaluating benchmarks...", 
            total=len(benchmarks)
        )
        
        for benchmark in benchmarks:
            benchmark_name = benchmark['name']
            
            console.print(f"Evaluating: [cyan]{benchmark_name}[/cyan]")
            
            try:
                results = evaluate(
                    benchmark_name=benchmark_name,
                    agent_type=agent_type,
                    max_tasks=max_tasks
                )
                
                all_results[benchmark_name] = {
                    "task_success_rate": results['task_success_rate'],
                    "execution_completion_rate": results['execution_completion_rate'],
                    "tool_accuracy": results['tool_accuracy'],
                    "num_tasks": results['num_tasks'],
                    "num_successful": results['num_successful']
                }
                
                console.print(f"  ✓ TSR: {results['task_success_rate']:.1%}")
                
            except Exception as e:
                console.print(f"  ✗ Error: {str(e)}", style="red")
                all_results[benchmark_name] = {"error": str(e)}
            
            progress.update(task, advance=1)
            console.print()
    
    # Display summary table
    console.print("\n[bold]Summary Results[/bold]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Benchmark", style="cyan", width=20)
    table.add_column("TSR", justify="right", style="green", width=10)
    table.add_column("ECR", justify="right", style="yellow", width=10)
    table.add_column("Tool Acc", justify="right", style="blue", width=10)
    table.add_column("Tasks", justify="right", style="white", width=8)
    
    for benchmark_name, results in all_results.items():
        if "error" not in results:
            table.add_row(
                benchmark_name,
                f"{results['task_success_rate']:.1%}",
                f"{results['execution_completion_rate']:.1%}",
                f"{results['tool_accuracy']:.1%}",
                str(results['num_tasks'])
            )
        else:
            table.add_row(
                benchmark_name,
                "[red]ERROR[/red]",
                "-",
                "-",
                "-"
            )
    
    console.print(table)
    console.print()
    
    # Calculate aggregate statistics
    successful_benchmarks = [
        r for r in all_results.values() if "error" not in r
    ]
    
    if successful_benchmarks:
        avg_tsr = sum(r['task_success_rate'] for r in successful_benchmarks) / len(successful_benchmarks)
        avg_ecr = sum(r['execution_completion_rate'] for r in successful_benchmarks) / len(successful_benchmarks)
        avg_tool_acc = sum(r['tool_accuracy'] for r in successful_benchmarks) / len(successful_benchmarks)
        
        console.print("[bold]Aggregate Statistics:[/bold]")
        console.print(f"  Average TSR: {avg_tsr:.1%}")
        console.print(f"  Average ECR: {avg_ecr:.1%}")
        console.print(f"  Average Tool Accuracy: {avg_tool_acc:.1%}")
        console.print()
    
    # Save results to file
    output_path = Path(output_file)
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    console.print(f"[green]✓[/green] Results saved to: {output_path}")
    console.print()
    
    # Show best and worst performing benchmarks
    if successful_benchmarks:
        sorted_results = sorted(
            [(name, r) for name, r in all_results.items() if "error" not in r],
            key=lambda x: x[1]['task_success_rate'],
            reverse=True
        )
        
        console.print("[bold]Best Performing:[/bold]")
        for name, results in sorted_results[:3]:
            console.print(f"  • {name}: {results['task_success_rate']:.1%}")
        console.print()
        
        console.print("[bold]Most Challenging:[/bold]")
        for name, results in sorted_results[-3:]:
            console.print(f"  • {name}: {results['task_success_rate']:.1%}")
        console.print()

if __name__ == "__main__":
    main()

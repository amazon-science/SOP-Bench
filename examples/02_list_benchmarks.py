#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""
List Benchmarks Example

This example shows how to discover and explore available benchmarks.

Usage:
    python 02_list_benchmarks.py
"""

from amazon_sop_bench import list_benchmarks
from rich.console import Console
from rich.table import Table

def main():
    """List and display all available benchmarks."""
    
    console = Console()
    
    console.print("\n[bold cyan]SOP-Bench: Available Benchmarks[/bold cyan]\n")
    
    # Get all benchmarks
    benchmarks = list_benchmarks()
    
    # Create a rich table
    table = Table(title="Available Benchmarks", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", width=20)
    table.add_column("Domain", style="green", width=15)
    table.add_column("Tasks", justify="right", style="yellow", width=8)
    table.add_column("Tools", justify="right", style="blue", width=8)
    table.add_column("Description", style="white", width=50)
    
    # Add rows
    for benchmark in benchmarks:
        table.add_row(
            benchmark['name'],
            benchmark.get('domain', 'N/A'),
            str(benchmark['num_tasks']),
            str(benchmark['num_tools']),
            benchmark.get('description', 'N/A')[:50]
        )
    
    console.print(table)
    console.print()
    
    # Summary statistics
    total_tasks = sum(b['num_tasks'] for b in benchmarks)
    total_tools = sum(b['num_tools'] for b in benchmarks)
    
    console.print(f"[bold]Summary:[/bold]")
    console.print(f"  • Total Benchmarks: {len(benchmarks)}")
    console.print(f"  • Total Tasks: {total_tasks}")
    console.print(f"  • Total Tools: {total_tools}")
    console.print()
    
    # Show example usage
    console.print("[bold]Example Usage:[/bold]")
    console.print()
    console.print("[cyan]# Evaluate a specific benchmark[/cyan]")
    console.print("from amazon_sop_bench import evaluate")
    console.print()
    console.print("results = evaluate(")
    console.print(f"    benchmark_name='{benchmarks[0]['name']}',")
    console.print("    agent_type='function_calling'")
    console.print(")")
    console.print()
    
    # Show benchmark details
    console.print("[bold]Benchmark Details:[/bold]")
    console.print()
    for i, benchmark in enumerate(benchmarks[:3], 1):  # Show first 3
        console.print(f"[bold cyan]{i}. {benchmark['name']}[/bold cyan]")
        console.print(f"   Domain: {benchmark.get('domain', 'N/A')}")
        console.print(f"   Tasks: {benchmark['num_tasks']}")
        console.print(f"   Tools: {benchmark['num_tools']}")
        if 'description' in benchmark:
            console.print(f"   Description: {benchmark['description']}")
        console.print()
    
    if len(benchmarks) > 3:
        console.print(f"[dim]... and {len(benchmarks) - 3} more benchmarks[/dim]")
        console.print()

if __name__ == "__main__":
    main()

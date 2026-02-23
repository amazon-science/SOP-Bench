# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Results command for CLI."""

import click
import json
from pathlib import Path
from typing import Optional

from amazon_sop_bench.utils.logging import get_logger

logger = get_logger(__name__)

# Optional rich import for pretty output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


@click.command()
@click.argument("results_file", type=click.Path(exists=True))
@click.option(
    "--format", "output_format",
    type=click.Choice(["summary", "detailed", "json"]),
    default="summary",
    help="Display format"
)
@click.option(
    "--export",
    type=click.Path(),
    help="Export detailed results to CSV"
)
def results_cmd(
    results_file: str,
    output_format: str,
    export: Optional[str]
):
    """
    Display evaluation results from a JSON file.
    
    Shows formatted evaluation results including metrics,
    tool accuracy, and error distribution.
    
    RESULTS_FILE: Path to JSON results file
    
    Examples:
        sop-bench results results.json
        sop-bench results results.json --format detailed
        sop-bench results results.json --export detailed.csv
    """
    logger.info(f"Loading results from: {results_file}")
    
    try:
        # Load results
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        # Display results
        if output_format == "json":
            click.echo(json.dumps(results, indent=2))
        elif output_format == "detailed":
            _print_detailed_results(results)
        else:
            # Summary format (default)
            _print_summary_results(results)
        
        # Export to CSV if requested
        if export:
            _export_to_csv(results, export)
            click.echo(f"\nDetailed results exported to: {export}")
        
    except FileNotFoundError:
        click.echo(f"Error: Results file not found: {results_file}", err=True)
        raise click.Abort()
    except json.JSONDecodeError:
        click.echo(f"Error: Invalid JSON file: {results_file}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error(f"Error displaying results: {e}")
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


def _print_summary_results(results: dict):
    """Print summary results."""
    if RICH_AVAILABLE:
        _print_rich_summary(results)
    else:
        _print_basic_summary(results)


def _print_detailed_results(results: dict):
    """Print detailed results."""
    _print_summary_results(results)
    
    # Additional details
    if RICH_AVAILABLE:
        console = Console()
        
        # Tool accuracy details
        if results.get("tool_accuracy"):
            table = Table(title="Tool Accuracy Details")
            table.add_column("Tool", style="cyan")
            table.add_column("Accuracy", justify="right", style="green")
            
            for tool_name, accuracy in results["tool_accuracy"].items():
                if tool_name != "overall":
                    table.add_row(tool_name, f"{accuracy:.1%}")
            
            console.print(table)
        
        # Error distribution
        if results.get("error_distribution"):
            error_table = Table(title="Error Distribution")
            error_table.add_column("Error Type", style="red")
            error_table.add_column("Count", justify="right")
            
            for error_type, count in results["error_distribution"].items():
                if count > 0:
                    error_table.add_row(
                        error_type.replace("_", " ").title(),
                        str(count)
                    )
            
            console.print(error_table)
    else:
        # Basic detailed output
        print("\nTool Accuracy:")
        for tool_name, accuracy in results.get("tool_accuracy", {}).items():
            print(f"  {tool_name}: {accuracy:.1%}")
        
        print("\nError Distribution:")
        for error_type, count in results.get("error_distribution", {}).items():
            if count > 0:
                print(f"  {error_type.replace('_', ' ').title()}: {count}")


def _print_rich_summary(results: dict):
    """Print summary using Rich formatting."""
    console = Console()
    
    # Main results panel
    summary_text = f"""[bold]Benchmark:[/bold] {results.get('benchmark', 'Unknown')}
[bold]Agent:[/bold] {results.get('agent', 'Unknown')}
[bold]Model:[/bold] {results.get('model', 'Unknown')}

[bold green]Results:[/bold green]
  Task Success Rate:     {results.get('task_success_rate', 0):.1%} ({results.get('num_correct', 0)}/{results.get('num_tasks', 0)})
  Execution Completion:  {results.get('execution_completion_rate', 0):.1%} ({results.get('num_completed', 0)}/{results.get('num_tasks', 0)})
  Conditional TSR:       {results.get('conditional_task_success_rate', 0):.1%}
  
[bold blue]Performance:[/bold blue]
  Average Execution Time: {results.get('avg_execution_time', 0):.2f}s per task"""
    
    if results.get('tool_accuracy', {}).get('overall'):
        summary_text += f"\n  Overall Tool Accuracy:  {results['tool_accuracy']['overall']:.1%}"
    
    console.print(Panel(summary_text, title="Evaluation Results", border_style="blue"))


def _print_basic_summary(results: dict):
    """Print basic summary without Rich formatting."""
    print("\n" + "="*50)
    print("EVALUATION RESULTS")
    print("="*50)
    print(f"Benchmark: {results.get('benchmark', 'Unknown')}")
    print(f"Agent: {results.get('agent', 'Unknown')}")
    print(f"Model: {results.get('model', 'Unknown')}")
    print()
    print("Results:")
    print(f"  Task Success Rate:     {results.get('task_success_rate', 0):.1%} ({results.get('num_correct', 0)}/{results.get('num_tasks', 0)})")
    print(f"  Execution Completion:  {results.get('execution_completion_rate', 0):.1%} ({results.get('num_completed', 0)}/{results.get('num_tasks', 0)})")
    print(f"  Conditional TSR:       {results.get('conditional_task_success_rate', 0):.1%}")
    print()
    print("Performance:")
    print(f"  Average Execution Time: {results.get('avg_execution_time', 0):.2f}s per task")
    
    if results.get('tool_accuracy', {}).get('overall'):
        print(f"  Overall Tool Accuracy:  {results['tool_accuracy']['overall']:.1%}")
    
    print("="*50)


def _export_to_csv(results: dict, export_path: str):
    """Export detailed results to CSV."""
    try:
        import pandas as pd
        
        # Create basic results DataFrame
        data = {
            "benchmark": [results.get("benchmark", "")],
            "agent": [results.get("agent", "")],
            "model": [results.get("model", "")],
            "task_success_rate": [results.get("task_success_rate", 0)],
            "execution_completion_rate": [results.get("execution_completion_rate", 0)],
            "conditional_task_success_rate": [results.get("conditional_task_success_rate", 0)],
            "avg_execution_time": [results.get("avg_execution_time", 0)],
            "num_tasks": [results.get("num_tasks", 0)],
            "num_completed": [results.get("num_completed", 0)],
            "num_correct": [results.get("num_correct", 0)],
        }
        
        # Add tool accuracy columns
        for tool_name, accuracy in results.get("tool_accuracy", {}).items():
            data[f"tool_accuracy_{tool_name}"] = [accuracy]
        
        # Add error distribution columns
        for error_type, count in results.get("error_distribution", {}).items():
            data[f"error_{error_type}"] = [count]
        
        df = pd.DataFrame(data)
        df.to_csv(export_path, index=False)
        
    except ImportError:
        click.echo("Warning: pandas not available, cannot export to CSV", err=True)
    except Exception as e:
        click.echo(f"Error exporting to CSV: {e}", err=True)

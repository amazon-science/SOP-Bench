# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""List command for CLI."""

import click
from typing import Optional

from amazon_sop_bench.benchmarks import list_benchmarks
from amazon_sop_bench.utils.logging import get_logger

logger = get_logger(__name__)

# Optional rich import for pretty tables
try:
    from rich.console import Console
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


@click.command()
@click.option(
    "--domain",
    help="Filter by domain (e.g., content_moderation, healthcare)"
)
@click.option(
    "--format", "output_format",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format"
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed information"
)
def list_benchmarks_cmd(
    domain: Optional[str],
    output_format: str,
    verbose: bool
):
    """
    List available benchmarks.
    
    Shows all benchmarks with their key statistics including
    number of tasks, tools, and complexity scores.
    
    Examples:
        sop-bench list
        sop-bench list --domain content_moderation
        sop-bench list --format json
    """
    logger.info("Listing available benchmarks")
    
    try:
        # Get benchmarks
        benchmarks = list_benchmarks(domain=domain)
        
        if not benchmarks:
            if domain:
                click.echo(f"No benchmarks found for domain: {domain}")
            else:
                click.echo("No benchmarks found")
            return
        
        # Output in requested format
        if output_format == "json":
            import json
            click.echo(json.dumps(benchmarks, indent=2))
        elif output_format == "csv":
            import pandas as pd
            df = pd.DataFrame(benchmarks)
            click.echo(df.to_csv(index=False))
        else:
            # Table format (default)
            _print_benchmarks_table(benchmarks, verbose)
            
    except Exception as e:
        logger.error(f"Error listing benchmarks: {e}")
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


def _print_benchmarks_table(benchmarks, verbose: bool = False):
    """Print benchmarks in table format."""
    if RICH_AVAILABLE:
        _print_rich_table(benchmarks, verbose)
    else:
        _print_basic_table(benchmarks, verbose)


def _print_rich_table(benchmarks, verbose: bool = False):
    """Print benchmarks using Rich table."""
    console = Console()
    
    table = Table(title="Available Benchmarks")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Domain", style="green")
    table.add_column("Tasks", justify="right", style="blue")
    table.add_column("Tools", justify="right", style="blue")
    table.add_column("Complexity", justify="right", style="yellow")
    
    if verbose:
        table.add_column("Description", style="dim")
    
    for benchmark in benchmarks:
        row = [
            benchmark["name"],
            benchmark["domain"],
            str(benchmark["num_tasks"]),
            str(benchmark["num_tools"]),
            f"{benchmark['complexity_score']:.1f}" if benchmark.get("complexity_score") else "N/A",
        ]
        
        if verbose:
            description = benchmark.get("description", "")
            # Truncate long descriptions
            if len(description) > 50:
                description = description[:47] + "..."
            row.append(description)
        
        table.add_row(*row)
    
    console.print(table)
    
    # Summary
    total_tasks = sum(b["num_tasks"] for b in benchmarks)
    total_tools = sum(b["num_tools"] for b in benchmarks)
    
    console.print(f"\n[bold]Summary:[/bold] {len(benchmarks)} benchmarks, {total_tasks} total tasks, {total_tools} total tools")


def _print_basic_table(benchmarks, verbose: bool = False):
    """Print benchmarks using basic formatting."""
    # Header
    if verbose:
        print(f"{'Name':<25} {'Domain':<18} {'Tasks':>6} {'Tools':>6} {'Complexity':>10} {'Description'}")
        print("-" * 90)
    else:
        print(f"{'Name':<25} {'Domain':<18} {'Tasks':>6} {'Tools':>6} {'Complexity':>10}")
        print("-" * 70)
    
    # Rows
    for benchmark in benchmarks:
        complexity = f"{benchmark['complexity_score']:.1f}" if benchmark.get("complexity_score") else "N/A"
        
        if verbose:
            description = benchmark.get("description", "")
            if len(description) > 30:
                description = description[:27] + "..."
            print(f"{benchmark['name']:<25} {benchmark['domain']:<18} {benchmark['num_tasks']:>6} {benchmark['num_tools']:>6} {complexity:>10} {description}")
        else:
            print(f"{benchmark['name']:<25} {benchmark['domain']:<18} {benchmark['num_tasks']:>6} {benchmark['num_tools']:>6} {complexity:>10}")
    
    # Summary
    total_tasks = sum(b["num_tasks"] for b in benchmarks)
    total_tools = sum(b["num_tools"] for b in benchmarks)
    
    print(f"\nSummary: {len(benchmarks)} benchmarks, {total_tasks} total tasks, {total_tools} total tools")

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Compute and regenerate metrics commands for CLI."""

import click
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel

from amazon_sop_bench.evaluation.evaluator import Evaluator
from amazon_sop_bench.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


def run_metrics_command(
    benchmark: str,
    agent: str,
    max_tasks: Optional[int],
    output_dir: Optional[str],
    output_format: str,
    regenerate_files: bool
):
    """
    Shared logic for computing/regenerating metrics from trace files.
    
    Args:
        benchmark: Name of the benchmark
        agent: Agent type (react, function_calling)
        max_tasks: Optional limit on number of tasks
        output_dir: Optional output directory path
        output_format: Display format (summary/detailed)
        regenerate_files: Whether to regenerate CSV/JSON files
    """
    action = "regenerating" if regenerate_files else "computing"
    logger.info(f"{action.title()} metrics for: {benchmark} with {agent} agent")
    
    try:
        # Validate benchmark exists
        from amazon_sop_bench.benchmarks import list_benchmarks
        available_benchmarks = [b["name"] for b in list_benchmarks()]
        
        if benchmark not in available_benchmarks:
            click.echo(f"Error: Benchmark '{benchmark}' not found.", err=True)
            click.echo(f"Available benchmarks: {', '.join(available_benchmarks)}")
            raise click.Abort()
        
        # Create agent instance
        agent_instance = _create_agent_instance(agent)
        
        # Set up output directory
        eval_output_dir = None
        if output_dir:
            eval_output_dir = Path(output_dir)
        else:
            from amazon_sop_bench.config import get_config
            eval_output_dir = get_config().output_dir
        
        # Create evaluator
        evaluator = Evaluator(benchmark, agent_instance, output_dir=eval_output_dir)
        
        # Check if trace files exist
        agent_class_name = agent_instance.__class__.__name__
        trace_dir = evaluator.output_dir / f"{benchmark}_{agent_class_name}_traces"
        
        if not trace_dir.exists():
            click.echo(f"Error: No trace directory found at {trace_dir}", err=True)
            click.echo("Make sure you have run the evaluation with --save-traces flag.")
            raise click.Abort()
        
        trace_files = list(trace_dir.glob("trace_*.txt"))
        if not trace_files:
            click.echo(f"Error: No trace files found in {trace_dir}", err=True)
            raise click.Abort()
        
        # Compute metrics from trace files
        status_msg = f"[bold green]{action.title()} metrics from {len(trace_files)} trace files..."
        with console.status(status_msg):
            results = evaluator.regenerate_results_from_traces(max_tasks=max_tasks)
        
        # Display results using rich formatting
        if output_format == "detailed":
            _display_detailed_metrics(results)
        else:
            _display_summary_metrics(results)
        
        # Optionally regenerate output files
        if regenerate_files:
            with console.status("[bold blue]Regenerating CSV and JSON files..."):
                evaluator.regenerate_output_files(max_tasks)
            
            console.print(f"\n[bold green]✓[/bold green] Output files regenerated at: [cyan]{evaluator.output_dir}[/cyan]")
        
        logger.info(f"Metrics {action} completed successfully")
        
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("Make sure trace files exist for the specified benchmark and agent.")
        raise click.Abort()
    except Exception as e:
        logger.error(f"Error {action} metrics: {e}")
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


def _create_agent_instance(agent_type: str):
    """Create agent instance with proper error handling."""
    if agent_type == "react":
        try:
            from amazon_sop_bench.agents import ReActAgent
            return ReActAgent()
        except ImportError:
            raise ImportError(
                "ReAct agent requires langchain. "
                "Install with: pip install langchain langchain-aws"
            )
    elif agent_type == "function_calling":
        try:
            from amazon_sop_bench.agents import FunctionCallingAgent
            return FunctionCallingAgent()
        except ImportError:
            raise ImportError(
                "Function-Calling agent requires boto3. "
                "Install with: pip install boto3"
            )
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


def _display_summary_metrics(results):
    """Display summary metrics with rich formatting."""
    # Core metrics
    tsr = results.task_success_rate
    ecr = results.execution_completion_rate
    ctsr = results.conditional_task_success_rate
    
    summary_text = f"""[bold]Benchmark:[/bold] {results.benchmark_name}
[bold]Agent:[/bold] {results.agent_type}
[bold]Model:[/bold] {results.model_id}

[bold green]Key Metrics:[/bold green]
  TSR (Task Success Rate):       {tsr:.1%} ({results.num_correct}/{results.num_tasks})
  ECR (Execution Completion):    {ecr:.1%} ({results.num_completed}/{results.num_tasks})
  C-TSR (Conditional TSR):       {ctsr:.1%} ({results.num_correct}/{results.num_completed} completed tasks)

[bold blue]Performance:[/bold blue]
  Average Execution Time:        {results.avg_execution_time:.2f}s per task
  Total Tasks Processed:         {results.num_tasks}"""
    
    console.print(Panel(summary_text, title="📊 Metrics Summary", border_style="blue"))
    
    # Show relationship
    console.print(f"\n[dim]Note: TSR = ECR × C-TSR = {ecr:.1%} × {ctsr:.1%} = {tsr:.1%}[/dim]")


def _display_detailed_metrics(results):
    """Display detailed metrics including error breakdown."""
    # First show summary
    _display_summary_metrics(results)
    
    # Error distribution
    if results.error_distribution:
        console.print("\n[bold red]Error Breakdown:[/bold red]")
        
        total_errors = results.num_tasks - results.num_completed
        for error_type, count in results.error_distribution.items():
            if count > 0:
                percentage = (count / results.num_tasks) * 100
                error_name = error_type.replace("_", " ").title()
                console.print(f"  {error_name}: {count} ({percentage:.1f}%)")
        
        console.print(f"  [dim]Total Runtime Errors: {total_errors}[/dim]")
    
    # Tool accuracy if available
    if results.tool_accuracy and len(results.tool_accuracy) > 1:  # More than just 'overall'
        console.print("\n[bold cyan]Tool Accuracy:[/bold cyan]")
        for tool_name, accuracy in results.tool_accuracy.items():
            if tool_name != "overall":
                console.print(f"  {tool_name}: {accuracy:.1%}")
        
        if "overall" in results.tool_accuracy:
            console.print(f"  [bold]Overall: {results.tool_accuracy['overall']:.1%}[/bold]")


# CLI Command Functions

@click.command()
@click.argument("benchmark", required=True)
@click.option(
    "--agent", "-a",
    default="react",
    help="Agent type to compute metrics for"
)
@click.option(
    "--max-tasks",
    type=int,
    help="Limit number of tasks to include"
)
@click.option(
    "--output-dir",
    type=click.Path(),
    help="Output directory containing trace files"
)
@click.option(
    "--format", "output_format",
    type=click.Choice(["summary", "detailed"]),
    default="summary",
    help="Display format"
)
def compute_metrics_cmd(
    benchmark: str,
    agent: str,
    max_tasks: Optional[int],
    output_dir: Optional[str],
    output_format: str
):
    """
    Compute evaluation metrics from existing trace files.
    
    Quickly computes ECR, C-TSR, and TSR metrics from trace files
    without regenerating full CSV/JSON output files.
    
    BENCHMARK: Name of the benchmark to compute metrics for
    
    Examples:
        sop-bench compute-metrics dangerous_goods --agent react
        sop-bench compute-metrics dangerous_goods --agent react --max-tasks 100
        sop-bench compute-metrics content_flagging --agent function_calling --format detailed
    
    Note: If you need to clean up error traces and re-evaluate:
        1. Clean error traces: ./cleanup_traces.sh results/*_traces  
        2. Re-evaluate missing tasks: sop-bench evaluate BENCHMARK --agent AGENT --resume
        3. Compute updated metrics: sop-bench compute-metrics BENCHMARK --agent AGENT
    """
    run_metrics_command(
        benchmark=benchmark,
        agent=agent,
        max_tasks=max_tasks,
        output_dir=output_dir,
        output_format=output_format,
        regenerate_files=False  # compute-metrics only displays, doesn't regenerate files
    )


@click.command()
@click.argument("benchmark", required=True)
@click.option(
    "--agent", "-a",
    default="react",
    help="Agent type that was used for evaluation"
)
@click.option(
    "--max-tasks",
    type=int,
    help="Limit number of tasks to include in regeneration"
)
def regenerate_cmd(
    benchmark: str,
    agent: str,
    max_tasks: Optional[int]
):
    """
    Regenerate evaluation metrics from trace files.
    
    This command bypasses potentially stale CSV/JSON files and regenerates
    metrics directly from trace files, which are the source of truth for 
    completed evaluations. Use this when --resume shows incorrect metrics.
    
    BENCHMARK: Name of the benchmark to regenerate metrics for
    
    Examples:
        sop-bench regenerate content_flagging --agent react
        sop-bench regenerate dangerous_goods --agent function_calling
    
    Workflow for cleaning up error traces and re-evaluating:
        1. Clean error traces: ./cleanup_traces.sh results/*_traces
        2. Re-evaluate missing tasks: sop-bench evaluate BENCHMARK --agent AGENT --resume
        3. Regenerate metrics and files: sop-bench regenerate BENCHMARK --agent AGENT
    """
    run_metrics_command(
        benchmark=benchmark,
        agent=agent,
        max_tasks=max_tasks,
        output_dir=None,  # Use default output directory
        output_format="summary",  # Use summary format for regenerate
        regenerate_files=True  # regenerate command always regenerates files
    )


def regenerate_metrics_internal(benchmark_name: str, agent_type: str, max_tasks: int = None):
    """
    Legacy function for backward compatibility.
    
    Args:
        benchmark_name: Name of benchmark (e.g., 'content_flagging')
        max_tasks: Optional limit on number of tasks
    """
    run_metrics_command(
        benchmark=benchmark_name,
        agent=agent_type,
        max_tasks=max_tasks,
        output_dir=None,
        output_format="summary",
        regenerate_files=True
    )

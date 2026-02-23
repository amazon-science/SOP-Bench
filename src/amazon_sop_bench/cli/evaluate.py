# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Evaluate command for CLI."""

import click
from pathlib import Path
from typing import Optional

from rich.console import Console

from amazon_sop_bench.evaluation import evaluate
from amazon_sop_bench.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


@click.command()
@click.argument("benchmark", required=True)
@click.option(
    "--agent", "-a",
    type=click.Choice(["react", "function_calling"]),
    default="react",
    help="Agent type to use (react=LangChain AgentExecutor)"
)
@click.option(
    "--model", "-m",
    help="Override model ID (e.g., claude-3.5-sonnet)"
)
@click.option(
    "--max-tasks",
    type=int,
    help="Limit number of tasks (for testing)"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Output file path (JSON format)"
)
@click.option(
    "--output-dir",
    type=click.Path(),
    help="Output directory for all result files"
)
@click.option(
    "--save-traces",
    is_flag=True,
    help="Save execution traces for debugging"
)
@click.option(
    "--no-progress",
    is_flag=True,
    help="Disable progress bars"
)
@click.option(
    "--resume",
    is_flag=True,
    help="Resume from existing results if available (automatically detects and fills gaps)"
)
@click.option(
    "--max-workers",
    type=int,
    default=1,
    help="Number of parallel worker threads (default: 1, use >1 for parallelization)"
)
def evaluate_cmd(
    benchmark: str,
    agent: str,
    model: Optional[str],
    max_tasks: Optional[int],
    output: Optional[str],
    output_dir: Optional[str],
    save_traces: bool,
    no_progress: bool,
    resume: bool,
    max_workers: int
):
    """
    Run evaluation on a benchmark.
    
    Evaluates the specified agent on the given benchmark and displays
    results including Task Success Rate (TSR), Execution Completion Rate (ECR),
    and tool accuracy metrics.
    
    BENCHMARK: Name of the benchmark to evaluate (e.g., content_flagging)
    
    Examples:
        sop-bench evaluate content_flagging
        sop-bench evaluate content_flagging --agent function_calling
        sop-bench evaluate content_flagging --max-tasks 10 --output results.json
        sop-bench evaluate customer_service --agent react --save-traces
        sop-bench evaluate dangerous_goods --agent react --resume
    """
    logger.info(f"Starting evaluation: {benchmark} with {agent} agent")
    
    try:
        # Validate benchmark exists
        from amazon_sop_bench.benchmarks import list_benchmarks
        available_benchmarks = [b["name"] for b in list_benchmarks()]
        
        if benchmark not in available_benchmarks:
            click.echo(f"Error: Benchmark '{benchmark}' not found.", err=True)
            click.echo(f"Available benchmarks: {', '.join(available_benchmarks)}")
            raise click.Abort()
        
        # Show what we're about to do
        click.echo(f"Evaluating [bold cyan]{benchmark}[/bold cyan] with [bold green]{agent}[/bold green] agent...")
        if max_tasks:
            click.echo(f"Limited to {max_tasks} tasks")
        if model:
            click.echo(f"Using model: {model}")
        
        # Prepare agent configuration
        agent_config = {}
        if model:
            agent_config["model_id"] = model
        
        # Set up output directory
        eval_output_dir = None
        if output_dir:
            eval_output_dir = Path(output_dir)
        elif output:
            eval_output_dir = Path(output).parent
        
        # Override config for traces
        if save_traces:
            from amazon_sop_bench.config import get_config
            config = get_config()
            config.save_traces = True
        
        # Run evaluation
        click.echo("\nStarting evaluation...")
        
        results = evaluate(
            benchmark_name=benchmark,
            agent_type=agent,
            max_tasks=max_tasks,
            output_dir=eval_output_dir,
            resume=resume,
            max_workers=max_workers,
            model_id=model
        )
        
        # Save specific output file if requested
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            click.echo(f"\n[bold blue]Results saved to:[/bold blue] {output_path}")
        
        # Show key metrics
        console.print(f"\n[bold green]✓ Evaluation Complete![/bold green]")
        console.print(f"Task Success Rate: [bold]{results['task_success_rate']:.1%}[/bold]")
        console.print(f"Execution Completion Rate: [bold]{results['execution_completion_rate']:.1%}[/bold]")
        
        if results.get('tool_accuracy', {}).get('overall'):
            console.print(f"Tool Accuracy: [bold]{results['tool_accuracy']['overall']:.1%}[/bold]")
        
        logger.info("Evaluation completed successfully")
        
    except ImportError as e:
        if "langchain" in str(e).lower():
            click.echo("Error: ReAct agent requires langchain-aws.", err=True)
            click.echo("Install with: pip install langchain-aws pydantic", err=True)
        elif "boto3" in str(e).lower():
            click.echo("Error: Function-calling agent requires boto3.", err=True)
            click.echo("Install with: pip install boto3", err=True)
        else:
            click.echo(f"Import error: {e}", err=True)
        raise click.Abort()
        
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        click.echo(f"Error: {e}", err=True)
        
        # Provide helpful suggestions
        if "credentials" in str(e).lower() or "aws" in str(e).lower():
            click.echo("\nTip: Make sure your AWS credentials are configured:", err=True)
            click.echo("  1. Set environment variables in .env file", err=True)
            click.echo("  2. Or use AWS CLI: aws configure", err=True)
            click.echo("  3. Or set AWS_PROFILE environment variable", err=True)
        
        raise click.Abort()

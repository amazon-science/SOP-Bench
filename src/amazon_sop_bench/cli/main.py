# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Main CLI interface for amazon-sop-bench."""

import click
from pathlib import Path
from typing import Optional

from amazon_sop_bench import __version__
from amazon_sop_bench.utils.logging import setup_logging, get_logger

# Import CLI commands
from amazon_sop_bench.cli.list import list_benchmarks_cmd
from amazon_sop_bench.cli.evaluate import evaluate_cmd
from amazon_sop_bench.cli.results import results_cmd
from amazon_sop_bench.cli.compute_metrics import compute_metrics_cmd, regenerate_cmd

logger = get_logger(__name__)


@click.group()
@click.version_option(version=__version__)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose logging"
)
@click.option(
    "--log-file",
    type=click.Path(),
    help="Log to file"
)
def cli(verbose: bool, log_file: Optional[str]):
    """
    Amazon SOP-Bench: Benchmark for evaluating LLM agents on SOPs.
    
    This CLI provides commands to list benchmarks, run evaluations,
    and view results.
    
    Examples:
        sop-bench list
        sop-bench evaluate content_flagging --agent react
        sop-bench results results.json
    """
    # Set up logging
    log_level = "DEBUG" if verbose else "INFO"
    log_path = Path(log_file) if log_file else None
    setup_logging(level=log_level, log_file=log_path)
    
    logger.info(f"Amazon SOP-Bench CLI v{__version__}")
    if verbose:
        logger.info("Verbose logging enabled")


# Add commands to the CLI group
cli.add_command(list_benchmarks_cmd, name="list")
cli.add_command(evaluate_cmd, name="evaluate")
cli.add_command(results_cmd, name="results")
cli.add_command(compute_metrics_cmd, name="compute-metrics")
cli.add_command(regenerate_cmd, name="regenerate")


if __name__ == "__main__":
    cli()

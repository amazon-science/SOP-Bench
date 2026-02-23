#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""
Batch evaluation script for AmazonSOPBench.

Runs a single SOP across all models and agents, saving results to a dedicated CSV file.

Usage:
    python batch_evaluate.py --sop content_flagging
    python batch_evaluate.py --sop customer_service --max-tasks 10
    
Output:
    results/{sop_name}_results.csv
"""

import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from amazon_sop_bench import evaluate, list_benchmarks
from amazon_sop_bench.agents import FunctionCallingAgent, ReActAgent
from amazon_sop_bench.config import Config, set_config, get_config


# =============================================================================
# MODEL REGISTRY (18 Models)
# =============================================================================
MODELS: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------------------
    # ANTHROPIC CLAUDE MODELS (8) - All support tool calling
    # -------------------------------------------------------------------------
    "Claude 3.5 Sonnet v2": {
        "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "supports_function_calling": True,
        "config_type": "standard",
        "provider": "Anthropic"
    },
    "Claude 3.7 Sonnet": {
        "model_id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "supports_function_calling": True,
        "config_type": "standard",
        "provider": "Anthropic"
    },
    "Claude Opus 4": {
        "model_id": "us.anthropic.claude-opus-4-20250514-v1:0",
        "supports_function_calling": True,
        "config_type": "standard",
        "provider": "Anthropic"
    },
    "Claude Sonnet 4": {
        "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
        "supports_function_calling": True,
        "config_type": "standard",
        "provider": "Anthropic"
    },
    "Claude Opus 4.1": {
        "model_id": "us.anthropic.claude-opus-4-1-20250805-v1:0",
        "supports_function_calling": True,
        "config_type": "standard",
        "provider": "Anthropic"
    },
    "Claude Haiku 4.5": {
        "model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        "supports_function_calling": True,
        "config_type": "temp_only",  # Claude 4.5 models don't support top_p
        "provider": "Anthropic"
    },
    "Claude Sonnet 4.5": {
        "model_id": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "supports_function_calling": True,
        "config_type": "temp_only",
        "provider": "Anthropic"
    },
    "Claude Opus 4.5": {
        "model_id": "us.anthropic.claude-opus-4-5-20251101-v1:0",
        "supports_function_calling": True,
        "config_type": "temp_only",
        "provider": "Anthropic"
    },
    
    # -------------------------------------------------------------------------
    # META LLAMA MODELS (2)
    # -------------------------------------------------------------------------
    "Llama 3 70B": {
        "model_id": "meta.llama3-70b-instruct-v1:0",
        "supports_function_calling": False,  # Does NOT support tool calling
        "config_type": "standard",
        "provider": "Meta"
    },
    "Llama 3.3 70B": {
        "model_id": "us.meta.llama3-3-70b-instruct-v1:0",
        "supports_function_calling": True,
        "config_type": "standard",
        "provider": "Meta"
    },
    
    # -------------------------------------------------------------------------
    # DEEPSEEK MODELS (1)
    # -------------------------------------------------------------------------
    "DeepSeek R1": {
        "model_id": "us.deepseek.r1-v1:0",
        "supports_function_calling": False,  # Does NOT support tool calling
        "config_type": "standard",
        "provider": "DeepSeek"
    },
    
    # -------------------------------------------------------------------------
    # OPENAI MODELS (4)
    # -------------------------------------------------------------------------
    "OpenAI GPT-OSS 120B": {
        "model_id": "openai.gpt-oss-120b-1:0",
        "supports_function_calling": True,
        "config_type": "standard",
        "provider": "OpenAI"
    },
    "OpenAI GPT-OSS 20B": {
        "model_id": "openai.gpt-oss-20b-1:0",
        "supports_function_calling": True,
        "config_type": "standard",
        "provider": "OpenAI"
    },
    "OpenAI GPT-OSS Safeguard 120B": {
        "model_id": "openai.gpt-oss-safeguard-120b",
        "supports_function_calling": True,
        "config_type": "standard",
        "provider": "OpenAI"
    },
    "OpenAI GPT-OSS Safeguard 20B": {
        "model_id": "openai.gpt-oss-safeguard-20b",
        "supports_function_calling": True,
        "config_type": "standard",
        "provider": "OpenAI"
    },
}

# Agent types
AGENTS = ["react", "function_calling"]

# CSV columns
CSV_COLUMNS = [
    "model_name",
    "agent_type", 
    "model_id",
    "provider",
    "num_tasks",
    "num_completed",
    "num_correct",
    "ecr",
    "c_tsr",
    "tsr",
    "avg_execution_time",
    "tool_accuracy",
    "timestamp",
    "status",
    "error_message"
]


def get_results_file(sop_name: str) -> Path:
    """Get the results file path for a given SOP."""
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    return results_dir / f"{sop_name}_results.csv"


def load_completed_runs(results_file: Path) -> set:
    """Load completed model-agent combinations from existing results file."""
    completed = set()
    
    if not results_file.exists():
        return completed
    
    try:
        with open(results_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Only count as completed if status is success or we have valid results
                if row.get('status') == 'success' or (row.get('tsr') and row.get('tsr') != ''):
                    key = f"{row['model_name']}|{row['agent_type']}"
                    completed.add(key)
    except Exception as e:
        print(f"Warning: Could not load existing results: {e}")
    
    return completed


def write_csv_header(results_file: Path) -> None:
    """Write CSV header if file doesn't exist."""
    if results_file.exists():
        return
    
    with open(results_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()


def safe_round(value: Any, decimals: int = 4) -> float:
    """Safely round a value, handling dicts and None."""
    if value is None:
        return 0.0
    if isinstance(value, dict):
        # If it's a dict, try to extract 'overall' or first value
        if 'overall' in value:
            return round(float(value['overall']), decimals)
        elif 'Overall' in value:
            return round(float(value['Overall']), decimals)
        elif len(value) > 0:
            # Get first value
            return round(float(list(value.values())[0]), decimals)
        return 0.0
    try:
        return round(float(value), decimals)
    except (TypeError, ValueError):
        return 0.0


def append_result_to_csv(
    results_file: Path,
    model_name: str,
    agent_type: str,
    model_config: Dict[str, Any],
    results: Optional[Dict[str, Any]],
    error: Optional[str] = None
) -> None:
    """Append a single result row to the CSV file."""
    
    row = {
        "model_name": model_name,
        "agent_type": agent_type,
        "model_id": model_config["model_id"],
        "provider": model_config["provider"],
        "timestamp": datetime.now().isoformat(),
    }
    
    if error:
        row.update({
            "num_tasks": 0,
            "num_completed": 0,
            "num_correct": 0,
            "ecr": 0.0,
            "c_tsr": 0.0,
            "tsr": 0.0,
            "avg_execution_time": 0.0,
            "tool_accuracy": 0.0,
            "status": "error",
            "error_message": error
        })
    else:
        row.update({
            "num_tasks": results.get("num_tasks", 0),
            "num_completed": results.get("num_completed", 0),
            "num_correct": results.get("num_correct", 0),
            "ecr": safe_round(results.get("execution_completion_rate", 0.0), 4),
            "c_tsr": safe_round(results.get("conditional_task_success_rate", 0.0), 4),
            "tsr": safe_round(results.get("task_success_rate", 0.0), 4),
            "avg_execution_time": safe_round(results.get("avg_execution_time", 0.0), 2),
            "tool_accuracy": safe_round(results.get("tool_accuracy", 0.0), 4),
            "status": "success",
            "error_message": ""
        })
    
    with open(results_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerow(row)


def get_compatible_agents(model_config: Dict[str, Any], agents_filter: Optional[List[str]] = None) -> List[str]:
    """
    Get list of compatible agents for a model.
    
    Args:
        model_config: Model configuration dict
        agents_filter: Optional list of agent names to filter by
        
    Returns:
        List of compatible agent names
    """
    # ReAct variants always supported
    agents = ["react"]
    
    if model_config.get("supports_function_calling", False):
        agents.append("function_calling")
    
    # Filter by specified agents if provided
    if agents_filter:
        agents = [a for a in agents if a in agents_filter]
    
    return agents


def run_single_evaluation(
    sop_name: str,
    model_name: str,
    model_config: Dict[str, Any],
    agent_type: str,
    max_tasks: Optional[int] = None,
    save_traces: bool = False,
    max_workers: int = 1
) -> Dict[str, Any]:
    """
    Run a single model-agent evaluation on an SOP.
    
    Returns:
        Evaluation results dictionary
    """
    # Set model in config
    config = get_config()
    config.aws_model_id = model_config["model_id"]
    config.save_traces = save_traces
    
    # Create agent based on type
    if agent_type == "function_calling":
        agent = FunctionCallingAgent(model_id=model_config["model_id"])
    else:  # react (default)
        agent = ReActAgent(model_id=model_config["model_id"])
    
    # Run evaluation
    results = evaluate(
        benchmark_name=sop_name,
        agent=agent,
        max_tasks=max_tasks,
        max_workers=max_workers
    )
    
    return results


def run_sop_evaluation(
    sop_name: str,
    max_tasks: Optional[int] = None,
    save_traces: bool = False,
    models_filter: Optional[List[str]] = None,
    agents_filter: Optional[List[str]] = None,
    skip_existing: bool = True,
    max_workers: int = 1
) -> None:
    """
    Run all model × agent combinations for a single SOP.
    
    Args:
        sop_name: Name of the SOP to evaluate
        max_tasks: Optional limit on tasks per evaluation (for testing)
        save_traces: Whether to save execution traces
        models_filter: Optional list of model names to run (None = all)
        agents_filter: Optional list of agent names to run (None = all)
        skip_existing: Whether to skip already completed runs
        max_workers: Number of parallel worker threads per evaluation (default: 1)
    """
    results_file = get_results_file(sop_name)
    
    # Load completed runs for resume capability
    completed = set()
    if skip_existing:
        completed = load_completed_runs(results_file)
        if completed:
            print(f"📋 Found {len(completed)} completed runs in {results_file.name}")
    
    # Write header if new file
    write_csv_header(results_file)
    
    # Filter models if specified
    models_to_run = MODELS
    if models_filter:
        models_to_run = {k: v for k, v in MODELS.items() if k in models_filter}
    
    # Calculate total evaluations
    total_evaluations = sum(
        len(get_compatible_agents(config, agents_filter)) 
        for config in models_to_run.values()
    )
    
    print(f"\n{'='*70}")
    print(f"🚀 BATCH EVALUATION: {sop_name}")
    print(f"{'='*70}")
    print(f"Models: {len(models_to_run)}")
    print(f"Total evaluations: {total_evaluations}")
    print(f"Workers per evaluation: {max_workers}")
    print(f"Output: {results_file}")
    if max_tasks:
        print(f"Max tasks per run: {max_tasks}")
    if max_workers > 1:
        print(f"⚡ Parallel mode: {max_workers} concurrent tasks per model evaluation")
    print(f"{'='*70}\n")
    
    # Run evaluations
    completed_count = 0
    skipped_count = 0
    failed_count = 0
    
    for model_name, model_config in models_to_run.items():
        compatible_agents = get_compatible_agents(model_config, agents_filter)
        
        for agent_type in compatible_agents:
            run_key = f"{model_name}|{agent_type}"
            
            # Skip if already completed
            if run_key in completed:
                print(f"✓ Skipping {model_name} / {agent_type} (already completed)")
                skipped_count += 1
                continue
            
            print(f"\n{'─'*60}")
            print(f"▶ Running: {model_name} / {agent_type}")
            print(f"  Model ID: {model_config['model_id']}")
            print(f"{'─'*60}")
            
            try:
                results = run_single_evaluation(
                    sop_name=sop_name,
                    model_name=model_name,
                    model_config=model_config,
                    agent_type=agent_type,
                    max_tasks=max_tasks,
                    save_traces=save_traces,
                    max_workers=max_workers
                )
                
                # Extract metrics - handle both dict and object return types
                if isinstance(results, dict):
                    results_dict = {
                        "num_tasks": results.get("num_tasks", 0),
                        "num_completed": results.get("num_completed", 0),
                        "num_correct": results.get("num_correct", 0),
                        "task_success_rate": results.get("task_success_rate", 0.0),
                        "execution_completion_rate": results.get("execution_completion_rate", 0.0),
                        "conditional_task_success_rate": results.get("conditional_task_success_rate", 0.0),
                        "tool_accuracy": results.get("tool_accuracy", 0.0),
                        "avg_execution_time": results.get("avg_execution_time", 0.0),
                    }
                else:
                    # EvaluationResults object
                    results_dict = {
                        "num_tasks": results.num_tasks,
                        "num_completed": results.num_completed,
                        "num_correct": results.num_correct,
                        "task_success_rate": results.task_success_rate,
                        "execution_completion_rate": results.execution_completion_rate,
                        "conditional_task_success_rate": results.conditional_task_success_rate,
                        "tool_accuracy": results.tool_accuracy,
                        "avg_execution_time": results.avg_execution_time,
                    }
                
                append_result_to_csv(
                    results_file,
                    model_name,
                    agent_type,
                    model_config,
                    results_dict
                )
                
                tsr = results_dict["task_success_rate"]
                ecr = results_dict["execution_completion_rate"]
                print(f"  ✅ Complete: TSR={tsr:.1%}, ECR={ecr:.1%}")
                completed_count += 1
                
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                append_result_to_csv(
                    results_file,
                    model_name,
                    agent_type,
                    model_config,
                    None,
                    error=str(e)
                )
                failed_count += 1
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"📊 SUMMARY: {sop_name}")
    print(f"{'='*70}")
    print(f"✅ Completed: {completed_count}")
    print(f"⏭️  Skipped (existing): {skipped_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📁 Results saved to: {results_file}")
    print(f"{'='*70}\n")


def list_available_models() -> None:
    """Print all available models grouped by provider."""
    print("\n📋 AVAILABLE MODELS (18 Total)")
    print("="*60)
    
    # Group by provider
    providers: Dict[str, List[str]] = {}
    for model_name, config in MODELS.items():
        provider = config["provider"]
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(model_name)
    
    for provider, models in providers.items():
        print(f"\n{provider}:")
        for model_name in models:
            config = MODELS[model_name]
            fc_status = "✅ FC" if config["supports_function_calling"] else "❌ FC"
            print(f"  • {model_name} [{fc_status}]")
            print(f"    ID: {config['model_id']}")
    
    print(f"\n{'='*60}")
    print(f"FC = Function Calling support")
    print(f"Total: {len(MODELS)} models")


def list_available_sops() -> None:
    """Print all available SOPs."""
    print("\n📋 AVAILABLE SOPS")
    print("="*60)
    
    benchmarks = list_benchmarks()
    for b in benchmarks:
        print(f"  • {b['name']}: {b['num_tasks']} tasks")
    
    print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Batch evaluation for AmazonSOPBench across multiple models and agents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all models on content_flagging SOP
  python batch_evaluate.py --sop content_flagging
  
  # Run with limited tasks for testing
  python batch_evaluate.py --sop content_flagging --max-tasks 5
  
  # Run specific models with parallel workers
  python batch_evaluate.py --sop content_flagging --models "Claude 3.5 Sonnet v2,Llama 3.3 70B" --max-workers 4
  
  # List available models
  python batch_evaluate.py --list-models
  
  # List available SOPs
  python batch_evaluate.py --list-sops
        """
    )
    
    parser.add_argument(
        "--sop", 
        type=str, 
        help="Name of the SOP to evaluate (e.g., content_flagging)"
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=None,
        help="Maximum tasks per evaluation (for testing)"
    )
    parser.add_argument(
        "--models",
        type=str,
        default=None,
        help="Comma-separated list of model names to run (default: all)"
    )
    parser.add_argument(
        "--agents",
        type=str,
        default=None,
        help="Comma-separated list of agent types to run: react, function_calling (default: all compatible)"
    )
    parser.add_argument(
        "--save-traces",
        action="store_true",
        help="Save execution traces for debugging"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Don't skip already completed runs"
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List all available models and exit"
    )
    parser.add_argument(
        "--list-sops",
        action="store_true",
        help="List all available SOPs and exit"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=1,
        help="Number of parallel worker threads per evaluation (default: 1, use >1 for parallelization)"
    )
    
    args = parser.parse_args()
    
    # Handle list commands
    if args.list_models:
        list_available_models()
        return
    
    if args.list_sops:
        list_available_sops()
        return
    
    # Require --sop for evaluation
    if not args.sop:
        parser.error("--sop is required for evaluation. Use --list-sops to see available SOPs.")
    
    # Parse models filter
    models_filter = None
    if args.models:
        models_filter = [m.strip() for m in args.models.split(",")]
        # Validate model names
        invalid_models = [m for m in models_filter if m not in MODELS]
        if invalid_models:
            print(f"Error: Unknown models: {invalid_models}")
            print(f"Use --list-models to see available models.")
            sys.exit(1)
    
    # Parse agents filter
    agents_filter = None
    if args.agents:
        agents_filter = [a.strip() for a in args.agents.split(",")]
        # Validate agent names
        invalid_agents = [a for a in agents_filter if a not in AGENTS]
        if invalid_agents:
            print(f"Error: Unknown agents: {invalid_agents}")
            print(f"Available agents: {', '.join(AGENTS)}")
            sys.exit(1)
    
    # Run evaluation
    run_sop_evaluation(
        sop_name=args.sop,
        max_tasks=args.max_tasks,
        save_traces=args.save_traces,
        models_filter=models_filter,
        agents_filter=agents_filter,
        skip_existing=not args.no_resume,
        max_workers=args.max_workers
    )


if __name__ == "__main__":
    main()

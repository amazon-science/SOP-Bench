# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Benchmark management module.

This module provides functionality for loading and managing SOP benchmarks.
"""

from amazon_sop_bench.benchmarks.registry import BenchmarkRegistry, BenchmarkNotFoundError
from amazon_sop_bench.benchmarks.loader import BenchmarkLoader


def list_benchmarks(domain: str = None):
    """
    List all available benchmarks.
    
    Args:
        domain: Optional domain filter
        
    Returns:
        List of benchmark dictionaries
        
    Example:
        >>> from amazon_sop_bench import list_benchmarks
        >>> benchmarks = list_benchmarks()
        >>> for b in benchmarks:
        ...     print(f"{b['name']}: {b['num_tasks']} tasks")
    """
    registry = BenchmarkRegistry()
    return registry.list_benchmarks(domain=domain)


def load_benchmark(name: str):
    """
    Load a complete benchmark by name.
    
    Args:
        name: Benchmark name (e.g., "content_flagging")
        
    Returns:
        Benchmark object with SOP, tools, and tasks
        
    Example:
        >>> from amazon_sop_bench import load_benchmark
        >>> benchmark = load_benchmark("content_flagging")
        >>> print(benchmark.sop_text[:100])
    """
    loader = BenchmarkLoader()
    return loader.load(name)


__all__ = [
    "BenchmarkRegistry",
    "BenchmarkLoader",
    "BenchmarkNotFoundError",
    "list_benchmarks",
    "load_benchmark",
]

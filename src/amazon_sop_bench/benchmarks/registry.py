# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Benchmark registry for discovering and managing benchmarks."""

from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import json
from amazon_sop_bench.types import BenchmarkMetadata
from amazon_sop_bench.utils.logging import get_logger

logger = get_logger(__name__)


class BenchmarkNotFoundError(Exception):
    """Raised when a benchmark is not found."""
    pass


class BenchmarkRegistry:
    """
    Registry of available SOP benchmarks.
    
    Automatically discovers benchmarks in the data directory and
    provides methods to list, search, and retrieve benchmark metadata.
    
    Example:
        >>> registry = BenchmarkRegistry()
        >>> benchmarks = registry.list_benchmarks()
        >>> print(f"Found {len(benchmarks)} benchmarks")
        >>> 
        >>> metadata = registry.get_benchmark("content_flagging")
        >>> print(f"Tasks: {metadata.num_tasks}")
    """
    
    # Required files for a valid benchmark
    REQUIRED_FILES = ["sop.txt", "tools.py", "toolspecs.json"]
    
    # At least one of these test files must exist
    TEST_FILES = ["test_set.csv", "test_set_with_outputs.csv"]
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize registry and discover benchmarks.
        
        Args:
            data_dir: Optional custom data directory path.
                     If None, uses package's benchmarks/data directory.
        """
        if data_dir is None:
            # Default to package data directory
            package_dir = Path(__file__).parent
            data_dir = package_dir / "data"
        
        self.data_dir = Path(data_dir)
        self._cache: Dict[str, BenchmarkMetadata] = {}
        
        logger.info(f"Initializing BenchmarkRegistry with data_dir: {self.data_dir}")
        
        if not self.data_dir.exists():
            logger.warning(f"Data directory does not exist: {self.data_dir}")
            self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._discover_benchmarks()
    
    def _discover_benchmarks(self) -> None:
        """Scan data directory and discover all benchmarks."""
        logger.info("Discovering benchmarks...")
        
        if not self.data_dir.exists():
            logger.warning("No benchmarks found - data directory is empty")
            return
        
        discovered_count = 0
        
        # Scan all subdirectories
        for benchmark_dir in self.data_dir.iterdir():
            if not benchmark_dir.is_dir():
                continue
            
            # Skip hidden directories
            if benchmark_dir.name.startswith('.'):
                continue
            
            try:
                # Validate benchmark structure
                is_valid, errors = self._validate_benchmark_structure(benchmark_dir)
                
                if not is_valid:
                    logger.warning(
                        f"Skipping invalid benchmark '{benchmark_dir.name}': {', '.join(errors)}"
                    )
                    continue
                
                # Load or create metadata
                metadata = self._load_metadata(benchmark_dir)
                
                # Cache the metadata
                self._cache[metadata.name] = metadata
                discovered_count += 1
                
                logger.debug(f"Discovered benchmark: {metadata.name}")
                
            except Exception as e:
                logger.error(f"Error discovering benchmark '{benchmark_dir.name}': {e}")
                continue
        
        logger.info(f"Discovered {discovered_count} benchmarks")
    
    def _validate_benchmark_structure(self, benchmark_dir: Path) -> Tuple[bool, List[str]]:
        """
        Validate that a benchmark directory has all required files.
        
        Args:
            benchmark_dir: Path to benchmark directory
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required files
        for required_file in self.REQUIRED_FILES:
            file_path = benchmark_dir / required_file
            if not file_path.exists():
                errors.append(f"Missing required file: {required_file}")
        
        # Check for at least one test file
        has_test_file = any(
            (benchmark_dir / test_file).exists() 
            for test_file in self.TEST_FILES
        )
        if not has_test_file:
            errors.append(f"Missing test data file (need one of: {', '.join(self.TEST_FILES)})")
        
        return len(errors) == 0, errors
    
    def _load_metadata(self, benchmark_dir: Path) -> BenchmarkMetadata:
        """
        Load metadata for a benchmark.
        
        If metadata.json exists, load it. Otherwise, create basic metadata
        from directory structure.
        
        Args:
            benchmark_dir: Path to benchmark directory
            
        Returns:
            BenchmarkMetadata object
        """
        metadata_file = benchmark_dir / "metadata.json"
        
        if metadata_file.exists():
            # Load from metadata.json
            with open(metadata_file, 'r') as f:
                data = json.load(f)
            
            return BenchmarkMetadata(
                name=data.get("name", benchmark_dir.name),
                domain=data.get("domain", "unknown"),
                description=data.get("description", ""),
                num_tasks=data.get("num_tasks") or self._count_tasks(benchmark_dir),
                num_tools=data.get("num_tools") or self._count_tools(benchmark_dir),
                complexity_score=data.get("complexity_score", 0.0),
                human_complexity=data.get("human_complexity"),
                sop_path=benchmark_dir / "sop.txt",
                tools_path=benchmark_dir / "tools.py",
                toolspecs_path=benchmark_dir / "toolspecs.json",
                test_data_path=self._find_test_file(benchmark_dir),
                input_columns=data.get("input_columns", []),
                output_columns=data.get("output_columns", []),
            )
        else:
            # Create basic metadata from directory
            logger.debug(f"No metadata.json found for {benchmark_dir.name}, creating basic metadata")
            
            return BenchmarkMetadata(
                name=benchmark_dir.name.replace("_sop", ""),  # Remove _sop suffix if present
                domain="unknown",
                description=f"Benchmark: {benchmark_dir.name}",
                num_tasks=self._count_tasks(benchmark_dir),
                num_tools=self._count_tools(benchmark_dir),
                complexity_score=0.0,
                human_complexity=None,
                sop_path=benchmark_dir / "sop.txt",
                tools_path=benchmark_dir / "tools.py",
                toolspecs_path=benchmark_dir / "toolspecs.json",
                test_data_path=self._find_test_file(benchmark_dir),
                output_columns=[],
            )
    
    def _find_test_file(self, benchmark_dir: Path) -> Optional[Path]:
        """Find the test data file in the benchmark directory."""
        for test_file in self.TEST_FILES:
            file_path = benchmark_dir / test_file
            if file_path.exists():
                return file_path
        return None
    
    def _count_tasks(self, benchmark_dir: Path) -> int:
        """Count number of tasks in test data."""
        try:
            import pandas as pd
            test_file = self._find_test_file(benchmark_dir)
            if test_file:
                df = pd.read_csv(test_file)
                return len(df)
        except Exception as e:
            logger.debug(f"Could not count tasks: {e}")
        return 0
    
    def _count_tools(self, benchmark_dir: Path) -> int:
        """Count number of tools in toolspecs."""
        try:
            toolspecs_file = benchmark_dir / "toolspecs.json"
            if toolspecs_file.exists():
                with open(toolspecs_file, 'r') as f:
                    toolspecs = json.load(f)
                return len(toolspecs) if isinstance(toolspecs, list) else 0
        except Exception as e:
            logger.debug(f"Could not count tools: {e}")
        return 0
    
    def get_benchmark(self, name: str) -> BenchmarkMetadata:
        """
        Get metadata for a specific benchmark.
        
        Args:
            name: Benchmark name (e.g., "content_flagging")
            
        Returns:
            BenchmarkMetadata object
            
        Raises:
            BenchmarkNotFoundError: If benchmark doesn't exist
            
        Example:
            >>> registry = BenchmarkRegistry()
            >>> metadata = registry.get_benchmark("content_flagging")
            >>> print(metadata.num_tasks)
            226
        """
        if name not in self._cache:
            raise BenchmarkNotFoundError(
                f"Benchmark '{name}' not found. "
                f"Available benchmarks: {', '.join(self._cache.keys())}"
            )
        
        return self._cache[name]
    
    def list_benchmarks(
        self, 
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all benchmarks with optional domain filtering.
        
        Args:
            domain: Optional domain filter (e.g., "content_moderation")
            
        Returns:
            List of benchmark dictionaries with key information
            
        Example:
            >>> registry = BenchmarkRegistry()
            >>> benchmarks = registry.list_benchmarks()
            >>> for b in benchmarks:
            ...     print(f"{b['name']}: {b['num_tasks']} tasks")
        """
        benchmarks = []
        
        for metadata in self._cache.values():
            # Apply domain filter if specified
            if domain and metadata.domain != domain:
                continue
            
            benchmarks.append({
                "name": metadata.name,
                "domain": metadata.domain,
                "description": metadata.description,
                "num_tasks": metadata.num_tasks,
                "num_tools": metadata.num_tools,
                "complexity_score": metadata.complexity_score,
                "human_complexity": metadata.human_complexity,
            })
        
        # Sort by name
        benchmarks.sort(key=lambda x: x["name"])
        
        return benchmarks
    
    def get_all_domains(self) -> List[str]:
        """
        Get list of all unique domains.
        
        Returns:
            List of domain names
        """
        domains = set(metadata.domain for metadata in self._cache.values())
        return sorted(list(domains))
    
    def validate_benchmark(self, name: str) -> Tuple[bool, List[str]]:
        """
        Validate benchmark structure and data integrity.
        
        Args:
            name: Benchmark name
            
        Returns:
            Tuple of (is_valid, error_messages)
            
        Example:
            >>> registry = BenchmarkRegistry()
            >>> is_valid, errors = registry.validate_benchmark("content_flagging")
            >>> if not is_valid:
            ...     print(f"Errors: {errors}")
        """
        try:
            metadata = self.get_benchmark(name)
        except BenchmarkNotFoundError:
            return False, [f"Benchmark '{name}' not found"]
        
        errors = []
        
        # Check that all paths exist
        if metadata.sop_path and not metadata.sop_path.exists():
            errors.append(f"SOP file not found: {metadata.sop_path}")
        
        if metadata.tools_path and not metadata.tools_path.exists():
            errors.append(f"Tools file not found: {metadata.tools_path}")
        
        if metadata.toolspecs_path and not metadata.toolspecs_path.exists():
            errors.append(f"Toolspecs file not found: {metadata.toolspecs_path}")
        
        if metadata.test_data_path and not metadata.test_data_path.exists():
            errors.append(f"Test data file not found: {metadata.test_data_path}")
        
        # Validate file contents
        if metadata.sop_path and metadata.sop_path.exists():
            try:
                with open(metadata.sop_path, 'r') as f:
                    sop_text = f.read()
                if len(sop_text.strip()) == 0:
                    errors.append("SOP file is empty")
            except Exception as e:
                errors.append(f"Error reading SOP file: {e}")
        
        if metadata.toolspecs_path and metadata.toolspecs_path.exists():
            try:
                with open(metadata.toolspecs_path, 'r') as f:
                    toolspecs = json.load(f)
                if not isinstance(toolspecs, list):
                    errors.append("Toolspecs must be a JSON array")
            except Exception as e:
                errors.append(f"Error reading toolspecs file: {e}")
        
        return len(errors) == 0, errors
    
    def __len__(self) -> int:
        """Return number of registered benchmarks."""
        return len(self._cache)
    
    def __repr__(self) -> str:
        """String representation of registry."""
        return f"BenchmarkRegistry(benchmarks={len(self._cache)}, data_dir={self.data_dir})"

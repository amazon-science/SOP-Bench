# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Benchmark loader for loading complete benchmark data."""

from pathlib import Path
from typing import List, Dict, Any
import json
import pandas as pd
import importlib.util
import sys

from amazon_sop_bench.types import Benchmark, Task, BenchmarkMetadata
from amazon_sop_bench.benchmarks.registry import BenchmarkRegistry, BenchmarkNotFoundError
from amazon_sop_bench.tools.manager import ToolManager
from amazon_sop_bench.utils.logging import get_logger

logger = get_logger(__name__)


class BenchmarkLoader:
    """
    Loader for benchmark data.
    
    Loads SOP text, tool specifications, test data, and tool implementations
    for a given benchmark.
    
    Example:
        >>> loader = BenchmarkLoader()
        >>> benchmark = loader.load("content_flagging")
        >>> print(benchmark.sop_text[:100])
        >>> print(f"Loaded {len(benchmark.tasks)} tasks")
    """
    
    def __init__(self):
        """Initialize loader with registry."""
        self.registry = BenchmarkRegistry()
    
    def load(self, benchmark_name: str) -> Benchmark:
        """
        Load complete benchmark with all components.
        
        Args:
            benchmark_name: Name of the benchmark to load
            
        Returns:
            Complete Benchmark object with SOP, tools, and tasks
            
        Raises:
            BenchmarkNotFoundError: If benchmark doesn't exist
            ValueError: If benchmark data is invalid
            
        Example:
            >>> loader = BenchmarkLoader()
            >>> benchmark = loader.load("content_flagging")
            >>> print(f"Loaded {benchmark.metadata.name}")
        """
        logger.info(f"Loading benchmark: {benchmark_name}")
        
        # Get metadata from registry
        metadata = self.registry.get_benchmark(benchmark_name)
        
        # Load all components
        try:
            sop_text = self.load_sop(metadata.sop_path)
            toolspecs = self.load_toolspecs(metadata.toolspecs_path)
            tasks = self.load_test_data(metadata.test_data_path, metadata.output_columns, metadata.input_columns)
            tools_instance = self.load_tools(metadata.tools_path)
            
            # Create ToolManager to wrap the tools instance
            tool_manager = ToolManager(tools_instance, toolspecs)
            
            logger.info(
                f"Successfully loaded benchmark '{benchmark_name}': "
                f"{len(tasks)} tasks, {len(tool_manager)} tools"
            )
            
            return Benchmark(
                metadata=metadata,
                sop_text=sop_text,
                tools=tool_manager,
                tasks=tasks,
            )
            
        except Exception as e:
            logger.error(f"Error loading benchmark '{benchmark_name}': {e}")
            raise ValueError(f"Failed to load benchmark '{benchmark_name}': {e}")
    
    def load_sop(self, sop_path: Path) -> str:
        """
        Load SOP text from sop.txt file.
        
        Args:
            sop_path: Path to sop.txt file
            
        Returns:
            SOP text as string
            
        Raises:
            FileNotFoundError: If SOP file doesn't exist
            ValueError: If SOP file is empty
        """
        if not sop_path.exists():
            raise FileNotFoundError(f"SOP file not found: {sop_path}")
        
        try:
            with open(sop_path, 'r', encoding='utf-8') as f:
                sop_text = f.read()
            
            if not sop_text.strip():
                raise ValueError(f"SOP file is empty: {sop_path}")
            
            logger.debug(f"Loaded SOP text ({len(sop_text)} characters)")
            return sop_text
            
        except UnicodeDecodeError:
            # Try with different encoding
            with open(sop_path, 'r', encoding='latin-1') as f:
                sop_text = f.read()
            logger.debug(f"Loaded SOP text with latin-1 encoding")
            return sop_text
    
    def load_toolspecs(self, toolspecs_path: Path) -> List[Dict[str, Any]]:
        """
        Load tool specifications from toolspecs.json file.
        
        Args:
            toolspecs_path: Path to toolspecs.json file
            
        Returns:
            List of tool specification dictionaries
            
        Raises:
            FileNotFoundError: If toolspecs file doesn't exist
            ValueError: If toolspecs format is invalid
        """
        if not toolspecs_path.exists():
            raise FileNotFoundError(f"Toolspecs file not found: {toolspecs_path}")
        
        try:
            with open(toolspecs_path, 'r') as f:
                toolspecs = json.load(f)
            
            if not isinstance(toolspecs, list):
                raise ValueError("Toolspecs must be a JSON array")
            
            logger.debug(f"Loaded {len(toolspecs)} tool specifications")
            return toolspecs
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in toolspecs file: {e}")
    
    def load_test_data(self, test_data_path: Path, output_columns: List[str], input_columns: List[str]) -> List[Task]:
        """
        Load test cases from CSV file, separating inputs from expected outputs.
        
        Args:
            test_data_path: Path to test data CSV file
            output_columns: List of column names that represent expected outputs
            input_columns: List of column names that represent expected inputs
            
        Returns:
            List of Task objects
            
        Raises:
            FileNotFoundError: If test data file doesn't exist
            ValueError: If CSV format is invalid or output columns missing
        """
        if not test_data_path.exists():
            raise FileNotFoundError(f"Test data file not found: {test_data_path}")
        
        try:
            df = pd.read_csv(test_data_path)
            
            if len(df) == 0:
                raise ValueError("Test data file is empty")
            
            # Validate output_columns configuration
            if not output_columns:
                # Warn about missing output_columns
                logger.warning(
                    f"⚠️  Missing 'output_columns' in metadata.json for {test_data_path.parent.name}. "
                    f"Falling back to legacy mode - looking for 'expected_output' or 'final_decision' column. "
                    f"Consider adding 'output_columns' to metadata.json for better validation."
                )
                
                # Validate fallback columns exist
                if "expected_output" not in df.columns and "final_decision" not in df.columns:
                    raise ValueError(
                        f"Legacy mode requires 'expected_output' or 'final_decision' column in CSV. "
                        f"Available columns: {list(df.columns)}. "
                        f"Please add 'output_columns' to metadata.json or ensure CSV has required column."
                    )
            else:
                # Validate output columns exist in dataframe
                missing_cols = [col for col in output_columns if col not in df.columns]
                if missing_cols:
                    raise ValueError(
                        f"Output columns not found in CSV: {missing_cols}. "
                        f"Available columns: {list(df.columns)}. "
                        f"Please update metadata.json 'output_columns' or add missing columns to CSV."
                    )
            
            tasks = []
            for idx, row in df.iterrows():
                # Convert row to dictionary
                row_dict = row.to_dict()
                
                # Separate inputs from outputs
                if output_columns and input_columns:
                    # Extract expected outputs
                    expected_outputs = {}
                    inputs = {}
                    
                    for col, value in row_dict.items():
                        if col in output_columns:
                            expected_outputs[col] = value
                        elif col in input_columns:
                            inputs[col] = value
                    
                    # Store as dict if multiple outputs, single value if one output
                    if len(output_columns) == 1:
                        expected_output = expected_outputs[output_columns[0]]
                    else:
                        expected_output = expected_outputs
                else:
                    # Fallback to old behavior if no output_columns specified
                    inputs = row_dict
                    expected_output = row_dict.get("expected_output", row_dict.get("final_decision"))
                    
                    # Validate fallback produced a valid output
                    if expected_output is None:
                        raise ValueError(
                            f"Row {idx}: Could not determine expected output. "
                            f"CSV must have 'expected_output' or 'final_decision' column, "
                            f"or metadata.json must specify 'output_columns'."
                        )
                
                # Create Task object
                task = Task(
                    task_id=str(idx),
                    inputs=inputs,
                    expected_output=expected_output,
                    metadata={"row_index": idx}
                )
                tasks.append(task)
            
            logger.debug(f"Loaded {len(tasks)} test cases with {len(output_columns) if output_columns else 0} output columns")
            return tasks
            
        except Exception as e:
            raise ValueError(f"Error loading test data: {e}")
    
    def load_tools(self, tools_path: Path) -> Any:
        """
        Dynamically import and instantiate tools from tools.py file.
        
        Args:
            tools_path: Path to tools.py file
            
        Returns:
            Tool manager instance (specific to each benchmark)
            
        Raises:
            FileNotFoundError: If tools file doesn't exist
            ImportError: If tools module cannot be imported
        """
        if not tools_path.exists():
            raise FileNotFoundError(f"Tools file not found: {tools_path}")
        
        try:
            # Create a unique module name
            module_name = f"benchmark_tools_{tools_path.parent.name}"
            
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location(module_name, tools_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load module spec from {tools_path}")
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Find the manager class (typically ends with "Manager")
            manager_class = None
            for attr_name in dir(module):
                if attr_name.endswith("Manager") and not attr_name.startswith("_"):
                    manager_class = getattr(module, attr_name)
                    break
            
            if manager_class is None:
                raise ImportError(f"No Manager class found in {tools_path}")
            
            # Instantiate the manager
            tools_manager = manager_class()
            
            logger.debug(f"Loaded tools from {tools_path.name}")
            return tools_manager
            
        except Exception as e:
            logger.error(f"Error loading tools from {tools_path}: {e}")
            raise ImportError(f"Failed to load tools: {e}")
    
    def get_benchmark_path(self, benchmark_name: str) -> Path:
        """
        Get the directory path for a benchmark.
        
        Args:
            benchmark_name: Name of the benchmark
            
        Returns:
            Path to benchmark directory
        """
        metadata = self.registry.get_benchmark(benchmark_name)
        return metadata.sop_path.parent if metadata.sop_path else None

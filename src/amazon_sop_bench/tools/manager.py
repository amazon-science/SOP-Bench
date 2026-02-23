# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Tool manager for loading and managing benchmark tools."""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
from amazon_sop_bench.tools.base import BaseTool, ToolSpec, ToolCall
from amazon_sop_bench.utils.logging import get_logger

logger = get_logger(__name__)


class ToolManager:
    """
    Manager for loading and organizing tools for a benchmark.
    
    The ToolManager loads tool specifications and provides access to
    tool instances for agent execution.
    
    Example:
        >>> manager = ToolManager(benchmark_path)
        >>> tools = manager.get_tools()
        >>> tool_specs = manager.get_tool_specs()
        >>> result = manager.execute_tool("calculateBPI", {"userid": "123"})
    """
    
    def __init__(self, tools_instance: Any, toolspecs: List[Dict[str, Any]]):
        """
        Initialize tool manager.
        
        Args:
            tools_instance: Instance of the benchmark's tool manager class
                           (e.g., ContentFlaggingManager instance)
            toolspecs: List of tool specification dictionaries
        """
        self.tools_instance = tools_instance
        self.toolspecs = toolspecs
        
        # Handle nested toolSpec structure (Bedrock format)
        self._tool_specs_dict = {}
        for spec in toolspecs:
            if "toolSpec" in spec:
                # Bedrock format: {"toolSpec": {"name": "...", ...}}
                tool_spec = spec["toolSpec"]
                self._tool_specs_dict[tool_spec["name"]] = tool_spec
            elif "name" in spec:
                # Simple format: {"name": "...", ...}
                self._tool_specs_dict[spec["name"]] = spec
            else:
                logger.warning(f"Skipping invalid tool spec: {spec}")
        
        logger.debug(f"Initialized ToolManager with {len(self._tool_specs_dict)} tools")
    
    def get_tool_specs(self) -> List[Dict[str, Any]]:
        """
        Get all tool specifications.
        
        Returns:
            List of tool specification dictionaries
            
        Example:
            >>> specs = manager.get_tool_specs()
            >>> for spec in specs:
            ...     print(f"{spec['name']}: {spec['description']}")
        """
        return self.toolspecs
    
    def get_tool_spec(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get specification for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool specification dictionary or None if not found
        """
        return self._tool_specs_dict.get(tool_name)
    
    def has_tool(self, tool_name: str) -> bool:
        """
        Check if a tool exists.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            True if tool exists, False otherwise
        """
        return tool_name in self._tool_specs_dict
    
    def execute_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any]
    ) -> ToolCall:
        """
        Execute a tool with given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            
        Returns:
            ToolCall object with result and metadata
            
        Raises:
            ValueError: If tool doesn't exist
            Exception: If tool execution fails
            
        Example:
            >>> result = manager.execute_tool(
            ...     "calculateBotProbabilityIndex",
            ...     {"userid": "123", "is_possible_bot": 0.8}
            ... )
            >>> print(result.result)
        """
        if not self.has_tool(tool_name):
            available_tools = ', '.join(self._tool_specs_dict.keys())
            raise ValueError(
                f"Tool '{tool_name}' not found. "
                f"Available tools: {available_tools}"
            )
        
        try:
            # Use the tools instance's process_tool_call method if available
            if hasattr(self.tools_instance, 'process_tool_call'):
                result = self.tools_instance.process_tool_call(tool_name, parameters)
            else:
                # Fallback: try to call method directly
                if hasattr(self.tools_instance, tool_name):
                    method = getattr(self.tools_instance, tool_name)
                    result = method(**parameters)
                else:
                    raise AttributeError(
                        f"Tool '{tool_name}' not found in tools instance"
                    )
            
            return ToolCall(
                tool_name=tool_name,
                parameters=parameters,
                result=result,
                success=True,
                error=None,
            )
            
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            return ToolCall(
                tool_name=tool_name,
                parameters=parameters,
                result=None,
                success=False,
                error=str(e),
            )
    
    def validate_parameters(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate parameters for a tool call.
        
        Args:
            tool_name: Name of the tool
            parameters: Parameters to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        spec = self.get_tool_spec(tool_name)
        if not spec:
            return False, [f"Tool '{tool_name}' not found"]
        
        errors = []
        
        # Check required parameters
        if "parameters" in spec:
            for param_name, param_spec in spec["parameters"].items():
                if param_spec.get("required", False):
                    if param_name not in parameters:
                        errors.append(f"Missing required parameter: {param_name}")
        
        return len(errors) == 0, errors
    
    def get_tool_names(self) -> List[str]:
        """
        Get list of all tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tool_specs_dict.keys())
    
    def __len__(self) -> int:
        """Return number of tools."""
        return len(self.toolspecs)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ToolManager(tools={len(self.toolspecs)})"

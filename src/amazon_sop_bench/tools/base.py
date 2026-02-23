# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Base tool class for SOP execution."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class ToolSpec:
    """
    Tool specification for agents.
    
    Attributes:
        name: Tool name
        description: What the tool does
        parameters: Parameter specifications
        required_params: List of required parameter names
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    required_params: List[str]


@dataclass
class ToolCall:
    """
    Record of a tool call during execution.
    
    Attributes:
        tool_name: Name of the tool called
        parameters: Parameters passed to the tool
        result: Result returned by the tool
        success: Whether the call succeeded
        error: Error message if call failed
        timestamp: When the call was made
    """
    tool_name: str
    parameters: Dict[str, Any]
    result: Any = None
    success: bool = True
    error: Optional[str] = None
    timestamp: Optional[str] = None


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    
    Tools are functions that agents can call to retrieve information or
    perform actions. In SOP-Bench, tools use pre-computed mock data to
    ensure reproducibility.
    
    Example:
        >>> class MyTool(BaseTool):
        ...     def __init__(self, dataset_path):
        ...         super().__init__("my_tool", "Does something useful")
        ...         self.dataset_path = dataset_path
        ...     
        ...     def execute(self, param1, param2):
        ...         # Load data and return result
        ...         return result
        ...
        >>> tool = MyTool("data.csv")
        >>> result = tool.execute(param1="value1", param2="value2")
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize the tool.
        
        Args:
            name: Tool name (should match toolspec)
            description: Brief description of what the tool does
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, **params) -> Any:
        """
        Execute the tool with given parameters.
        
        This method must be implemented by all tool subclasses. It should:
        1. Validate input parameters
        2. Look up or compute the result (typically from mock data)
        3. Return the result in the expected format
        
        Args:
            **params: Tool-specific parameters
            
        Returns:
            Tool result (format depends on tool)
            
        Raises:
            ValueError: If parameters are invalid
            KeyError: If required data is missing
            
        Example:
            >>> result = tool.execute(user_id="123", content_id="456")
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    def get_spec(self) -> ToolSpec:
        """
        Get the tool specification for agents.
        
        Returns:
            ToolSpec with name, description, and parameters
        """
        # Default implementation - subclasses can override
        return ToolSpec(
            name=self.name,
            description=self.description,
            parameters={},
            required_params=[]
        )
    
    def validate_params(self, params: Dict[str, Any], required: List[str]) -> None:
        """
        Validate that required parameters are present.
        
        Args:
            params: Parameters provided
            required: List of required parameter names
            
        Raises:
            ValueError: If required parameters are missing
        """
        missing = [p for p in required if p not in params]
        if missing:
            raise ValueError(
                f"Missing required parameters for {self.name}: {missing}"
            )
    
    def __repr__(self) -> str:
        """String representation of the tool."""
        return f"{self.__class__.__name__}(name={self.name})"

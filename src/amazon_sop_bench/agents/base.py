# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Base agent class for SOP execution."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class AgentResult:
    """
    Result of agent execution on a task.
    
    Attributes:
        output: Final output produced by the agent
        tool_calls: List of tool calls made during execution
        reasoning_trace: Agent's reasoning steps (if available)
        execution_time: Time taken to execute the task (seconds)
        success: Whether the agent completed the task
        error: Error message if execution failed
    """
    output: Any
    tool_calls: List[Dict[str, Any]]
    reasoning_trace: Optional[str] = None
    execution_time: float = 0.0
    success: bool = True
    error: Optional[str] = None


class BaseAgent(ABC):
    """
    Abstract base class for all SOP-executing agents.
    
    All agent implementations must inherit from this class and implement
    the execute() method. This ensures a consistent interface for evaluation.
    
    Example:
        >>> class MyAgent(BaseAgent):
        ...     def execute(self, sop, task, tools):
        ...         # Your agent logic
        ...         return AgentResult(output=result, tool_calls=[])
        ...
        >>> agent = MyAgent()
        >>> result = agent.execute(sop_text, task_input, available_tools)
    """
    
    def __init__(self, model_id: Optional[str] = None, **kwargs):
        """
        Initialize the agent.
        
        Args:
            model_id: Optional model identifier (e.g., "claude-3.5-sonnet")
            **kwargs: Additional agent-specific configuration
        """
        self.model_id = model_id
        self.config = kwargs
    
    @abstractmethod
    def execute(
        self,
        sop: str,
        task: Dict[str, Any],
        tools: List[Dict[str, Any]]
    ) -> AgentResult:
        """
        Execute a task given SOP instructions and available tools.
        
        This is the main method that agents must implement. The agent should:
        1. Read and understand the SOP instructions
        2. Analyze the task inputs
        3. Plan which tools to call and in what order
        4. Execute tools via the tool manager
        5. Synthesize the final output
        6. Return results with execution trace
        
        Args:
            sop: Natural language SOP text describing the procedure
            task: Dictionary containing task inputs (e.g., {"user_id": "123"})
            tools: List of available tool specifications with:
                - name: Tool name
                - description: What the tool does
                - parameters: Required and optional parameters
                
        Returns:
            AgentResult containing:
                - output: Final result (format depends on SOP)
                - tool_calls: List of tools called with parameters
                - reasoning_trace: Agent's reasoning steps
                - execution_time: Time taken
                - success: Whether task completed
                - error: Error message if failed
                
        Raises:
            NotImplementedError: If not implemented by subclass
            
        Example:
            >>> result = agent.execute(
            ...     sop="Follow these steps...",
            ...     task={"user_id": "123", "content_id": "456"},
            ...     tools=[{"name": "getTrustScore", ...}]
            ... )
            >>> print(result.output)
            >>> print(f"Made {len(result.tool_calls)} tool calls")
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(model_id={self.model_id})"

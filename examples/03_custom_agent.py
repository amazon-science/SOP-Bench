#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""
Custom Agent Example

This example demonstrates how to implement a custom agent for SOP-Bench.

Usage:
    python 03_custom_agent.py
"""

from amazon_sop_bench.agents import BaseAgent
from amazon_sop_bench import evaluate
import random

class SimpleRandomAgent(BaseAgent):
    """
    A simple agent that makes random decisions.
    
    This is a minimal example showing the required interface.
    Real agents would use LLMs and sophisticated reasoning.
    """
    
    def __init__(self, **kwargs):
        """Initialize the agent."""
        super().__init__(**kwargs)
        self.name = "SimpleRandomAgent"
    
    def execute(self, sop: str, task: dict, tools: list) -> dict:
        """
        Execute a task given SOP instructions.
        
        Args:
            sop: Natural language SOP text
            task: Task inputs (dict)
            tools: Available tools (list)
            
        Returns:
            dict with keys:
                - output: Final decision/output
                - tool_calls: List of tool calls made
                - reasoning: Agent's reasoning trace
        """
        # In a real agent, you would:
        # 1. Parse the SOP
        # 2. Analyze the task
        # 3. Plan tool calls
        # 4. Execute tools
        # 5. Synthesize output
        
        # For this example, we'll just make a random decision
        decisions = ["approved", "rejected", "escalate", "pending"]
        random_decision = random.choice(decisions)
        
        # Format output using XML (recommended for best compatibility)
        output = f"<final_decision>{random_decision}</final_decision>"
        
        # Track tool calls (empty for this simple example)
        tool_calls = []
        
        # Reasoning trace
        reasoning = f"Randomly selected decision: {random_decision}"
        
        return {
            "output": output,
            "tool_calls": tool_calls,
            "reasoning": reasoning
        }


class SmartAgent(BaseAgent):
    """
    A smarter agent that actually uses tools.
    
    This example shows how to call tools and make decisions based on results.
    """
    
    def __init__(self, **kwargs):
        """Initialize the agent."""
        super().__init__(**kwargs)
        self.name = "SmartAgent"
    
    def execute(self, sop: str, task: dict, tools: list) -> dict:
        """Execute a task with tool usage."""
        
        tool_calls = []
        reasoning = []
        
        # Step 1: Analyze SOP
        reasoning.append(f"SOP Analysis: {len(sop)} characters")
        reasoning.append(f"Task inputs: {list(task.keys())}")
        reasoning.append(f"Available tools: {len(tools)}")
        
        # Step 2: Call tools (example - would be more sophisticated in real agent)
        if tools:
            # Example: Call first tool with task inputs
            first_tool = tools[0]
            tool_name = first_tool.get('name', 'unknown')
            
            reasoning.append(f"Calling tool: {tool_name}")
            
            # In a real agent, you would actually call the tool here
            # For this example, we'll just record the intent
            tool_calls.append({
                "tool": tool_name,
                "parameters": task,
                "result": "mock_result"
            })
        
        # Step 3: Make decision based on tool results
        # In a real agent, this would be based on actual tool outputs
        decision = "approved" if len(tool_calls) > 0 else "rejected"
        
        reasoning.append(f"Final decision: {decision}")
        
        # Format output
        output = f"<final_decision>{decision}</final_decision>"
        
        return {
            "output": output,
            "tool_calls": tool_calls,
            "reasoning": "\n".join(reasoning)
        }


def main():
    """Demonstrate custom agent usage."""
    
    print("=" * 60)
    print("SOP-Bench: Custom Agent Example")
    print("=" * 60)
    print()
    
    # Example 1: Simple Random Agent
    print("Example 1: Simple Random Agent")
    print("-" * 60)
    print("This agent makes random decisions without using tools.")
    print()
    
    random_agent = SimpleRandomAgent()
    
    results = evaluate(
        benchmark_name="content_flagging",
        agent=random_agent,
        max_tasks=5  # Test with 5 tasks
    )
    
    print(f"Results:")
    print(f"  Task Success Rate: {results['task_success_rate']:.1%}")
    print(f"  (Expected to be low since decisions are random)")
    print()
    
    # Example 2: Smart Agent
    print("Example 2: Smart Agent")
    print("-" * 60)
    print("This agent uses tools to make decisions.")
    print()
    
    smart_agent = SmartAgent()
    
    results = evaluate(
        benchmark_name="content_flagging",
        agent=smart_agent,
        max_tasks=5
    )
    
    print(f"Results:")
    print(f"  Task Success Rate: {results['task_success_rate']:.1%}")
    print(f"  Tool Accuracy: {results['tool_accuracy']:.1%}")
    print()
    
    # Tips
    print("=" * 60)
    print("Tips for Building Custom Agents")
    print("=" * 60)
    print("1. Inherit from BaseAgent")
    print("2. Implement execute(sop, task, tools) method")
    print("3. Return dict with 'output', 'tool_calls', 'reasoning'")
    print("4. Use XML format for output: <final_decision>value</final_decision>")
    print("5. Test with max_tasks=1 first")
    print("6. Use save_traces=True to debug")
    print()
    
    print("See ARCHITECTURE.md for more details on agent implementation.")
    print()

if __name__ == "__main__":
    main()

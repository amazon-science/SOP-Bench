# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Function-Calling Agent implementation for SOP execution."""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from amazon_sop_bench.agents.base import BaseAgent, AgentResult
from amazon_sop_bench.config import get_config
from amazon_sop_bench.utils.logging import get_logger

logger = get_logger(__name__)

# Optional boto3 import - only needed if using this agent
try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not available - Function-Calling agent will not work")


class FunctionCallingAgent(BaseAgent):
    """
    Function-Calling agent for SOP execution.
    
    This agent uses the native function-calling capabilities of LLMs
    to execute tools while following SOPs.
    
    Example:
        >>> agent = FunctionCallingAgent(model_id="claude-3.5-sonnet")
        >>> result = agent.execute(sop_text, task_input, tools)
        >>> print(result.output)
    """
    
    def __init__(self, model_id: Optional[str] = None, **kwargs):
        """
        Initialize Function-Calling agent.
        
        Args:
            model_id: Bedrock model ID (defaults to config)
            **kwargs: Additional configuration
        """
        super().__init__(model_id, **kwargs)
        
        if not BOTO3_AVAILABLE:
            raise ImportError(
                "boto3 is required for Function-Calling agent. "
                "Install with: pip install boto3"
            )
        
        self.config_obj = get_config()
        self.model_id = model_id or self.config_obj.aws_model_id
        self.bedrock_client = None
        
        logger.info(f"Initialized Function-Calling agent with model: {self.model_id}")
    
    def _setup_bedrock_client(self) -> None:
        """Set up the Bedrock client."""
        if self.bedrock_client is not None:
            return  # Already set up
        
        logger.info("Setting up Bedrock client")
        
        try:
            if self.config_obj.aws_role_arn:
                # Use role assumption
                session = boto3.Session()
                sts = session.client("sts", region_name=self.config_obj.aws_region)
                assumed = sts.assume_role(
                    RoleArn=self.config_obj.aws_role_arn,
                    RoleSessionName="SOPBenchSession"
                )
                creds = assumed["Credentials"]
                
                session = boto3.Session(
                    aws_access_key_id=creds["AccessKeyId"],
                    aws_secret_access_key=creds["SecretAccessKey"],
                    aws_session_token=creds["SessionToken"],
                    region_name=self.config_obj.aws_region
                )
                self.bedrock_client = session.client("bedrock-runtime")
            else:
                # Use default profile with ADA credential_process
                session = boto3.Session(profile_name='default')
                self.bedrock_client = session.client(
                    "bedrock-runtime",
                    region_name=self.config_obj.aws_region
                )
            
            logger.info("Successfully set up Bedrock client")
            
        except Exception as e:
            logger.error(f"Error setting up Bedrock client: {e}")
            raise
    
    def _create_tool_definitions(self, tool_manager) -> List[Dict[str, Any]]:
        """
        Create tool definitions for Bedrock function calling.
        
        Args:
            tool_manager: ToolManager instance
            
        Returns:
            List of tool definitions in Bedrock format
        """
        logger.info("Creating tool definitions for Bedrock")
        
        # Get the raw toolspecs - they have nested toolSpec structure
        tool_specs = tool_manager.get_tool_specs()
        
        # Convert to proper Bedrock format
        bedrock_tools = []
        for spec in tool_specs:
            if 'toolSpec' in spec:
                tool_spec = spec['toolSpec']
                
                # Convert to Bedrock format
                bedrock_tool = {
                    "name": tool_spec["name"],
                    "description": tool_spec["description"],
                    "input_schema": tool_spec["inputSchema"]["json"]
                }
                bedrock_tools.append(bedrock_tool)
            else:
                # If no nested toolSpec, convert directly
                bedrock_tool = {
                    "name": spec["name"],
                    "description": spec["description"],
                    "input_schema": spec.get("inputSchema", {}).get("json", {})
                }
                bedrock_tools.append(bedrock_tool)
        
        logger.info(f"Using {len(bedrock_tools)} tool definitions in Bedrock format")
        logger.debug(f"Tool names: {[tool.get('name', 'unknown') for tool in bedrock_tools]}")
        
        return bedrock_tools
    
    def _invoke_bedrock_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tool_definitions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock with tool definitions.
        
        Args:
            messages: Conversation messages
            tool_definitions: Tool definitions
            
        Returns:
            Bedrock response
        """
        logger.debug("Invoking Bedrock with tools")
        
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": messages,
            "max_tokens": self.config_obj.max_tokens,
            "temperature": self.config_obj.temperature,
            "tools": tool_definitions
        }
        
        response = self.bedrock_client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(payload)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body
    
    def execute(
        self,
        sop: str,
        task: Dict[str, Any],
        tools: Any  # ToolManager instance
    ) -> AgentResult:
        """
        Execute a task using function calling.
        
        Args:
            sop: SOP text
            task: Task inputs
            tools: ToolManager instance
            
        Returns:
            AgentResult with output and execution trace
        """
        start_time = time.time()
        logger.info("Executing Function-Calling agent on task")
        
        try:
            # Set up Bedrock client
            self._setup_bedrock_client()
            
            # Create tool definitions
            tool_definitions = self._create_tool_definitions(tools)
            
            # Format task input
            task_input = "\n".join([f"{k}: {v}" for k, v in task.items()])
            
            # Create initial message
            messages = [{
                "role": "user",
                "content": f"""Please follow this Standard Operating Procedure to process the given task:

<sop>
{sop}
</sop>

Task to process:
{task_input}

Follow the SOP step by step. Use the available tools to gather information and make decisions.

IMPORTANT: Once you have completed all steps, provide your final decision in the following XML format:

<final_decision>your_decision_value</final_decision>

Where your_decision_value should be the final decision as specified in the SOP. 
Provide ONLY the decision value inside the tags, without any additional explanation or formatting."""
        }]
            
            tool_calls = []
            max_iterations = 10
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                logger.info(f"Function-calling iteration {iteration}")
                
                # Invoke Bedrock
                response = self._invoke_bedrock_with_tools(messages, tool_definitions)
                
                # Add assistant message
                assistant_message = {
                    "role": "assistant",
                    "content": response.get("content", [])
                }
                messages.append(assistant_message)
                
                # Check if there are tool uses
                content = response.get("content", [])
                has_tool_use = any(
                    block.get("type") == "tool_use" 
                    for block in content if isinstance(block, dict)
                )
                
                if not has_tool_use:
                    # No more tool calls, we're done
                    logger.info("No more tool calls, execution complete")
                    break
                
                # Process tool calls
                tool_results = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_name = block.get("name")
                        tool_input = block.get("input", {})
                        tool_use_id = block.get("id")
                        
                        logger.info(f"Executing tool: {tool_name}")
                        
                        # Execute tool
                        result = tools.execute_tool(tool_name, tool_input)
                        
                        # Record tool call
                        tool_calls.append({
                            "tool": tool_name,
                            "input": tool_input,
                            "output": result.result,
                            "success": result.success,
                            "error": result.error
                        })
                        
                        # Create tool result message
                        tool_result = {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": json.dumps(result.result) if result.success else f"Error: {result.error}"
                        }
                        tool_results.append(tool_result)
                
                # Add tool results to conversation
                if tool_results:
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })
            
            # Extract final output
            final_content = messages[-1].get("content", [])
            if isinstance(final_content, list):
                # Find text content
                output = ""
                for block in final_content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        output += block.get("text", "")
                    elif isinstance(block, str):
                        output += block
            else:
                output = str(final_content)
            
            execution_time = time.time() - start_time
            
            logger.info(f"Function-Calling agent completed in {execution_time:.2f} seconds")
            
            return AgentResult(
                output=output,
                tool_calls=tool_calls,
                reasoning_trace=json.dumps(messages, indent=2),
                execution_time=execution_time,
                success=True,
                error=None
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Function-Calling agent failed: {e}")
            
            # Capture error information in trace for debugging
            error_trace = f"""ERROR OCCURRED DURING EXECUTION

Error Type: {type(e).__name__}
Error Message: {str(e)}

Execution Time: {execution_time:.2f}s

This error was logged to stderr and captured here for trace analysis."""
            
            return AgentResult(
                output=None,
                tool_calls=[],
                reasoning_trace=error_trace,
                execution_time=execution_time,
                success=False,
                error=str(e)
            )

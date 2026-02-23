# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""ReAct Agent (LangChain-based) with stop-sequence-safe wrapper for SOP execution.

This is the primary ReAct agent used for all SOP-Bench experiments. It uses
LangChain's ``create_react_agent`` / ``AgentExecutor`` with automatic
stop-sequence handling for all Bedrock model families.

Why a wrapper is needed
-----------------------
LangChain's ``create_react_agent`` injects ``stop=["\\nObservation:"]`` into
every LLM call to pause the model after ``Action``/``Action Input`` so the
tool can execute.  ``langchain-aws``'s ``ChatBedrock`` (InvokeModel API)
validates stop sequences against a hardcoded provider map
(``provider_stop_sequence_key_name_map`` in ``langchain_aws/llms/bedrock.py``)
that only includes ``anthropic``, ``amazon``, ``ai21``, ``cohere``, and
``mistral``.  Non-listed providers (``meta``, ``openai``) raise::

    ValueError: Stop sequence key name for {provider} is not supported.

This is a known ``langchain-aws`` limitation.  See:
- https://github.com/langchain-ai/langchain-aws (langchain-aws source)
- https://forum.langchain.com/t/langchain-v1-agentic-flow-on-bedrock-fails-for-non-claude-models-available-in-bedrock-llama4-nova-gpt-oss/2251

The ``ChatBedrockConverse`` class (Converse API) handles stop sequences
uniformly for all providers, but switching API paths mid-experiment would
introduce confounding variables in benchmark comparisons.  All SOP-Bench
results use InvokeModel for consistency.

Three-tier stop-sequence handling
---------------------------------
**Tier 1 — Claude (no wrapper):**
  ``ChatBedrock`` handles stop sequences natively.

**Tier 2 — OpenAI GPT-OSS (wrapper, stop passthrough):**
  OpenAI's InvokeModel API accepts the ``stop`` parameter, but
  ``ChatBedrock`` rejects it before the API call.  The wrapper bypasses
  validation and passes ``stop`` through.  GPT-OSS format quirks
  (``<reasoning>`` tags, bare ``<final_decision>``) are handled entirely
  by ``OpenAIReActOutputParser`` at the parse level — no LLM-output-level
  post-processing is needed.

**Tier 3 — Meta Llama / DeepSeek (wrapper, client-side truncation):**
  These models' InvokeModel APIs reject stop sequences entirely
  (``ValidationException: extraneous key [stop] is not permitted``).
  The wrapper drops ``stop``, then:

  1. Truncates generated text at the first ``\\nObservation:`` marker
     (simulates server-side stop behavior)
  2. Sanitizes Thought blocks — replaces premature ``Final Answer:``
     mentions inside Thought sections (before ``Action:``) with lowercase
     ``final answer`` to prevent LangChain's parser ambiguity error

Trade-offs
----------
- **Latency/cost**: Tier 3 models generate past ``Observation:`` before
  truncation.  Extra tokens are discarded but still billed.
- **Consistency**: All models use InvokeModel (not Converse API) to avoid
  API-path confounding variables in benchmark comparisons.
- **Why BaseChatModel wrapper**: ``ChatBedrock`` validates stop sequences
  in its invocation parameter preparation, before ``_generate`` is called.
  Subclassing cannot intercept this.  Wrapping via ``BaseChatModel`` and
  delegating to a ``ChatBedrock`` instance intercepts ``stop`` before
  ``ChatBedrock`` ever sees it.
"""

import json
import time
from typing import ClassVar, Dict, List, Any, Optional
from datetime import datetime

from amazon_sop_bench.agents.base import BaseAgent, AgentResult
from amazon_sop_bench.agents.openai_react_parser import OpenAIReActOutputParser
from amazon_sop_bench.config import get_config
from amazon_sop_bench.utils.logging import get_logger

logger = get_logger(__name__)

# Optional LangChain imports - only needed if using this agent
try:
    from langchain.agents import Tool, create_react_agent, AgentExecutor
    from langchain.prompts import PromptTemplate
    from langchain_aws.chat_models import ChatBedrock
    from langchain_core.language_models import BaseChatModel
    import boto3
    LANGCHAIN_AVAILABLE = True
except ImportError:
    Tool = Any
    PromptTemplate = Any
    BaseChatModel = Any
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain not available - ReAct Legacy agent will not work")


class StopSequenceSafeChatBedrock(BaseChatModel):
    """LangChain-compatible ChatBedrock wrapper with client-side stop handling.

    Wraps ``ChatBedrock`` via ``BaseChatModel`` (not subclass) to avoid
    ChatBedrock's internal stop-sequence validation which rejects stop
    sequences for Meta/Llama models before the API call.

    Post-processing performs two operations:

    1. **Client-side truncation** — cuts the generated text at the first
       ``\\nObservation:`` marker to simulate server-side stop-sequence
       behavior.  Without this, the model hallucinates tool outputs and
       LangChain never actually invokes the tools.

    2. **Thought sanitization** (Llama fix) — if the truncated output
       contains both ``Action:`` and ``Final Answer:`` (the latter inside
       a Thought block as future intent), the ``Final Answer:`` mention
       is replaced so LangChain's parser doesn't see ambiguity.
    """

    model_id: str
    region_name: str = "us-west-2"
    model_kwargs: dict = {}
    bedrock_llm: Any = None

    # Sequences to truncate at client-side.  Includes the ReAct stop
    # sequences that LangChain would normally inject server-side.
    REACT_STOP_SEQUENCES: ClassVar[List[str]] = [
        "\nObservation:",
        "\nObservation :",   # occasional whitespace variant
        "\nObservation:\n",
        "\nobservation:",    # lowercase variant (rare)
    ]

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, model_id: str, **kwargs):
        super().__init__(
            model_id=model_id,
            region_name=kwargs.get('region_name', 'us-west-2'),
            model_kwargs=kwargs.get('model_kwargs', {}),
        )
        self.bedrock_llm = ChatBedrock(model_id=model_id, **kwargs)

    def _needs_client_side_truncation(self) -> bool:
        """Check if this model needs client-side truncation (vs native stop)."""
        model_lower = self.model_id.lower()
        return any(token in model_lower for token in ("meta", "llama", "deepseek"))


    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        """Generate with model-appropriate stop-sequence handling.

        - **OpenAI GPT-OSS**: pass stop through natively (format quirks
          handled by ``OpenAIReActOutputParser`` at the parse level).
        - **Llama/DeepSeek**: drop stop, truncate client-side, sanitize
          Thought blocks.

        Args:
            messages: Chat messages to send to the model.
            stop: Stop sequences injected by LangChain.
            run_manager: LangChain callback manager.
            **kwargs: Additional keyword arguments forwarded to ChatBedrock.

        Returns:
            ChatResult with generations post-processed as needed.
        """
        if not self._needs_client_side_truncation():
            # OpenAI models: pass stop through natively.
            # Format quirks (<reasoning>, <final_decision>) are handled
            # by OpenAIReActOutputParser at the parse level.
            return self.bedrock_llm._generate(
                messages, stop=stop, run_manager=run_manager, **kwargs
            )

        # Llama/DeepSeek: call with stop=None, then truncate client-side
        result = self.bedrock_llm._generate(
            messages, stop=None, run_manager=run_manager, **kwargs
        )

        # Build the full set of sequences to truncate at
        stop_seqs = list(self.REACT_STOP_SEQUENCES)
        if stop:
            stop_seqs.extend(s for s in stop if s not in stop_seqs)

        if result.generations:
            for gen in result.generations:
                text = gen.text

                # --- Step 1: Client-side truncation ---
                # Simulate stop-sequence behavior by cutting at the earliest
                # stop marker.  This ensures LangChain's output parser sees
                # only the Action/Action Input block and not a hallucinated
                # Observation.
                earliest_pos = len(text)
                matched_seq = None
                for seq in stop_seqs:
                    pos = text.find(seq)
                    if pos != -1 and pos < earliest_pos:
                        earliest_pos = pos
                        matched_seq = seq
                if matched_seq is not None:
                    logger.debug(
                        "Client-side truncation: found %r at position %d, "
                        "discarding %d trailing characters",
                        matched_seq, earliest_pos,
                        len(text) - earliest_pos,
                    )
                    text = text[:earliest_pos]

                # --- Step 2: Thought sanitization (Llama ambiguity fix) ---
                # Llama models mention "Final Answer:" inside the Thought
                # block as future intent.  When Action: is also present,
                # LangChain's ReActOutputParser raises OutputParserException
                # ("both a final answer and a parse-able action").
                #
                # Fix: replace "Final Answer:" in the Thought section
                # (before the Action: line) with lowercase "final answer"
                # which the parser ignores.  Genuine Final Answer: lines
                # (no Action: present) are left untouched.
                if "\nAction:" in text or text.startswith("Action:"):
                    action_idx = text.find("\nAction:")
                    if action_idx == -1:
                        action_idx = 0  # starts with Action:
                    thought_section = text[:action_idx]
                    if "Final Answer:" in thought_section:
                        logger.debug(
                            "Thought sanitization: removing premature "
                            "'Final Answer:' from Thought block (Llama fix)"
                        )
                        sanitized_thought = thought_section.replace(
                            "Final Answer:", "final answer"
                        )
                        text = sanitized_thought + text[action_idx:]

                # Update both gen.text and gen.message.content.
                # ChatGeneration.text is a computed property that reads from
                # message.content, so we must update the message directly.
                if hasattr(gen, 'message') and gen.message is not None:
                    gen.message.content = text
                try:
                    gen.text = text
                except (AttributeError, TypeError):
                    pass  # text is a read-only property on ChatGeneration

        return result

    @property
    def _llm_type(self) -> str:
        return f"stop_safe_{self.bedrock_llm._llm_type}"

    def __getattr__(self, name):
        bedrock = self.__dict__.get('bedrock_llm')
        if bedrock is not None:
            return getattr(bedrock, name)
        raise AttributeError(
            f"'{self.__class__.__name__}' has no attribute '{name}'"
        )


class ReActAgent(BaseAgent):
    """ReAct (Reasoning + Acting) agent for SOP execution using LangChain.

    This is the primary ReAct agent used for all SOP-Bench experiments. It uses
    LangChain's ``create_react_agent`` / ``AgentExecutor`` with automatic
    stop-sequence stripping, client-side truncation, and Thought sanitization
    for model families that don't support stop sequences via InvokeModel
    (Meta/Llama, OpenAI, DeepSeek).

    Example::

        >>> agent = ReActAgent(
        ...     model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        ... )
        >>> result = agent.execute(sop_text, task_input, tools)
        >>> print(result.output)
    """

    # Models that need the stop-sequence-safe wrapper.
    # Two sub-categories:
    #   NEEDS_TRUNCATION: InvokeModel rejects stop param → use stop=None + client-side truncation
    #   NEEDS_PASSTHROUGH: InvokeModel supports stop param → pass stop=stop through (no truncation)
    NEEDS_TRUNCATION: ClassVar[tuple] = ("meta", "llama", "deepseek")
    NEEDS_PASSTHROUGH: ClassVar[tuple] = ("openai", "gpt")
    STOP_SEQ_UNSUPPORTED: ClassVar[tuple] = NEEDS_TRUNCATION + NEEDS_PASSTHROUGH

    def __init__(self, model_id: Optional[str] = None, **kwargs):
        super().__init__(model_id, **kwargs)
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is required for ReAct agent. "
                "Install with: pip install langchain langchain-aws"
            )
        self.config_obj = get_config()
        self.model_id = model_id or self.config_obj.aws_model_id
        self.llm = None
        self.agent = None
        logger.info(f"Initialized ReAct agent with model: {self.model_id}")

    def _needs_stop_seq_wrapper(self) -> bool:
        """Check if the model needs the stop-sequence-safe wrapper."""
        model_lower = self.model_id.lower()
        return any(token in model_lower for token in self.STOP_SEQ_UNSUPPORTED)

    def _get_model_kwargs(self) -> Dict[str, Any]:
        """Get model-specific kwargs based on model family."""
        model_lower = self.model_id.lower()
        if "meta" in model_lower or "llama" in model_lower:
            return {
                "temperature": self.config_obj.temperature,
                "max_gen_len": self.config_obj.max_tokens,
                "top_p": 0.9,
            }
        else:
            return {
                "temperature": self.config_obj.temperature,
                "max_tokens": self.config_obj.max_tokens,
            }

    def _setup_llm(self) -> None:
        """Set up the LLM client, wrapping with stop-sequence-safe layer if needed."""
        if self.llm is not None:
            return

        logger.info("Setting up Bedrock LLM client")
        try:
            model_kwargs = self._get_model_kwargs()
            use_wrapper = self._needs_stop_seq_wrapper()

            if self.config_obj.aws_role_arn:
                session = boto3.Session()
                sts = session.client("sts", region_name=self.config_obj.aws_region)
                assumed = sts.assume_role(
                    RoleArn=self.config_obj.aws_role_arn,
                    RoleSessionName="SOPBenchSession"
                )
                creds = assumed["Credentials"]
                bedrock_config = {
                    "model_id": self.model_id,
                    "region_name": self.config_obj.aws_region,
                    "aws_access_key_id": creds["AccessKeyId"],
                    "aws_secret_access_key": creds["SecretAccessKey"],
                    "aws_session_token": creds["SessionToken"],
                    "model_kwargs": model_kwargs,
                }
            else:
                bedrock_config = {
                    "model_id": self.model_id,
                    "region_name": self.config_obj.aws_region,
                    "model_kwargs": model_kwargs,
                }

            if use_wrapper:
                logger.info(
                    f"Using stop-sequence-safe wrapper for {self.model_id} "
                    f"(client-side truncation + thought sanitization enabled)"
                )
                self.llm = StopSequenceSafeChatBedrock(**bedrock_config)
            else:
                self.llm = ChatBedrock(**bedrock_config)

            logger.info("Successfully set up Bedrock LLM")
        except Exception as e:
            logger.error(f"Error setting up LLM: {e}")
            raise

    def _create_langchain_tools(self, tool_manager) -> List[Tool]:
        """Create LangChain tools from ToolManager."""
        logger.info("Creating LangChain tools from ToolManager")
        langchain_tools = []

        for tool_spec in tool_manager.get_tool_specs():
            if "toolSpec" in tool_spec:
                spec = tool_spec["toolSpec"]
            else:
                spec = tool_spec

            tool_name = spec["name"]
            description = spec.get("description", f"Tool: {tool_name}")

            def make_tool_func(name):
                def tool_func(input_str: str) -> str:
                    try:
                        params = json.loads(input_str) if isinstance(input_str, str) else input_str
                        result = tool_manager.execute_tool(name, params)
                        if result.success:
                            return json.dumps(result.result)
                        else:
                            return f"Error: {result.error}"
                    except Exception as e:
                        logger.error(f"Error in tool {name}: {e}")
                        return f"Error: {e}"
                return tool_func

            langchain_tools.append(
                Tool(
                    name=tool_name,
                    func=make_tool_func(tool_name),
                    description=description
                )
            )
            logger.debug(f"Created LangChain tool: {tool_name}")

        logger.info(f"Created {len(langchain_tools)} LangChain tools")
        return langchain_tools

    def _is_openai_model(self) -> bool:
        """Check if the current model is an OpenAI GPT-OSS variant."""
        model_lower = self.model_id.lower()
        return any(tok in model_lower for tok in self.NEEDS_PASSTHROUGH)

    def _create_react_prompt(self) -> PromptTemplate:
        """Create the ReAct prompt template."""
        template = """You are a helpful assistant that follows Standard Operating Procedures (SOPs) to solve problems.

You will be given an SOP and a task to complete. Follow the SOP step by step using the available tools.

<sop>
{sop}
</sop>

Available tools:
{tools}

Use the following format:

Question: the input question you must answer using the SOP
Thought: think about what you need to do next
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action as a valid JSON object
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: Provide your final decision in the following XML format:

<final_decision>your_decision_value</final_decision>

Where your_decision_value should be the final decision as specified in the SOP. Provide ONLY the decision value inside the tags, without any additional explanation or formatting.

Begin!

Question: {input}
{agent_scratchpad}"""
        return PromptTemplate.from_template(template)

    def execute(
        self,
        sop: str,
        task: Dict[str, Any],
        tools: Any  # ToolManager instance
    ) -> AgentResult:
        """Execute a task using ReAct prompting via LangChain AgentExecutor."""
        start_time = time.time()
        logger.info("Executing ReAct agent on task")

        try:
            self._setup_llm()
            langchain_tools = self._create_langchain_tools(tools)
            prompt = self._create_react_prompt()

            # Use custom output parser for OpenAI GPT-OSS models to handle
            # <reasoning> tags, bare <final_decision>, and Action-line noise
            output_parser_kwargs = {}
            if self._is_openai_model():
                tool_names = [t.name for t in langchain_tools]
                output_parser_kwargs["output_parser"] = (
                    OpenAIReActOutputParser(tool_names=tool_names)
                )
                logger.info(
                    "Using OpenAIReActOutputParser for GPT-OSS model "
                    f"({len(tool_names)} tools registered)"
                )

            react_agent = create_react_agent(
                llm=self.llm,
                tools=langchain_tools,
                prompt=prompt,
                **output_parser_kwargs,
            )

            agent_executor = AgentExecutor.from_agent_and_tools(
                agent=react_agent,
                tools=langchain_tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=15,
                return_intermediate_steps=True
            )

            task_input = "\n".join([f"{k}: {v}" for k, v in task.items()])

            logger.info("Invoking ReAct agent")
            result = agent_executor.invoke({
                "input": f"Process this task according to the SOP:\n\n{task_input}",
                "sop": sop,
                "tools": "\n".join(
                    [f"- {t.name}: {t.description}" for t in langchain_tools]
                ),
                "tool_names": ", ".join([t.name for t in langchain_tools])
            })

            output = result.get("output", str(result))

            # Extract tool calls from intermediate_steps
            tool_calls = []
            intermediate_steps = result.get("intermediate_steps", [])
            for iteration, step in enumerate(intermediate_steps):
                if len(step) >= 2:
                    agent_action, observation = step[0], step[1]
                    tool_name = getattr(agent_action, 'tool', str(agent_action))
                    tool_input = getattr(agent_action, 'tool_input', {})
                    tool_success = not str(observation).startswith("Error:")
                    tool_calls.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "output": str(observation),
                        "iteration": iteration + 1,
                        "success": tool_success
                    })

            execution_time = time.time() - start_time
            logger.info(
                f"ReAct agent completed in {execution_time:.2f} seconds"
            )

            return AgentResult(
                output=output,
                tool_calls=tool_calls,
                reasoning_trace=str(result),
                execution_time=execution_time,
                success=True,
                error=None
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"ReAct agent failed: {e}")
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

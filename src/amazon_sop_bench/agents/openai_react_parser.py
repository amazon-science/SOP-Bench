"""Custom ReAct output parser for OpenAI GPT-OSS models.

GPT-OSS models exhibit two format-compliance failures that cause
LangChain's default ``ReActOutputParser`` to reject otherwise-correct output:

1. **<reasoning> wrapper** — The model wraps its chain-of-thought in
   ``<reasoning>...</reasoning>`` tags instead of using ``Thought:``.
2. **Bare <final_decision>** — The model emits
   ``<final_decision>X</final_decision>`` directly (without ``Final Answer:``
   prefix), which the default parser cannot extract.

This parser handles both cases, falling back to the default
``ReActSingleInputOutputParser`` for well-formatted output.
"""

import re
from typing import List, Union

from langchain.agents import AgentOutputParser
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.schema import AgentAction, AgentFinish, OutputParserException

# Regex patterns for GPT-OSS quirks
_REASONING_TAG_RE = re.compile(r"<reasoning>.*?</reasoning>", re.DOTALL)
_FINAL_DECISION_RE = re.compile(
    r"<final_decision>\s*(.*?)\s*</final_decision>", re.DOTALL
)


class OpenAIReActOutputParser(AgentOutputParser):
    """ReAct output parser that handles GPT-OSS format quirks.

    Falls back to the default LangChain parser for well-formatted output.
    """

    default_parser: ReActSingleInputOutputParser = (
        ReActSingleInputOutputParser()
    )
    tool_names: List[str] = []

    def get_format_instructions(self) -> str:
        return self.default_parser.get_format_instructions()

    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        # Step 1: Strip <reasoning> tags — they confuse the default parser
        cleaned = _REASONING_TAG_RE.sub("", text).strip()

        # Step 2: Check for bare <final_decision> (no Final Answer: prefix)
        fd_match = _FINAL_DECISION_RE.search(cleaned)
        if fd_match and "Action:" not in cleaned:
            decision = fd_match.group(1).strip()
            return AgentFinish(
                return_values={"output": decision},
                log=text,
            )

        # Step 3: Try the default parser on cleaned text
        try:
            return self.default_parser.parse(cleaned)
        except OutputParserException:
            pass  # Fall through to final decision fallback

        # Step 4: If there's a <final_decision> anywhere and we couldn't
        # parse an action, treat it as final answer
        if fd_match:
            decision = fd_match.group(1).strip()
            return AgentFinish(
                return_values={"output": decision},
                log=text,
            )

        # Nothing worked — raise so handle_parsing_errors can kick in
        raise OutputParserException(
            f"Could not parse LLM output: `{text}`",
            llm_output=text,
        )

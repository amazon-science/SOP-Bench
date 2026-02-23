# Bedrock Model Compatibility: Non-Claude Model Handling

This document explains the custom processing required to run non-Claude models
(OpenAI GPT-OSS, Meta Llama, DeepSeek) with LangChain's ReAct agent on
Amazon Bedrock's InvokeModel API.

## The Problem

LangChain's `create_react_agent` injects `stop=["\nObservation:"]` into every
LLM call. This stop sequence is critical for the ReAct loop — it forces the
model to pause after emitting `Action`/`Action Input` so LangChain can execute
the tool and inject the real observation.

`langchain-aws`'s `ChatBedrock` class validates stop sequences against a
hardcoded provider map (`provider_stop_sequence_key_name_map` in
`langchain_aws/llms/bedrock.py`) that only includes `anthropic`, `amazon`,
`ai21`, `cohere`, and `mistral`. Any provider not in this map raises:

```
ValueError: Stop sequence key name for {provider} is not supported.
```

This affects all non-listed providers: `meta` (Llama), `openai` (GPT-OSS),
and `deepseek`.

### References

- [LangChain forum: Agentic flow fails for non-Claude models on Bedrock](https://forum.langchain.com/t/langchain-v1-agentic-flow-on-bedrock-fails-for-non-claude-models-available-in-bedrock-llama4-nova-gpt-oss/2251)
- [langchain-aws source (provider map)](https://github.com/langchain-ai/langchain-aws)
- [Bedrock Converse API InferenceConfiguration](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InferenceConfiguration.html)

## Why Not Use ChatBedrockConverse?

`ChatBedrockConverse` (Converse API) handles stop sequences uniformly for all
providers through a single `stopSequences` parameter. However, switching from
InvokeModel to Converse API mid-experiment would introduce a confounding
variable — different API paths can produce different tokenization and response
structures. All SOP-Bench results use InvokeModel for consistency.

## Why Not Patch the Provider Map?

We tested extending `provider_stop_sequence_key_name_map` to include
`"openai": "stop"` at instantiation time. While this bypasses the validation
error, `ChatBedrock` has additional internal routing issues for non-Anthropic
providers (e.g., "No generation chunks were returned" errors) that make direct
usage unreliable. The wrapper approach is the only path that works consistently.

## Solution: StopSequenceSafeChatBedrock Wrapper

We wrap `ChatBedrock` via `BaseChatModel` (not subclass) to intercept the
`stop` kwarg before `ChatBedrock`'s validation sees it. The wrapper delegates
to a `ChatBedrock` instance internally.

### Tier 1: Claude (No Wrapper)

Claude models use `ChatBedrock` directly. The InvokeModel API supports
`stop_sequences` natively, and `ChatBedrock`'s provider map includes
`anthropic`.

### Tier 2: OpenAI GPT-OSS (Wrapper + Parser)

**Stop handling:** The wrapper passes `stop=stop` through to `ChatBedrock`'s
internal `_generate()`, bypassing the provider map validation. OpenAI's
InvokeModel API accepts the `stop` parameter natively.

**Custom parser (`OpenAIReActOutputParser`):** Handles GPT-OSS format quirks
at the parse level:

| Issue | Example | Fix |
|-------|---------|-----|
| `<reasoning>` wrapper | `<reasoning>thinking...</reasoning>Action: tool` | Strip tags before parsing |
| Bare `<final_decision>` | `<final_decision>Hazard Class C</final_decision>` | Extract as final answer |

No LLM-output-level post-processing is applied. Experiments showed that
parser-only handling produces equivalent or better results compared to
adding `_generate`-level post-processing (46.4% vs 48.2% TSR on
dangerous_goods, 37.8% vs 37.8% on know_your_business).

### Tier 3: Meta Llama / DeepSeek (Wrapper + Client-Side Truncation)

**Stop handling:** The wrapper calls `ChatBedrock` with `stop=None` (the
InvokeModel API rejects stop parameters for Meta models with
`ValidationException: extraneous key [stop] is not permitted`).

**Client-side truncation:** The generated text is truncated at the first
`\nObservation:` marker, simulating server-side stop behavior. Without this,
the model hallucinates tool outputs and LangChain never actually invokes tools.

**Thought sanitization:** Llama models mention `Final Answer:` inside
`Thought:` blocks as future intent (e.g., "I'll provide the Final Answer:
with the classification"). When `Action:` is also present, LangChain's parser
raises "both a final answer and a parse-able action". The fix replaces
premature `Final Answer:` in the Thought section with lowercase
`final answer`, which the parser ignores.

## Impact on Benchmark Results

Experiments on the `dangerous_goods` SOP (274 tasks) with OpenAI GPT-OSS 120B:

| Configuration | TSR | ECR | Avg Time |
|---------------|-----|-----|----------|
| No fixes (raw ChatBedrock) | 0% | 100% | 11.4s |
| Llama-style truncation only | 4.4% | 100% | 11.3s |
| Parser only (final, Tier 2) | 47.1% | 100% | 2.2s |

Experiments on the `know_your_business` SOP (90 tasks) with OpenAI GPT-OSS 120B:

| Configuration | TSR | ECR | Avg Time |
|---------------|-----|-----|----------|
| No fixes (raw ChatBedrock) | 0% | 100% | 11.4s |
| Llama-style truncation only | 4.4% | 100% | 11.3s |
| Parser only (final, Tier 2) | 48.9% | 100% | 1.7s |

The custom parser eliminates all parsing errors and iteration-limit timeouts,
improving TSR from 0% to ~48% across both SOPs.

## File Reference

- `src/amazon_sop_bench/agents/react.py` — `StopSequenceSafeChatBedrock`
  wrapper (stop-sequence bypass for OpenAI, client-side truncation + Thought
  sanitization for Llama), `ReActAgent` class
- `src/amazon_sop_bench/agents/openai_react_parser.py` —
  `OpenAIReActOutputParser` for GPT-OSS format quirks (`<reasoning>` tag
  stripping, bare `<final_decision>` extraction)

# Agent Guide

SOP-Bench provides multiple agent implementations for evaluating how different architectures handle SOP execution.

## Table of Contents

- [Overview](#overview)
- [Agent Types](#agent-types)
- [Model Compatibility](#model-compatibility)
- [Programmatic Usage](#programmatic-usage)
- [Custom Agents](#custom-agents)
- [Performance Comparison](#performance-comparison)

---

## Overview

An **agent** in SOP-Bench is responsible for:
1. Reading the SOP (natural language instructions)
2. Understanding the task inputs
3. Orchestrating tool calls to gather information
4. Making a final decision based on the SOP logic

Different agent architectures approach this differently, leading to varying performance across benchmarks.

---

## Agent Types

### 1. Function Calling Agent (`function_calling`)

Uses AWS Bedrock's native Converse API for structured tool use.

```bash
./sop-bench evaluate content_flagging --agent function_calling
```

**How it works:**
- Sends tools as structured function definitions to the model
- Model returns structured tool calls
- Framework executes tools and returns results
- Model makes final decision

**Pros:**
- Clean, structured tool calls
- Native model support
- Lower token usage

**Cons:**
- Less reasoning visibility
- Can miss complex multi-step logic

### 2. ReAct Agent (`react`) — Recommended

Custom ReAct (Reasoning + Acting) loop optimized for SOP execution.

```bash
./sop-bench evaluate content_flagging --agent react
```

**How it works:**
1. **Thought:** Model reasons about what to do next
2. **Action:** Model decides which tool to call
3. **Observation:** Framework executes tool, returns result
4. **Repeat** until model reaches final answer

**Pros:**
- Works with all model families
- Visible reasoning chain
- Better at complex multi-step SOPs
- Optimized for SOP-specific patterns

**Cons:**
- Higher token usage
- Slower execution

### 3. ReAct Legacy Agent (`react_legacy`)

Original LangChain-based ReAct implementation for research comparison.

```bash
./sop-bench evaluate content_flagging --agent react_legacy
```

**When to use:**
- Comparing against original LangChain ReAct behavior
- Research reproducibility
- Historical baseline comparison

**Requirements:**
```bash
pip install langchain langchain-community
```

**Limitations:**
- Not compatible with OpenAI models on Bedrock (stop sequence issue)
- Less optimized than custom `react` agent

### 4. ReAct Meta Agent (`react_meta`)

Specialized ReAct agent optimized for Meta Llama models.

```bash
./sop-bench evaluate dangerous_goods --agent react_meta --model meta.llama3-70b-instruct-v1:0
```

**When to use:**
- Evaluating Llama models
- Need Llama-specific prompt formatting

---

## Model Compatibility

| Model Family | `function_calling` | `react` | `react_legacy` | `react_meta` |
|-------------|-------------------|---------|----------------|--------------|
| Claude (Anthropic) | ✅ | ✅ | ✅ | ❌ |
| Llama (Meta) | ✅ | ✅ | ✅ | ✅ |
| Mistral | ✅ | ✅ | ✅ | ❌ |
| OpenAI (via Bedrock) | ✅ | ✅ | ❌* | ❌ |
| DeepSeek | ✅ | ✅ | ✅ | ❌ |

*OpenAI models don't support the stop sequences used by LangChain's ReAct.

### Recommended Model IDs

```bash
# Claude 3.5 Sonnet (recommended)
--model us.anthropic.claude-3-5-sonnet-20241022-v2:0

# Claude 3 Haiku (faster, cheaper)
--model anthropic.claude-3-haiku-20240307-v1:0

# Llama 3 70B
--model meta.llama3-70b-instruct-v1:0

# Mistral Large
--model mistral.mistral-large-2402-v1:0
```

---

## Programmatic Usage

### Basic Evaluation

```python
from amazon_sop_bench import evaluate

results = evaluate(
    benchmark_name="content_flagging",
    agent_type="react",
    model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    max_tasks=10
)

print(f"Task Success Rate: {results['task_success_rate']:.1%}")
print(f"Tool Accuracy: {results['tool_accuracy']:.1%}")
```

### Comparing Agents

```python
from amazon_sop_bench import evaluate

agents = ["function_calling", "react", "react_legacy"]
benchmark = "dangerous_goods"

for agent in agents:
    results = evaluate(
        benchmark_name=benchmark,
        agent_type=agent,
        max_tasks=50
    )
    print(f"{agent}: TSR={results['task_success_rate']:.1%}")
```

### With Trace Saving

```python
from amazon_sop_bench import evaluate

results = evaluate(
    benchmark_name="content_flagging",
    agent_type="react",
    save_traces=True,
    trace_dir="my_traces/"
)

# Traces saved to my_traces/
```

### Batch Evaluation

```python
from amazon_sop_bench import evaluate, list_benchmarks

benchmarks = list_benchmarks()
all_results = {}

for benchmark in benchmarks:
    results = evaluate(
        benchmark_name=benchmark['name'],
        agent_type="react",
        max_tasks=20  # Quick evaluation
    )
    all_results[benchmark['name']] = results['task_success_rate']

# Print summary
for name, tsr in sorted(all_results.items(), key=lambda x: -x[1]):
    print(f"{name}: {tsr:.1%}")
```

---

## Custom Agents

You can implement your own agent by inheriting from `BaseAgent`.

### Basic Structure

```python
from amazon_sop_bench.agents import BaseAgent

class MyCustomAgent(BaseAgent):
    """My custom agent implementation."""
    
    def __init__(self, model_id: str, region: str = "us-west-2", **kwargs):
        super().__init__(model_id, region, **kwargs)
        # Your initialization here
    
    def execute(self, sop: str, task: dict, tools: list) -> dict:
        """
        Execute a task given SOP instructions.
        
        Args:
            sop: Natural language SOP text
            task: Task inputs (dict with task-specific data)
            tools: Available tools (list of tool specifications)
            
        Returns:
            dict with keys:
                - output: Final decision/output string
                - tool_calls: List of tool calls made
                - reasoning: Agent's reasoning trace (optional)
        """
        # 1. Parse the SOP
        # 2. Plan which tools to call
        # 3. Execute tools iteratively
        # 4. Apply SOP logic to make decision
        
        tool_calls = []
        reasoning = []
        
        # Your agent logic here...
        
        # Format output for best parsing
        final_output = f"<final_decision>{decision}</final_decision>"
        
        return {
            "output": final_output,
            "tool_calls": tool_calls,
            "reasoning": "\n".join(reasoning)
        }
```

### Using Your Custom Agent

```python
from amazon_sop_bench import evaluate
from my_agents import MyCustomAgent

# Create agent instance
agent = MyCustomAgent(
    model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    region="us-west-2"
)

# Evaluate
results = evaluate(
    benchmark_name="content_flagging",
    agent=agent  # Pass instance instead of agent_type string
)
```

### Output Format

For best compatibility with the evaluation framework, format your agent's output using XML tags:

```xml
<final_decision>your_decision_value</final_decision>
```

The framework uses a fallback parser chain: XML → JSON → Dict → Plain Text.

### Tool Call Format

Tool calls should be recorded as:

```python
tool_call = {
    "tool_name": "get_user_trust_score",
    "parameters": {"user_id": "U12345"},
    "result": {"trust_score": 0.85, "account_age_days": 120}
}
tool_calls.append(tool_call)
```

---

## Performance Comparison

### By Benchmark (Claude 3.5 Sonnet)

| Benchmark | FC-Agent | ReAct | Winner |
|-----------|----------|-------|--------|
| Aircraft Inspection | 1% | 87% | ReAct |
| Dangerous Goods | 59% | 80% | ReAct |
| Video Annotation | 49% | 69% | ReAct |
| Email Intent | 31% | 60% | ReAct |
| Know Your Business | 19% | 36% | ReAct |
| Video Classification | 52% | 21% | FC |
| Warehouse Inspection | 13% | 21% | ReAct |
| Content Flagging | 0% | 10% | ReAct |
| Customer Service | 14% | 3% | FC |
| Patient Intake | 0% | 0% | Tie |

### Key Insights

1. **ReAct generally outperforms Function-Calling** on complex, multi-step SOPs
2. **Function-Calling wins** on simpler, more structured tasks
3. **Both struggle** with healthcare (Patient Intake) — domain complexity matters
4. **Visible reasoning** in ReAct helps with debugging and understanding failures

### When to Use Which

| Scenario | Recommended Agent |
|----------|-------------------|
| Complex multi-step SOPs | `react` |
| Simple, structured tasks | `function_calling` |
| Llama models | `react_meta` |
| Research comparison | `react_legacy` |
| Production deployment | `function_calling` (lower cost) |
| Debugging/analysis | `react` (visible reasoning) |

---

## Next Steps

- **[Getting Started](GETTING_STARTED.md)** — Installation and setup
- **[Adding Benchmarks](ADDING_BENCHMARKS.md)** — Create custom SOPs
- **[Examples](../examples/)** — Code samples

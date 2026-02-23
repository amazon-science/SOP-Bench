# SOP-Bench Examples

This directory contains practical examples demonstrating how to use SOP-Bench for various use cases.

## Quick Start Examples

### Basic Usage
- **[01_basic_evaluation.py](01_basic_evaluation.py)** - Simple evaluation of a single benchmark
- **[02_list_benchmarks.py](02_list_benchmarks.py)** - List and explore available benchmarks

### Agent Examples
- **[03_custom_agent.py](03_custom_agent.py)** - Implement a custom agent
- **[04_compare_agents.py](04_compare_agents.py)** - Compare multiple agents

### Advanced Usage
- **[05_batch_evaluation.py](05_batch_evaluation.py)** - Evaluate multiple benchmarks
- **[06_parallel_execution.py](06_parallel_execution.py)** - Speed up evaluation with parallel workers
- **[07_save_traces.py](07_save_traces.py)** - Save execution traces for debugging

### Analysis
- **[08_analyze_results.py](08_analyze_results.py)** - Analyze evaluation results
- **[09_error_analysis.py](09_error_analysis.py)** - Identify common failure patterns

### Custom Benchmarks
- **[10_custom_benchmark.py](10_custom_benchmark.py)** - Create a new benchmark

## Running Examples

### Prerequisites

```bash
# Install SOP-Bench
pip install amazon-sop-bench

# Or install from source
cd AmazonSOPBench
pip install -e .

# Configure AWS credentials
cp .env.example .env
# Edit .env with your AWS credentials
```

### Run an Example

```bash
# From the examples directory
cd examples

# Run basic evaluation
python 01_basic_evaluation.py

# Run with custom parameters
python 06_parallel_execution.py --max-workers 5
```

## Example Categories

### 1. Getting Started (01-02)

Perfect for first-time users. Learn how to:
- Run your first evaluation
- List available benchmarks
- Understand the output metrics

### 2. Agent Development (03-04)

For researchers building new agents. Learn how to:
- Implement a custom agent
- Compare different agent architectures
- Evaluate agent performance

### 3. Advanced Evaluation (05-07)

For power users. Learn how to:
- Batch evaluate multiple benchmarks
- Use parallel execution for speed
- Save and analyze execution traces

### 4. Analysis & Debugging (08-09)

For understanding results. Learn how to:
- Analyze evaluation metrics
- Identify failure patterns
- Debug agent behavior

### 5. Customization (10)

For extending SOP-Bench. Learn how to:
- Create custom benchmarks
- Add new SOPs
- Implement custom tools

## Common Patterns

### Pattern 1: Quick Test

Test a single task to verify setup:

```python
from amazon_sop_bench import evaluate

results = evaluate(
    benchmark_name="content_flagging",
    agent_type="function_calling",
    max_tasks=1  # Just test one task
)
print(f"TSR: {results['task_success_rate']:.1%}")
```

### Pattern 2: Full Evaluation

Evaluate all tasks in a benchmark:

```python
results = evaluate(
    benchmark_name="content_flagging",
    agent_type="react",
    save_traces=True  # Save for debugging
)
```

### Pattern 3: Batch Evaluation

Evaluate multiple benchmarks:

```python
from amazon_sop_bench import list_benchmarks, evaluate

benchmarks = list_benchmarks()
for benchmark in benchmarks:
    results = evaluate(
        benchmark_name=benchmark['name'],
        agent_type="function_calling"
    )
    print(f"{benchmark['name']}: {results['task_success_rate']:.1%}")
```

### Pattern 4: Custom Agent

Implement your own agent:

```python
from amazon_sop_bench.agents import BaseAgent
from amazon_sop_bench import evaluate

class MyAgent(BaseAgent):
    def execute(self, sop, task, tools):
        # Your agent logic here
        return {
            "output": "<final_decision>approved</final_decision>",
            "tool_calls": [],
            "reasoning": "My reasoning"
        }

results = evaluate(
    benchmark_name="content_flagging",
    agent=MyAgent()
)
```

## Tips & Best Practices

### Performance

- **Use parallel execution** for faster evaluation:
  ```python
  evaluate(..., max_workers=10)
  ```

- **Limit tasks during development**:
  ```python
  evaluate(..., max_tasks=5)
  ```

### Debugging

- **Save traces** to understand agent behavior:
  ```python
  evaluate(..., save_traces=True)
  # Check: results/{benchmark}_{agent}_traces/
  ```

- **Use verbose logging**:
  ```python
  import logging
  logging.basicConfig(level=logging.DEBUG)
  ```

### Cost Management

- **Test with small samples** first:
  ```python
  evaluate(..., max_tasks=10)  # Test before full run
  ```

- **Monitor AWS costs** in Bedrock console

### Reproducibility

- **Set random seed** for consistent results:
  ```python
  import random
  random.seed(42)
  ```

- **Pin model version** in config:
  ```python
  AWS_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
  ```

## Troubleshooting

### Import Errors

```bash
# Reinstall package
pip install -e . --force-reinstall
```

### AWS Credential Errors

```bash
# Verify AWS access
aws sts get-caller-identity
aws bedrock list-foundation-models --region us-west-2
```

### Low Task Success Rate

- Check agent output format (use XML tags)
- Review execution traces
- Verify tool calls are correct

## Additional Resources

- **Documentation**: [README.md](../README.md)
- **Architecture**: [ARCHITECTURE.md](../ARCHITECTURE.md)
- **Contributing**: [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Research Paper**: [arXiv:2506.08119](https://arxiv.org/abs/2506.08119)

## Support

- **Issues**: [GitHub Issues](https://github.com/amazon/sop-bench/issues)
- **Discussions**: [GitHub Discussions](https://github.com/amazon/sop-bench/discussions)

---

**Happy benchmarking!** 🚀

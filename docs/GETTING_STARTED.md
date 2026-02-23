# Getting Started with SOP-Bench

This guide covers installation, configuration, and running your first evaluation.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [AWS Configuration](#aws-configuration)
- [Running Evaluations](#running-evaluations)
- [Understanding Results](#understanding-results)
- [Parallel Execution](#parallel-execution)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- **Python 3.9+**
- **AWS Account** with Bedrock access (for LLM inference)
- **Claude model access** enabled in your AWS region

### Verify Python Version

```bash
python --version  # Should be 3.9 or higher
```

---

## Installation

### Option 1: From Source (Recommended)

```bash
# Clone repository
git clone https://github.com/amazon-science/SOP-Bench.git
cd SOP-Bench

# Install in development mode
pip install -e .

# Verify installation
./sop-bench --version
```

### Option 2: From PyPI

```bash
pip install amazon-sop-bench
```

### Development Installation

For contributing or running tests:

```bash
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

---

## AWS Configuration

SOP-Bench uses AWS Bedrock for LLM inference. You need valid AWS credentials with Bedrock access.

### Option A: Using .env File (Recommended)

```bash
# Copy example configuration
cp .env.example .env

# Edit with your settings
nano .env  # or your preferred editor
```

Required settings in `.env`:

```bash
AWS_REGION=us-west-2
AWS_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# Optional: Use IAM role
# AWS_ROLE_ARN=arn:aws:iam::123456789012:role/YourRole
```

### Option B: Using AWS CLI

```bash
# Configure AWS credentials
aws configure

# Or set environment variables directly
export AWS_REGION=us-west-2
export AWS_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

### Option C: Using IAM Roles

For EC2 instances or Lambda functions, attach an IAM role with Bedrock permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-*"
      ]
    }
  ]
}
```

### Verify AWS Setup

```bash
# Test AWS credentials
aws sts get-caller-identity

# List available Bedrock models
aws bedrock list-foundation-models --region us-west-2 --query "modelSummaries[?contains(modelId, 'claude')]"
```

---

## Running Evaluations

### List Available Benchmarks

```bash
./sop-bench list
```

Output:
```
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━┓
┃ Name               ┃ Domain  ┃ Tasks ┃ Tools ┃ Complexity ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━┩
│ content_flagging   │ unknown │   226 │     4 │        9/10│
│ dangerous_goods    │ unknown │   327 │     4 │        7/10│
│ ...                │ ...     │   ... │   ... │        ... │
└────────────────────┴─────────┴───────┴───────┴────────────┘
```

### Quick Test (1 Task)

```bash
./sop-bench evaluate content_flagging --agent function_calling --max-tasks 1
```

### Full Evaluation

```bash
# Evaluate all tasks
./sop-bench evaluate content_flagging --agent react

# Save results to file
./sop-bench evaluate content_flagging --agent react --output results.json

# Save execution traces for debugging
./sop-bench evaluate content_flagging --agent react --save-traces
```

### Specify Model

```bash
# Use a specific model
./sop-bench evaluate dangerous_goods \
  --agent react \
  --model us.anthropic.claude-3-5-sonnet-20241022-v2:0
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--agent` | Agent type: `function_calling`, `react`, `react_legacy`, `react_meta` |
| `--max-tasks` | Limit number of tasks to evaluate |
| `--output` | Save results to JSON file |
| `--save-traces` | Save detailed execution traces |
| `--max-workers` | Number of parallel workers (default: 1) |
| `--model` | Override model ID |

---

## Understanding Results

### Metrics Explained

| Metric | Description |
|--------|-------------|
| **Task Success Rate (TSR)** | % of tasks where agent made correct final decision |
| **Execution Completion Rate (ECR)** | % of tasks that completed without errors |
| **Conditional TSR (C-TSR)** | Of completed tasks, % that were correct |
| **Tool Accuracy** | % of tool calls that were correct |

**Relationship:** `TSR = ECR × C-TSR`

### Example Output

```
✓ Evaluation Complete!
Task Success Rate: 65.0%
Execution Completion Rate: 85.0%
Conditional Task Success Rate: 76.5%
Tool Accuracy: 82.3%
```

### Results JSON Structure

```json
{
  "benchmark": "content_flagging",
  "agent": "react",
  "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
  "task_success_rate": 0.65,
  "execution_completion_rate": 0.85,
  "tool_accuracy": 0.823,
  "num_tasks": 226,
  "results": [
    {
      "task_id": 1,
      "success": true,
      "expected": "flag",
      "actual": "flag",
      "tool_calls": [...]
    }
  ]
}
```

### Viewing Results

```bash
./sop-bench results results.json
```

---

## Parallel Execution

Speed up evaluations with parallel workers:

```bash
# Run with 5 parallel workers
./sop-bench evaluate content_flagging --agent react --max-workers 5

# Run with 10 parallel workers (max recommended)
./sop-bench evaluate content_flagging --agent react --max-workers 10
```

### Throttling

If you encounter throttling errors from AWS Bedrock:
1. Reduce `--max-workers` (try 3-5)
2. Wait a few minutes and retry
3. Request quota increase from AWS

---

## Troubleshooting

### AWS Credentials Issues

**Error:** `Unable to locate credentials`

```bash
# Verify credentials are set
aws sts get-caller-identity

# Check .env file exists and is correct
cat .env
```

**Error:** `Access denied to Bedrock`

1. Verify your IAM user/role has Bedrock permissions
2. Check the model is enabled in your region
3. Verify the model ID is correct

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'amazon_sop_bench'`

```bash
# Ensure you're in the correct directory
cd /path/to/sop-bench

# Reinstall
pip install -e . --force-reinstall
```

### Low Task Success Rate

1. **Check traces:** Use `--save-traces` to see what the agent is doing
2. **Verify model:** Some models perform better than others
3. **Try different agent:** ReAct often outperforms Function-Calling

```bash
# Debug with traces
./sop-bench evaluate content_flagging --agent react --max-tasks 5 --save-traces

# Check traces
ls results/content_flagging_react_traces/
cat results/content_flagging_react_traces/trace_1.txt
```

### Output Parsing Issues

The framework uses automatic parser fallback (XML → JSON → Dict → Plain Text). For best results, ensure your custom agents output decisions in structured format:

```xml
<final_decision>your_decision_value</final_decision>
```

### Build/Package Issues

```bash
# Clean and rebuild
rm -rf build/ dist/ *.egg-info
pip install -e . --force-reinstall
```

---

## Next Steps

- **[Agents Guide](AGENTS.md)** — Learn about different agent types
- **[Adding Benchmarks](ADDING_BENCHMARKS.md)** — Create your own SOPs
- **[Examples](../examples/)** — Code samples for common use cases
- **[Architecture](../ARCHITECTURE.md)** — Technical deep dive

---

## Getting Help

- **GitHub Issues:** [Report bugs](https://github.com/amazon-science/SOP-Bench/issues)
- **Discussions:** [Ask questions](https://github.com/amazon-science/SOP-Bench/discussions)
- **Support:** Open an issue on [GitHub](https://github.com/amazon-science/sop-bench/issues)

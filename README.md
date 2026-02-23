# SOP-Bench : Complex Industrial SOPs for Evaluating LLM Agents

<img width="1200" height="800" alt="image" src="https://github.com/user-attachments/assets/db61aa12-b64e-47e6-b71d-01aa80c3124e" />

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](LICENSE)
[![Lint](https://github.com/amazon-science/SOP-Bench/actions/workflows/lint.yml/badge.svg)](https://github.com/amazon-science/SOP-Bench/actions/workflows/lint.yml)
[![Tests](https://github.com/amazon-science/SOP-Bench/actions/workflows/test.yml/badge.svg)](https://github.com/amazon-science/SOP-Bench/actions/workflows/test.yml)

## Overview

**SOP-Bench** is a comprehensive benchmark for evaluating LLM-based agents on complex, multi-step Standard Operating Procedures (SOPs) that are fundamental to industrial automation. Built from 2,000+ tasks across 12 industrial domains (healthcare, logistics, finance, content moderation, etc.), SOP-Bench addresses the gap between existing benchmarks and real-world procedural complexity.

🏭 **Human Expert-Authored SOPs** · 🤖 **Human-AI Collaborative Framework** · 📊 **Executable Interfaces** · 🔧 **Two Agent Architectures** · 📈 **11 Frontier Models Evaluated**

## News

- **[2026-02]** 🎉 SOP-Bench submitted to KDD 2026 Datasets and Benchmarks Track.

---

## The Problem

Standard Operating Procedures (SOPs) are the backbone of industrial operations—from content moderation to healthcare intake to supply chain logistics. These multi-step procedures require:

- **Sequential reasoning** across 10-50+ decision points
- **Tool orchestration** to gather information from multiple systems  
- **Implicit knowledge** that humans learn but rarely document
- **Ambiguity handling** when procedures don't cover edge cases

**Can LLM agents reliably execute these procedures?**

Our research shows they struggle significantly—with performance varying dramatically across domains (26.7%-94.3% success rates).

---

## Key Findings

📊 **Detailed leaderboard and benchmark results coming soon.**

Early findings from our evaluation of 11 frontier models:

- **Function-Calling agents**: ~64% average task success rate
- **ReAct agents**: ~55% average task success rate  
- **High execution rates (95%+)** indicate failures are reasoning-based, not technical
- **Open-source models** (DeepSeek-R1, Llama 3.3) approach proprietary performance
- **Architecture-model co-design matters**: Newer reasoning models can degrade ReAct performance without targeted prompt engineering

---

## What's in SOP-Bench?

**2,000+ tasks** across **12 industrial domains**, created through human-AI collaboration:

| Domain | Description |
|--------|-------------|
| Content Moderation | Bot detection, trust scoring, violation assessment |
| Customer Service | Issue diagnosis, system checks, resolution routing |
| Supply Chain | Safety data sheet analysis, hazard classification |
| Aviation | Pre-flight safety checks, compliance verification |
| Retail | Seller email categorization, routing decisions |
| Finance | Business entity verification, risk assessment |
| Healthcare | Insurance validation, medical history processing |
| Autonomous Driving | Object detection in driving scenarios |
| Media | Content moderation, category assignment |
| Logistics | Package damage assessment, compliance checks |
| *...and more* | |

**Human expert-authored SOPs** • **Mock tools for reproducibility** • **Ground-truth outputs** • **Multiple agent architectures**

---

## Example: What Does an SOP Task Look Like?

Here's a simplified example from the **Dangerous Goods** benchmark:

**SOP Instruction (excerpt):**
> *"1. Retrieve the Safety Data Sheet for the product. 2. Check if the product contains any Class 3 flammable liquids. 3. If flash point < 23°C, classify as Packing Group I..."*

**Task Input:**
```json
{
  "product_id": "CHEM-2847",
  "shipment_type": "air_freight"
}
```

**Expected Agent Behavior:**
1. Call `get_safety_data_sheet(product_id="CHEM-2847")`
2. Call `check_hazard_class(sds_id="SDS-2847")`
3. Call `get_flash_point(sds_id="SDS-2847")`
4. Apply classification logic from SOP
5. Return: `{"classification": "Class 3", "packing_group": "II"}`

**Ground Truth:** `packing_group: II`

The agent must correctly orchestrate tools AND apply the SOP's decision logic.

---

## Quick Start

### Install

```bash
git clone https://github.com/amazon-science/SOP-Bench.git
cd SOP-Bench
pip install -e .
```

### Configure AWS (for Bedrock models)

```bash
cp .env.example .env
# Edit .env with your AWS credentials and model ID
```

### Run Your First Evaluation

```bash
# List available benchmarks
./sop-bench list

# Evaluate on a single task
./sop-bench evaluate content_flagging --agent function_calling --max-tasks 1

# Expected output:
# Evaluating content_flagging with function_calling agent...
# Limited to 1 tasks
# 
# Starting evaluation...
# Evaluating content_flagging ━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:16
# 
# ✓ Evaluation Complete!
# Task Success Rate: 100.0%
# Execution Completion Rate: 100.0%
# Tool Accuracy: 100.0%
```

**Understanding the Metrics:**
- **Task Success Rate (TSR)**: Percentage of tasks where the agent made the correct decision
- **Execution Completion Rate (ECR)**: Percentage of tasks that completed without errors
- **Conditional Task Success Rate (C-TSR)**: Of the tasks that completed execution, how many were accurate? This measures decision accuracy for successfully executed tasks only.
- **Tool Accuracy**: Percentage of tool calls that were correct

**Note**: TSR = ECR × C-TSR (Task Success Rate equals Execution Completion Rate times Conditional Task Success Rate)

### 5. Run Full Evaluation

```bash
# Run on all tasks and save results
./sop-bench evaluate content_flagging --agent function_calling --output results.json

# Save execution traces for debugging
./sop-bench evaluate content_flagging --agent function_calling --save-traces

# View results
./sop-bench results results.json
```

### Parallel Execution

By default, AmazonSOPBench runs evaluations **sequentially** (one task at a time). You can enable parallel execution with the `--max-workers` option to speed up your evaluations. It is recommended to start with 3 workers and can increase up to 10 if you are not getting throttled. If you get throttling exception, just decrease the number of workers in next run. 

```bash
# Default: Sequential execution (1 worker)
./sop-bench evaluate content_flagging --agent function_calling

# Run with 10 parallel workers
./sop-bench evaluate content_flagging --agent function_calling --max-workers 10

# Run with 5 parallel workers
./sop-bench evaluate content_flagging --agent function_calling --max-workers 5
```

The `--max-workers` option is also available in `batch_evaluate.py` for batch runs across multiple models:

```bash
# Batch evaluate with 4 parallel workers per model run
python batch_evaluate.py --sop dangerous_goods \
  --models "Claude Opus 4.5,Claude Sonnet 4.5,Llama 3.3 70B,OpenAI GPT-OSS 120B" \
  --agents react --max-workers 4 --save-traces
```

**Debugging with Traces:**
When using `--save-traces`, execution traces are saved to `results/{benchmark}_{agent}_traces/` for detailed debugging of agent behavior and tool calls.

## Troubleshooting

### Common Issues

**AWS Credentials**: Ensure your AWS account has Bedrock access and Claude model permissions.
```bash
# Test AWS access
aws sts get-caller-identity
aws bedrock list-foundation-models --region us-west-2
```

**Import Errors**: Make sure you're in the AmazonSOPBench directory and installed correctly.
```bash
cd /path/to/AmazonSOPBench
pip install -e . --force-reinstall
```

**Low Task Success Rate**: The framework uses automatic parser fallback (XML → JSON → Dict → Plain Text) to extract agent decisions. For best results, agents should output decisions in structured format:
```xml
<final_decision>your_decision_value</final_decision>
```

**Debugging Failed Tasks**: Use `--save-traces` to save detailed execution logs:
```bash
./sop-bench evaluate content_flagging --agent function_calling --save-traces
# Check traces in: results/content_flagging_function_calling_traces/
```

For comprehensive testing and validation, see [VALIDATION_COMMANDS.md](VALIDATION_COMMANDS.md).

## Agent Types

AmazonSOPBench provides multiple agent implementations for evaluating SOP execution:

### 1. ReAct Agent (Default - Recommended)

The default `react` agent uses LangChain's `create_react_agent` / `AgentExecutor` with automatic stop-sequence handling for all Bedrock model families. This is the agent used for all SOP-Bench experiments.

```bash
# Use the ReAct agent (default)
./sop-bench evaluate content_flagging --agent react
```

**Features:**
- ✅ Works with all model families (Claude, Llama, OpenAI, DeepSeek)
- ✅ Automatic stop-sequence handling via `StopSequenceSafeChatBedrock` wrapper
- ✅ Client-side truncation and Thought sanitization for non-Claude models
- ✅ Used for all SOP-Bench paper experiments
- ✅ Recommended for all evaluations

The ReAct agent uses a `StopSequenceSafeChatBedrock` wrapper that automatically handles stop sequences across all model families:
- **Claude**: Native stop-sequence support (no wrapper needed)
- **OpenAI GPT-OSS**: Wrapper bypasses LangChain validation, passes stop sequences through natively
- **Meta Llama/DeepSeek**: Wrapper strips stop sequences, applies client-side truncation + Thought sanitization

**Usage Examples:**

```bash
# Use with Claude models
./sop-bench evaluate content_flagging \
  --agent react \
  --model us.anthropic.claude-3-5-sonnet-20241022-v2:0

# Use with Llama models
./sop-bench evaluate dangerous_goods \
  --agent react \
  --model us.meta.llama3-3-70b-instruct-v1:0

# Use with OpenAI models
./sop-bench evaluate dangerous_goods \
  --agent react \
  --model openai.gpt-oss-120b-1:0
```

**Programmatic Usage:**

```python
from amazon_sop_bench import evaluate

# Evaluate with ReAct agent
results = evaluate(
    benchmark_name="content_flagging",
    agent_type="react",
    model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0"
)

print(f"Task Success Rate: {results['task_success_rate']:.1%}")
```

### 2. Function Calling Agent

Native function calling using Bedrock's Converse API:

```bash
./sop-bench evaluate content_flagging --agent function_calling
```

## Available Benchmarks

| Benchmark | Domain | Description | Tasks | Complexity |
|-----------|--------|-------------|-------|------------|
| **content_flagging** | Content Moderation | Evaluate flagged user content through bot detection, trust scoring, and violation assessment | 226 | 9/10 |
| **customer_service** | Support | Diagnose and resolve customer service issues using system diagnostics | 208 | 8/10 |
| **dangerous_goods** | Supply Chain | Classify dangerous goods using safety data sheets and scoring systems | 327 | 7/10 |
| **aircraft_inspection** | Transportation | Conduct pre-flight safety inspections following aviation procedures | 150 | 9/10 |
| **email_intent** | Retail | Categorize seller support emails and route appropriately | 122 | 7/10 |
| **know_your_business** | Finance | Verify business entities for compliance and risk assessment | 122 | 9/10 |
| **patient_intake** | Healthcare | Register new patients with insurance and medical history validation | 90 | 7/10 |
| **video_annotation** | Autonomous Driving | Detect and annotate objects in driving videos | 168 | 10/10 |
| **video_classification** | Media | Classify and moderate user-generated video content | 198 | 9/10 |
| **warehouse_inspection** | Logistics | Inspect packages for damage and compliance | 200 | 9/10 |

## Programmatic Usage

### Basic Evaluation

```python
from amazon_sop_bench import evaluate, list_benchmarks

# Run evaluation
results = evaluate(
    benchmark_name="content_flagging",
    agent_type="react",
    max_tasks=10
)

print(f"Task Success Rate: {results['task_success_rate']:.1%}")
print(f"Tool Accuracy: {results['tool_accuracy']:.1%}")
```

📖 **[Full Getting Started Guide →](docs/GETTING_STARTED.md)**

---

## Example: What Does an SOP Task Look Like?

Here's a simplified example from the **Dangerous Goods** benchmark:

**SOP Instruction (excerpt):**
> *"1. Retrieve the Safety Data Sheet for the product. 2. Check if the product contains any Class 3 flammable liquids. 3. If flash point < 23°C, classify as Packing Group I..."*

**Task Input:**
```json
{
  "product_id": "CHEM-2847",
  "shipment_type": "air_freight"
}
```

**Expected Agent Behavior:**
1. Call `get_safety_data_sheet(product_id="CHEM-2847")`
2. Call `check_hazard_class(sds_id="SDS-2847")`  
3. Call `get_flash_point(sds_id="SDS-2847")`
4. Apply classification logic from SOP
5. Return: `{"classification": "Class 3", "packing_group": "II"}`

**Ground Truth:** `packing_group: II`

The agent must correctly orchestrate tools AND apply the SOP's decision logic.

---

## Agent Types

| Agent | Description | Best For |
|-------|-------------|----------|
| `function_calling` | Native Bedrock Converse API | Structured tool use |
| `react` | Custom ReAct loop (recommended) | All model families |

📖 **[Agent Documentation →](docs/AGENTS.md)**

---

## Adding Your Own Benchmarks

SOP-Bench is extensible. Create new benchmarks with:

```
benchmarks/data/your_benchmark/
├── sop.txt          # Natural language procedure
├── tools.py         # Tool implementations  
├── toolspecs.json   # Tool schemas for LLM
├── data.csv         # Test cases with ground truth
└── metadata.json    # Configuration
```

📖 **[Adding Benchmarks Guide →](docs/ADDING_BENCHMARKS.md)**

---

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](docs/GETTING_STARTED.md) | Installation, configuration, troubleshooting |
| [Agents Guide](docs/AGENTS.md) | Agent types, model compatibility, examples |
| [Adding Benchmarks](docs/ADDING_BENCHMARKS.md) | Create custom SOP benchmarks |
| [Architecture](ARCHITECTURE.md) | Technical design and internals |
| [Examples](examples/) | Code samples for common use cases |

---

## Citation

If you use SOP-Bench in your research, please cite:

```bibtex
@inproceedings{sopbench2026,
  title={SOP-Bench: Complex Industrial SOPs for Evaluating LLM Agents},
  author={Nandi, Subhrangshu and Datta, Arghya and Vichare, Nikhil and 
          Nama, Rohith and Patel, Udita and Bhattacharya, Indranil and 
          Asija, Shivam and Gupta, Arushi and Carenini, Giuseppe and 
          Xu, Jing and Ray, Shayan and Raja, Huzefa and Chan, Aaron and 
          Carbone, Francesco and Fei, Esther Xu and Du, Gaoyuan and 
          Akhtar, Zuhaib and Grover, Prince and Bhaduri, Sreyoshi and 
          Chen, Weian and Zhang, Wei and Xiong, Ming},
  booktitle={KDD},
  year={2026}
}
```

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- 🐛 [Report bugs](https://github.com/amazon-science/SOP-Bench/issues)
- 💡 [Request features](https://github.com/amazon-science/SOP-Bench/issues)  
- 📖 [Improve docs](https://github.com/amazon-science/SOP-Bench/pulls)
- 🔬 [Add benchmarks](docs/ADDING_BENCHMARKS.md)

---

## License

CC-BY-NC-4.0 — See [LICENSE](LICENSE)

---

## Links

- 📄 **Paper**: Coming soon
- 📧 **Contact**: Open an issue on [GitHub](https://github.com/amazon-science/sop-bench/issues)

---

<p align="center">
  <i>Built by the Applied AI team at Amazon</i>
</p>

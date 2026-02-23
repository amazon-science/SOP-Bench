# Amazon SOP-Bench Architecture

## Overview

Amazon SOP-Bench is a comprehensive benchmark for evaluating LLM agents on Standard Operating Procedures (SOPs). The system consists of three main components that work together to enable SOP generation, agent execution, and performance evaluation.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Amazon SOP-Bench                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Generation  │  │  Execution   │  │  Evaluation  │      │
│  │  (Optional)  │  │  (Core)      │  │  (Core)      │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│         ▼                  ▼                  ▼               │
│  ┌──────────────────────────────────────────────────┐       │
│  │              Benchmarks (Data Layer)              │       │
│  │  • 10 Industrial SOPs                             │       │
│  │  • Test datasets with ground truth                │       │
│  │  • Executable tools with mock data                │       │
│  └──────────────────────────────────────────────────┘       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Benchmarks Module (`benchmarks/`)

**Purpose**: Manage benchmark data and provide access to SOPs, tools, and test cases.

**Key Components**:
- `BenchmarkRegistry`: Discovers and catalogs available benchmarks
- `BenchmarkLoader`: Loads SOP text, tools, and test data
- `Benchmark`: Data class representing a complete benchmark

**Data Structure**:
```
benchmarks/data/
├── content_flagging/
│   ├── sop.txt              # Natural language SOP instructions
│   ├── tools.py             # Python tool implementations
│   ├── toolspecs.json       # Tool specifications for agents
│   ├── test_set.csv         # Test cases with inputs/outputs
│   └── metadata.json        # Benchmark metadata
├── customer_service/
└── ...
```

**Benchmark Metadata**:
```json
{
  "name": "content_flagging",
  "domain": "content_moderation",
  "description": "Content moderation workflow...",
  "num_tasks": 226,
  "num_tools": 4,
  "complexity_score": 9.0,
  "human_complexity": 7.67
}
```

### 2. Agents Module (`agents/`)

**Purpose**: Provide agent implementations that execute SOPs using LLMs and tools.

**Key Components**:
- `BaseAgent`: Abstract base class defining the agent interface
- `FunctionCallingAgent`: Uses LLM native function calling
- `ReActAgent`: Uses ReAct (Reasoning + Acting) prompting pattern via LangChain AgentExecutor
- `ReActAgent`: LangChain-based ReAct agent with stop-sequence handling

**Agent Interface**:
```python
class BaseAgent(ABC):
    """Base class for all agents."""
    
    @abstractmethod
    def execute(
        self, 
        sop: str, 
        task: Dict[str, Any], 
        tools: List[Tool]
    ) -> AgentResult:
        """
        Execute a task given SOP instructions and available tools.
        
        Args:
            sop: Natural language SOP text
            task: Task inputs (e.g., {"user_id": "123", "content_id": "456"})
            tools: List of available tools with specifications
            
        Returns:
            AgentResult with output, tool calls, and execution trace
        """
        pass
```

**Agent Workflow**:
1. Read and parse the SOP instructions
2. Analyze the task inputs
3. Plan which tools to call and in what order
4. Execute tools via ToolManager
5. Synthesize final output
6. Return result with execution trace

### 3. Tools Module (`tools/`)

**Purpose**: Manage tool execution with mock data for reproducible evaluation.

**Key Components**:
- `BaseTool`: Abstract base class for tools
- `ToolManager`: Loads and manages tools for a benchmark
- `ToolExecutor`: Executes tools with pre-computed mock responses

**Tool Interface**:
```python
class BaseTool(ABC):
    """Base class for all tools."""
    
    name: str
    description: str
    parameters: Dict[str, Any]
    
    @abstractmethod
    def execute(self, **params) -> Any:
        """Execute tool with given parameters."""
        pass
```

**Mock Data Execution**:
Tools don't call live APIs. Instead, they:
1. Look up inputs in pre-computed CSV dataset
2. Return corresponding outputs
3. Ensure reproducibility across runs

**Example**:
```python
# Tool implementation
def calculateBotProbabilityIndex(self, userid, is_possible_bot, ...):
    # Load dataset
    df = pd.read_csv(self.dataset_path)
    
    # Find matching row
    row = df[(df['userid'] == userid) & ...].iloc[0]
    
    # Return pre-computed result
    return row['bot_probability_index']
```

### 4. Evaluation Module (`evaluation/`)

**Purpose**: Measure agent performance and generate comprehensive reports.

**Key Components**:
- `Evaluator`: Orchestrates evaluation runs
- `MetricsCalculator`: Computes performance metrics
- `ResultReporter`: Formats and saves results

**Evaluation Workflow**:
```
1. Load benchmark (SOP + tools + test cases)
2. Initialize agent
3. For each test case:
   a. Agent executes task
   b. Compare output to ground truth
   c. Track tool calls and errors
4. Calculate aggregate metrics
5. Generate report
```

**Metrics**:
- **Task Success Rate (TSR)**: `correct_tasks / total_tasks`
- **Execution Completion Rate (ECR)**: `completed_tasks / total_tasks`
- **Conditional TSR (C-TSR)**: `correct_tasks / completed_tasks`
- **Tool Accuracy**: Percentage of correct tool calls
- **Error Distribution**: Categorization of failure modes

### 5. Generation Module (`generation/`) - Optional

**Purpose**: Generate new synthetic SOPs and benchmarks.

**Key Components**:
- `SOPGenerator`: Orchestrates the 6-step generation pipeline
- `PromptManager`: Manages prompt templates
- `LLMClient`: Interfaces with AWS Bedrock

**Generation Pipeline**:
```
1. Dataset Schema Generation
   ↓
2. SOP Document Generation
   ↓
3. Dataset Generation
   ↓
4. API Specification Generation
   ↓
5. Tool Code Generation
   ↓
6. Complexity Introduction
```

Each step uses LLM prompting with human-in-the-loop validation.

### 6. CLI Module (`cli/`)

**Purpose**: Provide command-line interface for all operations.

**Commands**:
- `sop-bench list`: List available benchmarks
- `sop-bench evaluate`: Run evaluation
- `sop-bench results`: Display results
- `sop-bench validate`: Validate benchmark structure

## Data Flow

### Evaluation Flow (Primary Use Case)

```
┌─────────────┐
│   Scientist │
│   runs CLI  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  sop-bench evaluate                     │
│    --benchmark content_flagging         │
│    --agent react                        │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Evaluator                              │
│  1. Load benchmark from registry        │
│  2. Initialize ReActAgent                    │
│  3. Load tools via ToolManager          │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  For each test case (226 tasks):        │
│                                          │
│  ┌────────────────────────────────┐    │
│  │ Agent.execute(sop, task, tools)│    │
│  │   ↓                             │    │
│  │ Agent reads SOP                 │    │
│  │   ↓                             │    │
│  │ Agent plans tool calls          │    │
│  │   ↓                             │    │
│  │ ToolManager.execute_tool()      │    │
│  │   ↓                             │    │
│  │ Agent synthesizes output        │    │
│  └────────────────────────────────┘    │
│                                          │
│  Compare output to ground truth         │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  MetricsCalculator                      │
│  • Calculate TSR, ECR, C-TSR            │
│  • Analyze tool accuracy                │
│  • Categorize errors                    │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  ResultReporter                         │
│  • Format results (JSON/CSV)            │
│  • Generate summary report              │
│  • Save execution traces                │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  results.json                           │
│  {                                       │
│    "benchmark": "content_flagging",     │
│    "agent": "react",                    │
│    "task_success_rate": 0.48,           │
│    "execution_completion_rate": 0.83,   │
│    ...                                   │
│  }                                       │
└─────────────────────────────────────────┘
```

## Design Principles

### 1. Separation of Concerns
Each module has a single, well-defined responsibility:
- **Benchmarks**: Data management
- **Agents**: Task execution
- **Tools**: Tool orchestration
- **Evaluation**: Performance measurement

### 2. Abstraction Through Base Classes
- `BaseAgent`: All agents implement the same interface
- `BaseTool`: All tools follow the same pattern
- Enables easy extension by scientists

### 3. Reproducibility
- Tools use pre-computed mock data (no live API calls)
- Deterministic execution (same inputs → same outputs)
- Execution traces saved for debugging

### 4. Extensibility
Scientists can extend the system by:
- Adding new agents (inherit from `BaseAgent`)
- Adding new benchmarks (follow data structure)
- Adding new metrics (extend `MetricsCalculator`)

### 5. Configuration Over Code
- Environment variables for AWS credentials
- Config file for model parameters
- No hardcoded values

## Technology Stack

### Core Dependencies
- **Python 3.9+**: Core language
- **Boto3**: AWS Bedrock integration
- **Pandas**: Data manipulation and CSV handling
- **Click**: CLI framework
- **Rich**: Pretty terminal output
- **python-dotenv**: Environment variable management

### Development Dependencies
- **pytest**: Testing framework
- **black**: Code formatting
- **mypy**: Type checking
- **ruff**: Fast linting

### Optional Dependencies
- **langchain**: For generation features
- **jinja2**: Template rendering

## File Organization

```
amazon_sop_bench/
├── config.py              # Configuration management
├── benchmarks/            # Benchmark data and loading
│   ├── loader.py
│   ├── registry.py
│   └── data/              # Actual benchmark files
├── agents/                # Agent implementations
│   ├── base.py
│   ├── function_calling.py
│   └── react.py
├── tools/                 # Tool execution
│   ├── base.py
│   ├── manager.py
│   └── executor.py
├── evaluation/            # Evaluation framework
│   ├── evaluator.py
│   ├── metrics.py
│   └── reporter.py
├── generation/            # SOP generation (optional)
│   ├── generator.py
│   └── prompts.py
├── cli/                   # Command-line interface
│   └── main.py
└── utils/                 # Shared utilities
    ├── logging.py
    └── aws.py
```

## Extension Points

### Adding a New Agent

```python
from amazon_sop_bench.agents import BaseAgent

class MyCustomAgent(BaseAgent):
    """My custom agent implementation."""
    
    def execute(self, sop, task, tools):
        # 1. Parse SOP
        # 2. Plan tool calls
        # 3. Execute tools
        # 4. Return result
        return AgentResult(...)
```

### Adding a New Benchmark

1. Create directory: `benchmarks/data/my_benchmark/`
2. Add required files:
   - `sop.txt`: Natural language SOP
   - `tools.py`: Tool implementations
   - `toolspecs.json`: Tool specifications
   - `test_set.csv`: Test cases
   - `metadata.json`: Benchmark metadata
3. Benchmark automatically discovered by registry

### Adding a New Metric

```python
from amazon_sop_bench.evaluation import MetricsCalculator

class CustomMetrics(MetricsCalculator):
    def calculate_custom_metric(self, results):
        # Your metric logic
        return metric_value
```

## Security Considerations

### AWS Credentials
- Never hardcode credentials in code
- Use environment variables or IAM roles
- Support cross-account access via role assumption

### Data Privacy
- All benchmark data is synthetic
- No real user data or PII
- Safe for public distribution

### Reproducibility
- Mock tools ensure no external API calls
- Deterministic execution
- Version-controlled datasets

## Performance Considerations

### Scalability
- Batch processing for multiple tasks
- Optional parallel execution
- Efficient CSV-based data lookup

### Memory Management
- Lazy loading of benchmarks
- Streaming for large datasets
- Configurable batch sizes

## Future Enhancements

### Planned Features
1. **Multi-modal SOPs**: Support for images and tables
2. **Hierarchical SOPs**: Nested sections with context switching
3. **Real-time Tools**: Optional live API integration
4. **Distributed Evaluation**: Parallel execution across machines
5. **Interactive Mode**: Step-by-step debugging

### Community Contributions
- Open for new benchmarks from any domain
- Encourage new agent architectures
- Welcome metric improvements

## References

- Paper: [arXiv:2506.08119](https://arxiv.org/abs/2506.08119)
- Website: http://sop-bench.s3-website-us-west-2.amazonaws.com/
- GitHub: https://github.com/amazon/sop-bench

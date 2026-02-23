# Adding New Benchmarks

This guide explains how to create custom SOP benchmarks for SOP-Bench.

## Table of Contents

- [Overview](#overview)
- [Directory Structure](#directory-structure)
- [Required Files](#required-files)
- [Step-by-Step Guide](#step-by-step-guide)
- [Complete Example](#complete-example)
- [Testing Your Benchmark](#testing-your-benchmark)
- [Best Practices](#best-practices)

---

## Overview

A benchmark in SOP-Bench consists of:
1. **SOP Document** — Natural language procedure instructions
2. **Tools** — Python functions the agent can call
3. **Tool Specifications** — JSON schemas for the LLM
4. **Test Data** — Tasks with ground truth answers
5. **Metadata** — Configuration for the benchmark

---

## Directory Structure

Create your benchmark in:

```
src/amazon_sop_bench/benchmarks/data/your_benchmark/
├── sop.txt          # Natural language SOP
├── tools.py         # Tool implementations
├── toolspecs.json   # Tool schemas for LLM
├── data.csv         # Test cases with ground truth
└── metadata.json    # Benchmark configuration
```

---

## Required Files

### 1. sop.txt — The Procedure

Write the SOP as natural language instructions. Include:

```
1. Purpose
[What this procedure accomplishes]

2. Scope
[What situations this covers]

3. Definitions
[Key terms and thresholds]

4. Input
[What data the agent receives]

5. Main Procedure
[Step-by-step instructions with decision logic]

6. Output
[Expected output format and possible values]
```

**Tips:**
- Be explicit about decision thresholds
- Include edge cases
- Specify what tools to use and when
- Define all terms that might be ambiguous

### 2. tools.py — Tool Implementations

Create a manager class with mock tool implementations:

```python
"""Tools for your_benchmark."""

class YourBenchmarkManager:
    """Manages tool execution for your benchmark."""
    
    def process_tool_call(self, tool_name: str, parameters: dict) -> dict:
        """Route tool calls to appropriate methods."""
        if tool_name == "tool_one":
            return self.tool_one(**parameters)
        elif tool_name == "tool_two":
            return self.tool_two(**parameters)
        raise ValueError(f"Unknown tool: {tool_name}")
    
    def tool_one(self, param1: str, param2: int) -> dict:
        """Description of what tool_one does.
        
        Args:
            param1: Description of param1
            param2: Description of param2
            
        Returns:
            Dictionary with result data
        """
        # Mock implementation - return realistic data
        return {
            "result": "value",
            "score": 0.85
        }
    
    def tool_two(self, input_id: str) -> dict:
        """Description of what tool_two does."""
        # Your implementation
        return {"status": "success"}
```

**Important:** Tools should be deterministic mock implementations that return consistent results for the same inputs.

### 3. toolspecs.json — Tool Schemas

Define tools in Bedrock's tool specification format:

```json
[
  {
    "toolSpec": {
      "name": "tool_one",
      "description": "Clear description of what this tool does and when to use it",
      "inputSchema": {
        "json": {
          "type": "object",
          "properties": {
            "param1": {
              "type": "string",
              "description": "Description of param1"
            },
            "param2": {
              "type": "integer",
              "description": "Description of param2"
            }
          },
          "required": ["param1", "param2"]
        }
      }
    }
  },
  {
    "toolSpec": {
      "name": "tool_two",
      "description": "Description of tool_two",
      "inputSchema": {
        "json": {
          "type": "object",
          "properties": {
            "input_id": {
              "type": "string",
              "description": "The ID to look up"
            }
          },
          "required": ["input_id"]
        }
      }
    }
  }
]
```

### 4. data.csv — Test Cases

Create test cases with inputs and expected outputs:

```csv
task_id,input_field_1,input_field_2,final_decision
1,value1,100,approve
2,value2,50,reject
3,value3,75,review
```

**Columns:**
- `task_id` — Unique identifier (required)
- Input columns — Data passed to the agent
- Output columns — Ground truth (must match `output_columns` in metadata)

### 5. metadata.json — Configuration

```json
{
  "name": "your_benchmark",
  "description": "Brief description of what this benchmark tests",
  "domain": "Your Domain",
  "complexity": 7,
  "output_columns": ["final_decision"]
}
```

**Fields:**
- `name` — Must match directory name
- `output_columns` — List of CSV columns that are expected outputs
- `complexity` — 1-10 rating (optional)
- `domain` — Category like "Healthcare", "Finance", etc. (optional)

**Multi-field outputs:**
```json
{
  "name": "your_benchmark",
  "output_columns": ["decision", "risk_level", "confidence"]
}
```

---

## Step-by-Step Guide

### Step 1: Create Directory

```bash
mkdir -p src/amazon_sop_bench/benchmarks/data/my_new_sop
cd src/amazon_sop_bench/benchmarks/data/my_new_sop
```

### Step 2: Write the SOP

Create `sop.txt` with clear, step-by-step instructions:

```
1. Purpose
Evaluate loan applications for approval based on credit score and income.

2. Scope
All personal loan applications under $50,000.

3. Definitions
- Credit Score Threshold: 650
- Debt-to-Income Ratio (DTI): Monthly debt / Monthly income
- Maximum DTI: 0.43

4. Input
- applicant_id: Unique applicant identifier
- loan_amount: Requested loan amount

5. Main Procedure
5.1 Retrieve applicant's credit report using get_credit_report tool
5.2 Calculate DTI ratio using get_financial_info tool
5.3 Apply decision logic:
    - If credit_score >= 650 AND dti <= 0.43: APPROVE
    - If credit_score >= 600 AND dti <= 0.35: APPROVE with conditions
    - Otherwise: REJECT

6. Output
Final decision: approve, conditional_approve, or reject
```

### Step 3: Implement Tools

Create `tools.py`:

```python
"""Tools for loan approval benchmark."""

class LoanApprovalManager:
    
    # Mock data for reproducibility
    CREDIT_DATA = {
        "APP001": {"credit_score": 720, "credit_history_years": 8},
        "APP002": {"credit_score": 580, "credit_history_years": 2},
        "APP003": {"credit_score": 640, "credit_history_years": 5},
    }
    
    FINANCIAL_DATA = {
        "APP001": {"monthly_income": 6000, "monthly_debt": 1500},
        "APP002": {"monthly_income": 3500, "monthly_debt": 2000},
        "APP003": {"monthly_income": 5000, "monthly_debt": 1600},
    }
    
    def process_tool_call(self, tool_name: str, parameters: dict) -> dict:
        if tool_name == "get_credit_report":
            return self.get_credit_report(**parameters)
        elif tool_name == "get_financial_info":
            return self.get_financial_info(**parameters)
        raise ValueError(f"Unknown tool: {tool_name}")
    
    def get_credit_report(self, applicant_id: str) -> dict:
        """Retrieve credit report for an applicant."""
        if applicant_id in self.CREDIT_DATA:
            return self.CREDIT_DATA[applicant_id]
        return {"error": "Applicant not found"}
    
    def get_financial_info(self, applicant_id: str) -> dict:
        """Retrieve financial information for an applicant."""
        if applicant_id in self.FINANCIAL_DATA:
            data = self.FINANCIAL_DATA[applicant_id]
            dti = data["monthly_debt"] / data["monthly_income"]
            return {**data, "dti_ratio": round(dti, 2)}
        return {"error": "Applicant not found"}
```

### Step 4: Define Tool Specs

Create `toolspecs.json`:

```json
[
  {
    "toolSpec": {
      "name": "get_credit_report",
      "description": "Retrieve the credit report for a loan applicant, including credit score and history length",
      "inputSchema": {
        "json": {
          "type": "object",
          "properties": {
            "applicant_id": {
              "type": "string",
              "description": "The unique identifier for the loan applicant"
            }
          },
          "required": ["applicant_id"]
        }
      }
    }
  },
  {
    "toolSpec": {
      "name": "get_financial_info",
      "description": "Retrieve financial information including income, debt, and calculated DTI ratio",
      "inputSchema": {
        "json": {
          "type": "object",
          "properties": {
            "applicant_id": {
              "type": "string",
              "description": "The unique identifier for the loan applicant"
            }
          },
          "required": ["applicant_id"]
        }
      }
    }
  }
]
```

### Step 5: Create Test Data

Create `data.csv`:

```csv
task_id,applicant_id,loan_amount,final_decision
1,APP001,25000,approve
2,APP002,15000,reject
3,APP003,30000,conditional_approve
```

### Step 6: Add Metadata

Create `metadata.json`:

```json
{
  "name": "loan_approval",
  "description": "Evaluate loan applications based on credit and financial criteria",
  "domain": "Finance",
  "complexity": 6,
  "output_columns": ["final_decision"]
}
```

---

## Complete Example

Here's a complete, working example you can copy:

```bash
# Create directory
mkdir -p src/amazon_sop_bench/benchmarks/data/document_approval
cd src/amazon_sop_bench/benchmarks/data/document_approval
```

**sop.txt:**
```
1. Purpose
Evaluate documents for approval based on completeness and risk assessment.

2. Scope
All document approval requests in the system.

3. Definitions
- Completeness Score: (filled_fields / required_fields) * 100
- Risk Levels: Low, Medium, High (based on document type)

4. Input
- document_id: Unique document identifier
- document_type: Type of document (contract, report, form)

5. Main Procedure
5.1 Use calculate_completeness tool to get completeness score
5.2 Use assess_risk tool to determine risk level
5.3 Apply decision logic:
    - If completeness >= 90% AND risk = Low: approved
    - If completeness >= 80% AND risk = Medium: approved
    - If completeness >= 95% AND risk = High: approved
    - Otherwise: rejected

6. Output
Final decision: approved or rejected
```

**tools.py:**
```python
"""Tools for document_approval benchmark."""

class DocumentApprovalManager:
    
    DOCUMENTS = {
        "DOC001": {"type": "form", "required": 10, "filled": 9},
        "DOC002": {"type": "contract", "required": 20, "filled": 15},
        "DOC003": {"type": "report", "required": 15, "filled": 13},
    }
    
    RISK_MAP = {
        "contract": "High",
        "report": "Medium",
        "form": "Low"
    }
    
    def process_tool_call(self, tool_name: str, parameters: dict) -> dict:
        if tool_name == "calculate_completeness":
            return self.calculate_completeness(**parameters)
        elif tool_name == "assess_risk":
            return self.assess_risk(**parameters)
        raise ValueError(f"Unknown tool: {tool_name}")
    
    def calculate_completeness(self, document_id: str) -> dict:
        """Calculate document completeness score."""
        if document_id in self.DOCUMENTS:
            doc = self.DOCUMENTS[document_id]
            score = (doc["filled"] / doc["required"]) * 100
            return {"completeness_score": round(score, 1)}
        return {"error": "Document not found"}
    
    def assess_risk(self, document_type: str) -> dict:
        """Assess risk level based on document type."""
        risk = self.RISK_MAP.get(document_type, "Medium")
        return {"risk_level": risk}
```

**toolspecs.json:**
```json
[
  {
    "toolSpec": {
      "name": "calculate_completeness",
      "description": "Calculate the completeness score for a document as a percentage",
      "inputSchema": {
        "json": {
          "type": "object",
          "properties": {
            "document_id": {
              "type": "string",
              "description": "The unique document identifier"
            }
          },
          "required": ["document_id"]
        }
      }
    }
  },
  {
    "toolSpec": {
      "name": "assess_risk",
      "description": "Assess the risk level based on document type",
      "inputSchema": {
        "json": {
          "type": "object",
          "properties": {
            "document_type": {
              "type": "string",
              "description": "Type of document: contract, report, or form"
            }
          },
          "required": ["document_type"]
        }
      }
    }
  }
]
```

**data.csv:**
```csv
task_id,document_id,document_type,final_decision
1,DOC001,form,approved
2,DOC002,contract,rejected
3,DOC003,report,approved
```

**metadata.json:**
```json
{
  "name": "document_approval",
  "description": "Evaluate documents for approval based on completeness and risk",
  "domain": "Operations",
  "complexity": 5,
  "output_columns": ["final_decision"]
}
```

---

## Testing Your Benchmark

### 1. Verify It's Detected

```bash
./sop-bench list
# Should show your new benchmark
```

### 2. Run Quick Test

```bash
./sop-bench evaluate document_approval --agent function_calling --max-tasks 1
```

### 3. Debug with Traces

```bash
./sop-bench evaluate document_approval --agent react --max-tasks 3 --save-traces

# Check traces
cat results/document_approval_react_traces/trace_1.txt
```

### 4. Run Full Evaluation

```bash
./sop-bench evaluate document_approval --agent react
```

---

## Best Practices

### SOP Writing

1. **Be explicit** — Don't assume domain knowledge
2. **Define thresholds** — "High risk" means nothing without numbers
3. **Specify tool usage** — Tell the agent which tools to use when
4. **Cover edge cases** — What happens when data is missing?
5. **Use consistent terminology** — Same terms in SOP and tool descriptions

### Tool Design

1. **Deterministic** — Same inputs = same outputs
2. **Realistic** — Return data that looks like real systems
3. **Error handling** — Return meaningful errors for invalid inputs
4. **Documentation** — Clear docstrings and descriptions

### Test Data

1. **Cover all paths** — Include cases for each decision branch
2. **Edge cases** — Boundary values, missing data
3. **Balanced** — Don't have 90% of one outcome
4. **Realistic** — Use plausible values

### Common Mistakes

❌ **Vague SOP instructions**
```
"Check if the score is good enough"
```

✅ **Specific instructions**
```
"If score >= 80, approve. If score < 80, reject."
```

❌ **Non-deterministic tools**
```python
def get_score(self, id):
    return {"score": random.randint(0, 100)}  # Bad!
```

✅ **Deterministic tools**
```python
def get_score(self, id):
    return self.SCORES.get(id, {"error": "Not found"})  # Good!
```

---

## Next Steps

- **[Getting Started](GETTING_STARTED.md)** — Installation and setup
- **[Agents Guide](AGENTS.md)** — Understanding agent types
- **[Examples](../examples/)** — Code samples

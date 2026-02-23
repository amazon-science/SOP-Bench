---
name: Bug Report
about: Report a bug or unexpected behavior
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description

A clear and concise description of what the bug is.

## Steps to Reproduce

Steps to reproduce the behavior:

1. Run command '...'
2. With parameters '...'
3. See error

## Expected Behavior

A clear description of what you expected to happen.

## Actual Behavior

What actually happened instead.

## Environment

- **OS**: [e.g., Ubuntu 22.04, macOS 14.0, Windows 11]
- **Python version**: [e.g., 3.9.7]
- **SOP-Bench version**: [e.g., 0.1.0]
- **AWS Region**: [e.g., us-west-2]
- **Model**: [e.g., anthropic.claude-3-5-sonnet-20241022-v2:0]

## Error Messages

```
Paste any error messages or stack traces here
```

## Code Sample

```python
# Minimal code to reproduce the issue
from amazon_sop_bench import evaluate

results = evaluate(
    benchmark_name="content_flagging",
    agent_type="function_calling"
)
```

## Additional Context

Add any other context about the problem here:
- Screenshots
- Log files
- Related issues
- Workarounds you've tried

## Possible Solution

If you have suggestions on how to fix the bug, please describe them here.

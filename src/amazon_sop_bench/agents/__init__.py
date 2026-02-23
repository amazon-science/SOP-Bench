# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Agent implementations module.

This module provides base agent abstractions and concrete implementations
for executing SOPs.
"""

from amazon_sop_bench.agents.base import BaseAgent, AgentResult

# Import concrete agents with graceful fallback
try:
    from amazon_sop_bench.agents.function_calling import FunctionCallingAgent
    FUNCTION_CALLING_AVAILABLE = True
except ImportError:
    FunctionCallingAgent = None
    FUNCTION_CALLING_AVAILABLE = False

try:
    from amazon_sop_bench.agents.react import ReActAgent
    REACT_AVAILABLE = True
except ImportError:
    ReActAgent = None
    REACT_AVAILABLE = False

__all__ = [
    "BaseAgent",
    "AgentResult",
]

if FUNCTION_CALLING_AVAILABLE:
    __all__.append("FunctionCallingAgent")

if REACT_AVAILABLE:
    __all__.append("ReActAgent")
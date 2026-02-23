# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Output parser for extracting decisions from agent outputs."""

import re
import json
import ast
from typing import Dict, Any, Optional, List
import pandas as pd

from amazon_sop_bench.utils.logging import get_logger

logger = get_logger(__name__)


class OutputParser:
    """
    Parser for extracting structured decisions from agent outputs.
    
    Handles multiple output formats with automatic fallback:
    - XML format: <decision>value</decision>
    - JSON format: {"decision": "value"}
    - Dict format: {'decision': 'value'}
    - Plain string: "value"
    - Multiple decisions: <decision_1>val1</decision_1><decision_2>val2</decision_2>
    
    Supports both single-field and multi-field decision extraction.
    Based on standardized evaluation logic from SOPBenchmarkGenerator.
    """
    
    def __init__(self):
        """Initialize output parser."""
        self.logger = logger
    
    def parse_decision(
        self, 
        output: str, 
        expected_columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Parse decision from agent output with automatic fallback chain.
        
        Tries parsers in order: XML → JSON → Dict → Tool Results → Plain Text
        
        Args:
            output: Agent output text (may include full reasoning trace)
            expected_columns: List of expected decision column names (optional)
            
        Returns:
            Dictionary with parsed decisions. Format:
            - Single field: {"decision": "value", "format": "xml_single"}
            - Multi field: {"decision": "primary_value", "decisions": {...}, "format": "xml_multi"}
            
        Example:
            >>> parser = OutputParser()
            >>> result = parser.parse_decision("<final_decision>allowed</final_decision>")
            >>> print(result)
            {'decision': 'allowed', 'format': 'xml_single'}
        """
        if not output or pd.isna(output):
            logger.debug("Empty or NaN output, returning unknown")
            return {"decision": "unknown", "format": "empty"}
        
        output_str = str(output).strip()
        
        # PRIORITY 1: Try <final_output> JSON format (matches original eval.ipynb)
        # This is the standard format agents output
        final_output_result = self._parse_final_output_json(output_str, expected_columns)
        if final_output_result:
            return final_output_result
        
        # PRIORITY 2: For multi-field outputs, try tool results extraction
        # (reasoning trace contains both SOP tags and tool results)
        if expected_columns and len(expected_columns) > 1:
            tool_result = self._parse_from_tool_results(output_str, expected_columns)
            if tool_result:
                return tool_result
        
        # PRIORITY 3: Try XML format (for <final_decision> tags)
        xml_result = self._parse_xml_format(output_str, expected_columns)
        if xml_result:
            return xml_result
        
        # Try JSON format
        json_result = self._parse_json_format(output_str)
        if json_result:
            return json_result
        
        # Try Dict format (Python dict in logs)
        dict_result = self._parse_dict_format(output_str)
        if dict_result:
            return dict_result
        
        # Fall back to plain string
        return self._parse_plain_format(output_str)
    
    def _parse_final_output_json(
        self,
        output: str,
        expected_columns: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from <final_output> tags (standard agent output format).
        
        This matches the original eval.ipynb parsing logic:
        Finds: <final_output>{...}</final_output>
        
        Args:
            output: Full output text
            expected_columns: Expected output field names
            
        Returns:
            Parsed decisions dict or None
        """
        try:
            # Find all <final_output> blocks (use last one like original eval)
            pattern = r'<final_output>\s*(\{.*?\})\s*</final_output>'
            matches = re.findall(pattern, output, re.DOTALL | re.IGNORECASE)
            
            if not matches:
                return None
            
            # Use last match (most recent output)
            last_json_str = matches[-1].strip()
            
            # Parse the JSON
            full_json = json.loads(last_json_str)
            
            if not isinstance(full_json, dict):
                return None
            
            logger.debug(f"Parsed JSON from <final_output> with {len(full_json)} fields")

            # Create lowercase key mapping for case-insensitive lookup
            full_json_lower = {k.lower(): v for k, v in full_json.items()}
            
            # If expected_columns specified, extract only those fields
            if expected_columns:
                decisions = {}
                for col in expected_columns:
                    col_lower = col.lower()
                    if col_lower in full_json_lower:
                        # Normalize value to lowercase string
                        decisions[col] = str(full_json_lower[col_lower]).lower()
                
                if decisions:
                    # Single field output
                    if len(decisions) == 1:
                        field_value = list(decisions.values())[0]
                        return {
                            "decision": field_value,
                            "format": "final_output_single"
                        }
                    # Multi-field output
                    else:
                        primary_decision = list(decisions.values())[0]
                        return {
                            "decision": primary_decision,
                            "decisions": decisions,
                            "format": "final_output_multi"
                        }
            else:
                # No expected columns - return all non-ID fields
                decision_fields = {
                    k: str(v).lower() for k, v in full_json.items()
                    if k.lower() not in ['id', 'task_id', 'email_id', 'product_id']
                }
                
                if decision_fields:
                    if len(decision_fields) == 1:
                        return {
                            "decision": list(decision_fields.values())[0],
                            "format": "final_output_single"
                        }
                    else:
                        return {
                            "decision": list(decision_fields.values())[0],
                            "decisions": decision_fields,
                            "format": "final_output_multi"
                        }
                        
        except (json.JSONDecodeError, AttributeError, KeyError) as e:
            logger.debug(f"Failed to parse <final_output> JSON: {e}")
        
        return None
    
    def _parse_xml_format(
        self, 
        output: str, 
        expected_columns: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Parse XML format decisions.
        
        Handles:
        - Single decision: <final_decision>value</final_decision>
        - Multiple decisions: <decision_1>val1</decision_1><decision_2>val2</decision_2>
        - Nested decisions: <final_response><field1>val1</field1><field2>val2</field2></final_response>
        """
        # Try common wrapper tags first
        wrapper_tags = ['final_response', 'final_decision', 'response', 'output']
        
        for wrapper_tag in wrapper_tags:
            wrapper_pattern = f'<{wrapper_tag}>(.*?)</{wrapper_tag}>'
            wrapper_match = re.search(wrapper_pattern, output, re.DOTALL | re.IGNORECASE)
            
            if wrapper_match:
                content = wrapper_match.group(1).strip()
                logger.debug(f"Found {wrapper_tag} wrapper tag")
                
                # Extract all XML tags within the wrapper
                all_tags = re.findall(r'<(\w+)>(.*?)</\1>', content, re.DOTALL | re.IGNORECASE)
                
                # If no nested XML tags, try parsing as Python dict (common in ReAct agent outputs)
                if not all_tags:
                    logger.debug(f"No nested XML tags in {wrapper_tag}, trying Python dict parsing")
                    logger.debug(f"Content to parse (first 500 chars): {content[:500]}")
                    dict_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if dict_match:
                        dict_text = dict_match.group(0)
                        # Handle escaped newlines/tabs from JSON-encoded strings
                        dict_text = dict_text.replace('\\n', '\n').replace('\\t', '\t')
                        logger.debug(f"Found dict pattern (unescaped): {dict_text[:200]}")
                        try:
                            parsed_dict = ast.literal_eval(dict_text)
                            if isinstance(parsed_dict, dict):
                                logger.debug(f"Parsed Python dict from {wrapper_tag} content")
                                
                                # Filter out ID fields
                                decisions = {
                                    k.lower(): str(v).lower() for k, v in parsed_dict.items()
                                    if k.lower() not in ['id', 'task_id', 'email_id', 'product_id', 'aircraft_id']
                                }
                                
                                if decisions:
                                    if len(decisions) == 1:
                                        return {
                                            "decision": list(decisions.values())[0],
                                            "format": "xml_dict_single"
                                        }
                                    else:
                                        primary_decision = self._select_primary_decision(decisions, expected_columns)
                                        return {
                                            "decision": primary_decision,
                                            "decisions": decisions,
                                            "format": "xml_dict_multi"
                                        }
                        except (ValueError, SyntaxError) as e:
                            logger.debug(f"Failed to parse Python dict from {wrapper_tag}: {e}")
                
                if all_tags:
                    decisions = {}
                    for tag_name, tag_value in all_tags:
                        # Skip common non-decision tags
                        if tag_name.lower() not in ['id', 'task_id', 'email_id', 'product_id']:
                            decisions[tag_name.lower()] = tag_value.strip().lower()
                    
                    if decisions:
                        # If multiple decision fields found
                        if len(decisions) > 1:
                            logger.debug(f"Found {len(decisions)} decision fields in XML")
                            # Prioritize expected columns if provided
                            primary_decision = self._select_primary_decision(decisions, expected_columns)
                            return {
                                "decision": primary_decision,
                                "decisions": decisions,
                                "format": "xml_multi"
                            }
                        # Single decision field
                        else:
                            field_name = list(decisions.keys())[0]
                            field_value = decisions[field_name]
                            return {
                                "decision": field_value,
                                "format": "xml_single"
                            }
        
        # Fallback: Look for any XML tags (no wrapper)
        all_tags = re.findall(r'<(\w+)>(.*?)</\1>', output, re.DOTALL | re.IGNORECASE)
        if all_tags:
            decisions = {}
            for tag_name, tag_value in all_tags:
                if tag_name.lower() not in ['id', 'task_id', 'email_id', 'product_id']:
                    decisions[tag_name.lower()] = tag_value.strip().lower()
            
            if decisions:
                if len(decisions) > 1:
                    # Use the same prioritization logic as the wrapper tag parsing
                    primary_decision = self._select_primary_decision(decisions, expected_columns)
                    return {
                        "decision": primary_decision,
                        "decisions": decisions,
                        "format": "xml_multi"
                    }
                else:
                    return {
                        "decision": list(decisions.values())[0],
                        "format": "xml_single"
                    }
        
        return None
    
    def _parse_json_format(self, output: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON format decisions.
        
        Handles: {"decision": "value"} or {"decision_1": "val1", "decision_2": "val2"}
        """
        try:
            # Try to find JSON object in output
            # Look for content between { and }
            json_match = re.search(r'\{[^{}]*\}', output)
            if json_match:
                json_str = json_match.group(0)
                # Handle Python dict format (single quotes)
                json_str = json_str.replace("'", '"')
                
                decisions = json.loads(json_str)
                logger.debug(f"Parsed JSON decisions: {decisions}")
                
                # Filter out ID fields
                decision_fields = {
                    k: v for k, v in decisions.items()
                    if k.lower() not in ['id', 'task_id', 'email_id', 'product_id']
                }
                
                if not decision_fields:
                    return None
                
                # If single decision field
                if len(decision_fields) == 1:
                    key = list(decision_fields.keys())[0]
                    return {
                        "decision": str(decision_fields[key]).lower(),
                        "format": "json_single"
                    }
                # Multiple decision fields
                else:
                    primary_decision = str(list(decision_fields.values())[0]).lower()
                    return {
                        "decision": primary_decision,
                        "decisions": {k: str(v).lower() for k, v in decision_fields.items()},
                        "format": "json_multi"
                    }
        except (json.JSONDecodeError, AttributeError) as e:
            logger.debug(f"JSON parsing failed: {e}")
        
        return None
    
    def _parse_dict_format(self, output: str) -> Optional[Dict[str, Any]]:
        """
        Parse Python dictionary format from logs.
        
        Handles: {'decision': 'value'} or {'field1': 'val1', 'field2': 'val2'}
        Common in log files where Python dicts are printed.
        """
        try:
            # Look for dictionary pattern after common markers
            markers = ['======= Final Response =====', 'Final Response:', 'Output:']
            content = output
            
            for marker in markers:
                if marker in output:
                    marker_pos = output.find(marker)
                    content = output[marker_pos + len(marker):]
                    break
            
            # Extract dictionary using regex (greedy to get full dict)
            dict_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not dict_match:
                return None
            
            dict_text = dict_match.group(0)
            
            # Parse using ast.literal_eval (safer than eval)
            parsed_dict = ast.literal_eval(dict_text)
            
            if not isinstance(parsed_dict, dict):
                return None
            
            logger.debug(f"Parsed dict format: {parsed_dict}")
            
            # Filter out ID fields
            decision_fields = {
                k: v for k, v in parsed_dict.items()
                if k.lower() not in ['id', 'task_id', 'email_id', 'product_id']
            }
            
            if not decision_fields:
                return None
            
            # Single decision field
            if len(decision_fields) == 1:
                key = list(decision_fields.keys())[0]
                return {
                    "decision": str(decision_fields[key]).lower(),
                    "format": "dict_single"
                }
            # Multiple decision fields
            else:
                primary_decision = str(list(decision_fields.values())[0]).lower()
                return {
                    "decision": primary_decision,
                    "decisions": {k: str(v).lower() for k, v in decision_fields.items()},
                    "format": "dict_multi"
                }
                
        except (ValueError, SyntaxError, AttributeError) as e:
            logger.debug(f"Dict parsing failed: {e}")
            return None
    
    def _parse_plain_format(self, output: str) -> Dict[str, Any]:
        """
        Parse plain string format.
        
        Extracts the decision as-is, handling common patterns.
        """
        # Clean up the output
        decision = output.lower().strip()
        
        # Remove common prefixes
        prefixes = ["final answer:", "decision:", "result:", "output:"]
        for prefix in prefixes:
            if decision.startswith(prefix):
                decision = decision[len(prefix):].strip()
        
        # If still too long, might be full explanation - mark as unknown
        if len(decision) > 100:
            logger.debug("Output too long for plain format, marking as unknown")
            decision = "unknown"
        
        return {
            "decision": decision,
            "format": "plain"
        }
    
    def compare_decisions(
        self,
        predicted: Any,
        expected: Any,
        fuzzy_match: bool = True
    ) -> bool:
        """
        Compare predicted and expected decisions.
        Handles both single-value and multi-field (dict) comparisons.
        For multi-field, ALL fields must match for True result.
        
        Args:
            predicted: Predicted decision (string or dict)
            expected: Expected decision (string or dict)
            fuzzy_match: Whether to allow fuzzy matching
            
        Returns:
            True if decisions match, False otherwise
        """
        # Handle dict-based multi-field outputs
        if isinstance(expected, dict) or isinstance(predicted, dict):
            return self._compare_multi_field(predicted, expected, fuzzy_match)
        
        # Single-value comparison
        return self._compare_single_value(predicted, expected, fuzzy_match)
    
    def _compare_single_value(
        self,
        predicted: Any,
        expected: Any,
        fuzzy_match: bool = True
    ) -> bool:
        """
        Compare single predicted and expected values.
        
        Args:
            predicted: Predicted value
            expected: Expected value
            fuzzy_match: Whether to allow fuzzy matching
            
        Returns:
            True if values match, False otherwise
        """
        # Define null-like values that should all be considered equivalent
        null_values = {'none', 'null', 'na', 'n/a', 'nan', 'unknown', ''}
        
        # Normalize predicted to string for null checking
        pred_str_lower = str(predicted).lower().strip() if predicted is not None else ''
        exp_str_lower = str(expected).lower().strip() if expected is not None else ''
        
        # Handle NaN/None/null-like cases - all should match each other
        pred_is_null = pd.isna(predicted) or pred_str_lower in null_values
        exp_is_null = pd.isna(expected) or exp_str_lower in null_values
        
        if pred_is_null and exp_is_null:
            return True
        if pred_is_null or exp_is_null:
            # One is null, other is not - no match
            return False
        
        # Convert to strings and lowercase
        pred_str = str(predicted).lower().strip()
        exp_str = str(expected).lower().strip()
        
        # Exact match
        if pred_str == exp_str:
            return True
        
        # Fuzzy matching
        if fuzzy_match:
            # Remove common variations
            pred_clean = pred_str.replace("_", " ").replace("-", " ")
            exp_clean = exp_str.replace("_", " ").replace("-", " ")
            
            if pred_clean == exp_clean:
                return True
            
            # Check if one contains the other
            if pred_clean in exp_clean or exp_clean in pred_clean:
                return True
        
        return False
    
    def _compare_multi_field(
        self,
        predicted: Any,
        expected: Dict[str, Any],
        fuzzy_match: bool = True
    ) -> bool:
        """
        Compare multi-field outputs. ALL fields must match for True result.
        
        Args:
            predicted: Predicted outputs (dict or parsed result dict)
            expected: Expected outputs as dict
            fuzzy_match: Whether to allow fuzzy matching per field
            
        Returns:
            True if ALL fields match, False otherwise
        """
        # Handle case where predicted is not a dict
        if not isinstance(predicted, dict):
            logger.warning(f"Expected dict for multi-field comparison, got {type(predicted)}")
            return False
        
        # Ensure expected is a dict
        if not isinstance(expected, dict):
            logger.warning(f"Expected dict for multi-field expected output, got {type(expected)}")
            return False
        
        # Get the actual decision values from parsed output
        # Parsed output may have structure: {"decision": "...", "decisions": {...}}
        predicted_values = predicted.get("decisions", predicted)
        
        # If predicted_values is still not dict, try using it as single value
        if not isinstance(predicted_values, dict):
            # Single value predicted, but expected is dict - check if it matches any field
            if len(expected) == 1:
                expected_value = list(expected.values())[0]
                return self._compare_single_value(predicted_values, expected_value, fuzzy_match)
            else:
                logger.warning("Multi-field expected but single value predicted")
                return False
        
        # Compare each field - ALL must match
        all_match = True
        for field_name, expected_value in expected.items():
            # Find matching field in predicted (case-insensitive)
            predicted_value = None
            for pred_key, pred_val in predicted_values.items():
                if pred_key.lower() == field_name.lower():
                    predicted_value = pred_val
                    break
            
            # If field not found in predicted, mark as mismatch
            if predicted_value is None:
                logger.debug(f"Field '{field_name}' not found in predicted output")
                all_match = False
                continue
            
            # Compare this field
            field_match = self._compare_single_value(predicted_value, expected_value, fuzzy_match)
            if not field_match:
                logger.debug(f"Field '{field_name}' mismatch: predicted='{predicted_value}', expected='{expected_value}'")
                all_match = False
        
        return all_match
    
    def _parse_from_tool_results(
        self,
        output: str,
        expected_columns: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract multi-field outputs from tool results in reasoning trace.
        
        For multi-field SOPs, tool calls return individual fields which
        we need to aggregate into a single decision dict.
        
        Args:
            output: Full output including reasoning trace
            expected_columns: List of expected output field names
            
        Returns:
            Parsed decisions dict or None
        """
        try:
            # Try to parse as JSON array (reasoning trace format)
            if output.startswith('['):
                trace = json.loads(output)
                
                # Extract tool results from trace
                decisions = {}
                for message in trace:
                    if message.get("role") == "user":
                        content = message.get("content", [])
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "tool_result":
                                tool_content = item.get("content", "")
                                try:
                                    # Parse tool result JSON
                                    result_data = json.loads(tool_content)
                                    if isinstance(result_data, dict):
                                        # Add any fields that match expected columns
                                        for key, value in result_data.items():
                                            if key in expected_columns:
                                                decisions[key] = str(value).lower()
                                except json.JSONDecodeError:
                                    continue
                
                # Check if we got all expected fields
                if decisions and len(decisions) >= len(expected_columns) / 2:
                    logger.debug(f"Extracted {len(decisions)} fields from tool results")
                    primary_decision = list(decisions.values())[0] if decisions else "unknown"
                    return {
                        "decision": primary_decision,
                        "decisions": decisions,
                        "format": "tool_results"
                    }
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _select_primary_decision(
        self,
        decisions: Dict[str, str],
        expected_columns: Optional[List[str]] = None
    ) -> str:
        """
        Select the primary decision from multiple parsed decisions.
        
        Generic method that prioritizes expected output columns if provided,
        otherwise uses first decision. Works for any SOP.
        
        Args:
            decisions: Dictionary of parsed decisions from XML tags
            expected_columns: List of expected output column names from benchmark metadata
            
        Returns:
            Primary decision value as string
        """
        if not decisions:
            return "unknown"
        
        # If expected columns provided, prioritize them
        if expected_columns:
            for expected_col in expected_columns:
                expected_col_lower = expected_col.lower()
                if expected_col_lower in decisions:
                    logger.debug(f"Selected primary decision from expected column: {expected_col_lower}")
                    return decisions[expected_col_lower]
        
        # Fallback to first decision (preserves existing behavior)
        primary_decision = list(decisions.values())[0]
        logger.debug(f"Selected first decision as primary: {primary_decision}")
        return primary_decision
    
    def extract_reason(self, output: str) -> Optional[str]:
        """
        Extract decision reason from output.
        
        Args:
            output: Agent output text
            
        Returns:
            Extracted reason or None
        """
        # Look for <final_decision_reason> tag
        reason_pattern = r'<final_decision_reason>(.*?)</final_decision_reason>'
        reason_match = re.search(reason_pattern, output, re.DOTALL | re.IGNORECASE)
        
        if reason_match:
            reason = reason_match.group(1).strip()
            logger.debug(f"Found reason: {reason[:50]}...")
            return reason
        
        # Look for common reason indicators
        reason_indicators = ["reason:", "because:", "explanation:"]
        for indicator in reason_indicators:
            if indicator in output.lower():
                # Extract text after indicator
                idx = output.lower().index(indicator)
                reason = output[idx + len(indicator):].strip()
                # Take first sentence or paragraph
                reason = reason.split('\n')[0][:200]
                return reason
        
        return None

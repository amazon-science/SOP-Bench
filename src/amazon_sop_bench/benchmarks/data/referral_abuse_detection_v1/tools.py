# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

import os, json
import pandas as pd
from typing import Dict, Any

class ReferralAbuseDetectionManager:
    """Manager class for referral abuse detection tools."""

    DATASET_CSV_FILE = "test_set_with_outputs.csv"
    TOOLSPEC_JSON_FILE = "toolspecs.json"

    def __init__(self):
        """Initialize paths to the dataset and toolspec files."""
        self.dataset_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), self.DATASET_CSV_FILE
        )
        self.toolspec_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), self.TOOLSPEC_JSON_FILE
        )
        with open(self.toolspec_file_path, "r") as fr:
            toolspec_json = json.load(fr)
        self.tool_config = {"tools": toolspec_json}

    def process_tool_call(self, tool_name: str, parameters: dict):
        """Process tool calls by routing to appropriate methods."""
        if tool_name == "investigate_account":
            return self.investigate_account(**parameters)
        elif tool_name == "analyze_traffic_patterns":
            return self.analyze_traffic_patterns(**parameters)
        elif tool_name == "determine_enforcement_action":
            return self.determine_enforcement_action(**parameters)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def investigate_account(self, account_id: str) -> Dict[str, Any]:
        """Perform comprehensive account investigation."""
        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[df["account_id"] == account_id]

        if matched_rows.empty:
            raise ValueError(f"Account not found: {account_id}")

        account = matched_rows.iloc[0]
        return {
            "account_id": account_id,
            "address_validity": bool(account['address_validity']),
            "email_pattern_suspicious": bool(account['email_pattern_suspicious']),
            "website_verified": bool(account['website_verified']),
            "business_description": account['business_description'],
            "account_status": account['account_status'],
            "connected_accounts": int(account['connected_accounts']),
            "login_geographic_consistency": bool(account['login_geographic_consistency'])
        }

    def analyze_traffic_patterns(self, account_id: str) -> Dict[str, Any]:
        """Analyze traffic patterns for fraud detection."""
        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[df["account_id"] == account_id]

        if matched_rows.empty:
            raise ValueError(f"Account not found: {account_id}")

        account = matched_rows.iloc[0]
        return {
            "account_id": account_id,
            "revenue_amount": float(account['revenue_amount']),
            "click_through_rate": float(account['click_through_rate']),
            "page_views": int(account['page_views']),
            "device_distribution": account['device_distribution'],
            "referral_source_quality": account['referral_source_quality'],
            "payment_method_shared": bool(account['payment_method_shared']),
            "order_patterns_suspicious": bool(account['order_patterns_suspicious'])
        }

    def determine_enforcement_action(self, account_id: str) -> Dict[str, Any]:
        """Get enforcement action guidelines."""
        return {
            "account_id": account_id,
            "enforcement_guidelines": {
                "Abusive Account Creation": "Account Closure",
                "Misleading Ad Copy": "Account Closure",
                "Personal Orders (Related)": "No Action",
                "No Violation": "No Action"
            },
            "note": "Apply the enforcement action corresponding to the violation type determined from scoring analysis"
        }

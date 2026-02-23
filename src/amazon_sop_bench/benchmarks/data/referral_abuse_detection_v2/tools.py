# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Tools for referral_abuse_detection_v2 benchmark - Enhanced version with temporal patterns and risk severity."""

import pandas as pd
from pathlib import Path

# Use test set without outputs to prevent data leakage
DATASET_CSV_FILE = "test_set_with_outputs.csv"
TOOLSPEC_JSON_FILE = "toolspecs.json"


class ReferralAbuseDetectionV2Manager:
    """Manager for referral abuse detection tools with enhanced complexity."""
    
    def __init__(self):
        """Initialize the manager and load dataset."""
        current_dir = Path(__file__).parent
        csv_path = current_dir / DATASET_CSV_FILE
        self.df = pd.read_csv(csv_path)
        
    def process_tool_call(self, tool_name: str, parameters: dict):
        """Route tool calls to appropriate methods."""
        if tool_name == "investigate_account":
            return self.investigate_account(**parameters)
        elif tool_name == "analyze_traffic_patterns":
            return self.analyze_traffic_patterns(**parameters)
        elif tool_name == "analyze_temporal_patterns":
            return self.analyze_temporal_patterns(**parameters)
        elif tool_name == "get_violation_history":
            return self.get_violation_history(**parameters)
        elif tool_name == "get_financial_impact":
            return self.get_financial_impact(**parameters)
        elif tool_name == "determine_enforcement_action":
            return self.determine_enforcement_action(**parameters)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    def investigate_account(self, account_id: str) -> dict:
        """Get account investigation data."""
        row = self.df[self.df['account_id'] == account_id]
        if row.empty:
            raise ValueError(f"Account {account_id} not found")
        
        row = row.iloc[0]
        return {
            "account_id": account_id,
            "user_email": row['user_email'],
            "registration_timestamp": row['registration_timestamp'],
            "address_validity": bool(row['address_validity']),
            "email_pattern_suspicious": bool(row['email_pattern_suspicious']),
            "website_verified": bool(row['website_verified']),
            "business_description": row['business_description'],
            "account_status": row['account_status'],
            "connected_accounts": int(row['connected_accounts']),
            "login_geographic_consistency": bool(row['login_geographic_consistency']),
            "account_age_days": int(row['account_age_days'])
        }
    
    def analyze_traffic_patterns(self, account_id: str) -> dict:
        """Get traffic and transaction analysis data."""
        row = self.df[self.df['account_id'] == account_id]
        if row.empty:
            raise ValueError(f"Account {account_id} not found")
        
        row = row.iloc[0]
        return {
            "account_id": account_id,
            "revenue_amount": float(row['revenue_amount']),
            "click_through_rate": float(row['click_through_rate']),
            "page_views": int(row['page_views']),
            "device_distribution": row['device_distribution'],
            "referral_source_quality": row['referral_source_quality'],
            "payment_method_shared": bool(row['payment_method_shared']),
            "order_patterns_suspicious": bool(row['order_patterns_suspicious'])
        }
    
    def analyze_temporal_patterns(self, account_id: str) -> dict:
        """Get temporal activity pattern data."""
        row = self.df[self.df['account_id'] == account_id]
        if row.empty:
            raise ValueError(f"Account {account_id} not found")
        
        row = row.iloc[0]
        return {
            "account_id": account_id,
            "registration_burst_detected": bool(row['registration_burst_detected']),
            "off_hours_activity_percentage": float(row['off_hours_activity_percentage']),
            "activity_spike_detected": bool(row['activity_spike_detected'])
        }
    
    def get_violation_history(self, account_id: str) -> dict:
        """Get violation history and rehabilitation status."""
        row = self.df[self.df['account_id'] == account_id]
        if row.empty:
            raise ValueError(f"Account {account_id} not found")
        
        row = row.iloc[0]
        return {
            "account_id": account_id,
            "previous_violations_count": int(row['previous_violations_count']),
            "last_violation_date": row['last_violation_date'] if pd.notna(row['last_violation_date']) else None,
            "warning_issued": bool(row['warning_issued']),
            "account_rehabilitation_status": row['account_rehabilitation_status']
        }
    
    def get_financial_impact(self, account_id: str) -> dict:
        """Get financial impact metrics."""
        row = self.df[self.df['account_id'] == account_id]
        if row.empty:
            raise ValueError(f"Account {account_id} not found")
        
        row = row.iloc[0]
        return {
            "account_id": account_id,
            "total_lifetime_revenue": float(row['total_lifetime_revenue']),
            "refund_rate_percentage": float(row['refund_rate_percentage']),
            "customer_complaint_count": int(row['customer_complaint_count'])
        }
    
    def determine_enforcement_action(self, account_id: str) -> dict:
        """Return enforcement action guidelines (not the actual decision)."""
        # This tool provides guidelines, not the actual decision
        # The agent must calculate scores and determine the action
        return {
            "message": "Enforcement action determined successfully",
            "note": "Agent must calculate violation scores and risk severity to determine final action"
        }

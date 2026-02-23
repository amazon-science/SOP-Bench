# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

import os, json, re
import pandas as pd
from typing import Dict, Any, List, Union
from datetime import datetime
from dateutil import parser

class TrafficSpoofingDetectionManager:
    """
    A manager class to process various stages of traffic spoofing detection by matching inputs
    to a reference dataset and returning the appropriate outputs.
    """

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
        if tool_name == "InvestigateViolations":
            return self.InvestigateViolations(**parameters)
        elif tool_name == "AnalyzeTrafficPatterns":
            return self.AnalyzeTrafficPatterns(**parameters)
        elif tool_name == "ValidateReferralSources":
            return self.ValidateReferralSources(**parameters)
        elif tool_name == "CalculateRiskScore":
            return self.CalculateRiskScore(**parameters)
        elif tool_name == "GenerateEvidenceReport":
            return self.GenerateEvidenceReport(**parameters)
        elif tool_name == "ExecuteEnforcementAction":
            return self.ExecuteEnforcementAction(**parameters)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def InvestigateViolations(self,
        partner_id: str,
        registered_websites: List[str],
        earnings_amount: float
        ) -> str:
        """
        Reviews creator's accounts and websites for violations.
        """
        if not all([partner_id, registered_websites, earnings_amount]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[(df["partner_id"] == partner_id)]

        if matched_rows.empty:
            raise ValueError("No data found for given partner_id.")

        return matched_rows.iloc[0]["investigation_status"]

    def AnalyzeTrafficPatterns(self,
        partner_id: str,
        engagement_score: float,
        conversion_rate: float,
        bounce_rate: float
        ) -> str:
        """
        Analyzes traffic data for suspicious patterns.
        """
        if not all([partner_id, engagement_score is not None, conversion_rate is not None, bounce_rate is not None]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[(df["partner_id"] == partner_id)]

        if matched_rows.empty:
            raise ValueError("No data found for given partner_id.")

        return matched_rows.iloc[0]["traffic_analysis_result"]

    def ValidateReferralSources(self,
        partner_id: str,
        unattributed_clicks: int,
        top_referral_source: str
        ) -> str:
        """
        Checks referral URLs and sources for legitimacy.
        """
        if not all([partner_id, unattributed_clicks is not None, top_referral_source]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[(df["partner_id"] == partner_id)]

        if matched_rows.empty:
            raise ValueError("No data found for given partner_id.")

        return matched_rows.iloc[0]["source_verification_result"]

    def CalculateRiskScore(self,
        partner_id: str,
        violation_type: str,
        engagement_score: float,
        conversion_rate: float
        ) -> str:
        """
        Calculates risk score based on detection signals.
        """
        if not all([partner_id, violation_type, engagement_score is not None, conversion_rate is not None]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[(df["partner_id"] == partner_id)]

        if matched_rows.empty:
            raise ValueError("No data found for given partner_id.")

        return matched_rows.iloc[0]["risk_level"]

    def GenerateEvidenceReport(self,
        partner_id: str,
        violation_type: str,
        evidence_collected: List[str]
        ) -> str:
        """
        Generates comprehensive evidence report.
        """
        if not all([partner_id, violation_type, evidence_collected]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[(df["partner_id"] == partner_id)]

        if matched_rows.empty:
            raise ValueError("No data found for given partner_id.")

        return "SUCCESS"

    def ExecuteEnforcementAction(self,
        partner_id: str,
        risk_level: str,
        violation_type: str
        ) -> str:
        """
        Executes the determined enforcement action.
        """
        if not all([partner_id, risk_level, violation_type]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[(df["partner_id"] == partner_id)]

        if matched_rows.empty:
            raise ValueError("No data found for given partner_id.")

        return "Enforcement action executed successfully"

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Tools for customer_service benchmark."""

import ast
import os
import json
import re
import pandas as pd
from typing import Any, Dict, List, Union


class ServiceAccountManager:

    DATASET_CSV_FILE = "test_set_with_outputs.csv"
    TOOLSPEC_JSON_FILE = "toolspecs.json"

    def __init__(self):
        """
        Initializes the ServiceAccountManager instance.

        This constructor sets up file paths for the dataset CSV file and toolspec JSON file
        relative to the current file location. It also loads the tool specifications into memory
        for later tool execution.

        Parameters:
        -----------
        dataset_file_path : str
            Full path to the customer service dataset CSV file.
        toolspec_file_path : str
            Full path to the customer service toolspec JSON file.
        tool_config : Dict[str, Any]
            Dictionary containing the loaded toolspec configurations.
        """
        self.dataset_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), self.DATASET_CSV_FILE
        )
        print(f"Dataset file path: {self.dataset_file_path}")
        self.toolspec_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), self.TOOLSPEC_JSON_FILE
        )
        print(f"Toolspec file path: {self.toolspec_file_path}")
        with open(self.toolspec_file_path, "r") as fr:
            toolspec_json = json.load(fr)
        self.tool_config = {"tools": toolspec_json}

    def validateAccount(self, account_id: str) -> Dict[str, Union[bool, str]]:
        """
        Validates the format of an account ID.

        Args:
            account_id (str): The account ID to validate

        Returns:
            Dict containing validation result and reason
        """
        if not account_id:
            raise ValueError("Missing required parameter: account_id")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        # Find matching record
        matched_row = df[df["account_id"] == account_id]

        if matched_row.empty:
            return {
                "is account id valid": False,
                "reason": f"Account ID {account_id} not found in records",
            }

        # Validates if the account_id follows the pattern: 3 uppercase letters, a hyphen, and 5 digits
        pattern = r"^[A-Z]{3}-\d{5}$"
        is_account_id_valid = bool(re.match(pattern, account_id))

        return {
            "is account id valid": is_account_id_valid,
            "reason": (
                "The account ID conforms to the organization's standard pattern"
                if is_account_id_valid
                else "Invalid account ID format"
            ),
        }

    def getAuthenticationDetails(
        self, account_id: str, is_account_id_valid: bool
    ) -> Dict[str, Any]:
        """
        Gets authentication details for an account.

        Args:
            account_id (str): The account ID
            is_account_id_valid (bool): Whether the account ID is valid

        Returns:
            Dict containing authentication history
        """
        if not account_id or is_account_id_valid is None:
            raise ValueError("Missing required parameters: account_id or is_account_id_valid")

        if not is_account_id_valid:
            raise ValueError("Invalid account ID provided")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        # Find matching record
        matched_row = df[
            (df["account_id"] == account_id) & (df["is_account_id_valid"] == is_account_id_valid)
        ]

        if matched_row.empty:
            raise ValueError(f"No record found for the provided parameters")

        # Parse authentication history
        auth_history = matched_row.iloc[0]["authentication_history"]
        if isinstance(auth_history, str):
            auth_history = json.loads(auth_history)

        return {"authentication records": auth_history}

    def createSessionAndOpenTicket(
        self, account_id: str, is_account_id_valid: bool, is_authenticated: bool
    ) -> Dict[str, str]:
        """
        Creates a session and opens a ticket.

        Args:
            account_id (str): The account ID
            is_account_id_valid (bool): Whether the account ID is valid
            is_authenticated (bool): Whether the account is authenticated

        Returns:
            Dict containing session token and ticket ID
        """
        if not account_id or is_account_id_valid is None or is_authenticated is None:
            raise ValueError("Missing required parameters")

        if not is_account_id_valid or not is_authenticated:
            raise ValueError("Account validation or authentication failed")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        # Find matching record
        matched_row = df[
            (df["account_id"] == account_id)
            & (df["is_account_id_valid"] == is_account_id_valid)
            & (df["is_authenticated"] == is_authenticated)
        ]

        if matched_row.empty:
            raise ValueError(f"No record found for the provided parameters")

        row = matched_row.iloc[0]
        return {"session token": row["session_token"], "ticket identifer": row["ticket_id"]}

    def checkAccountStatus(self, account_id: str, session_token: str) -> Dict[str, str]:
        """
        Checks account status.

        Args:
            account_id (str): The account ID
            session_token (str): Active session token

        Returns:
            Dict containing account status and reason
        """
        if not account_id or not session_token:
            raise ValueError("Missing required parameters: account_id or session_token")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        # Find matching record
        matched_row = df[(df["account_id"] == account_id) & (df["session_token"] == session_token)]

        if matched_row.empty:
            raise ValueError(f"No record found for the provided parameters")

        row = matched_row.iloc[0]
        return {
            "account status": row["account_status"],
            "reason": (
                row["reason_for_account_status"]
                if not pd.isna(row["reason_for_account_status"])
                else ""
            ),
        }

    def checkPaymentStatus(self, account_id: str, session_token: str) -> Dict[str, str]:
        """
        Checks payment status.

        Args:
            account_id (str): The account ID
            session_token (str): Active session token

        Returns:
            Dict containing payment status
        """
        if not account_id or not session_token:
            raise ValueError("Missing required parameters")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        # Find matching record
        matched_row = df[(df["account_id"] == account_id) & (df["session_token"] == session_token)]

        if matched_row.empty:
            raise ValueError(f"No record found for the provided parameters")

        row = matched_row.iloc[0]
        return {
            "overdue payment status": (
                row["overdue_payment_status"] if not pd.isna(row["overdue_payment_status"]) else ""
            )
        }

    def checkAccountSuspensionStatus(self, account_id: str, session_token: str) -> Dict[str, str]:
        """
        Checks account suspension status.

        Args:
            account_id (str): The account ID
            session_token (str): Active session token

        Returns:
            Dict containing suspension status
        """
        if not account_id or not session_token:
            raise ValueError("Missing required parameters")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        # Find matching record
        matched_row = df[(df["account_id"] == account_id) & (df["session_token"] == session_token)]

        if matched_row.empty:
            raise ValueError(f"No record found for the provided parameters")

        row = matched_row.iloc[0]
        return {
            "account suspension status": (
                row["account_suspension_status"]
                if not pd.isna(row["account_suspension_status"])
                else ""
            )
        }

    def checkServiceAreaOutage(
        self, account_id: str, session_token: str, service_area_code: str
    ) -> Dict[str, Any]:
        """
        Checks service area outages.

        Args:
            account_id (str): The account ID
            session_token (str): Active session token
            service_area_code (str): Service area code

        Returns:
            Dict containing outage information
        """
        if not account_id or not session_token or not service_area_code:
            raise ValueError("Missing required parameters")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        # Find matching record
        matched_row = df[
            (df["account_id"] == account_id)
            & (df["session_token"] == session_token)
            & (df["service_area_code"] == service_area_code)
        ]

        if matched_row.empty:
            raise ValueError(f"No record found for the provided parameters")

        row = matched_row.iloc[0]
        return {
            "outage detected": bool(row["outage_detected"]),  # Convert numpy.bool_ to Python bool
            "outage id": row["outage_id"] if not pd.isna(row["outage_id"]) else "",
            "radius miles": str(row["radius_miles"]) if not pd.isna(row["radius_miles"]) else "",
            "outage impact score": (
                float(row["outage_impact_score"]) if not pd.isna(row["outage_impact_score"]) else ""
            ),
            "expected outage resolution time": (
                row["expected_outage_resolution_time"]
                if not pd.isna(row["expected_outage_resolution_time"])
                else ""
            ),
        }

    def performTechnicalDiagnostics(
        self, account_id: str, session_token: str, service_type: str, subscribed_bandwidth: str
    ) -> Dict[str, Any]:
        """
        Performs technical diagnostics.

        Args:
            account_id (str): The account ID
            session_token (str): Active session token
            service_type (str): Type of service
            subscribed_bandwidth (str): Subscribed bandwidth

        Returns:
            Dict containing diagnostic results
        """
        if not all([account_id, session_token, service_type, subscribed_bandwidth]):
            raise ValueError("Missing required parameters")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        # Find matching record
        matched_row = df[
            (df["account_id"] == account_id)
            & (df["session_token"] == session_token)
            & (df["service_type"] == service_type)
            & (df["subscribed_bandwidth"] == subscribed_bandwidth)
        ]

        if matched_row.empty:
            raise ValueError(f"No record found for the provided parameters")

        row = matched_row.iloc[0]

        # Parse service metrics
        service_metrics = row["service_metrics"]
        if isinstance(service_metrics, str):
            service_metrics = json.loads(service_metrics)

        # Parse root causes
        root_causes = row["root_causes"]
        if isinstance(root_causes, str):
            root_causes = ast.literal_eval(root_causes)

        return {
            "timestamp diagnostics started": row["timestamp_diagnostics_started"],
            "timestamp diagnostics completed": row["timestamp_diagnostics_completed"],
            "service metrics": service_metrics,
            "root causes": root_causes,
        }

    def executeTroubleshooting(
        self, account_id: str, session_token: str, root_causes: List[str]
    ) -> Dict[str, Any]:
        """
        Executes troubleshooting steps.

        Args:
            account_id (str): The account ID
            session_token (str): Active session token
            root_causes (List[str]): List of root causes

        Returns:
            Dict containing troubleshooting results
        """
        if not account_id or not session_token or not root_causes:
            raise ValueError("Missing required parameters")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        # Find matching record
        matched_row = df[(df["account_id"] == account_id) & (df["session_token"] == session_token)]

        if matched_row.empty:
            raise ValueError(f"No record found for the provided parameters")

        row = matched_row.iloc[0]

        expected_root_causes = ast.literal_eval(row["root_causes"])
        if isinstance(expected_root_causes, str):
            expected_root_causes = ast.literal_eval(expected_root_causes)
        if isinstance(root_causes, str):
            root_causes = ast.literal_eval(root_causes)
        if root_causes != expected_root_causes:
            raise ValueError(f"Incorrect root causes: {root_causes}")

        # Parse service metrics
        service_metrics = row["service_metrics_post_troubleshooting"]
        if isinstance(service_metrics, str):
            service_metrics = json.loads(service_metrics)

        # Parse troubleshooting steps
        troubleshooting_steps = row["troubleshooting_steps"]
        if isinstance(troubleshooting_steps, str):
            troubleshooting_steps = ast.literal_eval(troubleshooting_steps)

        return {
            "timestamp troubleshooting started": row["timestamp_troubleshooting_started"],
            "timestamp troubleshooting completed": row["timestamp_troubleshooting_completed"],
            "troubleshooting steps": troubleshooting_steps,
            "updated service metrics": service_metrics,
        }

    def createEscalation(
        self,
        session_token: str,
        ticket_id: str,
        metrics_improved_post_troubleshooting: bool,
        escalation_required: bool,
    ) -> Dict[str, str]:
        """
        Creates escalation if needed.

        Args:
            session_token (str): Active session token
            ticket_id (str): Ticket ID
            metrics_improved_post_troubleshooting (bool): Whether metrics improved
            escalation_required (bool): Whether escalation is required

        Returns:
            Dict containing escalation details
        """
        if (
            not session_token
            or not ticket_id
            or metrics_improved_post_troubleshooting is None
            or escalation_required is None
        ):
            raise ValueError("Missing required parameters")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        # Find matching record
        matched_row = df[
            (df["session_token"] == session_token)
            & (df["ticket_id"] == ticket_id)
            & (df["metrics_improved_post_troubleshooting"] == metrics_improved_post_troubleshooting)
            & (df["escalation_required"] == escalation_required)
        ]

        if matched_row.empty:
            raise ValueError(f"No record found for the provided parameters")

        row = matched_row.iloc[0]
        return {
            "escalation ticket": (
                row["escalation_ticket_id"] if not pd.isna(row["escalation_ticket_id"]) else ""
            ),
            "escalation team": (
                row["escalation_team"] if not pd.isna(row["escalation_team"]) else ""
            ),
            "escalation reason": (
                row["escalation_reason"] if not pd.isna(row["escalation_reason"]) else ""
            ),
        }

    def process_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes tool calls to appropriate methods.

        Args:
            tool_name (str): Name of the tool to call
            tool_input (Dict[str, Any]): Input parameters for the tool

        Returns:
            Dict containing tool execution results
        """
        if tool_name == "validateAccount":
            return self.validateAccount(**tool_input)
        elif tool_name == "getAuthenticationDetails":
            return self.getAuthenticationDetails(**tool_input)
        elif tool_name == "createSessionAndOpenTicket":
            return self.createSessionAndOpenTicket(**tool_input)
        elif tool_name == "checkAccountStatus":
            return self.checkAccountStatus(**tool_input)
        elif tool_name == "checkPaymentStatus":
            return self.checkPaymentStatus(**tool_input)
        elif tool_name == "checkAccountSuspensionStatus":
            return self.checkAccountSuspensionStatus(**tool_input)
        elif tool_name == "checkServiceAreaOutage":
            return self.checkServiceAreaOutage(**tool_input)
        elif tool_name == "performTechnicalDiagnostics":
            return self.performTechnicalDiagnostics(**tool_input)
        elif tool_name == "executeTroubleshooting":
            return self.executeTroubleshooting(**tool_input)
        elif tool_name == "createEscalation":
            return self.createEscalation(**tool_input)
        else:
            raise ValueError(f"Invalid tool_name: {tool_name}")


if __name__ == "__main__":
    # Initialize the service manager
    service_manager = ServiceAccountManager()
    print("ServiceAccountManager initialized successfully!")

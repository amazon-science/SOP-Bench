# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

import os, json, re
import pandas as pd
from typing import Dict, Any, List, Union
from datetime import datetime
from dateutil import parser

class AircraftInspectionManager:
    """
    A manager class to process various stages of aircraft inspection by matching inputs
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

    def VerifyAircraftClearance(self,
        aircraft_id: str,
        tail_number: str,
        maintenance_record_id: str,
        expected_departure_time: str
        ) -> str:
        """
        Validates aircraft identification and checks maintenance records.
        """
        if not all([aircraft_id, tail_number, maintenance_record_id, expected_departure_time]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[(df["aircraft_id"] == aircraft_id)]

        if matched_rows.empty:
            raise ValueError("No data found for given aircraft_id and tail_number.")

        return matched_rows.iloc[0]["aircraft_ready"]

    def VerifyMechanicalComponents(self,
        aircraft_id: str,
        component_serial_number: str,
        inspection_location_id: str,
        component_weight: float,
        physical_condition_observation: str,
        installation_time: str
        ) -> str:
        """
        Performs comprehensive mechanical component verification.
        """
        if not all([aircraft_id, component_serial_number, inspection_location_id, component_weight, physical_condition_observation, installation_time]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[(df["aircraft_id"] == aircraft_id)]

        if matched_rows.empty:
            raise ValueError("No data found for given component_serial_number.")

        return matched_rows.iloc[0]["mechanical_inspection_result"]

    def VerifyElectricalSystems(self,
        aircraft_id: str,
        battery_status: str,
        circuit_continuity_check: str,
        avionics_diagnostics_response: str
        ) -> str:
        """
        Verifies electrical systems according to ESAP standards.
        """
        if not all([aircraft_id, battery_status, circuit_continuity_check, avionics_diagnostics_response]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[df["aircraft_id"] == aircraft_id]

        if matched_rows.empty:
            raise ValueError("No data found for given aircraft_id.")

        return matched_rows.iloc[0]["electrical_inspection_result"]

    def ReportComponentIncident(self,                
        aircraft_id: str,
        mechanical_inspection_result: str,
        electrical_inspection_result: str
        ) -> str:
        """
        Reports component incidents based on inspection results.
        """
        if not all([aircraft_id, mechanical_inspection_result, electrical_inspection_result]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[df["aircraft_id"] == aircraft_id]

        if matched_rows.empty:
            raise ValueError("No data found for given aircraft_id.")

        return matched_rows.iloc[0]["component_incident_response"]

    def ReportComponentMismatch(self,
        aircraft_id: str,
        component_serial_number: str,
        installed_component_serial_number: str,
        inspection_location_id: str
        ) -> str:
        """
        Reports component serial number mismatches during inspections.
        """
        if not all([aircraft_id, component_serial_number, installed_component_serial_number, inspection_location_id]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[df["aircraft_id"] == aircraft_id]

        if matched_rows.empty:
            raise ValueError("No data found for given component_serial_number.")

        return matched_rows.iloc[0]["component_mismatch_response"]
    
    def CrossCheckSpecifications(self,
        aircraft_id: str,
        component_weight: float,
        expected_component_weight:float,
        installation_time: str,
        actual_inspection_time: str
        ) -> str:
        """
        Reports component serial number mismatches during inspections.
        """
        if not all([aircraft_id, component_weight, expected_component_weight, installation_time, actual_inspection_time]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[df["aircraft_id"] == aircraft_id]

        if matched_rows.empty:
            raise ValueError("No data found for given component_serial_number.")

        return matched_rows.iloc[0]["cross_check_response"]
    
    def ReportCrossCheck(self,
        maintenance_record_id,
        aircraft_id: str,
        component_incident_response: str,
        component_mismatch_response: str
        ) -> str:
        """
        Reports component serial number mismatches during inspections.
        """
        if not all([aircraft_id, maintenance_record_id, component_incident_response, component_mismatch_response]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[df["aircraft_id"] == aircraft_id]


        if matched_rows.empty:
            raise ValueError("No data found for given component_serial_number.")

        return matched_rows.iloc[0]["cross_check_reporting_response"]
    
    def process_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatches tool calls to the corresponding class method.

        Parameters:
        - tool_name: Name of the function to invoke
        - tool_input: Dictionary of function arguments

        Returns:
        - Dictionary with key as output variable and value as result
        """
        if tool_name == "VerifyAircraftClearance":
            return {"aircraft_ready": self.VerifyAircraftClearance(**tool_input)}
        elif tool_name == "VerifyMechanicalComponents":
            return {"mechanical_inspection_result": self.VerifyMechanicalComponents(**tool_input)}
        elif tool_name == "VerifyElectricalSystems":
            return {"electrical_inspection_result": self.VerifyElectricalSystems(**tool_input)}
        elif tool_name == "ReportComponentIncident":
            return {"component_incident_response": self.ReportComponentIncident(**tool_input)}
        elif tool_name == "ReportComponentMismatch":
            return {"component_mismatch_response": self.ReportComponentMismatch(**tool_input)}
        elif tool_name == "CrossCheckSpecifications":
            return {"cross_check_response": self.CrossCheckSpecifications(**tool_input)}
        elif tool_name == "ReportCrossCheck":
            return {"cross_check_reporting_response": self.ReportCrossCheck(**tool_input)}
        else:
            raise ValueError(f"Invalid tool_name: {tool_name}")


if __name__ == "__main__":
    manager = AircraftInspectionManager()
        
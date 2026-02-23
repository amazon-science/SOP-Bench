# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

import os
import json
import pandas as pd
from typing import Dict, Any, List

class PatientIntakeManager:
    """
    A manager class to process various stages of patient intake by matching inputs
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

    def validateInsurance(
        self,
        patient_id: str,
        insurance_provider: str,
        policy_number: str,
        group_number: str,
        coverage_start_date: str,
        insurance_type: str
    ) -> str:
        """
        Validates patient's insurance coverage information.

        Parameters:
        - patient_id: Unique identifier for the patient
        - insurance_provider: Name of the provider
        - policy_number: Insurance policy number
        - group_number: Group number associated with the policy
        - coverage_start_date: Date when coverage started (YYYY-MM-DD)
        - insurance_type: Type of insurance (e.g. Private, Medicare)

        Returns:
        - insurance_validation: Validation result from the dataset
        """
        if not all([patient_id, insurance_provider, policy_number, group_number, coverage_start_date, insurance_type]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[df["patient_id"] == patient_id]

        if matched_rows.empty:
            raise ValueError("No data found for given patient_id.")
        if len(matched_rows) > 1:
            matched_rows = matched_rows.iloc[[0]]

        return matched_rows.iloc[0]["insurance_validation"]

    def validatePrescriptionBenefits(
        self,
        patient_id: str,
        insurance_provider: str,
        policy_number: str
    ) -> str:
        """
        Validates a patient's prescription insurance status.

        Parameters:
        - patient_id: Unique identifier for the patient
        - insurance_provider: Name of the insurance company
        - policy_number: Insurance policy number

        Returns:
        - prescription_insurance_validation: Validation result from the dataset
        """
        if not all([patient_id, insurance_provider, policy_number]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[df["patient_id"] == patient_id]

        if matched_rows.empty:
            raise ValueError("No data found for given patient_id.")
        if len(matched_rows) > 1:
            matched_rows = matched_rows.iloc[[0]]

        return matched_rows.iloc[0]["prescription_insurance_validation"]

    def verifyPharmacy(
        self,
        patient_id: str,
        preferred_pharmacy_name: str,
        preferred_pharmacy_address: str,
        pharmacy_phone: str
    ) -> str:
        """
        Verifies the patient's preferred pharmacy details.

        Parameters:
        - patient_id: Unique identifier for the patient
        - preferred_pharmacy_name: Pharmacy name
        - preferred_pharmacy_address: Address of the pharmacy
        - pharmacy_phone: Contact number

        Returns:
        - pharmacy_check: Result of pharmacy verification
        """
        if not all([patient_id, preferred_pharmacy_name, preferred_pharmacy_address, pharmacy_phone]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[df["patient_id"] == patient_id]

        if matched_rows.empty:
            raise ValueError("No data found for given patient_id.")
        if len(matched_rows) > 1:
            matched_rows = matched_rows.iloc[[0]]

        return matched_rows.iloc[0]["pharmacy_check"]

    def calculateLifestyleRisk(
        self,
        patient_id: str,
        smoking_status: str,
        alcohol_consumption: str,
        exercise_frequency: str
    ) -> str:
        """
        Assesses the patient's lifestyle risk level.

        Parameters:
        - patient_id: Unique identifier for the patient
        - smoking_status: Smoking habit (Never, Former, Current)
        - alcohol_consumption: Alcohol use (None, Occasional, Moderate, Heavy)
        - exercise_frequency: Weekly exercise frequency

        Returns:
        - life_style_risk_level: Computed risk level
        """
        if not all([patient_id, smoking_status, alcohol_consumption, exercise_frequency]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[df["patient_id"] == patient_id]

        if matched_rows.empty:
            raise ValueError("No data found for given patient_id.")
        if len(matched_rows) > 1:
            matched_rows = matched_rows.iloc[[0]]

        return matched_rows.iloc[0]["life_style_risk_level"]

    def calculateOverallRisk(
        self,
        patient_id: str,
        previous_surgeries: List[str],
        chronic_conditions: List[str],
        life_style_risk_level: str
    ) -> str:
        """
        Calculates the overall patient risk level based on medical and lifestyle data.

        Parameters:
        - patient_id: Unique identifier for the patient
        - previous_surgeries: List of surgeries
        - chronic_conditions: List of chronic illnesses
        - life_style_risk_level: Risk from calculateLifestyleRisk

        Returns:
        - overall_risk_level: Computed overall risk
        """
        if not all([patient_id, previous_surgeries, chronic_conditions, life_style_risk_level]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[df["patient_id"] == patient_id]

        if matched_rows.empty:
            raise ValueError("No data found for given patient_id.")
        if len(matched_rows) > 1:
            matched_rows = matched_rows.iloc[[0]]

        return matched_rows.iloc[0]["overall_risk_level"]

    def registerPatient(
        self,
        patient_id: str,
        insurance_validation: str,
        prescription_insurance_validation: str,
        life_style_risk_level: str,
        overall_risk_level: str,
        pharmacy_check: str
    ) -> str:
        """
        Registers a patient after completing all prior validations.

        Parameters:
        - patient_id: Unique identifier
        - insurance_validation: Result from validateInsurance
        - prescription_insurance_validation: Result from validatePrescriptionBenefits
        - life_style_risk_level: Result from calculateLifestyleRisk
        - overall_risk_level: Result from calculateOverallRisk
        - pharmacy_check: Result from verifyPharmacy

        Returns:
        - user_registration: Final registration status
        """
        if not all([patient_id, insurance_validation, prescription_insurance_validation, life_style_risk_level, overall_risk_level, pharmacy_check]):
            raise ValueError("Missing required input fields.")

        df = pd.read_csv(self.dataset_file_path)
        matched_rows = df[df["patient_id"] == patient_id]

        if matched_rows.empty:
            raise ValueError("No data found for given patient_id.")
        if len(matched_rows) > 1:
            matched_rows = matched_rows.iloc[[0]]

        return matched_rows.iloc[0]["user_registration"]

    def process_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatches tool calls to the corresponding class method.

        Parameters:
        - tool_name: Name of the function to invoke
        - tool_input: Dictionary of function arguments

        Returns:
        - Dictionary with key as output variable and value as result
        """
        if tool_name == "validateInsurance":
            return {"insurance_validation": self.validateInsurance(**tool_input)}
        elif tool_name == "validatePrescriptionBenefits":
            return {"prescription_insurance_validation": self.validatePrescriptionBenefits(**tool_input)}
        elif tool_name == "verifyPharmacy":
            return {"pharmacy_check": self.verifyPharmacy(**tool_input)}
        elif tool_name == "calculateLifestyleRisk":
            return {"life_style_risk_level": self.calculateLifestyleRisk(**tool_input)}
        elif tool_name == "calculateOverallRisk":
            return {"overall_risk_level": self.calculateOverallRisk(**tool_input)}
        elif tool_name == "registerPatient":
            return {"user_registration": self.registerPatient(**tool_input)}
        else:
            raise ValueError(f"Invalid tool_name: {tool_name}")

if __name__ == "__main__":
    manager = PatientIntakeManager()
        
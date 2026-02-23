# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0


import os
import json
import pandas as pd
from typing import Any, Dict, List
from datetime import datetime

class BusinessVerificationManager:
    
    DATASET_CSV_FILE = "test_set_with_outputs.csv"
    TOOLSPEC_JSON_FILE = "toolspecs.json"
    
    def __init__(self):
        """Initialize the BusinessVerificationManager with dataset path."""
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

    def getBusinessProfile(self, business_id: str) -> Dict[str, Any]:
        """
        Retrieves complete business profile and validates required fields.
        
        Parameters:
        -----------
        business_id : str
            Unique identifier for the business
            
        Returns:
        --------
        Dict[str, Any]
            Complete business profile information
            
        Raises:
        -------
        ValueError
            If business_id is invalid or not found
        """
        if not business_id:
            raise ValueError("Missing required parameter: business_id")
            
        # Load dataset
        df = pd.read_csv(self.dataset_file_path)
        
        # Find matching business
        matched_rows = df[df['business_id'] == business_id]
        
        if matched_rows.empty:
            raise ValueError(f"No business found with ID: {business_id}")
            
        if len(matched_rows) > 1:
            raise ValueError(f"Multiple businesses found with ID: {business_id}")
            
        row = matched_rows.iloc[0]
        
        return {
            "business_name": row['business_name'],
            "business_website": row['business_website'],
            "business_address": row['business_address'],
            "business_email": row['business_email'],
            "business_type": row['business_type'],
            "registration_number": row['registration_number'],
            "license_number": row['license_number'],
            "tax_id": row['tax_id'],
            "business_registration_state": row['business_registration_state']
        }

    def verifyBusinessRegistration(
        self, 
        business_id: str,
        registration_number: str,
        business_registration_state: str,
        license_number: str
    ) -> Dict[str, Any]:
        """
        Validates business registration and licensing status.
        
        Parameters:
        -----------
        business_id : str
            Unique identifier for the business
        registration_number : str
            Business registration number
        business_registration_state : str
            State/jurisdiction of registration
        license_number : str
            Business license number
            
        Returns:
        --------
        Dict[str, Any]
            Registration and license verification status
            
        Raises:
        -------
        ValueError
            If parameters are invalid or business not found
        """
        if not all([business_id, registration_number, business_registration_state, license_number]):
            raise ValueError("Missing one or more required parameters")
            
        # Load dataset
        df = pd.read_csv(self.dataset_file_path)
        
        # Find matching business
        matched_rows = df[
            (df['business_id'] == business_id) &
            (df['registration_number'] == registration_number) &
            (df['business_registration_state'] == business_registration_state) &
            (df['license_number'] == license_number)
        ]
        
        if matched_rows.empty:
            raise ValueError("No matching business record found")
            
        row = matched_rows.iloc[0]
        
        return {
            "registration_status": row['registration_status'],
            "date_of_entry": row['date_of_entry'],
            "license_expiry_date": row['license_expiry_date'],
        }

    def getOwnershipData(self, business_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieves the list of Ultimate Beneficial Owners (UBOs) for a given business.
        
        Parameters:
        -----------
        business_id : str
            Unique identifier for the business
            
        Returns:
        --------
        Dict[str, List[Dict[str, Any]]]
            List of UBOs and their ownership details
            
        Raises:
        -------
        ValueError
            If business_id is invalid or not found
        """
        if not business_id:
            raise ValueError("Missing required parameter: business_id")
            
        # Load dataset
        df = pd.read_csv(self.dataset_file_path)
        
        # Find matching business
        matched_rows = df[df['business_id'] == business_id]
        
        if matched_rows.empty:
            raise ValueError(f"No business found with ID: {business_id}")
            
        row = matched_rows.iloc[0]
        
        # Parse UBO list from JSON string
        ubo_list = row['ubo_list']
        if isinstance(ubo_list, dict):
            ubo_list = json.loads(ubo_list)
            
        return {"ubo_list": ubo_list}

    def verifyUBO(
        self, 
        business_id: str,
        ubo_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Processes and verifies Ultimate Beneficial Ownership information.
        
        Parameters:
        -----------
        business_id : str
            Unique identifier for the business
        ubo_list : List[Dict[str, Any]]
            List of UBOs to verify
            
        Returns:
        --------
        Dict[str, Any]
            UBO verification results
            
        Raises:
        -------
        ValueError
            If parameters are invalid or verification fails
        """
        if not business_id or not ubo_list:
            raise ValueError("Missing required parameters")
            
        # Load dataset
        df = pd.read_csv(self.dataset_file_path)
        
        # Find matching business
        matched_rows = df[df['business_id'] == business_id]
        
        if matched_rows.empty:
            raise ValueError(f"No business found with ID: {business_id}")
            
        row = matched_rows.iloc[0]
        
        return {
            "shell_company_suspected": bool(row['shell_company_suspected']),
            "ownership_layer_count": int(row['ownership_layer_count']),
            "offshore_jurisdiction_flag": bool(row['offshore_jurisdiction_flag'])
        }

    def performSanctionsCheck(
        self,
        business_id: str,
        ubo_list: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Executes sanctions and PEP screening for UBOs.
        
        Parameters:
        -----------
        business_id : str
            Unique identifier for the business
        ubo_list : List[Dict[str, Any]]
            List of UBOs to check
            
        Returns:
        --------
        Dict[str, List[Dict[str, str]]]
            Sanctions and PEP check results
            
        Raises:
        -------
        ValueError
            If parameters are invalid or check fails
        """
        def build_status_output(sanction_check_status_list, pep_status_list, target_name):
            try:
                sanction_status = next(person for person in sanction_check_status_list if person.get('name') == target_name)
            except StopIteration:
                raise ValueError(f"Name '{target_name}' not found in Sanctions database.")
            
            try:
                pep_status = next(person for person in pep_status_list if person.get('name') == target_name)
            except StopIteration:
                raise ValueError(f"Name '{target_name}' not found in PEP database.")
            
            output = {
                "sanction_check_status": [sanction_status],
                "pep_status": [pep_status]
            }
            return output
        
        if not business_id:
            raise ValueError("Missing required parameters")
            
        # Load dataset
        df = pd.read_csv(self.dataset_file_path)
        
        # Find matching business
        matched_rows = df[df['business_id'] == business_id]
        
        if matched_rows.empty:
            raise ValueError(f"No business found with ID: {business_id}")
            
        row = matched_rows.iloc[0]
        ubo_list = str(ubo_list).replace("'", '"')
        if isinstance(ubo_list, str):
            ubo_list = json.loads(ubo_list)        
        ubo_name = ubo_list[0]["name"]
        # Parse sanction and PEP status from JSON strings
        sanction_check_status = row['sanction_check_status'].replace("'", '"')
        pep_status = row['pep_status'].replace("'", '"')
        
        if isinstance(sanction_check_status, str):
            sanction_check_status_list = json.loads(sanction_check_status)
        if isinstance(pep_status, str):
            pep_status_list = json.loads(pep_status)
        
        
        return build_status_output(sanction_check_status_list, pep_status_list, ubo_name)

    def getBankData(self, business_id: str) -> Dict[str, str]:
        """
        Retrieves bank account information associated with a business.
        
        Parameters:
        -----------
        business_id : str
            Unique identifier for the business
            
        Returns:
        --------
        Dict[str, str]
            Bank account details
            
        Raises:
        -------
        ValueError
            If business_id is invalid or not found
        """
        if not business_id:
            raise ValueError("Missing required parameter: business_id")
            
        # Load dataset
        df = pd.read_csv(self.dataset_file_path)
        
        # Find matching business
        matched_rows = df[df['business_id'] == business_id]
        
        if matched_rows.empty:
            raise ValueError(f"No business found with ID: {business_id}")
            
        row = matched_rows.iloc[0]
        
        return {
            "bank_account_number": str(row['bank_account_number']),
            "banking_institution": str(row['banking_institution']),
            "bank_account_type": str(row['bank_account_type']),
            "bank_verification_status": str(row['bank_verification_status'])
        }

    def verifyBankAccount(
        self,
        business_id: str,
        bank_account_number: str,
        banking_institution: str,
        bank_account_type: str
    ) -> Dict[str, str]:
        """
        Validates bank account information.
        
        Parameters:
        -----------
        business_id : str
            Unique identifier for the business
        bank_account_number : str
            Bank account number
        banking_institution : str
            Name of the banking institution
        bank_account_type : str
            Type of bank account
            
        Returns:
        --------
        Dict[str, str]
            Bank account verification status
            
        Raises:
        -------
        ValueError
            If parameters are invalid or verification fails
        """
        if not all([business_id, bank_account_number, banking_institution, bank_account_type]):
            raise ValueError("Missing one or more required parameters")
            
        # Load dataset
        df = pd.read_csv(self.dataset_file_path)
        
        # Find matching business
        matched_rows = df[
            (df['business_id'] == business_id) &
            (df['bank_account_number'] == int(bank_account_number)) &
            (df['banking_institution'] == banking_institution) &
            (df['bank_account_type'] == bank_account_type)
        ]
        
        if matched_rows.empty:
            raise ValueError("No matching bank account record found")
            
        row = matched_rows.iloc[0]
        
        return {
            "bank_verification_status": str(row['bank_verification_status'])
        }

    def calculateRiskScore(self, business_id: str) -> Dict[str, float]:
        """
        Calculates final risk score and determines escalation status.
        
        Parameters:
        -----------
        business_id : str
            Unique identifier for the business
            
        Returns:
        --------
        Dict[str, float]
            Calculated risk score
            
        Raises:
        -------
        ValueError
            If business_id is invalid or calculation fails
        """
        if not business_id:
            raise ValueError("Missing required parameter: business_id")
            
        # Load dataset
        df = pd.read_csv(self.dataset_file_path)
        
        # Find matching business
        matched_rows = df[df['business_id'] == business_id]
        
        if matched_rows.empty:
            raise ValueError(f"No business found with ID: {business_id}")
            
        row = matched_rows.iloc[0]
        
        return {
            "risk_score": float(row['risk_score'])
        }

    def process_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes tool calls to appropriate methods.
        
        Parameters:
        -----------
        tool_name : str
            Name of the tool to execute
        tool_input : Dict[str, Any]
            Input parameters for the tool
            
        Returns:
        --------
        Dict[str, Any]
            Tool execution results
            
        Raises:
        -------
        ValueError
            If tool_name is invalid
        """
        if tool_name == "getBusinessProfile":
            return self.getBusinessProfile(**tool_input)
        elif tool_name == "verifyBusinessRegistration":
            return self.verifyBusinessRegistration(**tool_input)
        elif tool_name == "getOwnershipData":
            return self.getOwnershipData(**tool_input)
        elif tool_name == "verifyUBO":
            return self.verifyUBO(**tool_input)
        elif tool_name == "performSanctionsCheck":
            return self.performSanctionsCheck(**tool_input)
        elif tool_name == "getBankData":
            return self.getBankData(**tool_input)
        elif tool_name == "verifyBankAccount":
            return self.verifyBankAccount(**tool_input)
        elif tool_name == "calculateRiskScore":
            return self.calculateRiskScore(**tool_input)
        else:
            raise ValueError(f"Invalid tool_name: {tool_name}")


if __name__ == "__main__":
    # Initialize manager
    manager = BusinessVerificationManager()
    
    # Test getBusinessProfile
    print("\nTesting getBusinessProfile:")
    try:
        result = manager.getBusinessProfile(business_id="biz_001")
        print("Success:", result)
    except ValueError as e:
        print("Error:", str(e))
    try:
        result = manager.getBusinessProfile(business_id="invalid_id")
        print("Success:", result)
    except ValueError as e:
        print("Error:", str(e))
        
    # Test verifyBusinessRegistration
    print("\nTesting verifyBusinessRegistration:")
    try:
        result = manager.verifyBusinessRegistration(
            business_id="biz_001",
            registration_number="REG123456",
            business_registration_state="Delaware (USA)",
            license_number="LIC987654"
        )
        print("Success:", result)
    except ValueError as e:
        print("Error:", str(e))
        
    # Test getOwnershipData
    print("\nTesting getOwnershipData:")
    try:
        result = manager.getOwnershipData(business_id="biz_001")
        print("Success:", result)
    except ValueError as e:
        print("Error:", str(e))
        
    # Test verifyUBO
    print("\nTesting verifyUBO:")
    try:
        ubo_list = [
            {"name": "John Smith", "id": "ID001", "ownership": 60.0},
            {"name": "Jane Doe", "id": "ID002", "ownership": 40.0}
        ]
        result = manager.verifyUBO(business_id="biz_001", ubo_list=ubo_list)
        print("Success:", result)
    except ValueError as e:
        print("Error:", str(e))
        
    # Test performSanctionsCheck
    print("\nTesting performSanctionsCheck:")
    try:
        ubo_list = [
            {"name": "John Smith", "id": "ID001", "ownership": 60.0},
        ]
        result = manager.performSanctionsCheck(business_id="biz_001", ubo_list=ubo_list)
        print("Success:", result)
    except ValueError as e:
        print("Error:", str(e))

    # Test getBankData
    print("\nTesting getBankData:")
    try:
        result = manager.getBankData(business_id="biz_001")
        print("Success:", result)
    except ValueError as e:
        print("Error:", str(e))
    try:
        result = manager.getBankData(business_id="invalid_id")
        print("Success:", result)
    except ValueError as e:
        print("Error:", str(e))
        
    # Test verifyBankAccount
    print("\nTesting verifyBankAccount:")
    try:
        result = manager.verifyBankAccount(
            business_id="biz_001",
            bank_account_number="32678910",
            banking_institution="Bank of America",
            bank_account_type="Business"
        )
        print("Success:", result)
    except ValueError as e:
        print("Error:", str(e))
    try:
        result = manager.verifyBankAccount(
            business_id="biz_001",
            bank_account_number="invalid_account",
            banking_institution="Invalid Bank",
            bank_account_type="Invalid"
        )
        print("Success:", result)
    except ValueError as e:
        print("Error:", str(e))
        
    # Test calculateRiskScore
    print("\nTesting calculateRiskScore:")
    try:
        result = manager.calculateRiskScore(business_id="biz_001")
        print("Success:", result)
    except ValueError as e:
        print("Error:", str(e))
    try:
        result = manager.calculateRiskScore(business_id="invalid_id")
        print("Success:", result)
    except ValueError as e:
        print("Error:", str(e))
        
    # Test process_tool_call
    print("\nTesting process_tool_call:")
    try:
        result = manager.process_tool_call(
            tool_name="getBusinessProfile",
            tool_input={"business_id": "biz_001"}
        )
        print("Success:", result)
    except ValueError as e:
        print("Error:", str(e))
    try:
        result = manager.process_tool_call(
            tool_name="invalid_tool",
            tool_input={"business_id": "biz_001"}
        )
        print("Success:", result)
    except ValueError as e:
        print("Error:", str(e))
        
    # Test high-risk business scenario
    print("\nTesting high-risk business scenario:")
    try:
        # Get business profile
        profile = manager.getBusinessProfile(business_id="biz_002")
        print("Profile:", profile)
        
        # Verify registration
        reg_status = manager.verifyBusinessRegistration(
            business_id="biz_002",
            registration_number="REG789012",
            business_registration_state="Cayman Islands",
            license_number="LIC654321"
        )
        print("Registration Status:", reg_status)
        
        # Get ownership data
        ownership = manager.getOwnershipData(business_id="biz_002")
        print("Ownership:", ownership)
        
        # Verify UBO
        ubo_verification = manager.verifyUBO(
            business_id="biz_002",
            ubo_list=ownership["ubo_list"]
        )
        print("UBO Verification:", ubo_verification)
        
        # Perform sanctions check
        print(ownership["ubo_list"])
        sanctions = manager.performSanctionsCheck(
            business_id="biz_002",
            ubo_list=ownership["ubo_list"]
        )
        print("Sanctions Check:", sanctions)
        
        # Get bank data
        bank_data = manager.getBankData(business_id="biz_002")
        print("Bank Data:", bank_data)
        
        # Verify bank account
        bank_verification = manager.verifyBankAccount(
            business_id="biz_002",
            bank_account_number="45678901",
            banking_institution="CitiBank",
            bank_account_type="Business"
        )
        print("Bank Verification:", bank_verification)
        
        # Calculate risk score
        risk_score = manager.calculateRiskScore(business_id="biz_002")
        print("Risk Score:", risk_score)
    except ValueError as e:
        print("Error:", str(e))
        
    # Test low-risk business scenario
    print("\nTesting low-risk business scenario:")
    try:
        # Get business profile
        profile = manager.getBusinessProfile(business_id="biz_005")
        print("Profile:", profile)
        
        # Verify registration
        reg_status = manager.verifyBusinessRegistration(
            business_id="biz_005",
            registration_number="REG567890",
            business_registration_state="Oregon (USA)",
            license_number="LIC345678"
        )
        print("Registration Status:", reg_status)
        
        # Get ownership data
        ownership = manager.getOwnershipData(business_id="biz_005")
        print("Ownership:", ownership)
        
        # Verify UBO
        ubo_verification = manager.verifyUBO(
            business_id="biz_005",
            ubo_list=ownership["ubo_list"]
        )
        print("UBO Verification:", ubo_verification)
        
        # Perform sanctions check
        sanctions = manager.performSanctionsCheck(
            business_id="biz_005",
            ubo_list=ownership["ubo_list"]
        )
        print("Sanctions Check:", sanctions)
        
        # Get bank data
        bank_data = manager.getBankData(business_id="biz_005")
        print("Bank Data:", bank_data)
        
        # Verify bank account
        bank_verification = manager.verifyBankAccount(
            business_id="biz_005",
            bank_account_number="78901234",
            banking_institution="US Bank",
            bank_account_type="Checking"
        )
        print("Bank Verification:", bank_verification)
        
        # Calculate risk score
        risk_score = manager.calculateRiskScore(business_id="biz_005")
        print("Risk Score:", risk_score)
    except ValueError as e:
        print("Error:", str(e))

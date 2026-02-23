# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

import os
import json
import pandas as pd
from typing import Dict, Any

class DangerousGoodsManager:
    """
    A class to calculate various hazard scores for products based on their safety data sheets,
    handling guidelines, transportation requirements, and disposal guidelines.
    """
    
    DATASET_CSV_FILE = "test_set_with_outputs.csv"
    TOOLSPEC_JSON_FILE = "toolspecs.json"

    def __init__(self):
        """Initialize the DangerousGoodsManager with the dataset."""
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
        
    def calculate_sds_label_score(self, product_id: str, sds_label_text: str) -> Dict[str, Any]:
        """
        Calculate safety data sheet label score based on provided text.
        
        Args:
            product_id (str): Unique identifier for the product
            sds_label_text (str): Safety data sheet label text to analyze
            
        Returns:
            Dict[str, Any]: Dictionary containing product ID and calculated SDS label score
            
        Raises:
            ValueError: If product_id or sds_label_text is missing or invalid
        """
        # Validate input parameters
        if not product_id or not sds_label_text:
            raise ValueError("Missing required parameters: product_id or sds_label_text")
            
        # Load dataset
        df = pd.read_csv(self.dataset_file_path)
        
        # Find matching product
        matched_row = df[df['product_id'] == product_id]
        
        if matched_row.empty:
            raise ValueError(f"No product found with ID: {product_id}")
            
        if len(matched_row) > 1:
            raise ValueError(f"Multiple products found with ID: {product_id}")
            
        # Return the score
        return {
            "product_id": product_id,
            "sds_label_score": int(matched_row.iloc[0]['sds_label_score'])
        }
        
    def calculate_handling_score(self, product_id: str, handling_and_storage_guidelines: str) -> Dict[str, Any]:
        """
        Calculate handling and storage score based on provided guidelines.
        
        Args:
            product_id (str): Unique identifier for the product
            handling_and_storage_guidelines (str): Guidelines for handling and storage
            
        Returns:
            Dict[str, Any]: Dictionary containing product ID and calculated handling score
            
        Raises:
            ValueError: If product_id or handling_and_storage_guidelines is missing or invalid
        """
        # Validate input parameters
        if not product_id or not handling_and_storage_guidelines:
            raise ValueError("Missing required parameters: product_id or handling_and_storage_guidelines")
            
        # Load dataset
        df = pd.read_csv(self.dataset_file_path)
        
        # Find matching product
        matched_row = df[df['product_id'] == product_id]
        
        if matched_row.empty:
            raise ValueError(f"No product found with ID: {product_id}")
            
        if len(matched_row) > 1:
            raise ValueError(f"Multiple products found with ID: {product_id}")
            
        # Return the score
        return {
            "product_id": product_id,
            "handling_score": int(matched_row.iloc[0]['handling_score'])
        }
        
    def calculate_transportation_score(self, product_id: str, transportation_requirements: str) -> Dict[str, Any]:
        """
        Calculate transportation score based on provided requirements.
        
        Args:
            product_id (str): Unique identifier for the product
            transportation_requirements (str): Transportation requirements text
            
        Returns:
            Dict[str, Any]: Dictionary containing product ID and calculated transportation score
            
        Raises:
            ValueError: If product_id or transportation_requirements is missing or invalid
        """
        # Validate input parameters
        if not product_id or not transportation_requirements:
            raise ValueError("Missing required parameters: product_id or transportation_requirements")
            
        # Load dataset
        df = pd.read_csv(self.dataset_file_path)
        
        # Find matching product
        matched_row = df[df['product_id'] == product_id]
        
        if matched_row.empty:
            raise ValueError(f"No product found with ID: {product_id}")
            
        if len(matched_row) > 1:
            raise ValueError(f"Multiple products found with ID: {product_id}")
            
        # Return the score
        return {
            "product_id": product_id,
            "transportation_score": int(matched_row.iloc[0]['transportation_score'])
        }
        
    def calculate_disposal_score(self, product_id: str, disposal_guidelines: str) -> Dict[str, Any]:
        """
        Calculate disposal score based on provided guidelines.
        
        Args:
            product_id (str): Unique identifier for the product
            disposal_guidelines (str): Guidelines for product disposal
            
        Returns:
            Dict[str, Any]: Dictionary containing product ID and calculated disposal score
            
        Raises:
            ValueError: If product_id or disposal_guidelines is missing or invalid
        """
        # Validate input parameters
        if not product_id or not disposal_guidelines:
            raise ValueError("Missing required parameters: product_id or disposal_guidelines")
            
        # Load dataset
        df = pd.read_csv(self.dataset_file_path)
        
        # Find matching product
        matched_row = df[df['product_id'] == product_id]
        
        if matched_row.empty:
            raise ValueError(f"No product found with ID: {product_id}")
            
        if len(matched_row) > 1:
            raise ValueError(f"Multiple products found with ID: {product_id}")
            
        # Return the score
        return {
            "product_id": product_id,
            "disposal_score": int(matched_row.iloc[0]['disposal_score'])
        }
        
    def process_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process tool calls dynamically based on the tool name and input provided.
        
        Args:
            tool_name (str): Name of the tool to execute
            tool_input (Dict[str, Any]): Input parameters for the tool
            
        Returns:
            Dict[str, Any]: Tool execution results
            
        Raises:
            ValueError: If tool_name is invalid or unsupported
        """
        if tool_name == "calculate_sds_label_score":
            return self.calculate_sds_label_score(**tool_input)
        elif tool_name == "calculate_handling_score":
            return self.calculate_handling_score(**tool_input)
        elif tool_name == "calculate_transportation_score":
            return self.calculate_transportation_score(**tool_input)
        elif tool_name == "calculate_disposal_score":
            return self.calculate_disposal_score(**tool_input)
        else:
            raise ValueError(f"Invalid tool_name: {tool_name}")

# Test cases
if __name__ == "__main__":
    calculator = DangerousGoodsManager()
    
    print("="*50)
    print("Testing calculate_sds_label_score")
    
    # Invalid test case - missing product_id
    try:
        result = calculator.calculate_sds_label_score("", "Some label text")
        print("Should have raised ValueError")
    except ValueError as e:
        print(f"Expected error: {str(e)}")
        
    # Invalid test case - invalid product_id
    try:
        result = calculator.calculate_sds_label_score("INVALID_ID", "Some label text")
        print("Should have raised ValueError")
    except ValueError as e:
        print(f"Expected error: {str(e)}")
        
    # Valid test case
    try:
        result = calculator.calculate_sds_label_score("P_13024", "Acute aquatic toxicity")
        print(f"Valid result: {result}")
    except ValueError as e:
        print(f"Unexpected error: {str(e)}")
        
    print("="*50)
    print("Testing calculate_handling_score")
    
    # Invalid test case - missing guidelines
    try:
        result = calculator.calculate_handling_score("P_13024", "")
        print("Should have raised ValueError")
    except ValueError as e:
        print(f"Expected error: {str(e)}")
        
    # Valid test case
    try:
        result = calculator.calculate_handling_score("P_13024", "Store away from waterways")
        print(f"Valid result: {result}")
    except ValueError as e:
        print(f"Unexpected error: {str(e)}")
        
    print("="*50)
    print("Testing calculate_transportation_score")
    
    # Invalid test case - missing requirements
    try:
        result = calculator.calculate_transportation_score("P_13024", "")
        print("Should have raised ValueError")
    except ValueError as e:
        print(f"Expected error: {str(e)}")
        
    # Valid test case
    try:
        result = calculator.calculate_transportation_score("P_13024", "Marine pollutant protocols")
        print(f"Valid result: {result}")
    except ValueError as e:
        print(f"Unexpected error: {str(e)}")
        
    print("="*50)
    print("Testing calculate_disposal_score")
    
    # Invalid test case - missing guidelines
    try:
        result = calculator.calculate_disposal_score("P_13024", "")
        print("Should have raised ValueError")
    except ValueError as e:
        print(f"Expected error: {str(e)}")
        
    # Valid test case
    try:
        result = calculator.calculate_disposal_score("P_13024", "Specialized treatment required")
        print(f"Valid result: {result}")
    except ValueError as e:
        print(f"Unexpected error: {str(e)}")

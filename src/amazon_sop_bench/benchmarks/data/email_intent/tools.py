# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

import os
import json
import pandas as pd
import re
from typing import Dict, Any

class ProductListingManager:
    """
    Manages product listing operations including price, description and status retrieval.
    """
    
    DATASET_CSV_FILE = "test_set_with_outputs.csv"
    TOOLSPEC_JSON_FILE = "toolspecs.json"
    
    def __init__(self):
        """
        Initializes the ProductListingManager with the dataset path.
        """
        self.dataset_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            self.DATASET_CSV_FILE
        )
        print(f"Dataset file path: {self.dataset_file_path}")

    def get_product_price(
            self, 
            product_id: str, 
            marketplace_id: str
            ) -> Dict[str, Any]:
        """
        Retrieves the current price for a specified product.

        Parameters:
        -----------
        product_id : str
            Unique identifier for the product
        marketplace_id : str
            Marketplace identifier

        Returns:
        --------
        Dict[str, Any]
            Dictionary containing product_id and listing_price

        Raises:
        -------
        ValueError
            If product_id is invalid or product is not found
        """
        if not product_id:
            raise ValueError("Missing required parameter: product_id")

        if not re.match("^P[A-Z0-9]{5}$", product_id):
            raise ValueError("Invalid product_id format")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)
        
        # Find matching product
        matched_rows = df[df["product_id"] == product_id]

        if matched_rows.empty:
            raise ValueError(f"No product found with id={product_id}")

        row = matched_rows.iloc[0]
        
        return {
            "product_id": row["product_id"],
            "listing_price": float(row["listing_price"]) if pd.notna(row["listing_price"]) else 0.0
        }

    def get_product_description(self, product_id: str) -> Dict[str, Any]:
        """
        Retrieves the current listing status and metadata for a product.

        Parameters:
        -----------
        product_id : str
            Unique identifier for the product

        Returns:
        --------
        Dict[str, Any]
            Dictionary containing product details and metadata

        Raises:
        -------
        ValueError
            If product_id is invalid or product is not found
        """
        if not product_id:
            raise ValueError("Missing required parameter: product_id")

        if not re.match("^P[A-Z0-9]{5}$", product_id):
            raise ValueError("Invalid product_id format")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)
        
        # Find matching product
        matched_rows = df[df["product_id"] == product_id]

        if matched_rows.empty:
            raise ValueError(f"No product found with id={product_id}")

        row = matched_rows.iloc[0]
        
        return {
            "product_id": row["product_id"],
            "product_description": row["product_description"] if pd.notna(row["product_description"]) else ""
        }

    def get_product_description_from_image(
        self, 
        product_id: str, 
        s3_url: str, 
        summarize: bool = False
    ) -> Dict[str, Any]:
        """
        Analyzes a product image and returns its description.

        Parameters:
        -----------
        product_id : str
            Unique product identifier
        s3_url : str
            S3 path to the product image
        summarize : bool, optional
            Whether to return summarized description

        Returns:
        --------
        Dict[str, Any]
            Dictionary containing product description from image analysis

        Raises:
        -------
        ValueError
            If parameters are invalid or image analysis fails
        """
        if not product_id or not s3_url:
            raise ValueError("Missing required parameters")

        if not re.match("^P[A-Z0-9]{5}$", product_id):
            raise ValueError("Invalid product_id format")

        if not re.match("^s3://[a-z0-9.-]+/.*$", s3_url):
            raise ValueError("Invalid s3_url format")

        # Note: Actual image analysis would go here
        # This is a placeholder implementation
        return {
            "product_id": product_id,
            "image_url": s3_url,
            "description": "Sample product description from image analysis",
            "is_summarized": summarize
        }

    def get_inventory_status(
        self, 
        product_id: str, 
        marketplace_id: str, 
        include_forecasts: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieves inventory levels and status for a product.

        Parameters:
        -----------
        product_id : str
            Unique product identifier
        marketplace_id : str
            Marketplace identifier
        include_forecasts : bool, optional
            Whether to include inventory forecasts

        Returns:
        --------
        Dict[str, Any]
            Dictionary containing inventory status and optional forecasts

        Raises:
        -------
        ValueError
            If parameters are invalid or product not found
        """
        if not product_id or not marketplace_id:
            raise ValueError("Missing required parameters")

        if not re.match("^P[A-Z0-9]{5}$", product_id):
            raise ValueError("Invalid product_id format")

        if not re.match("^[A-Z]{2}[0-9]{3}$", marketplace_id):
            raise ValueError("Invalid marketplace_id format")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)
        
        # Find matching product
        matched_rows = df[
            (df["product_id"] == product_id) & 
            (df["marketplace_id"] == marketplace_id)
        ]

        if matched_rows.empty:
            raise ValueError(f"No product found with id={product_id} in marketplace={marketplace_id}")

        row = matched_rows.iloc[0]
        
        response = {
            "product_id": product_id,
            "marketplace_id": marketplace_id,
            "current_stock": int(row["product_inventory"]) if pd.notna(row["product_inventory"]) else 0
        }

        if include_forecasts:
            response.update({
                "forecast_30_days": {
                    "projected_stock": int(row["projected_stock"]) if pd.notna(row["projected_stock"]) else 0,
                    "restock_recommendation": row["restock_recommendation"] if pd.notna(row["restock_recommendation"]) else None
                }
            })

        return response

    def get_product_listing_status(
        self, 
        product_id: str, 
        marketplace_id: str, 
        include_history: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieves the current listing status based on the most recent update.

        Parameters:
        -----------
        product_id : str
            Unique 6-character product identifier starting with 'P'
        marketplace_id : str
            The marketplace identifier where the product is listed (e.g., 'US001')
        include_history : bool, optional
            If True, includes the status change history for the last 30 days (default: False)

        Returns:
        --------
        Dict[str, Any]
            Dictionary containing product_id, marketplace_id, current_status, and 
            optionally status_history if include_history is True

        Raises:
        -------
        ValueError
            If product_id or marketplace_id is invalid or product is not found
        """
        if not product_id or not marketplace_id:
            raise ValueError("Missing required parameters: product_id or marketplace_id")

        # Validate product_id format
        if not re.match("^P[A-Z0-9]{5}$", product_id):
            raise ValueError("Invalid product_id format. Must start with 'P' followed by 5 alphanumeric characters")

        # Validate marketplace_id format
        if not re.match("^[A-Z]{2}[0-9]{3}$", marketplace_id):
            raise ValueError("Invalid marketplace_id format. Must be 2 uppercase letters followed by 3 digits")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)
        
        # Find matching product
        matched_rows = df[
            (df["product_id"] == product_id) & 
            (df["marketplace_id"] == marketplace_id)
        ]

        if len(matched_rows) > 1:
            raise ValueError(
                f"Multiple records found for product_id={product_id} in marketplace={marketplace_id}"
            )

        if matched_rows.empty:
            raise ValueError(
                f"No product found with id={product_id} in marketplace={marketplace_id}"
            )

        row = matched_rows.iloc[0]
        
        response = {
            "product_id": row["product_id"],
            "marketplace_id": row["marketplace_id"],
            "current_status": row["listing_status_details"] if pd.notna(row["listing_status_details"]) else "",
        }

        # Add history if requested
        if include_history:
            history_df = df[
                (df["product_id"] == product_id) & 
                (df["marketplace_id"] == marketplace_id)
            ].sort_values("update_timestamp", ascending=False)
            
            response["status_history"] = history_df[
                ["update_timestamp", "listing_status_details"]
            ].to_dict("records")

        return response

    def process_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes the tool call to appropriate method based on tool name.

        Parameters:
        -----------
        tool_name : str
            Name of the tool to execute
        tool_input : Dict[str, Any]
            Input parameters for the tool

        Returns:
        --------
        Dict[str, Any]
            Response from the executed tool

        Raises:
        -------
        ValueError
            If tool_name is invalid
        """
        tool_map = {
            "get_product_price": self.get_product_price,
            "get_product_description": self.get_product_description,
            "get_product_description_from_image": self.get_product_description_from_image,
            "get_product_listing_status": self.get_product_listing_status,
            "get_inventory_status": self.get_inventory_status
        }

        if tool_name not in tool_map:
            raise ValueError(f"Invalid tool_name: {tool_name}")

        return tool_map[tool_name](**tool_input)


if __name__ == "__main__":
    product_manager = ProductListingManager()
    
    ######################## Unit tests for API - get_product_price ########################
    print("=" * 25)
    print("Invalid test case 1 for API - get_product_price")
    try:
        invalid_response = product_manager.get_product_price(
<<<<<<< Updated upstream
            product_id="",
            marketplace_id=""
=======
            product_id="", 
            email_id=""
>>>>>>> Stashed changes
        )
    except ValueError as e:
        print(f"Expected error: {str(e)}")

    print("=" * 25)
    print("Invalid test case 2 for API - get_product_price")
    try:
        invalid_response = product_manager.get_product_price(
<<<<<<< Updated upstream
            product_id="INVALID",
            marketplace_id="US001"
=======
            product_id="INVALID", 
            email_id="E1011"
>>>>>>> Stashed changes
        )
    except ValueError as e:
        print(f"Expected error: {str(e)}")

    print("=" * 25)
    print("Valid test case for API - get_product_price")
    try:
        valid_response = product_manager.get_product_price(
<<<<<<< Updated upstream
            product_id="P91Z2A",
            marketplace_id="US001"
=======
            product_id="P91Z2A", 
            email_id="E1013"
>>>>>>> Stashed changes
        )
        print(f"Valid response: {valid_response}")
    except ValueError as e:
        print(f"Unexpected error: {str(e)}")

    ######################## Unit tests for API - get_product_description ########################
    print("=" * 25)
    print("Invalid test case 1 for API - get_product_description")
    try:
        invalid_response = product_manager.get_product_description(
<<<<<<< Updated upstream
            product_id=""
=======
            product_id="", 
            email_id=""
>>>>>>> Stashed changes
        )
    except ValueError as e:
        print(f"Expected error: {str(e)}")

    print("=" * 25)
    print("Invalid test case 2 for API - get_product_description")
    try:
        invalid_response = product_manager.get_product_description(
<<<<<<< Updated upstream
            product_id="INVALID"
=======
            product_id="INVALID", 
            email_id="E1011"
>>>>>>> Stashed changes
        )
    except ValueError as e:
        print(f"Expected error: {str(e)}")

    print("=" * 25)
    print("Valid test case for API - get_product_description")
    try:
        valid_response = product_manager.get_product_description(
<<<<<<< Updated upstream
            product_id="P23B4C"
=======
            product_id="P23B4C", 
            email_id="E1014"
>>>>>>> Stashed changes
        )
        print(f"Valid response: {valid_response}")
    except ValueError as e:
        print(f"Unexpected error: {str(e)}")

<<<<<<< Updated upstream
    ######################## Unit tests for API - get_product_listing_status ########################
    print("=" * 25)
    print("Invalid test case 1 for API - get_product_listing_status")
    try:
        invalid_response = product_manager.get_product_listing_status(
            product_id="",
            marketplace_id=""
=======
    ######################## Unit tests for API - get_product_description ########################
    print("=" * 25)
    print("Invalid test case 1 for API - get_product_description")
    try:
        invalid_response = product_manager.get_product_listing_status(
            product_id="", 
            email_id=""
>>>>>>> Stashed changes
        )
    except ValueError as e:
        print(f"Expected error: {str(e)}")

    print("=" * 25)
<<<<<<< Updated upstream
    print("Invalid test case 2 for API - get_product_listing_status")
    try:
        invalid_response = product_manager.get_product_listing_status(
            product_id="INVALID",
            marketplace_id="US001"
=======
    print("Invalid test case 2 for API - get_product_description")
    try:
        invalid_response = product_manager.get_product_listing_status(
            product_id="INVALID", 
            email_id="E1011"
>>>>>>> Stashed changes
        )
    except ValueError as e:
        print(f"Expected error: {str(e)}")

    print("=" * 25)
<<<<<<< Updated upstream
    print("Valid test case for API - get_product_listing_status")
    try:
        valid_response = product_manager.get_product_listing_status(
            product_id="P78X9Y",
            marketplace_id="US001"
=======
    print("Valid test case for API - get_product_description")
    try:
        valid_response = product_manager.get_product_listing_status(
            product_id="P78X9Y", 
            email_id="E1012"
>>>>>>> Stashed changes
        )
        print(f"Valid response: {valid_response}")
    except ValueError as e:
        print(f"Unexpected error: {str(e)}")
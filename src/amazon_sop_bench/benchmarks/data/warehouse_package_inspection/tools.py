# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

import os
import json
import pandas as pd
import logging
import uuid
import re
from datetime import datetime
from typing import Any, Dict, List, Union, Optional
from enum import Enum

class ProblemType(Enum):
    UNCONFIRMED_QUANTITY = "Unconfirmed Quantity"
    CANCELLED_QUANTITY = "Cancelled Quantity"
    OVERAGE_QUANTITY = "Overage Quantity"
    WRONG_WAREHOUSE = "Wrong Warehouse"
    VENDOR_DAMAGED = "Vendor Damaged"
    WRONG_ITEM = "Wrong Item"
    UNDERAGE_QUANTITY = "Underage Quantity"
    SEVERE_UNMATCHED_QUANTITY = "Severe Unmatched Quantity"

class WarehousePackageInspectionManager:

    DATASET_CSV_FILE = "test_set_with_outputs.csv"
    TOOLSPEC_JSON_FILE = "toolspecs.json"

    def __init__(self):
        """
        Initializes the WarehousePackageInspectionManager instance.

        This constructor sets up file paths for the dataset CSV file and toolspec JSON file
        relative to the current file location. It also loads the tool specifications into memory
        for later tool execution.
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

    def assessPackageCondition(
        self, po_number: str, package_image_path: str
    ) -> Dict[str, Union[str, List[str]]]:
        """
        Evaluates the physical condition of received packages using damage detection algorithm.
        
        Args:
            po_number (str): Purchase order number associated with the shipment being assessed
            package_image_path (str): File system path to the package image analyzed for damage
            
        Returns:
            Dict[str, Union[str, List[str]]]: Contains package condition assessment and problem types
            
        Raises:
            ValueError: If input parameters are invalid
            FileNotFoundError: If image file doesn't exist
        """
        logging.info(f"Assessing package condition for PO: {po_number}")
        
        # Input validation
        if not po_number or not isinstance(po_number, str):
            raise ValueError("Invalid PO number")
        if not package_image_path or not isinstance(package_image_path, str):
            raise ValueError("Invalid image path")

        try:
            # Use deterministic logic for testing (based on PO number)
            damage_detected = (int(po_number[2:]) % 3 == 0)
            
            if damage_detected:
                return {
                    "package_condition": "damaged",
                    "problem_type": ["Vendor Damaged"]
                }
            else:
                return {
                    "package_condition": "intact",
                    "problem_type": []
                }
                
        except Exception as e:
            logging.error(f"Image processing error: {str(e)}")
            raise ValueError(f"Failed to process package image: {str(e)}")

    def calculateChargeback(
        self,
        po_number: str,
        problem_type: List[str],
        ordered_quantity: int,
        received_quantity: int,
        unit_cost: float
    ) -> Dict[str, Union[bool, float]]:
        """
        Calculates vendor chargeback amounts based on identified shipment problems.
        
        Args:
            po_number: Purchase order number for the shipment
            problem_type: Array of identified problems with the shipment
            ordered_quantity: Number of units originally ordered on the PO
            received_quantity: Actual number of units received at warehouse
            unit_cost: Cost per unit for chargeback calculation
        
        Returns:
            Dict containing chargeable status and charge amount
        
        Raises:
            ValueError: For invalid inputs or calculation errors
        """
        try:
            # Input validation
            if not isinstance(problem_type, list):
                raise ValueError("Problem type must be a list")
            
            if ordered_quantity < 0 or received_quantity < 0:
                raise ValueError("Quantities cannot be negative")
                
            if unit_cost <= 0:
                raise ValueError("Unit cost must be positive")

            # Initialize charge amount
            total_charge = 0.0
            
            # Convert problem types to set for unique values
            unique_problems = set(problem_type)
            
            # Process each problem type
            for problem in unique_problems:
                try:
                    problem_enum = ProblemType(problem)
                except ValueError:
                    raise ValueError(f"Invalid problem type: {problem}")
                    
                if problem_enum == ProblemType.WRONG_ITEM:
                    # Charge for all received items
                    total_charge += received_quantity * unit_cost
                    
                elif problem_enum in [ProblemType.UNCONFIRMED_QUANTITY, 
                                    ProblemType.CANCELLED_QUANTITY]:
                    # Charge for missing quantity
                    if ordered_quantity > received_quantity:
                        total_charge += (ordered_quantity - received_quantity) * unit_cost
                        
                elif problem_enum == ProblemType.VENDOR_DAMAGED:
                    # Charge for damaged items
                    total_charge += received_quantity * unit_cost
                    
                elif problem_enum == ProblemType.WRONG_WAREHOUSE:
                    # Charge handling fee (10% of total value)
                    total_charge += received_quantity * unit_cost * 0.1
            
            # Round to 2 decimal places
            total_charge = round(total_charge, 2)
            
            return {
                "chargeable": total_charge > 0,
                "charge_amount": total_charge
            }
            
        except Exception as e:
            logging.error(f"Chargeback calculation error for PO {po_number}: {str(e)}")
            raise ValueError(f"Chargeback calculation error: {str(e)}")

    def calculateQuantityVariance(
        self,
        po_number: str,
        ordered_quantity: int,
        confirmed_quantity: int,
        received_quantity: int,
        QVT: float = 5.0
    ) -> Dict[str, Union[float, List[str], bool]]:
        """
        Calculates quantity variance between ordered, confirmed, and received quantities.
        
        Args:
            po_number: Purchase order number for the shipment
            ordered_quantity: Number of units originally ordered on the PO
            confirmed_quantity: Number of units confirmed by vendor before shipping
            received_quantity: Actual number of units received at warehouse
            QVT: Quantity Variance Threshold percentage (default 5.0)
        
        Returns:
            Dict containing quantity variance, problem types, and chargeable status
        
        Raises:
            ValueError: If quantities are negative or invalid
        """
        try:
            # Validate inputs
            if any(q < 0 for q in [ordered_quantity, confirmed_quantity, received_quantity]):
                raise ValueError("Quantities cannot be negative")
            
            problems = []
            
            # Handle cancelled quantity case
            if confirmed_quantity == 0:
                return {
                    "quantity_variance": 0,
                    "problem_type": ["Cancelled Quantity"],
                    "chargeable": False
                }
            
            # Calculate quantity variance
            quantity_variance = ((received_quantity - confirmed_quantity) / confirmed_quantity * 100) if confirmed_quantity != 0 else 0
            
            # Identify quantity problems
            if received_quantity > ordered_quantity:
                problems.append("Overage Quantity")
            elif received_quantity < ordered_quantity:
                problems.append("Underage Quantity")
                
            # Check for severe variance
            if abs(quantity_variance) > QVT:
                problems.append("Severe Unmatched Quantity")
            
            # Determine if chargeable
            chargeable = len(problems) > 0 and "Overage Quantity" not in problems
            
            return {
                "quantity_variance": round(quantity_variance, 2),
                "problem_type": problems,
                "chargeable": chargeable
            }
            
        except Exception as e:
            logging.error(f"Error processing quantity variance for PO {po_number}: {str(e)}")
            raise ValueError(f"Quantity variance calculation error: {str(e)}")

    def generateProblemReport(
        self,
        po_number: str,
        vendor_id: str,
        vendor_name: str,
        problem_type: List[str],
        charge_amount: float = 0.0,
        resolution_status: str = "Pending"
    ) -> Dict[str, Union[str, dict]]:
        """
        Generates a comprehensive problem classification report for shipment issues.
        
        Args:
            po_number: Purchase order number associated with the shipment
            vendor_id: Unique identifier for the vendor
            vendor_name: Name of the shipping vendor
            problem_type: List of identified problems with the shipment
            charge_amount: Total chargeback amount calculated for the problems
            resolution_status: Current status of the problem resolution process
        
        Returns:
            Dictionary containing the complete problem report with multiple sections
        
        Raises:
            ValueError: If input validation fails
        """
        valid_problem_types = [p.value for p in ProblemType]
        valid_resolution_statuses = ["Pending", "Processing", "Resolved", "Returned to Vendor"]
        
        # Validate inputs
        if not all([po_number, vendor_id, vendor_name]):
            raise ValueError("Missing required parameters")
        
        if not all(prob in valid_problem_types for prob in problem_type):
            raise ValueError(f"Invalid problem type. Valid types: {valid_problem_types}")
            
        if resolution_status not in valid_resolution_statuses:
            raise ValueError(f"Invalid resolution status. Valid statuses: {valid_resolution_statuses}")
            
        if charge_amount < 0:
            raise ValueError("Charge amount cannot be negative")
            
        try:
            report_id = f"RPT-{uuid.uuid4().hex[:8]}"
            
            # Generate problem summary
            problem_summary = {
                "total_problems": len(problem_type),
                "unique_problems": len(set(problem_type)),
                "problems_breakdown": {p: problem_type.count(p) for p in set(problem_type)},
                "primary_issue": problem_type[0] if problem_type else "None"
            }
            
            # Generate chargeback details
            chargeback_details = {
                "chargeable": charge_amount > 0,
                "charge_amount": charge_amount,
                "charge_date": datetime.now().strftime("%Y-%m-%d"),
                "charge_reason": problem_type[0] if problem_type else "None"
            }
            
            # Generate resolution details and next steps based on problem types and status
            next_steps = []
            
            if "Wrong Item" in problem_type:
                next_steps.append("Initiate immediate return to vendor")
            if "Vendor Damaged" in problem_type:
                next_steps.append("Document damage with photos")
            if any(p.endswith("Quantity") for p in problem_type):
                next_steps.append("Reconcile quantity discrepancy")
            if resolution_status == "Pending":
                next_steps.append("Await vendor acknowledgment")
                
            resolution_details = {
                "current_status": resolution_status,
                "status_date": datetime.now().strftime("%Y-%m-%d"),
                "requires_return": "Wrong Item" in problem_type,
                "next_steps": next_steps
            }
            
            return {
                "report_id": report_id,
                "problem_summary": problem_summary,
                "chargeback_details": chargeback_details,
                "resolution_details": resolution_details
            }
                
        except Exception as e:
            logging.error(f"Error generating problem report for PO {po_number}: {str(e)}")
            raise ValueError(f"Failed to generate problem report: {str(e)}")

    def validateBarcode(
        self,
        po_number: str,
        confirmed_product_id: str,
        received_product_bar_code: str
    ) -> Dict[str, Union[bool, List[str], str]]:
        """
        Validates the received product barcode against the confirmed product ID.
        
        Args:
            po_number: Purchase order number associated with the shipment
            confirmed_product_id: 13-digit product identification code confirmed by vendor
            received_product_bar_code: File path to the barcode image of the received product
            
        Returns:
            Dict containing barcode match status, problem types, and resolution status
            
        Raises:
            ValueError: If inputs are invalid or barcode analysis fails
        """
        # Input validation
        if not po_number or not isinstance(po_number, str):
            raise ValueError("Invalid PO number")
        if not confirmed_product_id or not isinstance(confirmed_product_id, str):
            raise ValueError("Invalid product ID")
        if not received_product_bar_code or not isinstance(received_product_bar_code, str):
            raise ValueError("Invalid barcode image path")
            
        try:
            # Use deterministic logic for testing (based on PO number)
            barcode_match = (int(po_number[2:]) % 2 == 0)
                
            # If barcode doesn't match, it's a wrong item and should be returned
            if not barcode_match:
                return {
                    "barcode_match": False,
                    "problem_type": ["Wrong Item"],
                    "resolution_status": "Returned to Vendor"
                }
            else:
                return {
                    "barcode_match": True,
                    "problem_type": [],
                    "resolution_status": "Processing"
                }
                
        except Exception as e:
            logging.error(f"Error validating barcode for PO {po_number}: {str(e)}")
            raise ValueError(f"Barcode validation error: {str(e)}")

    def updateResolutionStatus(
        self,
        po_number: str,
        problem_type: List[str],
        current_status: str
    ) -> Dict[str, str]:
        """
        Updates the resolution status of a shipment based on identified problems and current status.
        
        Args:
            po_number: Purchase order number associated with the shipment
            problem_type: Array of identified problems for the shipment
            current_status: Current resolution status of the shipment
            
        Returns:
            Dict containing updated resolution status and timestamp
            
        Raises:
            ValueError: If inputs are invalid or status transition is not allowed
        """
        # Validate inputs
        if not po_number or not isinstance(po_number, str):
            raise ValueError("Invalid PO number")

        valid_problems = [p.value for p in ProblemType]
        valid_statuses = ["Pending", "Processing", "Resolved", "Returned to Vendor"]

        # Validate problem types
        if not all(prob in valid_problems for prob in problem_type):
            raise ValueError(f"Invalid problem type detected. Valid types: {valid_problems}")

        # Validate current status
        if current_status not in valid_statuses:
            raise ValueError(f"Invalid current status: {current_status}. Valid statuses: {valid_statuses}")

        try:
            # Determine new status based on problems
            new_status = current_status

            if "Wrong Item" in problem_type:
                new_status = "Returned to Vendor"
            elif len(problem_type) > 0:
                if current_status == "Pending":
                    new_status = "Processing"
                elif current_status == "Returned to Vendor":
                    raise ValueError(
                        "Cannot transition from 'Returned to Vendor' status"
                    )

            # Generate timestamp
            timestamp = datetime.now().isoformat()

            return {
                "resolution_status": new_status,
                "updated_at": timestamp
            }
            
        except Exception as e:
            logging.error(f"Error updating resolution status for PO {po_number}: {str(e)}")
            raise ValueError(f"Failed to update resolution status: {str(e)}")

    def verifyWarehouseLocation(
        self,
        po_number: str,
        intended_warehouse_id: str,
        actual_warehouse_id: str
    ) -> Dict[str, Union[bool, List[str]]]:
        """
        Validates whether a shipment was delivered to its intended warehouse location.
        
        Args:
            po_number: Purchase order number associated with the shipment
            intended_warehouse_id: ID of the warehouse where the shipment was supposed to be delivered
            actual_warehouse_id: ID of the warehouse where the shipment was actually delivered
            
        Returns:
            Dict containing location match status and problem types
            
        Raises:
            ValueError: If required parameters or warehouse ID formats are invalid
        """
        # Validate input parameters
        if not all([po_number, intended_warehouse_id, actual_warehouse_id]):
            raise ValueError("All parameters are required")

        try:
            # Normalize warehouse IDs for comparison
            intended_warehouse_id = intended_warehouse_id.strip().upper()
            actual_warehouse_id = actual_warehouse_id.strip().upper()

            # Compare warehouse locations
            location_match = intended_warehouse_id == actual_warehouse_id
            problem_type = [] if location_match else ["Wrong Warehouse"]

            return {
                "location_match": location_match,
                "problem_type": problem_type
            }
            
        except Exception as e:
            logging.error(f"Error verifying warehouse location for PO {po_number}: {str(e)}")
            raise ValueError(f"Warehouse location verification error: {str(e)}")

    def process_tool_call(self, tool_name, tool_input):
        """
        Processes a tool call dynamically based on the tool name and input provided.

        This method acts as a router to dispatch execution to the appropriate warehouse
        receiving tool function based on the tool name. It parses and validates the inputs,
        calls the appropriate method, and returns the corresponding output.

        Parameters:
        -----------
        tool_name : str
            Name of the warehouse receiving tool to execute
        tool_input : Dict[str, Any]
            Dictionary containing the required input parameters for the specified tool.

        Returns:
        --------
        Any
            Output generated by the corresponding tool execution.

        Raises:
        -------
        ValueError
            If the `tool_name` is invalid or does not correspond to any supported tool.
        """
        if tool_name == "assessPackageCondition":
            return self.assessPackageCondition(**tool_input)
        elif tool_name == "calculateChargeback":
            return self.calculateChargeback(**tool_input)
        elif tool_name == "calculateQuantityVariance":
            return self.calculateQuantityVariance(**tool_input)
        elif tool_name == "generateProblemReport":
            return self.generateProblemReport(**tool_input)
        elif tool_name == "validateBarcode":
            return self.validateBarcode(**tool_input)
        elif tool_name == "updateResolutionStatus":
            return self.updateResolutionStatus(**tool_input)
        elif tool_name == "verifyWarehouseLocation":
            return self.verifyWarehouseLocation(**tool_input)
        else:
            raise ValueError(f"Invalid tool_name: {tool_name}")

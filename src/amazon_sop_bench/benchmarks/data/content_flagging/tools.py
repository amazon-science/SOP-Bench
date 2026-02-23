# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

from typing import Dict, List, Union, Optional, Any
import json, os, math, random
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

class ContentFlaggingManager:

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


    def calculate_device_consistency(self, device_type: str, os: str, browser: str) -> float:

        """
        Calculate device consistency score based on device information
        """

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)
        
        # Find matching business
        matched_rows = df[(df['device_type'] == device_type) & (df['os'] == os) & (df['browser'] == browser)]

        consistency_score = random.random()
                    
        return round(consistency_score, 2)
    
    def calculateBotProbabilityIndex(self,
            userid: str,
            is_possible_bot: float,
            Captcha_tries: int,
            device_type: str,
            os: str,
            browser: str
        ) -> Dict[str, Union[float, List[str]]]:
        """
        Calculate Bot Probability Index based on user behavior and device metrics
        
        Args:
            userid: Unique user identifier
            is_possible_bot: Float between 0-1 indicating initial bot probability
            Captcha_tries: Number of captcha attempts (0-5)
            device_type: Type of device used
            operating_system: Operating system of device
            browser: Browser used
            
        Returns:
            Dictionary containing bot_probability_index, device_consistency_score, and risk_flags
        
        Raises:
            InvalidUserIDError: If userid is invalid
            MissingDataError: If required fields are missing
        """
        if userid is None or is_possible_bot is None or Captcha_tries is None or device_type is None or os is None or browser is None:
            raise ValueError("Missing one or more required parameters")
        
        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        matched_rows = df[
            (df['userid'] == userid) &
            (df['is_possible_bot'] == is_possible_bot) &
            (df['Captcha_tries'] == Captcha_tries) &
            (df['device_type'] == device_type) &
            (df['os'] == os) &
            (df['browser'] == browser)
        ]

        if matched_rows.empty:
            raise ValueError("No matching data found")
            
        row = matched_rows.iloc[0]

        userid = row['userid']
        is_possible_bot = row['is_possible_bot']
        Captcha_tries = row['Captcha_tries']
        device_type = row['device_type']
        os = row['os']
        browser = row['browser']

        # Initialize variables
        bpi = random.random()
        
        # Calculate device consistency
        device_consistency_score = self.calculate_device_consistency(device_type, os, browser)
        
        # Adjust BPI based on device consistency
        if device_consistency_score < 0.5:
            bpi = min(1.0, bpi + 0.2)
            
        
        return {
            "bot_probability_index": round(bpi, 2),
            "device_consistency_score": device_consistency_score
        }


    
    def calculateContentSeverityIndex(self,
        content_id: str,
        PrimaryViolationType: str,
        SecondaryViolationType: str,
        PrimaryViolation_Confidence: float,
        SecondaryViolation_Confidence: float
        ) -> int:
        """
        Calculate content severity index based on violation analysis.
        
        Args:
            content_id: Unique identifier for content
            PrimaryViolationType: Main violation category
            SecondaryViolationType: Secondary violation category
            PrimaryViolation_Confidence: Confidence score (0-100) for primary violation
            SecondaryViolation_Confidence: Confidence score (0-100) for secondary violation
        
        Returns:
            Dict containing content_severity_index and violation_analysis
        
        Raises:
            ValidationError: If input parameters are invalid
        """
    
        # Violation type weights
        VIOLATION_WEIGHTS = {
            'hate_speech': 1.0,
            'spam': 0.6,
            'violence': 0.9,
            'adult_content': 0.7,
            'copyright': 0.5,
            'misinformation': 0.8,
            'bot_activity': 0.7,
            'self_harm': 1.0,
            'discrimination': 0.9,
            'harassment': 0.8
        }
        
        # Validate inputs
        if content_id is None or PrimaryViolationType is None or SecondaryViolationType is None or PrimaryViolation_Confidence is None or SecondaryViolation_Confidence is None:
            raise ValueError("Missing one or more required parameters")
        
        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        matched_rows = df[
            (df['content_id'] == content_id) &
            (df['PrimaryViolationType'] == PrimaryViolationType) &
            (df['SecondaryViolationType'] == SecondaryViolationType) &
            (df['PrimaryViolation_Confidence'] == PrimaryViolation_Confidence) &
            (df['SecondaryViolation_Confidence'] == SecondaryViolation_Confidence)
        ]

        if matched_rows.empty:
            raise ValueError("No matching business record found")
            
        row = matched_rows.iloc[0]

        content_id = row['content_id']
        PrimaryViolationType = row['PrimaryViolationType']
        SecondaryViolationType = row['SecondaryViolationType']
        PrimaryViolation_Confidence = row['PrimaryViolation_Confidence']
        SecondaryViolation_Confidence = row['SecondaryViolation_Confidence']

        # Calculate primary score
        primary_score = (
            VIOLATION_WEIGHTS[PrimaryViolationType] * 
            (PrimaryViolation_Confidence / 100)
        ) * 100
        
        # Calculate secondary score
        secondary_score = 0
        if SecondaryViolationType and SecondaryViolation_Confidence > 0:
            secondary_score = (
                VIOLATION_WEIGHTS[SecondaryViolationType] * 
                (SecondaryViolation_Confidence / 100)
            ) * 100
            
            # Apply correlation multiplier if violations are related
            if PrimaryViolationType == SecondaryViolationType:
                secondary_score *= 1.2
        
        # Calculate composite score
        composite_score = (primary_score * 0.7) + (secondary_score * 0.3)
        
        # Normalize final score to 0-100 range
        content_severity_index = min(round(composite_score), 100)
        
        return content_severity_index
    
    def calculate_user_trust_score(self,
        userid: str,
        NumberofPreviousPosts: int,
        CountofFlaggedPosts: int,
        Latitude: float,
        Longitude: float,
        bot_probability_index: float,
        device_consistency_score: float
        ) -> int:

        """
        Calculate user trust score based on multiple factors as per SOP requirements.

        Args:
            userid: Unique identifier for the user
            NumberofPreviousPosts: Total number of user's previous posts
            CountofFlaggedPosts: Number of user's flagged posts
            Latitude: Geographic latitude
            Longitude: Geographic longitude
            bot_probability_index: Bot probability score (0-1)
            device_consistency_score: Device consistency score (0-1)
        
        Always returns an integer trust score between 0-100.
        """
        # Validate inputs
        if userid is None or NumberofPreviousPosts is None or CountofFlaggedPosts is None or Latitude is None or Longitude is None or bot_probability_index is None or device_consistency_score is None:
            raise ValueError("Missing one or more required parameters")
        
        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        matched_rows = df[
            (df['userid'] == userid) &
            (df['NumberofPreviousPosts'] == NumberofPreviousPosts) &
            (df['CountofFlaggedPosts'] == CountofFlaggedPosts) &
            (df['Latitude'] == Latitude) &
            (df['Longitude'] == Longitude)
        ]

        if matched_rows.empty:
            raise ValueError("No matching business record found")
            
        row = matched_rows.iloc[0]

        userid = row['userid']
        NumberofPreviousPosts = row['NumberofPreviousPosts']
        CountofFlaggedPosts = row['CountofFlaggedPosts']
        Latitude = row['Latitude']
        Longitude = row['Longitude']
        # bot_probability_index and device_consistency_score are passed as parameters, not from CSV


        try:
            # Validate inputs
            if not (-90 <= Latitude <= 90) or not (-180 <= Longitude <= 180):
                raise ValueError("Invalid geographic coordinates")
            
            # Calculate base score
            base_score = 50
            
            # Apply post history modifiers
            post_history_score = min(NumberofPreviousPosts * 0.3, 30)
            flag_penalty = min(CountofFlaggedPosts * -0.5, -25)
            base_score += post_history_score + flag_penalty
            
            # Calculate geographic risk quotient
            grq = math.cos(math.radians(Latitude)) * math.cos(math.radians(Longitude))
            grq = abs(grq)  # Normalize to 0-1
            geographic_modifier = 1 - (grq * 0.2)  # Convert to modifier (0.8-1.0)
            
            # Calculate behavioral modifier
            bot_penalty = 1 - bot_probability_index
            device_bonus = device_consistency_score
            behavioral_modifier = (bot_penalty + device_bonus) / 2
            
            # Calculate final score
            user_trust_score = int(base_score * geographic_modifier * behavioral_modifier)
            user_trust_score = max(0, min(100, user_trust_score))  # Clamp between 0 and 100
            
            return user_trust_score
            
        except Exception as e:
            print(f"Error calculating trust score: {e}")
            return 25
        
        
        
    def determineFinalDecision(self,
        content_id: str,
        user_trust_score: int,
        content_severity_index: int,
        bot_probability_index: float,
        NumberofPreviousPosts: int,
        CountofFlaggedPosts: int
        ) -> str:
            """
            Determines final content disposition based on multiple factors.
            
            Args:
                content_id: Unique identifier for the content
                user_trust_score: Trust score (0-100)
                content_severity_index: Content severity score (0-100)
                bot_probability_index: Bot probability score (0-1)
                NumberofPreviousPosts: Total number of user's posts
                CountofFlaggedPosts: Number of user's flagged posts
            
            Returns:
                Dictionary containing final decision and decision factors
            
            Raises:
                ValidationError: If input parameters are invalid
            """
    
            # Input validation
            
            if content_id is None or user_trust_score is None or content_severity_index is None or bot_probability_index is None or NumberofPreviousPosts is None or CountofFlaggedPosts is None:
                raise ValueError("Missing one or more required parameters")
            
            # Load dataset
            df = pd.read_csv(self.dataset_file_path)

            matched_rows = df[
                (df['content_id'] == content_id) &
                (df['NumberofPreviousPosts'] == NumberofPreviousPosts) &
                (df['CountofFlaggedPosts'] == CountofFlaggedPosts)
            ]

            if matched_rows.empty:
                raise ValueError("No matching record found")
                
            row = matched_rows.iloc[0]

            content_id = row['content_id']
            NumberofPreviousPosts = row['NumberofPreviousPosts']
            CountofFlaggedPosts = row['CountofFlaggedPosts']
           
            # Validate score ranges
            if not (0 <= user_trust_score <= 100 and 
                    0 <= content_severity_index <= 100 and 
                    0 <= bot_probability_index <= 1):
                raise ValueError(f"scores out of range: {user_trust_score, content_severity_index, bot_probability_index}")
                

            # Calculate weights
            trust_weight = 0.35
            severity_weight = 0.40
            historical_weight = 0.25
            
            # Calculate historical factor (0-100)
            historical_factor = 100 * (1 - (CountofFlaggedPosts / max(NumberofPreviousPosts, 1)))
            
            # Bot probability modifier
            bot_modifier = 1 + (bot_probability_index * 0.5)  # Increases severity if bot likelihood is high
            
            # Calculate final score
            final_score = (
                (user_trust_score * trust_weight) +
                (content_severity_index * severity_weight * bot_modifier) +
                (historical_factor * historical_weight)
            )
            
            # Determine final decision
            if final_score > 80:
                final_decision = "user_banned"
            elif final_score > 60:
                final_decision = "removed"
            elif final_score > 40:
                final_decision = "warning"
            else:
                final_decision = "allowed"
            
            
            return final_decision
    
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
        if tool_name == "calculateBotProbabilityIndex":
            return self.calculateBotProbabilityIndex(**tool_input)
        elif tool_name == "calculateContentSeverityIndex":
            return self.calculateContentSeverityIndex(**tool_input)
        elif tool_name == "calculate_user_trust_score":
            return self.calculate_user_trust_score(**tool_input)
        elif tool_name == "determineFinalDecision":
            return self.determineFinalDecision(**tool_input)
        else:
            raise ValueError(f"Invalid tool_name: {tool_name}")
        
if __name__ == "__main__":
    # Initialize manager
    manager = ContentFlaggingManager()

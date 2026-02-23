# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

import os
import json
import pandas as pd
from typing import Any, Dict, List
import random


class VideoContentModerationSystemManager:
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
            random.shuffle(toolspec_json)
        self.tool_config = {"tools": toolspec_json}

    def validateVideo(self, video_id: str, video_path: str) -> Dict[str, Any]:
        """
        Validates video format and extracts technical metadata.

        Parameters:
        -----------
        video_id : str
            Unique identifier for the video
        video_path : str
            Path to the video file

        Returns:
        --------
        Dict[str, Any]
            Dictionary containing video validation results and metadata
        """
        if not video_id or not video_path:
            raise ValueError("Missing required parameters: video_id or video_path")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        # Find matching video record
        matched_rows = df[(df["video_id"] == video_id) & (df["video_path"] == video_path)]

        if len(matched_rows) > 1:
            raise ValueError(f"Multiple records found for video_id: {video_id}")

        if matched_rows.empty:
            raise ValueError(f"No record found for video_id: {video_id}")

        row = matched_rows.iloc[0]

        return {
            "video_id": row["video_id"],
            "format": row["format"],
            "duration_seconds": int(row["duration_seconds"]),
            "frame_rate": float(row["frame_rate"]),
            "resolution": row["resolution"],
            "region": row["region"],
            "video_language": row["video_language"],
            "uploader_id": row["uploader_id"],
            "uploader_history": row["uploader_history"],
            "upload_timestamp": row["upload_timestamp"],
            "metadata_tags": row["metadata_tags"],
        }

    def assignReviewer(self, video_id: str, video_language: str, region: str) -> Dict[str, str]:
        """
        Assigns a qualified reviewer to the video content.

        Parameters:
        -----------
        video_id : str
            Unique identifier for the video
        video_language : str
            Language of the video content
        region : str
            Region code for the video

        Returns:
        --------
        Dict[str, str]
            Dictionary containing video_id and assigned reviewer_id
        """
        if not video_id or not video_language or not region:
            raise ValueError("Missing required parameters: video_id, video_language, or region")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        # Find matching video record
        matched_rows = df[
            (df["video_id"] == video_id)
            & (df["video_language"] == video_language)
            & (df["region"] == region)
        ]

        if len(matched_rows) > 1:
            raise ValueError(f"Multiple records found for video_id: {video_id}")

        if matched_rows.empty:
            raise ValueError(f"No record found for video_id: {video_id}")

        row = matched_rows.iloc[0]

        return {"video_id": row["video_id"], "initial_reviewer_id": row["initial_reviewer_id"]}

    def getReview(self, video_id: str, initial_reviewer_id: str) -> Dict[str, Any]:
        """
        Fetches the review details for a given video and reviewer.

        Parameters:
        -----------
        video_id : str
            Unique identifier for the video
        initial_reviewer_id : str
            ID of the assigned reviewer

        Returns:
        --------
        Dict[str, Any]
            Dictionary containing review details
        """
        if not video_id or not initial_reviewer_id:
            raise ValueError("Missing required parameters: video_id or initial_reviewer_id")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        # Find matching review record
        matched_rows = df[
            (df["video_id"] == video_id) & (df["initial_reviewer_id"] == initial_reviewer_id)
        ]

        if len(matched_rows) > 1:
            raise ValueError(f"Multiple records found for video_id: {video_id}")

        if matched_rows.empty:
            raise ValueError(f"No record found for video_id: {video_id}")

        row = matched_rows.iloc[0]

        detected_categories = row["detected_categories"]
        confidence_scores = row["confidence_scores"]

        return {
            "video_id": row["video_id"],
            "initial_reviewer_id": row["initial_reviewer_id"],
            "detected_categories": detected_categories,
            "confidence_scores": confidence_scores,
        }

    def submitContentModeration(
        self,
        video_id: str,
        initial_reviewer_id: str,
    ) -> Dict[str, Any]:
        """
        Records initial content moderation findings.

        Parameters:
        -----------
        video_id : str
            Unique identifier for the video
        initial_reviewer_id : str
            ID of the reviewer
        review_notes : str
            Notes from the review
        detected_categories : List[str]
            List of detected content categories
        confidence_scores : List[float]
            Confidence scores for detected categories

        Returns:
        --------
        Dict[str, Any]
            Dictionary containing review submission results
        """
        if not all([video_id, initial_reviewer_id]):
            raise ValueError("Missing required parameters")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        # Find matching record
        matched_rows = df[
            (df["video_id"] == video_id) & (df["initial_reviewer_id"] == initial_reviewer_id)
        ]

        if len(matched_rows) > 1:
            raise ValueError(f"Multiple records found for video_id: {video_id}")

        if matched_rows.empty:
            raise ValueError(f"No record found for video_id: {video_id}")

        row = matched_rows.iloc[0]

        return {
            "video_id": row["video_id"],
            "moderator_id": row["moderator_id"] if not pd.isna(row["moderator_id"]) else None,
        }

    def implementModeration(self, video_id: str, moderator_id: str) -> Dict[str, Any]:
        """
        Implements final moderation decisions.

        Parameters:
        -----------
        video_id : str
            Unique identifier for the video
        moderator_id : str
            ID of the moderator

        Returns:
        --------
        Dict[str, Any]
            Dictionary containing moderation implementation results
        """
        if not video_id or not moderator_id:
            raise ValueError("Missing required parameters: video_id or moderator_id")

        # Load dataset
        df = pd.read_csv(self.dataset_file_path)

        # Find matching record
        matched_rows = df[(df["video_id"] == video_id) & (df["moderator_id"] == moderator_id)]

        if len(matched_rows) > 1:
            raise ValueError(f"Multiple records found for video_id: {video_id}")

        if matched_rows.empty:
            raise ValueError(f"No record found for video_id: {video_id}")

        row = matched_rows.iloc[0]
        return {
            "video_id": row["video_id"],
            "moderation_notes": row["moderation_notes"],
        }

    def detectHateSpeech(self, video_id: str, transcript: str) -> Dict[str, bool]:
        """
        Identifies presence of hate speech in video content.

        Parameters:
        -----------
        video_id : str
            Unique identifier for the video
        transcript : str
            Video transcript text

        Returns:
        --------
        Dict[str, bool]
            Hate speech detection results
        """
        pass

    def assessAgeRating(self, video_id: str, content_flags: List[str]) -> Dict[str, str]:
        """
        Determines appropriate age rating for content.

        Parameters:
        -----------
        video_id : str
            Unique identifier for the video
        content_flags : List[str]
            List of content warning flags

        Returns:
        --------
        Dict[str, str]
            Age rating assessment results
        """
        pass

    def detectExplicitContent(self, video_id: str) -> Dict[str, Any]:
        """
        Identifies explicit content in video.

        Parameters:
        -----------
        video_id : str
            Unique identifier for the video

        Returns:
        --------
        Dict[str, Any]
            Explicit content detection results
        """
        pass

    def generateContentWarnings(
        self, video_id: str, detected_issues: List[str]
    ) -> Dict[str, List[str]]:
        """
        Generates appropriate content warnings.

        Parameters:
        -----------
        video_id : str
            Unique identifier for the video
        detected_issues : List[str]
            List of detected content issues

        Returns:
        --------
        Dict[str, List[str]]
            Generated content warnings
        """
        pass

    def checkUserHistory(self, uploader_id: str) -> Dict[str, Any]:
        """
        Reviews uploader history for violations.

        Parameters:
        -----------
        uploader_id : str
            Unique identifier for the uploader

        Returns:
        --------
        Dict[str, Any]
            User history review results
        """
        pass

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
        """
        tool_mapping = {
            "validateVideo": self.validateVideo,
            "assignReviewer": self.assignReviewer,
            "getReview": self.getReview,
            "submitContentModeration": self.submitContentModeration,
            "implementModeration": self.implementModeration,
            "detectHateSpeech": self.detectHateSpeech,
            "assessAgeRating": self.assessAgeRating,
            "detectExplicitContent": self.detectExplicitContent,
            "generateContentWarnings": self.generateContentWarnings,
            "checkUserHistory": self.checkUserHistory,
        }
        if tool_name not in tool_mapping:
            raise ValueError(f"Invalid tool_name: {tool_name}")

        return tool_mapping[tool_name](**tool_input)


if __name__ == "__main__":
    moderation_system = VideoContentModerationSystemManager()

    # Test validateVideo
    print("Testing validateVideo...")
    try:
        result = moderation_system.validateVideo(
            video_id="vid_00002", video_path="/data/videos/vid_00002.mp4"
        )
        print("Success:", result)
    except Exception as e:
        print("Error:", str(e))

    # Test assignReviewer
    print("\nTesting assignReviewer...")
    try:
        result = moderation_system.assignReviewer(
            video_id="vid_00002", video_language="es", region="MX"
        )
        print("Success:", result)
    except Exception as e:
        print("Error:", str(e))

    # Test getReview
    print("\nTesting getReview...")
    try:
        result = moderation_system.getReview(video_id="vid_00002", initial_reviewer_id="rev_002")
        print("Success:", result)
    except Exception as e:
        print("Error:", str(e))

    # Test submitContentReview
    print("\nTesting submitContentModeration...")
    try:
        result = moderation_system.submitContentModeration(
            video_id="vid_00002", initial_reviewer_id="rev_002"
        )
        print("Success:", result)
    except Exception as e:
        print("Error:", str(e))

    # Test implementModeration
    print("\nTesting implementModeration...")
    try:
        result = moderation_system.implementModeration(video_id="vid_00002", moderator_id="mod_001")
        print("Success:", result)
    except Exception as e:
        print("Error:", str(e))

    # Test invalid cases
    print("\nTesting invalid cases...")

    # Invalid video_id
    try:
        moderation_system.validateVideo(
            video_id="invalid_id", video_path="/data/videos/invalid.mp4"
        )
    except Exception as e:
        print("Expected error for invalid video_id:", str(e))

    # Missing parameters
    try:
        moderation_system.assignReviewer(video_id="", video_language="", region="")
    except Exception as e:
        print("Expected error for missing parameters:", str(e))

    # Invalid reviewer_id
    try:
        moderation_system.getReview(video_id="vid_00001", initial_reviewer_id="invalid_reviewer")
    except Exception as e:
        print("Expected error for invalid reviewer_id:", str(e))

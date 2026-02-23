# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Configuration management for amazon-sop-bench."""

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


@dataclass
class Config:
    """
    Configuration for amazon-sop-bench with sensible defaults.
    
    All settings can be overridden via environment variables or programmatically.
    
    Attributes:
        aws_region: AWS region for Bedrock (default: us-west-2)
        aws_model_id: Bedrock model ID (default: Claude 3.5 Sonnet)
        aws_role_arn: Optional IAM role ARN for cross-account access
        temperature: LLM temperature for generation (default: 0.5)
        max_tokens: Maximum tokens for LLM responses (default: 8192)
        output_dir: Directory for saving results (default: ./results)
        save_traces: Whether to save execution traces (default: True)
        log_level: Logging level (default: INFO)
    """
    
    # AWS Settings
    aws_region: str = field(
        default_factory=lambda: os.getenv("AWS_REGION", "us-east-1")
    )
    aws_model_id: str = field(
        default_factory=lambda: os.getenv(
            "AWS_MODEL_ID", 
            "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        )
    )
    aws_role_arn: Optional[str] = field(
        default_factory=lambda: os.getenv("AWS_ROLE_ARN")
    )
    
    # Model Settings
    temperature: float = field(
        default_factory=lambda: float(os.getenv("TEMPERATURE", "0.5"))
    )
    max_tokens: int = field(
        default_factory=lambda: int(os.getenv("MAX_TOKENS", "8192"))
    )
    
    # Evaluation Settings
    output_dir: Path = field(
        default_factory=lambda: Path(os.getenv("OUTPUT_DIR", "./results"))
    )
    save_traces: bool = field(
        default_factory=lambda: os.getenv("SAVE_TRACES", "false").lower() == "true"
    )
    
    # Logging Settings
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )
    
    def __post_init__(self):
        """Ensure output directory exists and validate settings."""
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate temperature
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError(f"Temperature must be between 0 and 1, got {self.temperature}")
        
        # Validate max_tokens
        if self.max_tokens <= 0:
            raise ValueError(f"max_tokens must be positive, got {self.max_tokens}")
        
        # Validate log_level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}, got {self.log_level}")


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get or create the global configuration instance.
    
    Returns:
        Config: The global configuration object
        
    Example:
        >>> from amazon_sop_bench.config import get_config
        >>> config = get_config()
        >>> print(config.aws_region)
        us-west-2
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def set_config(config: Config) -> None:
    """
    Set the global configuration instance.
    
    Args:
        config: Configuration object to set as global
        
    Example:
        >>> from amazon_sop_bench.config import Config, set_config
        >>> custom_config = Config(temperature=0.7)
        >>> set_config(custom_config)
    """
    global _config
    _config = config


def reset_config() -> None:
    """Reset the global configuration to default values."""
    global _config
    _config = None

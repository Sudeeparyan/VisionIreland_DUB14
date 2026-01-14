"""Configuration management for Comic Audio Narrator backend"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # AWS Configuration
    aws_region: str = "us-west-2"
    aws_default_region: Optional[str] = None  # Fallback alias
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None

    @property
    def effective_aws_region(self) -> str:
        """Get the effective AWS region, checking both AWS_REGION and AWS_DEFAULT_REGION"""
        return self.aws_region or self.aws_default_region or "us-west-2"

    # Bedrock Configuration
    bedrock_model_id_vision: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    bedrock_model_id_analysis: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

    # Polly Configuration
    polly_engine: str = "neural"
    polly_output_format: str = "mp3"

    # S3 Configuration
    s3_bucket_name: str = "comic-audio-narrator-library"
    s3_storage_class: str = "INTELLIGENT_TIERING"

    # Local Storage Configuration
    local_storage_path: str = "./storage/audio"
    local_storage_quota_gb: int = 100

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

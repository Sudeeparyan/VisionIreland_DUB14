"""AWS SDK client initialization and management"""

import boto3
from typing import Optional
from .config import settings


class AWSClients:
    """Manages AWS service clients for Bedrock, Polly, and S3"""

    _instance: Optional["AWSClients"] = None
    _bedrock_client = None
    _polly_client = None
    _s3_client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def bedrock(self):
        """Get or create Bedrock client"""
        if self._bedrock_client is None:
            self._bedrock_client = boto3.client(
                "bedrock-runtime",
                region_name=settings.aws_region,
            )
        return self._bedrock_client

    @property
    def polly(self):
        """Get or create Polly client"""
        if self._polly_client is None:
            self._polly_client = boto3.client(
                "polly",
                region_name=settings.aws_region,
            )
        return self._polly_client

    @property
    def s3(self):
        """Get or create S3 client"""
        if self._s3_client is None:
            self._s3_client = boto3.client(
                "s3",
                region_name=settings.aws_region,
            )
        return self._s3_client

    def close(self):
        """Close all client connections"""
        if self._bedrock_client:
            self._bedrock_client.close()
        if self._polly_client:
            self._polly_client.close()
        if self._s3_client:
            self._s3_client.close()
        self._bedrock_client = None
        self._polly_client = None
        self._s3_client = None


# Global AWS clients instance
aws_clients = AWSClients()

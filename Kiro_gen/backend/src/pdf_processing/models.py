"""Data models for PDF processing module"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Panel:
    """Represents a single panel extracted from a comic PDF"""

    id: str
    sequence_number: int
    image_data: bytes
    image_format: str  # 'png' or 'jpeg'
    image_resolution: dict  # {'width': int, 'height': int}
    extracted_text: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ComicMetadata:
    """Metadata about the extracted comic"""

    title: str
    total_panels: int
    extracted_at: datetime
    image_quality: str  # 'high' or 'standard'
    author: Optional[str] = None

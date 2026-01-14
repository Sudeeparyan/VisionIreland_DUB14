"""Batch processing for large PDFs with queue management."""

from dataclasses import dataclass, field
from typing import List, Optional, Callable, Any
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BatchStatus(Enum):
    """Status of a batch processing job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BatchJob:
    """Represents a batch processing job."""
    id: str
    pdf_path: str
    status: BatchStatus = BatchStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_panels: int = 0
    processed_panels: int = 0
    error_message: Optional[str] = None
    results: List[Any] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'pdf_path': self.pdf_path,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_panels': self.total_panels,
            'processed_panels': self.processed_panels,
            'error_message': self.error_message,
            'results': self.results,
        }


class BatchProcessor:
    """Manages batch processing of large PDFs."""

    def __init__(self, max_concurrent_jobs: int = 3, batch_size: int = 10):
        """Initialize batch processor.
        
        Args:
            max_concurrent_jobs: Maximum concurrent jobs to process
            batch_size: Number of panels to process per batch
        """
        self.max_concurrent_jobs = max_concurrent_jobs
        self.batch_size = batch_size
        self.jobs: dict[str, BatchJob] = {}
        self.queue: List[str] = []
        self.active_jobs: set[str] = set()

    def submit_job(self, job_id: str, pdf_path: str, total_panels: int) -> BatchJob:
        """Submit a new batch job.
        
        Args:
            job_id: Unique job identifier
            pdf_path: Path to PDF file
            total_panels: Total number of panels in PDF
            
        Returns:
            BatchJob instance
        """
        job = BatchJob(
            id=job_id,
            pdf_path=pdf_path,
            total_panels=total_panels,
        )
        self.jobs[job_id] = job
        self.queue.append(job_id)
        logger.info(f"Submitted batch job {job_id} with {total_panels} panels")
        return job

    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Get job by ID."""
        return self.jobs.get(job_id)

    def get_job_status(self, job_id: str) -> Optional[BatchJob]:
        """Get job status.
        
        Returns the full BatchJob object for status checks.
        """
        return self.jobs.get(job_id)

    def start_job(self, job_id: str) -> bool:
        """Start processing a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job started, False if already processing or not found
        """
        if len(self.active_jobs) >= self.max_concurrent_jobs:
            return False

        job = self.jobs.get(job_id)
        if not job or job.status != BatchStatus.PENDING:
            return False

        job.status = BatchStatus.PROCESSING
        job.started_at = datetime.now()
        self.active_jobs.add(job_id)
        logger.info(f"Started processing batch job {job_id}")
        return True

    def update_progress(self, job_id: str, processed_panels: int) -> bool:
        """Update job progress.
        
        Args:
            job_id: Job identifier
            processed_panels: Number of panels processed so far
            
        Returns:
            True if updated, False if job not found
        """
        job = self.jobs.get(job_id)
        if not job:
            return False

        job.processed_panels = processed_panels
        return True

    def complete_job(self, job_id: str, results: List[Any]) -> bool:
        """Mark job as completed.
        
        Args:
            job_id: Job identifier
            results: Processing results
            
        Returns:
            True if completed, False if job not found
        """
        job = self.jobs.get(job_id)
        if not job:
            return False

        job.status = BatchStatus.COMPLETED
        job.completed_at = datetime.now()
        job.results = results
        self.active_jobs.discard(job_id)
        logger.info(f"Completed batch job {job_id}")
        return True

    def fail_job(self, job_id: str, error_message: str) -> bool:
        """Mark job as failed.
        
        Args:
            job_id: Job identifier
            error_message: Error description
            
        Returns:
            True if failed, False if job not found
        """
        job = self.jobs.get(job_id)
        if not job:
            return False

        job.status = BatchStatus.FAILED
        job.completed_at = datetime.now()
        job.error_message = error_message
        self.active_jobs.discard(job_id)
        logger.error(f"Failed batch job {job_id}: {error_message}")
        return True

    def get_next_job(self) -> Optional[str]:
        """Get next job to process from queue."""
        while self.queue:
            job_id = self.queue.pop(0)
            job = self.jobs.get(job_id)
            if job and job.status == BatchStatus.PENDING:
                return job_id
        return None

    def get_active_jobs(self) -> List[BatchJob]:
        """Get all active jobs."""
        return [self.jobs[job_id] for job_id in self.active_jobs if job_id in self.jobs]

    def get_all_jobs(self) -> List[BatchJob]:
        """Get all jobs."""
        return list(self.jobs.values())

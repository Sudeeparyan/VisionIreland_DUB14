"""Property-based tests for batch processing."""

import pytest
from hypothesis import given, strategies as st

from src.processing.batch_processor import BatchProcessor, BatchStatus


def job_id_strategy():
    """Generate valid job IDs."""
    return st.text(
        alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-',
        min_size=1,
        max_size=20
    )


class TestBatchProcessingProperties:
    """Property-based tests for BatchProcessor"""

    @given(
        job_id=job_id_strategy(),
        pdf_path=st.text(min_size=1, max_size=100),
        total_panels=st.integers(min_value=1, max_value=1000)
    )
    def test_submitted_job_is_retrievable(self, job_id, pdf_path, total_panels):
        """Submitted job can be retrieved with same data."""
        processor = BatchProcessor()
        processor.submit_job(job_id, pdf_path, total_panels)
        
        job = processor.get_job(job_id)
        assert job is not None
        assert job.id == job_id
        assert job.total_panels == total_panels

    @given(
        job_ids=st.lists(
            job_id_strategy(),
            min_size=1,
            max_size=10,
            unique=True
        )
    )
    def test_all_submitted_jobs_retrievable(self, job_ids):
        """All submitted jobs are retrievable."""
        processor = BatchProcessor()
        
        for job_id in job_ids:
            processor.submit_job(job_id, f"/path/{job_id}.pdf", 50)
        
        all_jobs = processor.get_all_jobs()
        assert len(all_jobs) == len(job_ids)
        
        for job_id in job_ids:
            assert processor.get_job(job_id) is not None

    @given(
        processed=st.integers(min_value=0, max_value=100),
        total=st.integers(min_value=1, max_value=100)
    )
    def test_progress_update_preserves_data(self, processed, total):
        """Progress updates preserve job data."""
        processor = BatchProcessor()
        processor.submit_job("job_1", "/path/test.pdf", total)
        processor.start_job("job_1")
        
        processor.update_progress("job_1", processed)
        
        job = processor.get_job("job_1")
        assert job.processed_panels == processed
        assert job.total_panels == total

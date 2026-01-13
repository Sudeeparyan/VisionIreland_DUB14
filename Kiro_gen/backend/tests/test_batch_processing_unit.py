"""Unit tests for batch processing."""

import pytest
from datetime import datetime

from src.processing.batch_processor import BatchProcessor, BatchStatus


class TestBatchProcessor:
    """Test suite for BatchProcessor"""

    @pytest.fixture
    def processor(self):
        """Create a BatchProcessor"""
        return BatchProcessor(max_concurrent_jobs=2, batch_size=10)

    def test_submit_job(self, processor):
        """Test submitting a batch job"""
        job = processor.submit_job("job_1", "/path/to/pdf.pdf", 50)
        
        assert job.id == "job_1"
        assert job.status == BatchStatus.PENDING
        assert job.total_panels == 50

    def test_get_job(self, processor):
        """Test retrieving a job"""
        processor.submit_job("job_1", "/path/to/pdf.pdf", 50)
        
        job = processor.get_job("job_1")
        assert job is not None
        assert job.id == "job_1"

    def test_get_job_status(self, processor):
        """Test getting job status"""
        processor.submit_job("job_1", "/path/to/pdf.pdf", 50)
        
        status = processor.get_job_status("job_1")
        assert status == "pending"

    def test_start_job(self, processor):
        """Test starting a job"""
        processor.submit_job("job_1", "/path/to/pdf.pdf", 50)
        
        result = processor.start_job("job_1")
        assert result is True
        assert processor.get_job_status("job_1") == "processing"

    def test_start_job_respects_concurrency_limit(self, processor):
        """Test that concurrent job limit is respected"""
        processor.submit_job("job_1", "/path/to/pdf1.pdf", 50)
        processor.submit_job("job_2", "/path/to/pdf2.pdf", 50)
        processor.submit_job("job_3", "/path/to/pdf3.pdf", 50)
        
        assert processor.start_job("job_1") is True
        assert processor.start_job("job_2") is True
        assert processor.start_job("job_3") is False

    def test_update_progress(self, processor):
        """Test updating job progress"""
        processor.submit_job("job_1", "/path/to/pdf.pdf", 50)
        processor.start_job("job_1")
        
        result = processor.update_progress("job_1", 25)
        assert result is True
        assert processor.get_job("job_1").processed_panels == 25

    def test_complete_job(self, processor):
        """Test completing a job"""
        processor.submit_job("job_1", "/path/to/pdf.pdf", 50)
        processor.start_job("job_1")
        
        results = [{"panel": 1}, {"panel": 2}]
        success = processor.complete_job("job_1", results)
        
        assert success is True
        job = processor.get_job("job_1")
        assert job.status == BatchStatus.COMPLETED
        assert job.results == results

    def test_fail_job(self, processor):
        """Test failing a job"""
        processor.submit_job("job_1", "/path/to/pdf.pdf", 50)
        processor.start_job("job_1")
        
        success = processor.fail_job("job_1", "PDF corrupted")
        
        assert success is True
        job = processor.get_job("job_1")
        assert job.status == BatchStatus.FAILED
        assert job.error_message == "PDF corrupted"

    def test_get_next_job(self, processor):
        """Test getting next job from queue"""
        processor.submit_job("job_1", "/path/to/pdf1.pdf", 50)
        processor.submit_job("job_2", "/path/to/pdf2.pdf", 50)
        
        next_job = processor.get_next_job()
        assert next_job == "job_1"

    def test_get_active_jobs(self, processor):
        """Test getting active jobs"""
        processor.submit_job("job_1", "/path/to/pdf1.pdf", 50)
        processor.submit_job("job_2", "/path/to/pdf2.pdf", 50)
        
        processor.start_job("job_1")
        
        active = processor.get_active_jobs()
        assert len(active) == 1
        assert active[0].id == "job_1"

    def test_get_all_jobs(self, processor):
        """Test getting all jobs"""
        processor.submit_job("job_1", "/path/to/pdf1.pdf", 50)
        processor.submit_job("job_2", "/path/to/pdf2.pdf", 50)
        
        all_jobs = processor.get_all_jobs()
        assert len(all_jobs) == 2

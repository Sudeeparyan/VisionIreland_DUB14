"""Integration tests for API endpoints."""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import json
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.main import app
from src.storage.library_manager import LibraryManager
from src.monitoring.cost_monitor import CostMonitor
from src.monitoring.metrics import MetricsCollector


class TestAPIIntegration:
    """Test API endpoints with mocked backend services."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def mock_app_state(self, temp_storage):
        """Mock app state with test dependencies."""
        
        # Create mock components
        library_manager = Mock(spec=LibraryManager)
        cost_monitor = Mock(spec=CostMonitor)
        metrics_collector = Mock(spec=MetricsCollector)
        
        # Mock pipeline orchestrator
        pipeline_orchestrator = Mock()
        batch_processor = Mock()
        pipeline_orchestrator.batch_processor = batch_processor
        
        # Set up app state
        app.state.library_manager = library_manager
        app.state.cost_monitor = cost_monitor
        app.state.metrics_collector = metrics_collector
        app.state.pipeline_orchestrator = pipeline_orchestrator
        
        return {
            "library_manager": library_manager,
            "cost_monitor": cost_monitor,
            "metrics_collector": metrics_collector,
            "pipeline_orchestrator": pipeline_orchestrator,
            "batch_processor": batch_processor
        }

    @pytest.fixture
    def client(self, mock_app_state):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_pdf_content(self):
        """Create sample PDF content for testing."""
        return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\nxref\n%%EOF\n"

    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Comic Audio Narrator API"
        assert "endpoints" in data

    def test_health_check(self, client, mock_app_state):
        """Test health check endpoint."""
        mock_app_state["metrics_collector"].get_current_timestamp.return_value = "2024-01-01T00:00:00"
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_upload_pdf_success(self, client, mock_app_state, sample_pdf_content):
        """Test successful PDF upload."""
        
        # Mock successful background processing setup
        mock_app_state["pipeline_orchestrator"].process_comic = AsyncMock()
        
        # Upload file
        files = {"file": ("test.pdf", sample_pdf_content, "application/pdf")}
        data = {"title": "Test Comic"}
        
        response = client.post("/api/upload", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        assert "job_id" in result
        assert result["message"] == "File uploaded successfully. Processing started."
        assert result["filename"] == "test.pdf"

    def test_upload_invalid_file_type(self, client, mock_app_state):
        """Test upload with invalid file type."""
        
        files = {"file": ("test.txt", b"not a pdf", "text/plain")}
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "File type not supported" in data["detail"]

    def test_upload_file_too_large(self, client, mock_app_state):
        """Test upload with file too large."""
        
        # Create large file content (over 50MB)
        large_content = b"x" * (51 * 1024 * 1024)
        files = {"file": ("large.pdf", large_content, "application/pdf")}
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "File too large" in data["detail"]

    def test_upload_empty_file(self, client, mock_app_state):
        """Test upload with empty file."""
        
        files = {"file": ("empty.pdf", b"", "application/pdf")}
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "File is empty" in data["detail"]

    def test_get_job_status_success(self, client, mock_app_state):
        """Test getting job status for existing job."""
        
        # Mock job info
        mock_job_info = Mock()
        mock_job_info.status = "processing"
        mock_job_info.panels_processed = 5
        mock_job_info.total_panels = 10
        mock_job_info.created_at = "2024-01-01T00:00:00"
        mock_job_info.updated_at = "2024-01-01T00:05:00"
        mock_job_info.error_message = None
        mock_job_info.result = None
        
        mock_app_state["batch_processor"].get_job_status.return_value = mock_job_info
        
        response = client.get("/api/jobs/test-job-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-123"
        assert data["status"] == "processing"
        assert data["progress"] == 50  # 5/10 * 100

    def test_get_job_status_not_found(self, client, mock_app_state):
        """Test getting job status for non-existent job."""
        
        mock_app_state["batch_processor"].get_job_status.return_value = None
        
        response = client.get("/api/jobs/nonexistent-job")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_cancel_job_success(self, client, mock_app_state):
        """Test cancelling a job."""
        
        mock_app_state["batch_processor"].cancel_job.return_value = True
        
        response = client.delete("/api/jobs/test-job-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-123"
        assert "cancelled successfully" in data["message"]

    def test_cancel_job_not_found(self, client, mock_app_state):
        """Test cancelling non-existent job."""
        
        mock_app_state["batch_processor"].cancel_job.return_value = False
        
        response = client.delete("/api/jobs/nonexistent-job")
        
        assert response.status_code == 404

    def test_list_jobs(self, client, mock_app_state):
        """Test listing jobs with pagination."""
        
        # Mock job list
        mock_jobs = [
            Mock(
                job_id="job1",
                status="completed",
                panels_processed=10,
                total_panels=10,
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:10:00"
            ),
            Mock(
                job_id="job2",
                status="processing",
                panels_processed=3,
                total_panels=8,
                created_at="2024-01-01T01:00:00",
                updated_at="2024-01-01T01:03:00"
            )
        ]
        
        mock_app_state["batch_processor"].list_jobs.return_value = mock_jobs
        
        response = client.get("/api/jobs?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 2
        assert data["pagination"]["total"] == 2

    def test_get_library_success(self, client, mock_app_state):
        """Test getting library items."""
        
        # Mock library items
        mock_items = [
            Mock(
                id="audio1",
                title="Comic 1",
                filename="comic1.mp3",
                upload_date="2024-01-01T00:00:00",
                duration=120.5,
                file_size=1024000,
                metadata={"characters": ["Hero", "Villain"], "scenes": ["City"]}
            ),
            Mock(
                id="audio2",
                title="Comic 2",
                filename="comic2.mp3",
                upload_date="2024-01-02T00:00:00",
                duration=95.2,
                file_size=800000,
                metadata={"characters": ["Wizard"], "scenes": ["Forest"]}
            )
        ]
        
        mock_app_state["library_manager"].get_library_index = AsyncMock(return_value=mock_items)
        
        response = client.get("/api/library")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        # Items are sorted by upload_date desc, so Comic 2 (2024-01-02) comes first
        assert data["items"][0]["title"] == "Comic 2"
        assert data["items"][0]["characters"] == ["Wizard"]

    def test_search_library(self, client, mock_app_state):
        """Test searching library."""
        
        # Mock search results
        mock_results = [
            Mock(
                id="audio1",
                title="Hero Comic",
                filename="hero.mp3",
                upload_date="2024-01-01T00:00:00",
                duration=120.5,
                file_size=1024000,
                metadata={"characters": ["Hero"], "scenes": ["City"]}
            )
        ]
        
        mock_app_state["library_manager"].search_library = AsyncMock(return_value=mock_results)
        
        response = client.get("/api/library/search?q=hero")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "hero" in data["items"][0]["title"].lower()

    def test_get_library_stats(self, client, mock_app_state):
        """Test getting library statistics."""
        
        # Mock library items for stats
        from datetime import datetime
        mock_items = [
            Mock(
                duration=120.0,
                file_size=1000000,
                upload_date=datetime(2024, 1, 1),
                metadata={"characters": ["Hero"], "scenes": ["City"]}
            ),
            Mock(
                duration=95.0,
                file_size=800000,
                upload_date=datetime(2024, 1, 2),
                metadata={"characters": ["Villain"], "scenes": ["Forest"]}
            )
        ]
        
        mock_app_state["library_manager"].get_library_index = AsyncMock(return_value=mock_items)
        
        response = client.get("/api/library/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 2
        assert data["total_duration_seconds"] == 215.0
        assert data["unique_characters"] == 2
        assert data["unique_scenes"] == 2

    def test_get_audio_metadata(self, client, mock_app_state):
        """Test getting audio metadata."""
        
        # Mock library item
        mock_item = Mock(
            id="audio123",
            title="Test Comic",
            filename="test.mp3",
            upload_date="2024-01-01T00:00:00",
            duration=120.0,
            file_size=1000000,
            metadata={"characters": ["Hero"]}
        )
        
        mock_app_state["library_manager"].get_library_index = AsyncMock(return_value=[mock_item])
        
        response = client.get("/api/audio/audio123/metadata")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "audio123"
        assert data["title"] == "Test Comic"

    def test_get_audio_metadata_not_found(self, client, mock_app_state):
        """Test getting metadata for non-existent audio."""
        
        mock_app_state["library_manager"].get_library_index = AsyncMock(return_value=[])
        
        response = client.get("/api/audio/nonexistent/metadata")
        
        assert response.status_code == 404

    def test_delete_audio_success(self, client, mock_app_state):
        """Test deleting audio file."""
        
        mock_app_state["library_manager"].delete_audio = AsyncMock(return_value=True)
        
        response = client.delete("/api/audio/audio123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["audio_id"] == "audio123"
        assert "deleted successfully" in data["message"]

    def test_delete_audio_not_found(self, client, mock_app_state):
        """Test deleting non-existent audio."""
        
        mock_app_state["library_manager"].delete_audio = AsyncMock(return_value=False)
        
        response = client.delete("/api/audio/nonexistent")
        
        assert response.status_code == 404

    def test_get_metrics(self, client, mock_app_state):
        """Test getting system metrics."""
        
        mock_metrics = {
            "timestamp": "2024-01-01T00:00:00",
            "job_summary": {
                "total_jobs": 5,
                "completed_jobs": 3,
                "failed_jobs": 1,
                "running_jobs": 1
            },
            "performance": {
                "avg_processing_time_seconds": 45.2,
                "avg_panels_per_second": 0.8
            }
        }
        
        mock_app_state["metrics_collector"].get_metrics = AsyncMock(return_value=mock_metrics)
        
        response = client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_summary"]["total_jobs"] == 5

    def test_get_costs(self, client, mock_app_state):
        """Test getting cost information."""
        
        mock_costs = {
            "summary": {
                "total_jobs": 5,
                "total_cost_usd": 12.45,
                "daily_cost_usd": 2.30,
                "monthly_cost_usd": 45.67
            },
            "service_breakdown": {
                "bedrock": {"total_cost_usd": 8.20},
                "polly": {"total_cost_usd": 3.15},
                "s3": {"total_cost_usd": 1.10}
            }
        }
        
        mock_app_state["cost_monitor"].get_cost_summary = AsyncMock(return_value=mock_costs)
        
        response = client.get("/costs")
        
        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["total_cost_usd"] == 12.45

    def test_service_unavailable_errors(self, client):
        """Test endpoints when services are unavailable."""
        
        # Clear app state to simulate unavailable services
        app.state.library_manager = None
        app.state.cost_monitor = None
        app.state.metrics_collector = None
        app.state.pipeline_orchestrator = None
        
        # Test endpoints that require services
        response = client.get("/api/library")
        assert response.status_code == 503
        
        response = client.get("/metrics")
        assert response.status_code == 503
        
        response = client.get("/costs")
        assert response.status_code == 503
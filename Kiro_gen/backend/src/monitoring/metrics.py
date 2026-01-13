"""Metrics collection and monitoring for Comic Audio Narrator."""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import time
import psutil
import threading

logger = logging.getLogger(__name__)


@dataclass
class JobMetrics:
    """Metrics for a specific job."""
    job_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed
    
    # Processing metrics
    panels_processed: int = 0
    total_panels: int = 0
    processing_time_seconds: float = 0.0
    
    # API metrics
    bedrock_api_calls: int = 0
    bedrock_response_time_ms: List[float] = field(default_factory=list)
    polly_api_calls: int = 0
    polly_response_time_ms: List[float] = field(default_factory=list)
    s3_api_calls: int = 0
    s3_response_time_ms: List[float] = field(default_factory=list)
    
    # Error metrics
    errors: List[Dict[str, Any]] = field(default_factory=list)
    retries: int = 0
    
    # Quality metrics
    audio_duration_seconds: float = 0.0
    audio_file_size_bytes: int = 0
    character_count: int = 0


@dataclass
class SystemMetrics:
    """System-level metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_percent: float
    disk_used_gb: float
    active_jobs: int
    queue_size: int


class MetricsCollector:
    """Collects and aggregates metrics for monitoring and optimization."""
    
    def __init__(self, max_history_hours: int = 24):
        """Initialize metrics collector.
        
        Args:
            max_history_hours: Maximum hours of metrics to keep in memory
        """
        self.max_history_hours = max_history_hours
        self.job_metrics: Dict[str, JobMetrics] = {}
        self.system_metrics: deque = deque(maxlen=max_history_hours * 60)  # 1 per minute
        
        # Performance tracking
        self.api_response_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.throughput_metrics = defaultdict(list)
        
        # System monitoring
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Start system monitoring
        self.start_system_monitoring()

    def start_system_monitoring(self) -> None:
        """Start background system monitoring."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._system_monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Started system metrics monitoring")

    def stop_system_monitoring(self) -> None:
        """Stop background system monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Stopped system metrics monitoring")

    def _system_monitor_loop(self) -> None:
        """Background loop for collecting system metrics."""
        while self._monitoring:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Count active jobs
                active_jobs = len([j for j in self.job_metrics.values() if j.status == "running"])
                
                metrics = SystemMetrics(
                    timestamp=datetime.now(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_used_mb=memory.used / (1024 * 1024),
                    disk_percent=disk.percent,
                    disk_used_gb=disk.used / (1024 * 1024 * 1024),
                    active_jobs=active_jobs,
                    queue_size=0  # Would need to get from batch processor
                )
                
                self.system_metrics.append(metrics)
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
            
            # Sleep for 60 seconds
            time.sleep(60)

    async def start_job_tracking(self, job_id: str) -> None:
        """Start metrics tracking for a job."""
        self.job_metrics[job_id] = JobMetrics(
            job_id=job_id,
            started_at=datetime.now()
        )
        logger.debug(f"Started metrics tracking for job {job_id}")

    async def update_job_progress(self, job_id: str, panels_processed: int, total_panels: int) -> None:
        """Update job progress metrics."""
        if job_id not in self.job_metrics:
            await self.start_job_tracking(job_id)
        
        metrics = self.job_metrics[job_id]
        metrics.panels_processed = panels_processed
        metrics.total_panels = total_panels

    async def track_api_call(
        self,
        job_id: str,
        service: str,
        response_time_ms: float,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Track API call metrics."""
        if job_id not in self.job_metrics:
            await self.start_job_tracking(job_id)
        
        metrics = self.job_metrics[job_id]
        
        # Update service-specific metrics
        if service == "bedrock":
            metrics.bedrock_api_calls += 1
            metrics.bedrock_response_time_ms.append(response_time_ms)
        elif service == "polly":
            metrics.polly_api_calls += 1
            metrics.polly_response_time_ms.append(response_time_ms)
        elif service == "s3":
            metrics.s3_api_calls += 1
            metrics.s3_response_time_ms.append(response_time_ms)
        
        # Track errors
        if not success and error:
            metrics.errors.append({
                "service": service,
                "error": error,
                "timestamp": datetime.now().isoformat(),
                "response_time_ms": response_time_ms
            })
            self.error_counts[service] += 1
        
        # Update global response time tracking
        self.api_response_times[service].append(response_time_ms)
        
        # Keep only recent response times (last 1000)
        if len(self.api_response_times[service]) > 1000:
            self.api_response_times[service] = self.api_response_times[service][-1000:]

    async def track_retry(self, job_id: str, service: str, attempt: int) -> None:
        """Track retry attempts."""
        if job_id not in self.job_metrics:
            await self.start_job_tracking(job_id)
        
        metrics = self.job_metrics[job_id]
        metrics.retries += 1
        
        logger.debug(f"Retry tracked for job {job_id}, service {service}, attempt {attempt}")

    async def complete_job_tracking(self, job_id: str, result: Dict[str, Any]) -> None:
        """Complete metrics tracking for a job."""
        if job_id not in self.job_metrics:
            logger.warning(f"Job {job_id} not found in metrics tracking")
            return
        
        metrics = self.job_metrics[job_id]
        metrics.completed_at = datetime.now()
        metrics.status = "completed"
        
        # Calculate processing time
        if metrics.started_at:
            metrics.processing_time_seconds = (
                metrics.completed_at - metrics.started_at
            ).total_seconds()
        
        # Extract quality metrics from result
        if result:
            metrics.audio_duration_seconds = result.get('audio_duration', 0.0)
            metrics.audio_file_size_bytes = result.get('file_size', 0)
            metrics.character_count = result.get('character_count', 0)
        
        # Update throughput metrics
        if metrics.processing_time_seconds > 0:
            panels_per_second = metrics.panels_processed / metrics.processing_time_seconds
            self.throughput_metrics['panels_per_second'].append(panels_per_second)
        
        logger.info(f"Completed metrics tracking for job {job_id}")

    async def error_job_tracking(self, job_id: str, error: str) -> None:
        """Mark job as failed in metrics tracking."""
        if job_id not in self.job_metrics:
            logger.warning(f"Job {job_id} not found in metrics tracking")
            return
        
        metrics = self.job_metrics[job_id]
        metrics.completed_at = datetime.now()
        metrics.status = "failed"
        
        # Add error to metrics
        metrics.errors.append({
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "fatal": True
        })
        
        logger.info(f"Error tracked for job {job_id}: {error}")

    async def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        now = datetime.now()
        
        # Job metrics summary
        total_jobs = len(self.job_metrics)
        completed_jobs = len([j for j in self.job_metrics.values() if j.status == "completed"])
        failed_jobs = len([j for j in self.job_metrics.values() if j.status == "failed"])
        running_jobs = len([j for j in self.job_metrics.values() if j.status == "running"])
        
        # Performance metrics
        avg_processing_time = 0.0
        avg_panels_per_second = 0.0
        
        completed_job_metrics = [j for j in self.job_metrics.values() if j.status == "completed"]
        if completed_job_metrics:
            avg_processing_time = sum(j.processing_time_seconds for j in completed_job_metrics) / len(completed_job_metrics)
        
        if self.throughput_metrics['panels_per_second']:
            avg_panels_per_second = sum(self.throughput_metrics['panels_per_second']) / len(self.throughput_metrics['panels_per_second'])
        
        # API response time metrics
        api_metrics = {}
        for service, response_times in self.api_response_times.items():
            if response_times:
                api_metrics[service] = {
                    "avg_response_time_ms": sum(response_times) / len(response_times),
                    "min_response_time_ms": min(response_times),
                    "max_response_time_ms": max(response_times),
                    "total_calls": len(response_times),
                    "error_count": self.error_counts.get(service, 0)
                }
        
        # System metrics (last 5 minutes)
        recent_system_metrics = [
            m for m in self.system_metrics 
            if (now - m.timestamp).total_seconds() <= 300
        ]
        
        current_system = None
        if recent_system_metrics:
            latest = recent_system_metrics[-1]
            current_system = {
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "memory_used_mb": latest.memory_used_mb,
                "disk_percent": latest.disk_percent,
                "disk_used_gb": latest.disk_used_gb,
                "active_jobs": latest.active_jobs,
                "timestamp": latest.timestamp.isoformat()
            }
        
        return {
            "timestamp": now.isoformat(),
            "job_summary": {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "running_jobs": running_jobs,
                "success_rate": completed_jobs / total_jobs if total_jobs > 0 else 0
            },
            "performance": {
                "avg_processing_time_seconds": avg_processing_time,
                "avg_panels_per_second": avg_panels_per_second,
                "total_panels_processed": sum(j.panels_processed for j in self.job_metrics.values())
            },
            "api_metrics": api_metrics,
            "system_metrics": current_system,
            "error_summary": dict(self.error_counts)
        }

    def get_current_timestamp(self) -> str:
        """Get current timestamp for health checks."""
        return datetime.now().isoformat()

    async def close(self) -> None:
        """Close metrics collector."""
        self.stop_system_monitoring()
        logger.info("Closed metrics collector")
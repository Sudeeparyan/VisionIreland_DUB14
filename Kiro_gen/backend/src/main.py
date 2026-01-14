"""FastAPI main application for Comic Audio Narrator backend."""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
import uvicorn

from .config import settings
from .api.upload import upload_router
from .api.jobs import jobs_router
from .api.library import library_router
from .api.audio import audio_router
from .processing.pipeline_orchestrator import PipelineOrchestrator
from .storage.library_manager import LibraryManager
from .storage.local_manager import LocalStorageManager
from .storage.s3_manager import S3StorageManager
from .monitoring.cost_monitor import CostMonitor
from .monitoring.logger import setup_logging
from .monitoring.metrics import MetricsCollector

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global instances
pipeline_orchestrator: PipelineOrchestrator = None
library_manager: LibraryManager = None
cost_monitor: CostMonitor = None
metrics_collector: MetricsCollector = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    global pipeline_orchestrator, library_manager, cost_monitor, metrics_collector

    logger.info("Starting Comic Audio Narrator backend...")

    # Initialize components
    try:
        # Create storage directories
        Path(settings.local_storage_path).mkdir(parents=True, exist_ok=True)

        # Initialize storage managers
        local_manager = LocalStorageManager(storage_path=settings.local_storage_path)

        s3_manager = S3StorageManager(
            bucket_name=settings.s3_bucket_name, region=settings.aws_region
        )

        # Initialize library manager
        library_manager = LibraryManager(local_manager=local_manager, s3_manager=s3_manager)

        # Initialize cost monitor
        cost_monitor = CostMonitor()

        # Initialize metrics collector
        metrics_collector = MetricsCollector()

        # Initialize pipeline orchestrator
        pipeline_orchestrator = PipelineOrchestrator(
            library_manager=library_manager,
            use_neural_voices=settings.polly_engine == "neural",
            enable_caching=True,
            batch_size=10,
        )

        # Set global instances for API routes
        app.state.pipeline_orchestrator = pipeline_orchestrator
        app.state.library_manager = library_manager
        app.state.cost_monitor = cost_monitor
        app.state.metrics_collector = metrics_collector

        logger.info("Backend initialization complete")

    except Exception as e:
        logger.error(f"Failed to initialize backend: {e}")
        raise

    yield

    # Cleanup
    logger.info("Shutting down Comic Audio Narrator backend...")
    if cost_monitor:
        await cost_monitor.close()
    if metrics_collector:
        await metrics_collector.close()


# Create FastAPI app
app = FastAPI(
    title="Comic Audio Narrator API",
    description="Transform comic books into engaging audio narratives",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(upload_router, prefix="/api", tags=["upload"])
app.include_router(jobs_router, prefix="/api", tags=["jobs"])
app.include_router(library_router, prefix="/api", tags=["library"])
app.include_router(audio_router, prefix="/api", tags=["audio"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Comic Audio Narrator API",
        "version": "0.1.0",
        "description": "Transform comic books into engaging audio narratives",
        "endpoints": {
            "upload": "/api/upload",
            "jobs": "/api/jobs/{job_id}",
            "library": "/api/library",
            "audio": "/api/audio/{audio_id}",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": (
            app.state.metrics_collector.get_current_timestamp()
            if hasattr(app.state, "metrics_collector") and app.state.metrics_collector
            else None
        ),
    }


@app.get("/metrics")
async def get_metrics():
    """Get system metrics."""
    if not hasattr(app.state, "metrics_collector") or not app.state.metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics collector not available")

    return await app.state.metrics_collector.get_metrics()


@app.get("/costs")
async def get_costs():
    """Get cost information."""
    if not hasattr(app.state, "cost_monitor") or not app.state.cost_monitor:
        raise HTTPException(status_code=503, detail="Cost monitor not available")

    return await app.state.cost_monitor.get_cost_summary()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
        log_level=settings.log_level.lower(),
    )

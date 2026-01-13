"""Cost monitoring and optimization for AWS services."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class ServiceCost:
    """Cost information for a specific AWS service."""
    service_name: str
    api_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    characters_processed: int = 0
    storage_gb_hours: float = 0.0
    estimated_cost_usd: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class JobCost:
    """Cost tracking for a specific job."""
    job_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    bedrock_cost: ServiceCost = field(default_factory=lambda: ServiceCost("bedrock"))
    polly_cost: ServiceCost = field(default_factory=lambda: ServiceCost("polly"))
    s3_cost: ServiceCost = field(default_factory=lambda: ServiceCost("s3"))
    total_estimated_cost: float = 0.0
    status: str = "running"  # running, completed, failed


class CostMonitor:
    """Monitors and tracks costs for AWS services."""
    
    # AWS pricing (approximate, as of 2024)
    BEDROCK_PRICING = {
        "claude-3-5-sonnet": {
            "input_per_1k_tokens": 0.003,
            "output_per_1k_tokens": 0.015
        },
        "nova-pro": {
            "input_per_1k_tokens": 0.0008,
            "output_per_1k_tokens": 0.0032
        }
    }
    
    POLLY_PRICING = {
        "neural": 0.000016,  # per character
        "standard": 0.000004  # per character
    }
    
    S3_PRICING = {
        "standard": 0.023,  # per GB per month
        "intelligent_tiering": 0.0125  # per GB per month
    }

    def __init__(self):
        """Initialize cost monitor."""
        self.job_costs: Dict[str, JobCost] = {}
        self.daily_costs: Dict[str, ServiceCost] = {}
        self.monthly_costs: Dict[str, ServiceCost] = {}
        self.cost_alerts: List[Dict[str, Any]] = []
        
        # Cost thresholds for alerts
        self.daily_threshold_usd = 50.0
        self.monthly_threshold_usd = 500.0
        self.job_threshold_usd = 10.0

    async def start_job_tracking(self, job_id: str) -> None:
        """Start cost tracking for a job."""
        self.job_costs[job_id] = JobCost(
            job_id=job_id,
            started_at=datetime.now()
        )
        logger.info(f"Started cost tracking for job {job_id}")

    async def track_bedrock_usage(
        self,
        job_id: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        api_calls: int = 1
    ) -> None:
        """Track Bedrock API usage and costs."""
        if job_id not in self.job_costs:
            await self.start_job_tracking(job_id)
        
        job_cost = self.job_costs[job_id]
        
        # Determine model pricing
        model_key = "claude-3-5-sonnet" if "claude" in model_id.lower() else "nova-pro"
        pricing = self.BEDROCK_PRICING.get(model_key, self.BEDROCK_PRICING["claude-3-5-sonnet"])
        
        # Calculate cost
        input_cost = (input_tokens / 1000) * pricing["input_per_1k_tokens"]
        output_cost = (output_tokens / 1000) * pricing["output_per_1k_tokens"]
        total_cost = input_cost + output_cost
        
        # Update job cost
        job_cost.bedrock_cost.api_calls += api_calls
        job_cost.bedrock_cost.input_tokens += input_tokens
        job_cost.bedrock_cost.output_tokens += output_tokens
        job_cost.bedrock_cost.estimated_cost_usd += total_cost
        job_cost.bedrock_cost.last_updated = datetime.now()
        
        # Update daily/monthly aggregates
        await self._update_daily_costs("bedrock", api_calls, input_tokens, output_tokens, 0, 0, total_cost)
        
        logger.debug(f"Tracked Bedrock usage for job {job_id}: ${total_cost:.4f}")

    async def track_polly_usage(
        self,
        job_id: str,
        engine: str,
        characters: int,
        api_calls: int = 1
    ) -> None:
        """Track Polly API usage and costs."""
        if job_id not in self.job_costs:
            await self.start_job_tracking(job_id)
        
        job_cost = self.job_costs[job_id]
        
        # Calculate cost
        price_per_char = self.POLLY_PRICING.get(engine, self.POLLY_PRICING["neural"])
        total_cost = characters * price_per_char
        
        # Update job cost
        job_cost.polly_cost.api_calls += api_calls
        job_cost.polly_cost.characters_processed += characters
        job_cost.polly_cost.estimated_cost_usd += total_cost
        job_cost.polly_cost.last_updated = datetime.now()
        
        # Update daily/monthly aggregates
        await self._update_daily_costs("polly", api_calls, 0, 0, characters, 0, total_cost)
        
        logger.debug(f"Tracked Polly usage for job {job_id}: ${total_cost:.4f}")

    async def track_s3_usage(
        self,
        job_id: str,
        storage_class: str,
        size_gb: float,
        hours: float = 1.0
    ) -> None:
        """Track S3 storage usage and costs."""
        if job_id not in self.job_costs:
            await self.start_job_tracking(job_id)
        
        job_cost = self.job_costs[job_id]
        
        # Calculate cost (prorated for hours)
        price_per_gb_month = self.S3_PRICING.get(storage_class, self.S3_PRICING["standard"])
        total_cost = size_gb * (hours / (24 * 30)) * price_per_gb_month
        
        # Update job cost
        job_cost.s3_cost.storage_gb_hours += size_gb * hours
        job_cost.s3_cost.estimated_cost_usd += total_cost
        job_cost.s3_cost.last_updated = datetime.now()
        
        # Update daily/monthly aggregates
        await self._update_daily_costs("s3", 0, 0, 0, 0, size_gb * hours, total_cost)
        
        logger.debug(f"Tracked S3 usage for job {job_id}: ${total_cost:.4f}")

    async def complete_job_tracking(self, job_id: str, result: Dict[str, Any]) -> None:
        """Complete cost tracking for a job."""
        if job_id not in self.job_costs:
            logger.warning(f"Job {job_id} not found in cost tracking")
            return
        
        job_cost = self.job_costs[job_id]
        job_cost.completed_at = datetime.now()
        job_cost.status = "completed"
        
        # Calculate total cost
        job_cost.total_estimated_cost = (
            job_cost.bedrock_cost.estimated_cost_usd +
            job_cost.polly_cost.estimated_cost_usd +
            job_cost.s3_cost.estimated_cost_usd
        )
        
        # Check for cost alerts
        await self._check_cost_alerts(job_cost)
        
        logger.info(f"Completed cost tracking for job {job_id}: ${job_cost.total_estimated_cost:.4f}")

    async def error_job_tracking(self, job_id: str, error: str) -> None:
        """Mark job as failed in cost tracking."""
        if job_id not in self.job_costs:
            logger.warning(f"Job {job_id} not found in cost tracking")
            return
        
        job_cost = self.job_costs[job_id]
        job_cost.completed_at = datetime.now()
        job_cost.status = "failed"
        
        # Calculate total cost even for failed jobs
        job_cost.total_estimated_cost = (
            job_cost.bedrock_cost.estimated_cost_usd +
            job_cost.polly_cost.estimated_cost_usd +
            job_cost.s3_cost.estimated_cost_usd
        )
        
        logger.info(f"Error in job {job_id}, total cost: ${job_cost.total_estimated_cost:.4f}")

    async def get_job_cost(self, job_id: str) -> Optional[JobCost]:
        """Get cost information for a specific job."""
        return self.job_costs.get(job_id)

    async def get_cost_summary(self) -> Dict[str, Any]:
        """Get comprehensive cost summary."""
        # Calculate totals
        total_jobs = len(self.job_costs)
        completed_jobs = len([j for j in self.job_costs.values() if j.status == "completed"])
        failed_jobs = len([j for j in self.job_costs.values() if j.status == "failed"])
        
        total_cost = sum(j.total_estimated_cost for j in self.job_costs.values())
        
        # Daily costs
        today = datetime.now().date()
        daily_cost = sum(
            cost.estimated_cost_usd 
            for cost in self.daily_costs.values() 
            if cost.last_updated.date() == today
        )
        
        # Monthly costs
        current_month = datetime.now().replace(day=1).date()
        monthly_cost = sum(
            cost.estimated_cost_usd 
            for cost in self.monthly_costs.values() 
            if cost.last_updated.date() >= current_month
        )
        
        return {
            "summary": {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "total_cost_usd": total_cost,
                "daily_cost_usd": daily_cost,
                "monthly_cost_usd": monthly_cost
            },
            "service_breakdown": {
                "bedrock": {
                    "total_api_calls": sum(j.bedrock_cost.api_calls for j in self.job_costs.values()),
                    "total_input_tokens": sum(j.bedrock_cost.input_tokens for j in self.job_costs.values()),
                    "total_output_tokens": sum(j.bedrock_cost.output_tokens for j in self.job_costs.values()),
                    "total_cost_usd": sum(j.bedrock_cost.estimated_cost_usd for j in self.job_costs.values())
                },
                "polly": {
                    "total_api_calls": sum(j.polly_cost.api_calls for j in self.job_costs.values()),
                    "total_characters": sum(j.polly_cost.characters_processed for j in self.job_costs.values()),
                    "total_cost_usd": sum(j.polly_cost.estimated_cost_usd for j in self.job_costs.values())
                },
                "s3": {
                    "total_storage_gb_hours": sum(j.s3_cost.storage_gb_hours for j in self.job_costs.values()),
                    "total_cost_usd": sum(j.s3_cost.estimated_cost_usd for j in self.job_costs.values())
                }
            },
            "alerts": self.cost_alerts[-10:],  # Last 10 alerts
            "thresholds": {
                "daily_threshold_usd": self.daily_threshold_usd,
                "monthly_threshold_usd": self.monthly_threshold_usd,
                "job_threshold_usd": self.job_threshold_usd
            }
        }

    async def _update_daily_costs(
        self,
        service: str,
        api_calls: int,
        input_tokens: int,
        output_tokens: int,
        characters: int,
        storage_gb_hours: float,
        cost: float
    ) -> None:
        """Update daily cost aggregates."""
        today = datetime.now().date().isoformat()
        key = f"{service}_{today}"
        
        if key not in self.daily_costs:
            self.daily_costs[key] = ServiceCost(service)
        
        daily_cost = self.daily_costs[key]
        daily_cost.api_calls += api_calls
        daily_cost.input_tokens += input_tokens
        daily_cost.output_tokens += output_tokens
        daily_cost.characters_processed += characters
        daily_cost.storage_gb_hours += storage_gb_hours
        daily_cost.estimated_cost_usd += cost
        daily_cost.last_updated = datetime.now()

    async def _check_cost_alerts(self, job_cost: JobCost) -> None:
        """Check for cost threshold alerts."""
        # Job-level alert
        if job_cost.total_estimated_cost > self.job_threshold_usd:
            alert = {
                "type": "job_threshold",
                "job_id": job_cost.job_id,
                "cost": job_cost.total_estimated_cost,
                "threshold": self.job_threshold_usd,
                "timestamp": datetime.now().isoformat()
            }
            self.cost_alerts.append(alert)
            logger.warning(f"Job cost alert: {job_cost.job_id} exceeded ${self.job_threshold_usd}")
        
        # Daily alert
        today = datetime.now().date()
        daily_total = sum(
            cost.estimated_cost_usd 
            for cost in self.daily_costs.values() 
            if cost.last_updated.date() == today
        )
        
        if daily_total > self.daily_threshold_usd:
            alert = {
                "type": "daily_threshold",
                "cost": daily_total,
                "threshold": self.daily_threshold_usd,
                "date": today.isoformat(),
                "timestamp": datetime.now().isoformat()
            }
            self.cost_alerts.append(alert)
            logger.warning(f"Daily cost alert: ${daily_total:.2f} exceeded ${self.daily_threshold_usd}")

    async def close(self) -> None:
        """Close cost monitor and save state."""
        logger.info("Closing cost monitor")
        # Could save state to file or database here
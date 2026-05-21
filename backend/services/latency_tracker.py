"""
Latency tracking and monitoring service
"""
import time
from  typing import Dict, List
from  datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class LatencyTracker:
    """Track latency of different pipeline components"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.metrics: Dict[str, Dict] = {}
        self.start_time = time.time()
    
    def start(self, component: str) -> None:
        """Start timing a component"""
        if component not in self.metrics:
            self.metrics[component] = {
                "start_time": None,
                "end_time": None,
                "duration_ms": 0,
                "count": 0
            }
        self.metrics[component]["start_time"] = time.time()
    
    def end(self, component: str) -> float:
        """End timing a component and return duration"""
        if component not in self.metrics:
            return 0
        
        self.metrics[component]["end_time"] = time.time()
        duration_ms = (
            self.metrics[component]["end_time"] - 
            self.metrics[component]["start_time"]
        ) * 1000
        
        self.metrics[component]["duration_ms"] = duration_ms
        self.metrics[component]["count"] += 1
        
        return duration_ms
    
    def get_total_latency(self) -> float:
        """Get total pipeline latency from  start"""
        return (time.time() - self.start_time) * 1000
    
    def get_breakdown(self) -> Dict[str, float]:
        """Get latency breakdown by component"""
        return {
            component: metrics["duration_ms"]
            for component, metrics in self.metrics.items()
            if metrics["duration_ms"] > 0
        }
    
    def get_report(self) -> Dict:
        """Get comprehensive latency report"""
        return {
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "total_latency_ms": self.get_total_latency(),
            "breakdown": self.get_breakdown(),
            "components": {
                name: {
                    "duration_ms": metrics["duration_ms"],
                    "count": metrics["count"],
                }
                for name, metrics in self.metrics.items()
            }
        }
    
    def log_report(self) -> None:
        """Log the latency report"""
        report = self.get_report()
        logger.info(f"Latency Report: {json.dumps(report)}")

class LatencyMonitor:
    """Monitor and aggregate latency metrics"""
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self.trackers: Dict[str, LatencyTracker] = {}
    
    def create_tracker(self, session_id: str) -> LatencyTracker:
        """Create a new latency tracker"""
        tracker = LatencyTracker(session_id)
        self.trackers[session_id] = tracker
        return tracker
    
    def get_tracker(self, session_id: str) -> LatencyTracker:
        """Get existing tracker"""
        if session_id not in self.trackers:
            return self.create_tracker(session_id)
        return self.trackers[session_id]
    
    async def save_metrics(self, session_id: str) -> bool:
        """Save latency metrics to database"""
        if not self.db_session or session_id not in self.trackers:
            return False
        
        try:
            tracker = self.trackers[session_id]
            report = tracker.get_report()
            
            # Save individual component metrics
            from models.models import LatencyMetric
            
            for component, duration in report["breakdown"].items():
                metric = LatencyMetric(
                    session_id=session_id,
                    component=component,
                    duration_ms=duration
                )
                self.db_session.add(metric)
            
            # Save total metric
            total_metric = LatencyMetric(
                session_id=session_id,
                component="total",
                duration_ms=report["total_latency_ms"]
            )
            self.db_session.add(total_metric)
            
            await self.db_session.commit()
            return True
        
        except Exception as e:
            logger.error(f"Error saving latency metrics: {e}")
            return False

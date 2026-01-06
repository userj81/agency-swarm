import json
from datetime import datetime, timedelta

from pydantic import Field

from agency_swarm.tools import BaseTool


class MonitorApplicationTool(BaseTool):
    """
    Monitor application metrics, logs, and performance indicators.
    Provides real-time insights into application health and operational status.
    """

    metric_type: str = Field(
        default="all",
        description="Type of metrics to retrieve. Options: 'all', 'performance', 'errors', 'resources', 'requests'. Defaults to 'all'.",
    )

    time_range: str = Field(
        default="1h",
        description="Time range for metrics data. Format: '5m', '1h', '24h', '7d'. Defaults to '1h'.",
    )

    application_name: str = Field(
        default=None,
        description="Optional application name to filter metrics. If not specified, returns metrics for all applications.",
    )

    include_logs: bool = Field(
        default=False,
        description="Include recent log entries in the output. Defaults to False.",
    )

    alert_threshold: str = Field(
        default=None,
        description="Optional threshold for alerting (e.g., 'cpu>80', 'errors>10'). Only returns metrics exceeding threshold.",
    )

    def run(self):
        """
        Retrieve and return application monitoring metrics and status.
        """
        try:
            # Parse time range
            time_delta = self._parse_time_range(self.time_range)

            # Get current metrics
            current_time = datetime.now()

            # Simulated metrics data (in production, would fetch from monitoring system)
            metrics = {
                "timestamp": current_time.isoformat(),
                "time_range": self.time_range,
                "application": self.application_name or "all",
            }

            # Performance metrics
            if self.metric_type in ["all", "performance"]:
                metrics["performance"] = {
                    "response_time_avg_ms": 145.2,
                    "response_time_p95_ms": 320.5,
                    "response_time_p99_ms": 580.1,
                    "throughput_rps": 245.8,
                    "error_rate_percent": 0.12,
                    "status": "healthy",
                }

            # Error metrics
            if self.metric_type in ["all", "errors"]:
                metrics["errors"] = {
                    "total_errors": 12,
                    "errors_by_type": {
                        "4xx_errors": 8,
                        "5xx_errors": 4,
                        "timeout_errors": 0,
                    },
                    "recent_errors": [
                        {
                            "timestamp": (current_time - timedelta(minutes=5)).isoformat(),
                            "type": "500",
                            "message": "Internal server error",
                            "endpoint": "/api/users",
                        },
                        {
                            "timestamp": (current_time - timedelta(minutes=15)).isoformat(),
                            "type": "404",
                            "message": "Not found",
                            "endpoint": "/api/invalid",
                        },
                    ] if self.metric_type == "errors" else [],
                }

            # Resource metrics
            if self.metric_type in ["all", "resources"]:
                metrics["resources"] = {
                    "cpu_percent": 42.3,
                    "memory_percent": 67.8,
                    "disk_percent": 55.2,
                    "network_in_mbps": 12.4,
                    "network_out_mbps": 28.6,
                    "active_connections": 145,
                }

            # Request metrics
            if self.metric_type in ["all", "requests"]:
                metrics["requests"] = {
                    "total_requests": 884520,
                    "requests_by_status": {
                        "200": 883480,
                        "301": 520,
                        "400": 320,
                        "404": 180,
                        "500": 20,
                    },
                    "top_endpoints": [
                        {"path": "/api/users", "requests": 245120, "avg_response_time": 120.5},
                        {"path": "/api/posts", "requests": 189340, "avg_response_time": 180.2},
                        {"path": "/api/comments", "requests": 156780, "avg_response_time": 95.8},
                    ],
                }

            # Health status
            metrics["health"] = self._calculate_health_status(metrics)

            # Include logs if requested
            if self.include_logs:
                metrics["logs"] = self._get_recent_logs(current_time)

            # Apply alert threshold filter if specified
            if self.alert_threshold:
                filtered_metrics = self._apply_threshold_filter(metrics, self.alert_threshold)
                if filtered_metrics is None:
                    metrics["summary"] = f"No metrics exceed threshold: {self.alert_threshold}"
                else:
                    metrics = filtered_metrics
                    metrics["summary"] = f"Metrics exceeding threshold '{self.alert_threshold}'"
            else:
                metrics["summary"] = self._generate_summary(metrics)

            return json.dumps(metrics, indent=2)

        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "metric_type": self.metric_type,
            }
            return json.dumps(result, indent=2)

    def _parse_time_range(self, time_range: str) -> timedelta:
        """Parse time range string into timedelta."""
        unit = time_range[-1]
        value = int(time_range[:-1])

        if unit == "m":
            return timedelta(minutes=value)
        elif unit == "h":
            return timedelta(hours=value)
        elif unit == "d":
            return timedelta(days=value)
        else:
            return timedelta(hours=1)  # Default to 1 hour

    def _calculate_health_status(self, metrics: dict) -> dict:
        """Calculate overall health status from metrics."""
        health = {
            "status": "healthy",
            "issues": [],
        }

        # Check performance
        if "performance" in metrics:
            perf = metrics["performance"]
            if perf["response_time_p95_ms"] > 500:
                health["status"] = "degraded"
                health["issues"].append("High response time (P95 > 500ms)")
            if perf["error_rate_percent"] > 1:
                health["status"] = "unhealthy"
                health["issues"].append(f"High error rate: {perf['error_rate_percent']}%")

        # Check resources
        if "resources" in metrics:
            res = metrics["resources"]
            if res["cpu_percent"] > 80:
                health["status"] = "degraded"
                health["issues"].append(f"High CPU usage: {res['cpu_percent']}%")
            if res["memory_percent"] > 85:
                health["status"] = "degraded"
                health["issues"].append(f"High memory usage: {res['memory_percent']}%")

        return health

    def _get_recent_logs(self, current_time: datetime) -> list:
        """Get recent log entries."""
        logs = [
            {
                "timestamp": (current_time - timedelta(seconds=30)).isoformat(),
                "level": "INFO",
                "message": "Request processed successfully",
                "endpoint": "/api/users",
                "duration_ms": 120,
            },
            {
                "timestamp": (current_time - timedelta(minutes=2)).isoformat(),
                "level": "WARNING",
                "message": "Slow query detected",
                "endpoint": "/api/posts",
                "duration_ms": 850,
            },
            {
                "timestamp": (current_time - timedelta(minutes=5)).isoformat(),
                "level": "ERROR",
                "message": "Database connection timeout",
                "endpoint": "/api/comments",
                "duration_ms": 5000,
            },
        ]

        return logs

    def _apply_threshold_filter(self, metrics: dict, threshold: str) -> dict | None:
        """Filter metrics based on alert threshold."""
        try:
            # Parse threshold (e.g., "cpu>80", "errors>10")
            if ">" in threshold:
                metric, value = threshold.split(">")
                value = float(value)
                value_str = str(value)

                # Check if threshold is exceeded
                threshold_exceeded = False
                exceeded_value = None

                # Check in resources
                if "resources" in metrics:
                    res = metrics["resources"]
                    if metric == "cpu" and res["cpu_percent"] > value:
                        threshold_exceeded = True
                        exceeded_value = res["cpu_percent"]
                    elif metric == "memory" and res["memory_percent"] > value:
                        threshold_exceeded = True
                        exceeded_value = res["memory_percent"]

                # Check in errors
                if "errors" in metrics:
                    errors = metrics["errors"]
                    if metric == "errors" and errors["total_errors"] > value:
                        threshold_exceeded = True
                        exceeded_value = errors["total_errors"]

                if threshold_exceeded:
                    return {
                        "alert_triggered": True,
                        "threshold": threshold,
                        "current_value": exceeded_value,
                        "message": f"Threshold exceeded: {metric} = {exceeded_value} > {value}",
                    }

            return None

        except Exception:
            return metrics  # Return all metrics if threshold parsing fails

    def _generate_summary(self, metrics: dict) -> str:
        """Generate a summary of the monitoring data."""
        summary_parts = []

        if "health" in metrics:
            health_status = metrics["health"]["status"].upper()
            summary_parts.append(f"Status: {health_status}")

            if metrics["health"]["issues"]:
                summary_parts.append(f"Issues: {len(metrics['health']['issues'])}")

        if "performance" in metrics:
            perf = metrics["performance"]
            summary_parts.append(f"Response time: {perf['response_time_avg_ms']:.1f}ms avg")

        if "resources" in metrics:
            res = metrics["resources"]
            summary_parts.append(f"CPU: {res['cpu_percent']}%, Memory: {res['memory_percent']}%")

        return " | ".join(summary_parts) if summary_parts else "Monitoring data retrieved"


if __name__ == "__main__":
    # Test the tool
    tool = MonitorApplicationTool(metric_type="all", time_range="1h")
    print(tool.run())

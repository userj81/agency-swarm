import json
from datetime import datetime

from pydantic import Field

from agency_swarm.tools import BaseTool


class SetupMonitoringTool(BaseTool):
    """
    Configure monitoring and alerting for applications and infrastructure.
    Sets up metrics collection, dashboards, and alerting rules.
    """

    service_name: str = Field(
        ...,
        description="Name of the service/application to monitor (e.g., 'api-server', 'web-app', 'database').",
    )

    monitoring_type: str = Field(
        default="full",
        description="Type of monitoring to set up. Options: 'full', 'basic', 'performance', 'security'. Defaults to 'full'.",
    )

    alert_email: str = Field(
        default=None,
        description="Email address for alert notifications. If not specified, alerts are logged only.",
    )

    environment: str = Field(
        default="production",
        description="Environment to monitor. Options: 'dev', 'staging', 'production'. Defaults to 'production'.",
    )

    retention_days: int = Field(
        default=30,
        description="Data retention period in days. Defaults to 30.",
    )

    def run(self):
        """
        Set up monitoring configuration and return details.
        """
        try:
            # Validate inputs
            valid_types = ["full", "basic", "performance", "security"]
            if self.monitoring_type not in valid_types:
                result = {
                    "success": False,
                    "error": f"Invalid monitoring_type: {self.monitoring_type}",
                    "valid_types": valid_types,
                }
                return json.dumps(result, indent=2)

            valid_environments = ["dev", "staging", "production"]
            if self.environment not in valid_environments:
                result = {
                    "success": False,
                    "error": f"Invalid environment: {self.environment}",
                    "valid_environments": valid_environments,
                }
                return json.dumps(result, indent=2)

            # Generate monitoring configuration
            config = {
                "service_name": self.service_name,
                "environment": self.environment,
                "monitoring_type": self.monitoring_type,
                "created_at": datetime.now().isoformat(),
                "retention_days": self.retention_days,
            }

            # Set up metrics collection
            config["metrics"] = self._setup_metrics()

            # Set up dashboards
            config["dashboards"] = self._setup_dashboards()

            # Set up alerts
            config["alerts"] = self._setup_alerts()

            # Set up logging
            config["logging"] = self._setup_logging()

            # Generate access URLs
            config["access_urls"] = self._generate_access_urls()

            # Add recommendations
            config["recommendations"] = self._generate_recommendations()

            config["success"] = True
            config["summary"] = (
                f"Monitoring configured for {self.service_name} in {self.environment} "
                f"with {len(config['alerts']['rules'])} alert rules"
            )

            return json.dumps(config, indent=2)

        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "service_name": self.service_name,
            }
            return json.dumps(result, indent=2)

    def _setup_metrics(self) -> dict:
        """Set up metrics collection configuration."""
        metrics = {
            "collection_interval_seconds": 60,
            "metrics_types": {
                "system": ["cpu", "memory", "disk", "network"],
                "application": ["requests", "response_time", "error_rate", "throughput"],
                "custom": ["business_metrics", "user_actions"],
            }
        }

        # Adjust based on monitoring type
        if self.monitoring_type == "basic":
            metrics["metrics_types"] = {
                "system": ["cpu", "memory"],
                "application": ["requests", "error_rate"],
            }
        elif self.monitoring_type == "performance":
            metrics["metrics_types"] = {
                "application": ["response_time", "throughput", "error_rate"],
                "custom": ["database_queries", "cache_hits"],
            }
        elif self.monitoring_type == "security":
            metrics["metrics_types"] = {
                "application": ["failed_auth_attempts", "blocked_requests"],
                "custom": ["security_events", "intrusion_detection"],
            }

        return metrics

    def _setup_dashboards(self) -> list:
        """Set up monitoring dashboards."""
        dashboards = [
            {
                "name": "Overview",
                "description": "High-level service metrics",
                "panels": [
                    {"title": "Request Rate", "type": "graph"},
                    {"title": "Error Rate", "type": "graph"},
                    {"title": "Response Time", "type": "heatmap"},
                    {"title": "Active Connections", "type": "gauge"},
                ],
            },
            {
                "name": "Infrastructure",
                "description": "System resource metrics",
                "panels": [
                    {"title": "CPU Usage", "type": "graph"},
                    {"title": "Memory Usage", "type": "graph"},
                    {"title": "Disk I/O", "type": "graph"},
                    {"title": "Network Traffic", "type": "graph"},
                ],
            },
            {
                "name": "Application Performance",
                "description": "Detailed application metrics",
                "panels": [
                    {"title": "Response Time Percentiles", "type": "graph"},
                    {"title": "Throughput", "type": "graph"},
                    {"title": "Error Rate by Endpoint", "type": "table"},
                    {"title": "Slow Queries", "type": "table"},
                ],
            },
        ]

        # Adjust based on monitoring type
        if self.monitoring_type == "basic":
            dashboards = dashboards[:1]
        elif self.monitoring_type == "performance":
            dashboards = [dashboards[0], dashboards[2]]
        elif self.monitoring_type == "security":
            dashboards = [
                {
                    "name": "Security",
                    "description": "Security-related metrics",
                    "panels": [
                        {"title": "Failed Auth Attempts", "type": "graph"},
                        {"title": "Blocked Requests", "type": "graph"},
                        {"title": "Security Events", "type": "table"},
                    ],
                }
            ]

        return dashboards

    def _setup_alerts(self) -> dict:
        """Set up alerting rules."""
        alert_rules = []

        # Common alert rules
        alert_rules.extend([
            {
                "name": "HighErrorRate",
                "condition": "error_rate > 5%",
                "duration": "5m",
                "severity": "warning",
                "description": "Error rate exceeds 5% for 5 minutes",
            },
            {
                "name": "HighResponseTime",
                "condition": "response_time_p95 > 1s",
                "duration": "10m",
                "severity": "warning",
                "description": "95th percentile response time exceeds 1 second",
            },
            {
                "name": "ServiceDown",
                "condition": "up == 0",
                "duration": "1m",
                "severity": "critical",
                "description": "Service is not responding",
            },
            {
                "name": "HighCPUUsage",
                "condition": "cpu_percent > 80%",
                "duration": "15m",
                "severity": "warning",
                "description": "CPU usage exceeds 80% for 15 minutes",
            },
            {
                "name": "HighMemoryUsage",
                "condition": "memory_percent > 85%",
                "duration": "15m",
                "severity": "warning",
                "description": "Memory usage exceeds 85% for 15 minutes",
            },
        ])

        # Add production-specific alerts
        if self.environment == "production":
            alert_rules.append({
                "name": "CriticalErrorRate",
                "condition": "error_rate > 10%",
                "duration": "2m",
                "severity": "critical",
                "description": "Critical error rate in production",
            })

        # Adjust based on monitoring type
        if self.monitoring_type == "basic":
            alert_rules = alert_rules[:3]
        elif self.monitoring_type == "performance":
            alert_rules = [alert_rules[0], alert_rules[1]]
        elif self.monitoring_type == "security":
            alert_rules = [
                {
                    "name": "FailedAuthAttempts",
                    "condition": "failed_auth_rate > 10/min",
                    "duration": "5m",
                    "severity": "critical",
                    "description": "High rate of failed authentication attempts",
                },
                {
                    "name": "SuspiciousActivity",
                    "condition": "security_events > 100/min",
                    "duration": "5m",
                    "severity": "critical",
                    "description": "Suspicious activity detected",
                },
            ]

        # Configure notification channels
        notification_channels = []

        if self.alert_email:
            notification_channels.append({
                "type": "email",
                "address": self.alert_email,
                "severity_levels": ["critical", "warning"],
            })

        notification_channels.append({
            "type": "slack",
            "webhook": "https://hooks.slack.com/services/XXX",
            "severity_levels": ["critical"],
        })

        return {
            "rules": alert_rules,
            "notification_channels": notification_channels,
        }

    def _setup_logging(self) -> dict:
        """Set up logging configuration."""
        logging_config = {
            "level": "INFO" if self.environment != "production" else "WARNING",
            "format": "json",
            "outputs": ["stdout", "file"],
            "retention_days": self.retention_days,
        }

        # Add log aggregation for production
        if self.environment == "production":
            logging_config["outputs"].append("elasticsearch")
            logging_config["aggregation_enabled"] = True

        return logging_config

    def _generate_access_urls(self) -> dict:
        """Generate access URLs for monitoring interfaces."""
        service_slug = self.service_name.lower().replace("-", "_")

        return {
            "grafana_dashboard": f"https://grafana.example.com/d/{service_slug}",
            "metrics_endpoint": f"https://metrics.example.com/api/v1/metrics?service={self.service_name}",
            "logs": f"https://logs.example.com/explore?service={self.service_name}",
            "alerts": f"https://alerts.example.com?service={self.service_name}",
        }

    def _generate_recommendations(self) -> list:
        """Generate monitoring setup recommendations."""
        recommendations = [
            "Review and adjust alert thresholds based on normal traffic patterns",
            "Set up on-call rotation for critical alerts",
            "Create runbooks for common alert scenarios",
            "Regularly review and update dashboards",
        ]

        if self.environment == "production":
            recommendations.extend([
                "Set up synthetic monitoring for critical endpoints",
                "Configure anomaly detection for unusual patterns",
                "Integrate with incident management system",
            ])

        if not self.alert_email:
            recommendations.append("Configure email notification for alert delivery")

        return recommendations


if __name__ == "__main__":
    # Test the tool
    tool = SetupMonitoringTool(
        service_name="api-server",
        environment="production",
        alert_email="devops@example.com"
    )
    print(tool.run())

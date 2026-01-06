import json
from datetime import datetime, timedelta

from pydantic import Field

from agency_swarm.tools import BaseTool


class GenerateDeploymentReportTool(BaseTool):
    """
    Generate comprehensive deployment reports including success rates, failure analysis,
    performance metrics, and deployment trends over time.
    """

    time_range: str = Field(
        default="7d",
        description="Time range for the report. Format: '24h', '7d', '30d', '90d'. Defaults to '7d'.",
    )

    environment: str = Field(
        default="all",
        description="Filter by environment. Options: 'all', 'dev', 'staging', 'production'. Defaults to 'all'.",
    )

    include_details: bool = Field(
        default=True,
        description="Include detailed deployment logs and individual deployment records. Defaults to True.",
    )

    report_format: str = Field(
        default="json",
        description="Output format for the report. Options: 'json', 'summary'. Defaults to 'json'.",
    )

    def run(self):
        """
        Generate the deployment report and return comprehensive metrics.
        """
        try:
            # Parse time range
            time_delta = self._parse_time_range(self.time_range)
            end_date = datetime.now()
            start_date = end_date - time_delta

            # Generate report data
            report = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "time_range": self.time_range,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "environment": self.environment,
                },
                "summary": self._generate_summary_metrics(start_date, end_date),
            }

            # Add detailed deployment records if requested
            if self.include_details:
                report["deployments"] = self._get_deployment_records(start_date, end_date)

            # Add trends analysis
            report["trends"] = self._analyze_trends(start_date, end_date)

            # Add failure analysis
            report["failure_analysis"] = self._analyze_failures(start_date, end_date)

            # Add recommendations
            report["recommendations"] = self._generate_recommendations(report)

            # Format output
            if self.report_format == "summary":
                output = self._format_summary(report)
            else:
                output = report

            return json.dumps(output, indent=2)

        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
            }
            return json.dumps(result, indent=2)

    def _parse_time_range(self, time_range: str) -> timedelta:
        """Parse time range string into timedelta."""
        unit = time_range[-1]
        value = int(time_range[:-1])

        if unit == "h":
            return timedelta(hours=value)
        elif unit == "d":
            return timedelta(days=value)
        else:
            return timedelta(days=7)  # Default to 7 days

    def _generate_summary_metrics(self, start_date: datetime, end_date: datetime) -> dict:
        """Generate summary metrics for the time period."""
        # Simulated data - in production would query actual deployment records
        total_deployments = 45
        successful_deployments = 41
        failed_deployments = 4
        rolled_back_deployments = 2

        summary = {
            "total_deployments": total_deployments,
            "successful": successful_deployments,
            "failed": failed_deployments,
            "rolled_back": rolled_back_deployments,
            "success_rate": round(successful_deployments / total_deployments * 100, 1),
            "mean_time_to_deploy_minutes": 12.5,
            "median_deployment_time_minutes": 8.2,
            "deployments_per_day": round(total_deployments / ((end_date - start_date).days or 1), 1),
        }

        # Breakdown by environment
        if self.environment == "all":
            summary["by_environment"] = {
                "dev": {
                    "total": 20,
                    "successful": 19,
                    "failed": 1,
                    "success_rate": 95.0,
                },
                "staging": {
                    "total": 15,
                    "successful": 14,
                    "failed": 1,
                    "success_rate": 93.3,
                },
                "production": {
                    "total": 10,
                    "successful": 8,
                    "failed": 2,
                    "success_rate": 80.0,
                },
            }

        return summary

    def _get_deployment_records(self, start_date: datetime, end_date: datetime) -> list:
        """Get detailed deployment records for the time period."""
        # Simulated deployment records
        deployments = []

        # Generate some sample deployments
        for i in range(10):
            timestamp = end_date - timedelta(hours=i * 6)
            env = ["dev", "staging", "production"][i % 3]
            success = i % 10 != 3 and i % 10 != 7  # Simulate 2 failures

            deployment = {
                "deployment_id": f"deploy-{timestamp.strftime('%Y%m%d-%H%M%S')}",
                "timestamp": timestamp.isoformat(),
                "environment": env,
                "version": f"v1.2.{10-i}",
                "status": "success" if success else "failed",
                "duration_seconds": 450 + (i * 30) if success else 120,
                "deployer": "devops-engineer",
                "strategy": "rolling",
            }

            if not success:
                deployment["failure_reason"] = "Health check timeout" if i % 10 == 3 else "Tests failed"
                deployment["rolled_back"] = i % 10 == 3

            deployments.append(deployment)

        return deployments

    def _analyze_trends(self, start_date: datetime, end_date: datetime) -> dict:
        """Analyze deployment trends over time."""
        trends = {
            "deployment_frequency": {
                "trend": "increasing",
                "change_percent": 15.5,
                "description": "Deployment frequency has increased over the period",
            },
            "success_rate": {
                "trend": "stable",
                "change_percent": 2.3,
                "description": "Success rate has remained stable",
            },
            "deployment_time": {
                "trend": "decreasing",
                "change_percent": -8.7,
                "description": "Average deployment time has decreased",
            },
            "rollback_rate": {
                "trend": "decreasing",
                "change_percent": -25.0,
                "description": "Rollback rate has decreased significantly",
            },
        }

        return trends

    def _analyze_failures(self, start_date: datetime, end_date: datetime) -> dict:
        """Analyze deployment failures."""
        failures = {
            "total_failures": 4,
            "failure_categories": {
                "health_check_failures": 2,
                "test_failures": 1,
                "configuration_errors": 1,
            },
            "common_failure_reasons": [
                {
                    "reason": "Health check timeout",
                    "count": 2,
                    "percentage": 50.0,
                },
                {
                    "reason": "Integration tests failed",
                    "count": 1,
                    "percentage": 25.0,
                },
                {
                    "reason": "Configuration validation failed",
                    "count": 1,
                    "percentage": 25.0,
                },
            ],
            "mttr_mean_time_to_resolve_minutes": 35.5,
            "rollbacks_performed": 2,
        }

        return failures

    def _generate_recommendations(self, report: dict) -> list:
        """Generate actionable recommendations based on report data."""
        recommendations = []

        summary = report["summary"]
        failure_analysis = report["failure_analysis"]

        # Success rate recommendations
        if summary["success_rate"] < 90:
            recommendations.append(
                f"Success rate is {summary['success_rate']}%. Investigate and address common failure patterns."
            )

        # Deployment time recommendations
        if summary["mean_time_to_deploy_minutes"] > 15:
            recommendations.append(
                "Consider optimizing deployment pipeline to reduce mean deployment time."
            )

        # Failure-specific recommendations
        if failure_analysis["failure_categories"]["health_check_failures"] > 0:
            recommendations.append(
                "Review health check configurations and timeout values."
            )

        if failure_analysis["failure_categories"]["test_failures"] > 0:
            recommendations.append(
                "Implement pre-deployment test validation to catch issues earlier."
            )

        # Rollback recommendations
        if failure_analysis["rollbacks_performed"] > 0:
            recommendations.append(
                "Consider implementing canary deployments to reduce rollback frequency."
            )

        # Environment-specific recommendations
        if "by_environment" in summary:
            prod = summary["by_environment"].get("production", {})
            if prod.get("success_rate", 100) < 90:
                recommendations.append(
                    "Production success rate is below target. Consider requiring staging validation first."
                )

        if not recommendations:
            recommendations.append("Deployment metrics look good! Maintain current practices.")

        return recommendations

    def _format_summary(self, report: dict) -> dict:
        """Format report as a summary."""
        summary = report["summary"]
        failure_analysis = report["failure_analysis"]
        recommendations = report["recommendations"]

        return {
            "period": f"{report['report_metadata']['start_date'][:10]} to {report['report_metadata']['end_date'][:10]}",
            "environment": report["report_metadata"]["environment"],
            "deployments": summary["total_deployments"],
            "success_rate": f"{summary['success_rate']}%",
            "avg_deployment_time": f"{summary['mean_time_to_deploy_minutes']} min",
            "failures": failure_analysis["total_failures"],
            "rollbacks": failure_analysis["rollbacks_performed"],
            "top_recommendations": recommendations[:3],
        }


if __name__ == "__main__":
    # Test the tool
    tool = GenerateDeploymentReportTool(time_range="7d", environment="all")
    print(tool.run())

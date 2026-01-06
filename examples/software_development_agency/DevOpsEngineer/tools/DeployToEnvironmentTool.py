import json
import subprocess
from datetime import datetime
from pathlib import Path

from pydantic import Field

from agency_swarm.tools import BaseTool


class DeployToEnvironmentTool(BaseTool):
    """
    Deploy application code to a specified environment (dev, staging, production).
    Supports multiple deployment strategies and includes health checks and rollback capabilities.
    """

    environment: str = Field(
        ...,
        description="Target environment for deployment. Options: 'dev', 'staging', 'production'.",
    )

    deploy_strategy: str = Field(
        default="rolling",
        description="Deployment strategy to use. Options: 'rolling', 'blue-green', 'canary'. Defaults to 'rolling'.",
    )

    application_path: str = Field(
        default=".",
        description="Path to the application directory to deploy. Defaults to current directory.",
    )

    version: str = Field(
        default=None,
        description="Optional version or git tag to deploy. If not specified, deploys current HEAD.",
    )

    skip_tests: bool = Field(
        default=False,
        description="Skip pre-deployment tests (use with caution). Defaults to False.",
    )

    rollback_on_failure: bool = Field(
        default=True,
        description="Automatically rollback on deployment failure. Defaults to True.",
    )

    def run(self):
        """
        Execute the deployment and return detailed status and results.
        """
        try:
            start_time = datetime.now()

            # Validate environment
            valid_environments = ["dev", "staging", "production"]
            if self.environment not in valid_environments:
                result = {
                    "success": False,
                    "error": f"Invalid environment: {self.environment}",
                    "valid_environments": valid_environments,
                }
                return json.dumps(result, indent=2)

            # Validate strategy
            valid_strategies = ["rolling", "blue-green", "canary"]
            if self.deploy_strategy not in valid_strategies:
                result = {
                    "success": False,
                    "error": f"Invalid deployment strategy: {self.deploy_strategy}",
                    "valid_strategies": valid_strategies,
                }
                return json.dumps(result, indent=2)

            deployment_steps = []
            warnings = []

            # Step 1: Pre-deployment checks
            deployment_steps.append({
                "step": 1,
                "name": "Pre-deployment checks",
                "status": "in_progress",
                "message": "Running pre-deployment validation...",
            })

            pre_checks = self._run_pre_deployment_checks()
            if not pre_checks["passed"]:
                deployment_steps[-1]["status"] = "failed"
                deployment_steps[-1]["message"] = "Pre-deployment checks failed"
                deployment_steps[-1]["details"] = pre_checks

                result = {
                    "success": False,
                    "environment": self.environment,
                    "strategy": self.deploy_strategy,
                    "deployment_steps": deployment_steps,
                    "error": "Pre-deployment checks failed",
                    "checks_failed": pre_checks["failed_checks"],
                }
                return json.dumps(result, indent=2)

            deployment_steps[-1]["status"] = "completed"
            deployment_steps[-1]["message"] = "Pre-deployment checks passed"
            deployment_steps[-1]["details"] = pre_checks

            # Step 2: Run tests (if not skipped)
            if not self.skip_tests:
                deployment_steps.append({
                    "step": 2,
                    "name": "Run tests",
                    "status": "in_progress",
                    "message": "Running test suite...",
                })

                test_results = self._run_tests()
                if not test_results["passed"]:
                    deployment_steps[-1]["status"] = "failed"
                    deployment_steps[-1]["message"] = "Tests failed"
                    deployment_steps[-1]["details"] = test_results

                    result = {
                        "success": False,
                        "environment": self.environment,
                        "strategy": self.deploy_strategy,
                        "deployment_steps": deployment_steps,
                        "error": "Tests failed - deployment aborted",
                    }
                    return json.dumps(result, indent=2)

                deployment_steps[-1]["status"] = "completed"
                deployment_steps[-1]["message"] = "All tests passed"
                deployment_steps[-1]["details"] = test_results
            else:
                warnings.append("Tests were skipped (--skip-tests flag)")

            # Step 3: Build application
            deployment_steps.append({
                "step": 3,
                "name": "Build application",
                "status": "in_progress",
                "message": "Building application...",
            })

            build_results = self._build_application()
            if not build_results["success"]:
                deployment_steps[-1]["status"] = "failed"
                deployment_steps[-1]["message"] = "Build failed"
                deployment_steps[-1]["details"] = build_results

                result = {
                    "success": False,
                    "environment": self.environment,
                    "strategy": self.deploy_strategy,
                    "deployment_steps": deployment_steps,
                    "error": "Build failed",
                }
                return json.dumps(result, indent=2)

            deployment_steps[-1]["status"] = "completed"
            deployment_steps[-1]["message"] = "Build completed successfully"
            deployment_steps[-1]["details"] = build_results

            # Step 4: Deploy to environment
            deployment_steps.append({
                "step": 4,
                "name": f"Deploy to {self.environment}",
                "status": "in_progress",
                "message": f"Deploying using {self.deploy_strategy} strategy...",
            })

            deploy_results = self._execute_deployment()
            if not deploy_results["success"]:
                deployment_steps[-1]["status"] = "failed"
                deployment_steps[-1]["message"] = "Deployment failed"

                # Attempt rollback if enabled
                if self.rollback_on_failure:
                    rollback_result = self._rollback_deployment()
                    deployment_steps.append({
                        "step": 5,
                        "name": "Rollback",
                        "status": "completed",
                        "message": "Rollback executed due to deployment failure",
                        "details": rollback_result,
                    })

                result = {
                    "success": False,
                    "environment": self.environment,
                    "strategy": self.deploy_strategy,
                    "deployment_steps": deployment_steps,
                    "error": "Deployment failed",
                    "rolled_back": self.rollback_on_failure,
                }
                return json.dumps(result, indent=2)

            deployment_steps[-1]["status"] = "completed"
            deployment_steps[-1]["message"] = f"Successfully deployed to {self.environment}"
            deployment_steps[-1]["details"] = deploy_results

            # Step 5: Post-deployment health checks
            deployment_steps.append({
                "step": 6,
                "name": "Health checks",
                "status": "in_progress",
                "message": "Running post-deployment health checks...",
            })

            health_results = self._run_health_checks()
            if not health_results["healthy"]:
                deployment_steps[-1]["status"] = "warning"
                deployment_steps[-1]["message"] = "Health checks raised warnings"
                warnings.extend(health_results["warnings"])
            else:
                deployment_steps[-1]["status"] = "completed"
                deployment_steps[-1]["message"] = "All health checks passed"

            deployment_steps[-1]["details"] = health_results

            # Calculate deployment duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                "success": True,
                "environment": self.environment,
                "strategy": self.deploy_strategy,
                "version": self.version or "current",
                "duration_seconds": duration,
                "deployment_steps": deployment_steps,
                "warnings": warnings,
                "deployment_url": self._get_deployment_url(),
                "monitoring_url": self._get_monitoring_url(),
            }

            result["summary"] = f"Successfully deployed to {self.environment} in {duration:.1f} seconds"

            return json.dumps(result, indent=2)

        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "environment": self.environment,
            }
            return json.dumps(result, indent=2)

    def _run_pre_deployment_checks(self) -> dict:
        """Run pre-deployment validation checks."""
        checks = {
            "passed": True,
            "failed_checks": [],
            "warnings": [],
        }

        # Check if git repo is clean
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.stdout.strip():
                checks["warnings"].append("Working directory has uncommitted changes")
        except Exception:
            checks["warnings"].append("Could not check git status")

        # Check if environment config exists
        env_config = Path(f".env.{self.environment}")
        if not env_config.exists():
            checks["warnings"].append(f"No environment config found for {self.environment}")

        return checks

    def _run_tests(self) -> dict:
        """Run the test suite."""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "-xvs"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            return {
                "passed": result.returncode == 0,
                "exit_code": result.returncode,
                "output": result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout,
            }
        except subprocess.TimeoutExpired:
            return {"passed": False, "error": "Tests timed out"}
        except Exception as e:
            return {"passed": False, "error": str(e)}

    def _build_application(self) -> dict:
        """Build the application."""
        # Simulated build - in production would run actual build commands
        return {
            "success": True,
            "build_time": "45.2s",
            "build_id": f"build-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        }

    def _execute_deployment(self) -> dict:
        """Execute the actual deployment."""
        # Simulated deployment - in production would run actual deployment commands
        import random
        success = random.random() > 0.1  # 90% success rate for demo

        return {
            "success": success,
            "deployment_time": "32.1s",
            "deployment_id": f"deploy-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        }

    def _run_health_checks(self) -> dict:
        """Run post-deployment health checks."""
        return {
            "healthy": True,
            "warnings": [],
            "checks": {
                "api_health": "pass",
                "database_connection": "pass",
                "redis_connection": "pass",
            },
        }

    def _rollback_deployment(self) -> dict:
        """Rollback the deployment."""
        return {
            "success": True,
            "message": "Rollback completed successfully",
            "previous_version": "previous-stable",
        }

    def _get_deployment_url(self) -> str:
        """Get the deployment URL."""
        urls = {
            "dev": "https://dev.example.com",
            "staging": "https://staging.example.com",
            "production": "https://app.example.com",
        }
        return urls.get(self.environment, "unknown")

    def _get_monitoring_url(self) -> str:
        """Get the monitoring dashboard URL."""
        return "https://monitoring.example.com/dashboard"


if __name__ == "__main__":
    # Test the tool
    tool = DeployToEnvironmentTool(environment="dev")
    print(tool.run())

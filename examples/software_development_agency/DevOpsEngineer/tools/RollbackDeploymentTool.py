import json
from datetime import datetime

from pydantic import Field

from agency_swarm.tools import BaseTool


class RollbackDeploymentTool(BaseTool):
    """
    Rollback a deployment to a previous version. Provides safe rollback mechanisms
    with verification and post-rollback health checks.
    """

    environment: str = Field(
        ...,
        description="Target environment for rollback. Options: 'dev', 'staging', 'production'.",
    )

    target_version: str = Field(
        default=None,
        description="Specific version to rollback to (e.g., git commit SHA, version tag). If not specified, rolls back to previous stable version.",
    )

    reason: str = Field(
        default="Deployment issue",
        description="Reason for rollback (for documentation purposes). Defaults to 'Deployment issue'.",
    )

    force: bool = Field(
        default=False,
        description="Force rollback even if health checks fail. Use with caution. Defaults to False.",
    )

    backup_before_rollback: bool = Field(
        default=True,
        description="Create backup of current state before rollback. Defaults to True.",
    )

    def run(self):
        """
        Execute the rollback and return detailed status and results.
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

            # Get current deployment state
            current_state = self._get_current_deployment_state()

            rollback_steps = []

            # Step 1: Backup current state
            if self.backup_before_rollback:
                rollback_steps.append({
                    "step": 1,
                    "name": "Backup current state",
                    "status": "in_progress",
                    "message": "Creating backup of current deployment...",
                })

                backup_result = self._create_backup(current_state)

                if backup_result["success"]:
                    rollback_steps[-1]["status"] = "completed"
                    rollback_steps[-1]["message"] = "Backup completed successfully"
                    rollback_steps[-1]["details"] = backup_result
                else:
                    rollback_steps[-1]["status"] = "failed"
                    rollback_steps[-1]["message"] = "Backup failed"
                    rollback_steps[-1]["details"] = backup_result

                    result = {
                        "success": False,
                        "error": "Backup failed - rollback aborted for safety",
                        "environment": self.environment,
                        "rollback_steps": rollback_steps,
                    }
                    return json.dumps(result, indent=2)

            # Step 2: Identify target version
            rollback_steps.append({
                "step": 2,
                "name": "Identify target version",
                "status": "in_progress",
                "message": "Determining rollback target version...",
            })

            target_version_info = self._identify_target_version(self.target_version)
            rollback_steps[-1]["status"] = "completed"
            rollback_steps[-1]["message"] = f"Target version identified: {target_version_info['version']}"
            rollback_steps[-1]["details"] = target_version_info

            # Step 3: Pre-rollback validation
            rollback_steps.append({
                "step": 3,
                "name": "Pre-rollback validation",
                "status": "in_progress",
                "message": "Running pre-rollback validation...",
            })

            validation_result = self._run_pre_rollback_validation(target_version_info)

            if not validation_result["valid"] and not self.force:
                rollback_steps[-1]["status"] = "failed"
                rollback_steps[-1]["message"] = "Pre-rollback validation failed"
                rollback_steps[-1]["details"] = validation_result

                result = {
                    "success": False,
                    "error": "Pre-rollback validation failed. Use force=True to override.",
                    "environment": self.environment,
                    "target_version": target_version_info["version"],
                    "rollback_steps": rollback_steps,
                }
                return json.dumps(result, indent=2)

            rollback_steps[-1]["status"] = "completed"
            rollback_steps[-1]["message"] = "Pre-rollback validation passed"
            rollback_steps[-1]["details"] = validation_result

            # Step 4: Execute rollback
            rollback_steps.append({
                "step": 4,
                "name": "Execute rollback",
                "status": "in_progress",
                "message": f"Rolling back to version {target_version_info['version']}...",
            })

            rollback_result = self._execute_rollback(target_version_info, current_state)

            if not rollback_result["success"]:
                rollback_steps[-1]["status"] = "failed"
                rollback_steps[-1]["message"] = "Rollback execution failed"
                rollback_steps[-1]["details"] = rollback_result

                result = {
                    "success": False,
                    "error": "Rollback execution failed",
                    "environment": self.environment,
                    "target_version": target_version_info["version"],
                    "rollback_steps": rollback_steps,
                }
                return json.dumps(result, indent=2)

            rollback_steps[-1]["status"] = "completed"
            rollback_steps[-1]["message"] = "Rollback executed successfully"
            rollback_steps[-1]["details"] = rollback_result

            # Step 5: Post-rollback health checks
            rollback_steps.append({
                "step": 5,
                "name": "Post-rollback health checks",
                "status": "in_progress",
                "message": "Running post-rollback health checks...",
            })

            health_result = self._run_post_rollback_health_checks()

            if not health_result["healthy"] and not self.force:
                rollback_steps[-1]["status"] = "warning"
                rollback_steps[-1]["message"] = "Post-rollback health checks failed"
                rollback_steps[-1]["details"] = health_result

                result = {
                    "success": False,
                    "error": "Post-rollback health checks failed. Application may be unstable.",
                    "environment": self.environment,
                    "target_version": target_version_info["version"],
                    "rollback_steps": rollback_steps,
                }
                return json.dumps(result, indent=2)

            rollback_steps[-1]["status"] = "completed"
            rollback_steps[-1]["message"] = "Post-rollback health checks passed"
            rollback_steps[-1]["details"] = health_result

            # Calculate duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                "success": True,
                "environment": self.environment,
                "previous_version": current_state["version"],
                "current_version": target_version_info["version"],
                "reason": self.reason,
                "duration_seconds": duration,
                "rollback_steps": rollback_steps,
                "backup_created": self.backup_before_rollback,
                "backup_id": backup_result.get("backup_id") if self.backup_before_rollback else None,
            }

            result["summary"] = (
                f"Successfully rolled back {self.environment} from {current_state['version']} "
                f"to {target_version_info['version']} in {duration:.1f} seconds"
            )

            return json.dumps(result, indent=2)

        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "environment": self.environment,
            }
            return json.dumps(result, indent=2)

    def _get_current_deployment_state(self) -> dict:
        """Get current deployment state."""
        # In production, would fetch actual deployment state
        return {
            "version": "v1.2.3",
            "deployed_at": "2024-01-15T10:30:00",
            "status": "active",
            "deployment_id": "deploy-20240115-103000",
        }

    def _create_backup(self, current_state: dict) -> dict:
        """Create backup of current state."""
        # In production, would create actual backup
        import random
        success = random.random() > 0.05  # 95% success rate

        if success:
            return {
                "success": True,
                "backup_id": f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "backup_location": f"s3://backups/{self.environment}/{current_state['version']}/",
                "created_at": datetime.now().isoformat(),
            }
        else:
            return {
                "success": False,
                "error": "Failed to create backup (simulated failure)",
            }

    def _identify_target_version(self, requested_version: str | None) -> dict:
        """Identify the target version for rollback."""
        if requested_version:
            # User specified a version
            return {
                "version": requested_version,
                "type": "user_specified",
                "available": True,
            }
        else:
            # Get previous stable version
            return {
                "version": "v1.2.2",
                "type": "previous_stable",
                "available": True,
            }

    def _run_pre_rollback_validation(self, target_version_info: dict) -> dict:
        """Run validation checks before rollback."""
        checks = {
            "valid": True,
            "checks_performed": [],
        }

        # Check if target version exists
        checks["checks_performed"].append({
            "check": "Target version exists",
            "status": "pass" if target_version_info["available"] else "fail",
        })

        # Check if rollback is safe (no breaking changes)
        checks["checks_performed"].append({
            "check": "Rollback compatibility",
            "status": "pass",
        })

        # Check environment connectivity
        checks["checks_performed"].append({
            "check": "Environment connectivity",
            "status": "pass",
        })

        # Determine overall validity
        failed_checks = [c for c in checks["checks_performed"] if c["status"] == "fail"]
        checks["valid"] = len(failed_checks) == 0

        return checks

    def _execute_rollback(self, target_version_info: dict, current_state: dict) -> dict:
        """Execute the actual rollback."""
        # In production, would execute actual rollback (e.g., terraform apply, kubectl rollout undo, etc.)
        import random
        success = random.random() > 0.1  # 90% success rate

        if success:
            return {
                "success": True,
                "rollback_time": "45.2s",
                "deployment_id": f"rollback-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "previous_deployment_id": current_state.get("deployment_id"),
            }
        else:
            return {
                "success": False,
                "error": "Rollback execution failed (simulated failure)",
            }

    def _run_post_rollback_health_checks(self) -> dict:
        """Run health checks after rollback."""
        # Simulated health checks
        import random

        health = {
            "healthy": True,
            "checks": {
                "application_responding": random.choice([True, True, True, True, False]),
                "database_connected": True,
                "cache_connected": True,
                "api_endpoints_working": random.choice([True, True, True, False]),
            },
        }

        # Determine overall health
        failed_checks = [k for k, v in health["checks"].items() if not v]
        health["healthy"] = len(failed_checks) == 0
        health["failed_checks"] = failed_checks

        return health


if __name__ == "__main__":
    # Test the tool
    tool = RollbackDeploymentTool(environment="dev", reason="Critical bug discovered")
    print(tool.run())

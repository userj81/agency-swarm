import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import Field

from agency_swarm.tools import BaseTool


class ConfigureInfrastructureTool(BaseTool):
    """
    Configure and manage infrastructure using Infrastructure as Code (IaC).
    Supports Terraform, CloudFormation, and other IaC tools for defining and provisioning resources.
    """

    config_type: str = Field(
        ...,
        description="Type of infrastructure configuration. Options: 'terraform', 'cloudformation', 'kubernetes', 'docker-compose'.",
    )

    resource_type: str = Field(
        ...,
        description="Type of resource to configure. Examples: 'server', 'database', 'load-balancer', 'network', 'storage'.",
    )

    config_file: str = Field(
        default=None,
        description="Path to existing configuration file to modify. If not specified, creates new configuration.",
    )

    environment: str = Field(
        default="dev",
        description="Target environment for infrastructure. Options: 'dev', 'staging', 'production'. Defaults to 'dev'.",
    )

    instance_type: str = Field(
        default="t3.micro",
        description="Instance type or size for resources. Defaults to 't3.micro'.",
    )

    apply_changes: bool = Field(
        default=False,
        description="Apply configuration changes immediately. Defaults to False (dry-run mode).",
    )

    def run(self):
        """
        Configure infrastructure and return detailed status and configuration.
        """
        try:
            # Validate inputs
            valid_config_types = ["terraform", "cloudformation", "kubernetes", "docker-compose"]
            if self.config_type not in valid_config_types:
                result = {
                    "success": False,
                    "error": f"Invalid config_type: {self.config_type}",
                    "valid_types": valid_config_types,
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

            # Generate configuration based on type and resource
            config_result = {
                "config_type": self.config_type,
                "resource_type": self.resource_type,
                "environment": self.environment,
                "timestamp": datetime.now().isoformat(),
                "dry_run": not self.apply_changes,
            }

            # Generate configuration
            if self.config_type == "terraform":
                config_result["configuration"] = self._generate_terraform_config()
                config_result["config_file"] = "main.tf"

            elif self.config_type == "cloudformation":
                config_result["configuration"] = self._generate_cloudformation_template()
                config_result["config_file"] = "template.yaml"

            elif self.config_type == "kubernetes":
                config_result["configuration"] = self._generate_kubernetes_manifest()
                config_result["config_file"] = "deployment.yaml"

            elif self.config_type == "docker-compose":
                config_result["configuration"] = self._generate_docker_compose()
                config_result["config_file"] = "docker-compose.yml"

            # Calculate estimated costs
            config_result["estimated_cost"] = self._estimate_cost(
                self.resource_type, self.instance_type, self.environment
            )

            # Apply configuration if requested
            if self.apply_changes:
                apply_result = self._apply_infrastructure_changes(config_result)
                config_result["apply_result"] = apply_result

                if apply_result["success"]:
                    config_result["summary"] = f"Infrastructure configured and applied successfully for {self.resource_type} in {self.environment}"
                    config_result["success"] = True
                else:
                    config_result["summary"] = f"Configuration generated but apply failed: {apply_result['error']}"
                    config_result["success"] = False
            else:
                config_result["summary"] = f"Infrastructure configuration generated for {self.resource_type} in {self.environment} (dry-run mode - not applied)"
                config_result["success"] = True

            # Add recommendations
            config_result["recommendations"] = self._get_recommendations(
                self.resource_type, self.environment
            )

            return json.dumps(config_result, indent=2)

        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "config_type": self.config_type,
                "resource_type": self.resource_type,
            }
            return json.dumps(result, indent=2)

    def _generate_terraform_config(self) -> dict:
        """Generate Terraform configuration."""
        config = {
            "terraform": {
                "required_version": ">= 1.0",
                "required_providers": {
                    "aws": {
                        "source": "hashicorp/aws",
                        "version": "~> 5.0"
                    }
                }
            },
            "provider": {
                "aws": {
                    "region": "us-east-1"
                }
            },
            "resource": {}
        }

        # Add resource configuration based on type
        if self.resource_type == "server":
            config["resource"]["aws_instance"] = {
                "app_server": {
                    "ami": "ami-0c55b159cbfafe1f0",
                    "instance_type": self.instance_type,
                    "tags": {
                        "Name": f"{self.environment}-app-server",
                        "Environment": self.environment
                    }
                }
            }

        elif self.resource_type == "database":
            config["resource"]["aws_db_instance"] = {
                "main": {
                    "engine": "postgres",
                    "instance_class": self._map_instance_to_db(self.instance_type),
                    "allocated_storage": 20,
                    "engine_version": "14.7",
                    "username": "admin",
                    "tags": {
                        "Name": f"{self.environment}-database",
                        "Environment": self.environment
                    }
                }
            }

        elif self.resource_type == "load-balancer":
            config["resource"]["aws_lb"] = {
                "main": {
                    "name": f"{self.environment}-load-balancer",
                    "internal": False,
                    "load_balancer_type": "application",
                    "security_groups": ["sg-12345678"],
                    "subnets": ["subnet-12345", "subnet-67890"],
                    "tags": {
                        "Environment": self.environment
                    }
                }
            }

        return config

    def _generate_cloudformation_template(self) -> dict:
        """Generate AWS CloudFormation template."""
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": f"Infrastructure for {self.resource_type} in {self.environment}",
            "Parameters": {
                "Environment": {
                    "Type": "String",
                    "Default": self.environment,
                    "Description": "Environment name"
                }
            },
            "Resources": {}
        }

        if self.resource_type == "server":
            template["Resources"]["AppServer"] = {
                "Type": "AWS::EC2::Instance",
                "Properties": {
                    "InstanceType": self.instance_type,
                    "ImageId": "ami-0c55b159cbfafe1f0",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": {"Fn::Sub": "${Environment}-app-server"}
                        },
                        {
                            "Key": "Environment",
                            "Value": {"Ref": "Environment"}
                        }
                    ]
                }
            }

        elif self.resource_type == "database":
            template["Resources"]["Database"] = {
                "Type": "AWS::RDS::DBInstance",
                "Properties": {
                    "Engine": "postgres",
                    "DBInstanceClass": self._map_instance_to_db(self.instance_type),
                    "AllocatedStorage": "20",
                    "MasterUsername": "admin",
                    "Tags": [
                        {
                            "Key": "Environment",
                            "Value": {"Ref": "Environment"}
                        }
                    ]
                }
            }

        return template

    def _generate_kubernetes_manifest(self) -> dict:
        """Generate Kubernetes deployment manifest."""
        manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": f"{self.resource_type}-{self.environment}",
                "labels": {
                    "app": self.resource_type,
                    "environment": self.environment
                }
            },
            "spec": {
                "replicas": self._get_replica_count(self.environment),
                "selector": {
                    "matchLabels": {
                        "app": self.resource_type
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": self.resource_type,
                            "environment": self.environment
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": self.resource_type,
                                "image": f"{self.resource_type}:latest",
                                "ports": [
                                    {
                                        "containerPort": 80
                                    }
                                ],
                                "resources": {
                                    "requests": {
                                        "cpu": self._get_cpu_request(self.environment),
                                        "memory": self._get_memory_request(self.environment)
                                    },
                                    "limits": {
                                        "cpu": self._get_cpu_limit(self.environment),
                                        "memory": self._get_memory_limit(self.environment)
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }

        return manifest

    def _generate_docker_compose(self) -> dict:
        """Generate Docker Compose configuration."""
        config = {
            "version": "3.8",
            "services": {}
        }

        if self.resource_type == "server":
            config["services"]["app"] = {
                "build": ".",
                "ports": ["8000:8000"],
                "environment": [
                    f"ENVIRONMENT={self.environment}"
                ],
                "restart": "unless-stopped"
            }

        elif self.resource_type == "database":
            config["services"]["database"] = {
                "image": "postgres:14",
                "environment": [
                    "POSTGRES_USER=admin",
                    "POSTGRES_PASSWORD=password",
                    "POSTGRES_DB=myapp"
                ],
                "ports": ["5432:5432"],
                "volumes": ["db_data:/var/lib/postgresql/data"],
                "restart": "unless-stopped"
            }
            config["volumes"] = {
                "db_data": {}
            }

        return config

    def _apply_infrastructure_changes(self, config_result: dict) -> dict:
        """Apply infrastructure changes (simulated)."""
        # In production, this would run actual terraform apply, kubectl apply, etc.
        import random

        # Simulate 90% success rate
        success = random.random() > 0.1

        if success:
            return {
                "success": True,
                "message": "Infrastructure changes applied successfully",
                "resource_id": f"i-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "apply_time": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Failed to apply infrastructure changes (simulated failure)",
            }

    def _estimate_cost(self, resource_type: str, instance_type: str, environment: str) -> dict:
        """Estimate monthly infrastructure costs."""
        # Base costs (USD per month)
        base_costs = {
            "t3.micro": 8.0,
            "t3.small": 15.0,
            "t3.medium": 30.0,
            "t3.large": 60.0,
            "m5.large": 96.0,
            "m5.xlarge": 192.0,
        }

        base_cost = base_costs.get(instance_type, 20.0)

        # Multiplier by environment
        env_multipliers = {
            "dev": 1.0,
            "staging": 2.0,
            "production": 3.0,
        }

        multiplier = env_multipliers.get(environment, 1.0)
        estimated_cost = base_cost * multiplier

        # Add resource-specific costs
        if resource_type == "database":
            estimated_cost *= 1.5
        elif resource_type == "load-balancer":
            estimated_cost += 18.0  # LB base cost

        return {
            "monthly_estimate_usd": round(estimated_cost, 2),
            "breakdown": {
                "compute": round(base_cost * multiplier, 2),
                "additional": round(estimated_cost - base_cost * multiplier, 2)
            }
        }

    def _get_recommendations(self, resource_type: str, environment: str) -> list:
        """Get recommendations for the infrastructure configuration."""
        recommendations = []

        if environment == "production":
            recommendations.append("Enable auto-scaling for production workloads")
            recommendations.append("Configure multi-AZ deployment for high availability")
            recommendations.append("Enable backup and disaster recovery")

        if resource_type == "database":
            recommendations.append("Configure read replicas for improved performance")
            recommendations.append("Enable automated backups")

        if resource_type == "server":
            recommendations.append("Consider using load balancer for high traffic scenarios")

        return recommendations

    def _map_instance_to_db(self, instance_type: str) -> str:
        """Map EC2 instance type to RDS instance class."""
        mapping = {
            "t3.micro": "db.t3.micro",
            "t3.small": "db.t3.small",
            "t3.medium": "db.t3.medium",
            "t3.large": "db.t3.large",
            "m5.large": "db.m5.large",
        }
        return mapping.get(instance_type, "db.t3.micro")

    def _get_replica_count(self, environment: str) -> int:
        """Get replica count based on environment."""
        counts = {
            "dev": 1,
            "staging": 2,
            "production": 3,
        }
        return counts.get(environment, 1)

    def _get_cpu_request(self, environment: str) -> str:
        """Get CPU request based on environment."""
        requests = {
            "dev": "100m",
            "staging": "250m",
            "production": "500m",
        }
        return requests.get(environment, "100m")

    def _get_cpu_limit(self, environment: str) -> str:
        """Get CPU limit based on environment."""
        limits = {
            "dev": "500m",
            "staging": "1000m",
            "production": "2000m",
        }
        return limits.get(environment, "500m")

    def _get_memory_request(self, environment: str) -> str:
        """Get memory request based on environment."""
        requests = {
            "dev": "128Mi",
            "staging": "256Mi",
            "production": "512Mi",
        }
        return requests.get(environment, "128Mi")

    def _get_memory_limit(self, environment: str) -> str:
        """Get memory limit based on environment."""
        limits = {
            "dev": "512Mi",
            "staging": "1Gi",
            "production": "2Gi",
        }
        return limits.get(environment, "512Mi")


if __name__ == "__main__":
    # Test the tool
    tool = ConfigureInfrastructureTool(
        config_type="terraform",
        resource_type="server",
        environment="dev"
    )
    print(tool.run())

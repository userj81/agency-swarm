# Software Development Agency

A multi-agent system for automated software development workflows using Agency Swarm.

## Overview

This agency demonstrates a complete software development lifecycle with 4 specialized agents working together to deliver software features from concept to deployment.

## Agents

### CEO (Chief Executive Officer)
- **Role**: Coordinates the entire workflow and makes high-level decisions
- **Responsibilities**:
  - Receives and analyzes user requests
  - Delegates tasks to appropriate team members
  - Monitors progress and ensures deadlines are met
  - Compiles final responses for stakeholders

### Developer
- **Role**: Implements features and writes code
- **Responsibilities**:
  - Implements features according to requirements
  - Writes clean, maintainable code
  - Fixes bugs and issues
  - Follows coding standards and best practices

### QA Tester (Quality Assurance Specialist)
- **Role**: Ensures software quality through testing
- **Responsibilities**:
  - Designs and executes test plans
  - Reviews code for bugs and quality issues
  - Validates requirements and acceptance criteria
  - Reports findings with severity classifications

### DevOps Engineer
- **Role**: Manages infrastructure and deployments
- **Responsibilities**:
  - Designs and maintains CI/CD pipelines
  - Manages infrastructure as code
  - Executes deployments (rolling, blue-green, canary)
  - Sets up monitoring and alerting

## Workflow

```
User Request
    ↓
CEO (analyzes and delegates)
    ↓
Developer (implements feature)
    ↓
QA Tester (tests and validates)
    ↓ (if passes)
DevOps Engineer (deploys)
    ↓
CEO (compiles final response)

    ↓ (if QA fails)
Developer (fixes issues)
    ↓
QA Tester (re-tests)
```

## Tools

### QA Tester Tools (6)
1. **RunTestsTool** - Execute test suites (pytest, jest, unittest)
2. **GenerateCoverageReportTool** - Generate code coverage reports
3. **AnalyzeCodeQualityTool** - Analyze complexity, duplication, maintainability
4. **ReviewCodeForBugsTool** - Review code for bugs and security issues
5. **ValidateRequirementsTool** - Validate against requirements
6. **GenerateTestCasesTool** - Generate test case suggestions

### DevOps Engineer Tools (7)
1. **DeployToEnvironmentTool** - Deploy to dev/staging/production
2. **RunCICDPipelineTool** - Execute CI/CD pipelines
3. **MonitorApplicationTool** - Monitor metrics and logs
4. **ConfigureInfrastructureTool** - Configure IaC (Terraform, CloudFormation)
5. **RollbackDeploymentTool** - Rollback failed deployments
6. **GenerateDeploymentReportTool** - Generate deployment analytics
7. **SetupMonitoringTool** - Set up monitoring and alerting

## Usage

### Basic Usage
```bash
python main.py "Implement a user authentication system with login, logout, and password reset"
```

### Interactive Mode
```bash
python main.py --interactive
```

### Generate Visualization
```bash
python main.py --visualize
```

## Communication Flows

The agency uses the following communication patterns:

1. **CEO → Developer**: Task delegation with requirements
2. **Developer → QA Tester**: Submit code for testing
3. **QA Tester → DevOps Engineer**: Approved code for deployment
4. **QA Tester → Developer**: Failed tests with feedback
5. **DevOps Engineer → Developer**: Infrastructure requirements

## Example Workflows

### Feature Development
1. User: "Add a comments feature to the blog"
2. CEO analyzes and delegates to Developer
3. Developer implements comments system
4. QA Tester tests the feature
5. DevOps Engineer deploys to production
6. CEO confirms completion

### Bug Fix
1. User: "The login form is not working"
2. CEO prioritizes and delegates to Developer
3. Developer fixes the bug
4. QA Tester verifies the fix
5. DevOps Engineer deploys hotfix
6. CEO confirms resolution

## Customization

### Adding New Tools
Create tools in the agent's `tools/` directory following the BaseTool pattern:

```python
from agency_swarm.tools import BaseTool
from pydantic import Field

class MyCustomTool(BaseTool):
    """Description of what the tool does."""

    param1: str = Field(..., description="Parameter description")

    def run(self):
        # Tool implementation
        return json.dumps({"result": "success"})
```

### Modifying Communication Flows
Edit `main.py` to change how agents communicate:

```python
agency = Agency(
    ceo,
    communication_flows=[
        ceo > developer,
        developer > qa_tester,
        qa_tester > devops_engineer,
        # Add or modify flows here
    ],
)
```

## Project Structure

```
software_development_agency/
├── CEO/
│   ├── CEO.py
│   ├── instructions.md
│   └── __init__.py
├── Developer/
│   ├── Developer.py
│   ├── instructions.md
│   ├── tools/
│   │   └── __init__.py
│   └── __init__.py
├── QATester/
│   ├── QATester.py
│   ├── instructions.md
│   ├── tools/
│   │   ├── RunTestsTool.py
│   │   ├── GenerateCoverageReportTool.py
│   │   ├── AnalyzeCodeQualityTool.py
│   │   ├── ReviewCodeForBugsTool.py
│   │   ├── ValidateRequirementsTool.py
│   │   ├── GenerateTestCasesTool.py
│   │   └── __init__.py
│   └── __init__.py
├── DevOpsEngineer/
│   ├── DevOpsEngineer.py
│   ├── instructions.md
│   ├── tools/
│   │   ├── DeployToEnvironmentTool.py
│   │   ├── RunCICDPipelineTool.py
│   │   ├── MonitorApplicationTool.py
│   │   ├── ConfigureInfrastructureTool.py
│   │   ├── RollbackDeploymentTool.py
│   │   ├── GenerateDeploymentReportTool.py
│   │   ├── SetupMonitoringTool.py
│   │   └── __init__.py
│   └── __init__.py
├── main.py
├── agency_manifesto.md
└── README.md
```

## Requirements

- Python 3.9+
- agency-swarm (from parent project)
- OpenAI API key

## License

This example is part of the Agency Swarm project.

from agency_swarm import Agent


devops_engineer = Agent(
    name="DevOpsEngineer",
    description=(
        "DevOps Engineer responsible for infrastructure management, CI/CD pipelines, "
        "deployment automation, monitoring, and operational excellence."
    ),
    instructions="./instructions.md",
    tools_folder="./tools",
    model="gpt-4o-mini",
)

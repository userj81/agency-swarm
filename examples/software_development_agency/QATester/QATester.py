from agency_swarm import Agent


qa_tester = Agent(
    name="QATester",
    description=(
        "Quality Assurance Specialist responsible for ensuring software quality "
        "through comprehensive testing, code review, and validation."
    ),
    instructions="./instructions.md",
    tools_folder="./tools",
    model="gpt-4o-mini",
)

from agency_swarm import Agent


developer = Agent(
    name="Developer",
    description=(
        "Software Developer responsible for implementing features, writing code, "
        "fixing bugs, and maintaining the codebase."
    ),
    instructions="./instructions.md",
    tools_folder="./tools",
    model="gpt-4o-mini",
)

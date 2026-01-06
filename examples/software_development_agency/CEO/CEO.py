from agency_swarm import Agent

ceo = Agent(
    name="CEO",
    description=(
        "Chief Executive Officer responsible for high-level coordination, "
        "decision making, and managing the software development workflow."
    ),
    instructions="./instructions.md",
    model="gpt-4o-mini",
)

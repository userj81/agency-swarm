#!/usr/bin/env python3
"""
Software Development Agency - Main Script

This script sets up and runs a software development agency with 4 agents:
1. CEO - Coordinates the workflow and makes decisions
2. Developer - Implements features and writes code
3. QATester - Tests software and ensures quality
4. DevOpsEngineer - Manages infrastructure and deployments

Usage:
    python main.py "Implement a login feature with tests and deploy it"
"""

import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from CEO import ceo
from Developer import developer
from DevOpsEngineer import devops_engineer
from QATester import qa_tester

from agency_swarm import Agency


def get_agency():
    """
    Create and configure the Software Development Agency.

    The agency follows this workflow:
    1. User requests feature → CEO
    2. CEO delegates to Developer
    3. Developer implements → sends to QA
    4. QA Tester tests and validates
    5. If QA passes → DevOps deploys → CEO compiles final response
    6. If QA fails → returns to Developer with feedback
    """
    agency = Agency(
        ceo,  # Entry point agent
        communication_flows=[
            # CEO can delegate to all team members
            ceo > developer,
            ceo > qa_tester,
            ceo > devops_engineer,

            # Developer sends work to QA for testing
            developer > qa_tester,

            # QA Tester sends to DevOps for deployment (after tests pass)
            qa_tester > devops_engineer,

            # DevOps can coordinate with Developer (infrastructure needs)
            devops_engineer > developer,
        ],
        name="Software Development Agency",
        shared_instructions=(
            "This is a software development agency. "
            "Follow the standard development workflow: "
            "CEO → Developer → QA Tester → DevOps Engineer → CEO. "
            "Quality and reliability are top priorities. "
            "Always communicate clearly about progress, blockers, and decisions."
        ),
    )

    return agency


def main():
    """Main entry point for running the agency."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Software Development Agency - Multi-Agent System"
    )
    parser.add_argument(
        "message",
        nargs="?",
        help="Message/task for the agency to work on",
        default="Introduce yourself and explain your role",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate and display agency visualization",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )

    args = parser.parse_args()

    # Create the agency
    print("Initializing Software Development Agency...")
    print("=" * 60)
    print("Team Members:")
    print("  - CEO: Coordinates workflow and makes decisions")
    print("  - Developer: Implements features and writes code")
    print("  - QA Tester: Tests software and ensures quality")
    print("  - DevOps Engineer: Manages infrastructure and deployments")
    print("=" * 60)
    print()

    agency = get_agency()

    # Generate visualization if requested
    if args.visualize:
        print("Generating agency visualization...")
        output_file = agency.visualize(
            output_file="software_development_agency.html",
            include_tools=True,
            open_browser=True,
        )
        print(f"Visualization saved to: {output_file}")
        print()

    # Run in interactive mode or single message mode
    if args.interactive:
        print("Starting interactive mode...")
        print("Type 'quit' or 'exit' to stop")
        print("-" * 60)

        while True:
            try:
                user_input = input("\nYou: ").strip()

                if user_input.lower() in ["quit", "exit", "q"]:
                    print("Goodbye!")
                    break

                if not user_input:
                    continue

                print("\nAgency is working...")
                result = agency.get_completion(user_input)
                print(f"\nCEO: {result}")

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
    else:
        # Single message mode
        print(f"Task: {args.message}")
        print("-" * 60)
        print("\nAgency is working...\n")

        result = agency.get_completion(args.message)

        print("-" * 60)
        print(f"\nFinal Result:\n{result}")


if __name__ == "__main__":
    main()

import json
import subprocess
from pathlib import Path

from pydantic import Field

from agency_swarm.tools import BaseTool


class RunTestsTool(BaseTool):
    """
    Execute test suites and return results including pass/fail status, errors, and coverage information.
    Supports multiple test frameworks (pytest, jest, unittest, etc.) and provides detailed output.
    """

    test_path: str = Field(
        ...,
        description="Path to test file or directory to run tests from. Can be a specific file (e.g., 'tests/test_api.py') or a directory (e.g., 'tests/').",
    )

    test_framework: str = Field(
        default="pytest",
        description="Testing framework to use. Options: 'pytest', 'unittest', 'jest', 'mocha', 'robot'. Defaults to 'pytest'.",
    )

    coverage: bool = Field(
        default=True,
        description="Generate coverage report alongside test results. Defaults to True.",
    )

    verbose: bool = Field(
        default=False,
        description="Enable verbose output for detailed test information. Defaults to False.",
    )

    extra_args: str = Field(
        default="",
        description="Additional command line arguments to pass to the test runner (e.g., '-v -k test_login'). Defaults to empty string.",
    )

    def run(self):
        """
        Execute the test suite and return comprehensive results.
        """
        try:
            test_path = Path(self.test_path)

            if not test_path.exists():
                result = {
                    "success": False,
                    "error": f"Test path does not exist: {self.test_path}",
                    "test_path": self.test_path,
                    "test_framework": self.test_framework,
                }
                return json.dumps(result, indent=2)

            # Build command based on framework
            if self.test_framework == "pytest":
                cmd = ["python", "-m", "pytest", str(test_path)]

                if self.coverage:
                    cmd = ["python", "-m", "coverage", "run", "-m", "pytest", str(test_path)]

                if self.verbose:
                    cmd.append("-v")

                if self.extra_args:
                    cmd.extend(self.extra_args.split())

            elif self.test_framework == "unittest":
                cmd = ["python", "-m", "unittest", "discover", "-s", str(test_path)]

                if self.verbose:
                    cmd.append("-v")

                if self.extra_args:
                    cmd.extend(self.extra_args.split())

            elif self.test_framework == "jest":
                cmd = ["npx", "jest", str(test_path)]

                if self.coverage:
                    cmd.append("--coverage")

                if self.verbose:
                    cmd.append("--verbose")

                if self.extra_args:
                    cmd.extend(self.extra_args.split())

            elif self.test_framework == "mocha":
                cmd = ["npx", "mocha", str(test_path)]

                if self.extra_args:
                    cmd.extend(self.extra_args.split())

            else:
                result = {
                    "success": False,
                    "error": f"Unsupported test framework: {self.test_framework}",
                    "supported_frameworks": ["pytest", "unittest", "jest", "mocha", "robot"],
                }
                return json.dumps(result, indent=2)

            # Execute tests
            result_process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            # Parse output for key metrics
            stdout = result_process.stdout
            stderr = result_process.stderr

            # Extract test counts from pytest output
            tests_run = 0
            tests_passed = 0
            tests_failed = 0

            if self.test_framework == "pytest" and " passed" in stdout:
                try:
                    # Parse "X passed in Y seconds"
                    for line in stdout.split("\n"):
                        if " passed" in line or " failed" in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part.isdigit():
                                    if "passed" in parts[i + 1] if i + 1 < len(parts) else False:
                                        tests_passed = int(part)
                                    elif "failed" in parts[i + 1] if i + 1 < len(parts) else False:
                                        tests_failed = int(part)
                    tests_run = tests_passed + tests_failed
                except Exception:
                    tests_run = -1  # Unable to parse

            # Get coverage if using pytest with coverage
            coverage_percent = None
            if self.coverage and self.test_framework == "pytest":
                try:
                    coverage_result = subprocess.run(
                        ["python", "-m", "coverage", "report", "--format=json"],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if coverage_result.stdout:
                        coverage_data = json.loads(coverage_result.stdout)
                        coverage_percent = coverage_data.get("totals", {}).get("percent_covered")
                except Exception:
                    pass

            # Build result
            result = {
                "success": result_process.returncode == 0,
                "exit_code": result_process.returncode,
                "test_framework": self.test_framework,
                "test_path": self.test_path,
                "tests_run": tests_run if tests_run > 0 else "unable to parse",
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "coverage_percent": coverage_percent,
                "stdout": stdout[-2000:] if len(stdout) > 2000 else stdout,  # Truncate long output
                "stderr": stderr[-1000:] if len(stderr) > 1000 else stderr,
                "command": " ".join(cmd),
            }

            # Add summary
            if result["success"]:
                result["summary"] = f"All tests passed successfully! ({tests_run} tests)"
            else:
                result["summary"] = f"Tests failed. {tests_failed} of {tests_run} tests failed."

            return json.dumps(result, indent=2)

        except subprocess.TimeoutExpired:
            result = {
                "success": False,
                "error": "Test execution timed out after 5 minutes",
                "test_path": self.test_path,
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "test_path": self.test_path,
                "test_framework": self.test_framework,
            }
            return json.dumps(result, indent=2)


if __name__ == "__main__":
    # Test the tool
    tool = RunTestsTool(test_path=".", test_framework="pytest")
    print(tool.run())

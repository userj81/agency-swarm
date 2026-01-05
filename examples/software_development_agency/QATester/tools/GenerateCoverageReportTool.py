import json
import subprocess
from pathlib import Path

from pydantic import Field

from agency_swarm.tools import BaseTool


class GenerateCoverageReportTool(BaseTool):
    """
    Generate comprehensive code coverage reports showing which parts of the codebase are tested.
    Supports multiple coverage tools and formats (HTML, JSON, terminal).
    """

    source_path: str = Field(
        ...,
        description="Path to the source code directory or file to analyze coverage for (e.g., 'src/', 'src/mymodule.py').",
    )

    coverage_format: str = Field(
        default="json",
        description="Output format for the coverage report. Options: 'json', 'html', 'terminal', 'xml'. Defaults to 'json'.",
    )

    output_file: str = Field(
        default=None,
        description="Optional output file path for saving the report. If not specified, uses default location.",
    )

    fail_under: float = Field(
        default=None,
        description="Optional coverage threshold. If coverage is below this percentage, the tool reports a failure. Range: 0-100.",
    )

    omit_patterns: str = Field(
        default="",
        description="Comma-separated file patterns to omit from coverage (e.g., '*/tests/*,*/__init__.py'). Defaults to empty.",
    )

    def run(self):
        """
        Generate the coverage report and return detailed results.
        """
        try:
            source_path = Path(self.source_path)

            if not source_path.exists():
                result = {
                    "success": False,
                    "error": f"Source path does not exist: {self.source_path}",
                    "source_path": self.source_path,
                }
                return json.dumps(result, indent=2)

            # Try to use coverage.py (Python)
            cmd = ["python", "-m", "coverage", "report", "--include", str(source_path / "*.py")]

            # Add omit patterns
            if self.omit_patterns:
                cmd.extend(["--omit", self.omit_patterns])

            # Add fail_under if specified
            if self.fail_under is not None:
                cmd.extend(["--fail-under", str(self.fail_under)])

            # First, try to get JSON report
            if self.coverage_format == "json":
                json_cmd = cmd.copy()
                json_cmd.extend(["--format", "json"])

                result_process = subprocess.run(
                    json_cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result_process.returncode == 0 and result_process.stdout:
                    try:
                        coverage_data = json.loads(result_process.stdout)

                        # Generate a comprehensive report
                        result = {
                            "success": True,
                            "format": "json",
                            "source_path": self.source_path,
                            "totals": coverage_data.get("totals", {}),
                            "files": coverage_data.get("files", {}),
                            "summary": self._generate_summary(coverage_data),
                        }

                        return json.dumps(result, indent=2)
                    except json.JSONDecodeError:
                        pass

            # Fallback to terminal report
            cmd = ["python", "-m", "coverage", "report"]
            if self.omit_patterns:
                cmd.extend(["--omit", self.omit_patterns])

            result_process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            stdout = result_process.stdout
            stderr = result_process.stderr

            # Parse terminal output for key metrics
            total_lines = None
            total_covered = None
            coverage_percent = None

            for line in stdout.split("\n"):
                if line.startswith("TOTAL"):
                    parts = line.split()
                    if len(parts) >= 5:
                        try:
                            total_lines = int(parts[-3].replace(",", ""))
                            total_covered = int(parts[-2].replace(",", ""))
                            coverage_percent_str = parts[1].replace("%", "")
                            coverage_percent = float(coverage_percent_str)
                        except (ValueError, IndexError):
                            pass

            # Check if coverage met threshold
            meets_threshold = True
            if self.fail_under is not None and coverage_percent is not None:
                meets_threshold = coverage_percent >= self.fail_under

            result = {
                "success": result_process.returncode == 0 and meets_threshold,
                "format": "terminal",
                "source_path": self.source_path,
                "coverage_percent": coverage_percent,
                "total_lines": total_lines,
                "lines_covered": total_covered,
                "lines_missing": total_lines - total_covered if total_lines and total_covered else None,
                "meets_threshold": meets_threshold,
                "threshold": self.fail_under,
                "output": stdout[-3000:] if len(stdout) > 3000 else stdout,
                "stderr": stderr[-1000:] if len(stderr) > 1000 else stderr,
                "command": " ".join(cmd),
            }

            # Generate summary
            if coverage_percent:
                if meets_threshold:
                    result["summary"] = f"Coverage: {coverage_percent:.1f}% - Meets threshold of {self.fail_under}%"
                else:
                    result["summary"] = f"Coverage: {coverage_percent:.1f}% - Below threshold of {self.fail_under}%"
            else:
                result["summary"] = "Unable to parse coverage metrics. Check output for details."

            return json.dumps(result, indent=2)

        except subprocess.TimeoutExpired:
            result = {
                "success": False,
                "error": "Coverage generation timed out after 60 seconds",
                "source_path": self.source_path,
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "source_path": self.source_path,
            }
            return json.dumps(result, indent=2)

    def _generate_summary(self, coverage_data):
        """Generate a human-readable summary from coverage data."""
        totals = coverage_data.get("totals", {})
        summary = []

        if "percent_covered" in totals:
            percent = totals["percent_covered"]
            summary.append(f"Overall Coverage: {percent:.1f}%")

        if "covered_lines" in totals and "num_statements" in totals:
            covered = totals["covered_lines"]
            total = totals["num_statements"]
            missing = total - covered
            summary.append(f"Lines: {covered}/{total} covered ({missing} missing)")

        if "num_branches" in totals and "covered_branches" in totals:
            branches = totals["num_branches"]
            covered = totals["covered_branches"]
            branch_percent = (covered / branches * 100) if branches > 0 else 0
            summary.append(f"Branches: {covered}/{branches} covered ({branch_percent:.1f}%)")

        return " | ".join(summary) if summary else "Unable to generate summary"


if __name__ == "__main__":
    # Test the tool
    tool = GenerateCoverageReportTool(source_path=".")
    print(tool.run())

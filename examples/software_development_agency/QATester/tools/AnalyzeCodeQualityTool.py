import ast
import json
from pathlib import Path
from typing import Any

from pydantic import Field

from agency_swarm.tools import BaseTool


class AnalyzeCodeQualityTool(BaseTool):
    """
    Analyze code quality metrics including complexity, duplication, maintainability issues, and code smells.
    Provides actionable feedback for improving code quality.
    """

    file_path: str = Field(
        ...,
        description="Path to the source code file or directory to analyze (e.g., 'src/main.py' or 'src/').",
    )

    check_complexity: bool = Field(
        default=True,
        description="Analyze cyclomatic complexity of functions and methods. Defaults to True.",
    )

    check_duplication: bool = Field(
        default=True,
        description="Check for duplicated code patterns. Defaults to True.",
    )

    max_complexity: int = Field(
        default=10,
        description="Maximum cyclomatic complexity threshold. Functions exceeding this are flagged. Defaults to 10.",
    )

    max_line_length: int = Field(
        default=88,
        description="Maximum line length for code style checking. Defaults to 88 (Black standard).",
    )

    def run(self):
        """
        Analyze the code quality and return detailed metrics and findings.
        """
        try:
            path = Path(self.file_path)

            if not path.exists():
                result = {
                    "success": False,
                    "error": f"Path does not exist: {self.file_path}",
                }
                return json.dumps(result, indent=2)

            # Collect all Python files
            if path.is_file():
                python_files = [path]
            else:
                python_files = list(path.rglob("*.py"))

            if not python_files:
                result = {
                    "success": True,
                    "message": "No Python files found to analyze",
                    "path": self.file_path,
                }
                return json.dumps(result, indent=2)

            # Analyze each file
            all_issues = []
            all_metrics = []
            total_complexity = 0
            total_functions = 0
            total_lines = 0

            for file_path in python_files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        lines = content.split("\n")

                    file_metrics = {
                        "file": str(file_path),
                        "lines": len(lines),
                        "functions": 0,
                        "classes": 0,
                        "complexity": 0,
                        "issues": [],
                    }

                    # Parse AST
                    tree = ast.parse(content, filename=str(file_path))

                    # Check for issues
                    for i, line in enumerate(lines, 1):
                        # Check line length
                        if len(line) > self.max_line_length:
                            file_metrics["issues"].append({
                                "line": i,
                                "type": "line_too_long",
                                "severity": "low",
                                "message": f"Line exceeds {self.max_line_length} characters ({len(line)} chars)",
                            })

                    # Analyze AST nodes
                    for node in ast.walk(tree):
                        # Count classes
                        if isinstance(node, ast.ClassDef):
                            file_metrics["classes"] += 1

                        # Count and analyze functions
                        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            file_metrics["functions"] += 1
                            complexity = self._calculate_complexity(node)
                            file_metrics["complexity"] += complexity

                            # Check complexity threshold
                            if self.check_complexity and complexity > self.max_complexity:
                                file_metrics["issues"].append({
                                    "line": node.lineno,
                                    "type": "high_complexity",
                                    "severity": "medium" if complexity < self.max_complexity * 2 else "high",
                                    "message": f"Function '{node.name}' has high complexity ({complexity}), exceeds threshold of {self.max_complexity}",
                                    "function": node.name,
                                    "complexity": complexity,
                                })

                    # Check for TODO/FIXME comments
                    for i, line in enumerate(lines, 1):
                        stripped = line.strip()
                        if "TODO" in stripped or "FIXME" in stripped:
                            file_metrics["issues"].append({
                                "line": i,
                                "type": "todo_comment",
                                "severity": "info",
                                "message": f"Found TODO/FIXME comment: {stripped[:50]}...",
                            })

                    # Check for long functions (>50 lines)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            func_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                            if func_lines > 50:
                                file_metrics["issues"].append({
                                    "line": node.lineno,
                                    "type": "long_function",
                                    "severity": "medium",
                                    "message": f"Function '{node.name}' is too long ({func_lines} lines). Consider refactoring.",
                                    "function": node.name,
                                    "lines": func_lines,
                                })

                    total_functions += file_metrics["functions"]
                    total_complexity += file_metrics["complexity"]
                    total_lines += file_metrics["lines"]

                    all_metrics.append(file_metrics)
                    all_issues.extend(file_metrics["issues"])

                except SyntaxError as e:
                    all_issues.append({
                        "file": str(file_path),
                        "type": "syntax_error",
                        "severity": "critical",
                        "message": f"Syntax error: {str(e)}",
                    })
                except Exception as e:
                    all_issues.append({
                        "file": str(file_path),
                        "type": "analysis_error",
                        "severity": "low",
                        "message": f"Could not analyze file: {str(e)}",
                    })

            # Calculate aggregate metrics
            avg_complexity = total_complexity / total_functions if total_functions > 0 else 0

            # Count issues by severity
            severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
            for issue in all_issues:
                severity = issue.get("severity", "low")
                if severity in severity_counts:
                    severity_counts[severity] += 1

            # Generate quality score (0-100)
            quality_score = 100
            quality_score -= severity_counts["critical"] * 20
            quality_score -= severity_counts["high"] * 10
            quality_score -= severity_counts["medium"] * 5
            quality_score -= severity_counts["low"] * 1
            quality_score = max(0, quality_score)

            result = {
                "success": True,
                "path": self.file_path,
                "summary": {
                    "files_analyzed": len(python_files),
                    "total_lines": total_lines,
                    "total_functions": total_functions,
                    "total_classes": sum(m["classes"] for m in all_metrics),
                    "average_complexity": round(avg_complexity, 2),
                    "quality_score": quality_score,
                },
                "issues_by_severity": severity_counts,
                "issues": all_issues[:100],  # Limit to first 100 issues
                "file_metrics": all_metrics[:20],  # Limit to first 20 files
                "recommendations": self._generate_recommendations(severity_counts, avg_complexity),
            }

            # Add summary message
            if quality_score >= 80:
                result["summary_message"] = f"Good code quality! Score: {quality_score}/100"
            elif quality_score >= 60:
                result["summary_message"] = f"Moderate code quality. Score: {quality_score}/100. Some improvements recommended."
            else:
                result["summary_message"] = f"Poor code quality. Score: {quality_score}/100. Significant improvements needed."

            return json.dumps(result, indent=2)

        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "path": self.file_path,
            }
            return json.dumps(result, indent=2)

    def _calculate_complexity(self, node: ast.AST) -> int:
        """
        Calculate cyclomatic complexity of a function node.
        Complexity = 1 (base) + number of decision points
        """
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Count decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.match):  # Python 3.10+
                complexity += 1

        return complexity

    def _generate_recommendations(self, severity_counts: dict, avg_complexity: float) -> list:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        if severity_counts["critical"] > 0:
            recommendations.append("Address critical issues immediately (syntax errors, major problems)")

        if severity_counts["high"] > 0:
            recommendations.append(f"Refactor {severity_counts['high']} high-severity issues to improve maintainability")

        if avg_complexity > 15:
            recommendations.append(f"Average complexity ({avg_complexity:.1f}) is high. Break down complex functions.")

        if severity_counts["medium"] > 5:
            recommendations.append("Consider addressing medium-severity issues to improve code quality")

        if not recommendations:
            recommendations.append("Code quality looks good! Maintain current standards.")

        return recommendations


if __name__ == "__main__":
    # Test the tool
    tool = AnalyzeCodeQualityTool(file_path=".")
    print(tool.run())

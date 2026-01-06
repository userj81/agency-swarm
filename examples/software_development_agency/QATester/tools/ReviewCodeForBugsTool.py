import ast
import json
import re
from pathlib import Path

from pydantic import Field

from agency_swarm.tools import BaseTool


class ReviewCodeForBugsTool(BaseTool):
    """
    Review code for potential bugs, security vulnerabilities, and common programming errors.
    Provides detailed analysis with severity ratings and fix suggestions.
    """

    file_path: str = Field(
        ...,
        description="Path to the source code file to review for bugs (e.g., 'src/main.py').",
    )

    check_security: bool = Field(
        default=True,
        description="Include security vulnerability checks. Defaults to True.",
    )

    check_performance: bool = Field(
        default=True,
        description="Include performance issue checks. Defaults to True.",
    )

    check_logic_errors: bool = Field(
        default=True,
        description="Check for common logic errors. Defaults to True.",
    )

    def run(self):
        """
        Review the code and return detailed bug findings.
        """
        try:
            path = Path(self.file_path)

            if not path.exists():
                result = {
                    "success": False,
                    "error": f"File does not exist: {self.file_path}",
                }
                return json.dumps(result, indent=2)

            if not path.is_file():
                result = {
                    "success": False,
                    "error": f"Path is not a file: {self.file_path}",
                }
                return json.dumps(result, indent=2)

            with open(path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            bugs = []

            # Parse AST
            try:
                tree = ast.parse(content, filename=str(path))
            except SyntaxError as e:
                bugs.append({
                    "line": e.lineno,
                    "type": "syntax_error",
                    "severity": "critical",
                    "message": f"Syntax error: {e.msg}",
                    "fix": "Fix the syntax error before proceeding",
                })
                result = {
                    "success": True,
                    "file": str(path),
                    "bugs_found": len(bugs),
                    "bugs": bugs,
                }
                return json.dumps(result, indent=2)

            # Check for common bugs and issues
            bugs.extend(self._check_security_issues(content, lines, tree))
            bugs.extend(self._check_performance_issues(content, lines, tree))
            bugs.extend(self._check_logic_errors(content, lines, tree))
            bugs.extend(self._check_exception_handling(lines, tree))
            bugs.extend(self._check_resource_leaks(lines, tree))

            # Sort by severity
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
            bugs.sort(key=lambda b: severity_order.get(b["severity"], 5))

            result = {
                "success": True,
                "file": str(path),
                "bugs_found": len(bugs),
                "bugs_by_severity": self._count_by_severity(bugs),
                "bugs": bugs,
                "summary": self._generate_summary(bugs),
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "file": self.file_path,
            }
            return json.dumps(result, indent=2)

    def _check_security_issues(self, content, lines, tree):
        """Check for security vulnerabilities."""
        issues = []

        # Check for hardcoded passwords/API keys
        password_patterns = [
            r"password\s*=\s*['\"][^'\"]{8,}['\"]",
            r"api_key\s*=\s*['\"][^'\"]{20,}['\"]",
            r"secret\s*=\s*['\"][^'\"]{16,}['\"]",
            r"token\s*=\s*['\"][^'\"]{20,}['\"]",
        ]

        for i, line in enumerate(lines, 1):
            for pattern in password_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        "line": i,
                        "type": "hardcoded_secret",
                        "severity": "high",
                        "message": "Possible hardcoded secret/credential detected",
                        "code": line.strip(),
                        "fix": "Use environment variables or a secure secrets manager",
                    })

        # Check for SQL injection vulnerabilities
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for string concatenation in SQL queries
                if isinstance(node.func, ast.Attribute) and node.func.attr == "execute":
                    for arg in node.args:
                        if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                            issues.append({
                                "line": node.lineno,
                                "type": "sql_injection",
                                "severity": "critical",
                                "message": "Possible SQL injection vulnerability - using string concatenation",
                                "fix": "Use parameterized queries instead",
                            })

        # Check for eval() usage
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "eval":
                    issues.append({
                        "line": node.lineno,
                        "type": "dangerous_eval",
                        "severity": "high",
                        "message": "Use of eval() is dangerous and can lead to code injection",
                        "fix": "Avoid eval() or use safer alternatives",
                    })

        # Check for shell=True in subprocess
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ["run", "call", "Popen"]:
                        for keyword in node.keywords:
                            if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant):
                                if keyword.value.value is True:
                                    issues.append({
                                        "line": node.lineno,
                                        "type": "shell_injection",
                                        "severity": "high",
                                        "message": "subprocess with shell=True is vulnerable to shell injection",
                                        "fix": "Use shell=False or validate input thoroughly",
                                    })

        return issues

    def _check_performance_issues(self, content, lines, tree):
        """Check for performance issues."""
        issues = []

        # Check for nested loops that could be optimized
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Check if nested in another for loop
                parent = self._find_parent_loop(tree, node)
                if parent:
                    issues.append({
                        "line": node.lineno,
                        "type": "nested_loop",
                        "severity": "low",
                        "message": "Nested loop detected - consider optimization for large datasets",
                        "fix": "Consider using dictionaries, sets, or more efficient algorithms",
                    })

        # Check for string concatenation in loops
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                for child in ast.walk(node):
                    if isinstance(child, ast.AugAssign):
                        if isinstance(child.target, ast.Name) and isinstance(child.op, ast.Add):
                            issues.append({
                                "line": child.lineno,
                                "type": "string_concat_loop",
                                "severity": "medium",
                                "message": "String concatenation in loop can be slow",
                                "fix": "Use list and join() for better performance",
                            })

        # Check for global variable usage
        global_vars = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                for name in node.names:
                    global_vars.add(name)

        if global_vars:
            issues.append({
                "line": 1,
                "type": "global_variables",
                "severity": "low",
                "message": f"Global variables detected: {', '.join(global_vars)}",
                "fix": "Consider using function parameters or class attributes",
            })

        return issues

    def _check_logic_errors(self, content, lines, tree):
        """Check for common logic errors."""
        issues = []

        # Check for empty except blocks
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if not node.body:
                    issues.append({
                        "line": node.lineno,
                        "type": "empty_except",
                        "severity": "medium",
                        "message": "Empty except block - errors will be silently ignored",
                        "fix": "Add proper error handling or logging",
                    })
                elif len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    issues.append({
                        "line": node.lineno,
                        "type": "pass_except",
                        "severity": "medium",
                        "message": "Except block with only pass - errors will be silently ignored",
                        "fix": "Add proper error handling or logging",
                    })

        # Check for missing return statements
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.returns:  # Function has return type annotation
                    has_return = False
                    for child in ast.walk(node):
                        if isinstance(child, ast.Return):
                            has_return = True
                            break
                    if not has_return:
                        issues.append({
                            "line": node.lineno,
                            "type": "missing_return",
                            "severity": "medium",
                            "message": f"Function '{node.name}' has return type but no return statement",
                            "fix": "Add appropriate return statement or remove type annotation",
                        })

        # Check for using is with string/number comparisons
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                for op in node.ops:
                    if isinstance(op, (ast.Is, ast.IsNot)):
                        left = node.left
                        if isinstance(left, ast.Constant):
                            if isinstance(left.value, (str, int, float)):
                                issues.append({
                                    "line": node.lineno,
                                    "type": "identity_comparison",
                                    "severity": "low",
                                    "message": "Using 'is' for literal comparison (should use == or !=)",
                                    "fix": f"Use == instead of is for comparing {type(left.value).__name__} values",
                                })

        return issues

    def _check_exception_handling(self, lines, tree):
        """Check exception handling patterns."""
        issues = []

        # Check for bare except
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append({
                        "line": node.lineno,
                        "type": "bare_except",
                        "severity": "high",
                        "message": "Bare except clause catches all exceptions including SystemExit",
                        "fix": "Specify exception type (e.g., except Exception)",
                    })

        return issues

    def _check_resource_leaks(self, lines, tree):
        """Check for potential resource leaks."""
        issues = []

        # Check for file operations without context manager
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id == "open":
                        # Check if wrapped in with statement
                        if not self._is_in_context_manager(tree, node):
                            issues.append({
                                "line": node.lineno,
                                "type": "unclosed_file",
                                "severity": "medium",
                                "message": "File opened without context manager - may not be properly closed",
                                "fix": "Use 'with open()' statement instead",
                            })

        return issues

    def _find_parent_loop(self, tree, node):
        """Find if a node is nested inside another loop."""
        for parent in ast.walk(tree):
            if isinstance(parent, (ast.For, ast.While)) and parent != node:
                # Check if node is descendant of parent
                for child in ast.walk(parent):
                    if child == node:
                        return parent
        return None

    def _is_in_context_manager(self, tree, node):
        """Check if a node is inside a with statement."""
        # Simplified check - in production would do proper AST traversal
        return False

    def _count_by_severity(self, bugs):
        """Count bugs by severity level."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for bug in bugs:
            severity = bug.get("severity", "low")
            if severity in counts:
                counts[severity] += 1
        return counts

    def _generate_summary(self, bugs):
        """Generate a summary message."""
        if not bugs:
            return "No bugs found! Code looks clean."

        critical = sum(1 for b in bugs if b["severity"] == "critical")
        high = sum(1 for b in bugs if b["severity"] == "high")

        if critical > 0:
            return f"Found {len(bugs)} issues including {critical} critical bugs requiring immediate attention."
        elif high > 0:
            return f"Found {len(bugs)} issues including {high} high-severity bugs."
        else:
            return f"Found {len(bugs)} issues that should be addressed."


if __name__ == "__main__":
    # Test the tool
    tool = ReviewCodeForBugsTool(file_path=__file__)
    print(tool.run())

import ast
import json
from pathlib import Path
from typing import Any

from pydantic import Field

from agency_swarm.tools import BaseTool


class GenerateTestCasesTool(BaseTool):
    """
    Generate test case suggestions for existing code. Analyzes functions and classes
    to create comprehensive test scenarios including edge cases, boundary conditions, and error cases.
    """

    file_path: str = Field(
        ...,
        description="Path to the source code file to generate test cases for (e.g., 'src/main.py').",
    )

    test_framework: str = Field(
        default="pytest",
        description="Target test framework for generated test cases. Options: 'pytest', 'unittest', 'jest'. Defaults to 'pytest'.",
    )

    include_edge_cases: bool = Field(
        default=True,
        description="Include edge case and boundary condition tests. Defaults to True.",
    )

    include_error_cases: bool = Field(
        default=True,
        description="Include error handling and exception tests. Defaults to True.",
    )

    def run(self):
        """
        Generate test cases for the provided code and return detailed suggestions.
        """
        try:
            path = Path(self.file_path)

            if not path.exists():
                result = {
                    "success": False,
                    "error": f"File does not exist: {self.file_path}",
                }
                return json.dumps(result, indent=2)

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse the AST
            try:
                tree = ast.parse(content, filename=str(path))
            except SyntaxError as e:
                result = {
                    "success": False,
                    "error": f"Syntax error in file: {e.msg}",
                    "line": e.lineno,
                }
                return json.dumps(result, indent=2)

            # Analyze the code
            test_cases = []

            # Extract functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    test_cases.extend(self._generate_function_tests(node, content))
                elif isinstance(node, ast.ClassDef):
                    test_cases.extend(self._generate_class_tests(node, content))

            # Group test cases
            grouped_cases = self._group_test_cases(test_cases)

            result = {
                "success": True,
                "file": str(path),
                "test_framework": self.test_framework,
                "summary": {
                    "total_test_cases": len(test_cases),
                    "functions_tested": len(set(tc["function"] for tc in test_cases)),
                    "classes_tested": len(set(tc["class"] for tc in test_cases if tc["class"])),
                },
                "test_cases": test_cases,
                "grouped_by_function": grouped_cases,
                "generated_code": self._generate_test_code(test_cases, path.name),
            }

            result["summary_message"] = f"Generated {len(test_cases)} test cases for {result['summary']['functions_tested']} function(s)"

            return json.dumps(result, indent=2)

        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "file": self.file_path,
            }
            return json.dumps(result, indent=2)

    def _generate_function_tests(self, node: ast.FunctionDef, content: str) -> list:
        """Generate test cases for a function."""
        test_cases = []

        function_name = node.name
        args = [arg.arg for arg in node.args.args]

        # Basic positive test case
        test_cases.append({
            "function": function_name,
            "class": None,
            "test_name": f"test_{function_name}_basic",
            "test_type": "positive",
            "description": f"Test basic functionality of {function_name}",
            "inputs": self._infer_test_inputs(args),
            "expected_output": "Expected result based on function logic",
            "setup": "",
            "teardown": "",
        })

        if self.include_edge_cases:
            # Edge case: empty inputs
            test_cases.append({
                "function": function_name,
                "class": None,
                "test_name": f"test_{function_name}_empty_inputs",
                "test_type": "edge_case",
                "description": f"Test {function_name} with empty/None inputs",
                "inputs": {arg: None for arg in args},
                "expected_output": "Handle empty inputs gracefully",
                "setup": "",
                "teardown": "",
            })

            # Edge case: boundary values
            test_cases.append({
                "function": function_name,
                "class": None,
                "test_name": f"test_{function_name}_boundary_values",
                "test_type": "edge_case",
                "description": f"Test {function_name} with boundary values (0, -1, max)",
                "inputs": self._infer_boundary_inputs(args),
                "expected_output": "Handle boundary values correctly",
                "setup": "",
                "teardown": "",
            })

        if self.include_error_cases:
            # Error case: invalid input types
            test_cases.append({
                "function": function_name,
                "class": None,
                "test_name": f"test_{function_name}_invalid_types",
                "test_type": "error_case",
                "description": f"Test {function_name} with invalid input types",
                "inputs": {arg: "invalid_string" for arg in args},
                "expected_output": "TypeError or ValueError",
                "setup": "",
                "teardown": "",
                "expected_exception": "TypeError or ValueError",
            })

        return test_cases

    def _generate_class_tests(self, node: ast.ClassDef, content: str) -> list:
        """Generate test cases for a class."""
        test_cases = []

        class_name = node.name

        # Test initialization
        test_cases.append({
            "function": "__init__",
            "class": class_name,
            "test_name": f"test_{class_name}_initialization",
            "test_type": "positive",
            "description": f"Test {class_name} object initialization",
            "inputs": self._infer_class_init_inputs(node),
            "expected_output": f"{class_name} instance created successfully",
            "setup": "",
            "teardown": "",
        })

        # Test methods
        for child in node.body:
            if isinstance(child, ast.FunctionDef) and not child.name.startswith("__"):
                method_tests = self._generate_function_tests(child, content)
                for test in method_tests:
                    test["class"] = class_name
                    test["test_name"] = test["test_name"].replace(f"test_{child.name}", f"test_{class_name}_{child.name}")
                test_cases.extend(method_tests)

        return test_cases

    def _infer_test_inputs(self, args: list) -> dict:
        """Infer appropriate test inputs based on argument names."""
        inputs = {}

        for arg in args:
            arg_lower = arg.lower()

            if "name" in arg_lower or "title" in arg_lower or "text" in arg_lower:
                inputs[arg] = '"test_string"'
            elif "id" in arg_lower:
                inputs[arg] = "1"
            elif "count" in arg_lower or "num" in arg_lower or "number" in arg_lower:
                inputs[arg] = "5"
            elif "price" in arg_lower or "amount" in arg_lower or "cost" in arg_lower:
                inputs[arg] = "10.99"
            elif "enabled" in arg_lower or "active" in arg_lower:
                inputs[arg] = "True"
            elif "data" in arg_lower or "items" in arg_lower or "list" in arg_lower:
                inputs[arg] = "[]"
            elif "config" in arg_lower or "settings" in arg_lower:
                inputs[arg] = "{}"
            else:
                inputs[arg] = "None"

        return inputs

    def _infer_boundary_inputs(self, args: list) -> dict:
        """Infer boundary value test inputs."""
        inputs = {}

        for arg in args:
            arg_lower = arg.lower()

            if "count" in arg_lower or "num" in arg_lower or "number" in arg_lower:
                inputs[arg] = "0"  # Boundary for numbers
            elif "price" in arg_lower or "amount" in arg_lower:
                inputs[arg] = "0.0"
            elif "id" in arg_lower:
                inputs[arg] = "-1"  # Invalid ID
            else:
                inputs[arg] = '""'  # Empty string

        return inputs

    def _infer_class_init_inputs(self, node: ast.ClassDef) -> dict:
        """Infer initialization inputs for a class."""
        inputs = {}

        for child in node.body:
            if isinstance(child, ast.FunctionDef) and child.name == "__init__":
                args = [arg.arg for arg in child.args.args if arg.arg != "self"]
                inputs = self._infer_test_inputs(args)
                break

        return inputs

    def _group_test_cases(self, test_cases: list) -> dict:
        """Group test cases by function/class."""
        grouped = {}

        for tc in test_cases:
            key = f"{tc['class'] or 'module'}.{tc['function']}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(tc)

        return grouped

    def _generate_test_code(self, test_cases: list, file_name: str) -> str:
        """Generate actual test code based on the test framework."""
        if self.test_framework == "pytest":
            return self._generate_pytest_code(test_cases, file_name)
        elif self.test_framework == "unittest":
            return self._generate_unittest_code(test_cases, file_name)
        elif self.test_framework == "jest":
            return self._generate_jest_code(test_cases, file_name)
        else:
            return f"# Framework {self.test_framework} not yet supported"

    def _generate_pytest_code(self, test_cases: list, file_name: str) -> str:
        """Generate pytest-style test code."""
        code_lines = [
            '"""',
            f'Auto-generated tests for {file_name}',
            '"""',
            'import pytest',
            'from unittest.mock import Mock, patch',
            '',
            '',
        ]

        for tc in test_cases:
            code_lines.append(f"def {tc['test_name']}():")
            code_lines.append(f'    """')
            code_lines.append(f'    {tc["description"]}')
            code_lines.append(f'    """')

            # Add inputs as variables
            for key, value in tc["inputs"].items():
                code_lines.append(f'    {key} = {value}')

            code_lines.append('')
            code_lines.append('    # TODO: Implement test logic')
            code_lines.append('    # Example:')
            if tc["class"]:
                code_lines.append(f'    # obj = {tc["class"]}(**locals())')
            code_lines.append('    # result = function_under_test(**locals())')
            code_lines.append('    # assert result is not None')
            code_lines.append('')
            code_lines.append('    raise NotImplementedError("Test not implemented yet")')
            code_lines.append('')
            code_lines.append('')

        return "\n".join(code_lines)

    def _generate_unittest_code(self, test_cases: list, file_name: str) -> str:
        """Generate unittest-style test code."""
        code_lines = [
            '"""',
            f'Auto-generated tests for {file_name}',
            '"""',
            'import unittest',
            'from unittest.mock import Mock, patch',
            '',
            '',
        ]

        # Group by class for unittest structure
        by_class = {}
        for tc in test_cases:
            cls = tc["class"] or "TestModule"
            if cls not in by_class:
                by_class[cls] = []
            by_class[cls].append(tc)

        for cls_name, cases in by_class.items():
            code_lines.append(f"class {cls_name}Tests(unittest.TestCase):")
            code_lines.append('    """')
            code_lines.append(f'    Test cases for {cls_name}')
            code_lines.append('    """')
            code_lines.append('')

            for tc in cases:
                code_lines.append(f'    def {tc["test_name"]}(self):')
                code_lines.append(f'        """')
                code_lines.append(f'        {tc["description"]}')
                code_lines.append(f'        """')
                code_lines.append('        # TODO: Implement test')
                code_lines.append('        self.fail("Test not implemented")')
                code_lines.append('')

            code_lines.append('')

        code_lines.append("")
        code_lines.append("if __name__ == '__main__':")
        code_lines.append("    unittest.main()")

        return "\n".join(code_lines)

    def _generate_jest_code(self, test_cases: list, file_name: str) -> str:
        """Generate Jest-style test code for JavaScript/TypeScript."""
        code_lines = [
            '// Auto-generated tests',
            "// TODO: Add proper imports",
            '',
            '',
        ]

        for tc in test_cases:
            code_lines.append(f"describe('{tc['class'] or 'Module'}', () => {{")
            code_lines.append(f"  {tc['test_name']}() {{")

            if tc["class"]:
                code_lines.append(f"    // Test {tc['class']}.{tc['function']}")
            else:
                code_lines.append(f"    // Test {tc['function']}")

            code_lines.append("    // TODO: Implement test")
            code_lines.append("    expect(true).toBe(true)")
            code_lines.append("  }")
            code_lines.append("}")

        return "\n".join(code_lines)


if __name__ == "__main__":
    # Test the tool
    tool = GenerateTestCasesTool(file_path=__file__)
    print(tool.run())

import json
from pathlib import Path
from typing import Any

from pydantic import Field

from agency_swarm.tools import BaseTool


class ValidateRequirementsTool(BaseTool):
    """
    Validate that implemented features meet the specified requirements and acceptance criteria.
    Compares implementation against requirements document or user story.
    """

    requirements_path: str = Field(
        ...,
        description="Path to the requirements document or file containing acceptance criteria (e.g., 'docs/requirements.md', 'stories/user_story_1.md').",
    )

    implementation_path: str = Field(
        ...,
        description="Path to the implementation file(s) to validate (e.g., 'src/main.py', 'src/').",
    )

    requirements_text: str = Field(
        default=None,
        description="Optional requirements text as string. If provided, takes precedence over requirements_path. Useful for inline requirements.",
    )

    check_documentation: bool = Field(
        default=True,
        description="Check if code has adequate documentation (docstrings, comments). Defaults to True.",
    )

    def run(self):
        """
        Validate implementation against requirements and return detailed report.
        """
        try:
            # Load requirements
            if self.requirements_text:
                requirements_content = self.requirements_text
                requirements_source = "provided_text"
            else:
                req_path = Path(self.requirements_path)
                if not req_path.exists():
                    result = {
                        "success": False,
                        "error": f"Requirements file not found: {self.requirements_path}",
                    }
                    return json.dumps(result, indent=2)

                with open(req_path, "r", encoding="utf-8") as f:
                    requirements_content = f.read()
                requirements_source = str(req_path)

            # Parse requirements
            parsed_requirements = self._parse_requirements(requirements_content)

            if not parsed_requirements:
                result = {
                    "success": False,
                    "error": "Could not parse any requirements from the provided content",
                    "requirements_source": requirements_source,
                }
                return json.dumps(result, indent=2)

            # Analyze implementation
            impl_path = Path(self.implementation_path)
            if not impl_path.exists():
                result = {
                    "success": False,
                    "error": f"Implementation path not found: {self.implementation_path}",
                }
                return json.dumps(result, indent=2)

            implementation_analysis = self._analyze_implementation(impl_path)

            # Validate requirements against implementation
            validation_results = []

            for req in parsed_requirements:
                validation = self._validate_requirement(req, implementation_analysis)
                validation_results.append(validation)

            # Calculate overall score
            total_requirements = len(validation_results)
            passed_requirements = sum(1 for v in validation_results if v["status"] == "passed")
            overall_pass_rate = (passed_requirements / total_requirements * 100) if total_requirements > 0 else 0

            result = {
                "success": True,
                "requirements_source": requirements_source,
                "implementation_path": self.implementation_path,
                "summary": {
                    "total_requirements": total_requirements,
                    "passed": passed_requirements,
                    "failed": total_requirements - passed_requirements,
                    "pass_rate": round(overall_pass_rate, 1),
                },
                "validation_results": validation_results,
                "implementation_analysis": implementation_analysis,
                "overall_status": "passed" if overall_pass_rate >= 80 else "failed",
                "recommendations": self._generate_recommendations(validation_results),
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
            }
            return json.dumps(result, indent=2)

    def _parse_requirements(self, content: str) -> list[dict]:
        """
        Parse requirements from markdown or text content.
        Extracts acceptance criteria and user stories.
        """
        requirements = []
        lines = content.split("\n")

        current_requirement = None
        acceptance_criteria = []

        for line in lines:
            line = line.strip()

            # Detect user story or requirement heading
            if line.startswith(("## ", "### ", "Requirement:", "User Story:")):
                # Save previous requirement if exists
                if current_requirement:
                    if acceptance_criteria:
                        current_requirement["acceptance_criteria"] = acceptance_criteria
                    requirements.append(current_requirement)

                # Start new requirement
                title = line.lstrip("#").strip()
                title = title.replace("Requirement:", "").replace("User Story:", "").strip()
                current_requirement = {
                    "title": title,
                    "type": "user_story" if "User Story" in line else "requirement",
                    "acceptance_criteria": [],
                }
                acceptance_criteria = []

            # Detect acceptance criteria
            elif line.startswith(("- ", "*", "•")):
                criterion = line.lstrip("-*•").strip()
                if criterion:
                    acceptance_criteria.append(criterion)

            # Detect acceptance criteria list
            elif line.lower().startswith("acceptance criteria"):
                continue  # Next lines will be the criteria

            # Detect Gherkin syntax (Given/When/Then)
            elif line.startswith(("Given ", "When ", "Then ", "And ")):
                criterion = line.strip()
                acceptance_criteria.append(criterion)

        # Save last requirement
        if current_requirement:
            if acceptance_criteria:
                current_requirement["acceptance_criteria"] = acceptance_criteria
            requirements.append(current_requirement)

        # If no structured requirements found, create one from content
        if not requirements:
            requirements.append({
                "title": "General Requirements",
                "type": "requirement",
                "acceptance_criteria": [s.strip() for s in content.split("\n") if s.strip() and not s.startswith("#")],
            })

        return requirements

    def _analyze_implementation(self, impl_path: Path) -> dict:
        """
        Analyze implementation files to extract features, functions, and documentation.
        """
        analysis = {
            "files": [],
            "total_functions": 0,
            "total_classes": 0,
            "total_lines": 0,
            "documented_functions": 0,
            "features_found": [],
        }

        if impl_path.is_file():
            files = [impl_path]
        else:
            files = list(impl_path.rglob("*.py"))

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                lines = content.split("\n")
                file_analysis = {
                    "path": str(file_path),
                    "lines": len(lines),
                    "functions": [],
                    "classes": [],
                }

                # Extract function names and check for docstrings
                import ast
                try:
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            file_analysis["functions"].append({
                                "name": node.name,
                                "line": node.lineno,
                                "has_docstring": ast.get_docstring(node) is not None,
                            })
                            if ast.get_docstring(node):
                                analysis["documented_functions"] += 1

                        elif isinstance(node, ast.ClassDef):
                            file_analysis["classes"].append({
                                "name": node.name,
                                "line": node.lineno,
                                "has_docstring": ast.get_docstring(node) is not None,
                            })

                    analysis["total_functions"] += len(file_analysis["functions"])
                    analysis["total_classes"] += len(file_analysis["classes"])

                except SyntaxError:
                    pass  # Skip files with syntax errors

            analysis["total_lines"] += file_analysis["lines"]
            analysis["files"].append(file_analysis)

            # Extract potential feature names from comments and function names
            for line in lines:
                line_stripped = line.strip()
                if line_stripped.startswith("# Feature:") or line_stripped.startswith("# Implements:"):
                    feature = line_stripped.replace("# Feature:", "").replace("# Implements:", "").strip()
                    analysis["features_found"].append(feature)

            except Exception:
                pass

        return analysis

    def _validate_requirement(self, requirement: dict, impl_analysis: dict) -> dict:
        """
        Validate a single requirement against the implementation.
        """
        validation = {
            "requirement": requirement["title"],
            "status": "unknown",
            "acceptance_criteria_results": [],
            "notes": [],
        }

        passed_criteria = 0
        total_criteria = len(requirement.get("acceptance_criteria", []))

        for criterion in requirement.get("acceptance_criteria", []):
            criterion_result = {
                "criterion": criterion,
                "status": "unknown",
                "evidence": [],
            }

            # Simple keyword matching for validation
            # In production, this would use more sophisticated analysis
            criterion_lower = criterion.lower()

            # Check for implementation keywords
            found = False
            for file_info in impl_analysis.get("files", []):
                file_path = file_info["path"].lower()

                # Look for keyword matches in function names
                for func in file_info.get("functions", []):
                    if any(keyword in func["name"].lower() for keyword in criterion_lower.split()):
                        found = True
                        criterion_result["evidence"].append(f"Function '{func['name']}' in {file_path}")

                # Look for keyword matches in class names
                for cls in file_info.get("classes", []):
                    if any(keyword in cls["name"].lower() for keyword in criterion_lower.split()):
                        found = True
                        criterion_result["evidence"].append(f"Class '{cls['name']}' in {file_path}")

            # Check for common patterns
            if "test" in criterion_lower and impl_analysis.get("total_functions", 0) > 0:
                found = True
                criterion_result["evidence"].append("Implementation code exists")

            if "error" in criterion_lower or "exception" in criterion_lower:
                criterion_result["evidence"].append("Error handling should be verified manually")

            if "document" in criterion_lower and impl_analysis.get("documented_functions", 0) > 0:
                found = True
                criterion_result["evidence"].append(f"{impl_analysis['documented_functions']} documented functions")

            # Determine status
            if found or len(criterion_result["evidence"]) > 0:
                criterion_result["status"] = "likely_passed"
                passed_criteria += 1
            else:
                criterion_result["status"] = "requires_manual_verification"
                validation["notes"].append(f"Manual verification needed: {criterion}")

            validation["acceptance_criteria_results"].append(criterion_result)

        # Determine overall requirement status
        if total_criteria == 0:
            validation["status"] = "manual_verification_required"
        elif passed_criteria == total_criteria:
            validation["status"] = "passed"
        elif passed_criteria > 0:
            validation["status"] = "partial"
        else:
            validation["status"] = "requires_manual_verification"

        return validation

    def _generate_recommendations(self, validation_results: list) -> list:
        """Generate recommendations based on validation results."""
        recommendations = []

        manual_required = [v for v in validation_results if v["status"] in ["requires_manual_verification", "unknown"]]
        if manual_required:
            recommendations.append(f"Manual verification required for {len(manual_required)} requirement(s)")

        partial = [v for v in validation_results if v["status"] == "partial"]
        if partial:
            recommendations.append(f"{len(partial)} requirement(s) partially implemented")

        passed = [v for v in validation_results if v["status"] == "passed"]
        if passed:
            recommendations.append(f"{len(passed)} requirement(s) fully validated")

        return recommendations


if __name__ == "__main__":
    # Test the tool
    tool = ValidateRequirementsTool(
        requirements_text="""
## User Login Feature

Acceptance Criteria:
- User can login with valid credentials
- Error message shown for invalid credentials
- Session is created after successful login
- Password field is masked
    """,
        implementation_path="."
    )
    print(tool.run())

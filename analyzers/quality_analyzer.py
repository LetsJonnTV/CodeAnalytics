"""
Code Analytics - Code Quality Analyzer
Checks for code quality issues, maintainability, and best practices
"""

import re
from typing import Dict, List, Any
from collections import Counter


class QualityAnalyzer:
    """Analyze code for quality issues"""

    def __init__(self, code: str, language: str = "unknown"):
        self.code = code
        self.language = language.lower()
        self.lines = code.split("\n")

    def analyze(self) -> Dict[str, Any]:
        """Run full quality analysis"""
        results = {
            "score": 0,
            "issues": [],
            "metrics": self._calculate_metrics(),
            "naming_issues": self._check_naming(),
            "documentation": self._check_documentation(),
            "code_smells": self._detect_code_smells(),
            "maintainability": self._check_maintainability(),
        }

        # Calculate overall score
        results["score"] = self._calculate_score(results)
        results["grade"] = self._get_grade(results["score"])

        return results

    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate code metrics"""
        total_lines = len(self.lines)
        code_lines = sum(1 for line in self.lines if line.strip() and not self._is_comment(line))
        blank_lines = sum(1 for line in self.lines if not line.strip())
        comment_lines = sum(1 for line in self.lines if self._is_comment(line))

        # Calculate average line length
        non_empty_lines = [line for line in self.lines if line.strip()]
        avg_line_length = sum(len(line) for line in non_empty_lines) / max(len(non_empty_lines), 1)

        # Count functions and classes
        function_count = len(re.findall(r"^\s*(def|function|func)\s+\w+", self.code, re.MULTILINE))
        class_count = len(re.findall(r"^\s*class\s+\w+", self.code, re.MULTILINE))

        return {
            "total_lines": total_lines,
            "code_lines": code_lines,
            "blank_lines": blank_lines,
            "comment_lines": comment_lines,
            "comment_ratio": comment_lines / max(code_lines, 1),
            "average_line_length": round(avg_line_length, 1),
            "function_count": function_count,
            "class_count": class_count,
            "lines_per_function": code_lines / max(function_count, 1),
        }

    def _is_comment(self, line: str) -> bool:
        """Check if line is a comment"""
        stripped = line.strip()
        return stripped.startswith(("#", "//", "/*", "*", '"""', "'''"))

    def _check_naming(self) -> List[Dict[str, Any]]:
        """Check naming conventions"""
        issues = []

        # Python naming conventions
        if self.language == "python":
            # Check function names (should be snake_case)
            for match in re.finditer(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", self.code):
                name = match.group(1)
                if not name.startswith("_") and not name.islower() and name != name.lower():
                    if not name.isupper():  # Allow constants
                        line_num = self.code[: match.start()].count("\n") + 1
                        issues.append(
                            {
                                "line": line_num,
                                "name": name,
                                "type": "function",
                                "message": f"Function '{name}' should use snake_case",
                            }
                        )

            # Check class names (should be PascalCase)
            for match in re.finditer(r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)", self.code):
                name = match.group(1)
                if not name[0].isupper():
                    line_num = self.code[: match.start()].count("\n") + 1
                    issues.append(
                        {
                            "line": line_num,
                            "name": name,
                            "type": "class",
                            "message": f"Class '{name}' should use PascalCase",
                        }
                    )

            # Check variable names (avoid single letters except loop counters)
            for match in re.finditer(r"\b([a-zA-Z])\s*=\s*(?!.*for)", self.code):
                name = match.group(1)
                if name not in ("i", "j", "k", "x", "y", "z", "_"):
                    line_num = self.code[: match.start()].count("\n") + 1
                    issues.append(
                        {
                            "line": line_num,
                            "name": name,
                            "type": "variable",
                            "message": f"Single-letter variable '{name}' - use descriptive name",
                        }
                    )

        # JavaScript/TypeScript naming conventions
        elif self.language in ("javascript", "typescript"):
            # Check function names (should be camelCase)
            for match in re.finditer(r"function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)", self.code):
                name = match.group(1)
                if name[0].isupper() and not name.isupper():
                    line_num = self.code[: match.start()].count("\n") + 1
                    issues.append(
                        {
                            "line": line_num,
                            "name": name,
                            "type": "function",
                            "message": f"Function '{name}' should use camelCase",
                        }
                    )

        return issues

    def _check_documentation(self) -> Dict[str, Any]:
        """Check documentation coverage"""
        results = {
            "has_module_doc": False,
            "functions_documented": 0,
            "functions_total": 0,
            "classes_documented": 0,
            "classes_total": 0,
            "undocumented": [],
        }

        if self.language == "python":
            # Check for module docstring
            stripped_code = self.code.lstrip()
            if stripped_code.startswith('"""') or stripped_code.startswith("'''"):
                results["has_module_doc"] = True

            # Check function docstrings
            function_pattern = r'def\s+(\w+)\s*\([^)]*\):\s*\n(\s*)("""|\'\'\')?'
            for match in re.finditer(r"def\s+(\w+)\s*\([^)]*\):", self.code):
                results["functions_total"] += 1
                func_name = match.group(1)

                # Check if next non-empty line is a docstring
                pos = match.end()
                remaining = self.code[pos : pos + 100]
                if re.match(r'\s*\n\s*("""|\'\'\')', remaining):
                    results["functions_documented"] += 1
                else:
                    line_num = self.code[: match.start()].count("\n") + 1
                    results["undocumented"].append({"name": func_name, "type": "function", "line": line_num})

            # Check class docstrings
            for match in re.finditer(r"class\s+(\w+)[^:]*:", self.code):
                results["classes_total"] += 1
                class_name = match.group(1)

                pos = match.end()
                remaining = self.code[pos : pos + 100]
                if re.match(r'\s*\n\s*("""|\'\'\')', remaining):
                    results["classes_documented"] += 1
                else:
                    line_num = self.code[: match.start()].count("\n") + 1
                    results["undocumented"].append({"name": class_name, "type": "class", "line": line_num})

        # Calculate coverage
        total = results["functions_total"] + results["classes_total"]
        documented = results["functions_documented"] + results["classes_documented"]
        results["coverage"] = documented / max(total, 1)

        return results

    def _detect_code_smells(self) -> List[Dict[str, Any]]:
        """Detect code smells"""
        smells = []

        # Long method detection
        in_function = False
        function_start = 0
        function_name = ""
        function_lines = 0

        for i, line in enumerate(self.lines, 1):
            if re.match(r"^\s*(def|function)\s+(\w+)", line):
                if in_function and function_lines > 30:
                    smells.append(
                        {
                            "line": function_start,
                            "type": "long_method",
                            "message": f"Long method '{function_name}' ({function_lines} lines)",
                            "severity": "medium",
                        }
                    )
                match = re.search(r"(def|function)\s+(\w+)", line)
                function_name = match.group(2) if match else "unknown"
                function_start = i
                function_lines = 0
                in_function = True
            elif in_function:
                function_lines += 1

        # Too many parameters
        for match in re.finditer(r"def\s+(\w+)\s*\(([^)]+)\)", self.code):
            params = match.group(2).split(",")
            if len(params) > 5:
                line_num = self.code[: match.start()].count("\n") + 1
                smells.append(
                    {
                        "line": line_num,
                        "type": "too_many_parameters",
                        "message": f"Function '{match.group(1)}' has too many parameters ({len(params)})",
                        "severity": "medium",
                    }
                )

        # Deeply nested code
        max_indent = 0
        max_indent_line = 0
        for i, line in enumerate(self.lines, 1):
            if line.strip():
                indent = len(line) - len(line.lstrip())
                indent_level = indent // 4  # Assume 4 spaces per level
                if indent_level > max_indent:
                    max_indent = indent_level
                    max_indent_line = i

        if max_indent > 4:
            smells.append(
                {
                    "line": max_indent_line,
                    "type": "deep_nesting",
                    "message": f"Deeply nested code ({max_indent} levels)",
                    "severity": "high",
                }
            )

        # Duplicate code detection (simple)
        line_counts = Counter(line.strip() for line in self.lines if len(line.strip()) > 20)
        for line_content, count in line_counts.most_common(5):
            if count >= 3:
                smells.append(
                    {
                        "line": 0,
                        "type": "duplicate_code",
                        "message": f"Duplicated line appears {count} times: '{line_content[:40]}...'",
                        "severity": "low",
                    }
                )

        # Magic numbers
        magic_numbers = []
        for i, line in enumerate(self.lines, 1):
            if not self._is_comment(line):
                numbers = re.findall(r"(?<![a-zA-Z_])\d{2,}(?![a-zA-Z_\d])", line)
                for num in numbers:
                    if num not in ("10", "100", "1000"):
                        magic_numbers.append((i, num))

        if len(magic_numbers) > 3:
            smells.append(
                {
                    "line": magic_numbers[0][0],
                    "type": "magic_numbers",
                    "message": f"Found {len(magic_numbers)} magic numbers - consider using named constants",
                    "severity": "low",
                }
            )

        return smells

    def _check_maintainability(self) -> Dict[str, Any]:
        """Check maintainability aspects"""
        results = {"issues": [], "suggestions": []}

        # Check for TODO/FIXME comments
        todo_count = len(re.findall(r"#\s*(TODO|FIXME|HACK|XXX)", self.code, re.IGNORECASE))
        if todo_count > 0:
            results["issues"].append(
                {"type": "technical_debt", "message": f"Found {todo_count} TODO/FIXME comments", "severity": "info"}
            )

        # Check for commented-out code
        commented_code = 0
        for line in self.lines:
            stripped = line.strip()
            if stripped.startswith("#") and re.search(r"(def |class |import |return |if |for |while )", stripped):
                commented_code += 1

        if commented_code > 2:
            results["issues"].append(
                {
                    "type": "commented_code",
                    "message": f"Found {commented_code} lines of commented-out code",
                    "severity": "low",
                }
            )

        # Check for dead imports (simple check)
        imports = re.findall(r"(?:from\s+\S+\s+)?import\s+(\w+)", self.code)
        for imp in imports:
            # Check if import is used (simple check)
            usage_count = len(re.findall(rf"\b{imp}\b", self.code))
            if usage_count == 1:  # Only the import itself
                results["suggestions"].append(f"Unused import: {imp}")

        return results

    def _calculate_score(self, results: Dict[str, Any]) -> int:
        """Calculate overall quality score (0-100)"""
        score = 100

        # Deduct for metrics issues
        metrics = results["metrics"]
        if metrics["comment_ratio"] < 0.1:
            score -= 10
        if metrics["average_line_length"] > 80:
            score -= 5
        if metrics["lines_per_function"] > 30:
            score -= 10

        # Deduct for naming issues
        score -= min(len(results["naming_issues"]) * 2, 15)

        # Deduct for documentation issues
        doc = results["documentation"]
        if not doc["has_module_doc"]:
            score -= 5
        doc_coverage = doc["coverage"]
        if doc_coverage < 0.5:
            score -= 10
        elif doc_coverage < 0.8:
            score -= 5

        # Deduct for code smells
        for smell in results["code_smells"]:
            if smell["severity"] == "high":
                score -= 8
            elif smell["severity"] == "medium":
                score -= 5
            else:
                score -= 2

        return max(0, min(100, score))

    def _get_grade(self, score: int) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def get_summary(self) -> str:
        """Get quality analysis summary"""
        results = self.analyze()

        grade = results["grade"]
        score = results["score"]

        grade_emoji = {"A": "🌟", "B": "✅", "C": "⚠️", "D": "🔶", "F": "❌"}

        parts = [
            f"{grade_emoji.get(grade, '📊')} Code Quality: {grade} ({score}/100)",
            "",
            f"📝 Documentation: {results['documentation']['coverage'] * 100:.0f}% covered",
            f"📏 Avg line length: {results['metrics']['average_line_length']:.0f} chars",
            f"💬 Comment ratio: {results['metrics']['comment_ratio'] * 100:.0f}%",
        ]

        if results["code_smells"]:
            parts.append(f"🔍 Code smells: {len(results['code_smells'])}")

        if results["naming_issues"]:
            parts.append(f"📛 Naming issues: {len(results['naming_issues'])}")

        return "\n".join(parts)

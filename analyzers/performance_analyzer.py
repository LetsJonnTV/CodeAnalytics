"""
Code Analytics - Performance Analyzer
Checks for performance issues and optimization opportunities
"""

import re
from typing import Dict, List, Any


class PerformanceAnalyzer:
    """Analyze code for performance issues"""

    def __init__(self, code: str, language: str = "unknown"):
        self.code = code
        self.language = language.lower()
        self.lines = code.split("\n")

    def analyze(self) -> Dict[str, Any]:
        """Run full performance analysis"""
        results = {"issues": [], "suggestions": [], "complexity_warnings": [], "memory_warnings": []}

        if self.language == "python":
            results["issues"].extend(self._check_python_performance())
            results["suggestions"].extend(self._get_python_suggestions())
        elif self.language in ("javascript", "typescript"):
            results["issues"].extend(self._check_js_performance())

        results["issues"].extend(self._check_general_performance())
        results["complexity_warnings"] = self._check_complexity()

        return results

    def _check_python_performance(self) -> List[Dict[str, Any]]:
        """Check Python-specific performance issues"""
        issues = []

        patterns = [
            # Loop optimizations
            (r"for\s+\w+\s+in\s+range\s*\(\s*len\s*\(", "Use enumerate() instead of range(len())", "medium"),
            # String concatenation in loops
            (r"for.*:\s*$", None, None),  # Mark for context check
            # Inefficient list operations
            (r"\+\s*\[\s*\w+\s*\]", "List concatenation in loop may be inefficient, use .append()", "medium"),
            # Global variable access in loops
            (r"global\s+\w+", "Global variable access is slower than local", "low"),
            # Inefficient comprehensions
            (
                r"\[\s*\w+\s+for\s+\w+\s+in\s+.*\s+if\s+.*\s+if\s+",
                "Multiple if conditions in comprehension - consider generator",
                "low",
            ),
            # Using + for string building
            (r'["\'].*["\']\s*\+\s*["\']', "String concatenation - consider f-strings or join()", "low"),
            # Not using generators
            (r"return\s+\[.*for.*in.*\]", "Consider using generator (yield) for large datasets", "low"),
            # Redundant operations
            (r"list\s*\(\s*\[", "Redundant list() call on list literal", "low"),
            (r"dict\s*\(\s*\{", "Redundant dict() call on dict literal", "low"),
            # Slow imports
            (r"^import\s+numpy", "NumPy import at module level - may slow startup", "info"),
            (r"^import\s+pandas", "Pandas import at module level - may slow startup", "info"),
            # Inefficient patterns
            (r"\.keys\s*\(\s*\)\s*\)", ".keys() often unnecessary - iterate dict directly", "low"),
            (r"if\s+\w+\s+in\s+\w+\.keys\s*\(\s*\)", 'Use "in dict" instead of "in dict.keys()"', "low"),
            # Type checking
            (r"type\s*\(\s*\w+\s*\)\s*==", "Use isinstance() instead of type() for type checking", "medium"),
            # Exception handling
            (r"except\s*:", "Bare except catches all exceptions including KeyboardInterrupt", "medium"),
            # File handling
            (r"\.read\s*\(\s*\)", "Reading entire file into memory - consider iterating lines", "info"),
            # Recursion without limit
            (
                r"def\s+(\w+)\s*\([^)]*\):[^}]*\1\s*\(",
                "Recursive function - ensure base case and consider iteration",
                "info",
            ),
        ]

        for i, line in enumerate(self.lines, 1):
            for pattern, message, severity in patterns:
                if message and re.search(pattern, line):
                    issues.append({"line": i, "message": message, "severity": severity, "code": line.strip()[:60]})

        return issues

    def _check_js_performance(self) -> List[Dict[str, Any]]:
        """Check JavaScript-specific performance issues"""
        issues = []

        patterns = [
            # DOM manipulation
            (r"document\.getElementById\s*\([^)]+\)", "Cache DOM elements instead of repeated lookups", "medium"),
            (r"\.innerHTML\s*\+?=", "Multiple innerHTML changes - batch updates or use DocumentFragment", "medium"),
            # Inefficient loops
            (r"for\s*\(\s*var\s+\w+\s*=\s*0.*\.length", "Cache array length outside loop", "low"),
            # Synchronous operations
            (r"\.forEach\s*\(\s*async", "forEach with async - use Promise.all with map instead", "high"),
            # Memory leaks
            (r"addEventListener\s*\(", "Ensure event listeners are removed when not needed", "info"),
            (r"setInterval\s*\(", "Ensure intervals are cleared to prevent memory leaks", "info"),
            # Blocking operations
            (r"JSON\.parse\s*\(", "Large JSON parsing can block - consider streaming", "info"),
            # Inefficient patterns
            (r"new\s+Array\s*\(\s*\d+\s*\)", "Use array literal [] instead of new Array()", "low"),
            (r"new\s+Object\s*\(\s*\)", "Use object literal {} instead of new Object()", "low"),
        ]

        for i, line in enumerate(self.lines, 1):
            for pattern, message, severity in patterns:
                if re.search(pattern, line):
                    issues.append({"line": i, "message": message, "severity": severity, "code": line.strip()[:60]})

        return issues

    def _check_general_performance(self) -> List[Dict[str, Any]]:
        """Check general performance issues"""
        issues = []

        # Check for deeply nested loops
        nesting_level = 0
        max_nesting = 0
        nested_line = 0

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()

            if re.match(r"^(for|while)\s+", stripped):
                nesting_level += 1
                if nesting_level > max_nesting:
                    max_nesting = nesting_level
                    nested_line = i
            elif stripped.startswith(("def ", "function ", "class ")):
                nesting_level = 0

            # Simple check for loop end (indentation-based)
            if nesting_level > 0 and not stripped and i > 1:
                prev_indent = len(self.lines[i - 2]) - len(self.lines[i - 2].lstrip())
                curr_indent = len(line) - len(line.lstrip()) if line else 0
                if curr_indent < prev_indent:
                    nesting_level = max(0, nesting_level - 1)

        if max_nesting >= 3:
            issues.append(
                {
                    "line": nested_line,
                    "message": f"Deeply nested loops ({max_nesting} levels) - O(n^{max_nesting}) complexity",
                    "severity": "high" if max_nesting >= 4 else "medium",
                    "code": "Nested loop structure",
                }
            )

        # Check for very long functions
        function_lines = 0
        function_start = 0
        in_function = False

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()

            if re.match(r"^(def|function|async\s+function)\s+", stripped):
                if in_function and function_lines > 50:
                    issues.append(
                        {
                            "line": function_start,
                            "message": f"Long function ({function_lines} lines) - consider breaking it up",
                            "severity": "medium" if function_lines < 100 else "high",
                            "code": "Function definition",
                        }
                    )
                in_function = True
                function_start = i
                function_lines = 0
            elif in_function:
                function_lines += 1

        return issues

    def _check_complexity(self) -> List[Dict[str, Any]]:
        """Check for complexity issues"""
        warnings = []

        # Check for long lines
        for i, line in enumerate(self.lines, 1):
            if len(line) > 120:
                warnings.append(
                    {"line": i, "message": f"Very long line ({len(line)} chars) - hard to read", "type": "readability"}
                )

        # Check for many conditions
        for i, line in enumerate(self.lines, 1):
            and_count = line.lower().count(" and ")
            or_count = line.lower().count(" or ")

            if and_count + or_count >= 3:
                warnings.append(
                    {
                        "line": i,
                        "message": f"Complex condition ({and_count + or_count} operators) - consider simplifying",
                        "type": "complexity",
                    }
                )

        return warnings

    def _get_python_suggestions(self) -> List[str]:
        """Get Python optimization suggestions"""
        suggestions = []

        # Check if using list comprehensions
        if "for " in self.code and "append(" in self.code:
            suggestions.append("Consider using list comprehensions instead of for-loop with append()")

        # Check if using with statement for files
        if "open(" in self.code and "with " not in self.code:
            suggestions.append("Use 'with' statement for file operations to ensure proper cleanup")

        # Check for slots in classes
        if "class " in self.code and "__slots__" not in self.code:
            suggestions.append("Consider using __slots__ in classes to reduce memory usage")

        # Check for lru_cache
        if "def " in self.code and "@lru_cache" not in self.code and "@cache" not in self.code:
            suggestions.append("Consider using @lru_cache for functions with repeated calls")

        # Check for typing
        if "def " in self.code and ":" in self.code and "->" not in self.code:
            suggestions.append("Consider adding type hints for better code quality and IDE support")

        return suggestions

    def get_summary(self) -> str:
        """Get performance analysis summary"""
        results = self.analyze()

        total_issues = len(results["issues"])

        if total_issues == 0:
            return "✅ No significant performance issues detected"

        severity_counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
        for issue in results["issues"]:
            severity_counts[issue.get("severity", "info")] += 1

        parts = [f"⚠️ Found {total_issues} potential performance issues:"]

        if severity_counts["high"] > 0:
            parts.append(f"  🔴 High impact: {severity_counts['high']}")
        if severity_counts["medium"] > 0:
            parts.append(f"  🟠 Medium impact: {severity_counts['medium']}")
        if severity_counts["low"] > 0:
            parts.append(f"  🟡 Low impact: {severity_counts['low']}")

        if results["suggestions"]:
            parts.append(f"\n💡 {len(results['suggestions'])} optimization suggestions available")

        return "\n".join(parts)

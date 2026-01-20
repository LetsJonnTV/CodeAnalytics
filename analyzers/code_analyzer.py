"""
Code Analytics - Basic Code Analyzer
"""

import re
import ast
import keyword
from typing import Dict, List, Any, Optional
from collections import Counter


class BasicAnalyzer:
    """Basic code analysis functionality"""

    def __init__(self, code: str, language: str = "Unknown"):
        self.code = code
        self.language = language
        self.lines = code.split("\n")

    def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic code statistics"""
        return {
            "total_lines": len(self.lines),
            "total_characters": len(self.code),
            "total_words": len(self.code.split()),
            "non_empty_lines": sum(1 for line in self.lines if line.strip()),
            "average_line_length": sum(len(line) for line in self.lines) / max(len(self.lines), 1),
            "max_line_length": max((len(line) for line in self.lines), default=0),
            "min_line_length": min((len(line) for line in self.lines if line.strip()), default=0),
        }

    def get_line_length_distribution(self) -> Dict[str, int]:
        """Get distribution of line lengths"""
        distribution = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0, "100+": 0}

        for line in self.lines:
            length = len(line)
            if length <= 20:
                distribution["0-20"] += 1
            elif length <= 40:
                distribution["21-40"] += 1
            elif length <= 60:
                distribution["41-60"] += 1
            elif length <= 80:
                distribution["61-80"] += 1
            elif length <= 100:
                distribution["81-100"] += 1
            else:
                distribution["100+"] += 1

        return distribution

    def find_long_lines(self, threshold: int = 80) -> List[Dict[str, Any]]:
        """Find lines exceeding length threshold"""
        long_lines = []
        for i, line in enumerate(self.lines, 1):
            if len(line) > threshold:
                long_lines.append(
                    {"line_number": i, "length": len(line), "content": line[:100] + "..." if len(line) > 100 else line}
                )
        return long_lines

    def find_duplicates(self, min_length: int = 10) -> List[Dict[str, Any]]:
        """Find duplicate lines in code"""
        line_locations = {}

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if len(stripped) >= min_length:
                if stripped not in line_locations:
                    line_locations[stripped] = []
                line_locations[stripped].append(i)

        duplicates = []
        for line, locations in line_locations.items():
            if len(locations) > 1:
                duplicates.append(
                    {
                        "content": line[:80] + "..." if len(line) > 80 else line,
                        "occurrences": len(locations),
                        "lines": locations,
                    }
                )

        return sorted(duplicates, key=lambda x: x["occurrences"], reverse=True)

    def get_indentation_analysis(self) -> Dict[str, Any]:
        """Analyze code indentation"""
        tabs_count = 0
        spaces_count = 0
        mixed_count = 0
        indent_sizes = []

        for line in self.lines:
            if not line.strip():
                continue

            leading_whitespace = len(line) - len(line.lstrip())
            if leading_whitespace == 0:
                continue

            has_tabs = "\t" in line[:leading_whitespace]
            has_spaces = " " in line[:leading_whitespace]

            if has_tabs and has_spaces:
                mixed_count += 1
            elif has_tabs:
                tabs_count += 1
            else:
                spaces_count += 1
                indent_sizes.append(leading_whitespace)

        # Detect common indent size
        common_indent = 4  # default
        if indent_sizes:
            counter = Counter(indent_sizes)
            most_common = counter.most_common(3)
            # Find GCD of common indents
            if most_common:
                for size, _ in most_common:
                    if size in [2, 4, 8]:
                        common_indent = size
                        break

        return {
            "tabs_usage": tabs_count,
            "spaces_usage": spaces_count,
            "mixed_usage": mixed_count,
            "detected_indent_size": common_indent,
            "style": "tabs" if tabs_count > spaces_count else "spaces",
        }

    def get_word_frequency(self, top_n: int = 20) -> List[tuple]:
        """Get most frequent words/identifiers in code"""
        # Extract words (identifiers, keywords, etc.)
        words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", self.code)
        counter = Counter(words)
        return counter.most_common(top_n)

    def find_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Find common code patterns and potential issues"""
        patterns = {
            "magic_numbers": [],
            "hardcoded_strings": [],
            "empty_blocks": [],
            "consecutive_blank_lines": [],
        }

        # Find magic numbers (standalone numbers that aren't 0, 1, -1)
        for i, line in enumerate(self.lines, 1):
            # Skip comments
            if line.strip().startswith(("#", "//", "/*", "*")):
                continue

            numbers = re.findall(r"(?<![a-zA-Z_])(-?\d+\.?\d*)(?![a-zA-Z_\d])", line)
            for num in numbers:
                try:
                    val = float(num)
                    if val not in (0, 1, -1, 2, 10, 100):
                        patterns["magic_numbers"].append({"line": i, "value": num, "context": line.strip()[:50]})
                except ValueError:
                    pass

        # Find consecutive blank lines (more than 2)
        blank_count = 0
        blank_start = 0
        for i, line in enumerate(self.lines, 1):
            if not line.strip():
                if blank_count == 0:
                    blank_start = i
                blank_count += 1
            else:
                if blank_count > 2:
                    patterns["consecutive_blank_lines"].append(
                        {"start_line": blank_start, "end_line": i - 1, "count": blank_count}
                    )
                blank_count = 0

        return patterns


class PythonAnalyzer(BasicAnalyzer):
    """Python-specific code analyzer"""

    def __init__(self, code: str):
        super().__init__(code, "Python")
        self.ast_tree = None
        self._parse_ast()

    def _parse_ast(self):
        """Parse Python AST"""
        try:
            self.ast_tree = ast.parse(self.code)
        except SyntaxError as e:
            self.ast_tree = None
            self.syntax_error = e

    def get_syntax_errors(self) -> Optional[Dict[str, Any]]:
        """Check for syntax errors"""
        if self.ast_tree is None and hasattr(self, "syntax_error"):
            e = self.syntax_error
            return {"message": str(e.msg), "line": e.lineno, "offset": e.offset, "text": e.text}
        return None

    def get_imports(self) -> Dict[str, List[Dict[str, Any]]]:
        """Extract all imports"""
        imports = {"standard": [], "third_party": [], "local": []}

        if self.ast_tree is None:
            return imports

        standard_libs = {
            "os",
            "sys",
            "json",
            "re",
            "math",
            "datetime",
            "time",
            "random",
            "collections",
            "itertools",
            "functools",
            "typing",
            "pathlib",
            "subprocess",
            "threading",
            "multiprocessing",
            "asyncio",
            "socket",
            "http",
            "urllib",
            "email",
            "html",
            "xml",
            "logging",
            "unittest",
            "argparse",
            "configparser",
            "csv",
            "sqlite3",
            "pickle",
            "copy",
            "io",
            "tempfile",
            "shutil",
            "glob",
            "hashlib",
            "hmac",
            "secrets",
            "base64",
            "binascii",
            "struct",
            "codecs",
            "string",
            "textwrap",
            "difflib",
            "pprint",
            "enum",
            "abc",
            "contextlib",
            "dataclasses",
            "inspect",
            "traceback",
            "warnings",
            "weakref",
            "types",
            "operator",
        }

        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split(".")[0]
                    category = "standard" if module in standard_libs else "third_party"
                    imports[category].append({"module": alias.name, "alias": alias.asname, "line": node.lineno})
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split(".")[0]
                    if node.level > 0:
                        category = "local"
                    elif module in standard_libs:
                        category = "standard"
                    else:
                        category = "third_party"

                    for alias in node.names:
                        imports[category].append(
                            {"module": node.module, "name": alias.name, "alias": alias.asname, "line": node.lineno}
                        )

        return imports

    def get_functions(self) -> List[Dict[str, Any]]:
        """Extract all function definitions"""
        functions = []

        if self.ast_tree is None:
            return functions

        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Get decorators
                decorators = [self._get_decorator_name(d) for d in node.decorator_list]

                # Get arguments
                args = []
                for arg in node.args.args:
                    args.append(
                        {"name": arg.arg, "annotation": ast.unparse(arg.annotation) if arg.annotation else None}
                    )

                # Get return annotation
                returns = ast.unparse(node.returns) if node.returns else None

                # Get docstring
                docstring = ast.get_docstring(node)

                # Count complexity (simple approximation)
                complexity = self._calculate_function_complexity(node)

                functions.append(
                    {
                        "name": node.name,
                        "line": node.lineno,
                        "end_line": node.end_lineno if hasattr(node, "end_lineno") else None,
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                        "decorators": decorators,
                        "arguments": args,
                        "returns": returns,
                        "docstring": docstring[:100] + "..." if docstring and len(docstring) > 100 else docstring,
                        "has_docstring": docstring is not None,
                        "complexity": complexity,
                    }
                )

        return functions

    def _get_decorator_name(self, decorator) -> str:
        """Get decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_decorator_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return str(decorator)

    def _calculate_function_complexity(self, node) -> int:
        """Calculate cyclomatic complexity approximation"""
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1

        return complexity

    def get_classes(self) -> List[Dict[str, Any]]:
        """Extract all class definitions"""
        classes = []

        if self.ast_tree is None:
            return classes

        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.ClassDef):
                # Get base classes
                bases = [ast.unparse(base) for base in node.bases]

                # Get decorators
                decorators = [self._get_decorator_name(d) for d in node.decorator_list]

                # Get methods
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(
                            {"name": item.name, "line": item.lineno, "is_async": isinstance(item, ast.AsyncFunctionDef)}
                        )

                # Get docstring
                docstring = ast.get_docstring(node)

                classes.append(
                    {
                        "name": node.name,
                        "line": node.lineno,
                        "end_line": node.end_lineno if hasattr(node, "end_lineno") else None,
                        "bases": bases,
                        "decorators": decorators,
                        "methods": methods,
                        "method_count": len(methods),
                        "docstring": docstring[:100] + "..." if docstring and len(docstring) > 100 else docstring,
                        "has_docstring": docstring is not None,
                    }
                )

        return classes

    def get_variables(self) -> List[Dict[str, Any]]:
        """Extract global variable assignments"""
        variables = []

        if self.ast_tree is None:
            return variables

        for node in self.ast_tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.append({"name": target.id, "line": node.lineno, "type_hint": None})
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    variables.append(
                        {
                            "name": node.target.id,
                            "line": node.lineno,
                            "type_hint": ast.unparse(node.annotation) if node.annotation else None,
                        }
                    )

        return variables

    def check_pep8_issues(self) -> List[Dict[str, Any]]:
        """Check for common PEP8 style issues"""
        issues = []

        for i, line in enumerate(self.lines, 1):
            # Line too long
            if len(line) > 79:
                issues.append({"line": i, "code": "E501", "message": f"Line too long ({len(line)} > 79 characters)"})

            # Trailing whitespace
            if line.rstrip() != line:
                issues.append({"line": i, "code": "W291", "message": "Trailing whitespace"})

            # Missing whitespace around operator
            if re.search(r"[a-zA-Z0-9]=[a-zA-Z0-9]", line) and "==" not in line and "!=" not in line:
                issues.append({"line": i, "code": "E225", "message": "Missing whitespace around operator"})

        return issues

    def get_complexity_metrics(self) -> Dict[str, Any]:
        """Get code complexity metrics"""
        functions = self.get_functions()
        classes = self.get_classes()

        complexities = [f["complexity"] for f in functions]

        return {
            "total_functions": len(functions),
            "total_classes": len(classes),
            "total_methods": sum(c["method_count"] for c in classes),
            "average_complexity": sum(complexities) / max(len(complexities), 1),
            "max_complexity": max(complexities) if complexities else 0,
            "high_complexity_functions": [f["name"] for f in functions if f["complexity"] > 10],
            "functions_without_docstring": sum(1 for f in functions if not f["has_docstring"]),
            "classes_without_docstring": sum(1 for c in classes if not c["has_docstring"]),
        }


def get_analyzer(code: str, language: str) -> BasicAnalyzer:
    """Factory function to get appropriate analyzer"""
    if language == "Python":
        return PythonAnalyzer(code)
    return BasicAnalyzer(code, language)

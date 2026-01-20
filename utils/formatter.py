"""
Code Analytics - Code Formatter
Supports formatting for multiple programming languages
"""

import os
import re
import subprocess
import tempfile
import shutil
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path


class CodeFormatter:
    """Universal code formatter supporting multiple languages"""

    # Formatter configurations
    FORMATTERS = {
        "python": {"tools": ["black", "autopep8", "yapf"], "extensions": [".py", ".pyw"], "builtin": True},
        "javascript": {"tools": ["prettier", "eslint --fix"], "extensions": [".js", ".jsx", ".mjs"], "builtin": True},
        "typescript": {"tools": ["prettier"], "extensions": [".ts", ".tsx"], "builtin": True},
        "html": {"tools": ["prettier", "html-beautify"], "extensions": [".html", ".htm"], "builtin": True},
        "css": {"tools": ["prettier", "css-beautify"], "extensions": [".css"], "builtin": True},
        "scss": {"tools": ["prettier"], "extensions": [".scss", ".sass"], "builtin": False},
        "json": {"tools": ["prettier"], "extensions": [".json"], "builtin": True},
        "xml": {"tools": ["xmllint --format"], "extensions": [".xml"], "builtin": True},
        "yaml": {"tools": ["prettier"], "extensions": [".yaml", ".yml"], "builtin": True},
        "markdown": {"tools": ["prettier"], "extensions": [".md", ".markdown"], "builtin": False},
        "java": {"tools": ["google-java-format"], "extensions": [".java"], "builtin": True},
        "csharp": {"tools": ["dotnet format"], "extensions": [".cs"], "builtin": True},
        "cpp": {"tools": ["clang-format"], "extensions": [".cpp", ".c", ".h", ".hpp", ".cc", ".cxx"], "builtin": True},
        "go": {"tools": ["gofmt"], "extensions": [".go"], "builtin": False},
        "rust": {"tools": ["rustfmt"], "extensions": [".rs"], "builtin": False},
        "ruby": {"tools": ["rubocop -a", "rufo"], "extensions": [".rb"], "builtin": False},
        "php": {"tools": ["php-cs-fixer fix", "phpcbf"], "extensions": [".php"], "builtin": True},
        "sql": {"tools": ["sql-formatter"], "extensions": [".sql"], "builtin": True},
        "shell": {"tools": ["shfmt"], "extensions": [".sh", ".bash"], "builtin": False},
        "lua": {"tools": ["lua-format"], "extensions": [".lua"], "builtin": True},
        "kotlin": {"tools": ["ktlint -F"], "extensions": [".kt", ".kts"], "builtin": False},
        "swift": {"tools": ["swiftformat"], "extensions": [".swift"], "builtin": False},
        "dart": {"tools": ["dart format"], "extensions": [".dart"], "builtin": False},
        "vue": {"tools": ["prettier"], "extensions": [".vue"], "builtin": False},
        "svelte": {"tools": ["prettier"], "extensions": [".svelte"], "builtin": False},
    }

    def __init__(self):
        self.available_tools = self._detect_available_tools()
        self.settings = {
            "indent_size": 4,
            "use_tabs": False,
            "max_line_length": 80,
            "end_with_newline": True,
            "trim_trailing_whitespace": True,
        }

    def _detect_available_tools(self) -> Dict[str, bool]:
        """Detect which formatting tools are available"""
        tools = {}

        # Common formatters to check
        tool_names = [
            "black",
            "autopep8",
            "yapf",
            "prettier",
            "npx prettier",
            "clang-format",
            "gofmt",
            "rustfmt",
            "shfmt",
            "sql-formatter",
        ]

        for tool in tool_names:
            cmd = tool.split()[0]
            tools[tool] = shutil.which(cmd) is not None

        # Check for npx (Node.js)
        tools["npx"] = shutil.which("npx") is not None

        return tools

    def get_language_from_extension(self, file_path: str) -> Optional[str]:
        """Get language from file extension"""
        ext = Path(file_path).suffix.lower() if file_path else ""

        for lang, config in self.FORMATTERS.items():
            if ext in config["extensions"]:
                return lang
        return None

    def format_code(self, code: str, language: str, file_path: Optional[str] = None) -> Tuple[str, bool, str]:
        """
        Format code using available tools or builtin formatter

        Returns:
            Tuple of (formatted_code, success, message)
        """
        language = language.lower()

        # Try external tools first
        success, result, message = self._try_external_formatter(code, language, file_path)
        if success:
            return result, True, message

        # Fall back to builtin formatter
        if language in self.FORMATTERS and self.FORMATTERS[language].get("builtin"):
            try:
                formatted = self._builtin_format(code, language)
                return formatted, True, f"Formatted with builtin {language} formatter"
            except Exception as e:
                return code, False, f"Builtin formatter error: {str(e)}"

        return code, False, f"No formatter available for {language}"

    def _try_external_formatter(self, code: str, language: str, file_path: Optional[str]) -> Tuple[bool, str, str]:
        """Try to format with external tools"""

        if language not in self.FORMATTERS:
            return False, code, "Language not supported"

        config = self.FORMATTERS[language]

        for tool in config["tools"]:
            try:
                # Try with npx for Node.js tools
                if tool in ["prettier"] and self.available_tools.get("npx"):
                    result = self._run_prettier(code, language)
                    if result is not None:
                        return True, result, f"Formatted with npx {tool}"

                # Try direct tool
                tool_cmd = tool.split()[0]
                if shutil.which(tool_cmd):
                    result = self._run_external_tool(code, tool, language)
                    if result is not None:
                        return True, result, f"Formatted with {tool}"

            except Exception as e:
                continue

        return False, code, "No external formatter succeeded"

    def _run_prettier(self, code: str, language: str) -> Optional[str]:
        """Run prettier formatter"""
        parser_map = {
            "javascript": "babel",
            "typescript": "typescript",
            "html": "html",
            "css": "css",
            "scss": "scss",
            "json": "json",
            "yaml": "yaml",
            "markdown": "markdown",
            "vue": "vue",
            "svelte": "svelte",
        }

        parser = parser_map.get(language, "babel")

        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(mode="w", suffix=f".{language}", delete=False, encoding="utf-8") as f:
                f.write(code)
                temp_path = f.name

            try:
                result = subprocess.run(
                    ["npx", "prettier", "--parser", parser, "--write", temp_path],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    with open(temp_path, "r", encoding="utf-8") as f:
                        return f.read()
            finally:
                os.unlink(temp_path)

        except Exception:
            pass

        return None

    def _run_external_tool(self, code: str, tool: str, language: str) -> Optional[str]:
        """Run an external formatting tool"""

        ext_map = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "cpp": ".cpp",
            "csharp": ".cs",
            "go": ".go",
            "rust": ".rs",
            "ruby": ".rb",
            "php": ".php",
            "sql": ".sql",
            "lua": ".lua",
        }

        ext = ext_map.get(language, ".txt")

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False, encoding="utf-8") as f:
                f.write(code)
                temp_path = f.name

            try:
                # Build command
                cmd_parts = tool.split()

                # Handle different tool patterns
                if tool == "black":
                    cmd = ["black", "-q", temp_path]
                elif tool == "autopep8":
                    cmd = ["autopep8", "--in-place", temp_path]
                elif tool == "yapf":
                    cmd = ["yapf", "-i", temp_path]
                elif tool == "clang-format":
                    cmd = ["clang-format", "-i", temp_path]
                elif tool == "gofmt":
                    cmd = ["gofmt", "-w", temp_path]
                elif tool == "rustfmt":
                    cmd = ["rustfmt", temp_path]
                else:
                    cmd = cmd_parts + [temp_path]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    with open(temp_path, "r", encoding="utf-8") as f:
                        return f.read()

            finally:
                os.unlink(temp_path)

        except Exception:
            pass

        return None

    def _builtin_format(self, code: str, language: str) -> str:
        """Apply builtin formatting rules"""

        formatters = {
            "python": self._format_python,
            "javascript": self._format_javascript,
            "typescript": self._format_javascript,
            "html": self._format_html,
            "css": self._format_css,
            "json": self._format_json,
            "xml": self._format_xml,
            "sql": self._format_sql,
            "java": self._format_java,
            "csharp": self._format_csharp,
            "cpp": self._format_cpp,
            "php": self._format_php,
            "lua": self._format_lua,
        }

        formatter = formatters.get(language)
        if formatter:
            code = formatter(code)

        # Apply common formatting
        code = self._apply_common_formatting(code)

        return code

    def _apply_common_formatting(self, code: str) -> str:
        """Apply common formatting rules to all languages"""
        lines = code.split("\n")

        # Trim trailing whitespace
        if self.settings["trim_trailing_whitespace"]:
            lines = [line.rstrip() for line in lines]

        # Remove excessive blank lines (more than 2 consecutive)
        result = []
        blank_count = 0
        for line in lines:
            if not line.strip():
                blank_count += 1
                if blank_count <= 2:
                    result.append(line)
            else:
                blank_count = 0
                result.append(line)

        code = "\n".join(result)

        # Ensure file ends with newline
        if self.settings["end_with_newline"] and not code.endswith("\n"):
            code += "\n"

        return code

    def _format_python(self, code: str) -> str:
        """Basic Python formatting"""
        lines = code.split("\n")
        formatted_lines = []

        for line in lines:
            # Fix spacing around operators
            line = re.sub(r"(\w)\s*=\s*(\w)", r"\1 = \2", line)
            line = re.sub(r"(\w)\s*==\s*(\w)", r"\1 == \2", line)
            line = re.sub(r"(\w)\s*!=\s*(\w)", r"\1 != \2", line)
            line = re.sub(r"(\w)\s*\+=\s*(\w)", r"\1 += \2", line)
            line = re.sub(r"(\w)\s*-=\s*(\w)", r"\1 -= \2", line)

            # Fix spacing after commas
            line = re.sub(r",(\S)", r", \1", line)

            # Fix spacing after colons in dicts
            line = re.sub(r":(\S)", r": \1", line)

            # Remove trailing semicolons
            line = re.sub(r";\s*$", "", line)

            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def _format_javascript(self, code: str) -> str:
        """Basic JavaScript/TypeScript formatting"""
        lines = code.split("\n")
        formatted_lines = []
        indent_level = 0
        indent_str = " " * self.settings["indent_size"]

        for line in lines:
            stripped = line.strip()

            # Decrease indent for closing braces
            if stripped.startswith(("}", "]", ")")):
                indent_level = max(0, indent_level - 1)

            # Apply indentation
            if stripped:
                formatted_line = indent_str * indent_level + stripped
            else:
                formatted_line = ""

            # Increase indent for opening braces
            open_braces = stripped.count("{") + stripped.count("[")
            close_braces = stripped.count("}") + stripped.count("]")
            indent_level += open_braces - close_braces
            indent_level = max(0, indent_level)

            # Fix spacing
            formatted_line = re.sub(r"\s*{\s*$", " {", formatted_line)
            formatted_line = re.sub(r"}\s*else", "} else", formatted_line)
            formatted_line = re.sub(r",(\S)", r", \1", formatted_line)

            formatted_lines.append(formatted_line)

        return "\n".join(formatted_lines)

    def _format_html(self, code: str) -> str:
        """Basic HTML formatting"""
        # Simple HTML indentation
        indent = 0
        indent_str = " " * self.settings["indent_size"]
        result = []

        # Split by tags while keeping tags
        parts = re.split(r"(<[^>]+>)", code)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Check for closing tag
            if part.startswith("</"):
                indent = max(0, indent - 1)
                result.append(indent_str * indent + part)
            # Check for self-closing or void tag
            elif part.startswith("<") and (
                part.endswith("/>")
                or re.match(r"<(br|hr|img|input|meta|link|area|base|col|embed|param|source|track|wbr)\b", part, re.I)
            ):
                result.append(indent_str * indent + part)
            # Opening tag
            elif part.startswith("<") and not part.startswith("<!"):
                result.append(indent_str * indent + part)
                if not part.endswith("/>"):
                    indent += 1
            else:
                # Text content
                if part:
                    result.append(indent_str * indent + part)

        return "\n".join(result)

    def _format_css(self, code: str) -> str:
        """Basic CSS formatting"""
        indent_str = " " * self.settings["indent_size"]

        # Add newlines after { and before }
        code = re.sub(r"\{\s*", " {\n", code)
        code = re.sub(r"\s*\}", "\n}", code)

        # Add newlines after semicolons (inside blocks)
        code = re.sub(r";\s*(?![\n}])", ";\n", code)

        # Process lines and add indentation
        lines = code.split("\n")
        result = []
        indent = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if stripped == "}":
                indent = max(0, indent - 1)

            result.append(indent_str * indent + stripped)

            if stripped.endswith("{"):
                indent += 1

        return "\n".join(result)

    def _format_json(self, code: str) -> str:
        """Format JSON with proper indentation"""
        import json

        try:
            parsed = json.loads(code)
            return json.dumps(parsed, indent=self.settings["indent_size"], ensure_ascii=False)
        except json.JSONDecodeError:
            return code

    def _format_xml(self, code: str) -> str:
        """Basic XML formatting"""
        # Similar to HTML but stricter
        return self._format_html(code)

    def _format_sql(self, code: str) -> str:
        """Basic SQL formatting"""
        # Uppercase SQL keywords
        keywords = [
            "SELECT",
            "FROM",
            "WHERE",
            "AND",
            "OR",
            "INSERT",
            "INTO",
            "VALUES",
            "UPDATE",
            "SET",
            "DELETE",
            "CREATE",
            "TABLE",
            "DROP",
            "ALTER",
            "JOIN",
            "LEFT",
            "RIGHT",
            "INNER",
            "OUTER",
            "ON",
            "AS",
            "ORDER",
            "BY",
            "GROUP",
            "HAVING",
            "LIMIT",
            "OFFSET",
            "UNION",
            "ALL",
            "DISTINCT",
            "COUNT",
            "SUM",
            "AVG",
            "MAX",
            "MIN",
            "NULL",
            "NOT",
            "IN",
            "LIKE",
            "BETWEEN",
            "EXISTS",
            "CASE",
            "WHEN",
            "THEN",
            "ELSE",
            "END",
            "ASC",
            "DESC",
            "PRIMARY",
            "KEY",
            "FOREIGN",
            "REFERENCES",
            "INDEX",
            "UNIQUE",
            "DEFAULT",
            "AUTO_INCREMENT",
        ]

        result = code
        for keyword in keywords:
            # Match whole word only (case insensitive)
            pattern = rf"\b{keyword}\b"
            result = re.sub(pattern, keyword, result, flags=re.IGNORECASE)

        # Add newlines before main keywords
        main_keywords = [
            "SELECT",
            "FROM",
            "WHERE",
            "AND",
            "OR",
            "ORDER BY",
            "GROUP BY",
            "HAVING",
            "JOIN",
            "LEFT JOIN",
            "RIGHT JOIN",
            "INNER JOIN",
            "LIMIT",
            "UNION",
        ]

        for keyword in main_keywords:
            result = re.sub(rf"\s*\b({keyword})\b", rf"\n\1", result, flags=re.IGNORECASE)

        # Indent after SELECT, add proper spacing
        lines = result.strip().split("\n")
        formatted = []
        indent = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.upper().startswith(("FROM", "WHERE", "ORDER", "GROUP", "HAVING", "LIMIT")):
                indent = 0
            elif stripped.upper().startswith(("AND", "OR")):
                indent = 1

            formatted.append("    " * indent + stripped)

            if stripped.upper().startswith("SELECT"):
                indent = 1

        return "\n".join(formatted)

    def _format_java(self, code: str) -> str:
        """Basic Java formatting"""
        return self._format_javascript(code)  # Similar brace style

    def _format_csharp(self, code: str) -> str:
        """Basic C# formatting"""
        return self._format_javascript(code)

    def _format_cpp(self, code: str) -> str:
        """Basic C++ formatting"""
        code = self._format_javascript(code)

        # Fix pointer/reference spacing (common C++ style)
        code = re.sub(r"\s*\*\s*(\w)", r"* \1", code)
        code = re.sub(r"\s*&\s*(\w)", r"& \1", code)

        return code

    def _format_php(self, code: str) -> str:
        """Basic PHP formatting"""
        return self._format_javascript(code)

    def _format_lua(self, code: str) -> str:
        """Basic Lua formatting"""
        lines = code.split("\n")
        formatted_lines = []
        indent = 0
        indent_str = " " * self.settings["indent_size"]

        increase_keywords = ["function", "if", "for", "while", "repeat", "do"]
        decrease_keywords = ["end", "until"]

        for line in lines:
            stripped = line.strip()

            # Check for decrease first
            if any(stripped.startswith(kw) for kw in decrease_keywords):
                indent = max(0, indent - 1)
            if stripped == "else" or stripped.startswith("elseif"):
                # Temporary decrease for else
                formatted_lines.append(indent_str * max(0, indent - 1) + stripped)
                continue

            formatted_lines.append(indent_str * indent + stripped if stripped else "")

            # Check for increase
            if any(kw in stripped for kw in increase_keywords) and "end" not in stripped:
                indent += 1

        return "\n".join(formatted_lines)

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return list(self.FORMATTERS.keys())

    def get_available_formatters(self) -> Dict[str, List[str]]:
        """Get available formatters per language"""
        result = {}

        for lang, config in self.FORMATTERS.items():
            available = []
            if config.get("builtin"):
                available.append("builtin")

            for tool in config["tools"]:
                tool_name = tool.split()[0]
                if self.available_tools.get(tool) or self.available_tools.get(tool_name):
                    available.append(tool)

            if self.available_tools.get("npx") and "prettier" in config["tools"]:
                if "prettier" not in available:
                    available.append("prettier (via npx)")

            result[lang] = available

        return result


# Global formatter instance
_formatter = None


def get_formatter() -> CodeFormatter:
    """Get global formatter instance"""
    global _formatter
    if _formatter is None:
        _formatter = CodeFormatter()
    return _formatter


def format_code(code: str, language: str, file_path: Optional[str] = None) -> Tuple[str, bool, str]:
    """Convenience function to format code"""
    formatter = get_formatter()
    return formatter.format_code(code, language, file_path)

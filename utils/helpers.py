"""
Code Analytics - Utility Functions
"""

import os
import re
import hashlib
from typing import Dict, List, Tuple, Optional
import chardet


def detect_encoding(file_path: str) -> str:
    """Detect file encoding"""
    with open(file_path, "rb") as f:
        result = chardet.detect(f.read())
        return result["encoding"] or "utf-8"


def read_file_safe(file_path: str) -> Tuple[str, str]:
    """Read file with automatic encoding detection"""
    encoding = detect_encoding(file_path)
    try:
        with open(file_path, "r", encoding=encoding) as f:
            return f.read(), encoding
    except Exception:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(), "utf-8"


def get_file_extension(file_path: str) -> str:
    """Get file extension"""
    return os.path.splitext(file_path)[1].lower()


def detect_language(file_path: str) -> str:
    """Detect programming language from file extension"""
    ext_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "JavaScript (React)",
        ".tsx": "TypeScript (React)",
        ".java": "Java",
        ".cpp": "C++",
        ".c": "C",
        ".h": "C/C++ Header",
        ".hpp": "C++ Header",
        ".cs": "C#",
        ".rb": "Ruby",
        ".go": "Go",
        ".rs": "Rust",
        ".php": "PHP",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".r": "R",
        ".sql": "SQL",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".sass": "SASS",
        ".less": "LESS",
        ".json": "JSON",
        ".xml": "XML",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".md": "Markdown",
        ".sh": "Shell",
        ".bash": "Bash",
        ".ps1": "PowerShell",
        ".bat": "Batch",
        ".lua": "Lua",
        ".pl": "Perl",
        ".ex": "Elixir",
        ".exs": "Elixir",
        ".erl": "Erlang",
        ".clj": "Clojure",
        ".fs": "F#",
        ".vb": "Visual Basic",
        ".dart": "Dart",
        ".vue": "Vue",
        ".svelte": "Svelte",
    }
    ext = get_file_extension(file_path)
    return ext_map.get(ext, "Unknown")


def get_pygments_lexer_name(file_path: str) -> str:
    """Get Pygments lexer name for syntax highlighting"""
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".rb": "ruby",
        ".go": "go",
        ".rs": "rust",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".r": "r",
        ".sql": "sql",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".json": "json",
        ".xml": "xml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".sh": "bash",
        ".bash": "bash",
        ".ps1": "powershell",
        ".bat": "batch",
        ".lua": "lua",
        ".pl": "perl",
    }
    ext = get_file_extension(file_path)
    return ext_map.get(ext, "text")


def calculate_file_hash(content: str) -> str:
    """Calculate MD5 hash of content"""
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def format_size(size_bytes: int) -> str:
    """Format byte size to human readable format"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def count_lines_by_type(code: str) -> Dict[str, int]:
    """Count different types of lines in code"""
    lines = code.split("\n")
    result = {
        "total": len(lines),
        "code": 0,
        "blank": 0,
        "comment": 0,
    }

    in_multiline_comment = False

    for line in lines:
        stripped = line.strip()

        # Check for blank lines
        if not stripped:
            result["blank"] += 1
            continue

        # Check for multi-line comments
        if '"""' in stripped or "'''" in stripped:
            if in_multiline_comment:
                in_multiline_comment = False
                result["comment"] += 1
            else:
                in_multiline_comment = True
                result["comment"] += 1
            continue

        if in_multiline_comment:
            result["comment"] += 1
            continue

        # Check for single-line comments
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("--"):
            result["comment"] += 1
            continue

        # Check for C-style block comments
        if stripped.startswith("/*"):
            result["comment"] += 1
            if "*/" not in stripped:
                in_multiline_comment = True
            continue

        if in_multiline_comment:
            result["comment"] += 1
            if "*/" in stripped:
                in_multiline_comment = False
            continue

        result["code"] += 1

    return result


def find_todos(code: str) -> List[Dict[str, any]]:
    """Find TODO, FIXME, HACK, XXX comments"""
    patterns = [
        (r"#\s*(TODO|FIXME|HACK|XXX|BUG|NOTE):\s*(.+)", "Python/Shell"),
        (r"//\s*(TODO|FIXME|HACK|XXX|BUG|NOTE):\s*(.+)", "C-style"),
        (r"/\*\s*(TODO|FIXME|HACK|XXX|BUG|NOTE):\s*(.+)\*/", "Block"),
    ]

    todos = []
    lines = code.split("\n")

    for line_num, line in enumerate(lines, 1):
        for pattern, style in patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                todos.append(
                    {
                        "type": match.group(1).upper(),
                        "message": match.group(2).strip(),
                        "line": line_num,
                        "style": style,
                    }
                )

    return todos


def extract_strings(code: str) -> List[Dict[str, any]]:
    """Extract string literals from code"""
    strings = []

    # Match various string patterns
    patterns = [
        (r'"""(.+?)"""', "triple-double"),
        (r"'''(.+?)'''", "triple-single"),
        (r'"([^"\\]*(?:\\.[^"\\]*)*)"', "double"),
        (r"'([^'\\]*(?:\\.[^'\\]*)*)'", "single"),
        (r"`([^`]*)`", "backtick"),
    ]

    for pattern, string_type in patterns:
        for match in re.finditer(pattern, code, re.DOTALL):
            strings.append({"value": match.group(1), "type": string_type, "length": len(match.group(1))})

    return strings

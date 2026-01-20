"""
Code Analytics - Syntax Highlighter
Uses Pygments for syntax highlighting in tkinter Text widget
"""

import tkinter as tk
from typing import Dict, Tuple, Optional

try:
    from pygments import lex
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.token import Token

    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False


class SyntaxHighlighter:
    """Syntax highlighting for code display"""

    # Color schemes
    THEMES = {
        "dark": {
            Token.Keyword: "#ff79c6",
            Token.Keyword.Namespace: "#ff79c6",
            Token.Keyword.Type: "#8be9fd",
            Token.Name: "#f8f8f2",
            Token.Name.Function: "#50fa7b",
            Token.Name.Class: "#8be9fd",
            Token.Name.Builtin: "#8be9fd",
            Token.Name.Decorator: "#50fa7b",
            Token.Name.Exception: "#ff5555",
            Token.String: "#f1fa8c",
            Token.String.Doc: "#6272a4",
            Token.Number: "#bd93f9",
            Token.Operator: "#ff79c6",
            Token.Comment: "#6272a4",
            Token.Comment.Single: "#6272a4",
            Token.Comment.Multiline: "#6272a4",
            Token.Punctuation: "#f8f8f2",
            Token.Error: "#ff5555",
            Token.Generic.Deleted: "#ff5555",
            Token.Generic.Inserted: "#50fa7b",
        },
        "light": {
            Token.Keyword: "#d73a49",
            Token.Keyword.Namespace: "#d73a49",
            Token.Keyword.Type: "#005cc5",
            Token.Name: "#24292e",
            Token.Name.Function: "#6f42c1",
            Token.Name.Class: "#005cc5",
            Token.Name.Builtin: "#005cc5",
            Token.Name.Decorator: "#6f42c1",
            Token.Name.Exception: "#d73a49",
            Token.String: "#032f62",
            Token.String.Doc: "#6a737d",
            Token.Number: "#005cc5",
            Token.Operator: "#d73a49",
            Token.Comment: "#6a737d",
            Token.Comment.Single: "#6a737d",
            Token.Comment.Multiline: "#6a737d",
            Token.Punctuation: "#24292e",
            Token.Error: "#cb2431",
            Token.Generic.Deleted: "#cb2431",
            Token.Generic.Inserted: "#22863a",
        },
        "monokai": {
            Token.Keyword: "#f92672",
            Token.Keyword.Namespace: "#f92672",
            Token.Keyword.Type: "#66d9ef",
            Token.Name: "#f8f8f2",
            Token.Name.Function: "#a6e22e",
            Token.Name.Class: "#66d9ef",
            Token.Name.Builtin: "#66d9ef",
            Token.Name.Decorator: "#a6e22e",
            Token.Name.Exception: "#f92672",
            Token.String: "#e6db74",
            Token.String.Doc: "#75715e",
            Token.Number: "#ae81ff",
            Token.Operator: "#f92672",
            Token.Comment: "#75715e",
            Token.Comment.Single: "#75715e",
            Token.Comment.Multiline: "#75715e",
            Token.Punctuation: "#f8f8f2",
            Token.Error: "#f92672",
        },
    }

    def __init__(self, text_widget: tk.Text, theme: str = "dark"):
        self.text_widget = text_widget
        self.theme = theme
        self.colors = self.THEMES.get(theme, self.THEMES["dark"])
        self.lexer = None
        self._setup_tags()

    def _setup_tags(self):
        """Setup text tags for highlighting"""
        for token_type, color in self.colors.items():
            tag_name = str(token_type)
            self.text_widget.tag_configure(tag_name, foreground=color)

        # Special formatting
        self.text_widget.tag_configure("bold", font=("Consolas", 11, "bold"))
        self.text_widget.tag_configure("italic", font=("Consolas", 11, "italic"))

    def set_lexer(self, lexer_name: str):
        """Set the lexer for syntax highlighting"""
        if not PYGMENTS_AVAILABLE:
            return

        try:
            self.lexer = get_lexer_by_name(lexer_name)
        except Exception:
            self.lexer = None

    def highlight(self, start: str = "1.0", end: str = tk.END):
        """Apply syntax highlighting to the text widget"""
        if not PYGMENTS_AVAILABLE or self.lexer is None:
            return

        # Get the code
        code = self.text_widget.get(start, end)

        # Remove existing tags
        for token_type in self.colors:
            self.text_widget.tag_remove(str(token_type), start, end)

        # Apply new highlighting
        self._apply_highlighting(code, start)

    def _apply_highlighting(self, code: str, start_pos: str = "1.0"):
        """Apply highlighting tokens"""
        try:
            tokens = lex(code, self.lexer)

            # Calculate starting position
            start_line, start_col = map(int, start_pos.split("."))
            current_line = start_line
            current_col = start_col

            for token_type, token_value in tokens:
                # Calculate positions
                start_index = f"{current_line}.{current_col}"

                # Update position based on token value
                lines = token_value.split("\n")
                if len(lines) > 1:
                    current_line += len(lines) - 1
                    current_col = len(lines[-1])
                else:
                    current_col += len(token_value)

                end_index = f"{current_line}.{current_col}"

                # Apply tag
                tag_name = self._get_tag_for_token(token_type)
                if tag_name:
                    self.text_widget.tag_add(tag_name, start_index, end_index)

        except Exception as e:
            print(f"Highlighting error: {e}")

    def _get_tag_for_token(self, token_type) -> Optional[str]:
        """Get the appropriate tag for a token type"""
        # Try exact match first
        if token_type in self.colors:
            return str(token_type)

        # Try parent token types
        parent = token_type
        while parent:
            if parent in self.colors:
                return str(parent)
            parent = parent.parent

        return None

    def set_theme(self, theme: str):
        """Change the color theme"""
        if theme in self.THEMES:
            self.theme = theme
            self.colors = self.THEMES[theme]
            self._setup_tags()
            self.highlight()


class LineNumbers:
    """Line numbers widget for code display"""

    def __init__(self, text_widget: tk.Text, canvas: tk.Canvas):
        self.text_widget = text_widget
        self.canvas = canvas
        self.line_count = 0

    def update(self):
        """Update line numbers"""
        self.canvas.delete("all")

        # Get the text widget's scroll position
        first_visible = self.text_widget.index("@0,0")
        last_visible = self.text_widget.index(f"@0,{self.text_widget.winfo_height()}")

        first_line = int(first_visible.split(".")[0])
        last_line = int(last_visible.split(".")[0])

        # Get total lines
        total_lines = int(self.text_widget.index("end-1c").split(".")[0])

        # Draw line numbers
        for line_num in range(first_line, min(last_line + 1, total_lines + 1)):
            # Get the y position of this line
            dline = self.text_widget.dlineinfo(f"{line_num}.0")
            if dline:
                y = dline[1]
                self.canvas.create_text(35, y, text=str(line_num), anchor="ne", fill="#6272a4", font=("Consolas", 10))


def apply_simple_highlighting(text_widget: tk.Text, code: str, language: str):
    """Apply simple regex-based highlighting when Pygments is not available"""
    # Clear existing tags
    for tag in text_widget.tag_names():
        if tag != "sel":
            text_widget.tag_remove(tag, "1.0", tk.END)

    # Setup basic tags
    text_widget.tag_configure("keyword", foreground="#ff79c6")
    text_widget.tag_configure("string", foreground="#f1fa8c")
    text_widget.tag_configure("comment", foreground="#6272a4")
    text_widget.tag_configure("number", foreground="#bd93f9")
    text_widget.tag_configure("function", foreground="#50fa7b")
    text_widget.tag_configure("class", foreground="#8be9fd")

    # Python keywords
    python_keywords = [
        "and",
        "as",
        "assert",
        "async",
        "await",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "nonlocal",
        "not",
        "or",
        "pass",
        "raise",
        "return",
        "try",
        "while",
        "with",
        "yield",
        "True",
        "False",
        "None",
    ]

    import re

    # Highlight keywords
    for keyword in python_keywords:
        pattern = rf"\b{keyword}\b"
        for match in re.finditer(pattern, code):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            text_widget.tag_add("keyword", start, end)

    # Highlight strings
    for match in re.finditer(r'(["\'])(?:(?!\1).)*\1', code):
        start = f"1.0+{match.start()}c"
        end = f"1.0+{match.end()}c"
        text_widget.tag_add("string", start, end)

    # Highlight comments
    for match in re.finditer(r"#.*$", code, re.MULTILINE):
        start = f"1.0+{match.start()}c"
        end = f"1.0+{match.end()}c"
        text_widget.tag_add("comment", start, end)

    # Highlight numbers
    for match in re.finditer(r"\b\d+\.?\d*\b", code):
        start = f"1.0+{match.start()}c"
        end = f"1.0+{match.end()}c"
        text_widget.tag_add("number", start, end)

    # Highlight function definitions
    for match in re.finditer(r"def\s+(\w+)", code):
        start = f"1.0+{match.start(1)}c"
        end = f"1.0+{match.end(1)}c"
        text_widget.tag_add("function", start, end)

    # Highlight class definitions
    for match in re.finditer(r"class\s+(\w+)", code):
        start = f"1.0+{match.start(1)}c"
        end = f"1.0+{match.end(1)}c"
        text_widget.tag_add("class", start, end)

"""
Code Analytics - Main Application
A comprehensive code analysis tool with modern UI
"""

import os
import sys
import json
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

try:
    from ttkbootstrap.widgets.scrolled import ScrolledText, ScrolledFrame
    from ttkbootstrap.widgets import ToolTip
except ImportError:
    from ttkbootstrap.scrolled import ScrolledText, ScrolledFrame
    from ttkbootstrap.tooltip import ToolTip

# Import analyzers
from analyzers.code_analyzer import BasicAnalyzer, PythonAnalyzer, get_analyzer
from analyzers.security_analyzer import SecurityAnalyzer
from analyzers.performance_analyzer import PerformanceAnalyzer
from analyzers.quality_analyzer import QualityAnalyzer

# Import utilities
from utils.helpers import (
    read_file_safe,
    detect_language,
    get_pygments_lexer_name,
    count_lines_by_type,
    find_todos,
    format_size,
    calculate_file_hash,
)
from utils.formatter import CodeFormatter, get_formatter

# Import UI components
from ui.syntax_highlighter import SyntaxHighlighter, apply_simple_highlighting, PYGMENTS_AVAILABLE
from ui.result_views import TreeResultView, MetricsView, IssuesListView, SummaryView, CodeStructureView


class CodeAnalyticsApp:
    """Main application class"""

    VERSION = "1.0.0"

    def __init__(self):
        # Create main window with ttkbootstrap theme
        self.root = ttk.Window(title="Code Analytics", themename="darkly", size=(1400, 900), minsize=(1000, 700))

        # Application state
        self.current_file: Optional[str] = None
        self.current_code: str = ""
        self.current_language: str = "Unknown"
        self.analysis_results: Dict[str, Any] = {}
        self.recent_files: List[str] = []
        self.settings = self._load_settings()

        # Setup UI
        self._setup_menu()
        self._setup_toolbar()
        self._setup_main_layout()
        self._setup_status_bar()

        # Bind keyboard shortcuts
        self._setup_shortcuts()

        # Load recent files
        self._load_recent_files()

    def _load_settings(self) -> Dict[str, Any]:
        """Load application settings"""
        settings_path = Path(__file__).parent / "settings.json"
        default_settings = {
            "theme": "darkly",
            "font_size": 11,
            "font_family": "Consolas",
            "auto_analyze": True,
            "show_line_numbers": True,
            "highlight_syntax": True,
            "max_recent_files": 10,
        }

        if settings_path.exists():
            try:
                with open(settings_path, "r") as f:
                    return {**default_settings, **json.load(f)}
            except Exception:
                pass

        return default_settings

    def _save_settings(self):
        """Save application settings"""
        settings_path = Path(__file__).parent / "settings.json"
        try:
            with open(settings_path, "w") as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Could not save settings: {e}")

    def _load_recent_files(self):
        """Load recent files list"""
        recent_path = Path(__file__).parent / "recent_files.json"
        if recent_path.exists():
            try:
                with open(recent_path, "r") as f:
                    self.recent_files = json.load(f)
            except Exception:
                pass

    def _save_recent_files(self):
        """Save recent files list"""
        recent_path = Path(__file__).parent / "recent_files.json"
        try:
            with open(recent_path, "w") as f:
                json.dump(self.recent_files[: self.settings["max_recent_files"]], f)
        except Exception:
            pass

    def _setup_menu(self):
        """Setup menu bar"""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open File...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Open Folder...", command=self.open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Paste Code", command=self.paste_code, accelerator="Ctrl+V")
        file_menu.add_separator()

        # Recent files submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)

        file_menu.add_separator()
        file_menu.add_command(label="Export Report...", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Alt+F4")

        # Analysis menu
        analysis_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Run Full Analysis", command=self.run_full_analysis, accelerator="F5")
        analysis_menu.add_separator()
        analysis_menu.add_command(label="Basic Statistics", command=lambda: self.run_analysis("basic"))
        analysis_menu.add_command(label="Security Scan", command=lambda: self.run_analysis("security"))
        analysis_menu.add_command(label="Performance Check", command=lambda: self.run_analysis("performance"))
        analysis_menu.add_command(label="Quality Analysis", command=lambda: self.run_analysis("quality"))
        analysis_menu.add_separator()
        analysis_menu.add_command(label="Find TODOs", command=self.find_todos)
        analysis_menu.add_command(label="Find Duplicates", command=self.find_duplicates)

        # View menu
        view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="View", menu=view_menu)

        # Theme submenu
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        for theme in ["darkly", "superhero", "solar", "cyborg", "vapor", "litera", "minty", "flatly"]:
            theme_menu.add_command(label=theme.title(), command=lambda t=theme: self.change_theme(t))

        view_menu.add_separator()
        view_menu.add_checkbutton(label="Show Line Numbers", command=self.toggle_line_numbers)
        view_menu.add_checkbutton(label="Syntax Highlighting", command=self.toggle_syntax_highlighting)

        # Tools menu
        tools_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Format Code", command=self.format_code, accelerator="Ctrl+Shift+F")
        tools_menu.add_command(label="Format Settings...", command=self.show_format_settings)
        tools_menu.add_separator()
        tools_menu.add_command(label="Compare Files...", command=self.compare_files)
        tools_menu.add_command(label="Batch Analyze Folder...", command=self.batch_analyze)
        tools_menu.add_separator()
        tools_menu.add_command(label="Settings...", command=self.show_settings)

        # Help menu
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_docs)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)

    def _setup_toolbar(self):
        """Setup toolbar"""
        self.toolbar = ttk.Frame(self.root, padding=5)
        self.toolbar.pack(fill="x", padx=5, pady=(5, 0))

        # File operations
        ttk.Button(self.toolbar, text="📂 Open", command=self.open_file, bootstyle="outline").pack(side="left", padx=2)

        ttk.Button(self.toolbar, text="📋 Paste", command=self.paste_code, bootstyle="outline").pack(
            side="left", padx=2
        )

        ttk.Separator(self.toolbar, orient="vertical").pack(side="left", padx=10, fill="y")

        # Analysis buttons
        ttk.Button(self.toolbar, text="▶️ Analyze", command=self.run_full_analysis, bootstyle="success").pack(
            side="left", padx=2
        )

        ttk.Button(
            self.toolbar, text="🔒 Security", command=lambda: self.run_analysis("security"), bootstyle="outline-warning"
        ).pack(side="left", padx=2)

        ttk.Button(
            self.toolbar,
            text="⚡ Performance",
            command=lambda: self.run_analysis("performance"),
            bootstyle="outline-info",
        ).pack(side="left", padx=2)

        ttk.Button(
            self.toolbar, text="📊 Quality", command=lambda: self.run_analysis("quality"), bootstyle="outline-primary"
        ).pack(side="left", padx=2)

        ttk.Separator(self.toolbar, orient="vertical").pack(side="left", padx=10, fill="y")

        # Export button
        ttk.Button(self.toolbar, text="📤 Export", command=self.export_report, bootstyle="outline").pack(
            side="left", padx=2
        )

        ttk.Separator(self.toolbar, orient="vertical").pack(side="left", padx=10, fill="y")

        # Format button
        ttk.Button(self.toolbar, text="✨ Format", command=self.format_code, bootstyle="outline-secondary").pack(
            side="left", padx=2
        )

        # Right side - search
        search_frame = ttk.Frame(self.toolbar)
        search_frame.pack(side="right", padx=5)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        self.search_entry.pack(side="left", padx=2)
        self.search_entry.bind("<Return>", self.search_in_code)

        ttk.Button(search_frame, text="🔍", command=self.search_in_code, bootstyle="outline", width=3).pack(side="left")

    def _setup_main_layout(self):
        """Setup main application layout"""
        # Main paned window
        self.main_paned = ttk.Panedwindow(self.root, orient="horizontal")
        self.main_paned.pack(fill="both", expand=True, padx=5, pady=5)

        # Left panel - Code view
        self.code_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(self.code_panel, weight=3)

        # File info header
        self.file_info_frame = ttk.Frame(self.code_panel)
        self.file_info_frame.pack(fill="x", pady=(0, 5))

        self.file_label = ttk.Label(self.file_info_frame, text="No file loaded", font=("Segoe UI", 10, "bold"))
        self.file_label.pack(side="left")

        self.language_label = ttk.Label(self.file_info_frame, text="", bootstyle="info")
        self.language_label.pack(side="right")

        # Code display with line numbers
        code_frame = ttk.Frame(self.code_panel)
        code_frame.pack(fill="both", expand=True)

        # Line numbers canvas
        self.line_numbers = tk.Canvas(code_frame, width=50, bg="#1a1a2e", highlightthickness=0)
        self.line_numbers.pack(side="left", fill="y")

        # Code text widget
        self.code_text = tk.Text(
            code_frame,
            wrap="none",
            font=(self.settings["font_family"], self.settings["font_size"]),
            bg="#1a1a2e",
            fg="#f8f8f2",
            insertbackground="white",
            selectbackground="#44475a",
            padx=10,
            pady=10,
        )
        self.code_text.pack(side="left", fill="both", expand=True)

        # Scrollbars for code
        code_vsb = ttk.Scrollbar(code_frame, orient="vertical", command=self._sync_scroll)
        code_vsb.pack(side="right", fill="y")

        code_hsb = ttk.Scrollbar(self.code_panel, orient="horizontal", command=self.code_text.xview)
        code_hsb.pack(fill="x")

        self.code_text.configure(yscrollcommand=self._on_code_scroll, xscrollcommand=code_hsb.set)

        # Bind events for line numbers update
        self.code_text.bind("<Configure>", self._update_line_numbers)
        self.code_text.bind("<KeyRelease>", self._update_line_numbers)

        # Initialize syntax highlighter
        if PYGMENTS_AVAILABLE:
            self.highlighter = SyntaxHighlighter(self.code_text, "dark")
        else:
            self.highlighter = None

        # Right panel - Analysis results
        self.results_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(self.results_panel, weight=2)

        # Results notebook (tabs)
        self.results_notebook = ttk.Notebook(self.results_panel)
        self.results_notebook.pack(fill="both", expand=True)

        # Overview tab
        self.overview_frame = ttk.Frame(self.results_notebook, padding=10)
        self.results_notebook.add(self.overview_frame, text="📊 Overview")
        self._setup_overview_tab()

        # Structure tab
        self.structure_frame = ttk.Frame(self.results_notebook, padding=10)
        self.results_notebook.add(self.structure_frame, text="🏗️ Structure")
        self._setup_structure_tab()

        # Security tab
        self.security_frame = ttk.Frame(self.results_notebook, padding=10)
        self.results_notebook.add(self.security_frame, text="🔒 Security")
        self._setup_security_tab()

        # Performance tab
        self.performance_frame = ttk.Frame(self.results_notebook, padding=10)
        self.results_notebook.add(self.performance_frame, text="⚡ Performance")
        self._setup_performance_tab()

        # Quality tab
        self.quality_frame = ttk.Frame(self.results_notebook, padding=10)
        self.results_notebook.add(self.quality_frame, text="📈 Quality")
        self._setup_quality_tab()

        # Issues tab
        self.issues_frame = ttk.Frame(self.results_notebook, padding=10)
        self.results_notebook.add(self.issues_frame, text="⚠️ Issues")
        self._setup_issues_tab()

    def _setup_overview_tab(self):
        """Setup overview tab content"""
        # Metrics display
        self.metrics_view = MetricsView(self.overview_frame)
        self.metrics_view.pack(fill="both", expand=True)

        # Initial placeholder
        placeholder = ttk.Label(
            self.metrics_view, text="Load a file or paste code to see analysis", font=("Segoe UI", 12)
        )
        placeholder.pack(pady=50)

    def _setup_structure_tab(self):
        """Setup structure tab content"""
        self.structure_view = CodeStructureView(self.structure_frame, on_select=self.go_to_line)
        self.structure_view.pack(fill="both", expand=True)

    def _setup_security_tab(self):
        """Setup security tab content"""
        # Summary at top
        self.security_summary_label = ttk.Label(
            self.security_frame, text="Run security analysis to see results", font=("Segoe UI", 11)
        )
        self.security_summary_label.pack(fill="x", pady=(0, 10))

        # Issues list
        self.security_issues_view = IssuesListView(self.security_frame, on_click=self.go_to_line)
        self.security_issues_view.pack(fill="both", expand=True)

    def _setup_performance_tab(self):
        """Setup performance tab content"""
        # Summary at top
        self.performance_summary_label = ttk.Label(
            self.performance_frame, text="Run performance analysis to see results", font=("Segoe UI", 11)
        )
        self.performance_summary_label.pack(fill="x", pady=(0, 10))

        # Issues list
        self.performance_issues_view = IssuesListView(self.performance_frame, on_click=self.go_to_line)
        self.performance_issues_view.pack(fill="both", expand=True)

        # Suggestions
        self.suggestions_label = ttk.Label(self.performance_frame, text="", font=("Segoe UI", 10), wraplength=400)
        self.suggestions_label.pack(fill="x", pady=10)

    def _setup_quality_tab(self):
        """Setup quality tab content"""
        # Score display
        self.quality_score_frame = ttk.Frame(self.quality_frame)
        self.quality_score_frame.pack(fill="x", pady=10)

        self.quality_grade_label = ttk.Label(self.quality_score_frame, text="-", font=("Segoe UI", 48, "bold"))
        self.quality_grade_label.pack()

        self.quality_score_label = ttk.Label(
            self.quality_score_frame, text="Run quality analysis", font=("Segoe UI", 12)
        )
        self.quality_score_label.pack()

        # Details
        self.quality_details_frame = ScrolledFrame(self.quality_frame)
        self.quality_details_frame.pack(fill="both", expand=True)

    def _setup_issues_tab(self):
        """Setup issues tab content"""
        # Filter buttons
        filter_frame = ttk.Frame(self.issues_frame)
        filter_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(filter_frame, text="Filter:").pack(side="left", padx=(0, 10))

        self.issue_filter = tk.StringVar(value="all")
        for text, value in [("All", "all"), ("Critical", "critical"), ("High", "high"), ("Medium", "medium")]:
            ttk.Radiobutton(
                filter_frame, text=text, variable=self.issue_filter, value=value, command=self._filter_issues
            ).pack(side="left", padx=5)

        # All issues list
        self.all_issues_view = IssuesListView(self.issues_frame, on_click=self.go_to_line)
        self.all_issues_view.pack(fill="both", expand=True)

    def _setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill="x", padx=5, pady=5)

        self.status_label = ttk.Label(self.status_bar, text="Ready", font=("Segoe UI", 9))
        self.status_label.pack(side="left")

        # Right side info
        self.cursor_label = ttk.Label(self.status_bar, text="Ln 1, Col 1", font=("Segoe UI", 9))
        self.cursor_label.pack(side="right", padx=10)

        self.encoding_label = ttk.Label(self.status_bar, text="UTF-8", font=("Segoe UI", 9))
        self.encoding_label.pack(side="right", padx=10)

        # Bind cursor position update
        self.code_text.bind("<KeyRelease>", self._update_cursor_position)
        self.code_text.bind("<ButtonRelease-1>", self._update_cursor_position)

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-v>", lambda e: self.paste_code())
        self.root.bind("<F5>", lambda e: self.run_full_analysis())
        self.root.bind("<Control-f>", lambda e: self.search_entry.focus())
        self.root.bind("<Control-g>", lambda e: self.show_go_to_line_dialog())
        self.root.bind("<Control-Shift-F>", lambda e: self.format_code())
        self.root.bind("<Control-Shift-f>", lambda e: self.format_code())
        self.root.bind("<Escape>", lambda e: self._clear_search())

    def _sync_scroll(self, *args):
        """Sync scrolling between line numbers and code"""
        self.code_text.yview(*args)
        self._update_line_numbers()

    def _on_code_scroll(self, *args):
        """Handle code text scrolling"""
        self._update_line_numbers()
        return True

    def _update_line_numbers(self, event=None):
        """Update line numbers display"""
        self.line_numbers.delete("all")

        if not self.settings["show_line_numbers"]:
            return

        # Get visible lines
        first_visible = self.code_text.index("@0,0")
        last_visible = self.code_text.index(f"@0,{self.code_text.winfo_height()}")

        first_line = int(first_visible.split(".")[0])
        last_line = int(last_visible.split(".")[0])

        # Draw line numbers
        for line_num in range(first_line, last_line + 1):
            dline = self.code_text.dlineinfo(f"{line_num}.0")
            if dline:
                y = dline[1]
                self.line_numbers.create_text(
                    40,
                    y + 2,
                    text=str(line_num),
                    anchor="ne",
                    fill="#6272a4",
                    font=(self.settings["font_family"], self.settings["font_size"] - 1),
                )

    def _update_cursor_position(self, event=None):
        """Update cursor position in status bar"""
        try:
            cursor_pos = self.code_text.index("insert")
            line, col = cursor_pos.split(".")
            self.cursor_label.config(text=f"Ln {line}, Col {int(col) + 1}")
        except Exception:
            pass

    def set_status(self, message: str):
        """Set status bar message"""
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def open_file(self):
        """Open a file for analysis"""
        filetypes = [
            ("All Code Files", "*.py *.js *.ts *.java *.cpp *.c *.cs *.rb *.go *.rs *.php"),
            ("Python Files", "*.py"),
            ("JavaScript/TypeScript", "*.js *.ts *.jsx *.tsx"),
            ("Java Files", "*.java"),
            ("C/C++ Files", "*.c *.cpp *.h *.hpp"),
            ("All Files", "*.*"),
        ]

        file_path = filedialog.askopenfilename(title="Open File", filetypes=filetypes)

        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path: str):
        """Load a file into the editor"""
        try:
            self.set_status(f"Loading {os.path.basename(file_path)}...")

            # Read file
            content, encoding = read_file_safe(file_path)

            # Update state
            self.current_file = file_path
            self.current_code = content
            self.current_language = detect_language(file_path)

            # Update UI
            self._display_code(content)
            self.file_label.config(text=os.path.basename(file_path))
            self.language_label.config(text=self.current_language)
            self.encoding_label.config(text=encoding.upper())

            # Add to recent files
            if file_path in self.recent_files:
                self.recent_files.remove(file_path)
            self.recent_files.insert(0, file_path)
            self._save_recent_files()
            self._update_recent_menu()

            # Auto-analyze if enabled
            if self.settings["auto_analyze"]:
                self.run_full_analysis()

            self.set_status(f"Loaded: {file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{str(e)}")
            self.set_status("Error loading file")

    def _display_code(self, code: str):
        """Display code in the text widget"""
        self.code_text.config(state="normal")
        self.code_text.delete("1.0", "end")
        self.code_text.insert("1.0", code)

        # Apply syntax highlighting
        if self.settings["highlight_syntax"]:
            if PYGMENTS_AVAILABLE and self.highlighter:
                lexer_name = get_pygments_lexer_name(self.current_file or "code.py")
                self.highlighter.set_lexer(lexer_name)
                self.highlighter.highlight()
            else:
                apply_simple_highlighting(self.code_text, code, self.current_language)

        self._update_line_numbers()

    def _update_recent_menu(self):
        """Update recent files menu"""
        self.recent_menu.delete(0, "end")

        for file_path in self.recent_files[:10]:
            self.recent_menu.add_command(
                label=os.path.basename(file_path), command=lambda p=file_path: self.load_file(p)
            )

    def paste_code(self):
        """Paste code from clipboard"""
        try:
            clipboard = self.root.clipboard_get()
            if clipboard:
                self.current_file = None
                self.current_code = clipboard
                self.current_language = self._detect_language_from_content(clipboard)

                self._display_code(clipboard)
                self.file_label.config(text="Pasted Code")
                self.language_label.config(text=self.current_language)

                if self.settings["auto_analyze"]:
                    self.run_full_analysis()

                self.set_status("Code pasted from clipboard")
        except Exception as e:
            messagebox.showerror("Error", f"Could not paste:\n{str(e)}")

    def _detect_language_from_content(self, code: str) -> str:
        """Detect language from code content"""
        # Simple heuristics
        if "def " in code and "import " in code:
            return "Python"
        elif "function " in code or "const " in code or "let " in code:
            return "JavaScript"
        elif "class " in code and "public " in code:
            return "Java"
        elif "#include" in code:
            return "C/C++"
        return "Unknown"

    def open_folder(self):
        """Open a folder for batch analysis"""
        folder_path = filedialog.askdirectory(title="Select Folder")
        if folder_path:
            self.batch_analyze(folder_path)

    def run_full_analysis(self):
        """Run all analysis types"""
        if not self.current_code:
            messagebox.showinfo("Info", "Please load a file or paste code first.")
            return

        self.set_status("Running full analysis...")

        # Run in thread to keep UI responsive
        def analyze():
            try:
                # Basic analysis
                analyzer = get_analyzer(self.current_code, self.current_language)
                self.analysis_results["basic"] = {
                    "stats": analyzer.get_basic_stats(),
                    "line_distribution": analyzer.get_line_length_distribution(),
                    "indentation": analyzer.get_indentation_analysis(),
                    "word_frequency": analyzer.get_word_frequency(15),
                    "patterns": analyzer.find_patterns(),
                    "duplicates": analyzer.find_duplicates(),
                }

                # Python-specific analysis
                if self.current_language == "Python" and isinstance(analyzer, PythonAnalyzer):
                    self.analysis_results["python"] = {
                        "imports": analyzer.get_imports(),
                        "functions": analyzer.get_functions(),
                        "classes": analyzer.get_classes(),
                        "variables": analyzer.get_variables(),
                        "pep8_issues": analyzer.check_pep8_issues(),
                        "complexity": analyzer.get_complexity_metrics(),
                        "syntax_error": analyzer.get_syntax_errors(),
                    }

                # Security analysis
                security = SecurityAnalyzer(self.current_code, self.current_language)
                self.analysis_results["security"] = security.analyze()

                # Performance analysis
                performance = PerformanceAnalyzer(self.current_code, self.current_language)
                self.analysis_results["performance"] = performance.analyze()

                # Quality analysis
                quality = QualityAnalyzer(self.current_code, self.current_language)
                self.analysis_results["quality"] = quality.analyze()

                # Line counts
                self.analysis_results["lines"] = count_lines_by_type(self.current_code)

                # TODOs
                self.analysis_results["todos"] = find_todos(self.current_code)

                # Update UI in main thread
                self.root.after(0, self._update_analysis_ui)

            except Exception as e:
                self.root.after(0, lambda: self._show_analysis_error(str(e)))

        thread = threading.Thread(target=analyze)
        thread.start()

    def _update_analysis_ui(self):
        """Update UI with analysis results"""
        try:
            # Update overview tab
            self._update_overview()

            # Update structure tab
            self._update_structure()

            # Update security tab
            self._update_security()

            # Update performance tab
            self._update_performance()

            # Update quality tab
            self._update_quality()

            # Update issues tab
            self._update_all_issues()

            self.set_status("Analysis complete")

        except Exception as e:
            self._show_analysis_error(str(e))

    def _update_overview(self):
        """Update overview tab"""
        basic = self.analysis_results.get("basic", {})
        stats = basic.get("stats", {})
        lines = self.analysis_results.get("lines", {})

        # Create metrics dictionary
        metrics = {
            "Total Lines": stats.get("total_lines", 0),
            "Code Lines": lines.get("code", 0),
            "Blank Lines": lines.get("blank", 0),
            "Comment Lines": lines.get("comment", 0),
            "Total Characters": stats.get("total_characters", 0),
            "Avg Line Length": f"{stats.get('average_line_length', 0):.1f}",
        }

        # Add complexity metrics if Python
        if "python" in self.analysis_results:
            complexity = self.analysis_results["python"].get("complexity", {})
            metrics["Functions"] = complexity.get("total_functions", 0)
            metrics["Classes"] = complexity.get("total_classes", 0)
            metrics["Avg Complexity"] = f"{complexity.get('average_complexity', 0):.1f}"

        self.metrics_view.set_metrics(metrics)

    def _update_structure(self):
        """Update structure tab"""
        classes = []
        functions = []
        variables = []

        if "python" in self.analysis_results:
            python_data = self.analysis_results["python"]
            classes = python_data.get("classes", [])
            functions = python_data.get("functions", [])
            variables = python_data.get("variables", [])

        self.structure_view.set_structure(classes, functions, variables)

    def _update_security(self):
        """Update security tab"""
        security = self.analysis_results.get("security", {})

        # Update summary
        total = security.get("total_issues", 0)
        risk = security.get("risk_score", 0)

        if total == 0:
            summary = "✅ No security issues detected"
            self.security_summary_label.config(bootstyle="success")
        else:
            severity = security.get("severity_counts", {})
            summary = f"⚠️ {total} issues found (Risk Score: {risk}/100)"
            if severity.get("critical", 0) > 0:
                self.security_summary_label.config(bootstyle="danger")
            elif severity.get("high", 0) > 0:
                self.security_summary_label.config(bootstyle="warning")
            else:
                self.security_summary_label.config(bootstyle="info")

        self.security_summary_label.config(text=summary)

        # Update issues list
        self.security_issues_view.set_issues(security.get("issues", []))

    def _update_performance(self):
        """Update performance tab"""
        performance = self.analysis_results.get("performance", {})

        # Update summary
        issues = performance.get("issues", [])
        if not issues:
            summary = "✅ No significant performance issues"
            self.performance_summary_label.config(bootstyle="success")
        else:
            high_count = sum(1 for i in issues if i.get("severity") == "high")
            summary = f"⚠️ {len(issues)} potential issues ({high_count} high priority)"
            self.performance_summary_label.config(bootstyle="warning" if high_count else "info")

        self.performance_summary_label.config(text=summary)

        # Update issues list
        self.performance_issues_view.set_issues(issues)

        # Update suggestions
        suggestions = performance.get("suggestions", [])
        if suggestions:
            self.suggestions_label.config(text="💡 Suggestions:\n• " + "\n• ".join(suggestions))
        else:
            self.suggestions_label.config(text="")

    def _update_quality(self):
        """Update quality tab"""
        quality = self.analysis_results.get("quality", {})

        grade = quality.get("grade", "-")
        score = quality.get("score", 0)

        # Grade colors
        grade_colors = {"A": "success", "B": "info", "C": "warning", "D": "warning", "F": "danger"}

        self.quality_grade_label.config(text=grade, bootstyle=grade_colors.get(grade, "secondary"))
        self.quality_score_label.config(text=f"{score}/100")

        # Clear and update details
        for widget in self.quality_details_frame.winfo_children():
            widget.destroy()

        # Add metrics
        metrics = quality.get("metrics", {})
        for name, value in metrics.items():
            row = ttk.Frame(self.quality_details_frame)
            row.pack(fill="x", pady=2)

            ttk.Label(row, text=name.replace("_", " ").title() + ":").pack(side="left")

            if isinstance(value, float):
                value_text = f"{value:.2f}"
            else:
                value_text = str(value)
            ttk.Label(row, text=value_text, font=("Segoe UI", 10, "bold")).pack(side="right")

        # Add code smells
        smells = quality.get("code_smells", [])
        if smells:
            ttk.Separator(self.quality_details_frame).pack(fill="x", pady=10)
            ttk.Label(self.quality_details_frame, text="Code Smells:", font=("Segoe UI", 10, "bold")).pack(anchor="w")

            for smell in smells:
                smell_label = ttk.Label(self.quality_details_frame, text=f"  • {smell['message']}", wraplength=350)
                smell_label.pack(anchor="w")

    def _update_all_issues(self):
        """Update all issues tab"""
        all_issues = []

        # Collect all issues
        if "security" in self.analysis_results:
            all_issues.extend(self.analysis_results["security"].get("issues", []))

        if "performance" in self.analysis_results:
            all_issues.extend(self.analysis_results["performance"].get("issues", []))

        if "quality" in self.analysis_results:
            for smell in self.analysis_results["quality"].get("code_smells", []):
                all_issues.append(
                    {
                        "line": smell.get("line", 0),
                        "category": "quality",
                        "message": smell.get("message", ""),
                        "severity": smell.get("severity", "low"),
                    }
                )

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 5))

        self.all_issues_data = all_issues
        self._filter_issues()

    def _filter_issues(self):
        """Filter issues based on selected filter"""
        filter_value = self.issue_filter.get()

        if filter_value == "all":
            filtered = self.all_issues_data
        else:
            filtered = [i for i in self.all_issues_data if i.get("severity") == filter_value]

        self.all_issues_view.set_issues(filtered)

    def _show_analysis_error(self, error: str):
        """Show analysis error"""
        messagebox.showerror("Analysis Error", f"An error occurred during analysis:\n{error}")
        self.set_status("Analysis failed")

    def run_analysis(self, analysis_type: str):
        """Run a specific type of analysis"""
        if not self.current_code:
            messagebox.showinfo("Info", "Please load a file or paste code first.")
            return

        self.set_status(f"Running {analysis_type} analysis...")

        try:
            if analysis_type == "basic":
                analyzer = get_analyzer(self.current_code, self.current_language)
                self.analysis_results["basic"] = {
                    "stats": analyzer.get_basic_stats(),
                    "line_distribution": analyzer.get_line_length_distribution(),
                    "indentation": analyzer.get_indentation_analysis(),
                }
                self._update_overview()
                self.results_notebook.select(0)

            elif analysis_type == "security":
                security = SecurityAnalyzer(self.current_code, self.current_language)
                self.analysis_results["security"] = security.analyze()
                self._update_security()
                self.results_notebook.select(2)

            elif analysis_type == "performance":
                performance = PerformanceAnalyzer(self.current_code, self.current_language)
                self.analysis_results["performance"] = performance.analyze()
                self._update_performance()
                self.results_notebook.select(3)

            elif analysis_type == "quality":
                quality = QualityAnalyzer(self.current_code, self.current_language)
                self.analysis_results["quality"] = quality.analyze()
                self._update_quality()
                self.results_notebook.select(4)

            self.set_status(f"{analysis_type.title()} analysis complete")

        except Exception as e:
            self._show_analysis_error(str(e))

    def go_to_line(self, line_number: int):
        """Navigate to a specific line in the code"""
        try:
            # Clear any existing highlighting
            self.code_text.tag_remove("highlight", "1.0", "end")

            # Configure highlight tag
            self.code_text.tag_configure("highlight", background="#44475a")

            # Highlight the line
            start = f"{line_number}.0"
            end = f"{line_number}.end"
            self.code_text.tag_add("highlight", start, end)

            # Scroll to the line
            self.code_text.see(start)

            # Set cursor
            self.code_text.mark_set("insert", start)

        except Exception:
            pass

    def show_go_to_line_dialog(self):
        """Show dialog to go to a specific line"""
        dialog = ttk.Toplevel(self.root)
        dialog.title("Go to Line")
        dialog.geometry("250x100")
        dialog.transient(self.root)

        ttk.Label(dialog, text="Line number:").pack(pady=10)

        entry = ttk.Entry(dialog)
        entry.pack(pady=5)
        entry.focus()

        def go():
            try:
                line = int(entry.get())
                self.go_to_line(line)
                dialog.destroy()
            except ValueError:
                pass

        entry.bind("<Return>", lambda e: go())
        ttk.Button(dialog, text="Go", command=go).pack(pady=10)

    def search_in_code(self, event=None):
        """Search for text in code"""
        query = self.search_var.get()
        if not query:
            return

        # Clear previous highlights
        self.code_text.tag_remove("search", "1.0", "end")
        self.code_text.tag_configure("search", background="#f1fa8c", foreground="#282a36")

        # Find all matches
        start = "1.0"
        count = 0

        while True:
            pos = self.code_text.search(query, start, stopindex="end", nocase=True)
            if not pos:
                break

            end = f"{pos}+{len(query)}c"
            self.code_text.tag_add("search", pos, end)
            start = end
            count += 1

        if count > 0:
            # Go to first match
            first = self.code_text.tag_ranges("search")
            if first:
                self.code_text.see(first[0])
            self.set_status(f"Found {count} matches")
        else:
            self.set_status("No matches found")

    def _clear_search(self):
        """Clear search highlighting"""
        self.code_text.tag_remove("search", "1.0", "end")
        self.search_var.set("")

    def find_todos(self):
        """Find and display all TODOs"""
        if not self.current_code:
            return

        todos = find_todos(self.current_code)

        if not todos:
            messagebox.showinfo("TODOs", "No TODO, FIXME, or HACK comments found.")
            return

        # Show in a dialog
        dialog = ttk.Toplevel(self.root)
        dialog.title(f"Found {len(todos)} TODO Comments")
        dialog.geometry("500x400")

        tree = ttk.Treeview(dialog, columns=("type", "line", "message"), show="headings")
        tree.heading("type", text="Type")
        tree.heading("line", text="Line")
        tree.heading("message", text="Message")

        tree.column("type", width=80)
        tree.column("line", width=60)
        tree.column("message", width=350)

        for todo in todos:
            tree.insert("", "end", values=(todo["type"], todo["line"], todo["message"]))

        tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Double-click to go to line
        def on_double_click(event):
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                line = item["values"][1]
                self.go_to_line(line)

        tree.bind("<Double-1>", on_double_click)

    def find_duplicates(self):
        """Find and display duplicate code"""
        if not self.current_code:
            return

        analyzer = BasicAnalyzer(self.current_code)
        duplicates = analyzer.find_duplicates()

        if not duplicates:
            messagebox.showinfo("Duplicates", "No significant duplicate lines found.")
            return

        # Show in a dialog
        dialog = ttk.Toplevel(self.root)
        dialog.title(f"Found {len(duplicates)} Duplicate Patterns")
        dialog.geometry("600x400")

        tree = ttk.Treeview(dialog, columns=("occurrences", "lines", "content"), show="headings")
        tree.heading("occurrences", text="Count")
        tree.heading("lines", text="Lines")
        tree.heading("content", text="Content")

        tree.column("occurrences", width=60)
        tree.column("lines", width=100)
        tree.column("content", width=420)

        for dup in duplicates[:20]:  # Show top 20
            lines_str = ", ".join(map(str, dup["lines"][:5]))
            if len(dup["lines"]) > 5:
                lines_str += "..."
            tree.insert("", "end", values=(dup["occurrences"], lines_str, dup["content"]))

        tree.pack(fill="both", expand=True, padx=10, pady=10)

    def export_report(self):
        """Export analysis report"""
        if not self.analysis_results:
            messagebox.showinfo("Info", "Run analysis first before exporting.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Report",
            defaultextension=".json",
            filetypes=[("JSON Report", "*.json"), ("Text Report", "*.txt"), ("HTML Report", "*.html")],
        )

        if not file_path:
            return

        try:
            if file_path.endswith(".json"):
                self._export_json(file_path)
            elif file_path.endswith(".txt"):
                self._export_text(file_path)
            elif file_path.endswith(".html"):
                self._export_html(file_path)

            messagebox.showinfo("Export Complete", f"Report saved to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Could not export report:\n{str(e)}")

    def _export_json(self, file_path: str):
        """Export as JSON"""
        report = {
            "file": self.current_file,
            "language": self.current_language,
            "timestamp": datetime.now().isoformat(),
            "results": self.analysis_results,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

    def _export_text(self, file_path: str):
        """Export as text"""
        lines = [
            "=" * 60,
            "CODE ANALYTICS REPORT",
            "=" * 60,
            f"File: {self.current_file or 'Pasted Code'}",
            f"Language: {self.current_language}",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        # Basic stats
        if "basic" in self.analysis_results:
            stats = self.analysis_results["basic"].get("stats", {})
            lines.extend(
                [
                    "BASIC STATISTICS",
                    "-" * 40,
                    f"Total Lines: {stats.get('total_lines', 0)}",
                    f"Total Characters: {stats.get('total_characters', 0)}",
                    f"Average Line Length: {stats.get('average_line_length', 0):.1f}",
                    "",
                ]
            )

        # Security
        if "security" in self.analysis_results:
            security = self.analysis_results["security"]
            lines.extend(
                [
                    "SECURITY ANALYSIS",
                    "-" * 40,
                    f"Total Issues: {security.get('total_issues', 0)}",
                    f"Risk Score: {security.get('risk_score', 0)}/100",
                    "",
                ]
            )

        # Quality
        if "quality" in self.analysis_results:
            quality = self.analysis_results["quality"]
            lines.extend(
                [
                    "CODE QUALITY",
                    "-" * 40,
                    f"Grade: {quality.get('grade', '-')}",
                    f"Score: {quality.get('score', 0)}/100",
                    "",
                ]
            )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _export_html(self, file_path: str):
        """Export as HTML"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Code Analytics Report</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 40px; background: #1a1a2e; color: #f8f8f2; }}
        h1 {{ color: #50fa7b; }}
        h2 {{ color: #8be9fd; border-bottom: 1px solid #44475a; padding-bottom: 10px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 20px; background: #282a36; border-radius: 8px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #bd93f9; }}
        .metric-label {{ font-size: 12px; color: #6272a4; }}
        .grade {{ font-size: 72px; font-weight: bold; }}
        .grade-A {{ color: #50fa7b; }}
        .grade-B {{ color: #8be9fd; }}
        .grade-C {{ color: #f1fa8c; }}
        .grade-D {{ color: #ffb86c; }}
        .grade-F {{ color: #ff5555; }}
    </style>
</head>
<body>
    <h1>📊 Code Analytics Report</h1>
    <p>File: {self.current_file or "Pasted Code"}</p>
    <p>Language: {self.current_language}</p>
    <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
"""

        # Add metrics
        if "basic" in self.analysis_results:
            stats = self.analysis_results["basic"].get("stats", {})
            html += """
    <h2>📈 Basic Statistics</h2>
    <div class="metrics">
"""
            for name, value in stats.items():
                html += f"""
        <div class="metric">
            <div class="metric-value">{value if isinstance(value, int) else f"{value:.1f}"}</div>
            <div class="metric-label">{name.replace("_", " ").title()}</div>
        </div>
"""
            html += "    </div>\n"

        # Add quality grade
        if "quality" in self.analysis_results:
            quality = self.analysis_results["quality"]
            grade = quality.get("grade", "-")
            score = quality.get("score", 0)
            html += f"""
    <h2>📊 Code Quality</h2>
    <div class="grade grade-{grade}">{grade}</div>
    <p>Score: {score}/100</p>
"""

        html += """
</body>
</html>
"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)

    def format_code(self):
        """Format the current code"""
        if not self.current_code:
            messagebox.showinfo("Info", "Please load a file or paste code first.")
            return
        
        self.set_status("Formatting code...")
        
        try:
            formatter = get_formatter()
            
            # Determine language
            language = self._get_formatter_language()
            
            # Format the code
            formatted_code, success, message = formatter.format_code(
                self.current_code, 
                language, 
                self.current_file
            )
            
            if success:
                # Update the code
                self.current_code = formatted_code
                self._display_code(formatted_code)
                self.set_status(f"✓ {message}")
                
                # Re-run analysis if auto-analyze is enabled
                if self.settings.get('auto_analyze'):
                    self.run_full_analysis()
            else:
                self.set_status(f"Format failed: {message}")
                messagebox.showwarning("Format Warning", message)
        
        except Exception as e:
            self.set_status("Format failed")
            messagebox.showerror("Format Error", f"Could not format code:\n{str(e)}")
    
    def _get_formatter_language(self) -> str:
        """Get the language name for the formatter"""
        lang_map = {
            'Python': 'python',
            'JavaScript': 'javascript',
            'JavaScript (React)': 'javascript',
            'TypeScript': 'typescript',
            'TypeScript (React)': 'typescript',
            'HTML': 'html',
            'CSS': 'css',
            'SCSS': 'scss',
            'SASS': 'scss',
            'JSON': 'json',
            'XML': 'xml',
            'YAML': 'yaml',
            'SQL': 'sql',
            'Java': 'java',
            'C#': 'csharp',
            'C++': 'cpp',
            'C': 'cpp',
            'C/C++ Header': 'cpp',
            'Go': 'go',
            'Rust': 'rust',
            'Ruby': 'ruby',
            'PHP': 'php',
            'Lua': 'lua',
            'Kotlin': 'kotlin',
            'Swift': 'swift',
            'Dart': 'dart',
            'Shell': 'shell',
            'Bash': 'shell',
            'Vue': 'vue',
            'Svelte': 'svelte',
            'Markdown': 'markdown'
        }
        return lang_map.get(self.current_language, 'python')
    
    def show_format_settings(self):
        """Show formatting settings dialog"""
        dialog = ttk.Toplevel(self.root)
        dialog.title("Format Settings")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        
        formatter = get_formatter()
        
        # Settings Frame
        settings_frame = ttk.LabelFrame(dialog, text="Formatting Options", padding=10)
        settings_frame.pack(fill='x', padx=10, pady=10)
        
        # Indent size
        ttk.Label(settings_frame, text="Indent Size:").grid(row=0, column=0, sticky='w', pady=5)
        indent_var = tk.IntVar(value=formatter.settings['indent_size'])
        ttk.Spinbox(settings_frame, from_=2, to=8, textvariable=indent_var, width=10).grid(row=0, column=1, sticky='w', pady=5)
        
        # Use tabs
        tabs_var = tk.BooleanVar(value=formatter.settings['use_tabs'])
        ttk.Checkbutton(settings_frame, text="Use Tabs instead of Spaces", variable=tabs_var).grid(row=1, column=0, columnspan=2, sticky='w', pady=5)
        
        # Max line length
        ttk.Label(settings_frame, text="Max Line Length:").grid(row=2, column=0, sticky='w', pady=5)
        line_length_var = tk.IntVar(value=formatter.settings['max_line_length'])
        ttk.Spinbox(settings_frame, from_=40, to=200, textvariable=line_length_var, width=10).grid(row=2, column=1, sticky='w', pady=5)
        
        # End with newline
        newline_var = tk.BooleanVar(value=formatter.settings['end_with_newline'])
        ttk.Checkbutton(settings_frame, text="End file with newline", variable=newline_var).grid(row=3, column=0, columnspan=2, sticky='w', pady=5)
        
        # Trim trailing whitespace
        trim_var = tk.BooleanVar(value=formatter.settings['trim_trailing_whitespace'])
        ttk.Checkbutton(settings_frame, text="Trim trailing whitespace", variable=trim_var).grid(row=4, column=0, columnspan=2, sticky='w', pady=5)
        
        # Available formatters info
        info_frame = ttk.LabelFrame(dialog, text="Available Formatters", padding=10)
        info_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create scrollable text for formatter info
        info_text = tk.Text(info_frame, height=12, font=('Consolas', 9), wrap='word')
        info_scrollbar = ttk.Scrollbar(info_frame, orient='vertical', command=info_text.yview)
        info_text.configure(yscrollcommand=info_scrollbar.set)
        
        info_text.pack(side='left', fill='both', expand=True)
        info_scrollbar.pack(side='right', fill='y')
        
        # Populate formatter info
        available = formatter.get_available_formatters()
        info_lines = []
        for lang, tools in sorted(available.items()):
            if tools:
                info_lines.append(f"✓ {lang.title()}: {', '.join(tools)}")
            else:
                info_lines.append(f"✗ {lang.title()}: No external formatter")
        
        info_text.insert('1.0', '\n'.join(info_lines))
        info_text.config(state='disabled')
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        def save_format_settings():
            formatter.settings['indent_size'] = indent_var.get()
            formatter.settings['use_tabs'] = tabs_var.get()
            formatter.settings['max_line_length'] = line_length_var.get()
            formatter.settings['end_with_newline'] = newline_var.get()
            formatter.settings['trim_trailing_whitespace'] = trim_var.get()
            dialog.destroy()
        
        ttk.Button(button_frame, text="Save", command=save_format_settings, bootstyle="success").pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, bootstyle="secondary").pack(side='right', padx=5)
        
        # Install info
        install_label = ttk.Label(
            dialog, 
            text="💡 Install external formatters for better results: black, prettier, clang-format, etc.",
            font=('Segoe UI', 8),
            foreground='gray'
        )
        install_label.pack(pady=(0, 10))

    def compare_files(self):
        """Compare two files"""
        messagebox.showinfo("Coming Soon", "File comparison feature coming soon!")

    def batch_analyze(self, folder_path: str = None):
        """Analyze multiple files in a folder"""
        if not folder_path:
            folder_path = filedialog.askdirectory(title="Select Folder for Batch Analysis")

        if not folder_path:
            return

        # Find all code files
        extensions = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".cs", ".rb", ".go"]
        files = []

        for ext in extensions:
            files.extend(Path(folder_path).rglob(f"*{ext}"))

        if not files:
            messagebox.showinfo("Info", "No code files found in the selected folder.")
            return

        # Show batch analysis dialog
        dialog = ttk.Toplevel(self.root)
        dialog.title(f"Batch Analysis - {len(files)} files")
        dialog.geometry("700x500")

        progress_var = tk.DoubleVar()
        progress = ttk.Progressbar(dialog, variable=progress_var, maximum=len(files))
        progress.pack(fill="x", padx=20, pady=20)

        status_label = ttk.Label(dialog, text="Analyzing...")
        status_label.pack()

        # Results tree
        tree = ttk.Treeview(dialog, columns=("file", "language", "lines", "issues", "grade"), show="headings")
        tree.heading("file", text="File")
        tree.heading("language", text="Language")
        tree.heading("lines", text="Lines")
        tree.heading("issues", text="Issues")
        tree.heading("grade", text="Grade")

        tree.pack(fill="both", expand=True, padx=20, pady=10)

        def analyze_batch():
            for i, file_path in enumerate(files):
                try:
                    content, _ = read_file_safe(str(file_path))
                    language = detect_language(str(file_path))

                    # Quick analysis
                    analyzer = get_analyzer(content, language)
                    stats = analyzer.get_basic_stats()

                    quality = QualityAnalyzer(content, language)
                    quality_result = quality.analyze()

                    security = SecurityAnalyzer(content, language)
                    security_result = security.analyze()

                    total_issues = security_result.get("total_issues", 0)
                    grade = quality_result.get("grade", "-")

                    dialog.after(
                        0,
                        lambda f=file_path, l=language, s=stats, i=total_issues, g=grade: tree.insert(
                            "", "end", values=(f.name, l, s.get("total_lines", 0), i, g)
                        ),
                    )

                except Exception as e:
                    dialog.after(0, lambda f=file_path: tree.insert("", "end", values=(f.name, "Error", "-", "-", "-")))

                progress_var.set(i + 1)
                dialog.after(0, lambda n=i + 1: status_label.config(text=f"Analyzed {n}/{len(files)} files"))

            dialog.after(0, lambda: status_label.config(text=f"Complete! Analyzed {len(files)} files"))

        thread = threading.Thread(target=analyze_batch)
        thread.start()

    def show_settings(self):
        """Show settings dialog"""
        dialog = ttk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.geometry("400x350")
        dialog.transient(self.root)

        notebook = ttk.Notebook(dialog)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Editor settings
        editor_frame = ttk.Frame(notebook, padding=10)
        notebook.add(editor_frame, text="Editor")

        ttk.Label(editor_frame, text="Font Family:").grid(row=0, column=0, sticky="w", pady=5)
        font_var = tk.StringVar(value=self.settings["font_family"])
        font_combo = ttk.Combobox(
            editor_frame, textvariable=font_var, values=["Consolas", "Courier New", "Monaco", "Source Code Pro"]
        )
        font_combo.grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(editor_frame, text="Font Size:").grid(row=1, column=0, sticky="w", pady=5)
        size_var = tk.IntVar(value=self.settings["font_size"])
        size_spin = ttk.Spinbox(editor_frame, from_=8, to=24, textvariable=size_var)
        size_spin.grid(row=1, column=1, sticky="ew", pady=5)

        auto_analyze_var = tk.BooleanVar(value=self.settings["auto_analyze"])
        ttk.Checkbutton(editor_frame, text="Auto-analyze on file load", variable=auto_analyze_var).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=5
        )

        line_numbers_var = tk.BooleanVar(value=self.settings["show_line_numbers"])
        ttk.Checkbutton(editor_frame, text="Show line numbers", variable=line_numbers_var).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=5
        )

        syntax_var = tk.BooleanVar(value=self.settings["highlight_syntax"])
        ttk.Checkbutton(editor_frame, text="Enable syntax highlighting", variable=syntax_var).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=5
        )

        # Save button
        def save_settings():
            self.settings["font_family"] = font_var.get()
            self.settings["font_size"] = size_var.get()
            self.settings["auto_analyze"] = auto_analyze_var.get()
            self.settings["show_line_numbers"] = line_numbers_var.get()
            self.settings["highlight_syntax"] = syntax_var.get()
            self._save_settings()

            # Apply changes
            self.code_text.config(font=(self.settings["font_family"], self.settings["font_size"]))
            self._update_line_numbers()

            dialog.destroy()

        ttk.Button(dialog, text="Save", command=save_settings, bootstyle="success").pack(pady=10)

    def change_theme(self, theme: str):
        """Change application theme"""
        try:
            self.root.style.theme_use(theme)
            self.settings["theme"] = theme
            self._save_settings()
        except Exception as e:
            print(f"Could not change theme: {e}")

    def toggle_line_numbers(self):
        """Toggle line numbers visibility"""
        self.settings["show_line_numbers"] = not self.settings["show_line_numbers"]
        if self.settings["show_line_numbers"]:
            self.line_numbers.pack(side="left", fill="y", before=self.code_text.master)
        else:
            self.line_numbers.pack_forget()
        self._update_line_numbers()

    def toggle_syntax_highlighting(self):
        """Toggle syntax highlighting"""
        self.settings["highlight_syntax"] = not self.settings["highlight_syntax"]
        if self.current_code:
            self._display_code(self.current_code)

    def show_docs(self):
        """Show documentation"""
        messagebox.showinfo(
            "Documentation",
            "Code Analytics Tool v" + self.VERSION + "\n\n"
            "Features:\n"
            "• Load and analyze code files\n"
            "• Security vulnerability scanning\n"
            "• Performance issue detection\n"
            "• Code quality metrics\n"
            "• Code structure visualization\n"
            "• Export reports (JSON, TXT, HTML)\n\n"
            "Supported languages:\n"
            "Python, JavaScript, TypeScript, Java, C/C++, C#, Go, Ruby, and more.",
        )

    def show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts = """
Keyboard Shortcuts:

Ctrl+O      Open file
Ctrl+V      Paste code
F5          Run full analysis
Ctrl+F      Search in code
Ctrl+G      Go to line
Escape      Clear search

File Navigation:
Double-click on structure items to go to line
Click on issues to highlight the relevant line
"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)

    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About Code Analytics",
            f"Code Analytics Tool\n"
            f"Version {self.VERSION}\n\n"
            "A comprehensive code analysis tool for developers.\n\n"
            "Features:\n"
            "• Multi-language support\n"
            "• Security scanning\n"
            "• Performance analysis\n"
            "• Code quality metrics\n"
            "• Syntax highlighting\n\n"
            "Built with Python, tkinter, and ttkbootstrap.",
        )

    def run(self):
        """Start the application"""
        self.root.mainloop()


def main():
    """Application entry point"""
    app = CodeAnalyticsApp()
    app.run()


if __name__ == "__main__":
    main()

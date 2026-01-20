"""
Code Analytics - Result Views
Display components for analysis results
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Any, Callable, Optional


class AnalysisResultView(ttk.Frame):
    """Base class for analysis result views"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.setup_ui()

    def setup_ui(self):
        """Override in subclasses"""
        pass

    def clear(self):
        """Clear all content"""
        for widget in self.winfo_children():
            widget.destroy()


class TreeResultView(AnalysisResultView):
    """Treeview-based result display"""

    def __init__(self, parent, columns: List[str], on_select: Optional[Callable] = None, **kwargs):
        self.columns = columns
        self.on_select = on_select
        super().__init__(parent, **kwargs)

    def setup_ui(self):
        # Create treeview with scrollbar
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=self.columns, show="headings", height=10)

        # Setup columns
        for col in self.columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100, minwidth=50)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Bind selection
        if self.on_select:
            self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _on_select(self, event):
        """Handle item selection"""
        selection = self.tree.selection()
        if selection and self.on_select:
            item = self.tree.item(selection[0])
            self.on_select(item["values"])

    def add_item(self, values: tuple, tags: tuple = ()):
        """Add an item to the tree"""
        self.tree.insert("", "end", values=values, tags=tags)

    def clear(self):
        """Clear all items"""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def set_data(self, data: List[Dict[str, Any]]):
        """Set data from a list of dictionaries"""
        self.clear()
        for item in data:
            values = tuple(item.get(col, "") for col in self.columns)
            self.add_item(values)


class MetricsView(AnalysisResultView):
    """Display metrics in a card-like layout"""

    def __init__(self, parent, **kwargs):
        self.metric_labels = {}
        self.metrics_frame = None
        super().__init__(parent, **kwargs)

    def setup_ui(self):
        self.metrics_frame = ttk.Frame(self)
        self.metrics_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def set_metrics(self, metrics: Dict[str, Any]):
        """Display metrics"""
        # Clear existing and recreate frame
        if self.metrics_frame:
            self.metrics_frame.destroy()
        self.metrics_frame = ttk.Frame(self)
        self.metrics_frame.pack(fill="both", expand=True, padx=5, pady=5)

        row = 0
        col = 0
        max_cols = 3

        for name, value in metrics.items():
            card = self._create_metric_card(self.metrics_frame, name, value)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # Configure grid weights
        for i in range(max_cols):
            self.metrics_frame.grid_columnconfigure(i, weight=1)

    def _create_metric_card(self, parent, name: str, value: Any) -> ttk.Frame:
        """Create a metric display card"""
        card = ttk.Frame(parent, relief="solid", borderwidth=1)
        card.configure(padding=10)

        # Name label
        name_label = ttk.Label(card, text=name.replace("_", " ").title(), font=("Segoe UI", 9))
        name_label.pack(anchor="w")

        # Value label
        if isinstance(value, float):
            value_text = f"{value:.2f}"
        else:
            value_text = str(value)

        value_label = ttk.Label(card, text=value_text, font=("Segoe UI", 16, "bold"))
        value_label.pack(anchor="w", pady=(5, 0))

        return card


class IssuesListView(AnalysisResultView):
    """Display issues with severity indicators"""

    SEVERITY_COLORS = {
        "critical": "#dc3545",
        "high": "#fd7e14",
        "medium": "#ffc107",
        "low": "#28a745",
        "info": "#17a2b8",
    }

    SEVERITY_ICONS = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "🔵"}

    def __init__(self, parent, on_click: Optional[Callable] = None, **kwargs):
        self.on_click = on_click
        self.issue_frames = []
        super().__init__(parent, **kwargs)

    def setup_ui(self):
        # Scrollable frame
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def set_issues(self, issues: List[Dict[str, Any]]):
        """Display issues"""
        # Clear existing
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.issue_frames.clear()

        if not issues:
            no_issues = ttk.Label(self.scrollable_frame, text="✅ No issues found", font=("Segoe UI", 11))
            no_issues.pack(pady=20)
            return

        for issue in issues:
            frame = self._create_issue_frame(issue)
            frame.pack(fill="x", padx=5, pady=2)
            self.issue_frames.append(frame)

    def _create_issue_frame(self, issue: Dict[str, Any]) -> ttk.Frame:
        """Create an issue display frame"""
        frame = ttk.Frame(self.scrollable_frame, relief="solid", borderwidth=1)
        frame.configure(padding=8)

        severity = issue.get("severity", "info")
        icon = self.SEVERITY_ICONS.get(severity, "⚪")

        # Header row
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill="x")

        # Severity icon and line number
        line = issue.get("line", 0)
        header_text = f"{icon} Line {line}" if line else icon

        header_label = ttk.Label(header_frame, text=header_text, font=("Segoe UI", 9, "bold"))
        header_label.pack(side="left")

        # Category/type badge
        category = issue.get("category", issue.get("type", ""))
        if category:
            category_label = ttk.Label(header_frame, text=category.replace("_", " ").upper(), font=("Segoe UI", 8))
            category_label.pack(side="right")

        # Message
        message = issue.get("message", "")
        message_label = ttk.Label(frame, text=message, font=("Segoe UI", 10), wraplength=400)
        message_label.pack(fill="x", pady=(5, 0), anchor="w")

        # Code preview
        code = issue.get("code", "")
        if code:
            code_label = ttk.Label(frame, text=f"  {code}", font=("Consolas", 9), foreground="#6c757d")
            code_label.pack(fill="x", anchor="w")

        # Bind click event
        if self.on_click and line:
            frame.bind("<Button-1>", lambda e, l=line: self.on_click(l))
            for child in frame.winfo_children():
                child.bind("<Button-1>", lambda e, l=line: self.on_click(l))

        return frame


class SummaryView(AnalysisResultView):
    """Display summary with score and grade"""

    def setup_ui(self):
        self.summary_frame = ttk.Frame(self)
        self.summary_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def set_summary(self, score: int, grade: str, details: Dict[str, Any]):
        """Display summary"""
        # Clear existing
        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        # Grade display
        grade_colors = {"A": "#28a745", "B": "#20c997", "C": "#ffc107", "D": "#fd7e14", "F": "#dc3545"}

        grade_frame = ttk.Frame(self.summary_frame)
        grade_frame.pack(pady=10)

        grade_label = ttk.Label(
            grade_frame, text=grade, font=("Segoe UI", 48, "bold"), foreground=grade_colors.get(grade, "#6c757d")
        )
        grade_label.pack()

        score_label = ttk.Label(grade_frame, text=f"{score}/100", font=("Segoe UI", 16))
        score_label.pack()

        # Details
        details_frame = ttk.Frame(self.summary_frame)
        details_frame.pack(fill="x", pady=10)

        for name, value in details.items():
            row = ttk.Frame(details_frame)
            row.pack(fill="x", pady=2)

            name_label = ttk.Label(row, text=name.replace("_", " ").title() + ":", font=("Segoe UI", 10))
            name_label.pack(side="left")

            value_label = ttk.Label(row, text=str(value), font=("Segoe UI", 10, "bold"))
            value_label.pack(side="right")


class CodeStructureView(AnalysisResultView):
    """Display code structure as a tree"""

    def __init__(self, parent, on_select: Optional[Callable] = None, **kwargs):
        self.on_select = on_select
        super().__init__(parent, **kwargs)

    def setup_ui(self):
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, show="tree headings")
        self.tree.heading("#0", text="Structure")
        self.tree.column("#0", width=300)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        if self.on_select:
            self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _on_select(self, event):
        selection = self.tree.selection()
        if selection and self.on_select:
            item = self.tree.item(selection[0])
            # Extract line number from tags
            tags = item.get("tags", ())
            if tags:
                try:
                    line = int(tags[0])
                    self.on_select(line)
                except (ValueError, IndexError):
                    pass

    def set_structure(self, classes: List[Dict], functions: List[Dict], variables: List[Dict]):
        """Display code structure"""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add classes
        if classes:
            classes_node = self.tree.insert("", "end", text="📦 Classes", open=True)
            for cls in classes:
                cls_node = self.tree.insert(
                    classes_node, "end", text=f"🔷 {cls['name']} (line {cls['line']})", tags=(str(cls["line"]),)
                )
                # Add methods
                for method in cls.get("methods", []):
                    self.tree.insert(cls_node, "end", text=f"  ⚡ {method['name']}()", tags=(str(method["line"]),))

        # Add functions
        if functions:
            funcs_node = self.tree.insert("", "end", text="⚡ Functions", open=True)
            for func in functions:
                async_prefix = "async " if func.get("is_async") else ""
                self.tree.insert(
                    funcs_node,
                    "end",
                    text=f"  {async_prefix}{func['name']}() - line {func['line']}",
                    tags=(str(func["line"]),),
                )

        # Add variables
        if variables:
            vars_node = self.tree.insert("", "end", text="📝 Variables", open=False)
            for var in variables:
                type_hint = f": {var['type_hint']}" if var.get("type_hint") else ""
                self.tree.insert(vars_node, "end", text=f"  {var['name']}{type_hint}", tags=(str(var["line"]),))

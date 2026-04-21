"""
guides_widget.py
----------------
UI for the Engineering Guides module.
Provides a list of available Markdown (.md) guides on the left,
and renders the selected guide into HTML on the right.
"""

import os
import glob
import markdown
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QTextBrowser, QLabel, QSplitter, QFrame, QListWidgetItem
)
from PyQt6.QtCore import Qt, QSize, QUrl
from PyQt6.QtGui import QFont
import qtawesome as qta


def _sep() -> QFrame:
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine); f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


class GuidesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.guides_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content")
        self._ensure_content_dir()
        self._build_ui()
        self._load_guides()

    def _ensure_content_dir(self):
        if not os.path.exists(self.guides_dir):
            os.makedirs(self.guides_dir, exist_ok=True)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 32)
        main_layout.setSpacing(20)

        # Title
        tr = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(qta.icon("fa5s.chalkboard-teacher", color="#a371f7").pixmap(28, 28))
        tr.addWidget(ico); tr.addSpacing(10)
        tc = QVBoxLayout(); tc.setSpacing(2)
        h1 = QLabel("Engineering Guides")
        h1.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        h1.setObjectName("section_title")
        tc.addWidget(h1)
        sub = QLabel("Standard Operating Procedures & Industry Guidelines")
        sub.setObjectName("header_subtitle")
        tc.addWidget(sub)
        tr.addLayout(tc); tr.addStretch()
        main_layout.addLayout(tr)
        main_layout.addWidget(_sep())

        # Splitter layout (List left, Browser right)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Panel (Guide List)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        lst_lbl = QLabel("Available Guides")
        lst_lbl.setStyleSheet("font-weight: bold; color: #c9d1d9; font-size: 14px;")
        left_layout.addWidget(lst_lbl)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #0d1117; 
                border: 1px solid #30363d; 
                border-radius: 6px; 
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #21262d;
                color: #c9d1d9;
            }
            QListWidget::item:selected {
                background-color: #1f3a5f;
                border-radius: 4px;
                color: #e6edf3;
            }
        """)
        self.list_widget.itemSelectionChanged.connect(self._on_guide_selected)
        left_layout.addWidget(self.list_widget)
        
        # Right Panel (Markdown Viewer)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 20px;
                color: #e6edf3;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        right_layout.addWidget(self.text_browser)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1) # ~25% width
        splitter.setStretchFactor(1, 3) # ~75% width
        main_layout.addWidget(splitter, 1)

    def _load_guides(self):
        self.list_widget.clear()
        files = glob.glob(os.path.join(self.guides_dir, "*.md"))
        if not files:
            self.text_browser.setHtml(
                "<h3 style='color:#c9d1d9'>No guides found.</h3>"
                f"<p style='color:#8b949e'>Add .md files to <b>{self.guides_dir}</b></p>"
            )
            return

        for filepath in files:
            title = self._extract_title(filepath) or os.path.basename(filepath).replace('.md', '').replace('_', ' ').title()
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, filepath)
            
            # Use appropriate icon
            if "transformer" in filepath.lower():
                item.setIcon(qta.icon("fa5s.charging-station", color="#a371f7"))
            else:
                item.setIcon(qta.icon("fa5s.file-alt", color="#8b949e"))
                
            self.list_widget.addItem(item)
            
        # Select first item by default
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _extract_title(self, filepath: str) -> str:
        """Read the first H1 header from the markdown file to use as the title."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("# "):
                        return line[2:].strip()
        except Exception:
            pass
        return ""

    def _on_guide_selected(self):
        items = self.list_widget.selectedItems()
        if not items:
            return
        
        filepath = items[0].data(Qt.ItemDataRole.UserRole)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                md_content = f.read()

            # Convert markdown to HTML
            # Using basic extensions for tables and fenced code
            html = markdown.markdown(md_content, extensions=['tables', 'fenced_code', 'nl2br'])
            
            # Simple replacements for TeX-like symbols if present
            html = html.replace("$\\delta$", "&delta;")
            html = html.replace("$\\pm$", "&plusmn;")
            html = html.replace("$\\Omega$", "&Omega;")
            html = html.replace("$\\div$", "&divide;")
            html = html.replace("$\\text{HV}$", "HV")
            html = html.replace("$\\text{LV}$", "LV")
            
            # Wrap in custom CSS for better dark mode readability inside QTextBrowser
            styled_html = f"""
            <html>
            <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #e6edf3; font-size: 14px; line-height: 1.5; }}
                h1 {{ color: #58a6ff; font-size: 24px; border-bottom: 1px solid #30363d; padding-bottom: 8px; margin-top: 5px; }}
                h2 {{ color: #a371f7; font-size: 20px; margin-top: 24px; }}
                h3 {{ color: #7ee787; font-size: 16px; margin-top: 20px; }}
                p {{ margin-bottom: 14px; }}
                ul, ol {{ margin-bottom: 14px; margin-left: -15px; }}
                li {{ margin-bottom: 6px; }}
                code {{ background-color: #2e343b; padding: 2px 4px; border-radius: 4px; font-family: Consolas, monospace; color: #ff7b72; }}
                pre {{ background-color: #161b22; border: 1px solid #30363d; padding: 12px; border-radius: 6px; overflow-x: auto; }}
                pre code {{ background-color: transparent; color: #e6edf3; padding: 0; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #30363d; padding: 10px; text-align: left; }}
                th {{ background-color: #1f3a5f; color: #e6edf3; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #0d1117; }}
                blockquote {{ border-left: 4px solid #58a6ff; margin: 0; padding-left: 15px; color: #8b949e; background-color: #0d1117; padding: 10px; border-radius: 0 4px 4px 0; }}
                .highlight {{ background-color: #2ea043; color: white; padding: 2px 5px; border-radius: 3px; font-weight: bold; font-size: 11px; }}
                .danger {{ background-color: #f85149; color: white; padding: 2px 5px; border-radius: 3px; font-weight: bold; font-size: 11px; }}
                img {{ max-width: 100%; height: auto; border: 1px solid #30363d; border-radius: 4px; margin: 10px 0; }}
            </style>
            </head>
            <body>
            {html}
            </body>
            </html>
            """
            
            # Resolve image paths by setting search paths for the folder where the guide is.
            self.text_browser.setSearchPaths([os.path.dirname(filepath)])
            self.text_browser.setHtml(styled_html)
            
        except Exception as e:
            self.text_browser.setHtml(f"<h3 style='color:#f85149'>Error loading guide</h3><p>{e}</p>")

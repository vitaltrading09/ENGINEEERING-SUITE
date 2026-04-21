"""
library_widget.py
-----------------
Datasheet Library — a full document management panel available as a
top-level sidebar module in the Engineering Calculator Suite.

Features:
  • Folder tree (left) mirrors the filesystem under LIBRARY_ROOT
  • File list (right) shows contents of the selected folder
  • Create / Rename / Delete folders
  • Upload any file (PDF, Excel, Word, etc.) into the selected folder
  • Double-click / Open button → launches file in system default viewer
  • Search bar filters files across all folders
  • Right-click context menus on both panels
"""

import os
import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem,
    QSplitter, QLineEdit, QInputDialog, QMessageBox, QFileDialog,
    QMenu, QSizePolicy, QFrame, QGroupBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon, QAction
import qtawesome as qta


# ─────────────────────────────────────────────────────────────────────────────
# Library root directory
# ─────────────────────────────────────────────────────────────────────────────

def get_library_root() -> Path:
    """Return (and create if needed) the datasheet library root directory."""
    root = Path(__file__).parent.parent / "datasheet_library" / "files"
    root.mkdir(parents=True, exist_ok=True)
    return root


# ─────────────────────────────────────────────────────────────────────────────
# Icon helper
# ─────────────────────────────────────────────────────────────────────────────

def _file_icon(filename: str) -> QIcon:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return qta.icon("fa5s.file-pdf",   color="#f85149")
    if ext in (".xlsx", ".xls", ".csv"):
        return qta.icon("fa5s.file-excel", color="#3fb950")
    if ext in (".docx", ".doc"):
        return qta.icon("fa5s.file-word",  color="#58a6ff")
    return qta.icon("fa5s.file",           color="#8b949e")


def _action_btn(text: str, icon_name: str, obj_name: str,
                icon_color: str = "#8b949e", h: int = 36) -> QPushButton:
    btn = QPushButton(text)
    btn.setObjectName(obj_name)
    btn.setIcon(qta.icon(icon_name, color=icon_color))
    btn.setIconSize(QSize(13, 13))
    btn.setFixedHeight(h)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def _sep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


# ─────────────────────────────────────────────────────────────────────────────
# Main widget
# ─────────────────────────────────────────────────────────────────────────────

class DatasheetLibraryWidget(QWidget):
    """
    Full-featured document library panel.
    Stores files under:  <project>/datasheet_library/files/<folder>/<file>
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._library_root = get_library_root()
        self._build_ui()
        self._refresh_tree()

    # ─────────────────────────────────────────────────────── UI Build ────────

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(32, 28, 32, 32)
        main.setSpacing(16)

        # Title row
        tr = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(qta.icon("fa5s.folder-open", color="#58a6ff").pixmap(28, 28))
        tr.addWidget(ico); tr.addSpacing(10)
        tc = QVBoxLayout(); tc.setSpacing(2)
        h1 = QLabel("Datasheet Library")
        h1.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        h1.setObjectName("section_title")
        tc.addWidget(h1)
        sub = QLabel("Organise and access cable datasheets, catalogues and reference documents")
        sub.setObjectName("header_subtitle")
        tc.addWidget(sub)
        tr.addLayout(tc); tr.addStretch()
        main.addLayout(tr)
        main.addWidget(_sep())

        # Action bar
        abar = QHBoxLayout(); abar.setSpacing(8)

        self.btn_new_folder = _action_btn("  New Folder",   "fa5s.folder-plus",  "secondary_btn")
        self.btn_upload     = _action_btn("  Upload Files", "fa5s.upload",        "primary_btn",  "white", 36)
        self.btn_open       = _action_btn("  Open",         "fa5s.external-link-alt", "secondary_btn")
        self.btn_delete     = _action_btn("  Delete",       "fa5s.trash-alt",     "danger_btn",   "#f85149")

        self.btn_new_folder.clicked.connect(self._create_folder)
        self.btn_upload.clicked.connect(self._upload_files)
        self.btn_open.clicked.connect(self._open_selected)
        self.btn_delete.clicked.connect(self._delete_selected)

        abar.addWidget(self.btn_new_folder)
        abar.addWidget(self.btn_upload)
        abar.addStretch()

        # Search bar
        search_lbl = QLabel("🔍")
        abar.addWidget(search_lbl)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search files…")
        self.search_edit.setFixedWidth(240)
        self.search_edit.textChanged.connect(self._filter_files)
        abar.addWidget(self.search_edit)

        abar.addSpacing(8)
        abar.addWidget(self.btn_open)
        abar.addWidget(self.btn_delete)
        main.addLayout(abar)

        # Splitter: folder tree (left) + file list (right)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)

        # ── Left: Folder tree ─────────────────────────────────────────────
        left_wid = QGroupBox("Folders")
        left_lay = QVBoxLayout(left_wid)
        left_lay.setContentsMargins(8, 12, 8, 8)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setAnimated(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._tree_context_menu)
        self.tree.currentItemChanged.connect(self._on_folder_selected)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                font-size: 13px;
            }
            QTreeWidget::item { padding: 6px 8px; }
            QTreeWidget::item:selected {
                background-color: #1f3a5f; color: #58a6ff;
            }
            QTreeWidget::item:hover { background-color: #161b22; }
            QTreeWidget::branch { background: transparent; }
        """)
        left_lay.addWidget(self.tree)
        splitter.addWidget(left_wid)

        # ── Right: File list ──────────────────────────────────────────────
        right_wid = QGroupBox("Files")
        right_lay = QVBoxLayout(right_wid)
        right_lay.setContentsMargins(8, 12, 8, 8)

        self.file_list = QListWidget()
        self.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self._file_context_menu)
        self.file_list.itemDoubleClicked.connect(self._open_item)
        self.file_list.setStyleSheet("""
            QListWidget {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                font-size: 13px;
            }
            QListWidget::item { padding: 8px 12px; border-bottom: 1px solid #21262d; }
            QListWidget::item:selected { background-color: #1f3a5f; color: #e6edf3; }
            QListWidget::item:hover    { background-color: #161b22; }
        """)
        right_lay.addWidget(self.file_list)

        # Status bar
        self.status_lbl = QLabel("Select a folder to view files. Double-click a file to open it.")
        self.status_lbl.setObjectName("header_subtitle")
        right_lay.addWidget(self.status_lbl)

        splitter.addWidget(right_wid)
        splitter.setSizes([260, 700])
        main.addWidget(splitter, 1)

    # ─────────────────────────────────────────────────── Tree Management ─────

    def _refresh_tree(self):
        """Rebuild the folder tree from the filesystem."""
        prev_selection = self._current_folder_path()
        self.tree.clear()

        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, "📚  Library Root")
        root_item.setData(0, Qt.ItemDataRole.UserRole, str(self._library_root))
        root_item.setFont(0, QFont("Segoe UI", 11, QFont.Weight.Bold))
        root_item.setForeground(0, QColor("#58a6ff"))

        self._populate_tree(root_item, self._library_root)
        self.tree.expandAll()

        # Restore selection
        if prev_selection:
            self._select_folder_path(prev_selection)
        else:
            self.tree.setCurrentItem(root_item)

    def _populate_tree(self, parent_item: QTreeWidgetItem, folder: Path):
        for sub in sorted(folder.iterdir()):
            if sub.is_dir():
                child = QTreeWidgetItem(parent_item)
                child.setText(0, f"📁  {sub.name}")
                child.setData(0, Qt.ItemDataRole.UserRole, str(sub))
                self._populate_tree(child, sub)

    def _current_folder_path(self) -> str | None:
        item = self.tree.currentItem()
        if item:
            return item.data(0, Qt.ItemDataRole.UserRole)
        return None

    def _select_folder_path(self, path: str):
        def _walk(item: QTreeWidgetItem):
            if item.data(0, Qt.ItemDataRole.UserRole) == path:
                self.tree.setCurrentItem(item)
                return True
            for i in range(item.childCount()):
                if _walk(item.child(i)):
                    return True
            return False
        for i in range(self.tree.topLevelItemCount()):
            _walk(self.tree.topLevelItem(i))

    def _on_folder_selected(self, current: QTreeWidgetItem, _prev):
        if current:
            self._load_files(Path(current.data(0, Qt.ItemDataRole.UserRole)))

    def _load_files(self, folder: Path):
        self.file_list.clear()
        if not folder.exists():
            return
        files = sorted([f for f in folder.iterdir() if f.is_file()],
                       key=lambda f: f.name.lower())
        search = self.search_edit.text().strip().lower()
        for f in files:
            if search and search not in f.name.lower():
                continue
            item = QListWidgetItem(_file_icon(f.name), f"  {f.name}")
            item.setData(Qt.ItemDataRole.UserRole, str(f))
            sz = f.stat().st_size
            if sz < 1024:        sz_str = f"{sz} B"
            elif sz < 1_048_576: sz_str = f"{sz/1024:.1f} KB"
            else:                sz_str = f"{sz/1_048_576:.1f} MB"
            item.setToolTip(f"{f.name}\n{sz_str}\n{str(f)}")
            self.file_list.addItem(item)
        count = self.file_list.count()
        self.status_lbl.setText(
            f"{count} file(s) in  {folder.name}"
            if count else f"No files in  {folder.name}  — upload some using the button above."
        )

    def _filter_files(self):
        folder_path = self._current_folder_path()
        if folder_path:
            self._load_files(Path(folder_path))

    # ─────────────────────────────────────────────────── Folder Actions ──────

    def _create_folder(self):
        parent_path = self._current_folder_path()
        if not parent_path:
            parent_path = str(self._library_root)
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if not ok or not name.strip():
            return
        name = name.strip().replace("/", "_").replace("\\", "_")
        new_path = Path(parent_path) / name
        if new_path.exists():
            QMessageBox.warning(self, "Exists", f"A folder named '{name}' already exists here.")
            return
        new_path.mkdir(parents=True)
        self._refresh_tree()
        self._select_folder_path(str(new_path))

    def _rename_folder(self):
        item = self.tree.currentItem()
        if not item:
            return
        old_path = Path(item.data(0, Qt.ItemDataRole.UserRole))
        if old_path == self._library_root:
            QMessageBox.information(self, "Cannot Rename", "The library root cannot be renamed.")
            return
        name, ok = QInputDialog.getText(self, "Rename Folder", "New name:", text=old_path.name)
        if not ok or not name.strip() or name.strip() == old_path.name:
            return
        new_path = old_path.parent / name.strip()
        old_path.rename(new_path)
        self._refresh_tree()

    def _delete_folder(self):
        item = self.tree.currentItem()
        if not item:
            return
        path = Path(item.data(0, Qt.ItemDataRole.UserRole))
        if path == self._library_root:
            QMessageBox.information(self, "Cannot Delete", "The library root cannot be deleted.")
            return
        count = sum(1 for _ in path.rglob("*") if _.is_file())
        msg = (f"Delete folder '{path.name}' and all {count} file(s) inside it?"
               if count else f"Delete empty folder '{path.name}'?")
        if QMessageBox.question(self, "Delete Folder", msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
               ) == QMessageBox.StandardButton.Yes:
            shutil.rmtree(path)
            self._refresh_tree()

    # ─────────────────────────────────────────────────── File Actions ────────

    def _upload_files(self):
        folder_path = self._current_folder_path()
        if not folder_path:
            QMessageBox.information(self, "Select Folder",
                "Please select a destination folder in the tree first.")
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Upload Files", str(os.path.expanduser("~")),
            "All Files (*);;PDF Documents (*.pdf);;Excel Files (*.xlsx *.xls);;CSV Files (*.csv)"
        )
        if not paths:
            return
        dest = Path(folder_path)
        copied, skipped = 0, 0
        for src in paths:
            src_path = Path(src)
            dst_path = dest / src_path.name
            if dst_path.exists():
                reply = QMessageBox.question(self, "File Exists",
                    f"'{src_path.name}' already exists in this folder. Replace it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    skipped += 1; continue
            shutil.copy2(src, dst_path)
            copied += 1
        msg = f"{copied} file(s) uploaded."
        if skipped: msg += f"  {skipped} skipped."
        self._load_files(dest)
        self.status_lbl.setText(msg)

    def _open_selected(self):
        item = self.file_list.currentItem()
        if item:
            self._open_item(item)
        else:
            QMessageBox.information(self, "No File Selected",
                "Select a file from the list, then click Open.")

    def _open_item(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                QMessageBox.critical(self, "Cannot Open", str(e))
        else:
            QMessageBox.warning(self, "File Not Found", f"File not found:\n{path}")

    def _rename_file(self):
        item = self.file_list.currentItem()
        if not item:
            return
        old_path = Path(item.data(Qt.ItemDataRole.UserRole))
        name, ok = QInputDialog.getText(self, "Rename File", "New filename:", text=old_path.name)
        if not ok or not name.strip() or name.strip() == old_path.name:
            return
        new_path = old_path.parent / name.strip()
        if new_path.exists():
            QMessageBox.warning(self, "Exists", f"A file named '{name}' already exists.")
            return
        old_path.rename(new_path)
        self._load_files(old_path.parent)

    def _delete_selected(self):
        items = self.file_list.selectedItems()
        if not items:
            QMessageBox.information(self, "No Selection", "Select file(s) to delete.")
            return
        names = "\n".join(Path(i.data(Qt.ItemDataRole.UserRole)).name for i in items)
        if QMessageBox.question(self, "Delete Files",
                f"Permanently delete {len(items)} file(s)?\n\n{names}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
               ) == QMessageBox.StandardButton.Yes:
            folder = None
            for item in items:
                p = Path(item.data(Qt.ItemDataRole.UserRole))
                folder = p.parent
                if p.exists():
                    p.unlink()
            if folder:
                self._load_files(folder)

    # ─────────────────────────────────────────────────── Context Menus ───────

    def _tree_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #161b22; color: #e6edf3;
                    border: 1px solid #30363d; border-radius: 6px; }
            QMenu::item { padding: 6px 20px; }
            QMenu::item:selected { background-color: #1f3a5f; }
        """)
        a_new    = menu.addAction(qta.icon("fa5s.folder-plus",  color="#58a6ff"), "  New Subfolder")
        a_upload = menu.addAction(qta.icon("fa5s.upload",       color="#3fb950"), "  Upload Files Here")
        menu.addSeparator()
        a_rename = menu.addAction(qta.icon("fa5s.edit",         color="#8b949e"), "  Rename Folder")
        a_delete = menu.addAction(qta.icon("fa5s.trash-alt",    color="#f85149"), "  Delete Folder")
        if item:
            path = Path(item.data(0, Qt.ItemDataRole.UserRole))
            a_rename.setEnabled(path != self._library_root)
            a_delete.setEnabled(path != self._library_root)
        action = menu.exec(self.tree.viewport().mapToGlobal(pos))
        if action == a_new:    self._create_folder()
        elif action == a_upload: self._upload_files()
        elif action == a_rename: self._rename_folder()
        elif action == a_delete: self._delete_folder()

    def _file_context_menu(self, pos):
        item = self.file_list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #161b22; color: #e6edf3;
                    border: 1px solid #30363d; border-radius: 6px; }
            QMenu::item { padding: 6px 20px; }
            QMenu::item:selected { background-color: #1f3a5f; }
        """)
        a_open   = menu.addAction(qta.icon("fa5s.external-link-alt", color="#58a6ff"), "  Open")
        a_rename = menu.addAction(qta.icon("fa5s.edit",               color="#8b949e"), "  Rename")
        menu.addSeparator()
        a_delete = menu.addAction(qta.icon("fa5s.trash-alt",          color="#f85149"), "  Delete")
        action = menu.exec(self.file_list.viewport().mapToGlobal(pos))
        if action == a_open:   self._open_item(item)
        elif action == a_rename: self._rename_file()
        elif action == a_delete: self._delete_selected()

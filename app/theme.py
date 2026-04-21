DARK_THEME = """
/* ============================================================
   ENGINEERING SUITE — DARK THEME
   ============================================================ */

QMainWindow, QWidget#central_widget {
    background-color: #0d1117;
    color: #e6edf3;
}

/* ---- Sidebar ---- */
QWidget#sidebar {
    background-color: #161b22;
    border-right: 1px solid #30363d;
}

QPushButton#nav_button {
    background-color: transparent;
    color: #8b949e;
    border: none;
    border-radius: 8px;
    padding: 10px 12px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}

QPushButton#nav_button:hover {
    background-color: #21262d;
    color: #e6edf3;
}

QPushButton#nav_button:checked {
    background-color: #1f3a5f;
    color: #58a6ff;
    border-left: 3px solid #58a6ff;
}

QPushButton#sidebar_toggle {
    background-color: transparent;
    border: none;
    color: #8b949e;
    padding: 8px;
    border-radius: 6px;
}

QPushButton#sidebar_toggle:hover {
    background-color: #21262d;
    color: #e6edf3;
}

/* ---- Header ---- */
QWidget#header {
    background-color: #161b22;
    border-bottom: 1px solid #30363d;
}

QLabel#header_title {
    color: #58a6ff;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

QLabel#header_subtitle {
    color: #8b949e;
    font-size: 12px;
}

QPushButton#theme_toggle_btn {
    background-color: #21262d;
    color: #8b949e;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
}

QPushButton#theme_toggle_btn:hover {
    background-color: #30363d;
    color: #e6edf3;
}

/* ---- Content Area ---- */
QWidget#content_area {
    background-color: #0d1117;
}

QScrollArea {
    background-color: #0d1117;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: #0d1117;
}

/* ---- Cards / Group Boxes ---- */
QGroupBox {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    margin-top: 16px;
    padding: 16px 14px 14px 14px;
    font-size: 13px;
    font-weight: 600;
    color: #8b949e;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #58a6ff;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* ---- Labels ---- */
QLabel {
    color: #c9d1d9;
    font-size: 13px;
}

QLabel#section_title {
    color: #e6edf3;
    font-size: 18px;
    font-weight: 700;
}

QLabel#result_value {
    color: #58a6ff;
    font-size: 22px;
    font-weight: 700;
}

QLabel#result_label {
    color: #8b949e;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

QLabel#pass_badge {
    background-color: #1a3a2a;
    color: #3fb950;
    border: 1px solid #3fb950;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 14px;
    font-weight: 700;
}

QLabel#fail_badge {
    background-color: #3a1a1a;
    color: #f85149;
    border: 1px solid #f85149;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 14px;
    font-weight: 700;
}

QLabel#neutral_badge {
    background-color: #21262d;
    color: #8b949e;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 14px;
    font-weight: 700;
}

/* ---- Input Fields ---- */
QLineEdit, QDoubleSpinBox, QSpinBox {
    background-color: #0d1117;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #1f3a5f;
}

QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {
    border: 1px solid #58a6ff;
    background-color: #0d1117;
}

QLineEdit:disabled, QDoubleSpinBox:disabled, QSpinBox:disabled {
    background-color: #161b22;
    color: #484f58;
    border-color: #21262d;
}

QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
QSpinBox::up-button, QSpinBox::down-button {
    background-color: #21262d;
    border: none;
    width: 18px;
    border-radius: 3px;
}

QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover,
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #30363d;
}

/* ---- Dropdowns ---- */
QComboBox {
    background-color: #0d1117;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    min-width: 140px;
}

QComboBox:focus {
    border: 1px solid #58a6ff;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid #30363d;
    border-radius: 0 6px 6px 0;
}

QComboBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #8b949e;
}

QComboBox QAbstractItemView {
    background-color: #161b22;
    color: #e6edf3;
    border: 1px solid #30363d;
    selection-background-color: #1f3a5f;
    selection-color: #58a6ff;
    padding: 4px;
}

/* ---- Radio Buttons ---- */
QRadioButton {
    color: #c9d1d9;
    font-size: 13px;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 9px;
    border: 2px solid #30363d;
    background-color: #0d1117;
}

QRadioButton::indicator:checked {
    border: 2px solid #58a6ff;
    background-color: #58a6ff;
}

QRadioButton::indicator:hover {
    border: 2px solid #58a6ff;
}

/* ---- Buttons ---- */
QPushButton#primary_btn {
    background-color: #238636;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#primary_btn:hover {
    background-color: #2ea043;
}

QPushButton#primary_btn:pressed {
    background-color: #196c2e;
}

QPushButton#secondary_btn {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton#secondary_btn:hover {
    background-color: #30363d;
    color: #e6edf3;
}

QPushButton#danger_btn {
    background-color: transparent;
    color: #f85149;
    border: 1px solid #f85149;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton#danger_btn:hover {
    background-color: #3a1a1a;
}

/* ---- Separators ---- */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #30363d;
}

/* ---- ScrollBar ---- */
QScrollBar:vertical {
    background: #0d1117;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #484f58;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #0d1117;
    height: 8px;
}

QScrollBar::handle:horizontal {
    background: #30363d;
    border-radius: 4px;
}

/* ---- Tooltip ---- */
QToolTip {
    background-color: #161b22;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}

/* ---- Splitter ---- */
QSplitter::handle {
    background-color: #30363d;
}

QSplitter::handle:horizontal {
    width: 1px;
}
"""

LIGHT_THEME = """
/* ============================================================
   ENGINEERING SUITE — LIGHT THEME
   ============================================================ */

QMainWindow, QWidget#central_widget {
    background-color: #f6f8fa;
    color: #24292f;
}

QWidget#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #d0d7de;
}

QPushButton#nav_button {
    background-color: transparent;
    color: #57606a;
    border: none;
    border-radius: 8px;
    padding: 10px 12px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}

QPushButton#nav_button:hover {
    background-color: #f6f8fa;
    color: #24292f;
}

QPushButton#nav_button:checked {
    background-color: #dbeafe;
    color: #1d4ed8;
    border-left: 3px solid #1d4ed8;
}

QPushButton#sidebar_toggle {
    background-color: transparent;
    border: none;
    color: #57606a;
    padding: 8px;
    border-radius: 6px;
}

QPushButton#sidebar_toggle:hover {
    background-color: #f6f8fa;
}

QWidget#header {
    background-color: #ffffff;
    border-bottom: 1px solid #d0d7de;
}

QLabel#header_title {
    color: #1d4ed8;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

QLabel#header_subtitle {
    color: #57606a;
    font-size: 12px;
}

QPushButton#theme_toggle_btn {
    background-color: #f6f8fa;
    color: #57606a;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
}

QPushButton#theme_toggle_btn:hover {
    background-color: #eef1f5;
}

QWidget#content_area {
    background-color: #f6f8fa;
}

QScrollArea {
    background-color: #f6f8fa;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: #f6f8fa;
}

QGroupBox {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 10px;
    margin-top: 16px;
    padding: 16px 14px 14px 14px;
    font-size: 13px;
    font-weight: 600;
    color: #57606a;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #1d4ed8;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
}

QLabel {
    color: #24292f;
    font-size: 13px;
}

QLabel#section_title {
    color: #24292f;
    font-size: 18px;
    font-weight: 700;
}

QLabel#result_value {
    color: #1d4ed8;
    font-size: 22px;
    font-weight: 700;
}

QLabel#result_label {
    color: #57606a;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.8px;
}

QLabel#pass_badge {
    background-color: #dcfce7;
    color: #16a34a;
    border: 1px solid #16a34a;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 14px;
    font-weight: 700;
}

QLabel#fail_badge {
    background-color: #fee2e2;
    color: #dc2626;
    border: 1px solid #dc2626;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 14px;
    font-weight: 700;
}

QLabel#neutral_badge {
    background-color: #f6f8fa;
    color: #57606a;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 14px;
    font-weight: 700;
}

QLineEdit, QDoubleSpinBox, QSpinBox {
    background-color: #ffffff;
    color: #24292f;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}

QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {
    border: 1px solid #1d4ed8;
}

QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
QSpinBox::up-button, QSpinBox::down-button {
    background-color: #f6f8fa;
    border: none;
    width: 18px;
}

QComboBox {
    background-color: #ffffff;
    color: #24292f;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}

QComboBox:focus {
    border: 1px solid #1d4ed8;
}

QComboBox::drop-down {
    width: 28px;
    border-left: 1px solid #d0d7de;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #24292f;
    border: 1px solid #d0d7de;
    selection-background-color: #dbeafe;
    selection-color: #1d4ed8;
}

QRadioButton {
    color: #24292f;
    font-size: 13px;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 9px;
    border: 2px solid #d0d7de;
    background-color: #ffffff;
}

QRadioButton::indicator:checked {
    border: 2px solid #1d4ed8;
    background-color: #1d4ed8;
}

QPushButton#primary_btn {
    background-color: #1a7f37;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#primary_btn:hover {
    background-color: #218838;
}

QPushButton#secondary_btn {
    background-color: #f6f8fa;
    color: #24292f;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
}

QPushButton#secondary_btn:hover {
    background-color: #eef1f5;
}

QPushButton#danger_btn {
    background-color: transparent;
    color: #dc2626;
    border: 1px solid #dc2626;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
}

QPushButton#danger_btn:hover {
    background-color: #fee2e2;
}

QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #d0d7de;
}

QScrollBar:vertical {
    background: #f6f8fa;
    width: 8px;
}

QScrollBar::handle:vertical {
    background: #d0d7de;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QToolTip {
    background-color: #ffffff;
    color: #24292f;
    border: 1px solid #d0d7de;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}

QSplitter::handle {
    background-color: #d0d7de;
}

QSplitter::handle:horizontal {
    width: 1px;
}
"""

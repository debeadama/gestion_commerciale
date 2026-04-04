# utils/styles.py
"""
Feuille de style globale SGC.
Appliquee une seule fois sur QApplication dans main.py.
Chaque vue peut surcharger uniquement ce dont elle a besoin.
"""

# ── Palette de couleurs ────────────────────────────────────────────────────
C_BG        = "#f8fafc"   # fond general
C_WHITE     = "#ffffff"
C_SIDEBAR   = "#0f172a"   # fond sidebar (identique au fond login)
C_BLUE      = "#1976D2"   # accent principal
C_BLUE_HOV  = "#1565C0"
C_BLUE_DARK = "#0d47a1"
C_TEXT      = "#1e293b"   # texte primaire
C_TEXT2     = "#64748b"   # texte secondaire
C_BORDER    = "#e2e8f0"   # bordures
C_MUTED     = "#94a3b8"   # placeholders, metadata
C_ROW_ALT   = "#f8fafc"   # ligne alternee
C_SEL       = "#dbeafe"   # selection tableau
C_RED_BG    = "#fee2e2"
C_RED       = "#dc2626"
C_GREEN_BG  = "#dcfce7"
C_GREEN     = "#16a34a"
C_AMBER_BG  = "#fef3c7"
C_AMBER     = "#d97706"

GLOBAL_STYLESHEET = f"""

/* ── Base ───────────────────────────────────────────────── */
* {{
    font-family: 'Segoe UI', Arial, sans-serif;
}}
QWidget {{
    font-size: 12px;
    color: {C_TEXT};
    background-color: {C_BG};
}}
QMainWindow, QDialog {{
    background-color: {C_BG};
}}

/* ── Sidebar ────────────────────────────────────────────── */
QFrame#sidebar {{
    background-color: {C_SIDEBAR};
    border: none;
}}
QFrame#title_frame {{
    background-color: {C_SIDEBAR};
    border: none;
}}

/* ── Inputs ─────────────────────────────────────────────── */
QLineEdit {{
    border: 1.5px solid {C_BORDER};
    border-radius: 6px;
    padding: 0 10px;
    background: {C_WHITE};
    color: {C_TEXT};
    min-height: 32px;
    max-height: 32px;
    selection-background-color: {C_SEL};
}}
QLineEdit:focus {{
    border-color: {C_BLUE};
    background: {C_WHITE};
}}
QLineEdit:hover:!focus {{
    border-color: {C_MUTED};
}}

QComboBox {{
    border: 1.5px solid {C_BORDER};
    border-radius: 6px;
    padding: 0 10px;
    background: {C_WHITE};
    color: {C_TEXT};
    min-height: 32px;
    max-height: 32px;
}}
QComboBox:focus {{
    border-color: {C_BLUE};
}}
QComboBox:hover:!focus {{
    border-color: {C_MUTED};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    border: 1px solid {C_BORDER};
    background: {C_WHITE};
    selection-background-color: {C_SEL};
    selection-color: {C_TEXT};
    outline: none;
}}

QSpinBox, QDoubleSpinBox {{
    border: 1.5px solid {C_BORDER};
    border-radius: 6px;
    padding: 0 8px;
    background: {C_WHITE};
    min-height: 32px;
    max-height: 32px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {C_BLUE};
}}
QTextEdit, QPlainTextEdit {{
    border: 1.5px solid {C_BORDER};
    border-radius: 6px;
    padding: 8px;
    background: {C_WHITE};
}}
QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {C_BLUE};
}}

/* ── Boutons ────────────────────────────────────────────── */
QPushButton {{
    border: none;
    border-radius: 6px;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 500;
    min-height: 32px;
    max-height: 32px;
    background-color: #e2e8f0;
    color: #475569;
}}
QPushButton:hover    {{ background-color: #cbd5e1; }}
QPushButton:pressed  {{ background-color: #94a3b8; }}
QPushButton:disabled {{ background-color: #f1f5f9; color: #cbd5e1; }}

QPushButton#btn_add {{
    background-color: {C_BLUE};
    color: {C_WHITE};
    font-weight: bold;
}}
QPushButton#btn_add:hover   {{ background-color: {C_BLUE_HOV}; }}
QPushButton#btn_add:pressed {{ background-color: {C_BLUE_DARK}; }}

QPushButton#btn_delete, QPushButton#btn_cancel {{
    background-color: {C_RED_BG};
    color: {C_RED};
}}
QPushButton#btn_delete:hover, QPushButton#btn_cancel:hover {{
    background-color: #fecaca;
}}
QPushButton#btn_delete:disabled, QPushButton#btn_cancel:disabled {{
    background-color: #f1f5f9; color: #cbd5e1;
}}

QPushButton#btn_validate {{
    background-color: {C_GREEN_BG};
    color: {C_GREEN};
    font-weight: bold;
}}
QPushButton#btn_validate:hover   {{ background-color: #bbf7d0; }}
QPushButton#btn_validate:disabled {{ background-color: #f1f5f9; color: #cbd5e1; }}

QPushButton#btn_pdf {{
    background-color: {C_AMBER_BG};
    color: {C_AMBER};
}}
QPushButton#btn_pdf:hover   {{ background-color: #fde68a; }}
QPushButton#btn_pdf:disabled {{ background-color: #f1f5f9; color: #cbd5e1; }}

QPushButton#btn_stock {{
    background-color: #ede9fe;
    color: #7c3aed;
}}
QPushButton#btn_stock:hover   {{ background-color: #ddd6fe; }}
QPushButton#btn_stock:disabled {{ background-color: #f1f5f9; color: #cbd5e1; }}

/* ── Tableaux ───────────────────────────────────────────── */
QTableWidget {{
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    background: {C_WHITE};
    gridline-color: transparent;
    alternate-background-color: {C_ROW_ALT};
    selection-background-color: {C_SEL};
    selection-color: {C_TEXT};
    outline: none;
}}
QTableWidget::item {{
    padding: 4px 10px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: {C_SEL};
    color: {C_TEXT};
}}
QHeaderView::section {{
    background-color: #f1f5f9;
    color: #475569;
    font-size: 11px;
    font-weight: bold;
    padding: 7px 10px;
    border: none;
    border-bottom: 1.5px solid {C_BORDER};
    letter-spacing: 0.3px;
    text-transform: uppercase;
}}
QHeaderView {{ background: transparent; border: none; }}

/* ── Scrollbars ─────────────────────────────────────────── */
QScrollBar:vertical {{
    border: none; background: #f1f5f9;
    width: 7px; border-radius: 4px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #cbd5e1; border-radius: 4px; min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {C_MUTED}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    border: none; background: #f1f5f9;
    height: 7px; border-radius: 4px; margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: #cbd5e1; border-radius: 4px; min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{ background: {C_MUTED}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Onglets ────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    background: {C_WHITE};
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {C_TEXT2};
    padding: 8px 16px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 12px;
    font-weight: bold;
}}
QTabBar::tab:selected {{
    color: {C_BLUE};
    border-bottom: 2px solid {C_BLUE};
    background: transparent;
}}
QTabBar::tab:hover {{ color: {C_BLUE}; }}

/* ── Separateurs ────────────────────────────────────────── */
QFrame[frameShape="4"] {{ color: {C_BORDER}; max-height: 1px; }}
QFrame[frameShape="5"] {{ color: {C_BORDER}; max-width: 1px; }}

/* ── MessageBox ─────────────────────────────────────────── */
QMessageBox {{ background: {C_WHITE}; }}
QMessageBox QLabel {{ background: {C_WHITE}; font-size: 13px; }}
QMessageBox QPushButton {{ min-width: 80px; }}

/* ── Dialogs ────────────────────────────────────────────── */
QDialog {{ background: {C_WHITE}; }}
QDialogButtonBox QPushButton {{
    min-width: 80px; background: #e2e8f0; color: #475569;
}}
QDialogButtonBox QPushButton[text="OK"],
QDialogButtonBox QPushButton[text="Enregistrer"] {{
    background: {C_BLUE}; color: white;
}}

/* ── CheckBox ───────────────────────────────────────────── */
QCheckBox, QRadioButton {{
    spacing: 8px; color: {C_TEXT};
}}

/* ── StatusBar ──────────────────────────────────────────── */
QStatusBar {{
    background: {C_BG}; color: {C_MUTED}; font-size: 11px;
}}
"""

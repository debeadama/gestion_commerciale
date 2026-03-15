# utils/pagination_widget.py
"""
Widget de pagination réutilisable pour les tableaux PyQt6.
Usage :
    self.pagination = PaginationWidget(page_size=50)
    self.pagination.page_changed.connect(self._on_page_changed)
    layout.addWidget(self.pagination)

    def _on_page_changed(self, page, offset, limit):
        data = MyController.get_all()[offset:offset+limit]
        self._populate_table(data)
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QComboBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont


class PaginationWidget(QWidget):
    """Barre de pagination avec boutons Précédent / Suivant et sélecteur de taille."""

    page_changed = pyqtSignal(int, int, int)  # (page, offset, limit)

    def __init__(self, page_size: int = 50, parent=None):
        super().__init__(parent)
        self._page      = 1
        self._page_size = page_size
        self._total     = 0
        self._build_ui()

    # ----------------------------------------------------------
    # Interface
    # ----------------------------------------------------------

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 2)
        layout.setSpacing(6)

        # Info total
        self.lbl_total = QLabel("")
        self.lbl_total.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(self.lbl_total)
        layout.addStretch()

        # Taille de page
        layout.addWidget(QLabel("Lignes :"))
        self.size_combo = QComboBox()
        self.size_combo.setFixedWidth(70)
        self.size_combo.setFixedHeight(28)
        for s in [25, 50, 100, 200]:
            self.size_combo.addItem(str(s), s)
        idx = self.size_combo.findData(self._page_size)
        if idx >= 0:
            self.size_combo.setCurrentIndex(idx)
        self.size_combo.currentIndexChanged.connect(self._on_size_changed)
        layout.addWidget(self.size_combo)

        # Navigation
        self.btn_first = self._nav_btn("«")
        self.btn_prev  = self._nav_btn("‹")
        self.lbl_page  = QLabel("Page 1 / 1")
        self.lbl_page.setFixedWidth(90)
        self.lbl_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_page.setStyleSheet("font-size: 12px; color: #1e293b;")
        self.btn_next  = self._nav_btn("›")
        self.btn_last  = self._nav_btn("»")

        self.btn_first.clicked.connect(self.go_first)
        self.btn_prev.clicked.connect(self.go_prev)
        self.btn_next.clicked.connect(self.go_next)
        self.btn_last.clicked.connect(self.go_last)

        for w in [self.btn_first, self.btn_prev, self.lbl_page,
                  self.btn_next, self.btn_last]:
            layout.addWidget(w)

    def _nav_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(28, 28)
        btn.setFont(QFont("Arial", 11))
        btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #e2e8f0; border-radius: 4px;
                background: white; color: #475569;
            }
            QPushButton:hover { background: #f1f5f9; }
            QPushButton:disabled { color: #cbd5e1; background: #f8fafc; }
        """)
        return btn

    # ----------------------------------------------------------
    # API publique
    # ----------------------------------------------------------

    def set_total(self, total: int):
        """Definit le nombre total d'enregistrements et actualise l'affichage."""
        self._total = total
        self._page  = min(self._page, max(1, self.page_count()))
        self._update_ui()

    def reset(self, total: int):
        """Remet a la page 1 avec un nouveau total."""
        self._total = total
        self._page  = 1
        self._update_ui()

    def page_count(self) -> int:
        if self._total == 0:
            return 1
        return (self._total + self._page_size - 1) // self._page_size

    def current_offset(self) -> int:
        return (self._page - 1) * self._page_size

    def current_limit(self) -> int:
        return self._page_size

    # ----------------------------------------------------------
    # Navigation
    # ----------------------------------------------------------

    def go_first(self):
        if self._page != 1:
            self._page = 1
            self._emit()

    def go_prev(self):
        if self._page > 1:
            self._page -= 1
            self._emit()

    def go_next(self):
        if self._page < self.page_count():
            self._page += 1
            self._emit()

    def go_last(self):
        last = self.page_count()
        if self._page != last:
            self._page = last
            self._emit()

    def _on_size_changed(self):
        self._page_size = self.size_combo.currentData()
        self._page      = 1
        self._emit()

    def _emit(self):
        self._update_ui()
        self.page_changed.emit(
            self._page, self.current_offset(), self.current_limit())

    def _update_ui(self):
        pc = self.page_count()
        self.lbl_page.setText(f"Page {self._page} / {pc}")
        self.lbl_total.setText(f"Total : {self._total} enregistrement(s)")
        self.btn_first.setEnabled(self._page > 1)
        self.btn_prev.setEnabled(self._page > 1)
        self.btn_next.setEnabled(self._page < pc)
        self.btn_last.setEnabled(self._page < pc)

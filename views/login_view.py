# views/login_view.py
import os

from controllers.auth_controller import SessionManager
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPixmap
from PyQt6.QtWidgets import QDialog, QGraphicsDropShadowEffect


class LoginView(QDialog):
    """Fenetre de connexion."""

    def __init__(self, parent=None):
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'login.ui')
        uic.loadUi(ui_path, self)
        self.setWindowTitle("SGC — Connexion")
        self._apply_styles()
        self._apply_fonts()
        self._connect_signals()

    def _connect_signals(self):
        self.login_btn.clicked.connect(self._do_login)
        self.password_input.returnPressed.connect(self._do_login)
        self.username_input.returnPressed.connect(
            lambda: self.password_input.setFocus())

    def _do_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        self.error_label.setVisible(False)

        if not username or not password:
            self._show_error("Veuillez remplir tous les champs.")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Vérification…")

        success, message = SessionManager.login(username, password)

        self.login_btn.setEnabled(True)
        self.login_btn.setText("Se connecter")

        if success:
            self.accept()
        else:
            self._show_error(message)
            self.password_input.clear()
            self.password_input.setFocus()

    def _show_error(self, msg: str) -> None:
        self.error_label.setText(msg)
        self.error_label.setVisible(True)

    def _apply_fonts(self) -> None:
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "assets", "sgc_logo.ico"
        )
        pixmap = QPixmap(logo_path).scaled(
            140, 140,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.lbl_icon.setPixmap(pixmap)
        self.lbl_icon.setText("")
        self.lbl_subtitle.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.lbl_title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.username_input.setFont(QFont("Segoe UI", 11))
        self.password_input.setFont(QFont("Segoe UI", 11))
        self.login_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.error_label.setFont(QFont("Segoe UI", 9))

    def _apply_styles(self) -> None:
        # Fond sombre du dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
            }
        """)

        # Card blanche avec ombre
        self.card.setStyleSheet("""
            QFrame#card {
                background-color: #ffffff;
                border-radius: 16px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        from PyQt6.QtGui import QColor
        shadow.setColor(QColor(0, 0, 0, 80))
        self.card.setGraphicsEffect(shadow)

        # Logo
        self.lbl_icon.setStyleSheet(
            "background: transparent; padding: 0; margin: 0;")
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Nom complet — lisible, contrasté
        self.lbl_subtitle.setStyleSheet("""
            QLabel {
                color: #1e293b;
                background: transparent;
                letter-spacing: 0.5px;
            }
        """)
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Titre "Connexion" — séparé visuellement par un espace
        self.lbl_title.setStyleSheet("""
            QLabel {
                color: #0f172a;
                background: transparent;
                letter-spacing: 1px;
                padding-bottom: 3px;
                border-bottom: 2px solid #1976D2;
            }
        """)
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Champs : fond tres leger, bordure subtile, focus bleu
        field_style = """
            QLineEdit {
                background-color: #f8fafc;
                border: 1.5px solid #e2e8f0;
                border-radius: 8px;
                padding: 0 14px;
                color: #1e293b;
                selection-background-color: #bfdbfe;
            }
            QLineEdit:focus {
                border-color: #1976D2;
                background-color: #ffffff;
            }
            QLineEdit:hover {
                border-color: #94a3b8;
            }
        """
        self.username_input.setStyleSheet(field_style)
        self.password_input.setStyleSheet(field_style)

        # Bouton
        self.login_btn.setStyleSheet("""
            QPushButton#login_btn {
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 8px;
                letter-spacing: 0.5px;
            }
            QPushButton#login_btn:hover {
                background-color: #1565C0;
            }
            QPushButton#login_btn:pressed {
                background-color: #0d47a1;
            }
            QPushButton#login_btn:disabled {
                background-color: #93c5fd;
                color: #e0f2fe;
            }
        """)

        # Erreur
        self.error_label.setStyleSheet("""
            QLabel {
                color: #ef4444;
                background: transparent;
                padding: 6px 0 0 0;
            }
        """)

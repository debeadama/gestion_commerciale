# views/login_view.py
import os
from PyQt6 import uic
from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import Qt
from controllers.auth_controller import SessionManager


class LoginView(QDialog):
    """Fenêtre de connexion — charge login.ui."""

    def __init__(self, parent=None):
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'login.ui')
        uic.loadUi(ui_path, self)
        self.setWindowTitle("Connexion - SGC-")
        self._apply_styles()
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
            self._show_error("Veuillez remplir tous les champs svp")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Verification...")

        # SessionManager.login() retourne (bool, message)
        success, message = SessionManager.login(username, password)

        self.login_btn.setEnabled(True)
        self.login_btn.setText("Se connecter")

        if success:
            self.accept()
        else:
            self._show_error(message)
            self.password_input.clear()
            self.password_input.setFocus()

    def _show_error(self, msg):
        self.error_label.setText(msg)
        self.error_label.setVisible(True)

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #f1f5f9; }
            QLineEdit {
                border: 1px solid #cbd5e1; border-radius: 6px;
                padding: 8px 12px; font-size: 13px; background: white;
            }
            QLineEdit:focus { border-color: #1976D2; }
            QPushButton#login_btn {
                background-color: #1976D2; color: white; border: none;
                border-radius: 6px; font-size: 13px; font-weight: bold;
                padding: 10px;
            }
            QPushButton#login_btn:hover { background-color: #1565C0; }
            QPushButton#login_btn:disabled { background-color: #90caf9; }
        """)

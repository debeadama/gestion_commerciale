# views/login_view.py
import os

from config import APP_VERSION
from controllers.auth_controller import SessionManager
from PyQt6 import uic
from PyQt6.QtCore import (Qt, QTimer, QPropertyAnimation,
                           QPoint, QEasingCurve)
from PyQt6.QtGui import QColor, QFont, QPixmap, QIcon, QAction
from PyQt6.QtWidgets import QDialog, QGraphicsDropShadowEffect

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 30


class LoginView(QDialog):
    """Fenetre de connexion."""

    def __init__(self, parent=None):
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'login.ui')
        uic.loadUi(ui_path, self)
        self.setWindowTitle("SGC - Connexion")

        self._failed_attempts = 0
        self._locked = False

        self._apply_styles()
        self._setup_password_toggle()
        self._connect_signals()

        self.lbl_version.setText(f"v{APP_VERSION}")
        self.username_input.setFocus()

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_fonts()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_password_toggle(self):
        """Ajoute le bouton œil pour afficher/masquer le mot de passe."""
        self._pwd_visible = False
        self._action_eye = QAction(self)
        self._update_eye_icon()
        self._action_eye.triggered.connect(self._toggle_password)
        self.password_input.addAction(
            self._action_eye, self.password_input.ActionPosition.TrailingPosition)

    def _connect_signals(self):
        self.login_btn.clicked.connect(self._do_login)
        self.password_input.returnPressed.connect(self._do_login)
        self.username_input.returnPressed.connect(
            lambda: self.password_input.setFocus())
        self.password_input.keyPressEvent = self._password_key_event

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _toggle_password(self):
        self._pwd_visible = not self._pwd_visible
        mode = (self.password_input.EchoMode.Normal
                if self._pwd_visible
                else self.password_input.EchoMode.Password)
        self.password_input.setEchoMode(mode)
        self._update_eye_icon()

    def _update_eye_icon(self):
        self._action_eye.setText("🙈" if self._pwd_visible else "👁")

    def _password_key_event(self, event):
        """Intercepte les touches pour détecter Caps Lock."""
        caps = bool(event.modifiers() & Qt.KeyboardModifier.GroupSwitchModifier) or \
               self._is_caps_lock_on()
        self.caps_lock_label.setVisible(caps)
        # Appel de l'implémentation parente
        from PyQt6.QtWidgets import QLineEdit
        QLineEdit.keyPressEvent(self.password_input, event)

    def _is_caps_lock_on(self):
        from PyQt6.QtWidgets import QApplication
        state = QApplication.keyboardModifiers()
        # Sur Windows, on détecte via une touche virtuelle
        try:
            import ctypes
            return bool(ctypes.WinDLL("User32.dll").GetKeyState(0x14) & 1)
        except Exception:
            return False

    def _do_login(self):
        if self._locked:
            return

        username = self.username_input.text().strip()
        password = self.password_input.text()

        self.error_label.setVisible(False)

        if not username or not password:
            self._show_error("Veuillez remplir tous les champs.")
            self._shake()
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Vérification…")

        success, message = SessionManager.login(username, password)

        self.login_btn.setEnabled(True)
        self.login_btn.setText("Se connecter")

        if success:
            self._failed_attempts = 0
            self.accept()
        else:
            self._failed_attempts += 1
            remaining = MAX_ATTEMPTS - self._failed_attempts

            if self._failed_attempts >= MAX_ATTEMPTS:
                self._start_lockout()
            else:
                self._show_error(
                    f"{message}  -  {remaining} tentative(s) restante(s).")
                self._shake()

            self.password_input.clear()
            self.password_input.setFocus()

    def _start_lockout(self):
        self._locked = True
        self._lockout_remaining = LOCKOUT_SECONDS
        self.login_btn.setEnabled(False)
        self._update_lockout_label()

        self._lockout_timer = QTimer(self)
        self._lockout_timer.timeout.connect(self._tick_lockout)
        self._lockout_timer.start(1000)

    def _tick_lockout(self):
        self._lockout_remaining -= 1
        if self._lockout_remaining <= 0:
            self._lockout_timer.stop()
            self._locked = False
            self._failed_attempts = 0
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Se connecter")
            self.error_label.setVisible(False)
        else:
            self._update_lockout_label()

    def _update_lockout_label(self):
        self._show_error(
            f"Trop de tentatives. Réessayez dans {self._lockout_remaining}s.")

    # ------------------------------------------------------------------
    # Shake animation
    # ------------------------------------------------------------------

    def _shake(self):
        pos = self.card.pos()
        anim = QPropertyAnimation(self.card, b"pos", self)
        anim.setDuration(350)
        anim.setEasingCurve(QEasingCurve.Type.Linear)
        anim.setKeyValueAt(0,    pos)
        anim.setKeyValueAt(0.15, QPoint(pos.x() - 8, pos.y()))
        anim.setKeyValueAt(0.30, QPoint(pos.x() + 8, pos.y()))
        anim.setKeyValueAt(0.45, QPoint(pos.x() - 6, pos.y()))
        anim.setKeyValueAt(0.60, QPoint(pos.x() + 6, pos.y()))
        anim.setKeyValueAt(0.75, QPoint(pos.x() - 3, pos.y()))
        anim.setKeyValueAt(0.90, QPoint(pos.x() + 3, pos.y()))
        anim.setKeyValueAt(1,    pos)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------

    def _show_error(self, msg: str) -> None:
        self.error_label.setText(msg)
        self.error_label.setVisible(True)

    def _apply_fonts(self) -> None:
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets", "logo_SGC_265x151.png"
        )
        src = QPixmap(logo_path)
        # Largeur reelle de la carte (dialog 440 - marges outer 28*2 = 384)
        card_w = self.lbl_icon.width() if self.lbl_icon.width() > 100 else 296
        logo_h = 136
        scaled = src.scaled(
            card_w, logo_h,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        # Recadrage centré
        x_off = max(0, (scaled.width()  - card_w) // 2)
        y_off = max(0, (scaled.height() - logo_h) // 2)
        cropped = scaled.copy(x_off, y_off, card_w, logo_h)
        # Coins arrondis (haut uniquement, correspondant a la carte)
        from PyQt6.QtGui import QPainter, QPainterPath
        from PyQt6.QtCore import QRectF
        rounded = QPixmap(cropped.size())
        rounded.fill(Qt.GlobalColor.transparent)
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        r = QRectF(rounded.rect())
        radius = 16.0
        path.moveTo(r.left() + radius, r.top())
        path.lineTo(r.right() - radius, r.top())
        path.arcTo(r.right() - 2*radius, r.top(), 2*radius, 2*radius, 90, -90)
        path.lineTo(r.right(), r.bottom())
        path.lineTo(r.left(),  r.bottom())
        path.arcTo(r.left(), r.top(), 2*radius, 2*radius, 180, -90)
        path.closeSubpath()
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, cropped)
        painter.end()
        self.lbl_icon.setPixmap(rounded)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.username_input.setFont(QFont("Segoe UI", 11))
        self.password_input.setFont(QFont("Segoe UI", 11))
        self.login_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.error_label.setFont(QFont("Segoe UI", 9))
        self.caps_lock_label.setFont(QFont("Segoe UI", 9))
        self.lbl_version.setFont(QFont("Segoe UI", 8))

    def _apply_styles(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
            }
        """)

        self.card.setStyleSheet("""
            QFrame#card {
                background-color: #ffffff;
                border-radius: 16px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.card.setGraphicsEffect(shadow)

        self.lbl_icon.setStyleSheet(
            "background: transparent; padding: 0; margin: 0; border-radius: 0px;")

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

        self.error_label.setStyleSheet("""
            QLabel {
                color: #ef4444;
                background: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: 6px;
                padding: 6px 8px;
            }
        """)

        self.caps_lock_label.setStyleSheet("""
            QLabel {
                color: #92400e;
                background: #fef3c7;
                border: 1px solid #fde68a;
                border-radius: 6px;
                padding: 4px 8px;
            }
        """)

        self.lbl_version.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                background: transparent;
            }
        """)

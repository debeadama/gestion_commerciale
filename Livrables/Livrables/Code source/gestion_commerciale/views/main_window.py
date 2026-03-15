# views/main_window.py
import os
from PyQt6 import uic
from PyQt6.QtWidgets import (QMainWindow, QMessageBox, QVBoxLayout, QLabel)
from PyQt6.QtCore import Qt, QTimer
from controllers.auth_controller import SessionManager
from views.clients_view import ClientsView
from views.products_view import ProductsView
from views.sales_view import SalesView
from views.stats_view import StatsView
from views.settings_view import SettingsView
from views.dashboard_view import DashboardView

INACTIVITY_TIMEOUT_MS = 15 * 60 * 1000
WARNING_BEFORE_MS     =  1 * 60 * 1000


def _confirm(parent, title, message):
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(message)
    box.setIcon(QMessageBox.Icon.Question)
    btn_oui = box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
    box.addButton("Non", QMessageBox.ButtonRole.NoRole)
    box.exec()
    return box.clickedButton() == btn_oui


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'main_window.ui')
        uic.loadUi(ui_path, self)
        self._connect_buttons()
        self._apply_styles()
        self._load_user_info()
        self._load_modules()
        self._setup_inactivity_timer()
        self.content_area.setCurrentWidget(self.page_dashboard)
        self.btn_dashboard.setChecked(True)

    # ----------------------------------------------------------
    # Timer d'inactivite
    # ----------------------------------------------------------

    def _setup_inactivity_timer(self):
        """Configure le timer de deconnexion automatique."""
        self._inactivity_timer = QTimer(self)
        self._inactivity_timer.setSingleShot(True)
        self._inactivity_timer.timeout.connect(self._warn_inactivity)
        self._inactivity_timer.start(INACTIVITY_TIMEOUT_MS - WARNING_BEFORE_MS)

        self._logout_timer = QTimer(self)
        self._logout_timer.setSingleShot(True)
        self._logout_timer.timeout.connect(self._auto_logout)

        self._warning_bar = QLabel(
            "  Deconnexion automatique dans 1 minute par inactivité. "
            "Appuyez sur une touche pour rester connecté.")
        self._warning_bar.setStyleSheet(
            "background-color: #f59e0b; color: white; "
            "font-weight: bold; font-size: 11px; padding: 6px;")
        self._warning_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._warning_bar.setVisible(False)

        central = self.centralWidget()
        if central and central.layout():
            central.layout().insertWidget(0, self._warning_bar)

    def _reset_inactivity_timer(self):
        """Remet le timer à zero à chaque interaction."""
        self._logout_timer.stop()
        self._warning_bar.setVisible(False)
        self._inactivity_timer.start(INACTIVITY_TIMEOUT_MS - WARNING_BEFORE_MS)

    def _warn_inactivity(self):
        """Affiche le bandeau d'avertissement."""
        self._warning_bar.setVisible(True)
        self._logout_timer.start(WARNING_BEFORE_MS)

    def _auto_logout(self):
        """Deconnexion automatique après inactivité."""
        self._warning_bar.setVisible(False)
        self._inactivity_timer.stop()
        self._logout_timer.stop()
        SessionManager.logout()
        QMessageBox.information(
            self, "Deconnexion automatique",
            "Vous avez été deconnecté automatiquement\n"
            "après 15 minutes d'inactivité.")
        self._show_login()

    # ----------------------------------------------------------
    # Evenements souris et clavier
    # ----------------------------------------------------------

    def mouseMoveEvent(self, event):
        self._reset_inactivity_timer()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        self._reset_inactivity_timer()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        self._reset_inactivity_timer()
        super().keyPressEvent(event)

    # ----------------------------------------------------------
    # Chargement des modules
    # ----------------------------------------------------------

    def _load_modules(self):
        """Integre chaque module dans sa page du StackedWidget."""
        self._dashboard_view = DashboardView()
        if self.page_dashboard.layout() is None:
            layout = QVBoxLayout(self.page_dashboard)
            layout.setContentsMargins(0, 0, 0, 0)
        self.page_dashboard.layout().addWidget(self._dashboard_view)

        self._clients_view = ClientsView()
        if self.page_clients.layout() is None:
            layout = QVBoxLayout(self.page_clients)
            layout.setContentsMargins(0, 0, 0, 0)
        self.page_clients.layout().addWidget(self._clients_view)

        self._products_view = ProductsView()
        if self.page_products.layout() is None:
            layout = QVBoxLayout(self.page_products)
            layout.setContentsMargins(0, 0, 0, 0)
        self.page_products.layout().addWidget(self._products_view)

        self._sales_view = SalesView()
        if self.page_sales.layout() is None:
            layout = QVBoxLayout(self.page_sales)
            layout.setContentsMargins(0, 0, 0, 0)
        self.page_sales.layout().addWidget(self._sales_view)

        self._stats_view = StatsView()
        if self.page_stats.layout() is None:
            layout = QVBoxLayout(self.page_stats)
            layout.setContentsMargins(0, 0, 0, 0)
        self.page_stats.layout().addWidget(self._stats_view)

        if SessionManager.has_permission('all') or SessionManager.get_role() == 'manager':
            self._settings_view = SettingsView()
            if self.page_settings.layout() is None:
                layout = QVBoxLayout(self.page_settings)
                layout.setContentsMargins(0, 0, 0, 0)
            self.page_settings.layout().addWidget(self._settings_view)

    # ----------------------------------------------------------
    # Connexion des boutons
    # ----------------------------------------------------------

    def _connect_buttons(self):
        self.btn_dashboard.clicked.connect(
            lambda: self._navigate(self.page_dashboard, self.btn_dashboard))
        self.btn_clients.clicked.connect(
            lambda: self._navigate(self.page_clients, self.btn_clients))
        self.btn_products.clicked.connect(
            lambda: self._navigate(self.page_products, self.btn_products))
        self.btn_sales.clicked.connect(
            lambda: self._navigate(self.page_sales, self.btn_sales))
        self.btn_stats.clicked.connect(
            lambda: self._navigate(self.page_stats, self.btn_stats))
        self.btn_settings.clicked.connect(
            lambda: self._navigate(self.page_settings, self.btn_settings))
        self.btn_logout.clicked.connect(self._logout)

    # ----------------------------------------------------------
    # Navigation
    # ----------------------------------------------------------

    def _navigate(self, page, active_btn):
        self._reset_inactivity_timer()
        for btn in [self.btn_dashboard, self.btn_clients, self.btn_products,
                    self.btn_sales, self.btn_stats, self.btn_settings]:
            btn.setChecked(False)
        active_btn.setChecked(True)
        self.content_area.setCurrentWidget(page)

    # ----------------------------------------------------------
    # Infos utilisateur
    # ----------------------------------------------------------

    def _load_user_info(self):
        user = SessionManager.get_current_user()
        if user:
            role_labels = {
                'admin':   'Administrateur',
                'manager': 'Manager',
                'vendeur': 'Vendeur',
            }
            role = role_labels.get(user['role'], user['role'])
            self.user_info.setText(
                f"Utilisateur connecté : {user['username']}\n"
                f"Profil : {role}")
        if not SessionManager.has_permission('all') and SessionManager.get_role() != 'manager':
            self.btn_settings.setVisible(False)

    # ----------------------------------------------------------
    # Deconnexion manuelle
    # ----------------------------------------------------------

    def _logout(self):
        if _confirm(self, "Déconnexion", "Voulez-vous vraiment vous deconnecter ?"):
            self._inactivity_timer.stop()
            self._logout_timer.stop()
            SessionManager.logout()
            self._show_login()

    # ----------------------------------------------------------
    # Retour a la page de connexion
    # ----------------------------------------------------------

    def _show_login(self):
        """Ferme la fenetre principale et rouvre la fenetre de connexion."""
        from views.login_view import LoginView
        self._login_window = LoginView()

        def on_login_accepted():
            self._next_window = MainWindow()
            self._next_window.showMaximized()

        self._login_window.accepted.connect(on_login_accepted)
        self._login_window.show()
        self.close()

    # ----------------------------------------------------------
    # Styles
    # ----------------------------------------------------------

    def _apply_styles(self):
        style = (
            "QFrame#sidebar { background-color: #003366; }"
            "QFrame#title_frame { background-color: #003366; padding: 15px; }"
            "QLabel#app_title { color: white; font-size: 40px; font-weight: bold; }"
            "QLabel#app_subtitle { color: #94a3b8; font-size: 11px; }"
            "QLabel#user_info { color: #cbd5e1; font-size: 12px; padding: 10px; }"
            "QPushButton#btn_dashboard, QPushButton#btn_clients,"
            "QPushButton#btn_products, QPushButton#btn_sales,"
            "QPushButton#btn_stats, QPushButton#btn_settings {"
            "    background-color: transparent; color: #94a3b8;"
            "    border: none; text-align: left;"
            "    padding-left: 30px; font-size: 13px; }"
            "QPushButton#btn_dashboard:hover, QPushButton#btn_clients:hover,"
            "QPushButton#btn_products:hover, QPushButton#btn_sales:hover,"
            "QPushButton#btn_stats:hover, QPushButton#btn_settings:hover {"
            "    background-color: #334155; color: white; }"
            "QPushButton#btn_dashboard:checked, QPushButton#btn_clients:checked,"
            "QPushButton#btn_products:checked, QPushButton#btn_sales:checked,"
            "QPushButton#btn_stats:checked, QPushButton#btn_settings:checked {"
            "    background-color: #1976D2; color: white; font-weight: bold; }"
            "QPushButton#btn_logout { background-color: transparent; color: #f87171;"
            "    border-top: 1px solid #334155; text-align: left;"
            "    padding-left: 25px; font-size: 15px; }"
            "QPushButton#btn_logout:hover { background-color: #7f1d1d; color: white; }"
            "QStackedWidget#content_area { background-color: #f1f5f9; }"
        )
        self.setStyleSheet(style)

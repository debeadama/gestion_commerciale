# main.py
"""
Point d'entree principal de l'application SGC.

Systeme de Gestion Commerciale — PyQt6 + MySQL.
"""

import logging
import logging.handlers
import os
import sys

from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication, QMessageBox

from database.connection import db
from views.login_view import LoginView


def setup_logging(app_dir: str) -> None:
    """Configure le systeme de logs avec rotation de fichiers."""
    log_dir = os.path.join(app_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "sgc.log")

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotation : 1 Mo max, 5 fichiers conserves
    file_handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def load_environment() -> str:
    """
    Detecte le chemin de l'application et charge le fichier .env.

    Gere les deux modes d'execution :
    - Executable PyInstaller (frozen)
    - Developpement normal

    Returns:
        str: Chemin absolu du fichier .env charge.
    """
    if getattr(sys, "frozen", False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    env_path = os.path.join(application_path, ".env")
    load_dotenv(env_path)

    return env_path


def print_debug_info(env_path: str) -> None:
    """
    Affiche les informations de debug si APP_DEBUG est active.

    Args:
        env_path (str): Chemin du fichier .env charge.
    """
    application_path = os.path.dirname(env_path)

    print(f"Chemin application : {application_path}")
    print(f"Fichier .env existe : {os.path.exists(env_path)}")
    print(f"Base de donnees    : {os.getenv('DB_NAME', 'N/A')}")


def main() -> None:
    """
    Initialise et lance l'application SGC.

    Verifie la connexion a la base de donnees, affiche la fenetre
    de connexion puis ouvre la fenetre principale apres authentification.
    """
    env_path = load_environment()

    app_dir = os.path.dirname(env_path)
    setup_logging(app_dir)

    if os.getenv("APP_DEBUG", "False").lower() == "true":
        print_debug_info(env_path)

    app = QApplication(sys.argv)
    app.setApplicationName("SGC - Systeme de Gestion Commerciale")
    app.setStyle("Fusion")

    from utils.styles import GLOBAL_STYLESHEET
    app.setStyleSheet(GLOBAL_STYLESHEET)

    if not db.connect():
        QMessageBox.critical(
            None,
            "Erreur de connexion",
            "Impossible de se connecter a la base de donnees.\n\n"
            "Verifiez que MySQL a demarré et que le fichier .env "
            "est correct.\n\n"
            f"Chemin recherche : {env_path}",
        )
        sys.exit(1)

    login = LoginView()

    def on_login_accepted() -> None:
        """
        Ouvre la fenetre principale apres authentification reussie.

        Importe MainWindow a la demande pour eviter les imports circulaires.
        """
        from views.main_window import MainWindow

        app._main_window = MainWindow()
        app._main_window.showMaximized()

    login.accepted.connect(on_login_accepted)
    login.exec()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
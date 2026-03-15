# main.py
"""
Point d'entree principal de l'application SGC.

Systeme de Gestion Commerciale — PyQt6 + MySQL.
"""

import os
import sys

from dotenv import load_dotenv

# ------------------------------------------------------------------
# Configuration du chemin du fichier .env
# ------------------------------------------------------------------

# Detecter si on est dans un executable PyInstaller ou en developpement
if getattr(sys, 'frozen', False):
    # Mode executable : le .env est dans le meme dossier que l'exe
    application_path = os.path.dirname(sys.executable)
else:
    # Mode developpement : le .env est a la racine du projet
    application_path = os.path.dirname(os.path.abspath(__file__))

# Charger le fichier .env depuis le bon emplacement
env_path = os.path.join(application_path, '.env')
load_dotenv(env_path)

# Affichage de debug (desactiver en production via APP_DEBUG=False)
if os.getenv('APP_DEBUG', 'False').lower() == 'true':
    print(f"Chemin application : {application_path}")
    print(f"Fichier .env existe : {os.path.exists(env_path)}")
    print(f"Base de donnees    : {os.getenv('DB_NAME', 'N/A')}")

# ------------------------------------------------------------------

from PyQt6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from database.connection import db
from views.login_view import LoginView


def main():
    """
    Initialise et lance l'application SGC.

    Verifie la connexion a la base de donnees, affiche la fenetre
    de connexion puis ouvre la fenetre principale apres authentification.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("SGC - Systeme de Gestion Commerciale")
    app.setStyle("Fusion")  # Theme visuel uniforme sur tous les OS

    # Verification de la connexion a la base de donnees
    if not db.connect():
        QMessageBox.critical(
            None,
            "Erreur de connexion",
            "Impossible de se connecter a la base de donnees.\n\n"
            "Verifiez que MySQL a demarre et que le fichier .env "
            "est correct.\n\n"
            f"Chemin recherche : {env_path}"
        )
        sys.exit(1)

    login = LoginView()

    def on_login_accepted():
        """
        Ouvre la fenetre principale apres authentification reussie.

        Importe MainWindow a la demande pour eviter les imports circulaires.
        """
        from views.main_window import MainWindow  # noqa: E402
        app._main_window = MainWindow()
        app._main_window.showMaximized()

    login.accepted.connect(on_login_accepted)
    login.exec()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

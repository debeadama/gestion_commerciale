# main.py
# Point d'entrée principal de l'application SGC (Système de Gestion Commerciale)

import sys
import os
from dotenv import load_dotenv

# ════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION DU CHEMIN DU FICHIER .env
# ════════════════════════════════════════════════════════════════════════════

# Détecter si on est dans un exécutable PyInstaller ou en mode développement
if getattr(sys, 'frozen', False):
    # Mode exécutable : le .env est dans le même dossier que l'exe
    application_path = os.path.dirname(sys.executable)
else:
    # Mode développement : le .env est à la racine du projet
    application_path = os.path.dirname(os.path.abspath(__file__))

# Charger le fichier .env depuis le bon emplacement
env_path = os.path.join(application_path, '.env')
load_dotenv(env_path)

# Affichage de debug (optionnel, à enlever en production)
if os.getenv('APP_DEBUG', 'False').lower() == 'true':
    print(f"🔍 Chemin application : {application_path}")
    print(f"📄 Fichier .env existe : {os.path.exists(env_path)}")
    print(f"🗄️  Base de données    : {os.getenv('DB_NAME', 'N/A')}")

# ════════════════════════════════════════════════════════════════════════════

from PyQt6.QtWidgets import QApplication, QMessageBox
from database.connection import db       # Singleton de connexion à la base de données
from views.login_view import LoginView   # Fenêtre de connexion utilisateur


def main():
    # --- Initialisation de l'application Qt ---
    app = QApplication(sys.argv)
    app.setApplicationName("SGC - Systeme de Gestion Commerciale -")
    app.setStyle("Fusion")  # Thème visuel uniforme sur tous les OS
    
    # --- Vérification de la connexion à la base de données ---
    # Si la connexion échoue, on informe l'utilisateur et on quitte proprement
    if not db.connect():
        QMessageBox.critical(
            None,
            "Erreur de connexion",
            "Impossible de se connecter a la base de données.\n\n"
            "Verifiez que MySQL a démarre et que le fichier .env. est correct\n\n"
            f"Chemin recherché : {env_path}"
        )
        sys.exit(1)  # Code de sortie 1 = erreur
    
    # --- Affichage de la fenêtre de connexion ---
    login = LoginView()
    
    def on_login_accepted():
        """
        Callback déclenché lorsque l'utilisateur s'authentifie avec succès.
        La MainWindow est importée.
        """
        from views.main_window import MainWindow
        app._main_window = MainWindow()
        app._main_window.showMaximized()  # Ouverture en plein écran
    
    # Connexion du signal Qt : login réussi → ouverture de la fenêtre principale
    login.accepted.connect(on_login_accepted)
    
    # Affichage bloquant de la boîte de dialogue de login (mode modal)
    login.exec()
    
    # --- Lancement de la boucle événementielle Qt ---
    # sys.exit() propage le code de retour de l'application au système
    sys.exit(app.exec())


if __name__ == "__main__":
    # Garantit que main() n'est appelé que si le script est exécuté directement
    main()
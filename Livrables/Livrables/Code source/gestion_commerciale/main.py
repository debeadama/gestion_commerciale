# main.py
# Point d'entrée principal de l'application SGC (Système de Gestion Commerciale)

import sys
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
            "Verifiez que MySQL a démarre et que le fichier .env. est correct"
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
    #
    main()
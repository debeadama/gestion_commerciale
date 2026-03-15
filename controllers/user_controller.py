# controllers/user_controller.py
"""
Controleur Utilisateur.
Logique metier pour la gestion des utilisateurs.
"""

import bcrypt
from models.user import UserModel
import logging

logger = logging.getLogger(__name__)


class UserController:

    # ── Lecture ───────────────────────────────────────────────

    @staticmethod
    def get_all() -> list:
        """Retourne tous les utilisateurs avec leurs infos (sans mot de passe)."""
        return UserModel.get_all() or []

    @staticmethod
    def get_by_id(user_id: int) -> dict:
        """Retourne un utilisateur par son ID."""
        return UserModel.get_by_id(user_id)

    # ── Creation ──────────────────────────────────────────────

    @staticmethod
    def create(username: str, password: str, role: str,
               nom_complet: str = '', email: str = '') -> tuple:
        """
        Cree un nouvel utilisateur.
        Returns: (True, user_id) ou (False, message_erreur)
        """
        if UserModel.find_by_username(username):
            return False, f"Le nom d'utilisateur '{username}' est deja utilise."

        if len(password) < 6:
            return False, "Le mot de passe doit contenir au moins 6 caracteres."

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        try:
            uid = UserModel.create(username, hashed, role, nom_complet, email)
            logger.info(f"Utilisateur cree : {username} ({role})")
            return True, uid
        except Exception as e:
            logger.error(f"Erreur creation utilisateur : {e}")
            return False, str(e)

    # ── Modification ──────────────────────────────────────────

    @staticmethod
    def update(user_id: int, username: str, role: str,
               nom_complet: str = '', email: str = '') -> tuple:
        """Met a jour les infos d'un utilisateur (hors mot de passe)."""
        if UserModel.find_by_username(username, exclude_id=user_id):
            return False, f"Le nom d'utilisateur '{username}' est deja pris."
        try:
            UserModel.update(user_id, username, role, nom_complet, email)
            return True, "Utilisateur mis a jour."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def change_password(user_id: int, new_password: str) -> tuple:
        """Change le mot de passe d'un utilisateur."""
        if len(new_password) < 6:
            return False, "Le mot de passe doit contenir au moins 6 caracteres."
        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        try:
            UserModel.change_password(user_id, hashed)
            return True, "Mot de passe modifie."
        except Exception as e:
            return False, str(e)

    # ── Suppression ───────────────────────────────────────────

    @staticmethod
    def delete(user_id: int, current_user_id: int) -> tuple:
        """
        Supprime un utilisateur.
        Interdit de supprimer son propre compte.
        """
        if user_id == current_user_id:
            return False, "Vous ne pouvez pas supprimer votre propre compte."
        try:
            UserModel.delete(user_id)
            return True, "Utilisateur supprime."
        except Exception as e:
            return False, str(e)

    # ── Statistiques ──────────────────────────────────────────

    @staticmethod
    def get_stats(user_id: int) -> dict:
        """Retourne les statistiques de ventes d'un vendeur."""
        return UserModel.get_stats(user_id)

    @staticmethod
    def get_vendeurs() -> list:
        """Retourne la liste des utilisateurs pour le filtre vendeur."""
        return UserModel.get_all()

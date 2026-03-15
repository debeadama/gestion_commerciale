# controllers/user_controller.py
"""
Controleur Utilisateur.

Logique metier pour la gestion des utilisateurs et des mots de passe.
"""

import logging

import bcrypt

from models.user import UserModel

logger = logging.getLogger(__name__)


class UserController:
    """Controleur pour la gestion des utilisateurs de l'application."""

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    @staticmethod
    def get_all() -> list:
        """
        Retourne tous les utilisateurs sans leurs mots de passe.

        Returns:
            list: Liste des utilisateurs ou liste vide.
        """
        return UserModel.get_all() or []

    @staticmethod
    def get_by_id(user_id: int) -> dict:
        """
        Retourne un utilisateur par son ID.

        Args:
            user_id (int): Identifiant de l'utilisateur.

        Returns:
            dict: Donnees de l'utilisateur ou None.
        """
        return UserModel.get_by_id(user_id)

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    @staticmethod
    def create(
        username: str,
        password: str,
        role: str,
        nom_complet: str = '',
        email: str = ''
    ) -> tuple:
        """
        Cree un nouvel utilisateur apres validation.

        Args:
            username (str): Nom d'utilisateur unique.
            password (str): Mot de passe en clair (min. 6 caracteres).
            role (str): Role attribue ('admin', 'manager', 'vendeur').
            nom_complet (str): Nom complet de l'utilisateur (optionnel).
            email (str): Adresse email (optionnelle).

        Returns:
            tuple: (True, user_id) ou (False, message_erreur).
        """
        if UserModel.find_by_username(username):
            return (
                False,
                f"Le nom d'utilisateur '{username}' est deja utilise."
            )

        if len(password) < 6:
            return (
                False,
                "Le mot de passe doit contenir au moins 6 caracteres."
            )

        hashed = bcrypt.hashpw(
            password.encode(), bcrypt.gensalt()
        ).decode()

        try:
            uid = UserModel.create(
                username, hashed, role, nom_complet, email
            )
            logger.info(f"Utilisateur cree : {username} ({role})")
            return True, uid
        except Exception as e:
            logger.error(f"Erreur creation utilisateur : {e}")
            return False, str(e)

    # ------------------------------------------------------------------
    # Modification
    # ------------------------------------------------------------------

    @staticmethod
    def update(
        user_id: int,
        username: str,
        role: str,
        nom_complet: str = '',
        email: str = ''
    ) -> tuple:
        """
        Met a jour les informations d'un utilisateur (hors mot de passe).

        Args:
            user_id (int): Identifiant de l'utilisateur.
            username (str): Nouveau nom d'utilisateur.
            role (str): Nouveau role.
            nom_complet (str): Nouveau nom complet (optionnel).
            email (str): Nouvelle adresse email (optionnelle).

        Returns:
            tuple: (True, message) ou (False, message_erreur).
        """
        if UserModel.find_by_username(username, exclude_id=user_id):
            return (
                False,
                f"Le nom d'utilisateur '{username}' est deja pris."
            )
        try:
            UserModel.update(user_id, username, role, nom_complet, email)
            return True, "Utilisateur mis a jour."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def change_password(user_id: int, new_password: str) -> tuple:
        """
        Change le mot de passe d'un utilisateur.

        Args:
            user_id (int): Identifiant de l'utilisateur.
            new_password (str): Nouveau mot de passe en clair.

        Returns:
            tuple: (True, message) ou (False, message_erreur).
        """
        if len(new_password) < 6:
            return (
                False,
                "Le mot de passe doit contenir au moins 6 caracteres."
            )
        hashed = bcrypt.hashpw(
            new_password.encode(), bcrypt.gensalt()
        ).decode()
        try:
            UserModel.change_password(user_id, hashed)
            return True, "Mot de passe modifie."
        except Exception as e:
            return False, str(e)

    # ------------------------------------------------------------------
    # Suppression
    # ------------------------------------------------------------------

    @staticmethod
    def delete(user_id: int, current_user_id: int) -> tuple:
        """
        Supprime un utilisateur.

        La suppression de son propre compte est interdite.

        Args:
            user_id (int): Identifiant de l'utilisateur a supprimer.
            current_user_id (int): Identifiant de l'utilisateur connecte.

        Returns:
            tuple: (True, message) ou (False, message_erreur).
        """
        if user_id == current_user_id:
            return (
                False,
                "Vous ne pouvez pas supprimer votre propre compte."
            )
        try:
            UserModel.delete(user_id)
            return True, "Utilisateur supprime."
        except Exception as e:
            return False, str(e)

    # ------------------------------------------------------------------
    # Statistiques
    # ------------------------------------------------------------------

    @staticmethod
    def get_stats(user_id: int) -> dict:
        """
        Retourne les statistiques de ventes d'un vendeur.

        Args:
            user_id (int): Identifiant du vendeur.

        Returns:
            dict: Nombre de ventes, CA total, derniere vente.
        """
        return UserModel.get_stats(user_id)

    @staticmethod
    def get_vendeurs() -> list:
        """
        Retourne la liste de tous les utilisateurs pour le filtre vendeur.

        Returns:
            list: Liste des utilisateurs.
        """
        return UserModel.get_all()

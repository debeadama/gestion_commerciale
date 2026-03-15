# controllers/auth_controller.py
"""Gere la session utilisateur et les permissions."""

import logging
from datetime import datetime

from models.user import UserModel

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Gere l'utilisateur connecte et ses droits.

    Classe entierement statique (pas besoin de l'instancier).
    """

    _current_user = None  # Donnees de l'utilisateur connecte
    _login_time = None    # Heure de connexion

    # Permissions par role — 'all' = acces complet (admin)
    PERMISSIONS = {
        'admin': ['all'],
        'manager': [
            'view_clients',
            'edit_clients',
            'view_products',
            'edit_products',
            'view_sales',
            'create_sales',
            'view_reports',
        ],
        'vendeur': [
            'view_clients',
            'edit_clients',
            'view_products',
            'create_sales',
            'view_sales',
        ],
    }

    # ------------------------------------------------------------------
    # Connexion / Deconnexion
    # ------------------------------------------------------------------

    @classmethod
    def login(cls, username: str, password: str) -> tuple[bool, str]:
        """
        Tente de connecter un utilisateur.

        Args:
            username (str): Nom d'utilisateur.
            password (str): Mot de passe en clair.

        Returns:
            tuple: (True, message_succes) ou (False, message_erreur).
        """
        user = UserModel.get_by_username(username)
        if not user:
            logger.warning(
                f"Connexion echouee — utilisateur inconnu : {username}"
            )
            return False, "Nom d'utilisateur ou mot de passe incorrect."

        if not UserModel.verify_password(password, user['password_hash']):
            logger.warning(
                f"Connexion echouee — mauvais mot de passe : {username}"
            )
            return False, "Nom d'utilisateur ou mot de passe incorrect."

        cls._current_user = user
        cls._login_time = datetime.now()
        logger.info(f"Connexion : {username} ({user['role']})")
        return True, f"Bienvenue, {username} !"

    @classmethod
    def logout(cls) -> None:
        """Ferme la session de l'utilisateur connecte."""
        if cls._current_user:
            logger.info(f"Deconnexion : {cls._current_user['username']}")
        cls._current_user = None
        cls._login_time = None

    # ------------------------------------------------------------------
    # Informations session
    # ------------------------------------------------------------------

    @classmethod
    def is_logged_in(cls) -> bool:
        """Retourne True si un utilisateur est connecte."""
        return cls._current_user is not None

    @classmethod
    def get_current_user(cls) -> dict | None:
        """Retourne le dictionnaire de l'utilisateur connecte ou None."""
        return cls._current_user

    @classmethod
    def get_role(cls) -> str | None:
        """Retourne le role de l'utilisateur connecte ou None."""
        return cls._current_user['role'] if cls._current_user else None

    @classmethod
    def get_username(cls) -> str | None:
        """Retourne le nom d'utilisateur connecte ou None."""
        return cls._current_user['username'] if cls._current_user else None

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    @classmethod
    def has_permission(cls, permission: str) -> bool:
        """
        Verifie si l'utilisateur connecte possede une permission donnee.

        Args:
            permission (str): Identifiant de la permission a verifier.
                Ex : 'view_reports', 'edit_clients'.

        Returns:
            bool: True si la permission est accordee, False sinon.

        Example:
            if SessionManager.has_permission('view_reports'):
                # afficher les rapports
        """
        if not cls._current_user:
            return False
        role = cls._current_user['role']
        perms = cls.PERMISSIONS.get(role, [])
        return 'all' in perms or permission in perms

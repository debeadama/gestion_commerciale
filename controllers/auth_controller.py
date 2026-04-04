# controllers/auth_controller.py
"""Gere la session utilisateur et les permissions."""

import logging
import time
from datetime import datetime

from models.user import UserModel

logger = logging.getLogger(__name__)

# Rate-limiting : max tentatives avant blocage temporaire
_MAX_ATTEMPTS = 5
_BLOCK_DURATION = 30  # secondes


class SessionManager:
    """
    Gere l'utilisateur connecte et ses droits.

    Classe entierement statique (pas besoin de l'instancier).
    """

    _current_user = None  # Donnees de l'utilisateur connecte
    _login_time = None    # Heure de connexion

    # {username: {'attempts': int, 'blocked_until': float}}
    _login_attempts: dict = {}

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
    def _check_rate_limit(cls, username: str) -> tuple[bool, str]:
        """Verifie si le compte est temporairement bloque. Retourne (ok, msg)."""
        entry = cls._login_attempts.get(username)
        if not entry:
            return True, ""
        blocked_until = entry.get('blocked_until', 0)
        if time.time() < blocked_until:
            remaining = int(blocked_until - time.time())
            return False, (
                f"Compte temporairement bloque. "
                f"Reessayez dans {remaining} seconde(s)."
            )
        return True, ""

    @classmethod
    def _record_failed_attempt(cls, username: str) -> None:
        """Enregistre une tentative echouee et bloque si necessaire."""
        entry = cls._login_attempts.setdefault(
            username, {'attempts': 0, 'blocked_until': 0}
        )
        entry['attempts'] += 1
        if entry['attempts'] >= _MAX_ATTEMPTS:
            entry['blocked_until'] = time.time() + _BLOCK_DURATION
            entry['attempts'] = 0
            logger.warning(
                f"Compte bloque apres {_MAX_ATTEMPTS} tentatives : {username}"
            )

    @classmethod
    def _reset_attempts(cls, username: str) -> None:
        """Reinitialise le compteur apres une connexion reussie."""
        cls._login_attempts.pop(username, None)

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
        ok, msg = cls._check_rate_limit(username)
        if not ok:
            return False, msg

        user = UserModel.get_by_username(username)
        if not user:
            cls._record_failed_attempt(username)
            logger.warning(
                f"Connexion echouee — utilisateur inconnu : {username}"
            )
            return False, "Nom d'utilisateur ou mot de passe incorrect."

        if not UserModel.verify_password(password, user['password_hash']):
            cls._record_failed_attempt(username)
            logger.warning(
                f"Connexion echouee — mauvais mot de passe : {username}"
            )
            return False, "Nom d'utilisateur ou mot de passe incorrect."

        cls._reset_attempts(username)
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

# controllers/auth_controller.py
# Gère la session utilisateur et les permissions

from models.user import UserModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Gère l'utilisateur connecté et ses droits.
    Classe entièrement statique (pas besoin de l'instancier).
    """

    _current_user = None   # Données de l'utilisateur connecté
    _login_time   = None   # Heure de connexion (pour le timeout)

    # Permissions par rôle
    # 'all' = accès complet (admin)
    PERMISSIONS = {
        'admin':   ['all'],
        'manager': [
            'view_clients', 'edit_clients',
            'view_products', 'edit_products',
            'view_sales', 'create_sales',
            'view_reports',
        ],
        'vendeur': [
            'view_clients', 'edit_clients',
            'view_products',
            'create_sales', 'view_sales',
        ],
    }

    # ----------------------------------------------------------
    # Connexion / Déconnexion
    # ----------------------------------------------------------

    @classmethod
    def login(cls, username: str, password: str) -> tuple[bool, str]:
        """
        Tente de connecter un utilisateur.

        Returns:
            (True, "message succès") ou (False, "message erreur")
        """
        # 1. Chercher l'utilisateur
        user = UserModel.get_by_username(username)
        if not user:
            logger.warning(f"Connexion échouée — utilisateur inconnu : {username}")
            return False, "Nom d'utilisateur ou mot de passe incorrect"

        # 2. Vérifier le mot de passe
        if not UserModel.verify_password(password, user['password_hash']):
            logger.warning(f"Connexion échouée — mauvais mot de passe : {username}")
            return False, "Nom d'utilisateur ou mot de passe incorrect"

        # 3. Ouvrir la session
        cls._current_user = user
        cls._login_time   = datetime.now()
        logger.info(f"✅ Connexion : {username} ({user['role']})")
        return True, f"Bienvenue, {username} !"

    @classmethod
    def logout(cls):
        """Ferme la session de l'utilisateur."""
        if cls._current_user:
            logger.info(f"Déconnexion : {cls._current_user['username']}")
        cls._current_user = None
        cls._login_time   = None

    # ----------------------------------------------------------
    # Informations session
    # ----------------------------------------------------------

    @classmethod
    def is_logged_in(cls) -> bool:
        return cls._current_user is not None

    @classmethod
    def get_current_user(cls) -> dict | None:
        return cls._current_user

    @classmethod
    def get_role(cls) -> str | None:
        return cls._current_user['role'] if cls._current_user else None

    @classmethod
    def get_username(cls) -> str | None:
        return cls._current_user['username'] if cls._current_user else None

    # ----------------------------------------------------------
    # Permissions
    # ----------------------------------------------------------

    @classmethod
    def has_permission(cls, permission: str) -> bool:
        """
        Vérifie si l'utilisateur connecté a une permission donnée.

        Exemple d'utilisation :
            if SessionManager.has_permission('view_reports'):
                # afficher les rapports
        """
        if not cls._current_user:
            return False
        role  = cls._current_user['role']
        perms = cls.PERMISSIONS.get(role, [])
        return 'all' in perms or permission in perms
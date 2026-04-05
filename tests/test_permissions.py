# test_permissions.py
# Tests unitaires pour SessionManager - gestion des sessions et permissions
# Lancer avec : python -m pytest test_permissions.py -v

import pytest
from unittest.mock import patch  # noqa: E402
from datetime import datetime  # noqa: E402


#
# Helpers / Fixtures
#

def make_user(username="alice", role="vendeur", password_hash="hashed_pw"):
    return {"username": username, "role": role, "password_hash": password_hash}


@pytest.fixture(autouse=True)
def reset_session():
    """Remet la session à zéro avant chaque test."""
    from controllers.auth_controller import SessionManager
    SessionManager._current_user = None
    SessionManager._login_time = None
    yield
    SessionManager._current_user = None
    SessionManager._login_time = None


@pytest.fixture
def vendeur():
    from controllers.auth_controller import SessionManager
    SessionManager._current_user = make_user(username="alice", role="vendeur")
    SessionManager._login_time = datetime.now()
    return SessionManager


@pytest.fixture
def manager():
    from controllers.auth_controller import SessionManager
    SessionManager._current_user = make_user(username="bob", role="manager")
    SessionManager._login_time = datetime.now()
    return SessionManager


@pytest.fixture
def admin():
    from controllers.auth_controller import SessionManager
    SessionManager._current_user = make_user(username="root", role="admin")
    SessionManager._login_time = datetime.now()
    return SessionManager


#
# 1. Login
#

class TestLogin:

    @patch("controllers.auth_controller.UserModel")
    def test_utilisateur_inconnu(self, mock_model):
        from controllers.auth_controller import SessionManager
        mock_model.get_by_username.return_value = None
        ok, msg = SessionManager.login("inconnu", "mdp")
        assert ok is False
        assert not SessionManager.is_logged_in()

    @patch("controllers.auth_controller.UserModel")
    def test_mauvais_mot_de_passe(self, mock_model):
        from controllers.auth_controller import SessionManager
        mock_model.get_by_username.return_value = make_user()
        mock_model.verify_password.return_value = False
        ok, msg = SessionManager.login("alice", "mauvais")
        assert ok is False
        assert not SessionManager.is_logged_in()

    @patch("controllers.auth_controller.UserModel")
    def test_login_succes(self, mock_model):
        from controllers.auth_controller import SessionManager
        mock_model.get_by_username.return_value = make_user()
        mock_model.verify_password.return_value = True
        ok, msg = SessionManager.login("alice", "bon_mdp")
        assert ok is True
        assert SessionManager.is_logged_in()
        assert SessionManager.get_username() == "alice"
        assert SessionManager.get_role() == "vendeur"


#
# 2. Logout
#

class TestLogout:

    def test_logout_vide_la_session(self, vendeur):
        vendeur.logout()
        assert not vendeur.is_logged_in()
        assert vendeur.get_current_user() is None

    def test_logout_sans_session_ne_plante_pas(self):
        from controllers.auth_controller import SessionManager
        SessionManager.logout()


#
# 3. Permissions - vendeur
#

class TestVendeur:

    @pytest.mark.parametrize("perm",
                             ["view_clients",
                              "edit_clients",
                              "view_products",
                              "create_sales",
                              "view_sales"])
    def test_permissions_autorisees(self, vendeur, perm):
        assert vendeur.has_permission(perm) is True

    @pytest.mark.parametrize("perm",
                             ["edit_products",
                              "view_reports",
                              "admin_panel"])
    def test_permissions_interdites(self, vendeur, perm):
        assert vendeur.has_permission(perm) is False


#
# 4. Permissions - manager
#

class TestManager:

    @pytest.mark.parametrize("perm",
                             ["view_clients",
                              "edit_clients",
                              "view_products",
                              "edit_products",
                              "view_sales",
                              "create_sales",
                              "view_reports"])
    def test_permissions_autorisees(self, manager, perm):
        assert manager.has_permission(perm) is True

    @pytest.mark.parametrize("perm", ["admin_panel", "manage_users"])
    def test_permissions_interdites(self, manager, perm):
        assert manager.has_permission(perm) is False


#
# 5. Permissions - admin
#

class TestAdmin:

    @pytest.mark.parametrize("perm",
                             ["view_clients",
                              "edit_products",
                              "view_reports",
                              "admin_panel",
                              "permission_inventee"])
    def test_admin_a_tout(self, admin, perm):
        assert admin.has_permission(perm) is True


#
# 6. Utilisateur déconnecté
#

class TestDeconnecte:

    @pytest.mark.parametrize("perm",
                             ["view_clients",
                              "view_reports",
                              "admin_panel"])
    def test_aucune_permission(self, perm):
        from controllers.auth_controller import SessionManager
        assert SessionManager.has_permission(perm) is False

"""
tests/test_login.py
--------------------
Tests unitaires de la fonction SessionManager.login()

Architecture réelle : SessionManager est une classe entièrement statique.
login() appelle UserModel.get_by_username() et UserModel.verify_password()
directement — on les mocke avec @patch pour ne pas toucher la base.

Pour exécuter :
    python tests/test_login.py
    ou
    python -m pytest tests/test_login.py -v
"""

from controllers.auth_controller import SessionManager  # noqa: E402
from unittest.mock import patch  # noqa: E402
import unittest
import sys
import os

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '..')))


class TestLogin(unittest.TestCase):
    """
    Tests de SessionManager.login().
    On mocke les deux méthodes de UserModel que login() appelle :
      - UserModel.get_by_username()
      - UserModel.verify_password()
    """

    def tearDown(self):
        """Réinitialise la session après chaque test."""
        SessionManager.logout()

    # ── TC-A-01 ─────────────────────────────────────────────
    @patch('controllers.auth_controller.UserModel.get_by_username',
           return_value=None)
    def test_username_vide_retourne_erreur(self, mock_get):
        """
        TC-A-01 : login() avec username vide doit retourner (False, message).
        Le code cherche en base et ne trouve rien → accès refusé.
        """
        ok, msg = SessionManager.login('', 'uvci@2026')

        self.assertFalse(ok, "login avec username vide doit retourner False")
        self.assertIsInstance(msg, str)
        self.assertFalse(SessionManager.is_logged_in())

    # ── TC-A-02 ─────────────────────────────────────────────
    @patch('controllers.auth_controller.UserModel.verify_password',
           return_value=False)
    @patch('controllers.auth_controller.UserModel.get_by_username')
    def test_password_vide_retourne_erreur(self, mock_get, mock_verify):
        """
        TC-A-02 : login() avec password vide doit retourner (False, message).
        Le code trouve l'utilisateur mais verify_password échoue.
        """
        mock_get.return_value = {
            'id': 1, 'username': 'admin',
            'password_hash': '$2b$12$fakehash',
            'role': 'admin', 'is_active': 1
        }

        ok, msg = SessionManager.login('admin', '')

        self.assertFalse(ok, "login avec password vide doit retourner False")
        self.assertIsInstance(msg, str)
        self.assertFalse(SessionManager.is_logged_in())

    # ── TC-A-03 ─────────────────────────────────────────────
    @patch('controllers.auth_controller.UserModel.get_by_username',
           return_value=None)
    def test_utilisateur_inexistant_retourne_erreur(self, mock_get):
        """
        TC-A-03 : login() avec un username inconnu doit retourner
        (False, message). get_by_username() renvoie None.
        """
        ok, msg = SessionManager.login('utilisateur_inconnu', 'uvci@2026')

        self.assertFalse(ok)
        self.assertIsInstance(msg, str)
        mock_get.assert_called_once_with('utilisateur_inconnu')

    # ── TC-A-04 ─────────────────────────────────────────────
    @patch('controllers.auth_controller.UserModel.verify_password',
           return_value=False)
    @patch('controllers.auth_controller.UserModel.get_by_username')
    def test_mauvais_mot_de_passe_retourne_erreur(self, mock_get, mock_verify):
        """
        TC-A-04 : login() avec un mauvais mot de passe doit retourner
        (False, message). verify_password() renvoie False.
        """
        mock_get.return_value = {
            'id': 1, 'username': 'admin',
            'password_hash': '$2b$12$fakehash',
            'role': 'admin', 'is_active': 1
        }

        ok, msg = SessionManager.login('admin', 'mauvais_mdp')

        self.assertFalse(ok)
        mock_verify.assert_called_once()

    # ── TC-A-05 ─────────────────────────────────────────────
    @patch('controllers.auth_controller.UserModel.verify_password',
           return_value=True)
    @patch('controllers.auth_controller.UserModel.get_by_username')
    def test_connexion_reussie_ouvre_session(self, mock_get, mock_verify):
        """
        TC-A-05 : login() avec de bons identifiants doit retourner
        (True, message) et enregistrer l'utilisateur dans la session.
        """
        mock_get.return_value = {
            'id': 1, 'username': 'admin',
            'password_hash': '$2b$12$fakehash',
            'role': 'admin', 'is_active': 1
        }

        ok, msg = SessionManager.login('admin', 'uvci@2026')

        self.assertTrue(ok, "Une connexion valide doit retourner True")
        self.assertIsInstance(msg, str)

        # La session doit être ouverte
        self.assertTrue(SessionManager.is_logged_in())
        self.assertEqual(SessionManager.get_username(), 'admin')
        self.assertEqual(SessionManager.get_role(), 'admin')


if __name__ == '__main__':
    unittest.main(verbosity=2)

"""
tests/test_user_controller.py
------------------------------
Tests unitaires de UserController.

Méthodes testées :
  - create()  : username existant, password trop court,
    succes, exception
  - update()          : username déjà pris, succès, exception
  - change_password() : password trop court, succès, exception
  - delete()          : suppression de son propre compte, succès, exception

Architecture : méthodes @staticmethod — UserModel et bcrypt sont
mockés avec @patch.

Pour exécuter :
    python tests/test_user_controller.py
    ou
    python -m pytest tests/test_user_controller.py -v
"""

from controllers.user_controller import UserController  # noqa: E402
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



# TEST create()


class TestUserControllerCreate(unittest.TestCase):
    """Tests de UserController.create()."""

    # ── TC-UC-01 ─────────────────────────────────────────────
    @patch('controllers.user_controller.UserModel.find_by_username',
           return_value={'id': 1, 'username': 'admin'})
    def test_username_existant_retourne_erreur(self, mock_find):
        """
        TC-UC-01 : create() avec un username déjà utilisé doit
        retourner (False, message) sans créer de compte.
        """
        ok, msg = UserController.create(
            username='admin', password='motdepasse',
            role='vendeur'
        )

        self.assertFalse(ok)
        self.assertIn('deja utilise', msg.lower())
        mock_find.assert_called_once_with('admin')

    # ── TC-UC-02 ─────────────────────────────────────────────
    @patch('controllers.user_controller.UserModel.find_by_username',
           return_value=None)
    def test_password_trop_court_retourne_erreur(self, mock_find):
        """
        TC-UC-02 : create() avec un password de moins de 6 caractères
        doit retourner (False, message) sans hacher ni insérer.
        """
        ok, msg = UserController.create(
            username='nouveau', password='abc',
            role='vendeur'
        )

        self.assertFalse(ok)
        self.assertIn('6', msg)

    # ── TC-UC-03 ─────────────────────────────────────────────
    @patch('controllers.user_controller.UserModel.create', return_value=5)
    @patch('controllers.user_controller.UserModel.find_by_username',
           return_value=None)
    def test_creation_reussie_retourne_id(self, mock_find, mock_create):
        """
        TC-UC-03 : create() avec des données valides doit retourner
        (True, user_id) et appeler UserModel.create() avec un hash bcrypt.
        """
        ok, uid = UserController.create(
            username='vendeur1', password='uvci@2026',
            role='vendeur', nom_complet='Kouassi Jean'
        )

        self.assertTrue(ok)
        self.assertEqual(uid, 5)
        mock_create.assert_called_once()

        # Le mot de passe transmis au modèle doit être un hash bcrypt
        args = mock_create.call_args[0]
        hashed = args[1]
        self.assertTrue(hashed.startswith('$2b$'),
                        "Le mot de passe doit être haché en bcrypt")

    # ── TC-UC-04 ─────────────────────────────────────────────
    @patch('controllers.user_controller.UserModel.create',
           side_effect=Exception("Erreur SQL"))
    @patch('controllers.user_controller.UserModel.find_by_username',
           return_value=None)
    def test_exception_bdd_retourne_erreur(self, mock_find, mock_create):
        """
        TC-UC-04 : Si UserModel.create() lève une exception,
        create() doit retourner (False, message) sans la propager.
        """
        ok, msg = UserController.create(
            username='test', password='motdepasse123',
            role='vendeur'
        )

        self.assertFalse(ok)
        self.assertIsInstance(msg, str)

    # ── TC-UC-05 ─────────────────────────────────────────────
    @patch('controllers.user_controller.UserModel.find_by_username',
           return_value=None)
    def test_password_exactement_6_caracteres_accepte(self, mock_find):
        """
        TC-UC-05 : create() avec un password de exactement 6 caractères
        doit passer la validation (limite basse acceptée).
        """
        patch_path = 'controllers.user_controller.UserModel.create'
        with patch(patch_path, return_value=6):
            ok, uid = UserController.create(
                username='user2', password='abc123',
                role='vendeur'
            )

        self.assertTrue(ok)
        self.assertEqual(uid, 6)



# TEST update()


class TestUserControllerUpdate(unittest.TestCase):
    """Tests de UserController.update()."""

    # ── TC-UU-01 ─────────────────────────────────────────────
    @patch('controllers.user_controller.UserModel.find_by_username',
           return_value={'id': 2, 'username': 'manager1'})
    def test_username_deja_pris_retourne_erreur(self, mock_find):
        """
        TC-UU-01 : update() avec un username déjà utilisé par un
        autre utilisateur doit retourner (False, message).
        """
        ok, msg = UserController.update(
            user_id=3, username='manager1', role='vendeur'
        )

        self.assertFalse(ok)
        self.assertIn('deja pris', msg.lower())
        mock_find.assert_called_once_with('manager1', exclude_id=3)

    # ── TC-UU-02 ─────────────────────────────────────────────
    @patch('controllers.user_controller.UserModel.update')
    @patch('controllers.user_controller.UserModel.find_by_username',
           return_value=None)
    def test_update_reussi(self, mock_find, mock_update):
        """
        TC-UU-02 : update() avec des données valides doit
        retourner (True, message) et appeler UserModel.update().
        """
        ok, msg = UserController.update(
            user_id=3, username='vendeur_new',
            role='vendeur', nom_complet='Bamba Awa'
        )

        self.assertTrue(ok)
        mock_update.assert_called_once_with(
            3, 'vendeur_new', 'vendeur', 'Bamba Awa', ''
        )

    # ── TC-UU-03 ─────────────────────────────────────────────
    @patch('controllers.user_controller.UserModel.update',
           side_effect=Exception("Erreur SQL"))
    @patch('controllers.user_controller.UserModel.find_by_username',
           return_value=None)
    def test_exception_bdd_retourne_erreur(self, mock_find, mock_update):
        """
        TC-UU-03 : Si UserModel.update() lève une exception,
        update() doit retourner (False, message).
        """
        ok, msg = UserController.update(
            user_id=3, username='vendeur_new', role='vendeur'
        )

        self.assertFalse(ok)
        self.assertIsInstance(msg, str)



# TEST change_password()


class TestUserControllerChangePassword(unittest.TestCase):
    """Tests de UserController.change_password()."""

    # ── TC-CP-01 ─────────────────────────────────────────────
    def test_nouveau_password_trop_court_retourne_erreur(self):
        """
        TC-CP-01 : change_password() avec un password < 6 caractères
        doit retourner (False, message) sans toucher la base.
        """
        ok, msg = UserController.change_password(user_id=1, new_password='abc')

        self.assertFalse(ok)
        self.assertIn('6', msg)

    # ── TC-CP-02 ─────────────────────────────────────────────
    @patch('controllers.user_controller.UserModel.change_password')
    def test_changement_reussi_hash_bcrypt(self, mock_change):
        """
        TC-CP-02 : change_password() avec un mot de passe valide doit
        retourner (True, message) et transmettre un hash bcrypt au modèle.
        """
        ok, msg = UserController.change_password(
            user_id=1, new_password='nouveauMdp2026'
        )

        self.assertTrue(ok)
        mock_change.assert_called_once()

        # Le hash transmis doit être un hash bcrypt
        hashed = mock_change.call_args[0][1]
        self.assertTrue(
            hashed.startswith('$2b$'),
            "Le nouveau mot de passe doit être haché")

    # ── TC-CP-03 ─────────────────────────────────────────────
    @patch('controllers.user_controller.UserModel.change_password',
           side_effect=Exception("Connexion perdue"))
    def test_exception_bdd_retourne_erreur(self, mock_change):
        """
        TC-CP-03 : Si UserModel.change_password() lève une exception,
        change_password() doit retourner (False, message).
        """
        ok, msg = UserController.change_password(
            user_id=1, new_password='validPassword'
        )

        self.assertFalse(ok)
        self.assertIsInstance(msg, str)



# TEST delete()


class TestUserControllerDelete(unittest.TestCase):
    """Tests de UserController.delete()."""

    # ── TC-UD-01 ─────────────────────────────────────────────
    def test_suppression_propre_compte_retourne_erreur(self):
        """
        TC-UD-01 : delete() avec user_id == current_user_id doit
        retourner (False, message) — un admin ne peut pas se supprimer.
        """
        ok, msg = UserController.delete(user_id=1, current_user_id=1)

        self.assertFalse(ok)
        self.assertIn('propre compte', msg.lower())

    # ── TC-UD-02 ─────────────────────────────────────────────
    @patch('controllers.user_controller.UserModel.delete')
    def test_suppression_autre_compte_reussit(self, mock_delete):
        """
        TC-UD-02 : delete() avec user_id != current_user_id doit
        retourner (True, message) et appeler UserModel.delete().
        """
        ok, msg = UserController.delete(user_id=3, current_user_id=1)

        self.assertTrue(ok)
        mock_delete.assert_called_once_with(3)

    # ── TC-UD-03 ─────────────────────────────────────────────
    @patch('controllers.user_controller.UserModel.delete',
           side_effect=Exception("Erreur SQL"))
    def test_exception_bdd_retourne_erreur(self, mock_delete):
        """
        TC-UD-03 : Si UserModel.delete() lève une exception,
        delete() doit retourner (False, message).
        """
        ok, msg = UserController.delete(user_id=3, current_user_id=1)

        self.assertFalse(ok)
        self.assertIsInstance(msg, str)

    # ── TC-UD-04 ─────────────────────────────────────────────
    @patch('controllers.user_controller.UserModel.delete')
    def test_suppression_transmet_bon_id(self, mock_delete):
        """
        TC-UD-04 : delete() doit transmettre l'ID exact à UserModel.delete().
        """
        UserController.delete(user_id=7, current_user_id=1)

        mock_delete.assert_called_once_with(7)



# POINT D'ENTRÉE


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestUserControllerCreate))
    suite.addTests(loader.loadTestsFromTestCase(TestUserControllerUpdate))
    suite.addTests(loader.loadTestsFromTestCase(
        TestUserControllerChangePassword))
    suite.addTests(loader.loadTestsFromTestCase(TestUserControllerDelete))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

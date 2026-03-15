"""
tests/test_model_user.py
-------------------------
Tests unitaires de UserModel.

Méthodes testées :
  - get_all()           : retourne liste sans mot de passe
  - get_by_id()         : trouvé, None si absent
  - get_by_username()   : trouvé avec hash, None si absent
  - verify_password()   : mot de passe correct, incorrect, exception
  - find_by_username()  : trouvé, None, avec/sans exclude_id
  - create()            : retourne ID, bons paramètres transmis
  - update()            : retourne True, bons paramètres
  - change_password()   : retourne True, hash transmis
  - delete()            : retourne True, bon ID transmis
  - get_stats()         : retourne dict, {} si None

Architecture : méthodes @staticmethod — db est mocké avec @patch.
verify_password() utilise bcrypt réel (pas de mock nécessaire).

Pour exécuter :
    python tests/test_model_user.py
    ou
    python -m pytest tests/test_model_user.py -v
"""

from models.user import UserModel  # noqa: E402
from unittest.mock import patch  # noqa: E402
import unittest
import sys
import os
import bcrypt

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '..')))



# TEST get_all()


class TestUserModelGetAll(unittest.TestCase):

    # ── TM-US-GA-01 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_get_all_retourne_liste(self, mock_db):
        """
        TM-US-GA-01 : get_all() doit appeler db.execute_query()
        et retourner la liste des utilisateurs.
        """
        mock_db.execute_query.return_value = [
            {'id': 1, 'username': 'admin', 'role': 'admin'},
            {'id': 2, 'username': 'manager1', 'role': 'manager'},
            {'id': 3, 'username': 'vendeur1', 'role': 'vendeur'},
        ]

        result = UserModel.get_all()

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['username'], 'admin')
        mock_db.execute_query.assert_called_once()

    # ── TM-US-GA-02 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_get_all_retourne_liste_vide_si_aucun(self, mock_db):
        """
        TM-US-GA-02 : get_all() doit retourner une liste vide
        si aucun utilisateur n'existe.
        """
        mock_db.execute_query.return_value = []

        result = UserModel.get_all()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)



# TEST get_by_id()


class TestUserModelGetById(unittest.TestCase):

    # ── TM-US-GI-01 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_get_by_id_retourne_utilisateur(self, mock_db):
        """
        TM-US-GI-01 : get_by_id() doit retourner le dict
        de l'utilisateur quand l'ID existe.
        """
        mock_db.execute_query.return_value = {
            'id': 1, 'username': 'admin',
            'role': 'admin', 'nom_complet': 'Admin SGC'
        }

        result = UserModel.get_by_id(1)

        self.assertIsNotNone(result)
        self.assertEqual(result['username'], 'admin')

    # ── TM-US-GI-02 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_get_by_id_retourne_none_si_absent(self, mock_db):
        """
        TM-US-GI-02 : get_by_id() doit retourner None
        quand l'ID n'existe pas.
        """
        mock_db.execute_query.return_value = None

        result = UserModel.get_by_id(999)

        self.assertIsNone(result)



# TEST get_by_username()


class TestUserModelGetByUsername(unittest.TestCase):

    # ── TM-US-GU-01 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_get_by_username_retourne_utilisateur_avec_hash(self, mock_db):
        """
        TM-US-GU-01 : get_by_username() doit retourner le dict
        complet incluant password_hash pour l'authentification.
        """
        mock_db.execute_query.return_value = {
            'id': 1, 'username': 'admin',
            'password_hash': '$2b$12$fakehash',
            'role': 'admin', 'is_active': 1
        }

        result = UserModel.get_by_username('admin')

        self.assertIsNotNone(result)
        self.assertIn('password_hash', result)
        mock_db.execute_query.assert_called_once_with(
            "SELECT * FROM users WHERE username=%s",
            ('admin',), fetch_one=True
        )

    # ── TM-US-GU-02 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_get_by_username_retourne_none_si_absent(self, mock_db):
        """
        TM-US-GU-02 : get_by_username() doit retourner None
        quand le username n'existe pas.
        """
        mock_db.execute_query.return_value = None

        result = UserModel.get_by_username('inconnu')

        self.assertIsNone(result)



# TEST verify_password()


class TestUserModelVerifyPassword(unittest.TestCase):
    """
    verify_password() utilise bcrypt réel — pas de mock.
    On génère un vrai hash pour tester.
    """

    def setUp(self):
        """Génère un hash bcrypt réel pour les tests."""
        self.mdp = 'uvci@2026'
        self.hash_valide = bcrypt.hashpw(
            self.mdp.encode(), bcrypt.gensalt(rounds=4)
        ).decode()

    # ── TM-US-VP-01 ──────────────────────────────────────────
    def test_mot_de_passe_correct_retourne_true(self):
        """
        TM-US-VP-01 : verify_password() doit retourner True
        quand le mot de passe correspond au hash bcrypt.
        """
        result = UserModel.verify_password(self.mdp, self.hash_valide)

        self.assertTrue(result)

    # ── TM-US-VP-02 ──────────────────────────────────────────
    def test_mot_de_passe_incorrect_retourne_false(self):
        """
        TM-US-VP-02 : verify_password() doit retourner False
        quand le mot de passe ne correspond pas au hash.
        """
        result = UserModel.verify_password('mauvais_mdp', self.hash_valide)

        self.assertFalse(result)

    # ── TM-US-VP-03 ──────────────────────────────────────────
    def test_hash_invalide_retourne_false(self):
        """
        TM-US-VP-03 : verify_password() doit retourner False
        sans lever d'exception si le hash est malformé.
        """
        result = UserModel.verify_password(
            'monmdp', 'hash_invalide_pas_bcrypt')

        self.assertFalse(result)



# TEST find_by_username()


class TestUserModelFindByUsername(unittest.TestCase):

    # ── TM-US-FU-01 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_trouve_utilisateur_existant(self, mock_db):
        """
        TM-US-FU-01 : find_by_username() doit retourner le dict
        si le username existe en base.
        """
        mock_db.execute_query.return_value = {'id': 1}

        result = UserModel.find_by_username('admin')

        self.assertIsNotNone(result)

    # ── TM-US-FU-02 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_retourne_none_si_absent(self, mock_db):
        """
        TM-US-FU-02 : find_by_username() doit retourner None
        si le username n'existe pas.
        """
        mock_db.execute_query.return_value = None

        result = UserModel.find_by_username('inexistant')

        self.assertIsNone(result)

    # ── TM-US-FU-03 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_avec_exclude_id_transmet_deux_params(self, mock_db):
        """
        TM-US-FU-03 : find_by_username() avec exclude_id doit
        transmettre (username, exclude_id) à db.execute_query().
        """
        mock_db.execute_query.return_value = None

        UserModel.find_by_username('manager1', exclude_id=3)

        call_args = mock_db.execute_query.call_args[0]
        params = call_args[1]
        self.assertIn('manager1', params)
        self.assertIn(3, params)

    # ── TM-US-FU-04 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_sans_exclude_id_transmet_un_seul_param(self, mock_db):
        """
        TM-US-FU-04 : find_by_username() sans exclude_id doit
        transmettre uniquement le username.
        """
        mock_db.execute_query.return_value = None

        UserModel.find_by_username('admin')

        call_args = mock_db.execute_query.call_args[0]
        params = call_args[1]
        self.assertEqual(params, ('admin',))



# TEST create()


class TestUserModelCreate(unittest.TestCase):

    # ── TM-US-CR-01 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_create_retourne_id_insere(self, mock_db):
        """
        TM-US-CR-01 : create() doit appeler db.execute_update()
        et retourner l'ID de l'utilisateur créé.
        """
        mock_db.execute_update.return_value = 5

        result = UserModel.create(
            username='vendeur2',
            password_hash='$2b$12$fakehash',
            role='vendeur',
            nom_complet='Bamba Awa',
            email='bamba@mail.ci'
        )

        self.assertEqual(result, 5)
        mock_db.execute_update.assert_called_once()

    # ── TM-US-CR-02 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_create_transmet_bons_parametres(self, mock_db):
        """
        TM-US-CR-02 : create() doit transmettre les paramètres
        dans le bon ordre : username, hash, nom_complet, email, role.
        """
        mock_db.execute_update.return_value = 6

        UserModel.create(
            'user3',
            '$2b$12$h',
            'vendeur',
            'User Trois',
            'u3@mail.ci')

        call_args = mock_db.execute_update.call_args[0]
        params = call_args[1]
        self.assertEqual(params[0], 'user3')          # username
        self.assertEqual(params[1], '$2b$12$h')       # password_hash
        self.assertEqual(params[2], 'User Trois')     # nom_complet
        self.assertEqual(params[3], 'u3@mail.ci')     # email
        self.assertEqual(params[4], 'vendeur')        # role



# TEST update()


class TestUserModelUpdate(unittest.TestCase):

    # ── TM-US-UP-01 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_update_retourne_true(self, mock_db):
        """
        TM-US-UP-01 : update() doit appeler db.execute_update()
        et retourner True.
        """
        result = UserModel.update(
            user_id=3, username='vendeur_maj',
            role='manager', nom_complet='Vendeur MAJ'
        )

        self.assertTrue(result)
        mock_db.execute_update.assert_called_once()

    # ── TM-US-UP-02 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_update_transmet_user_id_en_dernier(self, mock_db):
        """
        TM-US-UP-02 : update() doit placer user_id
        en dernière position dans les paramètres.
        """
        UserModel.update(user_id=7, username='user7', role='vendeur')

        call_args = mock_db.execute_update.call_args[0]
        params = call_args[1]
        self.assertEqual(params[-1], 7)



# TEST change_password()


class TestUserModelChangePassword(unittest.TestCase):

    # ── TM-US-CP-01 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_change_password_retourne_true(self, mock_db):
        """
        TM-US-CP-01 : change_password() doit appeler db.execute_update()
        et retourner True.
        """
        result = UserModel.change_password(1, '$2b$12$nouveauhash')

        self.assertTrue(result)
        mock_db.execute_update.assert_called_once()

    # ── TM-US-CP-02 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_change_password_transmet_hash_et_id(self, mock_db):
        """
        TM-US-CP-02 : change_password() doit transmettre
        le hash en premier et l'user_id en second.
        """
        UserModel.change_password(user_id=4, password_hash='$2b$12$hash')

        call_args = mock_db.execute_update.call_args[0]
        params = call_args[1]
        self.assertEqual(params[0], '$2b$12$hash')  # hash
        self.assertEqual(params[1], 4)               # user_id



# TEST delete()


class TestUserModelDelete(unittest.TestCase):

    # ── TM-US-DE-01 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_delete_retourne_true(self, mock_db):
        """
        TM-US-DE-01 : delete() doit appeler db.execute_update()
        et retourner True.
        """
        result = UserModel.delete(3)

        self.assertTrue(result)
        mock_db.execute_update.assert_called_once()

    # ── TM-US-DE-02 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_delete_transmet_bon_id(self, mock_db):
        """
        TM-US-DE-02 : delete() doit transmettre l'ID exact
        à db.execute_update().
        """
        UserModel.delete(8)

        call_args = mock_db.execute_update.call_args[0]
        params = call_args[1]
        self.assertEqual(params[0], 8)



# TEST get_stats()


class TestUserModelGetStats(unittest.TestCase):

    # ── TM-US-ST-01 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_get_stats_retourne_dict(self, mock_db):
        """
        TM-US-ST-01 : get_stats() doit retourner le dict
        des statistiques du vendeur.
        """
        mock_db.execute_query.return_value = {
            'nb_ventes': 12, 'ca_total': 600000,
            'total_paye': 580000, 'derniere_vente': '2026-02-20'
        }

        result = UserModel.get_stats(2)

        self.assertEqual(result['nb_ventes'], 12)
        self.assertEqual(result['ca_total'], 600000)

    # ── TM-US-ST-02 ──────────────────────────────────────────
    @patch('models.user.db')
    def test_get_stats_retourne_dict_vide_si_none(self, mock_db):
        """
        TM-US-ST-02 : get_stats() doit retourner {} si
        db.execute_query() retourne None.
        """
        mock_db.execute_query.return_value = None

        result = UserModel.get_stats(999)

        self.assertEqual(result, {})



# POINT D'ENTRÉE


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestUserModelGetAll))
    suite.addTests(loader.loadTestsFromTestCase(TestUserModelGetById))
    suite.addTests(loader.loadTestsFromTestCase(TestUserModelGetByUsername))
    suite.addTests(loader.loadTestsFromTestCase(TestUserModelVerifyPassword))
    suite.addTests(loader.loadTestsFromTestCase(TestUserModelFindByUsername))
    suite.addTests(loader.loadTestsFromTestCase(TestUserModelCreate))
    suite.addTests(loader.loadTestsFromTestCase(TestUserModelUpdate))
    suite.addTests(loader.loadTestsFromTestCase(TestUserModelChangePassword))
    suite.addTests(loader.loadTestsFromTestCase(TestUserModelDelete))
    suite.addTests(loader.loadTestsFromTestCase(TestUserModelGetStats))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

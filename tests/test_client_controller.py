"""
tests/test_client_controller.py
--------------------------------
Tests unitaires de ClientController.create() et ClientController.delete().

Architecture réelle : méthodes @staticmethod — ClientModel est appelé
directement, on le mocke avec @patch.

Pour exécuter :
    python tests/test_client_controller.py
    ou
    python -m pytest tests/test_client_controller.py -v
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch
from controllers.client_controller import ClientController


# ══════════════════════════════════════════════════════════════
# TEST create()
# ══════════════════════════════════════════════════════════════

class TestClientControllerCreate(unittest.TestCase):
    """Tests de ClientController.create()."""

    # ── TC-CC-01 ─────────────────────────────────────────────
    def test_nom_vide_retourne_erreur(self):
        """
        TC-CC-01 : create() avec nom vide doit retourner
        (False, message) sans interroger la base.
        """
        data = {'nom': '', 'prenom': 'Jean', 'telephone': '0701020304'}

        ok, msg = ClientController.create(data)

        self.assertFalse(ok)
        self.assertIn('nom', msg.lower())

    # ── TC-CC-02 ─────────────────────────────────────────────
    def test_nom_espaces_retourne_erreur(self):
        """
        TC-CC-02 : create() avec nom composé uniquement d'espaces
        doit retourner (False, message) — le strip() doit rejeter ce cas.
        """
        data = {'nom': '   ', 'prenom': 'Jean', 'telephone': ''}

        ok, msg = ClientController.create(data)

        self.assertFalse(ok)
        self.assertIn('nom', msg.lower())

    # ── TC-CC-03 ─────────────────────────────────────────────
    def test_prenom_vide_retourne_erreur(self):
        """
        TC-CC-03 : create() avec prénom vide doit retourner
        (False, message) sans interroger la base.
        """
        data = {'nom': 'KOUASSI', 'prenom': '', 'telephone': ''}

        ok, msg = ClientController.create(data)

        self.assertFalse(ok)
        self.assertIn('prenom', msg.lower())

    # ── TC-CC-04 ─────────────────────────────────────────────
    @patch('controllers.client_controller.ClientModel.find_duplicate')
    def test_doublon_telephone_retourne_erreur(self, mock_dup):
        """
        TC-CC-04 : create() avec un téléphone déjà utilisé pour le même
        nom+prénom doit retourner (False, message) sans insérer en base.
        """
        mock_dup.return_value = {'id': 1, 'nom': 'KOUASSI', 'prenom': 'Jean'}

        data = {'nom': 'KOUASSI', 'prenom': 'Jean', 'telephone': '0701020304'}

        ok, msg = ClientController.create(data)

        self.assertFalse(ok)
        self.assertIn('existe', msg.lower())
        mock_dup.assert_called_once_with('KOUASSI', 'Jean', '0701020304')

    # ── TC-CC-05 ─────────────────────────────────────────────
    @patch('controllers.client_controller.ClientModel.find_duplicate', return_value=None)
    @patch('controllers.client_controller.ClientModel.create', return_value=11)
    def test_creation_sans_telephone_reussit(self, mock_create, mock_dup):
        """
        TC-CC-05 : create() sans téléphone ne doit PAS appeler
        find_duplicate() et doit retourner (True, id).
        """
        data = {'nom': 'BAMBA', 'prenom': 'Awa', 'telephone': ''}

        ok, cid = ClientController.create(data)

        self.assertTrue(ok)
        self.assertEqual(cid, 11)
        mock_dup.assert_not_called()
        mock_create.assert_called_once()

    # ── TC-CC-06 ─────────────────────────────────────────────
    @patch('controllers.client_controller.ClientModel.find_duplicate', return_value=None)
    @patch('controllers.client_controller.ClientModel.create', return_value=12)
    def test_creation_complete_reussit(self, mock_create, mock_dup):
        """
        TC-CC-06 : create() avec tous les champs valides doit retourner
        (True, id) et appeler ClientModel.create() une seule fois.
        """
        data = {
            'nom': 'TRAORE', 'prenom': 'Moussa',
            'telephone': '0712345678', 'email': 'traore@mail.ci',
            'adresse': 'Cocody', 'ville': 'Abidjan'
        }

        ok, cid = ClientController.create(data)

        self.assertTrue(ok)
        self.assertEqual(cid, 12)
        mock_create.assert_called_once_with(data)

    # ── TC-CC-07 ─────────────────────────────────────────────
    @patch('controllers.client_controller.ClientModel.find_duplicate', return_value=None)
    @patch('controllers.client_controller.ClientModel.create',
           side_effect=Exception("Erreur SQL inattendue"))
    def test_exception_bdd_retourne_erreur(self, mock_create, mock_dup):
        """
        TC-CC-07 : Si ClientModel.create() lève une exception,
        create() doit retourner (False, message) sans propager l'exception.
        """
        data = {'nom': 'KONE', 'prenom': 'Ali', 'telephone': '0799887766'}

        ok, msg = ClientController.create(data)

        self.assertFalse(ok)
        self.assertIsInstance(msg, str)
        self.assertGreater(len(msg), 0)


# ══════════════════════════════════════════════════════════════
# TEST delete()
# ══════════════════════════════════════════════════════════════

class TestClientControllerDelete(unittest.TestCase):
    """Tests de ClientController.delete()."""

    # ── TC-CD-01 ─────────────────────────────────────────────
    @patch('controllers.client_controller.ClientModel.delete')
    def test_suppression_reussie(self, mock_delete):
        """
        TC-CD-01 : delete() doit retourner (True, message) quand
        ClientModel.delete() s'exécute sans erreur.
        """
        mock_delete.return_value = True

        ok, msg = ClientController.delete(1)

        self.assertTrue(ok)
        self.assertIsInstance(msg, str)
        mock_delete.assert_called_once_with(1)

    # ── TC-CD-02 ─────────────────────────────────────────────
    @patch('controllers.client_controller.ClientModel.delete',
           side_effect=ValueError("Impossible de supprimer : ce client a 3 vente(s)."))
    def test_suppression_client_avec_ventes_retourne_erreur(self, mock_delete):
        """
        TC-CD-02 : delete() doit retourner (False, message) quand
        ClientModel.delete() lève une ValueError (ventes associées).
        Le modèle protège la suppression — le controller propage le message.
        """
        ok, msg = ClientController.delete(2)

        self.assertFalse(ok)
        self.assertIn('vente', msg.lower())

    # ── TC-CD-03 ─────────────────────────────────────────────
    @patch('controllers.client_controller.ClientModel.delete',
           side_effect=Exception("Connexion MySQL perdue"))
    def test_exception_inattendue_retourne_erreur(self, mock_delete):
        """
        TC-CD-03 : delete() doit retourner (False, message) pour toute
        exception inattendue, sans propager l'erreur à la vue.
        """
        ok, msg = ClientController.delete(99)

        self.assertFalse(ok)
        self.assertIsInstance(msg, str)

    # ── TC-CD-04 ─────────────────────────────────────────────
    @patch('controllers.client_controller.ClientModel.delete')
    def test_suppression_appelle_model_avec_bon_id(self, mock_delete):
        """
        TC-CD-04 : delete() doit transmettre l'ID exact à ClientModel.delete().
        """
        mock_delete.return_value = True

        ClientController.delete(42)

        mock_delete.assert_called_once_with(42)


# ══════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestClientControllerCreate))
    suite.addTests(loader.loadTestsFromTestCase(TestClientControllerDelete))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

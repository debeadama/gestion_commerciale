"""
tests/test_client_controller.py
--------------------------------
Tests unitaires complets de ClientController.
Couvre : get_all, get_by_id, get_purchase_history, get_stats,
         create, update, delete, get_export_data.

Pour exécuter :
    python -m pytest tests/test_client_controller.py -v
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch
from controllers.client_controller import ClientController


# ══════════════════════════════════════════════════════════════
# TEST get_all()
# ══════════════════════════════════════════════════════════════

class TestClientControllerGetAll(unittest.TestCase):

    @patch('controllers.client_controller.ClientModel.get_all', return_value=[{'id': 1}])
    def test_get_all_sans_filtre(self, mock_get):
        """TC-CGA-01 : get_all() sans filtre retourne la liste du modèle."""
        result = ClientController.get_all()
        self.assertEqual(result, [{'id': 1}])
        mock_get.assert_called_once_with(None)

    @patch('controllers.client_controller.ClientModel.get_all', return_value=[{'id': 2}])
    def test_get_all_avec_recherche(self, mock_get):
        """TC-CGA-02 : get_all() avec recherche transmet le terme au modèle."""
        result = ClientController.get_all(search='KOUASSI')
        self.assertEqual(result, [{'id': 2}])
        mock_get.assert_called_once_with('KOUASSI')

    @patch('controllers.client_controller.ClientModel.get_all', return_value=None)
    def test_get_all_retourne_liste_vide_si_none(self, mock_get):
        """TC-CGA-03 : get_all() retourne [] si le modèle retourne None."""
        result = ClientController.get_all()
        self.assertEqual(result, [])


# ══════════════════════════════════════════════════════════════
# TEST get_by_id()
# ══════════════════════════════════════════════════════════════

class TestClientControllerGetById(unittest.TestCase):

    @patch('controllers.client_controller.ClientModel.get_by_id',
           return_value={'id': 1, 'nom': 'KOUASSI'})
    def test_get_by_id_existant(self, mock_get):
        """TC-CGB-01 : get_by_id() retourne le dict du modèle."""
        result = ClientController.get_by_id(1)
        self.assertEqual(result['nom'], 'KOUASSI')
        mock_get.assert_called_once_with(1)

    @patch('controllers.client_controller.ClientModel.get_by_id', return_value=None)
    def test_get_by_id_inexistant(self, mock_get):
        """TC-CGB-02 : get_by_id() retourne None si client inexistant."""
        result = ClientController.get_by_id(999)
        self.assertIsNone(result)


# ══════════════════════════════════════════════════════════════
# TEST get_purchase_history()
# ══════════════════════════════════════════════════════════════

class TestClientControllerPurchaseHistory(unittest.TestCase):

    @patch('controllers.client_controller.ClientModel.get_purchase_history',
           return_value=[{'facture': 'FAC-001'}])
    def test_historique_retourne_liste(self, mock_hist):
        """TC-CPH-01 : get_purchase_history() retourne la liste des achats."""
        result = ClientController.get_purchase_history(1)
        self.assertEqual(len(result), 1)
        mock_hist.assert_called_once_with(1)

    @patch('controllers.client_controller.ClientModel.get_purchase_history',
           return_value=None)
    def test_historique_vide_retourne_liste_vide(self, mock_hist):
        """TC-CPH-02 : get_purchase_history() retourne [] si None."""
        result = ClientController.get_purchase_history(99)
        self.assertEqual(result, [])


# ══════════════════════════════════════════════════════════════
# TEST get_stats()
# ══════════════════════════════════════════════════════════════

class TestClientControllerGetStats(unittest.TestCase):

    @patch('controllers.client_controller.ClientModel.get_stats',
           return_value={'ca_total': 500000, 'nb_achats': 3})
    def test_get_stats_retourne_dict(self, mock_stats):
        """TC-CGS-01 : get_stats() retourne les stats du modèle."""
        result = ClientController.get_stats(1)
        self.assertEqual(result['nb_achats'], 3)
        mock_stats.assert_called_once_with(1)


# ══════════════════════════════════════════════════════════════
# TEST create()
# ══════════════════════════════════════════════════════════════

class TestClientControllerCreate(unittest.TestCase):

    def test_nom_vide_retourne_erreur(self):
        """TC-CC-01 : create() avec nom vide retourne (False, message)."""
        ok, msg = ClientController.create({'nom': '', 'prenom': 'Jean'})
        self.assertFalse(ok)
        self.assertIn('nom', msg.lower())

    def test_nom_espaces_retourne_erreur(self):
        """TC-CC-02 : create() avec nom = espaces retourne (False, message)."""
        ok, msg = ClientController.create({'nom': '   ', 'prenom': 'Jean'})
        self.assertFalse(ok)
        self.assertIn('nom', msg.lower())

    def test_prenom_vide_retourne_erreur(self):
        """TC-CC-03 : create() avec prénom vide retourne (False, message)."""
        ok, msg = ClientController.create({'nom': 'KOUASSI', 'prenom': ''})
        self.assertFalse(ok)
        self.assertIn('prenom', msg.lower())

    @patch('controllers.client_controller.ClientModel.find_duplicate',
           return_value={'id': 1})
    def test_doublon_telephone_retourne_erreur(self, mock_dup):
        """TC-CC-04 : doublon téléphone retourne (False, message)."""
        ok, msg = ClientController.create(
            {'nom': 'KOUASSI', 'prenom': 'Jean', 'telephone': '0701020304'})
        self.assertFalse(ok)
        self.assertIn('existe', msg.lower())

    @patch('controllers.client_controller.ClientModel.find_duplicate', return_value=None)
    @patch('controllers.client_controller.ClientModel.create', return_value=11)
    def test_creation_sans_telephone_reussit(self, mock_create, mock_dup):
        """TC-CC-05 : create() sans téléphone réussit sans appeler find_duplicate."""
        ok, cid = ClientController.create({'nom': 'BAMBA', 'prenom': 'Awa', 'telephone': ''})
        self.assertTrue(ok)
        self.assertEqual(cid, 11)
        mock_dup.assert_not_called()

    @patch('controllers.client_controller.ClientModel.find_duplicate', return_value=None)
    @patch('controllers.client_controller.ClientModel.create', return_value=12)
    def test_creation_complete_reussit(self, mock_create, mock_dup):
        """TC-CC-06 : create() complet retourne (True, id)."""
        data = {'nom': 'TRAORE', 'prenom': 'Moussa', 'telephone': '0712345678'}
        ok, cid = ClientController.create(data)
        self.assertTrue(ok)
        self.assertEqual(cid, 12)

    @patch('controllers.client_controller.ClientModel.find_duplicate', return_value=None)
    @patch('controllers.client_controller.ClientModel.create',
           side_effect=Exception("Erreur SQL"))
    def test_exception_bdd_retourne_erreur(self, mock_create, mock_dup):
        """TC-CC-07 : exception BDD retourne (False, message)."""
        ok, msg = ClientController.create(
            {'nom': 'KONE', 'prenom': 'Ali', 'telephone': '0799887766'})
        self.assertFalse(ok)
        self.assertIsInstance(msg, str)


# ══════════════════════════════════════════════════════════════
# TEST update()
# ══════════════════════════════════════════════════════════════

class TestClientControllerUpdate(unittest.TestCase):

    def test_update_nom_vide_retourne_erreur(self):
        """TC-CU-01 : update() avec nom vide retourne (False, message)."""
        ok, msg = ClientController.update(1, {'nom': '', 'prenom': 'Jean'})
        self.assertFalse(ok)
        self.assertIn('nom', msg.lower())

    def test_update_prenom_vide_retourne_erreur(self):
        """TC-CU-02 : update() avec prénom vide retourne (False, message)."""
        ok, msg = ClientController.update(1, {'nom': 'KOUASSI', 'prenom': ''})
        self.assertFalse(ok)
        self.assertIn('prenom', msg.lower())

    @patch('controllers.client_controller.ClientModel.update')
    def test_update_reussie(self, mock_update):
        """TC-CU-03 : update() valide retourne (True, message)."""
        ok, msg = ClientController.update(
            1, {'nom': 'KOUASSI', 'prenom': 'Jean', 'telephone': '0701020304'})
        self.assertTrue(ok)
        self.assertIsInstance(msg, str)
        mock_update.assert_called_once()

    @patch('controllers.client_controller.ClientModel.update',
           side_effect=Exception("Connexion perdue"))
    def test_update_exception_retourne_erreur(self, mock_update):
        """TC-CU-04 : exception dans update() retourne (False, message)."""
        ok, msg = ClientController.update(1, {'nom': 'KOUASSI', 'prenom': 'Jean'})
        self.assertFalse(ok)
        self.assertIsInstance(msg, str)


# ══════════════════════════════════════════════════════════════
# TEST delete()
# ══════════════════════════════════════════════════════════════

class TestClientControllerDelete(unittest.TestCase):

    @patch('controllers.client_controller.ClientModel.delete')
    def test_suppression_reussie(self, mock_delete):
        """TC-CD-01 : delete() retourne (True, message) en cas de succès."""
        ok, msg = ClientController.delete(1)
        self.assertTrue(ok)
        mock_delete.assert_called_once_with(1)

    @patch('controllers.client_controller.ClientModel.delete',
           side_effect=ValueError("Ce client a 3 vente(s)."))
    def test_suppression_client_avec_ventes(self, mock_delete):
        """TC-CD-02 : ValueError retourne (False, message)."""
        ok, msg = ClientController.delete(2)
        self.assertFalse(ok)
        self.assertIn('vente', msg.lower())

    @patch('controllers.client_controller.ClientModel.delete',
           side_effect=Exception("Connexion MySQL perdue"))
    def test_exception_inattendue_retourne_erreur(self, mock_delete):
        """TC-CD-03 : exception inattendue retourne (False, message)."""
        ok, msg = ClientController.delete(99)
        self.assertFalse(ok)
        self.assertIsInstance(msg, str)

    @patch('controllers.client_controller.ClientModel.delete')
    def test_suppression_appelle_model_avec_bon_id(self, mock_delete):
        """TC-CD-04 : delete() transmet l'ID exact au modèle."""
        ClientController.delete(42)
        mock_delete.assert_called_once_with(42)


# ══════════════════════════════════════════════════════════════
# TEST get_export_data()
# ══════════════════════════════════════════════════════════════

class TestClientControllerExport(unittest.TestCase):

    @patch('controllers.client_controller.ClientModel.get_export_data',
           return_value=[{'nom': 'KOUASSI', 'ca_total': 500000}])
    def test_export_data_retourne_liste(self, mock_export):
        """TC-CE-01 : get_export_data() retourne la liste du modèle."""
        result = ClientController.get_export_data()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['nom'], 'KOUASSI')
        mock_export.assert_called_once()


# ══════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    unittest.main(verbosity=2)

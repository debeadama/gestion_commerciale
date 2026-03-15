"""
tests/test_model_client.py
---------------------------
Tests unitaires complets de ClientModel.
Couvre : get_all, get_by_id, find_duplicate, get_stats,
         get_export_data, create, update, delete,
         get_purchase_history, count.

Pour exécuter :
    python -m pytest tests/test_model_client.py -v
"""

from models.client import ClientModel  # noqa: E402
from unittest.mock import patch, call  # noqa: E402
import unittest
import sys
import os

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '..')))



# TEST get_all()


class TestClientModelGetAll(unittest.TestCase):

    @patch('models.client.db')
    def test_get_all_sans_recherche(self, mock_db):
        """TC-CMA-01 : get_all() sans search exécute la requête simple."""
        mock_db.execute_query.return_value = [{'id': 1}]
        result = ClientModel.get_all()
        self.assertEqual(len(result), 1)
        call_sql = mock_db.execute_query.call_args[0][0]
        self.assertIn('ORDER BY', call_sql)

    @patch('models.client.db')
    def test_get_all_avec_recherche(self, mock_db):
        """TC-CMA-02 : get_all(search) utilise LIKE avec le bon pattern."""
        mock_db.execute_query.return_value = []
        ClientModel.get_all(search='KOUASSI')
        params = mock_db.execute_query.call_args[0][1]
        self.assertIn('%KOUASSI%', params)



# TEST get_by_id()


class TestClientModelGetById(unittest.TestCase):

    @patch('models.client.db')
    def test_get_by_id_retourne_client(self, mock_db):
        """TC-CMB-01 : get_by_id() retourne le client."""
        mock_db.execute_query.return_value = {'id': 1, 'nom': 'KOUASSI'}
        result = ClientModel.get_by_id(1)
        self.assertEqual(result['nom'], 'KOUASSI')
        mock_db.execute_query.assert_called_once()

    @patch('models.client.db')
    def test_get_by_id_retourne_none_si_absent(self, mock_db):
        """TC-CMB-02 : get_by_id() retourne None si inexistant."""
        mock_db.execute_query.return_value = None
        result = ClientModel.get_by_id(999)
        self.assertIsNone(result)



# TEST find_duplicate()


class TestClientModelFindDuplicate(unittest.TestCase):

    @patch('models.client.db')
    def test_find_duplicate_retourne_client_si_doublon(self, mock_db):
        """TC-CMD-01 : find_duplicate() retourne le client existant."""
        mock_db.execute_query.return_value = {'id': 5}
        result = ClientModel.find_duplicate('KOUASSI', 'Jean', '0701020304')
        self.assertEqual(result['id'], 5)

    @patch('models.client.db')
    def test_find_duplicate_retourne_none_si_absent(self, mock_db):
        """TC-CMD-02 : find_duplicate() retourne None si pas de doublon."""
        mock_db.execute_query.return_value = None
        result = ClientModel.find_duplicate('BAMBA', 'Awa', '0799999999')
        self.assertIsNone(result)



# TEST get_stats()


class TestClientModelGetStats(unittest.TestCase):

    @patch('models.client.db')
    def test_get_stats_retourne_dict(self, mock_db):
        """TC-CMS-01 : get_stats() retourne les stats du client."""
        mock_db.execute_query.return_value = {
            'nb_achats': 3, 'ca_total': 500000,
            'total_paye': 500000, 'derniere_visite': '15/01/2024'
        }
        result = ClientModel.get_stats(1)
        self.assertEqual(result['nb_achats'], 3)
        params = mock_db.execute_query.call_args[0][1]
        self.assertEqual(params, (1,))

    @patch('models.client.db')
    def test_get_stats_retourne_dict_vide_si_none(self, mock_db):
        """TC-CMS-02 : get_stats() retourne {} si db retourne None."""
        mock_db.execute_query.return_value = None
        result = ClientModel.get_stats(999)
        self.assertEqual(result, {})



# TEST get_export_data()


class TestClientModelGetExportData(unittest.TestCase):

    @patch('models.client.db')
    def test_get_export_data_retourne_liste(self, mock_db):
        """TC-CME-01 : get_export_data() retourne la liste enrichie."""
        mock_db.execute_query.return_value = [
            {
                'nom': 'KOUASSI', 'prenom': 'Jean',
                'ca_total': 500000, 'nb_achats': 3,
            }
        ]
        result = ClientModel.get_export_data()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['nom'], 'KOUASSI')
        mock_db.execute_query.assert_called_once()

    @patch('models.client.db')
    def test_get_export_data_retourne_liste_vide_si_none(self, mock_db):
        """TC-CME-02 : get_export_data() retourne [] si db retourne None."""
        mock_db.execute_query.return_value = None
        result = ClientModel.get_export_data()
        self.assertEqual(result, [])

    @patch('models.client.db')
    def test_get_export_data_sql_contient_ca_total(self, mock_db):
        """TC-CME-03 : la requête SQL inclut le calcul du CA total."""
        mock_db.execute_query.return_value = []
        ClientModel.get_export_data()
        call_sql = mock_db.execute_query.call_args[0][0]
        self.assertIn('ca_total', call_sql.lower())
        self.assertIn('nb_achats', call_sql.lower())



# TEST create()


class TestClientModelCreate(unittest.TestCase):

    @patch('models.client.db')
    def test_create_retourne_id_insere(self, mock_db):
        """TC-CMC-01 : create() retourne l'ID inséré."""
        mock_db.execute_update.return_value = 15
        data = {'nom': 'TRAORE', 'prenom': 'Moussa', 'telephone': '0712345678'}
        result = ClientModel.create(data)
        self.assertEqual(result, 15)

    @patch('models.client.db')
    def test_create_champs_optionnels_none(self, mock_db):
        """TC-CMC-02 : champs optionnels absents sont passés comme None."""
        mock_db.execute_update.return_value = 16
        data = {'nom': 'BAMBA', 'prenom': 'Awa'}
        ClientModel.create(data)
        params = mock_db.execute_update.call_args[0][1]
        # telephone, email, adresse, ville, code_postal → None
        self.assertIsNone(params[2])
        self.assertIsNone(params[3])



# TEST update()


class TestClientModelUpdate(unittest.TestCase):

    @patch('models.client.db')
    def test_update_appelle_execute_update(self, mock_db):
        """TC-CMU-01 : update() appelle execute_update avec le bon ID."""
        mock_db.execute_update.return_value = True
        data = {'nom': 'KOUASSI', 'prenom': 'Jean', 'telephone': '0701020304'}
        result = ClientModel.update(1, data)
        self.assertTrue(result)
        params = mock_db.execute_update.call_args[0][1]
        self.assertEqual(params[-1], 1)



# TEST delete()


class TestClientModelDelete(unittest.TestCase):

    @patch('models.client.db')
    def test_delete_reussit_si_aucune_vente(self, mock_db):
        """TC-CMD-01 : delete() réussit si le client n'a pas de ventes."""
        mock_db.execute_query.return_value = {'total': 0}
        mock_db.execute_update.return_value = True
        result = ClientModel.delete(1)
        self.assertTrue(result)
        mock_db.execute_update.assert_called_once()

    @patch('models.client.db')
    def test_delete_leve_valueerror_si_ventes_associees(self, mock_db):
        """TC-CMD-02 : delete() lève ValueError si ventes associées."""
        mock_db.execute_query.return_value = {'total': 3}
        with self.assertRaises(ValueError) as ctx:
            ClientModel.delete(2)
        self.assertIn('vente', str(ctx.exception).lower())

    @patch('models.client.db')
    def test_delete_transmet_bon_id(self, mock_db):
        """TC-CMD-03 : delete() transmet l'ID exact à execute_update."""
        mock_db.execute_query.return_value = {'total': 0}
        mock_db.execute_update.return_value = True
        ClientModel.delete(42)
        params = mock_db.execute_update.call_args[0][1]
        self.assertEqual(params, (42,))



# TEST get_purchase_history()


class TestClientModelPurchaseHistory(unittest.TestCase):

    @patch('models.client.db')
    def test_get_purchase_history_retourne_liste(self, mock_db):
        """TC-CMH-01 : get_purchase_history() retourne les achats du client."""
        mock_db.execute_query.return_value = [
            {'id': 1, 'numero_facture': 'FAC-20240115-0001',
             'statut': 'payee'},
            {'id': 2, 'numero_facture': 'FAC-20240120-0002',
             'statut': 'partielle'},
        ]
        result = ClientModel.get_purchase_history(1)
        self.assertEqual(len(result), 2)
        params = mock_db.execute_query.call_args[0][1]
        self.assertEqual(params, (1,))

    @patch('models.client.db')
    def test_get_purchase_history_vide(self, mock_db):
        """TC-CMH-02 : get_purchase_history() retourne [] si aucun achat."""
        mock_db.execute_query.return_value = []
        result = ClientModel.get_purchase_history(999)
        self.assertEqual(result, [])

    @patch('models.client.db')
    def test_get_purchase_history_sql_filtre_par_client(self, mock_db):
        """TC-CMH-03 : la requête SQL filtre bien par client_id."""
        mock_db.execute_query.return_value = []
        ClientModel.get_purchase_history(5)
        call_sql = mock_db.execute_query.call_args[0][0]
        self.assertIn('client_id', call_sql)
        self.assertIn('ORDER BY', call_sql)



# TEST count()


class TestClientModelCount(unittest.TestCase):

    @patch('models.client.db')
    def test_count_retourne_entier(self, mock_db):
        """TC-CMT-01 : count() retourne le nombre total de clients."""
        mock_db.execute_query.return_value = {'total': 10}
        result = ClientModel.count()
        self.assertEqual(result, 10)

    @patch('models.client.db')
    def test_count_retourne_zero_si_none(self, mock_db):
        """TC-CMT-02 : count() retourne 0 si db retourne None."""
        mock_db.execute_query.return_value = None
        result = ClientModel.count()
        self.assertEqual(result, 0)



# POINT D'ENTRÉE


if __name__ == '__main__':
    unittest.main(verbosity=2)

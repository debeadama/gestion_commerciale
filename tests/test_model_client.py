"""
tests/test_model_client.py
---------------------------
Tests unitaires de ClientModel.

Méthodes testées :
  - get_all()              : sans/avec recherche
  - get_by_id()            : trouvé, None si absent
  - find_duplicate()       : trouvé, None si absent
  - create()               : retourne ID, champs optionnels à None
  - update()               : appel db avec bons paramètres
  - delete()               : succès, ValueError si ventes liées
  - get_stats()            : retourne dict ou {} si None
  - get_purchase_history() : retourne liste
  - count()                : retourne entier

Architecture : méthodes @staticmethod — db est mocké avec @patch.

Pour exécuter :
    python tests/test_model_client.py
    ou
    python -m pytest tests/test_model_client.py -v
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch, call
from models.client import ClientModel


# ══════════════════════════════════════════════════════════════
# TEST get_all()
# ══════════════════════════════════════════════════════════════

class TestClientModelGetAll(unittest.TestCase):

    # ── TM-CL-GA-01 ──────────────────────────────────────────
    @patch('models.client.db')
    def test_get_all_sans_recherche(self, mock_db):
        """
        TM-CL-GA-01 : get_all() sans paramètre doit appeler
        db.execute_query() avec la requête simple (sans WHERE).
        """
        mock_db.execute_query.return_value = [
            {'id': 1, 'nom': 'KOUASSI', 'prenom': 'Jean'},
            {'id': 2, 'nom': 'BAMBA',   'prenom': 'Awa'},
        ]

        result = ClientModel.get_all()

        self.assertEqual(len(result), 2)
        # Appel sans paramètres de recherche
        call_args = mock_db.execute_query.call_args
        self.assertIsNone(call_args[0][1] if len(call_args[0]) > 1 else None)

    # ── TM-CL-GA-02 ──────────────────────────────────────────
    @patch('models.client.db')
    def test_get_all_avec_recherche(self, mock_db):
        """
        TM-CL-GA-02 : get_all() avec paramètre search doit passer
        le pattern %search% en 4 exemplaires (nom, prenom, tel, email).
        """
        mock_db.execute_query.return_value = [
            {'id': 1, 'nom': 'KOUASSI', 'prenom': 'Jean'}
        ]

        result = ClientModel.get_all(search='kouassi')

        self.assertEqual(len(result), 1)
        call_args = mock_db.execute_query.call_args[0]
        params = call_args[1]
        self.assertEqual(params, ('%kouassi%', '%kouassi%', '%kouassi%', '%kouassi%'))


# ══════════════════════════════════════════════════════════════
# TEST get_by_id()
# ══════════════════════════════════════════════════════════════

class TestClientModelGetById(unittest.TestCase):

    # ── TM-CL-GI-01 ──────────────────────────────────────────
    @patch('models.client.db')
    def test_get_by_id_retourne_client(self, mock_db):
        """
        TM-CL-GI-01 : get_by_id() doit retourner le dict
        du client quand l'ID existe.
        """
        mock_db.execute_query.return_value = {
            'id': 1, 'nom': 'KOUASSI', 'prenom': 'Jean'
        }

        result = ClientModel.get_by_id(1)

        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 1)

    # ── TM-CL-GI-02 ──────────────────────────────────────────
    @patch('models.client.db')
    def test_get_by_id_retourne_none_si_absent(self, mock_db):
        """
        TM-CL-GI-02 : get_by_id() doit retourner None
        quand l'ID n'existe pas.
        """
        mock_db.execute_query.return_value = None

        result = ClientModel.get_by_id(999)

        self.assertIsNone(result)


# ══════════════════════════════════════════════════════════════
# TEST find_duplicate()
# ══════════════════════════════════════════════════════════════

class TestClientModelFindDuplicate(unittest.TestCase):

    # ── TM-CL-FD-01 ──────────────────────────────────────────
    @patch('models.client.db')
    def test_find_duplicate_retourne_client_si_doublon(self, mock_db):
        """
        TM-CL-FD-01 : find_duplicate() doit retourner le dict
        du client existant quand nom+prenom+telephone correspondent.
        """
        mock_db.execute_query.return_value = {'id': 1}

        result = ClientModel.find_duplicate('KOUASSI', 'Jean', '0701020304')

        self.assertIsNotNone(result)
        call_args = mock_db.execute_query.call_args[0]
        params = call_args[1]
        self.assertEqual(params, ('KOUASSI', 'Jean', '0701020304'))

    # ── TM-CL-FD-02 ──────────────────────────────────────────
    @patch('models.client.db')
    def test_find_duplicate_retourne_none_si_absent(self, mock_db):
        """
        TM-CL-FD-02 : find_duplicate() doit retourner None
        quand aucun doublon n'existe.
        """
        mock_db.execute_query.return_value = None

        result = ClientModel.find_duplicate('TRAORE', 'Moussa', '0799999999')

        self.assertIsNone(result)


# ══════════════════════════════════════════════════════════════
# TEST create()
# ══════════════════════════════════════════════════════════════

class TestClientModelCreate(unittest.TestCase):

    # ── TM-CL-CR-01 ──────────────────────────────────────────
    @patch('models.client.db')
    def test_create_retourne_id_insere(self, mock_db):
        """
        TM-CL-CR-01 : create() doit appeler db.execute_update()
        et retourner l'ID du client créé.
        """
        mock_db.execute_update.return_value = 11

        data = {
            'nom': 'TRAORE', 'prenom': 'Moussa',
            'telephone': '0712345678', 'email': 'traore@mail.ci',
            'adresse': 'Cocody', 'ville': 'Abidjan', 'code_postal': ''
        }

        result = ClientModel.create(data)

        self.assertEqual(result, 11)
        mock_db.execute_update.assert_called_once()

    # ── TM-CL-CR-02 ──────────────────────────────────────────
    @patch('models.client.db')
    def test_create_champs_optionnels_none(self, mock_db):
        """
        TM-CL-CR-02 : create() doit convertir les champs optionnels
        vides en None avant insertion.
        """
        mock_db.execute_update.return_value = 12

        data = {'nom': 'BAMBA', 'prenom': 'Awa',
                'telephone': '', 'email': '', 'adresse': '',
                'ville': '', 'code_postal': ''}

        ClientModel.create(data)

        call_args = mock_db.execute_update.call_args[0]
        params = call_args[1]
        # telephone, email, adresse, ville, code_postal doivent être None
        self.assertIsNone(params[2])  # telephone
        self.assertIsNone(params[3])  # email
        self.assertIsNone(params[4])  # adresse
        self.assertIsNone(params[5])  # ville
        self.assertIsNone(params[6])  # code_postal


# ══════════════════════════════════════════════════════════════
# TEST update()
# ══════════════════════════════════════════════════════════════

class TestClientModelUpdate(unittest.TestCase):

    # ── TM-CL-UP-01 ──────────────────────────────────────────
    @patch('models.client.db')
    def test_update_appelle_execute_update(self, mock_db):
        """
        TM-CL-UP-01 : update() doit appeler db.execute_update()
        avec le bon client_id en dernière position et retourner True.
        """
        data = {'nom': 'KOUASSI', 'prenom': 'Jean',
                'telephone': '0701020304', 'email': '',
                'adresse': '', 'ville': 'Abidjan', 'code_postal': ''}

        result = ClientModel.update(1, data)

        self.assertTrue(result)
        mock_db.execute_update.assert_called_once()
        call_args = mock_db.execute_update.call_args[0]
        params = call_args[1]
        self.assertEqual(params[-1], 1)  # client_id en dernière position


# ══════════════════════════════════════════════════════════════
# TEST delete()
# ══════════════════════════════════════════════════════════════

class TestClientModelDelete(unittest.TestCase):

    # ── TM-CL-DE-01 ──────────────────────────────────────────
    @patch('models.client.db')
    def test_delete_reussit_si_aucune_vente(self, mock_db):
        """
        TM-CL-DE-01 : delete() doit supprimer le client et retourner
        True quand aucune vente n'est associée.
        """
        mock_db.execute_query.return_value  = {'total': 0}
        mock_db.execute_update.return_value = 1

        result = ClientModel.delete(1)

        self.assertTrue(result)
        mock_db.execute_update.assert_called_once()

    # ── TM-CL-DE-02 ──────────────────────────────────────────
    @patch('models.client.db')
    def test_delete_leve_valueerror_si_ventes_associees(self, mock_db):
        """
        TM-CL-DE-02 : delete() doit lever une ValueError quand
        le client possède des ventes associées.
        """
        mock_db.execute_query.return_value = {'total': 3}

        with self.assertRaises(ValueError) as ctx:
            ClientModel.delete(2)

        self.assertIn('vente', str(ctx.exception).lower())
        mock_db.execute_update.assert_not_called()

    # ── TM-CL-DE-03 ──────────────────────────────────────────
    @patch('models.client.db')
    def test_delete_transmet_bon_id(self, mock_db):
        """
        TM-CL-DE-03 : delete() doit transmettre l'ID exact
        à db.execute_update().
        """
        mock_db.execute_query.return_value  = {'total': 0}
        mock_db.execute_update.return_value = 1

        ClientModel.delete(7)

        call_args = mock_db.execute_update.call_args[0]
        params = call_args[1]
        self.assertEqual(params[0], 7)


# ══════════════════════════════════════════════════════════════
# TEST get_stats()
# ══════════════════════════════════════════════════════════════

class TestClientModelGetStats(unittest.TestCase):

    # ── TM-CL-ST-01 ──────────────────────────────────────────
    @patch('models.client.db')
    def test_get_stats_retourne_dict(self, mock_db):
        """
        TM-CL-ST-01 : get_stats() doit retourner le dict
        des statistiques du client.
        """
        mock_db.execute_query.return_value = {
            'nb_achats': 5, 'ca_total': 250000,
            'total_paye': 250000, 'derniere_visite': '15/02/2026'
        }

        result = ClientModel.get_stats(1)

        self.assertEqual(result['nb_achats'], 5)
        self.assertEqual(result['ca_total'], 250000)

    # ── TM-CL-ST-02 ──────────────────────────────────────────
    @patch('models.client.db')
    def test_get_stats_retourne_dict_vide_si_none(self, mock_db):
        """
        TM-CL-ST-02 : get_stats() doit retourner {} si
        db.execute_query() retourne None.
        """
        mock_db.execute_query.return_value = None

        result = ClientModel.get_stats(999)

        self.assertEqual(result, {})


# ══════════════════════════════════════════════════════════════
# TEST count()
# ══════════════════════════════════════════════════════════════

class TestClientModelCount(unittest.TestCase):

    # ── TM-CL-CO-01 ──────────────────────────────────────────
    @patch('models.client.db')
    def test_count_retourne_entier(self, mock_db):
        """
        TM-CL-CO-01 : count() doit retourner le nombre total
        de clients sous forme d'entier.
        """
        mock_db.execute_query.return_value = {'total': 10}

        result = ClientModel.count()

        self.assertEqual(result, 10)

    # ── TM-CL-CO-02 ──────────────────────────────────────────
    @patch('models.client.db')
    def test_count_retourne_zero_si_none(self, mock_db):
        """
        TM-CL-CO-02 : count() doit retourner 0 si
        db.execute_query() retourne None.
        """
        mock_db.execute_query.return_value = None

        result = ClientModel.count()

        self.assertEqual(result, 0)


# ══════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestClientModelGetAll))
    suite.addTests(loader.loadTestsFromTestCase(TestClientModelGetById))
    suite.addTests(loader.loadTestsFromTestCase(TestClientModelFindDuplicate))
    suite.addTests(loader.loadTestsFromTestCase(TestClientModelCreate))
    suite.addTests(loader.loadTestsFromTestCase(TestClientModelUpdate))
    suite.addTests(loader.loadTestsFromTestCase(TestClientModelDelete))
    suite.addTests(loader.loadTestsFromTestCase(TestClientModelGetStats))
    suite.addTests(loader.loadTestsFromTestCase(TestClientModelCount))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

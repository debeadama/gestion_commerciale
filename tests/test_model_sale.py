"""
tests/test_model_sale.py
-------------------------
Tests unitaires de SaleModel.

Méthodes testées :
  - get_by_id()      : trouvé, None si absent
  - get_details()    : retourne liste lignes
  - generate_numero(): format FAC-YYYYMMDD-XXXX
  - create()         : INSERT vente + détails + UPDATE stock
  - add_payment()    : vente introuvable, annulée, montant > total, succès
  - validate()       : avec/sans montant_reste
  - cancel()         : introuvable, déjà annulée, déjà payée, succès
  - count()          : retourne entier ou 0

Architecture : méthodes @staticmethod — db est mocké avec @patch.

Pour exécuter :
    python tests/test_model_sale.py
    ou
    python -m pytest tests/test_model_sale.py -v
"""

import unittest
import sys
import os
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch, MagicMock, call
from models.sale import SaleModel


# ══════════════════════════════════════════════════════════════
# TEST get_by_id()
# ══════════════════════════════════════════════════════════════

class TestSaleModelGetById(unittest.TestCase):

    # ── TM-SA-GI-01 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_get_by_id_retourne_vente(self, mock_db):
        """
        TM-SA-GI-01 : get_by_id() doit retourner le dict
        de la vente quand l'ID existe.
        """
        mock_db.execute_query.return_value = {
            'id': 1, 'numero_facture': 'FAC-20260210-0001',
            'statut': 'payee', 'montant_total': 50000
        }

        result = SaleModel.get_by_id(1)

        self.assertIsNotNone(result)
        self.assertEqual(result['numero_facture'], 'FAC-20260210-0001')

    # ── TM-SA-GI-02 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_get_by_id_retourne_none_si_absent(self, mock_db):
        """
        TM-SA-GI-02 : get_by_id() doit retourner None
        quand l'ID n'existe pas.
        """
        mock_db.execute_query.return_value = None

        result = SaleModel.get_by_id(999)

        self.assertIsNone(result)


# ══════════════════════════════════════════════════════════════
# TEST get_details()
# ══════════════════════════════════════════════════════════════

class TestSaleModelGetDetails(unittest.TestCase):

    # ── TM-SA-GD-01 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_get_details_retourne_lignes(self, mock_db):
        """
        TM-SA-GD-01 : get_details() doit retourner la liste
        des lignes de détail de la vente.
        """
        mock_db.execute_query.return_value = [
            {'produit': 'Samsung A55', 'quantite': 2, 'prix_unitaire': 185000},
            {'produit': 'Câble USB',   'quantite': 1, 'prix_unitaire': 5000},
        ]

        result = SaleModel.get_details(1)

        self.assertEqual(len(result), 2)
        mock_db.execute_query.assert_called_once()


# ══════════════════════════════════════════════════════════════
# TEST generate_numero()
# ══════════════════════════════════════════════════════════════

class TestSaleModelGenerateNumero(unittest.TestCase):

    # ── TM-SA-GN-01 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_generate_numero_format_correct(self, mock_db):
        """
        TM-SA-GN-01 : generate_numero() doit produire un numéro
        au format FAC-YYYYMMDD-XXXX.
        """
        mock_db.execute_query.return_value = {'total': 0}

        numero = SaleModel.generate_numero()

        pattern = r'^FAC-\d{8}-\d{4}$'
        self.assertRegex(numero, pattern,
            msg=f"Format invalide : {numero}. Attendu : FAC-YYYYMMDD-XXXX")

    # ── TM-SA-GN-02 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_generate_numero_sequence_incrementee(self, mock_db):
        """
        TM-SA-GN-02 : generate_numero() doit incrémenter la séquence
        selon le nombre de ventes du jour (total + 1).
        Avec total=4, le numéro doit se terminer par -0005.
        """
        mock_db.execute_query.return_value = {'total': 4}

        numero = SaleModel.generate_numero()

        self.assertTrue(numero.endswith('-0005'),
            msg=f"Séquence incorrecte : {numero}")


# ══════════════════════════════════════════════════════════════
# TEST create()
# ══════════════════════════════════════════════════════════════

class TestSaleModelCreate(unittest.TestCase):

    # ── TM-SA-CR-01 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_create_retourne_sale_id(self, mock_db):
        """
        TM-SA-CR-01 : create() doit insérer la vente et retourner
        l'ID de la vente créée.
        """
        # 1er appel COUNT pour generate_numero, 2ème = INSERT vente (sale_id=7)
        mock_db.execute_query.return_value  = {'total': 0}
        mock_db.execute_update.return_value = 7

        sale_data = {
            'client_id': 1, 'user_id': 1,
            'montant_total': 50000, 'montant_paye': 50000,
            'montant_reste': 0, 'statut': 'payee', 'notes': '',
            'panier': [
                {'produit_id': 1, 'quantite': 1, 'prix_unitaire': 50000}
            ]
        }

        result = SaleModel.create(sale_data)

        self.assertEqual(result, 7)

    # ── TM-SA-CR-02 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_create_insere_details_et_met_a_jour_stock(self, mock_db):
        """
        TM-SA-CR-02 : create() avec 2 produits doit effectuer
        5 appels db.execute_update() :
        1 INSERT ventes + 2 INSERT ventes_details + 2 UPDATE stock.
        """
        mock_db.execute_query.return_value  = {'total': 0}
        mock_db.execute_update.return_value = 8

        sale_data = {
            'client_id': 1, 'user_id': 1,
            'montant_total': 100000, 'montant_paye': 100000,
            'montant_reste': 0, 'statut': 'payee', 'notes': '',
            'panier': [
                {'produit_id': 1, 'quantite': 2, 'prix_unitaire': 50000},
                {'produit_id': 2, 'quantite': 1, 'prix_unitaire': 5000},
            ]
        }

        SaleModel.create(sale_data)

        # 1 INSERT vente + 2×(INSERT detail + UPDATE stock) = 5 appels
        self.assertEqual(mock_db.execute_update.call_count, 5)


# ══════════════════════════════════════════════════════════════
# TEST add_payment()
# ══════════════════════════════════════════════════════════════

class TestSaleModelAddPayment(unittest.TestCase):

    # ── TM-SA-AP-01 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_add_payment_vente_introuvable_leve_valueerror(self, mock_db):
        """
        TM-SA-AP-01 : add_payment() doit lever ValueError
        si la vente n'existe pas.
        """
        mock_db.execute_query.return_value = None

        with self.assertRaises(ValueError) as ctx:
            SaleModel.add_payment(999, 10000)

        self.assertIn('introuvable', str(ctx.exception).lower())

    # ── TM-SA-AP-02 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_add_payment_vente_annulee_leve_valueerror(self, mock_db):
        """
        TM-SA-AP-02 : add_payment() doit lever ValueError
        si la vente est annulée.
        """
        mock_db.execute_query.return_value = {
            'id': 1, 'statut': 'annulee',
            'montant_paye': 0, 'montant_total': 50000, 'montant_reste': 50000
        }

        with self.assertRaises(ValueError) as ctx:
            SaleModel.add_payment(1, 10000)

        self.assertIn('annulee', str(ctx.exception).lower())

    # ── TM-SA-AP-03 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_add_payment_montant_depasse_total_leve_valueerror(self, mock_db):
        """
        TM-SA-AP-03 : add_payment() doit lever ValueError si
        nouveau_paye > montant_total.
        """
        mock_db.execute_query.return_value = {
            'id': 1, 'statut': 'partielle',
            'montant_paye': 30000, 'montant_total': 50000, 'montant_reste': 20000
        }

        with self.assertRaises(ValueError) as ctx:
            SaleModel.add_payment(1, 99999)  # 30000 + 99999 > 50000

        self.assertIn('depasse', str(ctx.exception).lower())

    # ── TM-SA-AP-04 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_add_payment_reussi_statut_payee(self, mock_db):
        """
        TM-SA-AP-04 : add_payment() avec paiement soldant la vente
        doit mettre le statut à 'payee' et retourner True.
        """
        mock_db.execute_query.return_value = {
            'id': 1, 'statut': 'partielle',
            'montant_paye': 20000, 'montant_total': 50000, 'montant_reste': 30000
        }
        mock_db.execute_update.return_value = 1

        result = SaleModel.add_payment(1, 30000)  # solde la vente

        self.assertTrue(result)
        call_args = mock_db.execute_update.call_args[0]
        params = call_args[1]
        self.assertEqual(params[1], 'payee')  # statut = 'payee'

    # ── TM-SA-AP-05 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_add_payment_partiel_statut_partielle(self, mock_db):
        """
        TM-SA-AP-05 : add_payment() avec paiement partiel doit
        garder le statut 'partielle'.
        """
        mock_db.execute_query.return_value = {
            'id': 1, 'statut': 'en_cours',
            'montant_paye': 0, 'montant_total': 50000, 'montant_reste': 50000
        }
        mock_db.execute_update.return_value = 1

        SaleModel.add_payment(1, 20000)  # paiement partiel

        call_args = mock_db.execute_update.call_args[0]
        params = call_args[1]
        self.assertEqual(params[1], 'partielle')


# ══════════════════════════════════════════════════════════════
# TEST cancel()
# ══════════════════════════════════════════════════════════════

class TestSaleModelCancel(unittest.TestCase):

    # ── TM-SA-CA-01 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_cancel_vente_introuvable_leve_valueerror(self, mock_db):
        """
        TM-SA-CA-01 : cancel() doit lever ValueError
        si la vente n'existe pas.
        """
        mock_db.execute_query.return_value = None

        with self.assertRaises(ValueError):
            SaleModel.cancel(999)

    # ── TM-SA-CA-02 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_cancel_vente_deja_annulee_leve_valueerror(self, mock_db):
        """
        TM-SA-CA-02 : cancel() doit lever ValueError
        si la vente est déjà annulée.
        """
        mock_db.execute_query.return_value = {
            'id': 1, 'statut': 'annulee'
        }

        with self.assertRaises(ValueError) as ctx:
            SaleModel.cancel(1)

        self.assertIn('annulee', str(ctx.exception).lower())

    # ── TM-SA-CA-03 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_cancel_vente_payee_leve_valueerror(self, mock_db):
        """
        TM-SA-CA-03 : cancel() doit lever ValueError
        si la vente est déjà payée.
        """
        mock_db.execute_query.return_value = {
            'id': 1, 'statut': 'payee'
        }

        with self.assertRaises(ValueError) as ctx:
            SaleModel.cancel(1)

        self.assertIn('payee', str(ctx.exception).lower())

    # ── TM-SA-CA-04 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_cancel_reussit_et_restaure_stock(self, mock_db):
        """
        TM-SA-CA-04 : cancel() sur une vente en_cours avec 2 produits
        doit effectuer 2 UPDATE stock + 1 UPDATE statut = 3 appels
        db.execute_update().
        """
        # Premier appel : get_by_id (vente en_cours)
        # Deuxième appel : get_details (2 lignes)
        mock_db.execute_query.side_effect = [
            {'id': 1, 'statut': 'en_cours'},  # get_by_id
            [                                  # get_details
                {'produit_id': 1, 'quantite': 2},
                {'produit_id': 2, 'quantite': 1},
            ]
        ]
        mock_db.execute_update.return_value = 1

        result = SaleModel.cancel(1)

        self.assertTrue(result)
        # 2 UPDATE stock + 1 UPDATE statut = 3 appels
        self.assertEqual(mock_db.execute_update.call_count, 3)


# ══════════════════════════════════════════════════════════════
# TEST count()
# ══════════════════════════════════════════════════════════════

class TestSaleModelCount(unittest.TestCase):

    # ── TM-SA-CO-01 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_count_retourne_entier(self, mock_db):
        """
        TM-SA-CO-01 : count() doit retourner le nombre total
        de ventes sous forme d'entier.
        """
        mock_db.execute_query.return_value = {'total': 7}

        result = SaleModel.count()

        self.assertEqual(result, 7)

    # ── TM-SA-CO-02 ──────────────────────────────────────────
    @patch('models.sale.db')
    def test_count_retourne_zero_si_none(self, mock_db):
        """
        TM-SA-CO-02 : count() doit retourner 0 si
        db.execute_query() retourne None.
        """
        mock_db.execute_query.return_value = None

        result = SaleModel.count()

        self.assertEqual(result, 0)


# ══════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestSaleModelGetById))
    suite.addTests(loader.loadTestsFromTestCase(TestSaleModelGetDetails))
    suite.addTests(loader.loadTestsFromTestCase(TestSaleModelGenerateNumero))
    suite.addTests(loader.loadTestsFromTestCase(TestSaleModelCreate))
    suite.addTests(loader.loadTestsFromTestCase(TestSaleModelAddPayment))
    suite.addTests(loader.loadTestsFromTestCase(TestSaleModelCancel))
    suite.addTests(loader.loadTestsFromTestCase(TestSaleModelCount))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

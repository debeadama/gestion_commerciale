"""
tests/test_sale_controller.py
------------------------------
Tests unitaires de SaleController.

Méthodes testées :
  - create()      : panier vide, stock insuffisant, calcul total,
                    statuts payee/partielle/en_cours, montant négatif,
                    montant > total, succès
  - cancel()      : vente introuvable, déjà annulée, déjà payée, succès
  - validate()    : permission insuffisante, vente introuvable,
                    statut non validable, succès
  - add_payment() : vente introuvable, déjà payée, montant invalide,
                    montant > reste, succès

Architecture : méthodes @staticmethod — SaleModel, ProductModel et
SessionManager sont mockés avec @patch.

Pour exécuter :
    python tests/test_sale_controller.py
    ou
    python -m pytest tests/test_sale_controller.py -v
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch, MagicMock
from controllers.sale_controller import SaleController


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def make_panier(produit_id=1, quantite=2, prix=50000):
    return [{'produit_id': produit_id, 'quantite': quantite, 'prix_unitaire': prix}]

def make_produit(stock=10, nom='Câble USB'):
    return {'id': 1, 'nom': nom, 'stock_actuel': stock}


# ══════════════════════════════════════════════════════════════
# TEST create()
# ══════════════════════════════════════════════════════════════

class TestSaleControllerCreate(unittest.TestCase):
    """Tests de SaleController.create()."""

    # ── TC-SC-01 ─────────────────────────────────────────────
    def test_panier_vide_retourne_erreur(self):
        """
        TC-SC-01 : create() avec panier vide doit retourner
        (False, message) sans interroger la base.
        """
        ok, msg = SaleController.create(client_id=1, panier=[], montant_paye=0)

        self.assertFalse(ok)
        self.assertIn('vide', msg.lower())

    # ── TC-SC-02 ─────────────────────────────────────────────
    @patch('controllers.sale_controller.ProductModel.get_by_id', return_value=None)
    def test_produit_introuvable_retourne_erreur(self, mock_get):
        """
        TC-SC-02 : create() avec un produit inexistant dans le panier
        doit retourner (False, message).
        """
        ok, msg = SaleController.create(
            client_id=1,
            panier=[{'produit_id': 999, 'quantite': 1, 'prix_unitaire': 5000}],
            montant_paye=5000
        )

        self.assertFalse(ok)
        self.assertIn('introuvable', msg.lower())

    # ── TC-SC-03 ─────────────────────────────────────────────
    @patch('controllers.sale_controller.ProductModel.get_by_id',
           return_value=make_produit(stock=2))
    def test_stock_insuffisant_retourne_erreur(self, mock_get):
        """
        TC-SC-03 : create() avec quantité demandée > stock disponible
        doit retourner (False, message contenant 'insuffisant').
        """
        ok, msg = SaleController.create(
            client_id=1,
            panier=make_panier(quantite=10),  # stock = 2
            montant_paye=0
        )

        self.assertFalse(ok)
        self.assertIn('insuffisant', msg.lower())

    # ── TC-SC-04 ─────────────────────────────────────────────
    @patch('controllers.sale_controller.ProductModel.get_by_id',
           return_value=make_produit(stock=10))
    def test_montant_paye_negatif_retourne_erreur(self, mock_get):
        """
        TC-SC-04 : create() avec montant_paye négatif doit
        retourner (False, message).
        """
        ok, msg = SaleController.create(
            client_id=1,
            panier=make_panier(quantite=1, prix=50000),
            montant_paye=-100
        )

        self.assertFalse(ok)
        self.assertIn('negatif', msg.lower())

    # ── TC-SC-05 ─────────────────────────────────────────────
    @patch('controllers.sale_controller.ProductModel.get_by_id',
           return_value=make_produit(stock=10))
    def test_montant_paye_superieur_au_total_retourne_erreur(self, mock_get):
        """
        TC-SC-05 : create() avec montant_paye > montant_total
        doit retourner (False, message).
        """
        # 1 produit à 50 000 → total = 50 000
        ok, msg = SaleController.create(
            client_id=1,
            panier=make_panier(quantite=1, prix=50000),
            montant_paye=999999  # > 50 000
        )

        self.assertFalse(ok)
        self.assertIn('depasse', msg.lower())

    # ── TC-SC-06 ─────────────────────────────────────────────
    @patch('controllers.sale_controller.SessionManager.get_current_user',
           return_value={'id': 1, 'role': 'admin'})
    @patch('controllers.sale_controller.SaleModel.create', return_value=7)
    @patch('controllers.sale_controller.ProductModel.get_by_id',
           return_value=make_produit(stock=10))
    def test_paiement_complet_statut_payee(self, mock_get, mock_create, mock_user):
        """
        TC-SC-06 : Quand montant_paye = montant_total, le statut
        dans sale_data doit être 'payee'.
        """
        # 1 produit à 50 000 → total = 50 000, paye = 50 000
        ok, sale_id = SaleController.create(
            client_id=1,
            panier=make_panier(quantite=1, prix=50000),
            montant_paye=50000
        )

        self.assertTrue(ok)
        self.assertEqual(sale_id, 7)
        sale_data_arg = mock_create.call_args[0][0]
        self.assertEqual(sale_data_arg['statut'], 'payee')

    # ── TC-SC-07 ─────────────────────────────────────────────
    @patch('controllers.sale_controller.SessionManager.get_current_user',
           return_value={'id': 1, 'role': 'admin'})
    @patch('controllers.sale_controller.SaleModel.create', return_value=8)
    @patch('controllers.sale_controller.ProductModel.get_by_id',
           return_value=make_produit(stock=10))
    def test_paiement_zero_statut_en_cours(self, mock_get, mock_create, mock_user):
        """
        TC-SC-07 : Quand montant_paye = 0, le statut doit être 'en_cours'.
        """
        ok, sale_id = SaleController.create(
            client_id=1,
            panier=make_panier(quantite=1, prix=50000),
            montant_paye=0
        )

        self.assertTrue(ok)
        sale_data_arg = mock_create.call_args[0][0]
        self.assertEqual(sale_data_arg['statut'], 'en_cours')

    # ── TC-SC-08 ─────────────────────────────────────────────
    @patch('controllers.sale_controller.SessionManager.get_current_user',
           return_value={'id': 1, 'role': 'admin'})
    @patch('controllers.sale_controller.SaleModel.create', return_value=9)
    @patch('controllers.sale_controller.ProductModel.get_by_id',
           return_value=make_produit(stock=10))
    def test_paiement_partiel_statut_partielle(self, mock_get, mock_create, mock_user):
        """
        TC-SC-08 : Quand 0 < montant_paye < montant_total,
        le statut doit être 'partielle'.
        """
        ok, sale_id = SaleController.create(
            client_id=1,
            panier=make_panier(quantite=1, prix=50000),
            montant_paye=25000   # < 50 000
        )

        self.assertTrue(ok)
        sale_data_arg = mock_create.call_args[0][0]
        self.assertEqual(sale_data_arg['statut'], 'partielle')

    # ── TC-SC-09 ─────────────────────────────────────────────
    @patch('controllers.sale_controller.SessionManager.get_current_user',
           return_value={'id': 1, 'role': 'admin'})
    @patch('controllers.sale_controller.SaleModel.create',
           side_effect=Exception("Erreur SQL"))
    @patch('controllers.sale_controller.ProductModel.get_by_id',
           return_value=make_produit(stock=10))
    def test_exception_bdd_retourne_erreur(self, mock_get, mock_create, mock_user):
        """
        TC-SC-09 : Si SaleModel.create() lève une exception,
        create() doit retourner (False, message).
        """
        ok, msg = SaleController.create(
            client_id=1,
            panier=make_panier(quantite=1, prix=50000),
            montant_paye=50000
        )

        self.assertFalse(ok)
        self.assertIsInstance(msg, str)


# ══════════════════════════════════════════════════════════════
# TEST cancel()
# ══════════════════════════════════════════════════════════════

class TestSaleControllerCancel(unittest.TestCase):
    """Tests de SaleController.cancel()."""

    # ── TC-SCA-01 ────────────────────────────────────────────
    @patch('controllers.sale_controller.SaleModel.get_by_id', return_value=None)
    def test_vente_introuvable_retourne_erreur(self, mock_get):
        """
        TC-SCA-01 : cancel() avec un ID inexistant doit
        retourner (False, message).
        """
        ok, msg = SaleController.cancel(999)

        self.assertFalse(ok)
        self.assertIn('introuvable', msg.lower())

    # ── TC-SCA-02 ────────────────────────────────────────────
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value={'id': 1, 'statut': 'annulee'})
    def test_vente_deja_annulee_retourne_erreur(self, mock_get):
        """
        TC-SCA-02 : cancel() sur une vente déjà annulée doit
        retourner (False, message) sans modifier la base.
        """
        ok, msg = SaleController.cancel(1)

        self.assertFalse(ok)
        self.assertIn('annulee', msg.lower())

    # ── TC-SCA-03 ────────────────────────────────────────────
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value={'id': 1, 'statut': 'payee'})
    def test_vente_payee_ne_peut_pas_etre_annulee(self, mock_get):
        """
        TC-SCA-03 : cancel() sur une vente payée doit
        retourner (False, message).
        """
        ok, msg = SaleController.cancel(1)

        self.assertFalse(ok)
        self.assertIn('payee', msg.lower())

    # ── TC-SCA-04 ────────────────────────────────────────────
    @patch('controllers.sale_controller.SaleModel.cancel')
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value={'id': 1, 'statut': 'en_cours'})
    def test_annulation_en_cours_reussit(self, mock_get, mock_cancel):
        """
        TC-SCA-04 : cancel() sur une vente en_cours doit
        retourner (True, message) et appeler SaleModel.cancel().
        """
        ok, msg = SaleController.cancel(1)

        self.assertTrue(ok)
        mock_cancel.assert_called_once_with(1)

    # ── TC-SCA-05 ────────────────────────────────────────────
    @patch('controllers.sale_controller.SaleModel.cancel')
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value={'id': 2, 'statut': 'partielle'})
    def test_annulation_partielle_reussit(self, mock_get, mock_cancel):
        """
        TC-SCA-05 : cancel() sur une vente partielle doit
        retourner (True, message).
        """
        ok, msg = SaleController.cancel(2)

        self.assertTrue(ok)
        mock_cancel.assert_called_once_with(2)


# ══════════════════════════════════════════════════════════════
# TEST validate()
# ══════════════════════════════════════════════════════════════

class TestSaleControllerValidate(unittest.TestCase):
    """Tests de SaleController.validate()."""

    # ── TC-SV-01 ─────────────────────────────────────────────
    @patch('controllers.sale_controller.SessionManager.has_permission',
           return_value=False)
    def test_permission_insuffisante_retourne_erreur(self, mock_perm):
        """
        TC-SV-01 : validate() sans la permission 'view_reports'
        doit retourner (False, message) sans interroger la base.
        """
        ok, msg = SaleController.validate(1)

        self.assertFalse(ok)
        self.assertIn('permission', msg.lower())

    # ── TC-SV-02 ─────────────────────────────────────────────
    @patch('controllers.sale_controller.SaleModel.get_by_id', return_value=None)
    @patch('controllers.sale_controller.SessionManager.has_permission',
           return_value=True)
    def test_vente_introuvable_retourne_erreur(self, mock_perm, mock_get):
        """
        TC-SV-02 : validate() avec un ID inexistant doit
        retourner (False, message).
        """
        ok, msg = SaleController.validate(999)

        self.assertFalse(ok)
        self.assertIn('introuvable', msg.lower())

    # ── TC-SV-03 ─────────────────────────────────────────────
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value={'id': 1, 'statut': 'payee', 'montant_reste': 0})
    @patch('controllers.sale_controller.SessionManager.has_permission',
           return_value=True)
    def test_vente_deja_payee_non_validable(self, mock_perm, mock_get):
        """
        TC-SV-03 : validate() sur une vente déjà payée doit
        retourner (False, message).
        """
        ok, msg = SaleController.validate(1)

        self.assertFalse(ok)

    # ── TC-SV-04 ─────────────────────────────────────────────
    @patch('controllers.sale_controller.SaleModel.validate')
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value={'id': 1, 'statut': 'en_cours', 'montant_reste': 50000})
    @patch('controllers.sale_controller.SessionManager.has_permission',
           return_value=True)
    def test_validation_en_cours_reussit(self, mock_perm, mock_get, mock_validate):
        """
        TC-SV-04 : validate() sur une vente en_cours avec permission
        doit retourner (True, message).
        """
        ok, msg = SaleController.validate(1)

        self.assertTrue(ok)
        mock_validate.assert_called_once_with(1, 50000.0)


# ══════════════════════════════════════════════════════════════
# TEST add_payment()
# ══════════════════════════════════════════════════════════════

class TestSaleControllerAddPayment(unittest.TestCase):
    """Tests de SaleController.add_payment()."""

    # ── TC-SP-01 ─────────────────────────────────────────────
    @patch('controllers.sale_controller.SaleModel.get_by_id', return_value=None)
    def test_vente_introuvable_retourne_erreur(self, mock_get):
        """
        TC-SP-01 : add_payment() avec un ID inexistant doit
        retourner (False, message).
        """
        ok, msg = SaleController.add_payment(999, 10000)

        self.assertFalse(ok)
        self.assertIn('introuvable', msg.lower())

    # ── TC-SP-02 ─────────────────────────────────────────────
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value={'id': 1, 'statut': 'payee', 'montant_reste': 0})
    def test_vente_deja_payee_retourne_erreur(self, mock_get):
        """
        TC-SP-02 : add_payment() sur une vente payée doit
        retourner (False, message).
        """
        ok, msg = SaleController.add_payment(1, 5000)

        self.assertFalse(ok)
        self.assertIn('payee', msg.lower())

    # ── TC-SP-03 ─────────────────────────────────────────────
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value={'id': 1, 'statut': 'partielle', 'montant_reste': 30000})
    def test_montant_negatif_retourne_erreur(self, mock_get):
        """
        TC-SP-03 : add_payment() avec montant <= 0 doit
        retourner (False, message).
        """
        ok, msg = SaleController.add_payment(1, -500)

        self.assertFalse(ok)

    # ── TC-SP-04 ─────────────────────────────────────────────
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value={'id': 1, 'statut': 'partielle', 'montant_reste': 30000})
    def test_montant_superieur_au_reste_retourne_erreur(self, mock_get):
        """
        TC-SP-04 : add_payment() avec montant > montant_reste doit
        retourner (False, message).
        """
        ok, msg = SaleController.add_payment(1, 99999)  # reste = 30 000

        self.assertFalse(ok)
        self.assertIn('depasse', msg.lower())

    # ── TC-SP-05 ─────────────────────────────────────────────
    @patch('controllers.sale_controller.SaleModel.add_payment')
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value={'id': 1, 'statut': 'partielle', 'montant_reste': 30000})
    def test_paiement_solde_retourne_message_solde(self, mock_get, mock_pay):
        """
        TC-SP-05 : add_payment() avec montant = montant_reste doit
        retourner (True, 'Vente soldee.').
        """
        ok, msg = SaleController.add_payment(1, 30000)

        self.assertTrue(ok)
        self.assertIn('soldee', msg.lower())


# ══════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestSaleControllerCreate))
    suite.addTests(loader.loadTestsFromTestCase(TestSaleControllerCancel))
    suite.addTests(loader.loadTestsFromTestCase(TestSaleControllerValidate))
    suite.addTests(loader.loadTestsFromTestCase(TestSaleControllerAddPayment))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

"""
tests/test_sale_integration.py
-------------------------------
Tests d'integration de SaleController couvrant les scenarios complexes :
  - Annulation avec remise en stock
  - Paiement partiel puis solde complet
  - Vente avec stock insuffisant (plusieurs produits)
  - Arrondis flottants sur montant_paye == montant_total
  - Blocage du rate-limiting apres 5 tentatives

Pour executer :
    python -m pytest tests/test_sale_integration.py -v
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from controllers.sale_controller import SaleController
from controllers.auth_controller import SessionManager


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def make_produit(id=1, nom='Produit A', stock=10):
    return {'id': id, 'nom': nom, 'stock_actuel': stock}


def make_vente(id=1, statut='en_cours', total=100000, paye=50000, reste=50000):
    return {
        'id': id,
        'statut': statut,
        'montant_total': total,
        'montant_paye': paye,
        'montant_reste': reste,
    }


# ──────────────────────────────────────────────────────────────
# Scenario 1 : Annulation avec remise en stock
# ──────────────────────────────────────────────────────────────

class TestAnnulationRemiseStock(unittest.TestCase):
    """
    Verifie que cancel() delegue au modele qui remet le stock a jour.
    """

    @patch('controllers.sale_controller.SaleModel.cancel')
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='en_cours'))
    def test_annulation_en_cours_appelle_cancel(self, mock_get, mock_cancel):
        """Annuler une vente en_cours doit appeler SaleModel.cancel."""
        ok, msg = SaleController.cancel(1)
        self.assertTrue(ok)
        mock_cancel.assert_called_once_with(1)
        self.assertIn('annulee', msg.lower())

    @patch('controllers.sale_controller.SaleModel.cancel')
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='partielle'))
    def test_annulation_partielle_appelle_cancel(self, mock_get, mock_cancel):
        """Annuler une vente partielle doit aussi appeler SaleModel.cancel."""
        ok, msg = SaleController.cancel(1)
        self.assertTrue(ok)
        mock_cancel.assert_called_once_with(1)

    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='payee'))
    def test_annulation_vente_payee_refusee(self, mock_get):
        """Une vente payee ne peut pas etre annulee."""
        ok, msg = SaleController.cancel(1)
        self.assertFalse(ok)
        self.assertIn('payee', msg.lower())

    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='annulee'))
    def test_annulation_deja_annulee_refusee(self, mock_get):
        """Une vente deja annulee ne peut pas l'etre a nouveau."""
        ok, msg = SaleController.cancel(1)
        self.assertFalse(ok)
        self.assertIn('annulee', msg.lower())


# ──────────────────────────────────────────────────────────────
# Scenario 2 : Paiement partiel puis solde complet
# ──────────────────────────────────────────────────────────────

class TestPaiementPartielPuisSolde(unittest.TestCase):
    """
    Simule le cycle : vente creee → paiement partiel → solde final.
    """

    @patch('controllers.sale_controller.SaleModel.add_payment')
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='en_cours', reste=100000))
    def test_premier_paiement_partiel(self, mock_get, mock_pay):
        """Premier paiement partiel : retourne True et mentionne le reste."""
        ok, msg = SaleController.add_payment(1, 40000)
        self.assertTrue(ok)
        self.assertIn('reste', msg.lower())
        mock_pay.assert_called_once_with(1, 40000)

    @patch('controllers.sale_controller.SaleModel.add_payment')
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='partielle', paye=40000, reste=60000))
    def test_deuxieme_paiement_partiel(self, mock_get, mock_pay):
        """Deuxieme paiement partiel sur une vente deja partielle."""
        ok, msg = SaleController.add_payment(1, 30000)
        self.assertTrue(ok)
        self.assertIn('reste', msg.lower())

    @patch('controllers.sale_controller.SaleModel.add_payment')
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='partielle', paye=70000, reste=30000))
    def test_solde_final(self, mock_get, mock_pay):
        """Dernier paiement qui solde la vente."""
        ok, msg = SaleController.add_payment(1, 30000)
        self.assertTrue(ok)
        self.assertIn('solde', msg.lower())

    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='payee', reste=0))
    def test_paiement_sur_vente_soldee_refuse(self, mock_get):
        """Impossible de payer une vente deja soldee."""
        ok, msg = SaleController.add_payment(1, 1000)
        self.assertFalse(ok)

    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='en_cours', reste=50000))
    def test_paiement_superieur_au_reste_refuse(self, mock_get):
        """Paiement superieur au reste refuse."""
        ok, msg = SaleController.add_payment(1, 99999)
        self.assertFalse(ok)
        self.assertIn('depasse', msg.lower())


# ──────────────────────────────────────────────────────────────
# Scenario 3 : Panier multi-produits avec stock insuffisant
# ──────────────────────────────────────────────────────────────

class TestPanierMultiProduits(unittest.TestCase):
    """
    Vente avec plusieurs produits : un seul en rupture bloque toute la vente.
    """

    def _make_produits_side_effect(self, stocks):
        """Cree un side_effect qui retourne chaque produit a tour de role."""
        produits = [
            make_produit(id=i + 1, nom=f'Produit {i + 1}', stock=s)
            for i, s in enumerate(stocks)
        ]
        return produits.__iter__().__next__, produits

    @patch('controllers.sale_controller.ProductModel.get_by_id')
    def test_deuxieme_produit_en_rupture_bloque_vente(self, mock_get):
        """Si le 2e produit est en rupture, la vente est refusee."""
        mock_get.side_effect = [
            make_produit(id=1, stock=10),  # OK
            make_produit(id=2, stock=1),   # Stock insuffisant
        ]
        panier = [
            {'produit_id': 1, 'quantite': 2, 'prix_unitaire': 10000},
            {'produit_id': 2, 'quantite': 5, 'prix_unitaire': 5000},
        ]
        ok, msg = SaleController.create(
            client_id=1, panier=panier, montant_paye=0
        )
        self.assertFalse(ok)
        self.assertIn('insuffisant', msg.lower())

    @patch('controllers.sale_controller.SessionManager.get_current_user',
           return_value={'id': 1})
    @patch('controllers.sale_controller.SaleModel.create', return_value=10)
    @patch('controllers.sale_controller.ProductModel.get_by_id')
    def test_tous_produits_en_stock_vente_creee(
            self, mock_get, mock_create, mock_user):
        """Si tous les produits sont en stock, la vente est creee."""
        mock_get.side_effect = [
            make_produit(id=1, stock=10),
            make_produit(id=2, stock=10),
        ]
        panier = [
            {'produit_id': 1, 'quantite': 2, 'prix_unitaire': 10000},
            {'produit_id': 2, 'quantite': 3, 'prix_unitaire': 5000},
        ]
        ok, sid = SaleController.create(
            client_id=1, panier=panier, montant_paye=35000
        )
        self.assertTrue(ok)
        self.assertEqual(sid, 10)


# ──────────────────────────────────────────────────────────────
# Scenario 4 : Arrondi flottant montant_paye == montant_total
# ──────────────────────────────────────────────────────────────

class TestArrondisFlottants(unittest.TestCase):
    """
    Verifie que les comparaisons flottantes ne rejettent pas
    des paiements valides a cause d'imprecisions d'arrondi.
    """

    @patch('controllers.sale_controller.SessionManager.get_current_user',
           return_value={'id': 1})
    @patch('controllers.sale_controller.SaleModel.create', return_value=11)
    @patch('controllers.sale_controller.ProductModel.get_by_id',
           return_value=make_produit(stock=10))
    def test_paiement_exact_avec_arrondi(self, mock_get, mock_create, mock_user):
        """
        0.1 + 0.2 = 0.30000000000000004 en Python.
        Le controlleur doit arrondir avant la comparaison.
        """
        panier = [{'produit_id': 1, 'quantite': 1, 'prix_unitaire': 0.3}]
        montant_paye = 0.1 + 0.2  # = 0.30000000000000004

        ok, result = SaleController.create(
            client_id=1, panier=panier, montant_paye=montant_paye
        )
        self.assertTrue(ok, f"Le paiement exact avec arrondi doit reussir : {result}")
        sale_data = mock_create.call_args[0][0]
        self.assertEqual(sale_data['statut'], 'payee')


# ──────────────────────────────────────────────────────────────
# Scenario 5 : Rate-limiting apres 5 tentatives echouees
# ──────────────────────────────────────────────────────────────

class TestRateLimiting(unittest.TestCase):
    """
    Verifie que SessionManager bloque un compte apres 5 echecs.
    """

    def setUp(self):
        """Remet les compteurs a zero avant chaque test."""
        SessionManager._login_attempts.clear()
        SessionManager.logout()

    def tearDown(self):
        SessionManager._login_attempts.clear()
        SessionManager.logout()

    @patch('controllers.auth_controller.UserModel.get_by_username',
           return_value=None)
    def test_cinq_echecs_bloquent_le_compte(self, mock_get):
        """Apres 5 echecs, le 6e tentative doit retourner un message de blocage."""
        username = 'test_user_rl'
        for _ in range(5):
            SessionManager.login(username, 'mauvais_mdp')

        ok, msg = SessionManager.login(username, 'mauvais_mdp')
        self.assertFalse(ok)
        self.assertIn('bloque', msg.lower())

    @patch('controllers.auth_controller.UserModel.get_by_username',
           return_value=None)
    def test_quatre_echecs_ne_bloquent_pas(self, mock_get):
        """4 echecs consecutifs ne doivent pas encore bloquer."""
        username = 'test_user_rl2'
        for _ in range(4):
            SessionManager.login(username, 'mauvais_mdp')

        ok, msg = SessionManager.login(username, 'mauvais_mdp')
        # Doit echouer pour mauvais mdp, pas pour blocage
        self.assertFalse(ok)
        self.assertNotIn('bloque', msg.lower())

    @patch('controllers.auth_controller.UserModel.verify_password',
           return_value=True)
    @patch('controllers.auth_controller.UserModel.get_by_username')
    @patch('controllers.auth_controller.UserModel.get_by_username')
    def test_succes_reinitialise_compteur(self, mock_get2, mock_get, mock_verify):
        """Une connexion reussie doit reinitialiser le compteur d'echecs."""
        username = 'test_user_rl3'
        mock_get.return_value = {
            'id': 1, 'username': username,
            'password_hash': '$2b$12$fakehash', 'role': 'vendeur',
        }

        # 3 echecs
        with patch('controllers.auth_controller.UserModel.get_by_username',
                   return_value=None):
            for _ in range(3):
                SessionManager.login(username, 'mauvais')

        # Connexion reussie
        with patch('controllers.auth_controller.UserModel.get_by_username',
                   return_value=mock_get.return_value):
            with patch('controllers.auth_controller.UserModel.verify_password',
                       return_value=True):
                ok, _ = SessionManager.login(username, 'bon_mdp')

        self.assertTrue(ok)
        self.assertNotIn(username, SessionManager._login_attempts)


if __name__ == '__main__':
    unittest.main(verbosity=2)

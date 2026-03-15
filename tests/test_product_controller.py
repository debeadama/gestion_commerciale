"""
tests/test_product_controller.py
---------------------------------
Tests unitaires de ProductController.

Méthodes testées :
  - create()           : validation nom, prix, succès, exception
  - delete()           : succès, ValueError, exception
  - add_stock_movement(): quantité <= 0, produit introuvable,
                          sortie > stock, entrée calcul, succès

Architecture : méthodes @staticmethod — ProductModel et app_cache
sont mockés avec @patch.

Pour exécuter :
    python tests/test_product_controller.py
    ou
    python -m pytest tests/test_product_controller.py -v
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch, MagicMock
from controllers.product_controller import ProductController


# ══════════════════════════════════════════════════════════════
# TEST create()
# ══════════════════════════════════════════════════════════════

class TestProductControllerCreate(unittest.TestCase):
    """Tests de ProductController.create()."""

    # ── TC-PC-01 ─────────────────────────────────────────────
    def test_nom_vide_retourne_erreur(self):
        """
        TC-PC-01 : create() avec nom vide doit retourner
        (False, message) sans appeler le modèle.
        """
        data = {'nom': '', 'prix_vente': 5000}

        ok, msg = ProductController.create(data)

        self.assertFalse(ok)
        self.assertIn('nom', msg.lower())

    # ── TC-PC-02 ─────────────────────────────────────────────
    def test_prix_negatif_retourne_erreur(self):
        """
        TC-PC-02 : create() avec un prix de vente négatif doit
        retourner (False, message) sans appeler le modèle.
        """
        data = {'nom': 'Câble USB', 'prix_vente': -500}

        ok, msg = ProductController.create(data)

        self.assertFalse(ok)
        self.assertIn('prix', msg.lower())

    # ── TC-PC-03 ─────────────────────────────────────────────
    def test_prix_invalide_retourne_erreur(self):
        """
        TC-PC-03 : create() avec un prix non numérique doit
        retourner (False, message).
        """
        data = {'nom': 'Câble USB', 'prix_vente': 'abc'}

        ok, msg = ProductController.create(data)

        self.assertFalse(ok)
        self.assertIn('prix', msg.lower())

    # ── TC-PC-04 ─────────────────────────────────────────────
    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.create', return_value=5)
    def test_creation_reussie_retourne_id(self, mock_create, mock_cache):
        """
        TC-PC-04 : create() avec données valides doit retourner
        (True, id) et invalider le cache low_stock.
        """
        data = {'nom': 'Samsung A55', 'prix_vente': 185000, 'stock_actuel': 10}

        ok, pid = ProductController.create(data)

        self.assertTrue(ok)
        self.assertEqual(pid, 5)
        mock_create.assert_called_once_with(data)
        mock_cache.invalidate.assert_called_once()

    # ── TC-PC-05 ─────────────────────────────────────────────
    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.create',
           side_effect=Exception("Duplicate entry"))
    def test_exception_bdd_retourne_erreur(self, mock_create, mock_cache):
        """
        TC-PC-05 : Si ProductModel.create() lève une exception,
        create() doit retourner (False, message) sans la propager.
        """
        data = {'nom': 'Chargeur', 'prix_vente': 12000}

        ok, msg = ProductController.create(data)

        self.assertFalse(ok)
        self.assertIsInstance(msg, str)


# ══════════════════════════════════════════════════════════════
# TEST delete()
# ══════════════════════════════════════════════════════════════

class TestProductControllerDelete(unittest.TestCase):
    """Tests de ProductController.delete()."""

    # ── TC-PD-01 ─────────────────────────────────────────────
    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.delete')
    def test_suppression_reussie(self, mock_delete, mock_cache):
        """
        TC-PD-01 : delete() doit retourner (True, message) et
        invalider le cache low_stock.
        """
        ok, msg = ProductController.delete(1)

        self.assertTrue(ok)
        mock_delete.assert_called_once_with(1)
        mock_cache.invalidate.assert_called_once()

    # ── TC-PD-02 ─────────────────────────────────────────────
    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.delete',
           side_effect=ValueError("Impossible : ce produit a des ventes associées."))
    def test_suppression_produit_avec_ventes_retourne_erreur(self, mock_delete, mock_cache):
        """
        TC-PD-02 : delete() doit retourner (False, message) quand
        ProductModel.delete() lève une ValueError.
        """
        ok, msg = ProductController.delete(2)

        self.assertFalse(ok)
        self.assertIsInstance(msg, str)


# ══════════════════════════════════════════════════════════════
# TEST add_stock_movement()
# ══════════════════════════════════════════════════════════════

class TestProductControllerStockMovement(unittest.TestCase):
    """Tests de ProductController.add_stock_movement()."""

    # ── TC-SM-01 ─────────────────────────────────────────────
    def test_quantite_zero_retourne_erreur(self):
        """
        TC-SM-01 : add_stock_movement() avec quantité = 0 doit
        retourner (False, message) sans interroger la base.
        """
        ok, msg = ProductController.add_stock_movement(1, 'entree', 0)

        self.assertFalse(ok)
        self.assertIn('quantite', msg.lower())

    # ── TC-SM-02 ─────────────────────────────────────────────
    def test_quantite_negative_retourne_erreur(self):
        """
        TC-SM-02 : add_stock_movement() avec quantité négative doit
        retourner (False, message) sans interroger la base.
        """
        ok, msg = ProductController.add_stock_movement(1, 'sortie', -5)

        self.assertFalse(ok)
        self.assertIn('quantite', msg.lower())

    # ── TC-SM-03 ─────────────────────────────────────────────
    @patch('controllers.product_controller.ProductModel.get_by_id', return_value=None)
    def test_produit_introuvable_retourne_erreur(self, mock_get):
        """
        TC-SM-03 : add_stock_movement() avec un product_id inexistant
        doit retourner (False, 'Produit introuvable.').
        """
        ok, msg = ProductController.add_stock_movement(999, 'entree', 10)

        self.assertFalse(ok)
        self.assertIn('introuvable', msg.lower())

    # ── TC-SM-04 ─────────────────────────────────────────────
    @patch('controllers.product_controller.ProductModel.get_by_id',
           return_value={'id': 1, 'nom': 'Câble USB', 'stock_actuel': 5})
    def test_sortie_superieure_au_stock_retourne_erreur(self, mock_get):
        """
        TC-SM-04 : sortie avec quantité > stock_actuel doit
        retourner (False, message contenant 'insuffisant').
        """
        ok, msg = ProductController.add_stock_movement(1, 'sortie', 10)

        self.assertFalse(ok)
        self.assertIn('insuffisant', msg.lower())

    # ── TC-SM-05 ─────────────────────────────────────────────
    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.apply_stock_movement')
    @patch('controllers.product_controller.ProductModel.get_by_id',
           return_value={'id': 1, 'nom': 'Câble USB', 'stock_actuel': 5})
    def test_sortie_valide_calcule_nouveau_stock(self, mock_get, mock_apply, mock_cache):
        """
        TC-SM-05 : sortie valide (quantité <= stock) doit calculer
        new_stock = stock_actuel - quantité et appeler apply_stock_movement
        avec le bon nouveau stock.
        Stock initial : 5, sortie : 3 → nouveau stock attendu : 2.
        """
        ok, msg = ProductController.add_stock_movement(
            1, 'sortie', 3, motif='Vente', user_id=1)

        self.assertTrue(ok)
        self.assertIn('2', msg)  # nouveau stock = 2

        # Vérification que apply_stock_movement a reçu new_stock=2
        args = mock_apply.call_args[0]
        self.assertEqual(args[5], 2)  # 6ème arg = new_stock

    # ── TC-SM-06 ─────────────────────────────────────────────
    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.apply_stock_movement')
    @patch('controllers.product_controller.ProductModel.get_by_id',
           return_value={'id': 1, 'nom': 'Câble USB', 'stock_actuel': 5})
    def test_entree_calcule_nouveau_stock(self, mock_get, mock_apply, mock_cache):
        """
        TC-SM-06 : entrée doit calculer new_stock = stock_actuel + quantité.
        Stock initial : 5, entrée : 10 → nouveau stock attendu : 15.
        """
        ok, msg = ProductController.add_stock_movement(
            1, 'entree', 10, motif='Réapprovisionnement', user_id=1)

        self.assertTrue(ok)
        self.assertIn('15', msg)  # nouveau stock = 15

        args = mock_apply.call_args[0]
        self.assertEqual(args[5], 15)  # new_stock = 15

    # ── TC-SM-07 ─────────────────────────────────────────────
    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.apply_stock_movement',
           side_effect=Exception("Erreur SQL"))
    @patch('controllers.product_controller.ProductModel.get_by_id',
           return_value={'id': 1, 'nom': 'Câble USB', 'stock_actuel': 10})
    def test_exception_apply_retourne_erreur(self, mock_get, mock_apply, mock_cache):
        """
        TC-SM-07 : Si apply_stock_movement() lève une exception,
        add_stock_movement() doit retourner (False, message).
        """
        ok, msg = ProductController.add_stock_movement(1, 'entree', 5)

        self.assertFalse(ok)
        self.assertIsInstance(msg, str)

    # ── TC-SM-08 ─────────────────────────────────────────────
    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.apply_stock_movement')
    @patch('controllers.product_controller.ProductModel.get_by_id',
           return_value={'id': 1, 'nom': 'Câble USB', 'stock_actuel': 5})
    def test_mouvement_invalide_cache_apres_succes(self, mock_get, mock_apply, mock_cache):
        """
        TC-SM-08 : Après un mouvement réussi, le cache low_stock
        doit être invalidé.
        """
        ProductController.add_stock_movement(1, 'entree', 5)

        mock_cache.invalidate.assert_called_once()


# ══════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestProductControllerCreate))
    suite.addTests(loader.loadTestsFromTestCase(TestProductControllerDelete))
    suite.addTests(loader.loadTestsFromTestCase(TestProductControllerStockMovement))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

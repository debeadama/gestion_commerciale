"""
tests/test_product_controller.py
---------------------------------
Tests unitaires complets de ProductController.
Couvre : get_all, get_by_id, get_categories (cache hit/miss),
         get_low_stock (cache hit/miss), get_movements,
         create, update, delete, add_stock_movement,
         create_category, delete_category, get_dashboard_stats.

Pour exécuter :
    python -m pytest tests/test_product_controller.py -v
"""

from controllers.product_controller import ProductController  # noqa: E402
from unittest.mock import patch, MagicMock  # noqa: E402
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


class TestProductControllerGetAll(unittest.TestCase):

    @patch('controllers.product_controller.ProductModel.get_all',
           return_value=[{'id': 1, 'nom': 'Câble USB'}])
    def test_get_all_sans_filtre(self, mock_get):
        """TC-PGA-01 : get_all() sans filtre retourne la liste du modèle."""
        result = ProductController.get_all()
        self.assertEqual(len(result), 1)
        mock_get.assert_called_once_with(None, None)

    @patch('controllers.product_controller.ProductModel.get_all',
           return_value=[{'id': 2}])
    def test_get_all_avec_recherche_et_categorie(self, mock_get):
        """TC-PGA-02 : get_all() transmet search et category_id au modèle."""
        result = ProductController.get_all(search='HP', category_id=1)
        self.assertEqual(len(result), 1)
        mock_get.assert_called_once_with('HP', 1)

    @patch('controllers.product_controller.ProductModel.get_all',
           return_value=None)
    def test_get_all_retourne_liste_vide_si_none(self, mock_get):
        """TC-PGA-03 : get_all() retourne [] si le modèle retourne None."""
        result = ProductController.get_all()
        self.assertEqual(result, [])



# TEST get_by_id()


class TestProductControllerGetById(unittest.TestCase):

    @patch('controllers.product_controller.ProductModel.get_by_id',
           return_value={'id': 1, 'nom': 'HP Laptop'})
    def test_get_by_id_existant(self, mock_get):
        """TC-PGB-01 : get_by_id() retourne le produit du modèle."""
        result = ProductController.get_by_id(1)
        self.assertEqual(result['nom'], 'HP Laptop')
        mock_get.assert_called_once_with(1)

    @patch('controllers.product_controller.ProductModel.get_by_id',
           return_value=None)
    def test_get_by_id_inexistant(self, mock_get):
        """TC-PGB-02 : get_by_id() retourne None si inexistant."""
        result = ProductController.get_by_id(999)
        self.assertIsNone(result)



# TEST get_categories() — cache hit / miss


class TestProductControllerGetCategories(unittest.TestCase):

    @patch('controllers.product_controller.app_cache')
    def test_get_categories_cache_hit(self, mock_cache):
        """TC-PGC-01 : get_categories() retourne le cache si disponible."""
        mock_cache.get.return_value = [{'id': 1, 'nom': 'Informatique'}]
        result = ProductController.get_categories()
        self.assertEqual(len(result), 1)
        mock_cache.get.assert_called_once()

    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.get_categories',
           return_value=[{'id': 1}, {'id': 2}])
    def test_get_categories_cache_miss(self, mock_model, mock_cache):
        """TC-PGC-02 : cache miss → appel modèle + mise en cache."""
        mock_cache.get.return_value = None
        result = ProductController.get_categories()
        self.assertEqual(len(result), 2)
        mock_model.assert_called_once()
        mock_cache.set.assert_called_once()

    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.get_categories',
           return_value=None)
    def test_get_categories_retourne_liste_vide_si_none(
            self, mock_model, mock_cache):
        """TC-PGC-03 : get_categories() retourne [] si modèle retourne None."""
        mock_cache.get.return_value = None
        result = ProductController.get_categories()
        self.assertEqual(result, [])



# TEST get_low_stock() — cache hit / miss


class TestProductControllerGetLowStock(unittest.TestCase):

    @patch('controllers.product_controller.app_cache')
    def test_get_low_stock_cache_hit(self, mock_cache):
        """TC-PLS-01 : get_low_stock() retourne le cache si disponible."""
        mock_cache.get.return_value = [{'id': 3, 'nom': 'Câble'}]
        result = ProductController.get_low_stock()
        self.assertEqual(len(result), 1)

    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.get_low_stock',
           return_value=[{'id': 1}, {'id': 2}, {'id': 3}])
    def test_get_low_stock_cache_miss(self, mock_model, mock_cache):
        """TC-PLS-02 : cache miss → appel modèle + mise en cache."""
        mock_cache.get.return_value = None
        result = ProductController.get_low_stock()
        self.assertEqual(len(result), 3)
        mock_model.assert_called_once()
        mock_cache.set.assert_called_once()



# TEST get_movements()


class TestProductControllerGetMovements(unittest.TestCase):

    @patch('controllers.product_controller.ProductModel.get_movements',
           return_value=[{'type': 'entree', 'quantite': 10}])
    def test_get_movements_retourne_liste(self, mock_get):
        """TC-PGM-01 : get_movements() retourne les mouvements du modèle."""
        result = ProductController.get_movements(1)
        self.assertEqual(len(result), 1)
        mock_get.assert_called_once_with(1)

    @patch('controllers.product_controller.ProductModel.get_movements',
           return_value=None)
    def test_get_movements_retourne_liste_vide_si_none(self, mock_get):
        """TC-PGM-02 : get_movements() retourne [] si None."""
        result = ProductController.get_movements(99)
        self.assertEqual(result, [])



# TEST create()


class TestProductControllerCreate(unittest.TestCase):

    def test_nom_vide_retourne_erreur(self):
        """TC-PC-01 : create() avec nom vide retourne (False, message)."""
        ok, msg = ProductController.create({'nom': '', 'prix_vente': 5000})
        self.assertFalse(ok)
        self.assertIn('nom', msg.lower())

    def test_prix_negatif_retourne_erreur(self):
        """TC-PC-02 : prix négatif retourne (False, message)."""
        ok, msg = ProductController.create(
            {'nom': 'Câble USB', 'prix_vente': -500})
        self.assertFalse(ok)
        self.assertIn('prix', msg.lower())

    def test_prix_invalide_retourne_erreur(self):
        """TC-PC-03 : prix non numérique retourne (False, message)."""
        ok, msg = ProductController.create(
            {'nom': 'Câble USB', 'prix_vente': 'abc'})
        self.assertFalse(ok)
        self.assertIn('prix', msg.lower())

    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.create',
           return_value=5)
    def test_creation_reussie(self, mock_create, mock_cache):
        """TC-PC-04 : create() valide retourne (True, id)."""
        ok, pid = ProductController.create(
            {'nom': 'Samsung A55', 'prix_vente': 185000})
        self.assertTrue(ok)
        self.assertEqual(pid, 5)
        mock_cache.invalidate.assert_called_once()

    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.create',
           side_effect=Exception("Duplicate entry"))
    def test_exception_bdd_retourne_erreur(self, mock_create, mock_cache):
        """TC-PC-05 : exception BDD retourne (False, message)."""
        ok, msg = ProductController.create(
            {'nom': 'Chargeur', 'prix_vente': 12000})
        self.assertFalse(ok)
        self.assertIsInstance(msg, str)



# TEST update()


class TestProductControllerUpdate(unittest.TestCase):

    def test_update_nom_vide_retourne_erreur(self):
        """TC-PU-01 : update() avec nom vide retourne (False, message)."""
        ok, msg = ProductController.update(1, {'nom': '', 'prix_vente': 5000})
        self.assertFalse(ok)
        self.assertIn('nom', msg.lower())

    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.update')
    def test_update_reussie(self, mock_update, mock_cache):
        """TC-PU-02 : update() valide retourne (True, message)."""
        ok, msg = ProductController.update(
            1, {'nom': 'HP Laptop Pro', 'prix_vente': 400000})
        self.assertTrue(ok)
        mock_update.assert_called_once()
        mock_cache.invalidate.assert_called_once()

    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.update',
           side_effect=Exception("Erreur SQL"))
    def test_update_exception_retourne_erreur(self, mock_update, mock_cache):
        """TC-PU-03 : exception dans update() retourne (False, message)."""
        ok, msg = ProductController.update(
            1, {'nom': 'HP Laptop', 'prix_vente': 350000})
        self.assertFalse(ok)
        self.assertIsInstance(msg, str)



# TEST delete()


class TestProductControllerDelete(unittest.TestCase):

    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.delete')
    def test_suppression_reussie(self, mock_delete, mock_cache):
        """TC-PD-01 : delete() retourne (True, message)
        et invalide le cache."""
        ok, msg = ProductController.delete(1)
        self.assertTrue(ok)
        mock_delete.assert_called_once_with(1)
        mock_cache.invalidate.assert_called_once()

    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.delete',
           side_effect=ValueError("Ce produit a des ventes associées."))
    def test_suppression_produit_avec_ventes(self, mock_delete, mock_cache):
        """TC-PD-02 : ValueError retourne (False, message)."""
        ok, msg = ProductController.delete(2)
        self.assertFalse(ok)
        self.assertIsInstance(msg, str)

    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.delete',
           side_effect=Exception("Connexion perdue"))
    def test_suppression_exception_generique(self, mock_delete, mock_cache):
        """TC-PD-03 : exception générique retourne (False, message)."""
        ok, msg = ProductController.delete(99)
        self.assertFalse(ok)
        self.assertIsInstance(msg, str)



# TEST add_stock_movement()


class TestProductControllerStockMovement(unittest.TestCase):

    def test_quantite_zero_retourne_erreur(self):
        """TC-SM-01 : quantité = 0 retourne (False, message)."""
        ok, msg = ProductController.add_stock_movement(1, 'entree', 0)
        self.assertFalse(ok)
        self.assertIn('quantite', msg.lower())

    def test_quantite_negative_retourne_erreur(self):
        """TC-SM-02 : quantité négative retourne (False, message)."""
        ok, msg = ProductController.add_stock_movement(1, 'sortie', -5)
        self.assertFalse(ok)
        self.assertIn('quantite', msg.lower())

    @patch('controllers.product_controller.ProductModel.get_by_id',
           return_value=None)
    def test_produit_introuvable_retourne_erreur(self, mock_get):
        """TC-SM-03 : produit inexistant retourne (False, 'introuvable')."""
        ok, msg = ProductController.add_stock_movement(999, 'entree', 10)
        self.assertFalse(ok)
        self.assertIn('introuvable', msg.lower())

    @patch('controllers.product_controller.ProductModel.get_by_id',
           return_value={'id': 1, 'nom': 'Câble USB', 'stock_actuel': 5})
    def test_sortie_superieure_au_stock_retourne_erreur(self, mock_get):
        """TC-SM-04 : sortie > stock retourne (False, 'insuffisant')."""
        ok, msg = ProductController.add_stock_movement(1, 'sortie', 10)
        self.assertFalse(ok)
        self.assertIn('insuffisant', msg.lower())

    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.apply_stock_movement')
    @patch('controllers.product_controller.ProductModel.get_by_id',
           return_value={'id': 1, 'nom': 'Câble USB', 'stock_actuel': 5})
    def test_sortie_valide_calcule_nouveau_stock(
            self, mock_get, mock_apply, mock_cache):
        """TC-SM-05 : sortie 3/5 → nouveau stock = 2."""
        ok, msg = ProductController.add_stock_movement(
            1, 'sortie', 3, user_id=1)
        self.assertTrue(ok)
        self.assertIn('2', msg)
        self.assertEqual(mock_apply.call_args[0][5], 2)

    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.apply_stock_movement')
    @patch('controllers.product_controller.ProductModel.get_by_id',
           return_value={'id': 1, 'nom': 'Câble USB', 'stock_actuel': 5})
    def test_entree_calcule_nouveau_stock(
            self, mock_get, mock_apply, mock_cache):
        """TC-SM-06 : entrée 10 + stock 5 → nouveau stock = 15."""
        ok, msg = ProductController.add_stock_movement(
            1, 'entree', 10, user_id=1)
        self.assertTrue(ok)
        self.assertIn('15', msg)
        self.assertEqual(mock_apply.call_args[0][5], 15)

    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.apply_stock_movement',
           side_effect=Exception("Erreur SQL"))
    @patch('controllers.product_controller.ProductModel.get_by_id',
           return_value={'id': 1, 'nom': 'Câble USB', 'stock_actuel': 10})
    def test_exception_apply_retourne_erreur(
            self, mock_get, mock_apply, mock_cache):
        """TC-SM-07 : exception dans apply retourne (False, message)."""
        ok, msg = ProductController.add_stock_movement(1, 'entree', 5)
        self.assertFalse(ok)

    @patch('controllers.product_controller.app_cache')
    @patch('controllers.product_controller.ProductModel.apply_stock_movement')
    @patch('controllers.product_controller.ProductModel.get_by_id',
           return_value={'id': 1, 'nom': 'Câble USB', 'stock_actuel': 5})
    def test_cache_invalide_apres_succes(
            self, mock_get, mock_apply, mock_cache):
        """TC-SM-08 : cache invalidé après mouvement réussi."""
        ProductController.add_stock_movement(1, 'entree', 5)
        mock_cache.invalidate.assert_called_once()



# TEST create_category()


class TestProductControllerCreateCategory(unittest.TestCase):

    def test_nom_vide_retourne_erreur(self):
        """TC-CAT-01 : create_category() nom vide
        retourne (False, message)."""
        ok, msg = ProductController.create_category('')
        self.assertFalse(ok)
        self.assertIn('nom', msg.lower())

    def test_nom_espaces_retourne_erreur(self):
        """TC-CAT-02 : create_category() espaces
        retourne (False, message)."""
        ok, msg = ProductController.create_category('   ')
        self.assertFalse(ok)
        self.assertIn('nom', msg.lower())

    @patch('controllers.product_controller.ProductModel.find_category_by_name',
           return_value={'id': 1, 'nom': 'Informatique'})
    def test_categorie_deja_existante_retourne_erreur(self, mock_find):
        """TC-CAT-03 : categorie existante
        retourne (False, message 'existe')."""
        ok, msg = ProductController.create_category('Informatique')
        self.assertFalse(ok)
        self.assertIn('existe', msg.lower())

    @patch('controllers.product_controller.ProductModel.find_category_by_name',
           return_value=None)
    @patch('controllers.product_controller.ProductModel.create_category',
           return_value=7)
    def test_creation_categorie_reussie(self, mock_create, mock_find):
        """TC-CAT-04 : create_category() valide retourne (True, id)."""
        ok, cid = ProductController.create_category(
            'Électronique', 'Appareils électroniques')
        self.assertTrue(ok)
        self.assertEqual(cid, 7)

    @patch('controllers.product_controller.ProductModel.find_category_by_name',
           return_value=None)
    @patch('controllers.product_controller.ProductModel.create_category',
           side_effect=Exception("Erreur SQL"))
    def test_creation_categorie_exception(self, mock_create, mock_find):
        """TC-CAT-05 : exception retourne (False, message)."""
        ok, msg = ProductController.create_category('Nouvelle')
        self.assertFalse(ok)
        self.assertIsInstance(msg, str)



# TEST delete_category()


class TestProductControllerDeleteCategory(unittest.TestCase):

    @patch('controllers.product_controller.ProductModel.delete_category')
    def test_suppression_categorie_reussie(self, mock_delete):
        """TC-DC-01 : delete_category() réussit retourne (True, message)."""
        ok, msg = ProductController.delete_category(1)
        self.assertTrue(ok)
        mock_delete.assert_called_once_with(1)

    @patch('controllers.product_controller.ProductModel.delete_category',
           side_effect=ValueError("Cette catégorie contient des produits."))
    def test_suppression_categorie_avec_produits(self, mock_delete):
        """TC-DC-02 : ValueError retourne (False, message)."""
        ok, msg = ProductController.delete_category(2)
        self.assertFalse(ok)
        self.assertIsInstance(msg, str)

    @patch('controllers.product_controller.ProductModel.delete_category',
           side_effect=Exception("Connexion perdue"))
    def test_suppression_categorie_exception_generique(self, mock_delete):
        """TC-DC-03 : exception générique retourne (False, message)."""
        ok, msg = ProductController.delete_category(99)
        self.assertFalse(ok)
        self.assertIsInstance(msg, str)



# TEST get_dashboard_stats()


class TestProductControllerDashboard(unittest.TestCase):

    @patch('controllers.product_controller.ProductModel.get_dashboard_stats',
           return_value={'total_produits': 20, 'valeur_stock': 5000000})
    def test_get_dashboard_stats_retourne_dict(self, mock_stats):
        """TC-DS-01 : get_dashboard_stats() retourne le dict du modèle."""
        result = ProductController.get_dashboard_stats()
        self.assertEqual(result['total_produits'], 20)
        mock_stats.assert_called_once()



# POINT D'ENTRÉE


if __name__ == '__main__':
    unittest.main(verbosity=2)

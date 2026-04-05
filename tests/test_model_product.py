"""
tests/test_model_product.py
----------------------------
Tests unitaires de ProductModel.

Méthodes testées :
  - get_all()              : sans/avec filtres
  - get_by_id()            : trouvé, None si absent
  - get_low_stock()        : retourne liste
  - apply_stock_movement() : 2 appels db (UPDATE + INSERT)
  - create()               : retourne ID, champs optionnels à None
  - update()               : bons paramètres transmis
  - delete()               : succès, ValueError si ventes liées
  - update_stock()         : appel avec bon stock et bon ID
  - count()                : retourne entier ou 0

Architecture : méthodes @staticmethod - db est mocké avec @patch.

Pour exécuter :
    python tests/test_model_product.py
    ou
    python -m pytest tests/test_model_product.py -v
"""

from models.product import ProductModel  # noqa: E402
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


class TestProductModelGetAll(unittest.TestCase):

    # ── TM-PR-GA-01 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_get_all_sans_filtre(self, mock_db):
        """
        TM-PR-GA-01 : get_all() sans paramètres doit appeler
        db.execute_query() sans paramètres de filtre.
        """
        mock_db.execute_query.return_value = [
            {'id': 1, 'nom': 'Samsung A55'},
            {'id': 2, 'nom': 'Câble USB'},
        ]

        result = ProductModel.get_all()

        self.assertEqual(len(result), 2)
        mock_db.execute_query.assert_called_once()

    # ── TM-PR-GA-02 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_get_all_avec_recherche(self, mock_db):
        """
        TM-PR-GA-02 : get_all() avec search doit passer
        le pattern en double (nom LIKE, description LIKE).
        """
        mock_db.execute_query.return_value = [{'id': 1, 'nom': 'Samsung A55'}]

        ProductModel.get_all(search='samsung')

        call_args = mock_db.execute_query.call_args[0]
        params = call_args[1]
        self.assertEqual(params, ('%samsung%', '%samsung%'))

    # ── TM-PR-GA-03 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_get_all_avec_category_id(self, mock_db):
        """
        TM-PR-GA-03 : get_all() avec category_id doit passer
        l'ID en paramètre de la requête.
        """
        mock_db.execute_query.return_value = []

        ProductModel.get_all(category_id=2)

        call_args = mock_db.execute_query.call_args[0]
        params = call_args[1]
        self.assertIn(2, params)



# TEST get_by_id()


class TestProductModelGetById(unittest.TestCase):

    # ── TM-PR-GI-01 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_get_by_id_retourne_produit(self, mock_db):
        """
        TM-PR-GI-01 : get_by_id() doit retourner le dict
        du produit quand l'ID existe.
        """
        mock_db.execute_query.return_value = {
            'id': 1, 'nom': 'Samsung A55', 'stock_actuel': 10
        }

        result = ProductModel.get_by_id(1)

        self.assertIsNotNone(result)
        self.assertEqual(result['nom'], 'Samsung A55')

    # ── TM-PR-GI-02 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_get_by_id_retourne_none_si_absent(self, mock_db):
        """
        TM-PR-GI-02 : get_by_id() doit retourner None
        quand le produit n'existe pas.
        """
        mock_db.execute_query.return_value = None

        result = ProductModel.get_by_id(999)

        self.assertIsNone(result)



# TEST get_low_stock()


class TestProductModelGetLowStock(unittest.TestCase):

    # ── TM-PR-LS-01 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_get_low_stock_retourne_produits_critiques(self, mock_db):
        """
        TM-PR-LS-01 : get_low_stock() doit retourner uniquement
        les produits dont stock_actuel <= stock_min.
        """
        mock_db.execute_query.return_value = [
            {'id': 3, 'nom': 'Câble USB', 'stock_actuel': 2, 'stock_min': 5},
            {'id': 7, 'nom': 'Chargeur', 'stock_actuel': 0, 'stock_min': 3},
        ]

        result = ProductModel.get_low_stock()

        self.assertEqual(len(result), 2)
        for p in result:
            self.assertLessEqual(p['stock_actuel'], p['stock_min'])



# TEST apply_stock_movement()


class TestProductModelApplyStockMovement(unittest.TestCase):

    # ── TM-PR-SM-01 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_apply_stock_movement_deux_appels_db(self, mock_db):
        """
        TM-PR-SM-01 : apply_stock_movement() doit effectuer exactement
        2 appels db.execute_update() : UPDATE stock + INSERT mouvement.
        """
        result = ProductModel.apply_stock_movement(
            product_id=1, type_mouvement='entree',
            quantite=10, motif='Réapprovisionnement',
            user_id=1, new_stock=20
        )

        self.assertTrue(result)
        self.assertEqual(mock_db.execute_update.call_count, 2)

    # ── TM-PR-SM-02 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_apply_stock_movement_nouveau_stock_correct(self, mock_db):
        """
        TM-PR-SM-02 : apply_stock_movement() doit passer new_stock=15
        dans le premier UPDATE produits.
        """
        ProductModel.apply_stock_movement(
            product_id=1, type_mouvement='entree',
            quantite=10, motif='Test', user_id=1, new_stock=15
        )

        premier_appel = mock_db.execute_update.call_args_list[0][0]
        params = premier_appel[1]
        self.assertEqual(params[0], 15)   # new_stock
        self.assertEqual(params[1], 1)    # product_id



# TEST create()


class TestProductModelCreate(unittest.TestCase):

    # ── TM-PR-CR-01 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_create_retourne_id_insere(self, mock_db):
        """
        TM-PR-CR-01 : create() doit appeler db.execute_update()
        et retourner l'ID du produit créé.
        """
        mock_db.execute_update.return_value = 5

        data = {
            'nom': 'Samsung A55', 'prix_achat': 120000,
            'prix_vente': 185000, 'stock_actuel': 10,
            'stock_min': 3, 'category_id': 1
        }

        result = ProductModel.create(data)

        self.assertEqual(result, 5)
        mock_db.execute_update.assert_called_once()

    # ── TM-PR-CR-02 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_create_champs_optionnels_none(self, mock_db):
        """
        TM-PR-CR-02 : create() doit convertir description, category_id
        absents en None avant insertion.
        """
        mock_db.execute_update.return_value = 6

        data = {'nom': 'Produit sans catégorie'}

        ProductModel.create(data)

        call_args = mock_db.execute_update.call_args[0]
        params = call_args[1]
        self.assertIsNone(params[1])   # description
        self.assertIsNone(params[6])   # category_id



# TEST update()


class TestProductModelUpdate(unittest.TestCase):

    # ── TM-PR-UP-01 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_update_retourne_true(self, mock_db):
        """
        TM-PR-UP-01 : update() doit appeler db.execute_update()
        et retourner True.
        """
        data = {
            'nom': 'Samsung A55 MAJ', 'prix_achat': 115000,
            'prix_vente': 180000, 'stock_min': 3, 'category_id': 1
        }

        result = ProductModel.update(1, data)

        self.assertTrue(result)
        mock_db.execute_update.assert_called_once()

    # ── TM-PR-UP-02 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_update_transmet_product_id_en_dernier(self, mock_db):
        """
        TM-PR-UP-02 : update() doit placer product_id
        en dernière position dans les paramètres.
        """
        data = {
            'nom': 'Test', 'prix_achat': 0,
            'prix_vente': 0, 'stock_min': 0, 'category_id': None
        }

        ProductModel.update(42, data)

        call_args = mock_db.execute_update.call_args[0]
        params = call_args[1]
        self.assertEqual(params[-1], 42)



# TEST delete()


class TestProductModelDelete(unittest.TestCase):

    # ── TM-PR-DE-01 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_delete_reussit_si_aucune_vente(self, mock_db):
        """
        TM-PR-DE-01 : delete() doit supprimer le produit et retourner
        True quand aucune vente ne le référence.
        """
        mock_db.execute_query.return_value = {'total': 0}
        mock_db.execute_update.return_value = 1

        result = ProductModel.delete(1)

        self.assertTrue(result)
        mock_db.execute_update.assert_called_once()

    # ── TM-PR-DE-02 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_delete_leve_valueerror_si_ventes_liees(self, mock_db):
        """
        TM-PR-DE-02 : delete() doit lever ValueError quand
        le produit est présent dans des ventes.
        """
        mock_db.execute_query.return_value = {'total': 4}

        with self.assertRaises(ValueError) as ctx:
            ProductModel.delete(2)

        self.assertIn('vente', str(ctx.exception).lower())
        mock_db.execute_update.assert_not_called()

    # ── TM-PR-DE-03 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_delete_transmet_bon_id(self, mock_db):
        """
        TM-PR-DE-03 : delete() doit transmettre l'ID exact
        à db.execute_update().
        """
        mock_db.execute_query.return_value = {'total': 0}
        mock_db.execute_update.return_value = 1

        ProductModel.delete(9)

        call_args = mock_db.execute_update.call_args[0]
        params = call_args[1]
        self.assertEqual(params[0], 9)



# TEST update_stock()


class TestProductModelUpdateStock(unittest.TestCase):

    # ── TM-PR-US-01 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_update_stock_appelle_execute_update(self, mock_db):
        """
        TM-PR-US-01 : update_stock() doit appeler db.execute_update()
        avec new_stock et product_id corrects, et retourner True.
        """
        result = ProductModel.update_stock(product_id=3, new_stock=25)

        self.assertTrue(result)
        mock_db.execute_update.assert_called_once()
        call_args = mock_db.execute_update.call_args[0]
        params = call_args[1]
        self.assertEqual(params[0], 25)  # new_stock
        self.assertEqual(params[1], 3)   # product_id



# TEST count()


class TestProductModelCount(unittest.TestCase):

    # ── TM-PR-CO-01 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_count_retourne_entier(self, mock_db):
        """
        TM-PR-CO-01 : count() doit retourner le nombre total
        de produits sous forme d'entier.
        """
        mock_db.execute_query.return_value = {'total': 20}

        result = ProductModel.count()

        self.assertEqual(result, 20)

    # ── TM-PR-CO-02 ──────────────────────────────────────────
    @patch('models.product.db')
    def test_count_retourne_zero_si_none(self, mock_db):
        """
        TM-PR-CO-02 : count() doit retourner 0 si
        db.execute_query() retourne None.
        """
        mock_db.execute_query.return_value = None

        result = ProductModel.count()

        self.assertEqual(result, 0)



# TEST get_categories()


class TestProductModelGetCategories(unittest.TestCase):

    @patch('models.product.db')
    def test_get_categories_retourne_liste(self, mock_db):
        """TC-PMC-01 : get_categories() retourne toutes les catégories."""
        mock_db.execute_query.return_value = [
            {'id': 1, 'nom': 'Informatique'},
            {'id': 2, 'nom': 'Téléphonie'},
        ]
        result = ProductModel.get_categories()
        self.assertEqual(len(result), 2)
        call_sql = mock_db.execute_query.call_args[0][0]
        self.assertIn('categories', call_sql)
        self.assertIn('ORDER BY', call_sql)

    @patch('models.product.db')
    def test_get_categories_vide(self, mock_db):
        """TC-PMC-02 : get_categories() retourne [] si aucune catégorie."""
        mock_db.execute_query.return_value = []
        result = ProductModel.get_categories()
        self.assertEqual(result, [])



# TEST get_movements()


class TestProductModelGetMovements(unittest.TestCase):

    @patch('models.product.db')
    def test_get_movements_retourne_historique(self, mock_db):
        """TC-PMM-01 : get_movements() retourne les mouvements du produit."""
        mock_db.execute_query.return_value = [
            {'type_mouvement': 'entree', 'quantite': 10},
            {'type_mouvement': 'sortie', 'quantite': 3},
        ]
        result = ProductModel.get_movements(1)
        self.assertEqual(len(result), 2)
        params = mock_db.execute_query.call_args[0][1]
        self.assertEqual(params, (1,))

    @patch('models.product.db')
    def test_get_movements_vide(self, mock_db):
        """TC-PMM-02 : get_movements() retourne [] si aucun mouvement."""
        mock_db.execute_query.return_value = []
        result = ProductModel.get_movements(999)
        self.assertEqual(result, [])

    @patch('models.product.db')
    def test_get_movements_sql_filtre_par_produit(self, mock_db):
        """TC-PMM-03 : la requête SQL filtre par produit_id."""
        mock_db.execute_query.return_value = []
        ProductModel.get_movements(5)
        call_sql = mock_db.execute_query.call_args[0][0]
        self.assertIn('produit_id', call_sql)



# TEST find_category_by_name()


class TestProductModelFindCategoryByName(unittest.TestCase):

    @patch('models.product.db')
    def test_find_category_existante(self, mock_db):
        """TC-PMF-01 : find_category_by_name()
        retourne la categorie si elle existe."""
        mock_db.execute_query.return_value = {'id': 1}
        result = ProductModel.find_category_by_name('Informatique')
        self.assertEqual(result['id'], 1)
        params = mock_db.execute_query.call_args[0][1]
        self.assertEqual(params, ('Informatique',))

    @patch('models.product.db')
    def test_find_category_inexistante(self, mock_db):
        """TC-PMF-02 : find_category_by_name() retourne None si inexistante."""
        mock_db.execute_query.return_value = None
        result = ProductModel.find_category_by_name('Inconnue')
        self.assertIsNone(result)



# TEST create_category()


class TestProductModelCreateCategory(unittest.TestCase):

    @patch('models.product.db')
    def test_create_category_retourne_id(self, mock_db):
        """TC-PMCC-01 : create_category() retourne l'ID inséré."""
        mock_db.execute_update.return_value = 7
        result = ProductModel.create_category('Électronique', 'Appareils')
        self.assertEqual(result, 7)
        params = mock_db.execute_update.call_args[0][1]
        self.assertEqual(params[0], 'Électronique')

    @patch('models.product.db')
    def test_create_category_sans_description(self, mock_db):
        """TC-PMCC-02 : create_category() fonctionne sans description."""
        mock_db.execute_update.return_value = 8
        result = ProductModel.create_category('Nouvelle')
        self.assertEqual(result, 8)
        params = mock_db.execute_update.call_args[0][1]
        self.assertEqual(params[1], '')



# TEST delete_category()


class TestProductModelDeleteCategory(unittest.TestCase):

    @patch('models.product.db')
    def test_delete_category_reussit_si_aucun_produit(self, mock_db):
        """TC-PMDC-01 : delete_category() reussit
        si aucun produit ne l'utilise."""
        mock_db.execute_query.return_value = {'nb': 0}
        mock_db.execute_update.return_value = True
        result = ProductModel.delete_category(1)
        self.assertTrue(result)
        mock_db.execute_update.assert_called_once()

    @patch('models.product.db')
    def test_delete_category_leve_valueerror_si_produits(self, mock_db):
        """TC-PMDC-02 : delete_category() leve ValueError
        si produits associes."""
        mock_db.execute_query.return_value = {'nb': 3}
        with self.assertRaises(ValueError) as ctx:
            ProductModel.delete_category(2)
        self.assertIn('produit', str(ctx.exception).lower())

    @patch('models.product.db')
    def test_delete_category_transmet_bon_id(self, mock_db):
        """TC-PMDC-03 : delete_category() transmet l'ID exact."""
        mock_db.execute_query.return_value = {'nb': 0}
        mock_db.execute_update.return_value = True
        ProductModel.delete_category(42)
        params = mock_db.execute_update.call_args[0][1]
        self.assertEqual(params, (42,))

    @patch('models.product.db')
    def test_delete_category_count_none(self, mock_db):
        """TC-PMDC-04 : delete_category() réussit si count retourne None."""
        mock_db.execute_query.return_value = None
        mock_db.execute_update.return_value = True
        result = ProductModel.delete_category(5)
        self.assertTrue(result)



# TEST get_dashboard_stats()


class TestProductModelDashboardStats(unittest.TestCase):

    # ── TC-PMDS-01 ───────────────────────────────────────────
    @patch('database.connection.db')
    def test_get_dashboard_stats_retourne_dict(self, mock_db):
        """
        TC-PMDS-01 : get_dashboard_stats() retourne le dict des stats.
        Note : patch sur database.connection.db car la méthode fait
        un import local 'from database.connection import db'.
        """
        mock_db.execute_query.return_value = {
            'total_produits': 20, 'nb_alertes': 3
        }
        result = ProductModel.get_dashboard_stats()
        self.assertEqual(result['total_produits'], 20)
        self.assertEqual(result['nb_alertes'], 3)

    # ── TC-PMDS-02 ───────────────────────────────────────────
    @patch('database.connection.db')
    def test_get_dashboard_stats_retourne_dict_vide_si_none(self, mock_db):
        """
        TC-PMDS-02 : get_dashboard_stats() retourne {} si db retourne None.
        """
        mock_db.execute_query.return_value = None
        result = ProductModel.get_dashboard_stats()
        self.assertEqual(result, {})



# POINT D'ENTRÉE


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestProductModelGetAll))
    suite.addTests(loader.loadTestsFromTestCase(TestProductModelGetById))
    suite.addTests(loader.loadTestsFromTestCase(TestProductModelGetLowStock))
    suite.addTests(loader.loadTestsFromTestCase(
        TestProductModelApplyStockMovement))
    suite.addTests(loader.loadTestsFromTestCase(TestProductModelCreate))
    suite.addTests(loader.loadTestsFromTestCase(TestProductModelUpdate))
    suite.addTests(loader.loadTestsFromTestCase(TestProductModelDelete))
    suite.addTests(loader.loadTestsFromTestCase(TestProductModelUpdateStock))
    suite.addTests(loader.loadTestsFromTestCase(TestProductModelCount))
    suite.addTests(loader.loadTestsFromTestCase(TestProductModelGetCategories))
    suite.addTests(loader.loadTestsFromTestCase(TestProductModelGetMovements))
    suite.addTests(loader.loadTestsFromTestCase(
        TestProductModelFindCategoryByName))
    suite.addTests(loader.loadTestsFromTestCase(
        TestProductModelCreateCategory))
    suite.addTests(loader.loadTestsFromTestCase(
        TestProductModelDeleteCategory))
    suite.addTests(loader.loadTestsFromTestCase(
        TestProductModelDashboardStats))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

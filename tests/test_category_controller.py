"""
tests/test_category_controller.py
-----------------------------------
Tests unitaires de CategoryController.

Méthodes testées :
  - get_all()  : cache hit, cache miss + mise en cache
  - create()   : nom vide, nom espaces, doublon, succès, exception
  - update()   : nom vide, doublon, succès, exception
  - delete()   : succès, ValueError produits liés, exception

Architecture : méthodes @staticmethod — CategoryModel et app_cache
sont mockés avec @patch.

Pour exécuter :
    python tests/test_category_controller.py
    ou
    python -m pytest tests/test_category_controller.py -v
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch
from controllers.category_controller import CategoryController


# ══════════════════════════════════════════════════════════════
# TEST get_all() — cache
# ══════════════════════════════════════════════════════════════

class TestCategoryControllerGetAll(unittest.TestCase):

    # ── TC-CC-GA-01 ──────────────────────────────────────────
    @patch('controllers.category_controller.app_cache')
    def test_cache_hit_ne_requete_pas_la_base(self, mock_cache):
        """
        TC-CC-GA-01 : get_all() avec cache chaud doit retourner
        la valeur du cache sans appeler CategoryModel.
        """
        mock_cache.get.return_value = [
            {'id': 1, 'nom': 'Téléphonie'},
            {'id': 2, 'nom': 'Informatique'},
        ]

        with patch('controllers.category_controller.CategoryModel.get_all') as mock_model:
            result = CategoryController.get_all()

        self.assertEqual(len(result), 2)
        mock_model.assert_not_called()

    # ── TC-CC-GA-02 ──────────────────────────────────────────
    @patch('controllers.category_controller.app_cache')
    @patch('controllers.category_controller.CategoryModel.get_all',
           return_value=[{'id': 1, 'nom': 'Téléphonie'}])
    def test_cache_miss_interroge_base_et_met_en_cache(self, mock_model, mock_cache):
        """
        TC-CC-GA-02 : get_all() avec cache froid doit appeler
        CategoryModel.get_all() et stocker le résultat en cache.
        """
        mock_cache.get.return_value = None

        result = CategoryController.get_all()

        mock_model.assert_called_once()
        mock_cache.set.assert_called_once()
        self.assertEqual(len(result), 1)


# ══════════════════════════════════════════════════════════════
# TEST create()
# ══════════════════════════════════════════════════════════════

class TestCategoryControllerCreate(unittest.TestCase):

    # ── TC-CC-CR-01 ──────────────────────────────────────────
    def test_nom_vide_retourne_erreur(self):
        """
        TC-CC-CR-01 : create() avec nom vide doit retourner
        (False, message) sans appeler le modèle.
        """
        ok, msg = CategoryController.create('')

        self.assertFalse(ok)
        self.assertIn('nom', msg.lower())

    # ── TC-CC-CR-02 ──────────────────────────────────────────
    def test_nom_espaces_retourne_erreur(self):
        """
        TC-CC-CR-02 : create() avec nom composé d'espaces uniquement
        doit retourner (False, message) — le strip() doit rejeter ce cas.
        """
        ok, msg = CategoryController.create('   ')

        self.assertFalse(ok)
        self.assertIn('nom', msg.lower())

    # ── TC-CC-CR-03 ──────────────────────────────────────────
    @patch('controllers.category_controller.CategoryModel.exists',
           return_value=True)
    def test_doublon_retourne_erreur(self, mock_exists):
        """
        TC-CC-CR-03 : create() avec un nom déjà existant doit
        retourner (False, message contenant 'existe').
        """
        ok, msg = CategoryController.create('Téléphonie')

        self.assertFalse(ok)
        self.assertIn('existe', msg.lower())

    # ── TC-CC-CR-04 ──────────────────────────────────────────
    @patch('controllers.category_controller.app_cache')
    @patch('controllers.category_controller.CategoryModel.create', return_value=3)
    @patch('controllers.category_controller.CategoryModel.exists', return_value=False)
    def test_creation_reussie_retourne_id(self, mock_exists, mock_create, mock_cache):
        """
        TC-CC-CR-04 : create() avec données valides doit retourner
        (True, id) et invalider le cache.
        """
        ok, cid = CategoryController.create('Électronique', 'Appareils électroniques')

        self.assertTrue(ok)
        self.assertEqual(cid, 3)
        mock_create.assert_called_once_with('Électronique', 'Appareils électroniques')
        mock_cache.invalidate.assert_called_once()

    # ── TC-CC-CR-05 ──────────────────────────────────────────
    @patch('controllers.category_controller.app_cache')
    @patch('controllers.category_controller.CategoryModel.create',
           side_effect=Exception("Duplicate entry"))
    @patch('controllers.category_controller.CategoryModel.exists', return_value=False)
    def test_exception_bdd_retourne_erreur(self, mock_exists, mock_create, mock_cache):
        """
        TC-CC-CR-05 : Si CategoryModel.create() lève une exception,
        create() doit retourner (False, message) sans la propager.
        """
        ok, msg = CategoryController.create('Nouvelle catégorie')

        self.assertFalse(ok)
        self.assertIsInstance(msg, str)


# ══════════════════════════════════════════════════════════════
# TEST update()
# ══════════════════════════════════════════════════════════════

class TestCategoryControllerUpdate(unittest.TestCase):

    # ── TC-CC-UP-01 ──────────────────────────────────────────
    def test_nom_vide_retourne_erreur(self):
        """
        TC-CC-UP-01 : update() avec nom vide doit retourner
        (False, message) sans appeler le modèle.
        """
        ok, msg = CategoryController.update(1, '')

        self.assertFalse(ok)
        self.assertIn('nom', msg.lower())

    # ── TC-CC-UP-02 ──────────────────────────────────────────
    @patch('controllers.category_controller.CategoryModel.exists',
           return_value=True)
    def test_doublon_retourne_erreur(self, mock_exists):
        """
        TC-CC-UP-02 : update() avec un nom déjà utilisé par une
        autre catégorie doit retourner (False, message).
        """
        ok, msg = CategoryController.update(2, 'Téléphonie')

        self.assertFalse(ok)
        self.assertIn('existe', msg.lower())
        mock_exists.assert_called_once_with('Téléphonie', exclude_id=2)

    # ── TC-CC-UP-03 ──────────────────────────────────────────
    @patch('controllers.category_controller.app_cache')
    @patch('controllers.category_controller.CategoryModel.update')
    @patch('controllers.category_controller.CategoryModel.exists', return_value=False)
    def test_update_reussi(self, mock_exists, mock_update, mock_cache):
        """
        TC-CC-UP-03 : update() avec données valides doit retourner
        (True, message) et invalider le cache.
        """
        ok, msg = CategoryController.update(1, 'Téléphonie Mobile', 'Smartphones')

        self.assertTrue(ok)
        mock_update.assert_called_once_with(1, 'Téléphonie Mobile', 'Smartphones')
        mock_cache.invalidate.assert_called_once()

    # ── TC-CC-UP-04 ──────────────────────────────────────────
    @patch('controllers.category_controller.app_cache')
    @patch('controllers.category_controller.CategoryModel.update',
           side_effect=Exception("Erreur SQL"))
    @patch('controllers.category_controller.CategoryModel.exists', return_value=False)
    def test_exception_bdd_retourne_erreur(self, mock_exists, mock_update, mock_cache):
        """
        TC-CC-UP-04 : Si CategoryModel.update() lève une exception,
        update() doit retourner (False, message).
        """
        ok, msg = CategoryController.update(1, 'Téléphonie')

        self.assertFalse(ok)
        self.assertIsInstance(msg, str)


# ══════════════════════════════════════════════════════════════
# TEST delete()
# ══════════════════════════════════════════════════════════════

class TestCategoryControllerDelete(unittest.TestCase):

    # ── TC-CC-DE-01 ──────────────────────────────────────────
    @patch('controllers.category_controller.app_cache')
    @patch('controllers.category_controller.CategoryModel.delete')
    def test_suppression_reussie(self, mock_delete, mock_cache):
        """
        TC-CC-DE-01 : delete() doit retourner (True, message)
        et invalider le cache.
        """
        ok, msg = CategoryController.delete(1)

        self.assertTrue(ok)
        mock_delete.assert_called_once_with(1)
        mock_cache.invalidate.assert_called_once()

    # ── TC-CC-DE-02 ──────────────────────────────────────────
    @patch('controllers.category_controller.app_cache')
    @patch('controllers.category_controller.CategoryModel.delete',
           side_effect=ValueError("Impossible : 3 produit(s) utilisent cette catégorie."))
    def test_suppression_categorie_avec_produits_retourne_erreur(self, mock_delete, mock_cache):
        """
        TC-CC-DE-02 : delete() doit retourner (False, message) quand
        CategoryModel.delete() lève une ValueError (produits liés).
        """
        ok, msg = CategoryController.delete(2)

        self.assertFalse(ok)
        self.assertIn('produit', msg.lower())

    # ── TC-CC-DE-03 ──────────────────────────────────────────
    @patch('controllers.category_controller.app_cache')
    @patch('controllers.category_controller.CategoryModel.delete',
           side_effect=Exception("Connexion perdue"))
    def test_exception_inattendue_retourne_erreur(self, mock_delete, mock_cache):
        """
        TC-CC-DE-03 : delete() doit retourner (False, message) pour
        toute exception inattendue.
        """
        ok, msg = CategoryController.delete(99)

        self.assertFalse(ok)
        self.assertIsInstance(msg, str)


# ══════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestCategoryControllerGetAll))
    suite.addTests(loader.loadTestsFromTestCase(TestCategoryControllerCreate))
    suite.addTests(loader.loadTestsFromTestCase(TestCategoryControllerUpdate))
    suite.addTests(loader.loadTestsFromTestCase(TestCategoryControllerDelete))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

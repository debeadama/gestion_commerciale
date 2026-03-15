"""
tests/test_category_model.py
-----------------------------
Tests unitaires de CategoryModel.

Méthodes testées :
  - get_all()    : appel db.execute_query()
  - get_by_id()  : retourne dict ou None
  - create()     : retourne l'ID inséré
  - update()     : appel db.execute_update() avec bons paramètres
  - delete()     : succès, ValueError si produits liés
  - exists()     : True si trouvé, False sinon, avec/sans exclude_id

Architecture : méthodes @staticmethod — db (instance globale de connexion)
est mockée avec @patch.

Pour exécuter :
    python tests/test_category_model.py
    ou
    python -m pytest tests/test_category_model.py -v
"""

from models.category import CategoryModel  # noqa: E402
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


class TestCategoryModelGetAll(unittest.TestCase):

    # ── TM-CA-GA-01 ──────────────────────────────────────────
    @patch('models.category.db')
    def test_get_all_retourne_liste(self, mock_db):
        """
        TM-CA-GA-01 : get_all() doit appeler db.execute_query()
        et retourner la liste des catégories.
        """
        mock_db.execute_query.return_value = [
            {'id': 1, 'nom': 'Téléphonie', 'nb_produits': 8},
            {'id': 2, 'nom': 'Informatique', 'nb_produits': 12},
        ]

        result = CategoryModel.get_all()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['nom'], 'Téléphonie')
        mock_db.execute_query.assert_called_once()

    # ── TM-CA-GA-02 ──────────────────────────────────────────
    @patch('models.category.db')
    def test_get_all_retourne_liste_vide_si_aucune_categorie(self, mock_db):
        """
        TM-CA-GA-02 : get_all() doit retourner une liste vide
        si aucune catégorie n'existe en base.
        """
        mock_db.execute_query.return_value = []

        result = CategoryModel.get_all()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)



# TEST get_by_id()


class TestCategoryModelGetById(unittest.TestCase):

    # ── TM-CA-GI-01 ──────────────────────────────────────────
    @patch('models.category.db')
    def test_get_by_id_retourne_categorie(self, mock_db):
        """
        TM-CA-GI-01 : get_by_id() doit retourner le dict
        de la catégorie quand l'ID existe.
        """
        mock_db.execute_query.return_value = {
            'id': 1, 'nom': 'Téléphonie', 'description': 'Smartphones'
        }

        result = CategoryModel.get_by_id(1)

        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['nom'], 'Téléphonie')

    # ── TM-CA-GI-02 ──────────────────────────────────────────
    @patch('models.category.db')
    def test_get_by_id_retourne_none_si_inexistant(self, mock_db):
        """
        TM-CA-GI-02 : get_by_id() doit retourner None
        quand l'ID n'existe pas.
        """
        mock_db.execute_query.return_value = None

        result = CategoryModel.get_by_id(999)

        self.assertIsNone(result)



# TEST create()


class TestCategoryModelCreate(unittest.TestCase):

    # ── TM-CA-CR-01 ──────────────────────────────────────────
    @patch('models.category.db')
    def test_create_retourne_id_insere(self, mock_db):
        """
        TM-CA-CR-01 : create() doit appeler db.execute_update()
        et retourner l'ID de la catégorie créée.
        """
        mock_db.execute_update.return_value = 4

        result = CategoryModel.create('Accessoires', 'Câbles et adaptateurs')

        self.assertEqual(result, 4)
        mock_db.execute_update.assert_called_once()

    # ── TM-CA-CR-02 ──────────────────────────────────────────
    @patch('models.category.db')
    def test_create_strip_les_espaces(self, mock_db):
        """
        TM-CA-CR-02 : create() doit transmettre le nom et la description
        sans espaces superflus (strip appliqué avant insertion).
        """
        mock_db.execute_update.return_value = 5

        CategoryModel.create('  Mobilier  ', '  Tables et chaises  ')

        call_args = mock_db.execute_update.call_args[0]
        params = call_args[1]
        self.assertEqual(params[0], 'Mobilier')
        self.assertEqual(params[1], 'Tables et chaises')



# TEST update()


class TestCategoryModelUpdate(unittest.TestCase):

    # ── TM-CA-UP-01 ──────────────────────────────────────────
    @patch('models.category.db')
    def test_update_appelle_execute_update(self, mock_db):
        """
        TM-CA-UP-01 : update() doit appeler db.execute_update()
        avec les bons paramètres et retourner True.
        """
        mock_db.execute_update.return_value = 1

        result = CategoryModel.update(1, 'Téléphonie Mobile', 'Smartphones')

        self.assertTrue(result)
        mock_db.execute_update.assert_called_once()
        call_args = mock_db.execute_update.call_args[0]
        params = call_args[1]
        self.assertEqual(params[0], 'Téléphonie Mobile')
        self.assertEqual(params[2], 1)  # category_id en 3ème position



# TEST delete()


class TestCategoryModelDelete(unittest.TestCase):

    # ── TM-CA-DE-01 ──────────────────────────────────────────
    @patch('models.category.db')
    def test_delete_reussit_si_aucun_produit(self, mock_db):
        """
        TM-CA-DE-01 : delete() doit supprimer la catégorie et retourner
        True quand aucun produit ne l'utilise (nb = 0).
        """
        mock_db.execute_query.return_value = {'nb': 0}
        mock_db.execute_update.return_value = 1

        result = CategoryModel.delete(1)

        self.assertTrue(result)
        mock_db.execute_update.assert_called_once()

    # ── TM-CA-DE-02 ──────────────────────────────────────────
    @patch('models.category.db')
    def test_delete_leve_valueerror_si_produits_lies(self, mock_db):
        """
        TM-CA-DE-02 : delete() doit lever une ValueError quand
        des produits utilisent cette catégorie.
        """
        mock_db.execute_query.return_value = {'nb': 5}

        with self.assertRaises(ValueError) as ctx:
            CategoryModel.delete(2)

        self.assertIn('produit', str(ctx.exception).lower())
        mock_db.execute_update.assert_not_called()

    # ── TM-CA-DE-03 ──────────────────────────────────────────
    @patch('models.category.db')
    def test_delete_appelle_execute_update_avec_bon_id(self, mock_db):
        """
        TM-CA-DE-03 : delete() doit transmettre l'ID exact à
        db.execute_update().
        """
        mock_db.execute_query.return_value = {'nb': 0}
        mock_db.execute_update.return_value = 1

        CategoryModel.delete(7)

        call_args = mock_db.execute_update.call_args[0]
        params = call_args[1]
        self.assertEqual(params[0], 7)



# TEST exists()


class TestCategoryModelExists(unittest.TestCase):

    # ── TM-CA-EX-01 ──────────────────────────────────────────
    @patch('models.category.db')
    def test_exists_retourne_true_si_trouve(self, mock_db):
        """
        TM-CA-EX-01 : exists() doit retourner True quand une
        catégorie avec ce nom existe en base.
        """
        mock_db.execute_query.return_value = {'id': 1}

        result = CategoryModel.exists('Téléphonie')

        self.assertTrue(result)

    # ── TM-CA-EX-02 ──────────────────────────────────────────
    @patch('models.category.db')
    def test_exists_retourne_false_si_absent(self, mock_db):
        """
        TM-CA-EX-02 : exists() doit retourner False quand aucune
        catégorie avec ce nom n'existe en base.
        """
        mock_db.execute_query.return_value = None

        result = CategoryModel.exists('Catégorie Inexistante')

        self.assertFalse(result)

    # ── TM-CA-EX-03 ──────────────────────────────────────────
    @patch('models.category.db')
    def test_exists_avec_exclude_id_utilise_bonne_requete(self, mock_db):
        """
        TM-CA-EX-03 : exists() avec exclude_id doit transmettre
        les deux paramètres (nom et exclude_id) à db.execute_query().
        """
        mock_db.execute_query.return_value = None

        CategoryModel.exists('Téléphonie', exclude_id=2)

        call_args = mock_db.execute_query.call_args[0]
        params = call_args[1]
        self.assertIn('Téléphonie', params)
        self.assertIn(2, params)

    # ── TM-CA-EX-04 ──────────────────────────────────────────
    @patch('models.category.db')
    def test_exists_sans_exclude_id_utilise_requete_simple(self, mock_db):
        """
        TM-CA-EX-04 : exists() sans exclude_id doit passer uniquement
        le nom comme paramètre à db.execute_query().
        """
        mock_db.execute_query.return_value = {'id': 3}

        CategoryModel.exists('Informatique')

        call_args = mock_db.execute_query.call_args[0]
        params = call_args[1]
        self.assertEqual(params, ('Informatique',))



# POINT D'ENTRÉE


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestCategoryModelGetAll))
    suite.addTests(loader.loadTestsFromTestCase(TestCategoryModelGetById))
    suite.addTests(loader.loadTestsFromTestCase(TestCategoryModelCreate))
    suite.addTests(loader.loadTestsFromTestCase(TestCategoryModelUpdate))
    suite.addTests(loader.loadTestsFromTestCase(TestCategoryModelDelete))
    suite.addTests(loader.loadTestsFromTestCase(TestCategoryModelExists))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

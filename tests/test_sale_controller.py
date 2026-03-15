"""
tests/test_sale_controller.py
------------------------------
Tests unitaires complets de SaleController.
Couvre : get_all, get_by_id, get_details, get_pending,
         create, add_payment, validate, cancel,
         get_kpi, get_top_products, get_top_clients,
         get_monthly_revenue, get_recent, get_dashboard_stats,
         get_report_ventes, get_report_impayes, get_report_vendeurs.

Pour exécuter :
    python -m pytest tests/test_sale_controller.py -v
"""

from controllers.sale_controller import SaleController  # noqa: E402
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


def make_panier(produit_id=1, quantite=2, prix=50000):
    return [{'produit_id': produit_id,
             'quantite': quantite,
             'prix_unitaire': prix}]


def make_produit(stock=10, nom='Câble USB'):
    return {'id': 1, 'nom': nom, 'stock_actuel': stock}


def make_vente(statut='en_cours', total=100000, paye=0, reste=100000):
    return {'id': 1, 'statut': statut, 'montant_total': total,
            'montant_paye': paye, 'montant_reste': reste}



# TEST get_all()


class TestSaleControllerGetAll(unittest.TestCase):

    @patch('controllers.sale_controller.SaleModel.get_all',
           return_value=[{'id': 1}])
    def test_get_all_retourne_liste(self, mock_get):
        """TC-SCA-01 : get_all() retourne la liste du modèle."""
        result = SaleController.get_all()
        self.assertEqual(len(result), 1)
        mock_get.assert_called_once_with(None, None)

    @patch('controllers.sale_controller.SaleModel.get_all',
           return_value=[{'id': 1}])
    def test_get_all_avec_filtres(self, mock_get):
        """TC-SCA-02 : get_all() transmet search et statut."""
        SaleController.get_all(search='FAC', statut='payee')
        mock_get.assert_called_once_with('FAC', 'payee')

    @patch('controllers.sale_controller.SaleModel.get_all', return_value=None)
    def test_get_all_retourne_liste_vide_si_none(self, mock_get):
        """TC-SCA-03 : get_all() retourne [] si modèle retourne None."""
        result = SaleController.get_all()
        self.assertEqual(result, [])



# TEST get_by_id()


class TestSaleControllerGetById(unittest.TestCase):

    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value={'id': 1, 'statut': 'payee'})
    def test_get_by_id_retourne_vente(self, mock_get):
        """TC-SCB-01 : get_by_id() retourne la vente du modèle."""
        result = SaleController.get_by_id(1)
        self.assertEqual(result['statut'], 'payee')
        mock_get.assert_called_once_with(1)

    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=None)
    def test_get_by_id_retourne_none(self, mock_get):
        """TC-SCB-02 : get_by_id() retourne None si vente inexistante."""
        result = SaleController.get_by_id(999)
        self.assertIsNone(result)



# TEST get_details()


class TestSaleControllerGetDetails(unittest.TestCase):

    @patch('controllers.sale_controller.SaleModel.get_details',
           return_value=[{'produit': 'HP Laptop', 'quantite': 1}])
    def test_get_details_retourne_lignes(self, mock_get):
        """TC-SCD-01 : get_details() retourne les lignes de la vente."""
        result = SaleController.get_details(1)
        self.assertEqual(len(result), 1)
        mock_get.assert_called_once_with(1)

    @patch('controllers.sale_controller.SaleModel.get_details',
           return_value=None)
    def test_get_details_retourne_liste_vide_si_none(self, mock_get):
        """TC-SCD-02 : get_details() retourne [] si None."""
        result = SaleController.get_details(99)
        self.assertEqual(result, [])



# TEST get_pending()


class TestSaleControllerGetPending(unittest.TestCase):

    @patch('controllers.sale_controller.SaleModel.get_pending',
           return_value=[{'id': 1, 'statut': 'en_cours'}])
    def test_get_pending_retourne_liste(self, mock_get):
        """TC-SCP-01 : get_pending() retourne les ventes en attente."""
        result = SaleController.get_pending()
        self.assertEqual(len(result), 1)
        mock_get.assert_called_once()

    @patch('controllers.sale_controller.SaleModel.get_pending',
           return_value=None)
    def test_get_pending_retourne_liste_vide_si_none(self, mock_get):
        """TC-SCP-02 : get_pending() retourne [] si None."""
        result = SaleController.get_pending()
        self.assertEqual(result, [])



# TEST create()


class TestSaleControllerCreate(unittest.TestCase):

    def test_panier_vide_retourne_erreur(self):
        """TC-SC-01 : panier vide retourne (False, message)."""
        ok, msg = SaleController.create(client_id=1, panier=[], montant_paye=0)
        self.assertFalse(ok)
        self.assertIn('vide', msg.lower())

    @patch('controllers.sale_controller.ProductModel.get_by_id',
           return_value=None)
    def test_produit_introuvable_retourne_erreur(self, mock_get):
        """TC-SC-02 : produit inexistant retourne (False, message)."""
        ok, msg = SaleController.create(
            client_id=1,
            panier=[{'produit_id': 999, 'quantite': 1, 'prix_unitaire': 5000}],
            montant_paye=5000)
        self.assertFalse(ok)
        self.assertIn('introuvable', msg.lower())

    @patch('controllers.sale_controller.ProductModel.get_by_id',
           return_value=make_produit(stock=2))
    def test_stock_insuffisant_retourne_erreur(self, mock_get):
        """TC-SC-03 : stock insuffisant retourne (False, message)."""
        ok, msg = SaleController.create(
            client_id=1, panier=make_panier(quantite=10), montant_paye=0)
        self.assertFalse(ok)
        self.assertIn('insuffisant', msg.lower())

    @patch('controllers.sale_controller.ProductModel.get_by_id',
           return_value=make_produit(stock=10))
    def test_montant_paye_negatif_retourne_erreur(self, mock_get):
        """TC-SC-04 : montant_paye négatif retourne (False, message)."""
        ok, msg = SaleController.create(
            client_id=1, panier=make_panier(), montant_paye=-100)
        self.assertFalse(ok)
        self.assertIn('negatif', msg.lower())

    @patch('controllers.sale_controller.ProductModel.get_by_id',
           return_value=make_produit(stock=10))
    def test_montant_paye_superieur_au_total_retourne_erreur(self, mock_get):
        """TC-SC-05 : montant_paye > total retourne (False, message)."""
        ok, msg = SaleController.create(
            client_id=1, panier=make_panier(quantite=1, prix=50000),
            montant_paye=999999)
        self.assertFalse(ok)
        self.assertIn('depasse', msg.lower())

    @patch('controllers.sale_controller.SessionManager.get_current_user',
           return_value={'id': 1})
    @patch('controllers.sale_controller.SaleModel.create', return_value=7)
    @patch('controllers.sale_controller.ProductModel.get_by_id',
           return_value=make_produit(stock=10))
    def test_vente_payee_complete(self, mock_prod, mock_create, mock_user):
        """TC-SC-06 : paiement total → statut payee, retourne (True, id)."""
        ok, sid = SaleController.create(
            client_id=1, panier=make_panier(quantite=1, prix=50000),
            montant_paye=50000)
        self.assertTrue(ok)
        self.assertEqual(sid, 7)
        sale_data = mock_create.call_args[0][0]
        self.assertEqual(sale_data['statut'], 'payee')

    @patch('controllers.sale_controller.SessionManager.get_current_user',
           return_value={'id': 1})
    @patch('controllers.sale_controller.SaleModel.create', return_value=8)
    @patch('controllers.sale_controller.ProductModel.get_by_id',
           return_value=make_produit(stock=10))
    def test_vente_partielle(self, mock_prod, mock_create, mock_user):
        """TC-SC-07 : paiement partiel → statut partielle."""
        ok, sid = SaleController.create(
            client_id=1, panier=make_panier(quantite=1, prix=50000),
            montant_paye=20000)
        self.assertTrue(ok)
        sale_data = mock_create.call_args[0][0]
        self.assertEqual(sale_data['statut'], 'partielle')

    @patch('controllers.sale_controller.SessionManager.get_current_user',
           return_value={'id': 1})
    @patch('controllers.sale_controller.SaleModel.create', return_value=9)
    @patch('controllers.sale_controller.ProductModel.get_by_id',
           return_value=make_produit(stock=10))
    def test_vente_en_cours_sans_paiement(
            self, mock_prod, mock_create, mock_user):
        """TC-SC-08 : paiement = 0 → statut en_cours."""
        ok, sid = SaleController.create(
            client_id=1, panier=make_panier(quantite=1, prix=50000),
            montant_paye=0)
        self.assertTrue(ok)
        sale_data = mock_create.call_args[0][0]
        self.assertEqual(sale_data['statut'], 'en_cours')

    @patch('controllers.sale_controller.SessionManager.get_current_user',
           return_value={'id': 1})
    @patch('controllers.sale_controller.SaleModel.create',
           side_effect=Exception("Erreur SQL"))
    @patch('controllers.sale_controller.ProductModel.get_by_id',
           return_value=make_produit(stock=10))
    def test_exception_bdd_retourne_erreur(
            self, mock_prod, mock_create, mock_user):
        """TC-SC-09 : exception BDD retourne (False, message)."""
        ok, msg = SaleController.create(
            client_id=1, panier=make_panier(), montant_paye=0)
        self.assertFalse(ok)



# TEST add_payment()


class TestSaleControllerAddPayment(unittest.TestCase):

    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=None)
    def test_vente_introuvable(self, mock_get):
        """TC-AP-01 : vente inexistante retourne (False, message)."""
        ok, msg = SaleController.add_payment(999, 10000)
        self.assertFalse(ok)
        self.assertIn('introuvable', msg.lower())

    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='payee'))
    def test_vente_deja_payee(self, mock_get):
        """TC-AP-02 : vente déjà payée retourne (False, message)."""
        ok, msg = SaleController.add_payment(1, 10000)
        self.assertFalse(ok)

    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='annulee'))
    def test_vente_annulee(self, mock_get):
        """TC-AP-03 : vente annulée retourne (False, message)."""
        ok, msg = SaleController.add_payment(1, 10000)
        self.assertFalse(ok)

    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='en_cours', reste=50000))
    def test_montant_zero_retourne_erreur(self, mock_get):
        """TC-AP-04 : montant = 0 retourne (False, message)."""
        ok, msg = SaleController.add_payment(1, 0)
        self.assertFalse(ok)

    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='en_cours', reste=50000))
    def test_montant_superieur_au_reste(self, mock_get):
        """TC-AP-05 : montant > reste retourne (False, message)."""
        ok, msg = SaleController.add_payment(1, 99999)
        self.assertFalse(ok)
        self.assertIn('depasse', msg.lower())

    @patch('controllers.sale_controller.SaleModel.add_payment')
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='en_cours', reste=50000))
    def test_paiement_partiel_reussi(self, mock_get, mock_pay):
        """TC-AP-06 : paiement partiel retourne (True, message avec reste)."""
        ok, msg = SaleController.add_payment(1, 30000)
        self.assertTrue(ok)
        self.assertIn('reste', msg.lower())

    @patch('controllers.sale_controller.SaleModel.add_payment')
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='en_cours', reste=50000))
    def test_paiement_complet_retourne_solde(self, mock_get, mock_pay):
        """TC-AP-07 : paiement complet retourne (True, 'Vente soldee.')"""
        ok, msg = SaleController.add_payment(1, 50000)
        self.assertTrue(ok)
        self.assertIn('solde', msg.lower())

    @patch('controllers.sale_controller.SaleModel.add_payment',
           side_effect=Exception("Erreur SQL"))
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='en_cours', reste=50000))
    def test_exception_retourne_erreur(self, mock_get, mock_pay):
        """TC-AP-08 : exception retourne (False, message)."""
        ok, msg = SaleController.add_payment(1, 10000)
        self.assertFalse(ok)



# TEST validate()


class TestSaleControllerValidate(unittest.TestCase):

    @patch('controllers.sale_controller.SessionManager.has_permission',
           return_value=False)
    def test_permission_insuffisante(self, mock_perm):
        """TC-SV-01 : permission insuffisante retourne (False, message)."""
        ok, msg = SaleController.validate(1)
        self.assertFalse(ok)
        self.assertIn('permission', msg.lower())

    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=None)
    @patch('controllers.sale_controller.SessionManager.has_permission',
           return_value=True)
    def test_vente_introuvable(self, mock_perm, mock_get):
        """TC-SV-02 : vente inexistante retourne (False, message)."""
        ok, msg = SaleController.validate(999)
        self.assertFalse(ok)
        self.assertIn('introuvable', msg.lower())

    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='annulee'))
    @patch('controllers.sale_controller.SessionManager.has_permission',
           return_value=True)
    def test_statut_non_validable(self, mock_perm, mock_get):
        """TC-SV-03 : vente annulée ne peut pas être validée."""
        ok, msg = SaleController.validate(1)
        self.assertFalse(ok)

    @patch('controllers.sale_controller.SaleModel.validate')
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='en_cours', reste=100000))
    @patch('controllers.sale_controller.SessionManager.has_permission',
           return_value=True)
    def test_validation_reussie(self, mock_perm, mock_get, mock_val):
        """TC-SV-04 : validation réussie retourne (True, message)."""
        ok, msg = SaleController.validate(1)
        self.assertTrue(ok)
        mock_val.assert_called_once()

    @patch('controllers.sale_controller.SaleModel.validate',
           side_effect=Exception("Erreur SQL"))
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='partielle', reste=50000))
    @patch('controllers.sale_controller.SessionManager.has_permission',
           return_value=True)
    def test_exception_retourne_erreur(self, mock_perm, mock_get, mock_val):
        """TC-SV-05 : exception dans validate() retourne (False, message)."""
        ok, msg = SaleController.validate(1)
        self.assertFalse(ok)



# TEST cancel()


class TestSaleControllerCancel(unittest.TestCase):

    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=None)
    def test_vente_introuvable(self, mock_get):
        """TC-SCN-01 : vente inexistante retourne (False, message)."""
        ok, msg = SaleController.cancel(999)
        self.assertFalse(ok)
        self.assertIn('introuvable', msg.lower())

    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='annulee'))
    def test_vente_deja_annulee(self, mock_get):
        """TC-SCN-02 : vente déjà annulée retourne (False, message)."""
        ok, msg = SaleController.cancel(1)
        self.assertFalse(ok)
        self.assertIn('annulee', msg.lower())

    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='payee'))
    def test_vente_payee_non_annulable(self, mock_get):
        """TC-SCN-03 : vente payée ne peut pas être annulée."""
        ok, msg = SaleController.cancel(1)
        self.assertFalse(ok)
        self.assertIn('payee', msg.lower())

    @patch('controllers.sale_controller.SaleModel.cancel')
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='en_cours'))
    def test_annulation_reussie(self, mock_get, mock_cancel):
        """TC-SCN-04 : annulation réussie retourne (True, message)."""
        ok, msg = SaleController.cancel(1)
        self.assertTrue(ok)
        mock_cancel.assert_called_once_with(1)

    @patch('controllers.sale_controller.SaleModel.cancel',
           side_effect=Exception("Erreur SQL"))
    @patch('controllers.sale_controller.SaleModel.get_by_id',
           return_value=make_vente(statut='en_cours'))
    def test_exception_retourne_erreur(self, mock_get, mock_cancel):
        """TC-SCN-05 : exception dans cancel() retourne (False, message)."""
        ok, msg = SaleController.cancel(1)
        self.assertFalse(ok)



# TEST méthodes statistiques


class TestSaleControllerStats(unittest.TestCase):

    @patch('controllers.sale_controller.SaleModel.get_kpi',
           return_value={'ca_jour': 150000})
    def test_get_kpi(self, mock_kpi):
        """TC-ST-01 : get_kpi() délègue au modèle."""
        result = SaleController.get_kpi()
        self.assertEqual(result['ca_jour'], 150000)
        mock_kpi.assert_called_once()

    @patch('controllers.sale_controller.SaleModel.get_top_products',
           return_value=[{'nom': 'HP Laptop'}])
    def test_get_top_products(self, mock_top):
        """TC-ST-02 : get_top_products() délègue au modèle avec limit."""
        result = SaleController.get_top_products(limit=3)
        self.assertEqual(len(result), 1)
        mock_top.assert_called_once_with(3)

    @patch('controllers.sale_controller.SaleModel.get_top_products',
           return_value=None)
    def test_get_top_products_retourne_liste_vide(self, mock_top):
        """TC-ST-03 : get_top_products() retourne [] si None."""
        result = SaleController.get_top_products()
        self.assertEqual(result, [])

    @patch('controllers.sale_controller.SaleModel.get_top_clients',
           return_value=[{'client': 'KOUASSI Jean'}])
    def test_get_top_clients(self, mock_top):
        """TC-ST-04 : get_top_clients() délègue au modèle."""
        result = SaleController.get_top_clients()
        self.assertEqual(len(result), 1)
        mock_top.assert_called_once_with(5)

    @patch('controllers.sale_controller.SaleModel.get_monthly_revenue',
           return_value=[{'mois': 'Jan 2024', 'ca': 500000}])
    def test_get_monthly_revenue(self, mock_rev):
        """TC-ST-05 : get_monthly_revenue() délègue au modèle."""
        result = SaleController.get_monthly_revenue(months=3)
        self.assertEqual(len(result), 1)
        mock_rev.assert_called_once_with(3)

    @patch('controllers.sale_controller.SaleModel.get_recent',
           return_value=[{'id': 1}])
    def test_get_recent(self, mock_rec):
        """TC-ST-06 : get_recent() délègue au modèle."""
        result = SaleController.get_recent(limit=5)
        self.assertEqual(len(result), 1)
        mock_rec.assert_called_once_with(5)

    @patch('controllers.sale_controller.SaleModel.get_dashboard_stats',
           return_value={'ca_total': 5000000})
    def test_get_dashboard_stats(self, mock_stats):
        """TC-ST-07 : get_dashboard_stats() délègue au modèle."""
        result = SaleController.get_dashboard_stats()
        self.assertEqual(result['ca_total'], 5000000)
        mock_stats.assert_called_once()

    @patch('controllers.sale_controller.SaleModel.get_report_ventes',
           return_value=[{'numero_facture': 'FAC-001'}])
    def test_get_report_ventes(self, mock_rep):
        """TC-ST-08 : get_report_ventes() délègue au modèle."""
        result = SaleController.get_report_ventes('2024-01-01', '2024-01-31')
        self.assertEqual(len(result), 1)
        mock_rep.assert_called_once_with('2024-01-01', '2024-01-31', None)

    @patch('controllers.sale_controller.SaleModel.get_report_impayes',
           return_value=[])
    def test_get_report_impayes(self, mock_rep):
        """TC-ST-09 : get_report_impayes() délègue au modèle."""
        SaleController.get_report_impayes(
            '2024-01-01', '2024-01-31', vendeur_id=2)
        mock_rep.assert_called_once_with('2024-01-01', '2024-01-31', 2)

    @patch('controllers.sale_controller.SaleModel.get_report_vendeurs',
           return_value=[{'vendeur': 'admin'}])
    def test_get_report_vendeurs(self, mock_rep):
        """TC-ST-10 : get_report_vendeurs() délègue au modèle."""
        result = SaleController.get_report_vendeurs('2024-01-01', '2024-01-31')
        self.assertEqual(len(result), 1)
        mock_rep.assert_called_once_with('2024-01-01', '2024-01-31')



# POINT D'ENTRÉE


if __name__ == '__main__':
    unittest.main(verbosity=2)

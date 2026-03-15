"""
tests/test_model_sale.py
-------------------------
Tests unitaires complets de SaleModel.
Couvre : get_all (filtres), get_pending, get_kpi,
         get_top_products, get_top_clients, get_monthly_revenue,
         add_payment, validate, cancel,
         count, get_recent, get_dashboard_stats,
         get_report_ventes (avec/sans vendeur),
         get_report_impayes (avec/sans vendeur),
         get_report_vendeurs.

Pour exécuter :
    python -m pytest tests/test_model_sale.py -v
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch, MagicMock
from models.sale import SaleModel


# ══════════════════════════════════════════════════════════════
# TEST get_all() — filtres search & statut
# ══════════════════════════════════════════════════════════════

class TestSaleModelGetAll(unittest.TestCase):

    @patch('models.sale.db')
    def test_get_all_sans_filtre(self, mock_db):
        """TC-SGA-01 : get_all() sans filtre exécute la requête sans WHERE."""
        mock_db.execute_query.return_value = [{'id': 1}]
        result = SaleModel.get_all()
        self.assertEqual(len(result), 1)
        call_args = mock_db.execute_query.call_args
        self.assertNotIn('WHERE', call_args[0][0])

    @patch('models.sale.db')
    def test_get_all_avec_search(self, mock_db):
        """TC-SGA-02 : get_all(search='FAC') construit un WHERE avec LIKE."""
        mock_db.execute_query.return_value = []
        SaleModel.get_all(search='FAC')
        call_args = mock_db.execute_query.call_args
        self.assertIn('LIKE', call_args[0][0])
        params = call_args[0][1]
        self.assertIn('%FAC%', params)

    @patch('models.sale.db')
    def test_get_all_avec_statut(self, mock_db):
        """TC-SGA-03 : get_all(statut='payee') ajoute filtre statut."""
        mock_db.execute_query.return_value = []
        SaleModel.get_all(statut='payee')
        call_args = mock_db.execute_query.call_args
        self.assertIn('statut', call_args[0][0])
        params = call_args[0][1]
        self.assertIn('payee', params)

    @patch('models.sale.db')
    def test_get_all_statut_tous_ignore(self, mock_db):
        """TC-SGA-04 : get_all(statut='tous') n'ajoute pas de filtre statut."""
        mock_db.execute_query.return_value = []
        SaleModel.get_all(statut='tous')
        call_args = mock_db.execute_query.call_args
        # params doit être None (aucun filtre)
        self.assertIsNone(call_args[0][1])

    @patch('models.sale.db')
    def test_get_all_search_et_statut(self, mock_db):
        """TC-SGA-05 : get_all(search, statut) combine les deux filtres."""
        mock_db.execute_query.return_value = []
        SaleModel.get_all(search='BAMBA', statut='partielle')
        call_args = mock_db.execute_query.call_args
        params = call_args[0][1]
        self.assertIn('%BAMBA%', params)
        self.assertIn('partielle', params)


# ══════════════════════════════════════════════════════════════
# TEST get_by_id()
# ══════════════════════════════════════════════════════════════

class TestSaleModelGetById(unittest.TestCase):

    @patch('models.sale.db')
    def test_get_by_id_retourne_vente(self, mock_db):
        """TC-SGB-01 : get_by_id() retourne la vente avec toutes les infos."""
        mock_db.execute_query.return_value = {
            'id': 1, 'statut': 'payee', 'client_nom': 'KOUASSI Jean'
        }
        result = SaleModel.get_by_id(1)
        self.assertEqual(result['statut'], 'payee')
        params = mock_db.execute_query.call_args[0][1]
        self.assertEqual(params, (1,))

    @patch('models.sale.db')
    def test_get_by_id_retourne_none_si_absent(self, mock_db):
        """TC-SGB-02 : get_by_id() retourne None si vente inexistante."""
        mock_db.execute_query.return_value = None
        result = SaleModel.get_by_id(999)
        self.assertIsNone(result)


# ══════════════════════════════════════════════════════════════
# TEST get_details()
# ══════════════════════════════════════════════════════════════

class TestSaleModelGetDetails(unittest.TestCase):

    @patch('models.sale.db')
    def test_get_details_retourne_lignes(self, mock_db):
        """TC-SGD-01 : get_details() retourne les lignes de la vente."""
        mock_db.execute_query.return_value = [
            {'produit': 'HP Laptop', 'quantite': 1, 'prix_unitaire': 350000},
            {'produit': 'Câble USB', 'quantite': 2, 'prix_unitaire': 5000},
        ]
        result = SaleModel.get_details(1)
        self.assertEqual(len(result), 2)
        params = mock_db.execute_query.call_args[0][1]
        self.assertEqual(params, (1,))

    @patch('models.sale.db')
    def test_get_details_vide(self, mock_db):
        """TC-SGD-02 : get_details() retourne [] si aucune ligne."""
        mock_db.execute_query.return_value = []
        result = SaleModel.get_details(99)
        self.assertEqual(result, [])

    @patch('models.sale.db')
    def test_get_details_sql_filtre_par_vente(self, mock_db):
        """TC-SGD-03 : la requête SQL filtre par vente_id."""
        mock_db.execute_query.return_value = []
        SaleModel.get_details(5)
        call_sql = mock_db.execute_query.call_args[0][0]
        self.assertIn('vente_id', call_sql)


# ══════════════════════════════════════════════════════════════
# TEST generate_numero()
# ══════════════════════════════════════════════════════════════

class TestSaleModelGenerateNumero(unittest.TestCase):

    @patch('models.sale.db')
    def test_generate_numero_format_correct(self, mock_db):
        """TC-SGN-01 : generate_numero() retourne un numéro au bon format."""
        mock_db.execute_query.return_value = {'total': 0}
        numero = SaleModel.generate_numero()
        self.assertTrue(numero.startswith('FAC-'))
        parts = numero.split('-')
        self.assertEqual(len(parts), 3)
        self.assertEqual(len(parts[1]), 8)  # YYYYMMDD
        self.assertEqual(parts[2], '0001')  # premier de la journée

    @patch('models.sale.db')
    def test_generate_numero_incremente(self, mock_db):
        """TC-SGN-02 : generate_numero() incrémente le séquenciel."""
        mock_db.execute_query.return_value = {'total': 4}
        numero = SaleModel.generate_numero()
        self.assertTrue(numero.endswith('0005'))


# ══════════════════════════════════════════════════════════════
# TEST create()
# ══════════════════════════════════════════════════════════════

class TestSaleModelCreate(unittest.TestCase):

    @patch('models.sale.db')
    @patch.object(SaleModel, 'generate_numero', return_value='FAC-20240115-0001')
    def test_create_retourne_sale_id(self, mock_num, mock_db):
        """TC-SMC-01 : create() retourne l'ID de la vente créée."""
        mock_db.execute_update.return_value = 7
        sale_data = {
            'client_id': 1, 'user_id': 1,
            'montant_total': 100000, 'montant_paye': 100000,
            'statut': 'payee', 'notes': '',
            'panier': [
                {'produit_id': 1, 'quantite': 2, 'prix_unitaire': 50000}
            ]
        }
        result = SaleModel.create(sale_data)
        self.assertEqual(result, 7)

    @patch('models.sale.db')
    @patch.object(SaleModel, 'generate_numero', return_value='FAC-20240115-0002')
    def test_create_insere_lignes_panier(self, mock_num, mock_db):
        """TC-SMC-02 : create() insère une ligne par produit du panier + update stock."""
        mock_db.execute_update.return_value = 8
        sale_data = {
            'client_id': 1, 'user_id': 1,
            'montant_total': 110000, 'montant_paye': 0,
            'statut': 'en_cours', 'notes': '',
            'panier': [
                {'produit_id': 1, 'quantite': 1, 'prix_unitaire': 100000},
                {'produit_id': 2, 'quantite': 2, 'prix_unitaire': 5000},
            ]
        }
        SaleModel.create(sale_data)
        # 1 INSERT vente + 2 INSERT details + 2 UPDATE stock = 5 appels
        self.assertEqual(mock_db.execute_update.call_count, 5)

    @patch('models.sale.db')
    @patch.object(SaleModel, 'generate_numero', return_value='FAC-20240115-0003')
    def test_create_panier_vide_pas_de_lignes(self, mock_num, mock_db):
        """TC-SMC-03 : create() avec panier vide insère seulement la vente."""
        mock_db.execute_update.return_value = 9
        sale_data = {
            'client_id': 1, 'user_id': 1,
            'montant_total': 0, 'montant_paye': 0,
            'statut': 'en_cours', 'notes': '',
            'panier': []
        }
        SaleModel.create(sale_data)
        # Seulement 1 INSERT vente, pas de lignes ni de stock
        self.assertEqual(mock_db.execute_update.call_count, 1)


# ══════════════════════════════════════════════════════════════
# TEST get_pending()
# ══════════════════════════════════════════════════════════════

class TestSaleModelGetPending(unittest.TestCase):

    @patch('models.sale.db')
    def test_get_pending_retourne_liste(self, mock_db):
        """TC-SGP-01 : get_pending() retourne les ventes en attente."""
        mock_db.execute_query.return_value = [
            {'id': 1, 'statut': 'en_cours'},
            {'id': 2, 'statut': 'partielle'},
        ]
        result = SaleModel.get_pending()
        self.assertEqual(len(result), 2)
        call_sql = mock_db.execute_query.call_args[0][0]
        self.assertIn("en_cours", call_sql)
        self.assertIn("partielle", call_sql)

    @patch('models.sale.db')
    def test_get_pending_vide(self, mock_db):
        """TC-SGP-02 : get_pending() retourne [] si aucune vente en attente."""
        mock_db.execute_query.return_value = []
        result = SaleModel.get_pending()
        self.assertEqual(result, [])


# ══════════════════════════════════════════════════════════════
# TEST get_kpi()
# ══════════════════════════════════════════════════════════════

class TestSaleModelGetKpi(unittest.TestCase):

    @patch('models.sale.db')
    def test_get_kpi_retourne_dict(self, mock_db):
        """TC-SK-01 : get_kpi() retourne un dict avec les KPIs."""
        mock_db.execute_query.return_value = {
            'ca_jour': 150000, 'ca_semaine': 800000,
            'ca_mois': 3000000, 'nb_en_cours': 2,
            'nb_partielles': 1, 'total_impayes': 250000
        }
        result = SaleModel.get_kpi()
        self.assertEqual(result['ca_jour'], 150000)
        self.assertIn('nb_en_cours', result)

    @patch('models.sale.db')
    def test_get_kpi_retourne_dict_vide_si_none(self, mock_db):
        """TC-SK-02 : get_kpi() retourne {} si db retourne None."""
        mock_db.execute_query.return_value = None
        result = SaleModel.get_kpi()
        self.assertEqual(result, {})


# ══════════════════════════════════════════════════════════════
# TEST get_top_products()
# ══════════════════════════════════════════════════════════════

class TestSaleModelGetTopProducts(unittest.TestCase):

    @patch('models.sale.db')
    def test_get_top_products_par_defaut(self, mock_db):
        """TC-STP-01 : get_top_products() appelle db avec limit=5."""
        mock_db.execute_query.return_value = []
        SaleModel.get_top_products()
        params = mock_db.execute_query.call_args[0][1]
        self.assertEqual(params, (5,))

    @patch('models.sale.db')
    def test_get_top_products_limite_personnalisee(self, mock_db):
        """TC-STP-02 : get_top_products(10) appelle db avec limit=10."""
        mock_db.execute_query.return_value = []
        SaleModel.get_top_products(limit=10)
        params = mock_db.execute_query.call_args[0][1]
        self.assertEqual(params, (10,))


# ══════════════════════════════════════════════════════════════
# TEST get_top_clients()
# ══════════════════════════════════════════════════════════════

class TestSaleModelGetTopClients(unittest.TestCase):

    @patch('models.sale.db')
    def test_get_top_clients_par_defaut(self, mock_db):
        """TC-STC-01 : get_top_clients() appelle db avec limit=5."""
        mock_db.execute_query.return_value = [
            {'client': 'KOUASSI Jean', 'ca_total': 500000}
        ]
        result = SaleModel.get_top_clients()
        self.assertEqual(len(result), 1)
        params = mock_db.execute_query.call_args[0][1]
        self.assertEqual(params, (5,))


# ══════════════════════════════════════════════════════════════
# TEST get_monthly_revenue()
# ══════════════════════════════════════════════════════════════

class TestSaleModelGetMonthlyRevenue(unittest.TestCase):

    @patch('models.sale.db')
    def test_get_monthly_revenue_par_defaut(self, mock_db):
        """TC-SMR-01 : get_monthly_revenue() appelle db avec months=6."""
        mock_db.execute_query.return_value = []
        SaleModel.get_monthly_revenue()
        params = mock_db.execute_query.call_args[0][1]
        self.assertEqual(params, (6,))

    @patch('models.sale.db')
    def test_get_monthly_revenue_personnalise(self, mock_db):
        """TC-SMR-02 : get_monthly_revenue(12) appelle db avec months=12."""
        mock_db.execute_query.return_value = []
        SaleModel.get_monthly_revenue(months=12)
        params = mock_db.execute_query.call_args[0][1]
        self.assertEqual(params, (12,))


# ══════════════════════════════════════════════════════════════
# TEST add_payment()
# ══════════════════════════════════════════════════════════════

class TestSaleModelAddPayment(unittest.TestCase):

    @patch('models.sale.db')
    @patch.object(SaleModel, 'get_by_id', return_value=None)
    def test_vente_introuvable_leve_exception(self, mock_get, mock_db):
        """TC-SAP-01 : add_payment() lève ValueError si vente inexistante."""
        with self.assertRaises(ValueError) as ctx:
            SaleModel.add_payment(999, 10000)
        self.assertIn('introuvable', str(ctx.exception).lower())

    @patch('models.sale.db')
    @patch.object(SaleModel, 'get_by_id', return_value={
        'id': 1, 'statut': 'annulee',
        'montant_total': 100000, 'montant_paye': 0, 'montant_reste': 100000
    })
    def test_paiement_vente_annulee_leve_exception(self, mock_get, mock_db):
        """TC-SAP-02 : add_payment() sur vente annulée lève ValueError."""
        with self.assertRaises(ValueError) as ctx:
            SaleModel.add_payment(1, 50000)
        self.assertIn('annulee', str(ctx.exception).lower())

    @patch('models.sale.db')
    @patch.object(SaleModel, 'get_by_id', return_value={
        'id': 1, 'statut': 'en_cours',
        'montant_total': 100000, 'montant_paye': 80000, 'montant_reste': 20000
    })
    def test_paiement_depasse_total_leve_exception(self, mock_get, mock_db):
        """TC-SAP-03 : paiement > reste lève ValueError."""
        with self.assertRaises(ValueError) as ctx:
            SaleModel.add_payment(1, 50000)
        self.assertIn('depasse', str(ctx.exception).lower())

    @patch('models.sale.db')
    @patch.object(SaleModel, 'get_by_id', return_value={
        'id': 1, 'statut': 'en_cours',
        'montant_total': 100000, 'montant_paye': 50000, 'montant_reste': 50000
    })
    def test_paiement_partiel_statut_partielle(self, mock_get, mock_db):
        """TC-SAP-04 : paiement partiel → statut = 'partielle'."""
        mock_db.execute_update.return_value = True
        result = SaleModel.add_payment(1, 30000)
        self.assertTrue(result)
        call_args = mock_db.execute_update.call_args[0]
        self.assertIn('partielle', call_args[1])

    @patch('models.sale.db')
    @patch.object(SaleModel, 'get_by_id', return_value={
        'id': 1, 'statut': 'en_cours',
        'montant_total': 100000, 'montant_paye': 50000, 'montant_reste': 50000
    })
    def test_paiement_complet_statut_payee(self, mock_get, mock_db):
        """TC-SAP-05 : paiement complet → statut = 'payee'."""
        mock_db.execute_update.return_value = True
        result = SaleModel.add_payment(1, 50000)
        self.assertTrue(result)
        call_args = mock_db.execute_update.call_args[0]
        self.assertIn('payee', call_args[1])


# ══════════════════════════════════════════════════════════════
# TEST validate()
# ══════════════════════════════════════════════════════════════

class TestSaleModelValidate(unittest.TestCase):

    @patch('models.sale.db')
    @patch.object(SaleModel, 'add_payment', return_value=True)
    def test_validate_avec_reste_appelle_add_payment(self, mock_pay, mock_db):
        """TC-SV-01 : validate() avec reste > 0 appelle add_payment."""
        result = SaleModel.validate(1, 25000)
        self.assertTrue(result)
        mock_pay.assert_called_once_with(1, 25000)

    @patch('models.sale.db')
    def test_validate_sans_reste_met_a_jour_statut(self, mock_db):
        """TC-SV-02 : validate() avec reste = 0 update directement le statut."""
        mock_db.execute_update.return_value = True
        result = SaleModel.validate(1, 0)
        self.assertTrue(result)
        call_sql = mock_db.execute_update.call_args[0][0]
        self.assertIn('payee', call_sql)


# ══════════════════════════════════════════════════════════════
# TEST cancel()
# ══════════════════════════════════════════════════════════════

class TestSaleModelCancel(unittest.TestCase):

    @patch('models.sale.db')
    @patch.object(SaleModel, 'get_by_id', return_value=None)
    def test_cancel_vente_introuvable_leve_exception(self, mock_get, mock_db):
        """TC-SC-01 : cancel() lève ValueError si vente inexistante."""
        with self.assertRaises(ValueError) as ctx:
            SaleModel.cancel(999)
        self.assertIn('introuvable', str(ctx.exception).lower())

    @patch('models.sale.db')
    @patch.object(SaleModel, 'get_by_id', return_value={
        'id': 1, 'statut': 'annulee'
    })
    def test_cancel_vente_deja_annulee_leve_exception(self, mock_get, mock_db):
        """TC-SC-02 : cancel() sur vente déjà annulée lève ValueError."""
        with self.assertRaises(ValueError) as ctx:
            SaleModel.cancel(1)
        self.assertIn('annulee', str(ctx.exception).lower())

    @patch('models.sale.db')
    @patch.object(SaleModel, 'get_by_id', return_value={
        'id': 1, 'statut': 'payee'
    })
    def test_cancel_vente_payee_leve_exception(self, mock_get, mock_db):
        """TC-SC-03 : cancel() sur vente payée lève ValueError."""
        with self.assertRaises(ValueError) as ctx:
            SaleModel.cancel(1)
        self.assertIn('payee', str(ctx.exception).lower())

    @patch('models.sale.db')
    @patch.object(SaleModel, 'get_details', return_value=[
        {'produit_id': 1, 'quantite': 2},
        {'produit_id': 2, 'quantite': 1},
    ])
    @patch.object(SaleModel, 'get_by_id', return_value={
        'id': 1, 'statut': 'en_cours'
    })
    def test_cancel_reussie_restaure_stock(self, mock_get, mock_details, mock_db):
        """TC-SC-04 : cancel() restaure le stock de chaque produit."""
        mock_db.execute_update.return_value = True
        result = SaleModel.cancel(1)
        self.assertTrue(result)
        # 2 appels stock + 1 UPDATE statut = 3 appels total
        self.assertEqual(mock_db.execute_update.call_count, 3)


# ══════════════════════════════════════════════════════════════
# TEST count()
# ══════════════════════════════════════════════════════════════

class TestSaleModelCount(unittest.TestCase):

    @patch('models.sale.db')
    def test_count_retourne_nombre(self, mock_db):
        """TC-SCT-01 : count() retourne le nombre total de ventes."""
        mock_db.execute_query.return_value = {'total': 42}
        result = SaleModel.count()
        self.assertEqual(result, 42)

    @patch('models.sale.db')
    def test_count_retourne_zero_si_none(self, mock_db):
        """TC-SCT-02 : count() retourne 0 si db retourne None."""
        mock_db.execute_query.return_value = None
        result = SaleModel.count()
        self.assertEqual(result, 0)


# ══════════════════════════════════════════════════════════════
# TEST get_recent()
# ══════════════════════════════════════════════════════════════

class TestSaleModelGetRecent(unittest.TestCase):

    @patch('models.sale.db')
    def test_get_recent_par_defaut(self, mock_db):
        """TC-SGR-01 : get_recent() appelle db avec limit=8."""
        mock_db.execute_query.return_value = []
        SaleModel.get_recent()
        params = mock_db.execute_query.call_args[0][1]
        self.assertEqual(params, (8,))

    @patch('models.sale.db')
    def test_get_recent_personnalise(self, mock_db):
        """TC-SGR-02 : get_recent(5) appelle db avec limit=5."""
        mock_db.execute_query.return_value = []
        SaleModel.get_recent(limit=5)
        params = mock_db.execute_query.call_args[0][1]
        self.assertEqual(params, (5,))


# ══════════════════════════════════════════════════════════════
# TEST get_dashboard_stats()
# ══════════════════════════════════════════════════════════════

class TestSaleModelDashboardStats(unittest.TestCase):

    @patch('models.sale.db')
    def test_get_dashboard_stats_retourne_dict(self, mock_db):
        """TC-SDS-01 : get_dashboard_stats() retourne le dict des stats."""
        mock_db.execute_query.return_value = {
            'ca_total': 5000000, 'ventes_jour': 3,
            'ventes_mois': 45, 'panier_moyen': 111111,
            'total_impayes': 200000
        }
        result = SaleModel.get_dashboard_stats()
        self.assertEqual(result['ca_total'], 5000000)

    @patch('models.sale.db')
    def test_get_dashboard_stats_retourne_dict_vide_si_none(self, mock_db):
        """TC-SDS-02 : get_dashboard_stats() retourne {} si None."""
        mock_db.execute_query.return_value = None
        result = SaleModel.get_dashboard_stats()
        self.assertEqual(result, {})


# ══════════════════════════════════════════════════════════════
# TEST get_report_ventes()
# ══════════════════════════════════════════════════════════════

class TestSaleModelReportVentes(unittest.TestCase):

    @patch('models.sale.db')
    def test_get_report_ventes_sans_vendeur(self, mock_db):
        """TC-SRV-01 : get_report_ventes() sans vendeur_id."""
        mock_db.execute_query.return_value = []
        SaleModel.get_report_ventes('2024-01-01', '2024-01-31')
        params = mock_db.execute_query.call_args[0][1]
        self.assertEqual(params, ['2024-01-01', '2024-01-31'])

    @patch('models.sale.db')
    def test_get_report_ventes_avec_vendeur(self, mock_db):
        """TC-SRV-02 : get_report_ventes() avec vendeur_id ajoute le filtre."""
        mock_db.execute_query.return_value = []
        SaleModel.get_report_ventes('2024-01-01', '2024-01-31', vendeur_id=3)
        params = mock_db.execute_query.call_args[0][1]
        self.assertIn(3, params)
        sql = mock_db.execute_query.call_args[0][0]
        self.assertIn('user_id', sql)


# ══════════════════════════════════════════════════════════════
# TEST get_report_impayes()
# ══════════════════════════════════════════════════════════════

class TestSaleModelReportImpayes(unittest.TestCase):

    @patch('models.sale.db')
    def test_get_report_impayes_sans_vendeur(self, mock_db):
        """TC-SRI-01 : get_report_impayes() sans vendeur_id."""
        mock_db.execute_query.return_value = []
        SaleModel.get_report_impayes('2024-01-01', '2024-01-31')
        params = mock_db.execute_query.call_args[0][1]
        self.assertEqual(params, ['2024-01-01', '2024-01-31'])

    @patch('models.sale.db')
    def test_get_report_impayes_avec_vendeur(self, mock_db):
        """TC-SRI-02 : get_report_impayes() avec vendeur_id ajoute le filtre."""
        mock_db.execute_query.return_value = []
        SaleModel.get_report_impayes('2024-01-01', '2024-01-31', vendeur_id=2)
        params = mock_db.execute_query.call_args[0][1]
        self.assertIn(2, params)


# ══════════════════════════════════════════════════════════════
# TEST get_report_vendeurs()
# ══════════════════════════════════════════════════════════════

class TestSaleModelReportVendeurs(unittest.TestCase):

    @patch('models.sale.db')
    def test_get_report_vendeurs_retourne_liste(self, mock_db):
        """TC-SRN-01 : get_report_vendeurs() retourne les stats par vendeur."""
        mock_db.execute_query.return_value = [
            {'vendeur': 'admin', 'nb_ventes': 5, 'ca': 500000}
        ]
        result = SaleModel.get_report_vendeurs('2024-01-01', '2024-01-31')
        self.assertEqual(len(result), 1)
        params = mock_db.execute_query.call_args[0][1]
        self.assertEqual(params, ['2024-01-01', '2024-01-31'])

    @patch('models.sale.db')
    def test_get_report_vendeurs_retourne_liste_vide_si_none(self, mock_db):
        """TC-SRN-02 : get_report_vendeurs() retourne [] si None."""
        mock_db.execute_query.return_value = None
        result = SaleModel.get_report_vendeurs('2024-01-01', '2024-01-31')
        self.assertEqual(result, [])


# ══════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    unittest.main(verbosity=2)
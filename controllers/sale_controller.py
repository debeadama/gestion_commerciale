# controllers/sale_controller.py
"""
Controleur Vente.
Logique metier pour la gestion des ventes et paiements.
"""

from models.sale import SaleModel
from models.product import ProductModel
from controllers.auth_controller import SessionManager
import logging

logger = logging.getLogger(__name__)


class SaleController:

    # ── Lecture ───────────────────────────────────────────────

    @staticmethod
    def get_all(search: str = None, statut: str = None) -> list:
        """Retourne toutes les ventes avec filtres optionnels."""
        return SaleModel.get_all(search, statut) or []

    @staticmethod
    def get_by_id(sale_id: int) -> dict:
        """Retourne une vente par son ID avec ses details."""
        return SaleModel.get_by_id(sale_id)

    @staticmethod
    def get_details(sale_id: int) -> list:
        """Retourne les lignes de detail d'une vente."""
        return SaleModel.get_details(sale_id) or []

    @staticmethod
    def get_pending() -> list:
        """Retourne les ventes en attente (en_cours ou partielles)."""
        return SaleModel.get_pending() or []

    # ── Creation ──────────────────────────────────────────────

    @staticmethod
    def create(client_id: int, panier: list,
               montant_paye: float, notes: str = '') -> tuple:
        """
        Cree une nouvelle vente.
        panier = [{'produit_id': x, 'quantite': y, 'prix_unitaire': z}, ...]
        Returns: (True, vente_id) ou (False, message_erreur)
        """
        if not panier:
            return False, "Le panier est vide."

        for ligne in panier:
            produit = ProductModel.get_by_id(ligne['produit_id'])
            if not produit:
                return False, f"Produit ID {ligne['produit_id']} introuvable."
            if produit['stock_actuel'] < ligne['quantite']:
                return False, (
                    f"Stock insuffisant pour '{produit['nom']}'. "
                    f"Disponible : {produit['stock_actuel']}, "
                    f"demande : {ligne['quantite']}.")

        montant_total = sum(
            float(l['quantite']) * float(l['prix_unitaire'])
            for l in panier)

        if montant_paye < 0:
            return False, "Le montant paye ne peut pas etre negatif."
        if montant_paye > montant_total:
            return False, "Le montant paye depasse le total de la vente."

        montant_reste = montant_total - montant_paye
        if montant_reste == 0:
            statut = 'payee'
        elif montant_paye == 0:
            statut = 'en_cours'
        else:
            statut = 'partielle'

        user = SessionManager.get_current_user()
        user_id = user['id'] if user else None

        try:
            sale_data = {
                'client_id':     client_id,
                'user_id':       user_id,
                'montant_total': montant_total,
                'montant_paye':  montant_paye,
                'montant_reste': montant_reste,
                'statut':        statut,
                'notes':         notes,
                'panier':        panier,
            }
            sale_id = SaleModel.create(sale_data)
            logger.info(
                f"Vente creee : ID={sale_id}, total={montant_total}, "
                f"statut={statut}")
            return True, sale_id
        except Exception as e:
            logger.error(f"Erreur creation vente : {e}")
            return False, str(e)

    # ── Paiement ──────────────────────────────────────────────

    @staticmethod
    def add_payment(sale_id: int, montant: float) -> tuple:
        """
        Ajoute un paiement partiel a une vente.
        Returns: (True, message) ou (False, message_erreur)
        """
        vente = SaleModel.get_by_id(sale_id)
        if not vente:
            return False, "Vente introuvable."

        if vente['statut'] in ('payee', 'annulee'):
            return False, f"Impossible : la vente est deja '{vente['statut']}'."

        reste = float(vente['montant_reste'])
        if montant <= 0:
            return False, "Le montant doit etre superieur a 0."
        if montant > reste:
            return False, (
                f"Le montant ({montant:.2f}) depasse le reste a payer ({reste:.2f}).")

        try:
            SaleModel.add_payment(sale_id, montant)
            new_reste = reste - montant
            msg = ("Vente soldee." if new_reste == 0
                   else f"Paiement enregistre. Reste : {new_reste:.2f}")
            return True, msg
        except Exception as e:
            return False, str(e)

    # ── Validation ────────────────────────────────────────────

    @staticmethod
    def validate(sale_id: int) -> tuple:
        """
        Valide une vente (passe le statut a 'payee').
        Uniquement pour admin et manager.
        """
        if not SessionManager.has_permission('view_reports'):
            return False, "Permission insuffisante pour valider une vente."

        vente = SaleModel.get_by_id(sale_id)
        if not vente:
            return False, "Vente introuvable."
        if vente['statut'] not in ('en_cours', 'partielle'):
            return False, "Seules les ventes en cours ou partielles peuvent etre validees."

        try:
            SaleModel.validate(sale_id, float(vente.get('montant_reste', 0)))
            logger.info(f"Vente {sale_id} validee.")
            return True, "Vente validee et marquee comme payee."
        except Exception as e:
            return False, str(e)

    # ── Annulation ────────────────────────────────────────────

    @staticmethod
    def cancel(sale_id: int) -> tuple:
        """
        Annule une vente et remet le stock a jour.
        Returns: (True, message) ou (False, message_erreur)
        """
        vente = SaleModel.get_by_id(sale_id)
        if not vente:
            return False, "Vente introuvable."
        if vente['statut'] == 'annulee':
            return False, "Cette vente est deja annulee."
        if vente['statut'] == 'payee':
            return False, "Une vente payee ne peut pas etre annulee."

        try:
            SaleModel.cancel(sale_id)
            logger.info(f"Vente {sale_id} annulee.")
            return True, "Vente annulee et stock remis a jour."
        except Exception as e:
            return False, str(e)

    # ── Statistiques ──────────────────────────────────────────

    @staticmethod
    def get_kpi() -> dict:
        """Retourne les KPIs principaux pour le dashboard."""
        return SaleModel.get_kpi()

    @staticmethod
    def get_top_products(limit: int = 5) -> list:
        """Retourne les produits les plus vendus."""
        return SaleModel.get_top_products(limit) or []

    @staticmethod
    def get_top_clients(limit: int = 5) -> list:
        """Retourne les meilleurs clients par CA."""
        return SaleModel.get_top_clients(limit) or []

    @staticmethod
    def get_monthly_revenue(months: int = 6) -> list:
        """Retourne le CA mensuel sur les N derniers mois."""
        return SaleModel.get_monthly_revenue(months) or []

    @staticmethod
    def get_recent(limit: int = 8) -> list:
        return SaleModel.get_recent(limit)

    @staticmethod
    def get_dashboard_stats() -> dict:
        return SaleModel.get_dashboard_stats()

    @staticmethod
    def get_report_ventes(debut, fin, vendeur_id=None) -> list:
        return SaleModel.get_report_ventes(debut, fin, vendeur_id)

    @staticmethod
    def get_report_impayes(debut, fin, vendeur_id=None) -> list:
        return SaleModel.get_report_impayes(debut, fin, vendeur_id)

    @staticmethod
    def get_report_vendeurs(debut, fin) -> list:
        return SaleModel.get_report_vendeurs(debut, fin)

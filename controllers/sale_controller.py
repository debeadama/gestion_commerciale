# controllers/sale_controller.py
"""
Controleur Vente.

Logique metier pour la gestion des ventes et des paiements.
"""

import logging

from controllers.auth_controller import SessionManager
from models.product import ProductModel
from models.sale import SaleModel

logger = logging.getLogger(__name__)


class SaleController:
    """Controleur pour la gestion des ventes, paiements et statistiques."""

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    @staticmethod
    def get_all(search: str = None, statut: str = None) -> list:
        """
        Retourne toutes les ventes avec filtres optionnels.

        Args:
            search (str): Terme de recherche (numero facture, client).
            statut (str): Filtre par statut (payee, partielle, ...).

        Returns:
            list: Liste des ventes ou liste vide.
        """
        return SaleModel.get_all(search, statut) or []

    @staticmethod
    def get_by_id(sale_id: int) -> dict:
        """
        Retourne une vente par son ID avec tous ses details.

        Args:
            sale_id (int): Identifiant de la vente.

        Returns:
            dict: Donnees de la vente ou None.
        """
        return SaleModel.get_by_id(sale_id)

    @staticmethod
    def get_details(sale_id: int) -> list:
        """
        Retourne les lignes de detail d'une vente.

        Args:
            sale_id (int): Identifiant de la vente.

        Returns:
            list: Liste des lignes ou liste vide.
        """
        return SaleModel.get_details(sale_id) or []

    @staticmethod
    def get_pending() -> list:
        """
        Retourne les ventes en attente (en_cours ou partielles).

        Returns:
            list: Liste des ventes en attente ou liste vide.
        """
        return SaleModel.get_pending() or []

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    @staticmethod
    def create(
        client_id: int,
        panier: list,
        montant_paye: float,
        notes: str = ''
    ) -> tuple:
        """
        Cree une nouvelle vente apres validation du panier et du stock.

        Args:
            client_id (int): Identifiant du client.
            panier (list): Liste de dicts avec produit_id, quantite,
                prix_unitaire.
            montant_paye (float): Montant paye par le client.
            notes (str): Notes optionnelles sur la vente.

        Returns:
            tuple: (True, vente_id) ou (False, message_erreur).
        """
        if not panier:
            return False, "Le panier est vide."

        for ligne in panier:
            produit = ProductModel.get_by_id(ligne['produit_id'])
            if not produit:
                return False, (
                    f"Produit ID {ligne['produit_id']} introuvable."
                )
            if produit['stock_actuel'] < ligne['quantite']:
                return False, (
                    f"Stock insuffisant pour '{produit['nom']}'. "
                    f"Disponible : {produit['stock_actuel']}, "
                    f"demande : {ligne['quantite']}."
                )

        montant_total = sum(
            float(ligne['quantite']) * float(ligne['prix_unitaire'])
            for ligne in panier
        )

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
                'client_id': client_id,
                'user_id': user_id,
                'montant_total': montant_total,
                'montant_paye': montant_paye,
                'montant_reste': montant_reste,
                'statut': statut,
                'notes': notes,
                'panier': panier,
            }
            sale_id = SaleModel.create(sale_data)
            logger.info(
                f"Vente creee : ID={sale_id}, "
                f"total={montant_total}, statut={statut}"
            )
            return True, sale_id
        except Exception as e:
            logger.error(f"Erreur creation vente : {e}")
            return False, str(e)

    # ------------------------------------------------------------------
    # Paiement
    # ------------------------------------------------------------------

    @staticmethod
    def add_payment(sale_id: int, montant: float) -> tuple:
        """
        Ajoute un paiement partiel ou complet a une vente.

        Args:
            sale_id (int): Identifiant de la vente.
            montant (float): Montant du paiement.

        Returns:
            tuple: (True, message) ou (False, message_erreur).
        """
        vente = SaleModel.get_by_id(sale_id)
        if not vente:
            return False, "Vente introuvable."

        if vente['statut'] in ('payee', 'annulee'):
            return False, (
                f"Impossible : la vente est deja '{vente['statut']}'."
            )

        reste = float(vente['montant_reste'])
        if montant <= 0:
            return False, "Le montant doit etre superieur a 0."
        if montant > reste:
            return False, (
                f"Le montant ({montant:.2f}) "
                f"depasse le reste a payer ({reste:.2f})."
            )

        try:
            SaleModel.add_payment(sale_id, montant)
            new_reste = reste - montant
            msg = (
                "Vente soldee."
                if new_reste == 0
                else f"Paiement enregistre. Reste : {new_reste:.2f}"
            )
            return True, msg
        except Exception as e:
            return False, str(e)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate(sale_id: int) -> tuple:
        """
        Valide une vente en passant son statut a 'payee'.

        Accessible uniquement aux roles admin et manager.

        Args:
            sale_id (int): Identifiant de la vente.

        Returns:
            tuple: (True, message) ou (False, message_erreur).
        """
        if not SessionManager.has_permission('view_reports'):
            return False, "Permission insuffisante pour valider une vente."

        vente = SaleModel.get_by_id(sale_id)
        if not vente:
            return False, "Vente introuvable."
        if vente['statut'] not in ('en_cours', 'partielle'):
            return False, (
                "Seules les ventes en cours ou partielles "
                "peuvent etre validees."
            )

        try:
            SaleModel.validate(
                sale_id, float(vente.get('montant_reste', 0))
            )
            logger.info(f"Vente {sale_id} validee.")
            return True, "Vente validee et marquee comme payee."
        except Exception as e:
            return False, str(e)

    # ------------------------------------------------------------------
    # Annulation
    # ------------------------------------------------------------------

    @staticmethod
    def cancel(sale_id: int) -> tuple:
        """
        Annule une vente et remet le stock des produits a jour.

        Args:
            sale_id (int): Identifiant de la vente.

        Returns:
            tuple: (True, message) ou (False, message_erreur).
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

    # ------------------------------------------------------------------
    # Statistiques et rapports
    # ------------------------------------------------------------------

    @staticmethod
    def get_kpi() -> dict:
        """
        Retourne les KPIs principaux pour le tableau de bord.

        Returns:
            dict: CA jour, semaine, mois, impayes, ventes en cours.
        """
        return SaleModel.get_kpi()

    @staticmethod
    def get_top_products(limit: int = 5) -> list:
        """
        Retourne les produits les plus vendus.

        Args:
            limit (int): Nombre de produits a retourner.

        Returns:
            list: Liste des produits ou liste vide.
        """
        return SaleModel.get_top_products(limit) or []

    @staticmethod
    def get_top_clients(limit: int = 5) -> list:
        """
        Retourne les meilleurs clients par chiffre d'affaires.

        Args:
            limit (int): Nombre de clients a retourner.

        Returns:
            list: Liste des clients ou liste vide.
        """
        return SaleModel.get_top_clients(limit) or []

    @staticmethod
    def get_monthly_revenue(months: int = 6) -> list:
        """
        Retourne le CA mensuel sur les N derniers mois.

        Args:
            months (int): Nombre de mois a inclure.

        Returns:
            list: Liste des CA mensuels ou liste vide.
        """
        return SaleModel.get_monthly_revenue(months) or []

    @staticmethod
    def get_recent(limit: int = 8) -> list:
        """
        Retourne les N dernieres ventes pour le tableau de bord.

        Args:
            limit (int): Nombre de ventes a retourner.

        Returns:
            list: Liste des ventes recentes.
        """
        return SaleModel.get_recent(limit)

    @staticmethod
    def get_dashboard_stats() -> dict:
        """
        Retourne les statistiques globales pour le tableau de bord.

        Returns:
            dict: CA total, ventes jour/mois, panier moyen, impayes.
        """
        return SaleModel.get_dashboard_stats()

    @staticmethod
    def get_report_ventes(
        debut: str,
        fin: str,
        vendeur_id: int = None
    ) -> list:
        """
        Retourne les ventes sur une periode pour le rapport.

        Args:
            debut (str): Date de debut (YYYY-MM-DD).
            fin (str): Date de fin (YYYY-MM-DD).
            vendeur_id (int): Filtre par vendeur (optionnel).

        Returns:
            list: Liste des ventes de la periode.
        """
        return SaleModel.get_report_ventes(debut, fin, vendeur_id)

    @staticmethod
    def get_report_impayes(
        debut: str,
        fin: str,
        vendeur_id: int = None
    ) -> list:
        """
        Retourne les impayes sur une periode pour le rapport.

        Args:
            debut (str): Date de debut (YYYY-MM-DD).
            fin (str): Date de fin (YYYY-MM-DD).
            vendeur_id (int): Filtre par vendeur (optionnel).

        Returns:
            list: Liste des ventes impayees.
        """
        return SaleModel.get_report_impayes(debut, fin, vendeur_id)

    @staticmethod
    def get_report_vendeurs(debut: str, fin: str) -> list:
        """
        Retourne les statistiques par vendeur pour le rapport.

        Args:
            debut (str): Date de debut (YYYY-MM-DD).
            fin (str): Date de fin (YYYY-MM-DD).

        Returns:
            list: Statistiques (nb ventes, CA) par vendeur.
        """
        return SaleModel.get_report_vendeurs(debut, fin)

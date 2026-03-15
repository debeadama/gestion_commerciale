# controllers/client_controller.py
"""
Controleur Client.
Logique metier pour la gestion des clients.
"""

from models.client import ClientModel
import logging

logger = logging.getLogger(__name__)


class ClientController:

    # ── Lecture ───────────────────────────────────────────────

    @staticmethod
    def get_all(search: str = None) -> list:
        """Retourne tous les clients, avec recherche multicritere optionnelle."""
        return ClientModel.get_all(search) or []

    @staticmethod
    def get_by_id(client_id: int) -> dict:
        """Retourne un client par son ID."""
        return ClientModel.get_by_id(client_id)

    @staticmethod
    def get_purchase_history(client_id: int) -> list:
        """Retourne l'historique des achats d'un client."""
        return ClientModel.get_purchase_history(client_id) or []

    @staticmethod
    def get_stats(client_id: int) -> dict:
        """Calcule les statistiques d'un client (CA, nb achats, derniere visite)."""
        return ClientModel.get_stats(client_id)

    # ── Creation ──────────────────────────────────────────────

    @staticmethod
    def create(data: dict) -> tuple:
        """
        Cree un nouveau client apres validation.
        Returns: (True, client_id) ou (False, message_erreur)
        """
        nom    = data.get('nom', '').strip()
        prenom = data.get('prenom', '').strip()

        if not nom:
            return False, "Le nom du client est obligatoire."
        if not prenom:
            return False, "Le prenom du client est obligatoire."

        # Verifier doublon (meme nom + prenom + telephone)
        telephone = data.get('telephone', '').strip()
        if telephone:
            existing = ClientModel.find_duplicate(nom, prenom, telephone)
            if existing:
                return False, "Un client avec ce nom et ce telephone existe deja."

        try:
            cid = ClientModel.create(data)
            logger.info(f"Client cree : {nom} {prenom} (ID: {cid})")
            return True, cid
        except Exception as e:
            logger.error(f"Erreur creation client : {e}")
            return False, str(e)

    # ── Modification ──────────────────────────────────────────

    @staticmethod
    def update(client_id: int, data: dict) -> tuple:
        """Met a jour un client existant apres validation."""
        nom    = data.get('nom', '').strip()
        prenom = data.get('prenom', '').strip()

        if not nom:
            return False, "Le nom du client est obligatoire."
        if not prenom:
            return False, "Le prenom du client est obligatoire."

        try:
            ClientModel.update(client_id, data)
            return True, "Client mis a jour."
        except Exception as e:
            return False, str(e)

    # ── Suppression ───────────────────────────────────────────

    @staticmethod
    def delete(client_id: int) -> tuple:
        """
        Supprime un client apres verification des ventes associees.
        Returns: (True, message) ou (False, message_erreur)
        """
        try:
            ClientModel.delete(client_id)
            return True, "Client supprime."
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)

    # ── Export ────────────────────────────────────────────────

    @staticmethod
    def get_export_data() -> list:
        """Retourne les donnees clients enrichies pour export."""
        return ClientModel.get_export_data()

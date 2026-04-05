# models/client.py
"""Modele Client - CRUD complet pour la gestion des clients."""

from database.connection import db




class ClientModel:
    """Modele d'acces aux donnees pour les clients."""

    @staticmethod
    def get_all(search: str = None) -> list:
        """
        Retourne tous les clients avec recherche multicritere optionnelle.

        Args:
            search (str): Terme de recherche sur nom, prenom, telephone
                ou email.

        Returns:
            list: Liste des clients ou None.
        """
        if search:
            pattern = f"%{search}%"
            return db.execute_query(
                """
                SELECT * FROM clients
                WHERE nom LIKE %s
                   OR prenom LIKE %s
                   OR telephone LIKE %s
                   OR email LIKE %s
                ORDER BY nom, prenom
                """,
                (pattern, pattern, pattern, pattern),
            )
        return db.execute_query(
            "SELECT * FROM clients ORDER BY nom, prenom"
        )

    @staticmethod
    def get_by_id(client_id: int) -> dict | None:
        """
        Retourne un client par son ID.

        Args:
            client_id (int): Identifiant du client.

        Returns:
            dict: Donnees du client ou None.
        """
        return db.execute_query(
            "SELECT * FROM clients WHERE id=%s",
            (client_id,),
            fetch_one=True,
        )

    @staticmethod
    def find_duplicate(
        nom: str,
        prenom: str,
        telephone: str
    ) -> dict | None:
        """
        Verifie si un client avec le meme nom, prenom et telephone existe.

        Args:
            nom (str): Nom du client.
            prenom (str): Prenom du client.
            telephone (str): Numero de telephone.

        Returns:
            dict: Client existant ou None.
        """
        return db.execute_query(
            "SELECT id FROM clients "
            "WHERE nom=%s AND prenom=%s AND telephone=%s",
            (nom, prenom, telephone),
            fetch_one=True,
        )

    @staticmethod
    def get_stats(client_id: int) -> dict:
        """
        Retourne les statistiques d'achat d'un client.

        Args:
            client_id (int): Identifiant du client.

        Returns:
            dict: Nombre d'achats, CA total, total paye, derniere visite.
        """
        result = db.execute_query(
            """
            SELECT
                COUNT(*)                        AS nb_achats,
                COALESCE(SUM(montant_total), 0) AS ca_total,
                COALESCE(SUM(montant_paye),  0) AS total_paye,
                DATE_FORMAT(
                    MAX(date_vente), '%%d/%%m/%%Y'
                )                               AS derniere_visite
            FROM ventes
            WHERE client_id = %s AND statut != 'annulee'
            """,
            (client_id,),
            fetch_one=True,
        )
        return result or {}

    @staticmethod
    def get_export_data() -> list:
        """
        Retourne les donnees clients enrichies pour export.

        Returns:
            list: Clients avec statistiques d'achat ou liste vide.
        """
        return db.execute_query(
            """
            SELECT
                c.nom, c.prenom, c.telephone, c.email,
                c.ville, c.code_postal,
                COALESCE(
                    (SELECT COUNT(*) FROM ventes
                     WHERE client_id = c.id AND statut != 'annulee'), 0
                ) AS nb_achats,
                COALESCE(
                    (SELECT SUM(montant_total) FROM ventes
                     WHERE client_id = c.id AND statut != 'annulee'), 0
                ) AS ca_total,
                (SELECT MAX(date_vente)
                 FROM ventes WHERE client_id = c.id) AS derniere_visite
            FROM clients c
            ORDER BY c.nom, c.prenom
            """
        ) or []

    @staticmethod
    def create(data: dict) -> int:
        """
        Ajoute un nouveau client en base de donnees.

        Args:
            data (dict): Donnees du client (nom, prenom, telephone, ...).

        Returns:
            int: ID du client cree.
        """
        return db.execute_update(
            """
            INSERT INTO clients
                (nom, prenom, telephone, email, adresse, ville, code_postal)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                data['nom'],
                data['prenom'],
                data.get('telephone') or None,
                data.get('email') or None,
                data.get('adresse') or None,
                data.get('ville') or None,
                data.get('code_postal') or None,
            ),
        )

    @staticmethod
    def update(client_id: int, data: dict) -> bool:
        """
        Met a jour un client existant.

        Args:
            client_id (int): Identifiant du client.
            data (dict): Nouvelles donnees du client.

        Returns:
            bool: True si la mise a jour a reussi.
        """
        db.execute_update(
            """
            UPDATE clients
            SET nom=%s, prenom=%s, telephone=%s, email=%s,
                adresse=%s, ville=%s, code_postal=%s
            WHERE id=%s
            """,
            (
                data['nom'],
                data['prenom'],
                data.get('telephone') or None,
                data.get('email') or None,
                data.get('adresse') or None,
                data.get('ville') or None,
                data.get('code_postal') or None,
                client_id,
            ),
        )
        return True

    @staticmethod
    def delete(client_id: int) -> bool:
        """
        Supprime un client.

        Args:
            client_id (int): Identifiant du client.

        Returns:
            bool: True si la suppression a reussi.

        Raises:
            ValueError: Si le client a des ventes associees.
        """
        result = db.execute_query(
            "SELECT COUNT(*) AS total FROM ventes WHERE client_id=%s",
            (client_id,),
            fetch_one=True,
        )
        if result and result['total'] > 0:
            raise ValueError(
                f"Impossible de supprimer : ce client a "
                f"{result['total']} vente(s) associee(s)."
            )
        db.execute_update(
            "DELETE FROM clients WHERE id=%s",
            (client_id,),
        )
        return True

    @staticmethod
    def get_purchase_history(client_id: int) -> list:
        """
        Retourne l'historique d'achats d'un client.

        Args:
            client_id (int): Identifiant du client.

        Returns:
            list: Liste des ventes ou None.
        """
        return db.execute_query(
            """
            SELECT v.id, v.numero_facture, v.date_vente,
                   v.montant_total, v.montant_paye,
                   v.montant_reste, v.statut
            FROM ventes v
            WHERE v.client_id=%s
            ORDER BY v.date_vente DESC
            """,
            (client_id,),
        )

    @staticmethod
    def count() -> int:
        """
        Retourne le nombre total de clients.

        Returns:
            int: Nombre de clients.
        """
        result = db.execute_query(
            "SELECT COUNT(*) AS total FROM clients",
            fetch_one=True,
        )
        return result['total'] if result else 0

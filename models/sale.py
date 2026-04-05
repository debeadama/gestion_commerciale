# models/sale.py
"""Modele Vente - CRUD complet pour la gestion des ventes."""

from datetime import datetime

from database.connection import db


class SaleModel:
    """Modele d'acces aux donnees pour les ventes et paiements."""

    @staticmethod
    def get_all(search: str = None, statut: str = None) -> list:
        """
        Retourne toutes les ventes avec filtres optionnels.

        Args:
            search (str): Recherche sur numero facture, nom ou prenom client.
            statut (str): Filtre par statut ('payee', 'partielle', ...).
                La valeur 'tous' desactive le filtre.

        Returns:
            list: Liste des ventes ou None.
        """
        conditions, params = [], []
        if search:
            pattern = f"%{search}%"
            conditions.append(
                "(v.numero_facture LIKE %s "
                "OR c.nom LIKE %s "
                "OR c.prenom LIKE %s)"
            )
            params += [pattern, pattern, pattern]
        if statut and statut != 'tous':
            conditions.append("v.statut = %s")
            params.append(statut)
        where = (
            "WHERE " + " AND ".join(conditions) if conditions else ""
        )
        return db.execute_query(
            f"""
            SELECT v.id, v.numero_facture,
                   CONCAT(c.nom, ' ', c.prenom) AS client,
                   u.username AS vendeur,
                   v.date_vente, v.montant_total,
                   v.montant_paye, v.montant_reste, v.statut
            FROM ventes v
            JOIN clients c ON v.client_id = c.id
            JOIN users   u ON v.user_id   = u.id
            {where}
            ORDER BY v.date_vente DESC
            """,
            params if params else None,
        )

    @staticmethod
    def get_by_id(sale_id: int) -> dict | None:
        """
        Retourne une vente par son ID avec toutes les informations.

        Args:
            sale_id (int): Identifiant de la vente.

        Returns:
            dict: Donnees completes de la vente ou None.
        """
        return db.execute_query(
            """
            SELECT v.*,
                   CONCAT(c.nom, ' ', c.prenom) AS client_nom,
                   c.telephone AS client_tel,
                   c.email     AS client_email,
                   c.adresse   AS client_adresse,
                   c.ville     AS client_ville,
                   u.username  AS vendeur
            FROM ventes v
            JOIN clients c ON v.client_id = c.id
            JOIN users   u ON v.user_id   = u.id
            WHERE v.id = %s
            """,
            (sale_id,),
            fetch_one=True,
        )

    @staticmethod
    def get_details(sale_id: int) -> list:
        """
        Retourne les lignes de detail d'une vente.

        Args:
            sale_id (int): Identifiant de la vente.

        Returns:
            list: Lignes de la vente avec nom produit et sous-totaux.
        """
        return db.execute_query(
            """
            SELECT vd.id, vd.produit_id, p.nom AS produit,
                   vd.quantite, vd.prix_unitaire, vd.sous_total
            FROM ventes_details vd
            JOIN produits p ON vd.produit_id = p.id
            WHERE vd.vente_id = %s
            """,
            (sale_id,),
        )

    @staticmethod
    def get_pending() -> list:
        """
        Retourne les ventes en attente de paiement.

        Returns:
            list: Ventes avec statut 'en_cours' ou 'partielle'.
        """
        return db.execute_query(
            """
            SELECT v.id, v.numero_facture, v.date_vente,
                   CONCAT(c.nom, ' ', c.prenom) AS client,
                   v.montant_total, v.montant_paye,
                   v.montant_reste, v.statut,
                   u.username AS vendeur
            FROM ventes v
            LEFT JOIN clients c ON v.client_id = c.id
            LEFT JOIN users   u ON v.user_id   = u.id
            WHERE v.statut IN ('en_cours', 'partielle')
            ORDER BY v.date_vente DESC
            """
        )

    @staticmethod
    def get_kpi() -> dict:
        """
        Retourne les KPIs principaux pour le tableau de bord.

        Returns:
            dict: CA jour, semaine, mois, impayes, ventes en cours.
        """
        result = db.execute_query(
            """
            SELECT
                COALESCE(SUM(CASE
                    WHEN DATE(date_vente) = CURDATE()
                     AND statut != 'annulee'
                    THEN montant_total ELSE 0 END), 0) AS ca_jour,
                COALESCE(SUM(CASE
                    WHEN YEARWEEK(date_vente) = YEARWEEK(CURDATE())
                     AND statut != 'annulee'
                    THEN montant_total ELSE 0 END), 0) AS ca_semaine,
                COALESCE(SUM(CASE
                    WHEN MONTH(date_vente) = MONTH(CURDATE())
                     AND YEAR(date_vente)  = YEAR(CURDATE())
                     AND statut != 'annulee'
                    THEN montant_total ELSE 0 END), 0) AS ca_mois,
                COUNT(CASE WHEN statut = 'en_cours'
                    THEN 1 END)                        AS nb_en_cours,
                COUNT(CASE WHEN statut = 'partielle'
                    THEN 1 END)                        AS nb_partielles,
                COALESCE(SUM(CASE
                    WHEN statut IN ('en_cours', 'partielle')
                    THEN montant_reste ELSE 0 END), 0) AS total_impayes
            FROM ventes
            """,
            fetch_one=True,
        )
        return result or {}

    @staticmethod
    def get_top_products(limit: int = 5) -> list:
        """
        Retourne les produits les plus vendus.

        Args:
            limit (int): Nombre de produits a retourner.

        Returns:
            list: Produits avec quantite vendue et CA.
        """
        return db.execute_query(
            """
            SELECT p.nom,
                   SUM(vd.quantite)                    AS total_vendu,
                   SUM(vd.quantite * vd.prix_unitaire) AS ca
            FROM ventes_details vd
            JOIN produits p ON vd.produit_id = p.id
            JOIN ventes   v ON vd.vente_id   = v.id
            WHERE v.statut != 'annulee'
            GROUP BY p.id, p.nom
            ORDER BY total_vendu DESC
            LIMIT %s
            """,
            (limit,),
        )

    @staticmethod
    def get_top_clients(limit: int = 5) -> list:
        """
        Retourne les meilleurs clients par chiffre d'affaires.

        Args:
            limit (int): Nombre de clients a retourner.

        Returns:
            list: Clients avec nombre de ventes et CA total.
        """
        return db.execute_query(
            """
            SELECT CONCAT(c.nom, ' ', c.prenom) AS client,
                   COUNT(v.id)                  AS nb_ventes,
                   SUM(v.montant_total)          AS ca_total
            FROM ventes v
            JOIN clients c ON v.client_id = c.id
            WHERE v.statut != 'annulee'
            GROUP BY c.id, c.nom, c.prenom
            ORDER BY ca_total DESC
            LIMIT %s
            """,
            (limit,),
        )

    @staticmethod
    def get_monthly_revenue(months: int = 6) -> list:
        """
        Retourne le CA mensuel sur les N derniers mois.

        Args:
            months (int): Nombre de mois a inclure.

        Returns:
            list: CA par mois avec annee et numero de mois.
        """
        return db.execute_query(
            """
            SELECT DATE_FORMAT(MIN(date_vente), '%%b %%Y') AS mois,
                   YEAR(date_vente)                        AS annee,
                   MONTH(date_vente)                       AS num_mois,
                   SUM(montant_total)                      AS ca
            FROM ventes
            WHERE statut != 'annulee'
              AND date_vente >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
            GROUP BY YEAR(date_vente), MONTH(date_vente)
            ORDER BY annee, num_mois
            """,
            (months,),
        )

    @staticmethod
    def generate_numero() -> str:
        """
        Genere un numero de facture unique au format FAC-YYYYMMDD-XXXX.

        Returns:
            str: Numero de facture unique.
        """
        today = datetime.now().strftime("%Y%m%d")
        result = db.execute_query(
            "SELECT COUNT(*) AS total FROM ventes "
            "WHERE DATE(date_vente) = CURDATE()",
            fetch_one=True,
        )
        seq = result['total'] + 1
        return f"FAC-{today}-{seq:04d}"

    @staticmethod
    def create(sale_data: dict) -> int:
        """
        Cree une nouvelle vente avec ses lignes de detail.

        Met a jour automatiquement le stock de chaque produit.

        Args:
            sale_data (dict): Donnees de la vente avec les cles :
                client_id, user_id, montant_total, montant_paye,
                montant_reste, statut, notes, panier.
                panier est une liste de dicts avec produit_id,
                quantite, prix_unitaire.

        Returns:
            int: ID de la vente creee.
        """
        numero = SaleModel.generate_numero()
        sale_id = db.execute_update(
            """
            INSERT INTO ventes
                (numero_facture, client_id, user_id, montant_total,
                 montant_paye, statut, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                numero,
                sale_data['client_id'],
                sale_data['user_id'],
                sale_data['montant_total'],
                sale_data['montant_paye'],
                sale_data['statut'],
                sale_data.get('notes', ''),
            ),
        )
        for ligne in sale_data['panier']:
            db.execute_update(
                """
                INSERT INTO ventes_details
                    (vente_id, produit_id, quantite, prix_unitaire)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    sale_id,
                    ligne['produit_id'],
                    ligne['quantite'],
                    ligne['prix_unitaire'],
                ),
            )
            db.execute_update(
                "UPDATE produits "
                "SET stock_actuel = stock_actuel - %s WHERE id = %s",
                (ligne['quantite'], ligne['produit_id']),
            )
        return sale_id

    @staticmethod
    def add_payment(sale_id: int, montant: float) -> bool:
        """
        Ajoute un paiement et met a jour le statut de la vente.

        Args:
            sale_id (int): Identifiant de la vente.
            montant (float): Montant du paiement.

        Returns:
            bool: True si le paiement a ete enregistre.

        Raises:
            ValueError: Si la vente est introuvable, annulee ou si le
                montant depasse le total restant.
        """
        vente = SaleModel.get_by_id(sale_id)
        if not vente:
            raise ValueError("Vente introuvable.")
        if vente['statut'] == 'annulee':
            raise ValueError("Impossible de payer une vente annulee.")
        nouveau_paye = float(vente['montant_paye']) + float(montant)
        total = float(vente['montant_total'])
        if nouveau_paye > total:
            raise ValueError(
                f"Montant depasse le total. "
                f"Reste : {float(vente['montant_reste']):.2f}"
            )
        nouveau_reste = total - nouveau_paye
        statut = 'payee' if nouveau_paye >= total else 'partielle'
        db.execute_update(
            "UPDATE ventes SET montant_paye=%s, statut=%s WHERE id=%s",
            (nouveau_paye, statut, sale_id),
        )
        return True

    @staticmethod
    def validate(sale_id: int, montant_reste: float) -> bool:
        """
        Force le statut de la vente a 'payee'.

        Solde le reste si necessaire via add_payment.

        Args:
            sale_id (int): Identifiant de la vente.
            montant_reste (float): Montant restant a solder.

        Returns:
            bool: True si la validation a reussi.
        """
        if montant_reste > 0:
            SaleModel.add_payment(sale_id, montant_reste)
        else:
            db.execute_update(
                "UPDATE ventes SET statut='payee' WHERE id=%s",
                (sale_id,),
            )
        return True

    @staticmethod
    def cancel(sale_id: int) -> bool:
        """
        Annule une vente et remet le stock des produits a jour.

        Args:
            sale_id (int): Identifiant de la vente.

        Returns:
            bool: True si l'annulation a reussi.

        Raises:
            ValueError: Si la vente est introuvable, deja annulee
                ou deja payee.
        """
        vente = SaleModel.get_by_id(sale_id)
        if not vente:
            raise ValueError("Vente introuvable.")
        if vente['statut'] == 'annulee':
            raise ValueError("Cette vente est deja annulee.")
        if vente['statut'] == 'payee':
            raise ValueError("Impossible d'annuler une vente deja payee.")
        details = SaleModel.get_details(sale_id)
        for detail in details:
            db.execute_update(
                "UPDATE produits "
                "SET stock_actuel = stock_actuel + %s WHERE id = %s",
                (detail['quantite'], detail['produit_id']),
            )
        db.execute_update(
            "UPDATE ventes SET statut='annulee' WHERE id=%s",
            (sale_id,),
        )
        return True

    @staticmethod
    def count() -> int:
        """
        Retourne le nombre total de ventes.

        Returns:
            int: Nombre de ventes.
        """
        result = db.execute_query(
            "SELECT COUNT(*) AS total FROM ventes",
            fetch_one=True,
        )
        return result['total'] if result else 0

    @staticmethod
    def get_recent(limit: int = 8) -> list:
        """
        Retourne les N dernieres ventes pour le tableau de bord.

        Args:
            limit (int): Nombre de ventes a retourner.

        Returns:
            list: Dernieres ventes avec client et montants.
        """
        return db.execute_query(
            """
            SELECT v.numero_facture,
                   CONCAT(c.nom, ' ', c.prenom) AS client,
                   v.montant_total, v.montant_paye, v.statut
            FROM ventes v
            JOIN clients c ON v.client_id = c.id
            ORDER BY v.date_vente DESC
            LIMIT %s
            """,
            (limit,),
        )

    @staticmethod
    def get_dashboard_stats() -> dict:
        """
        Retourne les statistiques globales pour le tableau de bord.

        Returns:
            dict: CA total, ventes jour/mois, panier moyen, impayes.
        """
        result = db.execute_query(
            """
            SELECT
                COALESCE(SUM(CASE WHEN statut = 'payee'
                    THEN montant_total ELSE 0 END), 0) AS ca_total,
                COUNT(CASE WHEN DATE(date_vente) = CURDATE()
                    THEN 1 END)                        AS ventes_jour,
                COUNT(CASE
                    WHEN MONTH(date_vente) = MONTH(CURDATE())
                     AND YEAR(date_vente)  = YEAR(CURDATE())
                    THEN 1 END)                        AS ventes_mois,
                COALESCE(AVG(CASE WHEN statut != 'annulee'
                    THEN montant_total END), 0)        AS panier_moyen,
                COALESCE(SUM(CASE
                    WHEN statut IN ('en_cours', 'partielle')
                    THEN montant_reste ELSE 0 END), 0) AS total_impayes
            FROM ventes
            """,
            fetch_one=True,
        )
        return result or {}

    @staticmethod
    def get_report_ventes(
        debut: str,
        fin: str,
        vendeur_id: int = None
    ) -> list:
        """
        Retourne les ventes sur une periode pour le rapport.

        Args:
            debut (str): Date de debut au format YYYY-MM-DD.
            fin (str): Date de fin au format YYYY-MM-DD.
            vendeur_id (int): Filtre par vendeur (optionnel).

        Returns:
            list: Ventes de la periode ou liste vide.
        """
        params = [debut, fin]
        v_filter = ""
        if vendeur_id:
            v_filter = "AND v.user_id = %s"
            params.append(vendeur_id)
        return db.execute_query(
            f"""
            SELECT v.numero_facture, DATE(v.date_vente) AS date_v,
                   CONCAT(c.nom, ' ', c.prenom) AS client,
                   u.username AS vendeur,
                   v.montant_total, v.montant_paye, v.statut
            FROM ventes v
            JOIN clients c ON v.client_id = c.id
            JOIN users   u ON v.user_id   = u.id
            WHERE DATE(v.date_vente) BETWEEN %s AND %s
              AND v.statut != 'annulee' {v_filter}
            ORDER BY v.date_vente DESC
            """,
            params,
        ) or []

    @staticmethod
    def get_report_impayes(
        debut: str,
        fin: str,
        vendeur_id: int = None
    ) -> list:
        """
        Retourne les impayes sur une periode pour le rapport.

        Args:
            debut (str): Date de debut au format YYYY-MM-DD.
            fin (str): Date de fin au format YYYY-MM-DD.
            vendeur_id (int): Filtre par vendeur (optionnel).

        Returns:
            list: Ventes impayees de la periode ou liste vide.
        """
        params = [debut, fin]
        v_filter = ""
        if vendeur_id:
            v_filter = "AND v.user_id = %s"
            params.append(vendeur_id)
        return db.execute_query(
            f"""
            SELECT v.numero_facture, DATE(v.date_vente) AS date_v,
                   CONCAT(c.nom, ' ', c.prenom) AS client,
                   v.montant_total, v.montant_paye, v.montant_reste
            FROM ventes v
            JOIN clients c ON v.client_id = c.id
            WHERE v.statut IN ('en_cours', 'partielle')
              AND DATE(v.date_vente) BETWEEN %s AND %s {v_filter}
            ORDER BY v.montant_reste DESC
            """,
            params,
        ) or []

    @staticmethod
    def get_report_vendeurs(debut: str, fin: str) -> list:
        """
        Retourne les statistiques par vendeur pour le rapport.

        Args:
            debut (str): Date de debut au format YYYY-MM-DD.
            fin (str): Date de fin au format YYYY-MM-DD.

        Returns:
            list: Statistiques (nb ventes, CA, paye) par vendeur.
        """
        return db.execute_query(
            """
            SELECT u.username                       AS vendeur,
                   COUNT(v.id)                      AS nb_ventes,
                   COALESCE(SUM(v.montant_total), 0) AS ca,
                   COALESCE(SUM(v.montant_paye),  0) AS paye
            FROM ventes v
            JOIN users u ON v.user_id = u.id
            WHERE DATE(v.date_vente) BETWEEN %s AND %s
              AND v.statut != 'annulee'
            GROUP BY u.id, u.username
            ORDER BY ca DESC
            """,
            [debut, fin],
        ) or []

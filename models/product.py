# models/product.py
"""Modele Produit — gestion produits, categories et stock."""

from database.connection import db


class ProductModel:

    @staticmethod
    def get_all(search: str = None, category_id: int = None) -> list:
        """Retourne tous les produits avec filtres optionnels."""
        conditions, params = [], []
        if search:
            pattern = f"%{search}%"
            conditions.append("(p.nom LIKE %s OR p.description LIKE %s)")
            params += [pattern, pattern]
        if category_id:
            conditions.append("p.category_id=%s")
            params.append(category_id)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        return db.execute_query(f"""
            SELECT p.id, p.nom, p.description,
                   p.prix_achat, p.prix_vente, p.stock_actuel, p.stock_min,
                   c.nom AS categorie, p.category_id
            FROM produits p
            LEFT JOIN categories c ON p.category_id = c.id
            {where}
            ORDER BY p.nom
        """, tuple(params) if params else None)

    @staticmethod
    def get_by_id(product_id: int) -> dict | None:
        """Retourne un produit par son ID."""
        return db.execute_query("""
            SELECT p.*, c.nom AS categorie_nom
            FROM produits p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id=%s
        """, (product_id,), fetch_one=True)

    @staticmethod
    def get_categories() -> list:
        """Retourne toutes les categories."""
        return db.execute_query("SELECT * FROM categories ORDER BY nom")

    @staticmethod
    def get_low_stock() -> list:
        """Retourne les produits en stock critique."""
        return db.execute_query("""
            SELECT p.id, p.nom, p.stock_actuel, p.stock_min,
                   c.nom AS categorie
            FROM produits p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.stock_actuel <= p.stock_min
              AND p.stock_min IS NOT NULL
              AND p.stock_min > 0
            ORDER BY p.stock_actuel ASC
        """)

    @staticmethod
    def get_movements(product_id: int) -> list:
        """Retourne l'historique des mouvements de stock d'un produit."""
        return db.execute_query("""
            SELECT ms.type_mouvement, ms.quantite, ms.motif,
                   ms.created_at,
                   u.username AS utilisateur
            FROM mouvements_stock ms
            LEFT JOIN users u ON ms.user_id = u.id
            WHERE ms.produit_id = %s
            ORDER BY ms.created_at DESC
            LIMIT 100
        """, (product_id,))

    @staticmethod
    def apply_stock_movement(product_id: int, type_mouvement: str,
                              quantite: int, motif: str,
                              user_id: int, new_stock: int) -> bool:
        """Met a jour le stock et enregistre le mouvement."""
        db.execute_update(
            "UPDATE produits SET stock_actuel=%s WHERE id=%s",
            (new_stock, product_id))
        db.execute_update("""
            INSERT INTO mouvements_stock
                (produit_id, type_mouvement, quantite, motif, user_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (product_id, type_mouvement, quantite, motif, user_id))
        return True

    @staticmethod
    def find_category_by_name(nom: str) -> dict | None:
        """Verifie si une categorie avec ce nom existe deja."""
        return db.execute_query(
            "SELECT id FROM categories WHERE nom=%s", (nom,), fetch_one=True)

    @staticmethod
    def create_category(nom: str, description: str = '') -> int:
        """Cree une nouvelle categorie. Retourne son ID."""
        return db.execute_update(
            "INSERT INTO categories (nom, description) VALUES (%s, %s)",
            (nom, description))

    @staticmethod
    def delete_category(category_id: int) -> bool:
        """
        Supprime une categorie.
        Leve ValueError si des produits l'utilisent.
        """
        count = db.execute_query(
            "SELECT COUNT(*) AS nb FROM produits WHERE category_id=%s",
            (category_id,), fetch_one=True)
        if count and count['nb'] > 0:
            raise ValueError(
                f"Impossible : {count['nb']} produit(s) utilisent cette categorie.")
        db.execute_update("DELETE FROM categories WHERE id=%s", (category_id,))
        return True

    @staticmethod
    def create(data: dict) -> int:
        """Cree un nouveau produit. Retourne son ID."""
        return db.execute_update("""
            INSERT INTO produits
                (nom, description, prix_achat, prix_vente,
                 stock_actuel, stock_min, category_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data['nom'],
            data.get('description')  or None,
            data.get('prix_achat')   or 0,
            data.get('prix_vente')   or 0,
            data.get('stock_actuel') or 0,
            data.get('stock_min')    or 0,
            data.get('category_id')  or None,
        ))

    @staticmethod
    def update(product_id: int, data: dict) -> bool:
        """Met a jour un produit existant."""
        db.execute_update("""
            UPDATE produits
            SET nom=%s, description=%s, prix_achat=%s,
                prix_vente=%s, stock_min=%s, category_id=%s
            WHERE id=%s
        """, (
            data['nom'],
            data.get('description') or None,
            data.get('prix_achat')  or 0,
            data.get('prix_vente')  or 0,
            data.get('stock_min')   or 0,
            data.get('category_id') or None,
            product_id,
        ))
        return True

    @staticmethod
    def delete(product_id: int) -> bool:
        """
        Supprime un produit.
        Leve ValueError si le produit a des ventes associees.
        """
        result = db.execute_query(
            "SELECT COUNT(*) AS total FROM ventes_details WHERE produit_id=%s",
            (product_id,), fetch_one=True)
        if result and result['total'] > 0:
            raise ValueError(
                f"Impossible : ce produit est present dans "
                f"{result['total']} vente(s).")
        db.execute_update("DELETE FROM produits WHERE id=%s", (product_id,))
        return True

    @staticmethod
    def update_stock(product_id: int, new_stock: int) -> bool:
        """Met a jour le stock d'un produit."""
        db.execute_update(
            "UPDATE produits SET stock_actuel=%s WHERE id=%s",
            (new_stock, product_id))
        return True

    @staticmethod
    def count() -> int:
        """Retourne le nombre total de produits."""
        result = db.execute_query(
            "SELECT COUNT(*) AS total FROM produits", fetch_one=True)
        return result['total'] if result else 0

    @staticmethod
    def get_dashboard_stats() -> dict:
        """Retourne les stats produits pour le dashboard."""
        from database.connection import db
        result = db.execute_query("""
            SELECT
                COUNT(*)                                    AS total_produits,
                COUNT(CASE WHEN stock_actuel <= stock_min
                    THEN 1 END)                             AS nb_alertes
            FROM produits
        """, fetch_one=True)
        return result or {}

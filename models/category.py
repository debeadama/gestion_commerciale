# models/category.py
"""Modele Categorie — gestion des categories de produits."""

from database.connection import db


class CategoryModel:

    @staticmethod
    def get_all() -> list:
        """Retourne toutes les categories avec le nombre de produits."""
        return db.execute_query("""
            SELECT c.id, c.nom, c.description,
                   (SELECT COUNT(*) FROM produits p
                    WHERE p.category_id = c.id) AS nb_produits
            FROM categories c
            ORDER BY c.nom
        """)

    @staticmethod
    def get_by_id(category_id: int) -> dict | None:
        """Retourne une categorie par son ID."""
        return db.execute_query(
            "SELECT * FROM categories WHERE id=%s",
            (category_id,), fetch_one=True)

    @staticmethod
    def create(nom: str, description: str = '') -> int:
        """Cree une nouvelle categorie. Retourne son ID."""
        return db.execute_update(
            "INSERT INTO categories (nom, description) VALUES (%s, %s)",
            (nom.strip(), description.strip()))

    @staticmethod
    def update(category_id: int, nom: str, description: str = '') -> bool:
        """Met a jour une categorie."""
        db.execute_update(
            "UPDATE categories SET nom=%s, description=%s WHERE id=%s",
            (nom.strip(), description.strip(), category_id))
        return True

    @staticmethod
    def delete(category_id: int) -> bool:
        """
        Supprime une categorie.
        Leve ValueError si des produits l'utilisent.
        """
        result = db.execute_query(
            "SELECT COUNT(*) AS nb FROM produits WHERE category_id=%s",
            (category_id,), fetch_one=True)
        if result and result['nb'] > 0:
            raise ValueError(
                f"Impossible : {result['nb']} produit(s) utilisent "
                f"cette categorie.")
        db.execute_update(
            "DELETE FROM categories WHERE id=%s", (category_id,))
        return True

    @staticmethod
    def exists(nom: str, exclude_id: int = None) -> bool:
        """Verifie si une categorie avec ce nom existe deja."""
        if exclude_id:
            result = db.execute_query(
                "SELECT id FROM categories WHERE nom=%s AND id!=%s",
                (nom, exclude_id), fetch_one=True)
        else:
            result = db.execute_query(
                "SELECT id FROM categories WHERE nom=%s",
                (nom,), fetch_one=True)
        return result is not None

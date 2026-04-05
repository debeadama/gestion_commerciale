# models/category.py
"""Modele Categorie - gestion des categories de produits."""

from database.connection import db


class CategoryModel:
    """Modele d'acces aux donnees pour les categories de produits."""

    @staticmethod
    def get_all() -> list:
        """
        Retourne toutes les categories avec le nombre de produits associes.

        Returns:
            list: Liste des categories ou None.
        """
        return db.execute_query("""
            SELECT c.id, c.nom, c.description,
                   (SELECT COUNT(*) FROM produits p
                    WHERE p.categorie_id = c.id) AS nb_produits
            FROM categories c
            ORDER BY c.nom
        """)

    @staticmethod
    def get_by_id(category_id: int) -> dict | None:
        """
        Retourne une categorie par son ID.

        Args:
            category_id (int): Identifiant de la categorie.

        Returns:
            dict: Donnees de la categorie ou None.
        """
        return db.execute_query(
            "SELECT * FROM categories WHERE id=%s",
            (category_id,),
            fetch_one=True,
        )

    @staticmethod
    def create(nom: str, description: str = '') -> int:
        """
        Cree une nouvelle categorie.

        Args:
            nom (str): Nom de la categorie.
            description (str): Description optionnelle.

        Returns:
            int: ID de la categorie creee.
        """
        return db.execute_update(
            "INSERT INTO categories (nom, description) VALUES (%s, %s)",
            (nom.strip(), description.strip()),
        )

    @staticmethod
    def update(
        category_id: int,
        nom: str,
        description: str = ''
    ) -> bool:
        """
        Met a jour une categorie existante.

        Args:
            category_id (int): Identifiant de la categorie.
            nom (str): Nouveau nom.
            description (str): Nouvelle description.

        Returns:
            bool: True si la mise a jour a reussi.
        """
        db.execute_update(
            "UPDATE categories SET nom=%s, description=%s WHERE id=%s",
            (nom.strip(), description.strip(), category_id),
        )
        return True

    @staticmethod
    def delete(category_id: int) -> bool:
        """
        Supprime une categorie.

        Args:
            category_id (int): Identifiant de la categorie.

        Returns:
            bool: True si la suppression a reussi.

        Raises:
            ValueError: Si des produits utilisent encore cette categorie.
        """
        result = db.execute_query(
            "SELECT COUNT(*) AS nb FROM produits WHERE categorie_id=%s",
            (category_id,),
            fetch_one=True,
        )
        if result and result['nb'] > 0:
            raise ValueError(
                f"Impossible : {result['nb']} produit(s) utilisent "
                f"cette categorie."
            )
        db.execute_update(
            "DELETE FROM categories WHERE id=%s",
            (category_id,),
        )
        return True

    @staticmethod
    def exists(nom: str, exclude_id: int = None) -> bool:
        """
        Verifie si une categorie avec ce nom existe deja.

        Args:
            nom (str): Nom a verifier.
            exclude_id (int): ID a exclure de la recherche (pour update).

        Returns:
            bool: True si une categorie avec ce nom existe.
        """
        if exclude_id:
            result = db.execute_query(
                "SELECT id FROM categories WHERE nom=%s AND id!=%s",
                (nom, exclude_id),
                fetch_one=True,
            )
        else:
            result = db.execute_query(
                "SELECT id FROM categories WHERE nom=%s",
                (nom,),
                fetch_one=True,
            )
        return result is not None

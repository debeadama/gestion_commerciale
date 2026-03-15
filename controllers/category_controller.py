# controllers/category_controller.py
"""
Controleur Categorie.

Logique metier pour la gestion des categories de produits.
"""

import logging

from models.category import CategoryModel
from utils.cache import app_cache

logger = logging.getLogger(__name__)

CACHE_KEY = 'categories_all'
CACHE_TTL = 600  # 10 minutes


class CategoryController:
    """Controleur pour la gestion des categories de produits."""

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    @staticmethod
    def get_all() -> list:
        """
        Retourne toutes les categories avec mise en cache (10 min).

        Returns:
            list: Liste des categories ou liste vide.
        """
        cached = app_cache.get(CACHE_KEY)
        if cached is not None:
            return cached
        result = CategoryModel.get_all() or []
        app_cache.set(CACHE_KEY, result, CACHE_TTL)
        return result

    @staticmethod
    def get_by_id(category_id: int) -> dict:
        """
        Retourne une categorie par son ID.

        Args:
            category_id (int): Identifiant de la categorie.

        Returns:
            dict: Donnees de la categorie ou None.
        """
        return CategoryModel.get_by_id(category_id)

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    @staticmethod
    def create(nom: str, description: str = '') -> tuple:
        """
        Cree une nouvelle categorie apres validation.

        Args:
            nom (str): Nom de la categorie.
            description (str): Description optionnelle.

        Returns:
            tuple: (True, category_id) ou (False, message_erreur).
        """
        nom = nom.strip()
        if not nom:
            return False, "Le nom de la categorie est obligatoire."
        if CategoryModel.exists(nom):
            return False, f"La categorie '{nom}' existe deja."
        try:
            cid = CategoryModel.create(nom, description)
            app_cache.invalidate(CACHE_KEY)
            logger.info(f"Categorie creee : {nom} (ID: {cid})")
            return True, cid
        except Exception as e:
            logger.error(f"Erreur creation categorie : {e}")
            return False, str(e)

    # ------------------------------------------------------------------
    # Modification
    # ------------------------------------------------------------------

    @staticmethod
    def update(
        category_id: int,
        nom: str,
        description: str = ''
    ) -> tuple:
        """
        Met a jour une categorie existante apres validation.

        Args:
            category_id (int): Identifiant de la categorie.
            nom (str): Nouveau nom.
            description (str): Nouvelle description.

        Returns:
            tuple: (True, message) ou (False, message_erreur).
        """
        nom = nom.strip()
        if not nom:
            return False, "Le nom de la categorie est obligatoire."
        if CategoryModel.exists(nom, exclude_id=category_id):
            return False, f"Une categorie '{nom}' existe deja."
        try:
            CategoryModel.update(category_id, nom, description)
            app_cache.invalidate(CACHE_KEY)
            return True, "Categorie mise a jour."
        except Exception as e:
            return False, str(e)

    # ------------------------------------------------------------------
    # Suppression
    # ------------------------------------------------------------------

    @staticmethod
    def delete(category_id: int) -> tuple:
        """
        Supprime une categorie.

        Args:
            category_id (int): Identifiant de la categorie.

        Returns:
            tuple: (True, message) ou (False, message_erreur).
        """
        try:
            CategoryModel.delete(category_id)
            app_cache.invalidate(CACHE_KEY)
            return True, "Categorie supprimee."
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)

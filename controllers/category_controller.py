# controllers/category_controller.py
"""
Controleur Categorie.
Logique metier pour la gestion des categories de produits.
"""

from models.category import CategoryModel
from utils.cache import app_cache
import logging

logger = logging.getLogger(__name__)

CACHE_KEY = 'categories_all'
CACHE_TTL = 600  # 10 minutes


class CategoryController:

    # ── Lecture ───────────────────────────────────────────────

    @staticmethod
    def get_all() -> list:
        """Retourne toutes les categories (avec cache 10 min)."""
        cached = app_cache.get(CACHE_KEY)
        if cached is not None:
            return cached
        result = CategoryModel.get_all() or []
        app_cache.set(CACHE_KEY, result, CACHE_TTL)
        return result

    @staticmethod
    def get_by_id(category_id: int) -> dict:
        """Retourne une categorie par son ID."""
        return CategoryModel.get_by_id(category_id)

    # ── Creation ──────────────────────────────────────────────

    @staticmethod
    def create(nom: str, description: str = '') -> tuple:
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

    # ── Modification ──────────────────────────────────────────

    @staticmethod
    def update(category_id: int, nom: str, description: str = '') -> tuple:
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

    # ── Suppression ───────────────────────────────────────────

    @staticmethod
    def delete(category_id: int) -> tuple:
        try:
            CategoryModel.delete(category_id)
            app_cache.invalidate(CACHE_KEY)
            return True, "Categorie supprimee."
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)

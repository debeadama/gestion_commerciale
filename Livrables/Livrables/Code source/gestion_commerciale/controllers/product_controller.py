# controllers/product_controller.py
"""
Controleur Produit.
Logique metier pour la gestion des produits et du stock.
"""

from models.product import ProductModel
from utils.cache import app_cache
import logging

logger = logging.getLogger(__name__)

CACHE_CATEGORIES = 'product_categories'
CACHE_LOW_STOCK  = 'product_low_stock'
CACHE_TTL        = 300  # 5 minutes


class ProductController:

    # ── Lecture ───────────────────────────────────────────────

    @staticmethod
    def get_all(search: str = None, category_id: int = None) -> list:
        """Retourne tous les produits avec filtre optionnel."""
        return ProductModel.get_all(search, category_id) or []

    @staticmethod
    def get_by_id(product_id: int) -> dict:
        """Retourne un produit par son ID."""
        return ProductModel.get_by_id(product_id)

    @staticmethod
    def get_categories() -> list:
        """Retourne toutes les categories (avec cache 5 min)."""
        cached = app_cache.get(CACHE_CATEGORIES)
        if cached is not None:
            return cached
        result = ProductModel.get_categories() or []
        app_cache.set(CACHE_CATEGORIES, result, CACHE_TTL)
        return result

    @staticmethod
    def get_low_stock() -> list:
        """Retourne les produits sous le seuil minimum (avec cache 5 min)."""
        cached = app_cache.get(CACHE_LOW_STOCK)
        if cached is not None:
            return cached
        result = ProductModel.get_low_stock() or []
        app_cache.set(CACHE_LOW_STOCK, result, CACHE_TTL)
        return result

    @staticmethod
    def get_movements(product_id: int) -> list:
        """Retourne l'historique des mouvements de stock d'un produit."""
        return ProductModel.get_movements(product_id) or []

    # ── Creation ──────────────────────────────────────────────

    @staticmethod
    def create(data: dict) -> tuple:
        nom = data.get('nom', '').strip()
        if not nom:
            return False, "Le nom du produit est obligatoire."
        try:
            prix = float(data.get('prix_vente', 0))
            if prix < 0:
                return False, "Le prix de vente ne peut pas etre negatif."
        except (ValueError, TypeError):
            return False, "Prix de vente invalide."
        try:
            pid = ProductModel.create(data)
            app_cache.invalidate(CACHE_LOW_STOCK)
            logger.info(f"Produit cree : {nom} (ID: {pid})")
            return True, pid
        except Exception as e:
            logger.error(f"Erreur creation produit : {e}")
            return False, str(e)

    @staticmethod
    def update(product_id: int, data: dict) -> tuple:
        nom = data.get('nom', '').strip()
        if not nom:
            return False, "Le nom du produit est obligatoire."
        try:
            ProductModel.update(product_id, data)
            app_cache.invalidate(CACHE_LOW_STOCK)
            return True, "Produit mis a jour."
        except Exception as e:
            return False, str(e)

    @staticmethod
    def delete(product_id: int) -> tuple:
        try:
            ProductModel.delete(product_id)
            app_cache.invalidate(CACHE_LOW_STOCK)
            return True, "Produit supprime."
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)

    # ── Mouvement de stock ────────────────────────────────────

    @staticmethod
    def add_stock_movement(product_id: int, type_mouvement: str,
                           quantite: int, motif: str = '',
                           user_id: int = None) -> tuple:
        """
        Enregistre un mouvement de stock (entree/sortie).
        Returns: (True, message) ou (False, message_erreur)
        """
        if quantite <= 0:
            return False, "La quantite doit etre superieure a 0."

        produit = ProductModel.get_by_id(product_id)
        if not produit:
            return False, "Produit introuvable."

        stock_actuel = int(produit.get('stock_actuel', 0))

        if type_mouvement == 'sortie':
            if quantite > stock_actuel:
                return False, (
                    f"Stock insuffisant. Stock actuel : {stock_actuel}, "
                    f"quantite demandee : {quantite}.")
            new_stock = stock_actuel - quantite
        else:
            new_stock = stock_actuel + quantite

        try:
            ProductModel.apply_stock_movement(
                product_id, type_mouvement, quantite, motif, user_id, new_stock)
            app_cache.invalidate(CACHE_LOW_STOCK)
            logger.info(
                f"Mouvement stock : {type_mouvement} {quantite} "
                f"pour produit {product_id}")
            return True, f"Stock mis a jour. Nouveau stock : {new_stock}"
        except Exception as e:
            return False, str(e)

    # ── Gestion categories ────────────────────────────────────

    @staticmethod
    def create_category(nom: str, description: str = '') -> tuple:
        """Cree une nouvelle categorie."""
        if not nom.strip():
            return False, "Le nom de la categorie est obligatoire."
        if ProductModel.find_category_by_name(nom):
            return False, f"La categorie '{nom}' existe deja."
        try:
            cid = ProductModel.create_category(nom.strip(), description.strip())
            return True, cid
        except Exception as e:
            return False, str(e)

    @staticmethod
    def delete_category(category_id: int) -> tuple:
        """Supprime une categorie si aucun produit ne l'utilise."""
        try:
            ProductModel.delete_category(category_id)
            return True, "Categorie supprimee."
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_dashboard_stats() -> dict:
        """Stats produits pour le dashboard."""
        return ProductModel.get_dashboard_stats()

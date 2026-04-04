# utils/cache.py
"""
Cache memoire simple pour les donnees statiques.
Evite de recharger categories et parametres a chaque appel.
"""
import logging
import time

logger = logging.getLogger(__name__)


class SimpleCache:
    """Cache cle-valeur avec expiration par entree."""

    def __init__(self, default_ttl: int = 300):
        """
        default_ttl : duree de vie en secondes (defaut 5 minutes)
        """
        self._store = {}          # {cle: (valeur, timestamp_expiration)}
        self.default_ttl = default_ttl

    def get(self, key: str):
        """Retourne la valeur si presente et non expiree, sinon None."""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value, ttl: int = None):
        """Stocke une valeur avec une duree de vie."""
        ttl = ttl if ttl is not None else self.default_ttl
        self._store[key] = (value, time.time() + ttl)

    def invalidate(self, key: str):
        """Supprime une entree du cache."""
        self._store.pop(key, None)

    def invalidate_prefix(self, prefix: str):
        """Supprime toutes les entrees dont la cle commence par prefix."""
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]

    def clear(self):
        """Vide tout le cache."""
        self._store.clear()

    def stats(self) -> dict:
        """Retourne des statistiques sur le cache."""
        now = time.time()
        actives = sum(1 for _, (_, exp) in self._store.items() if exp > now)
        expires = sum(1 for _, (_, exp) in self._store.items() if exp <= now)
        return {'total': len(self._store),
                'actives': actives, 'expires': expires}


# Instance globale partagee par toute l'application
app_cache = SimpleCache(default_ttl=300)  # 5 minutes par defaut

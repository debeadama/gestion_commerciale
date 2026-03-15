# database/connection.py
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class Database:
    """
    Gestionnaire de connexion MySQL avec pool simple (queue de connexions).
    Compatible monoposte et multi-utilisateurs.
    """

    def __init__(self):
        self.config = {
            'host':     os.getenv('DB_HOST',     'localhost'),
            'port':     int(os.getenv('DB_PORT', 3306)),
            'user':     os.getenv('DB_USER',     'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME',     'gestion_commerciale'),
            'charset':  'utf8mb4',
        }
        self._pool = []          # connexions disponibles
        self._pool_size = 5      # taille maximale du pool
        self._connection = None  # connexion principale (compat. ancienne API)

    # ----------------------------------------------------------
    # Connexion principale (compatibilite ascendante)
    # ----------------------------------------------------------

    def connect(self) -> bool:
        """Etablit la connexion principale. Retourne True si succes."""
        try:
            import pymysql
            self._connection = pymysql.connect(
                **self.config,
                autocommit=True,
                connect_timeout=10,
            )
            logger.info("✅ Connexion MySQL établie")
            return True
        except Exception as e:
            logger.error(f"❌ Connexion MySQL échouée : {e}")
            return False

    def disconnect(self):
        """Ferme toutes les connexions."""
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
            self._connection = None
        for conn in self._pool:
            try:
                conn.close()
            except Exception:
                pass
        self._pool.clear()

    # ----------------------------------------------------------
    # Pool de connexions
    # ----------------------------------------------------------

    def _get_connection(self):
        """
        Retourne une connexion disponible depuis le pool,
        ou cree une nouvelle si le pool est vide.
        """
        import pymysql

        # Essayer de recycler une connexion du pool
        while self._pool:
            conn = self._pool.pop()
            try:
                conn.ping(reconnect=True)
                return conn
            except Exception:
                pass  # connexion morte, on en prend une nouvelle

        # Creer une nouvelle connexion
        return pymysql.connect(
            **self.config,
            autocommit=True,
            connect_timeout=10,
        )

    def _release_connection(self, conn):
        """Remet une connexion dans le pool si celui-ci n'est pas plein."""
        if len(self._pool) < self._pool_size:
            try:
                conn.ping(reconnect=False)
                self._pool.append(conn)
                return
            except Exception:
                pass
        try:
            conn.close()
        except Exception:
            pass

    # ----------------------------------------------------------
    # Execute query (SELECT)
    # ----------------------------------------------------------

    def execute_query(self, query: str, params=None,
                      fetch_one: bool = False):
        """
        Execute une requete SELECT.
        Utilise le pool de connexions si la connexion principale est indisponible.
        """
        conn = None
        try:
            # Preference : connexion principale (compatibilite)
            if self._connection:
                try:
                    self._connection.ping(reconnect=True)
                    conn = self._connection
                    use_pool = False
                except Exception:
                    conn = None

            if conn is None:
                conn = self._get_connection()
                use_pool = True
            else:
                use_pool = False

            with conn.cursor(self._dict_cursor()) as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone() if fetch_one else cursor.fetchall()
                return result

        except Exception as e:
            logger.error(f"❌ Erreur SELECT : {e}")
            raise
        finally:
            if use_pool and conn and conn is not self._connection:
                self._release_connection(conn)

    # ----------------------------------------------------------
    # Execute update (INSERT / UPDATE / DELETE)
    # ----------------------------------------------------------

    def execute_update(self, query: str, params=None):
        """
        Execute une requete INSERT/UPDATE/DELETE.
        Retourne lastrowid pour les INSERT.
        """
        conn = None
        use_pool = False
        try:
            if self._connection:
                try:
                    self._connection.ping(reconnect=True)
                    conn = self._connection
                    use_pool = False
                except Exception:
                    conn = None

            if conn is None:
                conn = self._get_connection()
                use_pool = True

            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if not conn.autocommit_mode:
                    conn.commit()
                return cursor.lastrowid

        except Exception as e:
            logger.error(f"❌ Erreur UPDATE : {e}")
            if conn and not conn.autocommit_mode:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise
        finally:
            if use_pool and conn and conn is not self._connection:
                self._release_connection(conn)

    def _dict_cursor(self):
        """Retourne le type de curseur dict pymysql."""
        import pymysql.cursors
        return pymysql.cursors.DictCursor


# Instance globale
db = Database()

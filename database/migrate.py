# database/migrate.py
"""
Systeme de migration de schema SGC.

Principe :
  - Une table 'schema_versions' trace les migrations deja appliquees.
  - Les fichiers SQL dans database/migrations/ sont numerotes (001_, 002_, ...).
  - Seules les migrations non encore appliquees sont executees, dans l'ordre.

Usage :
    python -m database.migrate
    ou depuis le code :
        from database.migrate import run_migrations
        run_migrations()
"""

import logging
import os
import re

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def _ensure_versions_table(db) -> None:
    """Cree la table schema_versions si elle n'existe pas."""
    db.execute_update("""
        CREATE TABLE IF NOT EXISTS schema_versions (
            version     VARCHAR(10)  NOT NULL PRIMARY KEY,
            description VARCHAR(255) NULL,
            applied_at  DATETIME     DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)


def _applied_versions(db) -> set:
    """Retourne l'ensemble des versions deja appliquees."""
    rows = db.execute_query("SELECT version FROM schema_versions")
    return {r['version'] for r in rows} if rows else set()


def _migration_files() -> list[tuple[str, str]]:
    """
    Retourne les fichiers de migration tries par numero.
    Chaque entree : (version, chemin_complet).
    """
    if not os.path.isdir(MIGRATIONS_DIR):
        return []
    files = []
    for fname in sorted(os.listdir(MIGRATIONS_DIR)):
        if not fname.endswith(".sql"):
            continue
        match = re.match(r'^(\d+)_', fname)
        if not match:
            continue
        version = match.group(1).zfill(3)
        files.append((version, os.path.join(MIGRATIONS_DIR, fname)))
    return files


def run_migrations(db=None) -> int:
    """
    Execute toutes les migrations non encore appliquees.

    Args:
        db: Instance Database (utilise l'instance globale si None).

    Returns:
        int: Nombre de migrations appliquees.
    """
    if db is None:
        from database.connection import db as _db
        db = _db

    _ensure_versions_table(db)
    applied = _applied_versions(db)
    migrations = _migration_files()
    count = 0

    for version, filepath in migrations:
        if version in applied:
            continue

        fname = os.path.basename(filepath)
        logger.info(f"Application migration {version} : {fname}")

        try:
            with open(filepath, encoding="utf-8") as f:
                sql = f.read()

            # Executer chaque instruction separement (ignore les vides)
            for statement in sql.split(";"):
                stmt = statement.strip()
                if stmt and not stmt.startswith("--"):
                    try:
                        db.execute_update(stmt)
                    except Exception as e:
                        # Certaines instructions peuvent echouer si deja appliquees
                        logger.debug(
                            f"Instruction ignoree ({fname}) : {e}"
                        )

            # Enregistrer la version comme appliquee
            description = fname.replace(".sql", "").replace("_", " ", 1)
            db.execute_update(
                "INSERT IGNORE INTO schema_versions (version, description) "
                "VALUES (%s, %s)",
                (version, description),
            )
            count += 1
            logger.info(f"Migration {version} appliquee.")

        except Exception as e:
            logger.error(f"Echec migration {version} : {e}")
            raise

    if count == 0:
        logger.info("Base de donnees a jour - aucune migration a appliquer.")
    else:
        logger.info(f"{count} migration(s) appliquee(s).")

    return count


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    run_migrations()

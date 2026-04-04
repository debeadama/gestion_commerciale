# database/test_connexion.py
from database.connection import db


def test_connexion():
    """Vérifie que la connexion MySQL fonctionne."""
    print("\nTest de connexion à MySQL...")

    assert db.connect(), "Connexion MySQL échouée"
    print("Connexion réussie !")

    tables = db.execute_query("SHOW TABLES")
    assert tables, "Aucune table trouvée"
    print(f"Tables trouvées : {tables}")

    db.disconnect()   # ← nom correct
    print("Déconnexion réussie !")
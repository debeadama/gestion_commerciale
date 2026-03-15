# test_connexion.py — À supprimer après le test
from database.connection import db

print("Test de connexion à MySQL...")

if db.connect():
    print("✅ Connexion réussie !")
    
    # Test simple : liste les tables
    result = db.execute_query("SHOW TABLES")
    print(f"Tables trouvées : {result}")
    
    db.close()
else:
    print("❌ Connexion échouée. Vérifiez votre .env et que MySQL est démarré.")
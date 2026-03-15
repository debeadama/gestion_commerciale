# create_admin.py
# Script à exécuter UNE SEULE FOIS pour créer l'administrateur
# À supprimer ou sécuriser après utilisation

import bcrypt
from database.connection import db

def create_admin():
    """Crée le compte administrateur initial."""
    
    # ---- Paramètres du compte admin ----
    username = "admin"
    password = "uvci@2026"  
    email    = "admin@seyo.com"
    role     = "admin"
    # ------------------------------------

    print("Connexion à la base de données...")
    if not db.connect():
        print("❌ Impossible de se connecter à MySQL.")
        return

    # Vérifier si l'admin existe déjà
    existing = db.execute_query(
        "SELECT id FROM users WHERE username = %s",
        (username,),
        fetch_one=True
    )

    if existing:
        print(f"⚠️  L'utilisateur '{username}' existe déjà (ID: {existing['id']}).")
        db.close()
        return

    # Hacher le mot de passe avec bcrypt (12 rounds = bon équilibre sécurité/vitesse)
    print("Hachage du mot de passe...")
    salt        = bcrypt.gensalt(rounds=12)
    hashed_pw   = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    # Insérer l'admin en base
    user_id = db.execute_update(
        """
        INSERT INTO users (username, password_hash, role, email, is_active)
        VALUES (%s, %s, %s, %s, TRUE)
        """,
        (username, hashed_pw, role, email)
    )

    print("─" * 40)
    print("✅ Compte administrateur créé avec succès !")
    print(f"   ID       : {user_id}")
    print(f"   Username : {username}")
    print(f"   Mot passe: {password}")
    print(f"   Rôle     : {role}")
    print("─" * 40)
    print("⚠️  Pense à changer le mot de passe après ta première connexion !")

    db.close()


if __name__ == "__main__":
    create_admin()
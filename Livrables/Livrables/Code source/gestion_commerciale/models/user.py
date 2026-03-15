# models/user.py
"""Modele Utilisateur — CRUD complet pour la gestion des utilisateurs."""

from database.connection import db
import bcrypt


class UserModel:

    @staticmethod
    def get_all() -> list:
        """Retourne tous les utilisateurs (sans mot de passe)."""
        return db.execute_query("""
            SELECT id, username,
                   COALESCE(nom_complet, '') AS nom_complet,
                   COALESCE(email, '')       AS email,
                   role, created_at
            FROM users
            ORDER BY username
        """)

    @staticmethod
    def get_by_id(user_id: int) -> dict | None:
        """Retourne un utilisateur par son ID (sans mot de passe)."""
        return db.execute_query(
            "SELECT id, username, COALESCE(nom_complet,'') AS nom_complet, "
            "COALESCE(email,'') AS email, role FROM users WHERE id=%s",
            (user_id,), fetch_one=True)

    @staticmethod
    def get_by_username(username: str) -> dict | None:
        """Retourne un utilisateur avec son hash (pour authentification)."""
        return db.execute_query(
            "SELECT * FROM users WHERE username=%s",
            (username,), fetch_one=True)

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verifie si le mot de passe correspond au hash stocke."""
        try:
            return bcrypt.checkpw(password.encode(), password_hash.encode())
        except Exception:
            return False

    @staticmethod
    def find_by_username(username: str, exclude_id: int = None) -> dict | None:
        """Verifie si un username existe deja (pour doublon)."""
        if exclude_id:
            return db.execute_query(
                "SELECT id FROM users WHERE username=%s AND id!=%s",
                (username, exclude_id), fetch_one=True)
        return db.execute_query(
            "SELECT id FROM users WHERE username=%s",
            (username,), fetch_one=True)

    @staticmethod
    def create(username: str, password_hash: str, role: str,
               nom_complet: str = '', email: str = '') -> int:
        """Cree un nouvel utilisateur. Retourne son ID."""
        return db.execute_update(
            "INSERT INTO users (username, password_hash, nom_complet, email, role) "
            "VALUES (%s, %s, %s, %s, %s)",
            (username, password_hash, nom_complet, email, role))

    @staticmethod
    def update(user_id: int, username: str, role: str,
               nom_complet: str = '', email: str = '') -> bool:
        """Met a jour les infos d'un utilisateur."""
        db.execute_update(
            "UPDATE users SET username=%s, nom_complet=%s, email=%s, role=%s "
            "WHERE id=%s",
            (username, nom_complet, email, role, user_id))
        return True

    @staticmethod
    def change_password(user_id: int, password_hash: str) -> bool:
        """Met a jour le mot de passe d'un utilisateur."""
        db.execute_update(
            "UPDATE users SET password_hash=%s WHERE id=%s",
            (password_hash, user_id))
        return True

    @staticmethod
    def delete(user_id: int) -> bool:
        """Supprime un utilisateur."""
        db.execute_update("DELETE FROM users WHERE id=%s", (user_id,))
        return True

    @staticmethod
    def get_stats(user_id: int) -> dict:
        """Retourne les statistiques de ventes d'un vendeur."""
        result = db.execute_query("""
            SELECT
                COUNT(*)                        AS nb_ventes,
                COALESCE(SUM(montant_total), 0) AS ca_total,
                COALESCE(SUM(montant_paye),  0) AS total_paye,
                MAX(date_vente)                 AS derniere_vente
            FROM ventes
            WHERE user_id = %s AND statut != 'annulee'
        """, (user_id,), fetch_one=True)
        return result or {}

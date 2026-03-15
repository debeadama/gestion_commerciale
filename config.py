# config.py
"""
Configuration de l'application SGC.

Charge les parametres depuis le fichier .env.
Les mots de passe ne sont jamais ecrits directement dans le code.
"""

import os

from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# ------------------------------------------------------------------
# Configuration Base de Donnees
# ------------------------------------------------------------------
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME', 'gestion_commerciale'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'charset': 'utf8mb4',
}

# ------------------------------------------------------------------
# Configuration Application
# ------------------------------------------------------------------
APP_NAME = os.getenv('APP_NAME', 'SGC')
APP_VERSION = os.getenv('APP_VERSION', '1.0')
SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 1800))  # secondes

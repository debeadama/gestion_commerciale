# config.py
# Charge la configuration depuis le fichier .env
# JAMAIS de mots de passe écrits directement dans le code !

from dotenv import load_dotenv
import os

# Chargement des variables d'environnement
load_dotenv()

# --- Configuration Base de Données ---
DB_CONFIG = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'port':     int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME', 'gestion_commerciale'),
    'user':     os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'charset':  'utf8mb4',
}

# --- Configuration Application ---
APP_NAME       = os.getenv('APP_NAME', 'SGC')
APP_VERSION    = os.getenv('APP_VERSION', '1.0')
SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 1800))  # en secondes
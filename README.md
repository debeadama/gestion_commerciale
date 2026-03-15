# SGC — Système de Gestion Commerciale

Application de gestion commerciale développée avec Python 3.14 / PyQt6 / MySQL.

---

## Prérequis

- Windows 10/11 64 bits
- MySQL Server 5.7 ou 8.0
- Python 3.14 (pour le développement uniquement)

---

## Installation sur une nouvelle machine

### 1. Installer MySQL Server

Téléchargez et installez MySQL depuis : https://dev.mysql.com/downloads/installer/

Notez le mot de passe `root` créé pendant l'installation.

### 2. Lancer l'installateur

Exécutez `mysetup.exe` en tant qu'administrateur et suivez les étapes.

A la fin de l'installation, cochez **"Installer la base de données MySQL"** puis cliquez sur **Terminer**.

Une fenêtre s'ouvre et demande :

```
Entrez le mot de passe MySQL root :
```

Saisissez votre mot de passe. Le script crée automatiquement la base de données, importe les tables et génère le fichier `.env` dans le dossier d'installation.

### 3. Lancer l'application

Double-cliquez sur le raccourci **SGC** créé sur le Bureau.

---

## Configuration manuelle du fichier .env

Le fichier `.env` est généré automatiquement lors de l'installation. Si nécessaire, vous pouvez le modifier manuellement dans :

```
C:\Program Files\SGC\.env
```

Contenu du fichier :

```
DB_HOST=localhost
DB_PORT=3306
DB_NAME=gestion_commerciale
DB_USER=root
DB_PASSWORD=votre_mot_de_passe
```

---

## Structure du projet

```
gestion_commerciale/
├── controllers/        # Logique métier (auth, clients, produits, ventes)
├── models/             # Accès base de données
├── views/              # Interfaces graphiques PyQt6
├── database/           # Scripts SQL (schema, seed_data, add_indexes)
├── utils/              # Utilitaires (PDF, cache, pagination)
├── tests/              # Tests unitaires (313 tests, couverture 99%)
├── main.py             # Point d'entrée
├── install_db.bat      # Script d'installation de la base de données
└── .env                # Configuration de connexion (non versionné)
```

---

## Lancer les tests

```bash
python -m pytest tests/ --cov=controllers --cov=models --cov-report=term-missing
```

Résultats actuels : **313 tests passés — couverture 99%**

---

## Technologies utilisées

- Python 3.14
- PyQt6 — interfaces graphiques
- MySQL 8.0 — base de données
- bcrypt — hachage des mots de passe
- ReportLab — génération de PDF
- PyInstaller — création de l'exécutable
- InnoSetup — création de l'installateur Windows

---

## Déploiement

L'exécutable et l'installateur sont générés avec :

```bash
# Créer l'exécutable
pyinstaller main.spec

# Créer l'installateur (via InnoSetup)
# Compiler le fichier setup_SGC.iss
```

L'installateur final se trouve dans : `C:\gestion_commerciale\mysetup.exe`

---

Version 1.0 — Février 2026
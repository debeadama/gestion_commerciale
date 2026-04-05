# CLAUDE.md — SGC (Système de Gestion Commerciale)

## Présentation du projet

Application de gestion commerciale desktop (PyQt6 + MySQL) développée par **SORO Débé Adama**.
Architecture MVC, distribuée via un installeur Windows (Inno Setup).

---

## Stack technique

| Composant | Technologie |
|---|---|
| Interface | PyQt6 6.6.1 (fichiers `.ui` chargés via `uic.loadUi`) |
| Base de données | MySQL 8 via PyMYSQL |
| Authentification | bcrypt 4.1.2 |
| Configuration | python-dotenv (.env) |
| PDF | ReportLab 4.0.9 |
| Export Excel | openpyxl 3.1.2 |
| Graphiques | matplotlib 3.8.2 |
| Packaging | PyInstaller 6.3.0 + Inno Setup 6 |

---

## Structure

```
controllers/     # Logique métier (auth, client, produit, vente, catégorie, utilisateur)
models/          # Accès base de données (CRUD)
views/           # Interfaces PyQt6
  ui/            # Fichiers .ui (Qt Designer)
assets/          # Logos et icônes
database/        # schema.sql, seed_data.sql, add_indexes.sql, migrate.py
utils/           # cache, pagination, pdf_generator, logo, styles
tests/           # Tests unitaires (unittest + mock)
config.py        # Variables d'environnement
main.py          # Point d'entrée
SGC.iss          # Script installeur Inno Setup
main.spec        # Spec PyInstaller
```

---

## Commandes essentielles

```bash
# Lancer l'application
python main.py

# Tests
python -m pytest tests/ -v
python -m pytest tests/ --tb=short -q

# Couverture
python -m coverage run -m pytest tests/
python -m coverage report

# Générer l'exécutable
python -m PyInstaller main.spec --noconfirm

# Générer l'installeur (nécessite Inno Setup 6)
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" SGC.iss
```

---

## Configuration (.env)

En développement : `.env` à la racine du projet.
En mode installé (frozen) : `%APPDATA%\SGC\.env` — créé automatiquement au premier lancement.

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=gestion_commerciale
DB_USER=root
DB_PASSWORD=
APP_NAME=Système de Gestion Commerciale
APP_VERSION=1.0.0
SESSION_TIMEOUT=300
```

---

## Base de données

Installation complète (ordre obligatoire) :
```bash
mysql -u root -p < database/schema.sql        # Crée la BDD + tables + vues
mysql -u root -p gestion_commerciale < database/add_indexes.sql
mysql -u root -p gestion_commerciale < database/seed_data.sql
```

> `schema.sql` gère lui-même `CREATE DATABASE` et `USE` — ne pas spécifier la base en argument pour ce fichier.

---

## Conventions de code

- Pas de tirets longs (`—`) dans le code — utiliser `-`
- Méthodes statiques `@staticmethod` dans les controllers et models
- Cache applicatif via `utils/cache.py` (`app_cache`) avec clés nommées `CACHE_*`
- Chaque invalidation de cache appelle `invalidate` **deux fois** : `product_low_stock` + `product_all`
- Vues PyQt6 : styles appliqués dans `_apply_styles()`, polices dans `_apply_fonts()`
- `_apply_fonts()` appelé dans `showEvent` (pas dans `__init__`) pour garantir les dimensions correctes des widgets

---

## Fichiers à ne pas modifier sans raison

- `database/schema.sql` — structure de référence de la BDD
- `main.spec` — configuration PyInstaller
- `SGC.iss` — script installeur

---

## Chemins importants (mode installé)

| Ressource | Chemin |
|---|---|
| Exécutable | `C:\Program Files\SGC\SGC.exe` |
| Configuration `.env` | `%APPDATA%\SGC\.env` |
| Logs | `%APPDATA%\SGC\logs\sgc.log` |
| Installeur généré | `C:\gestion_commerciale\SGC_setup.exe` |

---

## Tests

328 tests unitaires — 0 échec attendu.
Les tests des controllers mockent `app_cache` et `ProductModel`.
Les vues (PyQt6) ne sont pas testées unitairement (0% coverage intentionnel).

```bash
# Vérification rapide avant chaque commit
python -m pytest tests/ --tb=no -q
```

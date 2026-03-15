<<<<<<< HEAD
# Gestion Commerciale - Guide d'utilisation

## 📋 Prérequis

Avant de lancer l'application, assurez-vous que :

1. **MySQL 8.0+** est installé et en cours d'exécution
2. La base de données `gestion_commerciale` a été créée

---

## 🚀 Installation de la base de données

### Étape 1 : Créer la base de données

Ouvrez MySQL et exécutez :

```sql
CREATE DATABASE gestion_commerciale CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Étape 2 : Importer le schéma

Le fichier `schema.sql` contient toutes les tables nécessaires. Importez-le dans MySQL.

---

## ⚙️ Configuration

1. Ouvrez le fichier `.env` dans le dossier d'installation
2. Modifiez les paramètres de connexion MySQL :
   ```
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=gestion_commerciale
   DB_USER=root
   DB_PASSWORD=votre_mot_de_passe
   ```
3. Personnalisez les informations de votre entreprise

---

## 🔐 Premier utilisateur

Après avoir créé la base de données, insérez un utilisateur administrateur :

```sql
INSERT INTO users (username, password_hash, role, email, is_active)
VALUES ('admin', 'hash_bcrypt_du_mot_de_passe', 'admin', 'admin@entreprise.com', TRUE);
```

**Mot de passe par défaut :** `admin123` (à changer immédiatement)

---

## 📞 Support

Pour toute question : contact@entreprise.com

---

**Version :** 1.0.0  
**Date :** Février 2025
=======
# gestion_commerciale
Système de Gestion Commerciale - PyQt6 + MySQL
>>>>>>> c593561443ef53cb66fb2c8aa31ced1e4118131b

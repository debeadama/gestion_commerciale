-- ============================================================
-- schema.sql — Creation des tables de la base de donnees
-- Systeme de Gestion Commerciale (E-GestComPro) — PyQt6 + MySQL
-- ============================================================

CREATE DATABASE IF NOT EXISTS gestion_commerciale
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE gestion_commerciale;

SET FOREIGN_KEY_CHECKS = 0;

-- ── Table users ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nom_complet   VARCHAR(100) NULL,
    email         VARCHAR(150) NULL DEFAULT NULL,
    role          ENUM('admin','manager','vendeur') NOT NULL DEFAULT 'vendeur',
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username  (username),
    INDEX idx_role      (role),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Table categories ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categories (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nom         VARCHAR(100) NOT NULL UNIQUE,
    description TEXT         NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_nom (nom)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Table clients ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS clients (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nom         VARCHAR(100) NOT NULL,
    prenom      VARCHAR(100) NOT NULL,
    telephone   VARCHAR(20)  NULL,
    email       VARCHAR(150) NULL,
    adresse     TEXT         NULL,
    ville       VARCHAR(100) NULL,
    code_postal VARCHAR(10)  NULL,
    notes       TEXT         NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_nom       (nom),
    INDEX idx_telephone (telephone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Table produits ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS produits (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    reference    VARCHAR(50)    NULL UNIQUE,
    nom          VARCHAR(150)   NOT NULL,
    description  TEXT           NULL,
    prix_achat   DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    prix_vente   DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    stock_actuel INT            NOT NULL DEFAULT 0,
    stock_min    INT            NULL DEFAULT 5,
    unite        VARCHAR(20)    NOT NULL DEFAULT 'unité',
    category_id  INT            NULL,
    actif        BOOLEAN        NOT NULL DEFAULT TRUE,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id)
        REFERENCES categories(id) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_nom       (nom),
    INDEX idx_reference (reference),
    INDEX idx_stock     (stock_actuel),
    INDEX idx_category  (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Table ventes ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ventes (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    numero_facture VARCHAR(30)    NOT NULL UNIQUE,
    client_id      INT            NOT NULL,
    user_id        INT            NULL,
    date_vente     DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    montant_total  DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    montant_paye   DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    montant_reste  DECIMAL(12, 2) GENERATED ALWAYS AS (montant_total - montant_paye) STORED,
    statut         ENUM('en_cours','payee','partielle','annulee') NOT NULL DEFAULT 'en_cours',
    notes          TEXT           NULL,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id)
        REFERENCES clients(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (user_id)
        REFERENCES users(id)   ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_client       (client_id),
    INDEX idx_user         (user_id),
    INDEX idx_statut       (statut),
    INDEX idx_date_vente   (date_vente),
    INDEX idx_num_facture  (numero_facture)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Table ventes_details ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS ventes_details (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    vente_id      INT            NOT NULL,
    produit_id    INT            NOT NULL,
    quantite      INT            NOT NULL,
    prix_unitaire DECIMAL(12, 2) NOT NULL,
    sous_total    DECIMAL(12, 2) GENERATED ALWAYS AS (quantite * prix_unitaire) STORED,
    FOREIGN KEY (vente_id)
        REFERENCES ventes(id)   ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (produit_id)
        REFERENCES produits(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_vente   (vente_id),
    INDEX idx_produit (produit_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Table mouvements_stock ────────────────────────────────────
CREATE TABLE IF NOT EXISTS mouvements_stock (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    produit_id     INT          NOT NULL,
    type_mouvement ENUM('entree','sortie','ajustement') NOT NULL,
    quantite       INT          NOT NULL,
    stock_avant    INT          NOT NULL DEFAULT 0,
    stock_apres    INT          NOT NULL DEFAULT 0,
    motif          VARCHAR(255) NULL,
    user_id        INT          NULL,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (produit_id)
        REFERENCES produits(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (user_id)
        REFERENCES users(id)    ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_produit    (produit_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Table parametres ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS parametres (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    cle        VARCHAR(100) NOT NULL UNIQUE,
    valeur     TEXT         NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_cle (cle)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Table logs ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS logs (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT          NULL,
    action     VARCHAR(100) NOT NULL,
    details    TEXT         NULL,
    ip_address VARCHAR(45)  NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_created_at (created_at),
    INDEX idx_action     (action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Vue : ventes enrichies ────────────────────────────────────
CREATE OR REPLACE VIEW vue_ventes AS
SELECT
    v.id, v.numero_facture, v.date_vente,
    v.montant_total, v.montant_paye, v.montant_reste, v.statut,
    CONCAT(c.nom, ' ', c.prenom) AS client,
    c.telephone AS client_telephone,
    u.username AS vendeur
FROM ventes v
JOIN clients c ON v.client_id = c.id
LEFT JOIN users u ON v.user_id = u.id;

-- ── Vue : stock critique ──────────────────────────────────────
CREATE OR REPLACE VIEW vue_stock_critique AS
SELECT
    p.id, p.reference, p.nom, p.stock_actuel, p.stock_min,
    p.stock_min - p.stock_actuel AS manque,
    c.nom AS categorie
FROM produits p
LEFT JOIN categories c ON p.category_id = c.id
WHERE p.stock_actuel <= p.stock_min
  AND p.stock_min IS NOT NULL
  AND p.stock_min > 0
ORDER BY p.stock_actuel ASC;

SET FOREIGN_KEY_CHECKS = 1;
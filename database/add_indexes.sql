-- add_indexes.sql
-- Script d'optimisation des index MySQL
-- Compatible MySQL 5.7 et 8.0
-- Lancer : mysql -u root -p gestion_commerciale < add_indexes.sql
DELIMITER $$
DROP PROCEDURE IF EXISTS add_index_if_not_exists$$
CREATE PROCEDURE add_index_if_not_exists(
    IN tbl  VARCHAR(64),
    IN idx  VARCHAR(64),
    IN cols VARCHAR(255)
)
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = tbl
          AND INDEX_NAME   = idx
    ) THEN
        SET @sql = CONCAT('ALTER TABLE `', tbl, '` ADD INDEX `', idx, '` (', cols, ')');
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        SELECT CONCAT('OK Index cree : ', tbl, '.', idx) AS resultat;
    ELSE
        SELECT CONCAT('-- Index existe deja : ', tbl, '.', idx) AS resultat;
    END IF;
END$$
DELIMITER ;
-- Clients
CALL add_index_if_not_exists('clients', 'idx_clients_nom',       '`nom`');
CALL add_index_if_not_exists('clients', 'idx_clients_telephone', '`telephone`');
CALL add_index_if_not_exists('clients', 'idx_clients_email',     '`email`');
-- Produits
CALL add_index_if_not_exists('produits', 'idx_produits_nom',          '`nom`');
CALL add_index_if_not_exists('produits', 'idx_produits_categorie_id', '`categorie_id`');
CALL add_index_if_not_exists('produits', 'idx_produits_stock',        '`stock_actuel`, `stock_min`');
-- Ventes
CALL add_index_if_not_exists('ventes', 'idx_ventes_date_vente', '`date_vente`');
CALL add_index_if_not_exists('ventes', 'idx_ventes_statut',     '`statut`');
CALL add_index_if_not_exists('ventes', 'idx_ventes_client_id',  '`client_id`');
CALL add_index_if_not_exists('ventes', 'idx_ventes_user_id',    '`user_id`');
-- Ventes details
CALL add_index_if_not_exists('ventes_details', 'idx_vd_vente_id',   '`vente_id`');
CALL add_index_if_not_exists('ventes_details', 'idx_vd_produit_id', '`produit_id`');
-- Logs
CALL add_index_if_not_exists('logs', 'idx_logs_created_at', '`created_at`');
CALL add_index_if_not_exists('logs', 'idx_logs_user_id',    '`user_id`');
-- Nettoyage
DROP PROCEDURE IF EXISTS add_index_if_not_exists;
-- Verification finale
SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
  AND INDEX_NAME LIKE 'idx_%'
ORDER BY TABLE_NAME, INDEX_NAME;
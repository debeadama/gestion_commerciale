-- Migration 002 : Ajout d'index de performance supplementaires
-- Ameliore les requetes de recherche sur les ventes et les produits.

ALTER TABLE ventes
    ADD INDEX IF NOT EXISTS idx_date_statut (date_vente, statut);

ALTER TABLE produits
    ADD INDEX IF NOT EXISTS idx_prix_vente (prix_vente);

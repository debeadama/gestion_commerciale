-- Migration 001 : Schema initial SGC
-- Applique le schema de base (tables principales + vues)
-- Ce fichier documente l'etat initial de la base.
-- Les nouvelles modifications passent par des migrations numerotees suivantes.

-- Marqueur : cette migration est consideree appliquee si la table 'users' existe.
SELECT 1 FROM users LIMIT 1;

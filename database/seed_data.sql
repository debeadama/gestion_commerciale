-- ============================================================
-- GESTION COMMERCIALE - Scripts SQL -DONNEES TEST
-- ============================================================

-- ── Utilisateurs (mots de passe hachés bcrypt = "uvci@2026") ─
-- Hash bcrypt généré pour "uvci@2026" avec coût 12
INSERT INTO users (username, password_hash, nom_complet, email, role) VALUES
('admin',   '$2b$12$0/RxCAYW8EPuxIlfL.9oMepz32jukQCoQrVg9pP.nHkgbtNYbfKZe', 'Administrateur Système',  'admin@gestion.ci',   'admin'),
('manager', '$2b$12$0/RxCAYW8EPuxIlfL.9oMepz32jukQCoQrVg9pP.nHkgbtNYbfKZe', 'Koné Mamadou',            'manager@gestion.ci', 'manager'),
('vendeur1','$2b$12$0/RxCAYW8EPuxIlfL.9oMepz32jukQCoQrVg9pP.nHkgbtNYbfKZe', 'Diallo Aminata',          'vendeur1@gestion.ci','vendeur'),
('vendeur2','$2b$12$0/RxCAYW8EPuxIlfL.9oMepz32jukQCoQrVg9pP.nHkgbtNYbfKZe', 'Touré Ibrahim',           'vendeur2@gestion.ci','vendeur');

-- ── Paramètres de l'application ───────────────────────────────
INSERT INTO parametres (cle, valeur) VALUES
('nom_entreprise',    'SEYO BOUTIQUE'),
('adresse',           'Yopougon, Rue S159, Abidjan'),
('telephone',         '+225 01 40 44 16 99'),
('email',             'info@seyo.ci'),
('site_web',          'www.seyoboutique.com'),
('registre_commerce', 'RC/ABJ/2024/B/00001'),
('nif',               'CI-2024-00001-A'),
('devise',            'FCFA'),
('tva',               '18'),
('format_facture',    'A4'),
('nb_decimales',      '2');

-- ── Catégories ────────────────────────────────────────────────
INSERT INTO categories (nom, description) VALUES
('Informatique',    'Ordinateurs, accessoires et periphériques'),
('Telephonie',      'Telephones mobiles et accessoires'),
('Fournitures',     'Fournitures de bureau et papeterie'),
('Mobilier',        'Mobilier de bureau et équipements'),
('Electronique',    'Appareils électroniques grand public'),
('Consommables',    'Encres, papier, batteries et consommables');

-- ── Produits ──────────────────────────────────────────────────
INSERT INTO produits (nom, reference, categorie_id, description, prix_achat, prix_vente, stock_actuel, stock_min, unite) VALUES
('Ordinateur Portable HP 15',  'INFO-001', 1, 'Intel i5, 8Go RAM, 256Go SSD',          250000, 350000, 15,  3,  'pièce'),
('Ordinateur Portable Dell',   'INFO-002', 1, 'Intel i7, 16Go RAM, 512Go SSD',         380000, 520000, 8,   2,  'pièce'),
('Clé USB 32Go',               'INFO-003', 1, 'USB 3.0 - Haute vitesse',               2500,   5000,   50,  10, 'pièce'),
('Souris sans fil Logitech',   'INFO-004', 1, 'Souris optique sans fil',               8000,   14000,  25,  5,  'pièce'),
('Clavier AZERTY',             'INFO-005', 1, 'Clavier filaire bureautique',           6000,   11000,  20,  5,  'pièce'),
('iPhone 14 128Go',            'TEL-001',  2, 'Apple iPhone 14, Noir',                480000, 650000, 5,   2,  'pièce'),
('Samsung Galaxy A54',         'TEL-002',  2, 'Samsung A54 5G 128Go',                 180000, 260000, 12,  3,  'pièce'),
('Coque iPhone 14',            'TEL-003',  2, 'Protection transparente',              1500,   4000,   40,  10, 'pièce'),
('Chargeur Rapide 65W',        'TEL-004',  2, 'Chargeur USB-C rapide',                5000,   9000,   30,  8,  'pièce'),
('Ramette A4 80g',             'FOU-001',  3, 'Ramette 500 feuilles A4 80g/m²',       2500,   4000,   80,  20, 'ramette'),
('Stylos Bille (boite 12)',     'FOU-002',  3, 'Stylos bleus boite de 12',             1200,   2500,   45,  10, 'boite'),
('Classeur A4 Noir',           'FOU-003',  3, 'Classeur à levier 8cm',                1500,   3000,   35,  10, 'pièce'),
('Post-it 76x76mm',            'FOU-004',  3, 'Bloc de 100 feuilles jaunes',           800,   1800,   60,  15, 'bloc'),
('Bureau Direction 160cm',     'MOB-001',  4, 'Bureau en L, couleur wengé',           85000, 150000,  3,   1,  'pièce'),
('Chaise Ergonomique',         'MOB-002',  4, 'Chaise de bureau réglable',            45000,  80000,  6,   2,  'pièce'),
('Armoire  rideaux',          'MOB-003',  4, 'Armoire 90x130cm, gris',               55000,  95000,  4,   1,  'pièce'),
('Television 55" Samsung',     'ELEC-001', 5, 'TV 4K UHD Smart TV 55 pouces',        200000, 320000,  4,   1,  'pièce'),
('Imprimante HP LaserJet',     'ELEC-002', 5, 'Imprimante laser monochrome',          85000, 130000,  7,   2,  'pièce'),
('Cartouche HP Noir',          'CONS-001', 6, 'Cartouche encre noire HP 664',         5000,  10000,  25,  8,  'pièce'),
('Papier Photo A4 Brillant',   'CONS-002', 6, 'Paquet 50 feuilles 180g',              3500,  7000,   30,  10, 'paquet');

-- ── Clients ───────────────────────────────────────────────────
INSERT INTO clients (nom, prenom, telephone, email, adresse, ville) VALUES
('KOUASSI',    'Jean-Baptiste', '+225 07 11 22 33', 'jb.kouassi@email.ci',    'Cocody Angré, Villa 15',         'Abidjan'),
('BAMBA',      'Fatoumata',     '+225 05 44 55 66', 'f.bamba@email.ci',       'Plateau, Immeuble Nour Al Hayat', 'Abidjan'),
('OUATTARA',   'Souleymane',    '+225 01 77 88 99', 'souleymane.o@email.ci',  'Yopougon Maroc',                 'Abidjan'),
('KONE',       'Aissatou',      '+225 07 22 33 44', 'aissatou.kone@email.ci', 'Marcory Zone 4',                 'Abidjan'),
('DIABY',      'Mamadou',       '+225 05 55 66 77', 'mamadou.d@email.ci',     'Adjamé 220 Logements',           'Abidjan'),
('N''GORAN',   'Adjoua',        '+225 01 88 99 00', 'n.goran@email.ci',       'Treichville Port-Bouet',         'Abidjan'),
('TRAORÉ',     'Ibrahim',       '+225 07 33 44 55', 'ibrahim.t@email.ci',     'Bouaké Centre',                  'Bouaké'),
('COULIBALY',  'Mariam',        '+225 05 66 77 88', 'mariam.c@email.ci',      'San-Pedro Port',                 'San-Pedro'),
('DOUMBIA',    'Seydou',        '+225 01 99 00 11', 'seydou.d@email.ci',      'Daloa Mairie',                   'Daloa'),
('ASSI',       'Christiane',    '+225 07 44 55 66', 'c.assi@email.ci',        'Abengourou Centre',              'Abengourou');

-- ── Ventes de test ────────────────────────────────────────────
-- Vente 1 : payée complètement
INSERT INTO ventes (numero_facture, client_id, user_id, montant_total, montant_paye, statut, date_vente) VALUES
('FAC-20240115-0001', 1, 3, 413000, 413000, 'payee', '2024-01-15 09:30:00');
INSERT INTO ventes_details (vente_id, produit_id, quantite, prix_unitaire) VALUES
(1, 1, 1, 350000),
(1, 4, 1, 14000),
(1, 5, 1, 11000),
(1, 3, 2, 5000);

-- Vente 2 : paiement partiel
INSERT INTO ventes (numero_facture, client_id, user_id, montant_total, montant_paye, statut, date_vente) VALUES
('FAC-20240118-0002', 2, 3, 650000, 300000, 'partielle', '2024-01-18 14:15:00');
INSERT INTO ventes_details (vente_id, produit_id, quantite, prix_unitaire) VALUES
(2, 6, 1, 650000);

-- Vente 3 : payée
INSERT INTO ventes (numero_facture, client_id, user_id, montant_total, montant_paye, statut, date_vente) VALUES
('FAC-20240122-0003', 3, 4, 120000, 120000, 'payee', '2024-01-22 10:00:00');
INSERT INTO ventes_details (vente_id, produit_id, quantite, prix_unitaire) VALUES
(3, 7, 1, 260000),  -- prix exemple ajusté
(3, 8, 2, 4000),
(3, 9, 1, 9000);

-- Vente 4 : en cours (crédit)
INSERT INTO ventes (numero_facture, client_id, user_id, montant_total, montant_paye, statut, date_vente) VALUES
('FAC-20240205-0004', 4, 3, 234000, 0, 'en_cours', '2024-02-05 11:30:00');
INSERT INTO ventes_details (vente_id, produit_id, quantite, prix_unitaire) VALUES
(4, 14, 1, 150000),
(4, 15, 1, 80000),
(4, 10, 1, 4000);

-- Vente 5 : payée
INSERT INTO ventes (numero_facture, client_id, user_id, montant_total, montant_paye, statut, date_vente) VALUES
('FAC-20240210-0005', 5, 4, 75000, 75000, 'payee', '2024-02-10 16:00:00');
INSERT INTO ventes_details (vente_id, produit_id, quantite, prix_unitaire) VALUES
(5, 10, 10, 4000),
(5, 11, 5, 2500),
(5, 12, 5, 3000),
(5, 13, 5, 1800);

-- Vente 6 : annulée
INSERT INTO ventes (numero_facture, client_id, user_id, montant_total, montant_paye, statut, date_vente) VALUES
('FAC-20240215-0006', 6, 3, 320000, 0, 'annulee', '2024-02-15 09:00:00');
INSERT INTO ventes_details (vente_id, produit_id, quantite, prix_unitaire) VALUES
(6, 17, 1, 320000);

-- Vente 7 : payée (mois récent)
INSERT INTO ventes (numero_facture, client_id, user_id, montant_total, montant_paye, statut, date_vente) VALUES
('FAC-20240301-0007', 7, 4, 546000, 546000, 'payee', '2024-03-01 10:30:00');
INSERT INTO ventes_details (vente_id, produit_id, quantite, prix_unitaire) VALUES
(7, 2, 1, 520000),
(7, 3, 2, 5000),
(7, 19, 2, 10000);

-- ── Mouvements de stock initiaux ──────────────────────────────
INSERT INTO mouvements_stock (produit_id, type_mouvement, quantite, motif, user_id) VALUES
(1,  'entree', 15, 'Stock initial',    1),
(2,  'entree', 8,  'Stock initial',    1),
(6,  'entree', 5,  'Stock initial',    1),
(7,  'entree', 12, 'Stock initial',    1),
(14, 'entree', 3,  'Stock initial',    1),
(17, 'entree', 4,  'Stock initial',    1),
(1,  'sortie', 1,  'Vente FAC-001',    3),
(7,  'sortie', 1,  'Vente FAC-003',    3);

-- ── Logs initiaux ─────────────────────────────────────────────
INSERT INTO logs (user_id, action, details) VALUES
(1, 'connexion',  'Première connexion administrateur'),
(1, 'parametres', 'Configuration initiale de l''entreprise'),
(1, 'sauvegarde', 'Sauvegarde initiale de la base de données');

-- ── Vérification finale ───────────────────────────────────────
SELECT 'users'            AS table_name, COUNT(*) AS nb FROM users
UNION ALL SELECT 'categories', COUNT(*) FROM categories
UNION ALL SELECT 'clients',    COUNT(*) FROM clients
UNION ALL SELECT 'produits',   COUNT(*) FROM produits
UNION ALL SELECT 'ventes',     COUNT(*) FROM ventes
UNION ALL SELECT 'ventes_details', COUNT(*) FROM ventes_details
UNION ALL SELECT 'mouvements_stock', COUNT(*) FROM mouvements_stock
UNION ALL SELECT 'parametres', COUNT(*) FROM parametres
UNION ALL SELECT 'logs',       COUNT(*) FROM logs;

-- FIN DU SCRIPT
-- Note : Mot de passe par défaut pour tous les utilisateurs de test = "uvci@2026"
-- IMPORTANT : Changer tous les mots de passe avant mise en production !
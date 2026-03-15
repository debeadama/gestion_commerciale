# views/dashboard_view.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QTableWidget, QTableWidgetItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from controllers.sale_controller import SaleController
from controllers.client_controller import ClientController
from controllers.product_controller import ProductController


class DashboardView(QWidget):
    """Dashboard principal avec chiffres cles et activite recente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._apply_styles()
        self.refresh()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(60000)

    # ----------------------------------------------------------
    # Construction de l'interface
    # ----------------------------------------------------------

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(15)
        main.setContentsMargins(20, 20, 20, 20)

        # En-tete
        header = QHBoxLayout()
        self.lbl_titre = QLabel("Tableau de Bord")
        self.lbl_titre.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.lbl_date = QLabel("")
        self.lbl_date.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(self.lbl_titre)
        header.addStretch()
        header.addWidget(self.lbl_date)
        main.addLayout(header)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main.addWidget(line)

        # Cartes ligne 1
        cards1 = QHBoxLayout()
        cards1.setSpacing(15)
        self.card_ca       = self._make_card("Chiffre d'Affaires", "0.00", "#1976D2", "Total ventes payees")
        self.card_ventes   = self._make_card("Ventes du jour",     "0",    "#059669", "Aujourd'hui")
        self.card_clients  = self._make_card("Clients",            "0",    "#7c3aed", "Total clients")
        self.card_produits = self._make_card("Produits",           "0",    "#d97706", "En catalogue")
        for c in [self.card_ca, self.card_ventes,
                  self.card_clients, self.card_produits]:
            cards1.addWidget(c['frame'])
        main.addLayout(cards1)

        # Cartes ligne 2
        cards2 = QHBoxLayout()
        cards2.setSpacing(15)
        self.card_impaye    = self._make_card("Montant Impaye",  "0.00", "#dc2626", "Ventes non soldees")
        self.card_stock_bas = self._make_card("Alertes Stock",   "0",    "#ea580c", "Produits en rupture")
        self.card_mois      = self._make_card("Ventes ce mois",  "0",    "#0891b2", "Ce mois-ci")
        self.card_panier    = self._make_card("Panier Moyen",    "0.00", "#65a30d", "Par vente")
        for c in [self.card_impaye, self.card_stock_bas,
                  self.card_mois, self.card_panier]:
            cards2.addWidget(c['frame'])
        main.addLayout(cards2)

        # Partie basse
        bottom = QHBoxLayout()
        bottom.setSpacing(15)

        # Dernieres ventes
        ventes_frame = QFrame()
        ventes_frame.setObjectName("bottom_frame")
        ventes_layout = QVBoxLayout(ventes_frame)
        ventes_layout.setContentsMargins(15, 15, 15, 15)
        lbl_v = QLabel("Dernières ventes")
        lbl_v.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        ventes_layout.addWidget(lbl_v)
        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(5)
        self.recent_table.setHorizontalHeaderLabels(
            ["N Facture", "Client", "Total", "Paye", "Statut"])
        self.recent_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self.recent_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.horizontalHeader().setStretchLastSection(True)
        self.recent_table.setAlternatingRowColors(True)
        ventes_layout.addWidget(self.recent_table)
        bottom.addWidget(ventes_frame, 3)

        # Stock bas
        stock_frame = QFrame()
        stock_frame.setObjectName("bottom_frame")
        stock_layout = QVBoxLayout(stock_frame)
        stock_layout.setContentsMargins(15, 15, 15, 15)
        lbl_s = QLabel("Alertes Stock Bas")
        lbl_s.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        stock_layout.addWidget(lbl_s)
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(3)
        self.stock_table.setHorizontalHeaderLabels(
            ["Produit", "Stock", "Minimum"])
        self.stock_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self.stock_table.verticalHeader().setVisible(False)
        self.stock_table.horizontalHeader().setStretchLastSection(True)
        self.stock_table.setAlternatingRowColors(True)
        stock_layout.addWidget(self.stock_table)
        bottom.addWidget(stock_frame, 2)

        main.addLayout(bottom)

    def _make_card(self, titre, valeur, color, sous_titre=''):
        frame = QFrame()
        frame.setObjectName("kpi_card")
        frame.setSizePolicy(QSizePolicy.Policy.Expanding,
                            QSizePolicy.Policy.Fixed)
        frame.setFixedHeight(110)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(4)
        bar = QFrame()
        bar.setFixedHeight(4)
        bar.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
        layout.addWidget(bar)
        lbl_titre = QLabel(titre)
        lbl_titre.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(lbl_titre)
        lbl_valeur = QLabel(valeur)
        lbl_valeur.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        lbl_valeur.setStyleSheet(f"color: {color};")
        layout.addWidget(lbl_valeur)
        if sous_titre:
            lbl_sub = QLabel(sous_titre)
            lbl_sub.setStyleSheet("color: #94a3b8; font-size: 10px;")
            layout.addWidget(lbl_sub)
        return {'frame': frame, 'valeur': lbl_valeur}

    # ----------------------------------------------------------
    # Chargement des donnees via controllers
    # ----------------------------------------------------------

    def refresh(self):
        from datetime import datetime
        self.lbl_date.setText(
            datetime.now().strftime("Mise a jour : %d/%m/%Y %H:%M"))
        self._load_kpis()
        self._load_recent_sales()
        self._load_low_stock()

    def _load_kpis(self):
        # Stats ventes
        sale_stats = SaleController.get_dashboard_stats()
        self.card_ca['valeur'].setText(
            f"{float(sale_stats.get('ca_total', 0)):.2f}")
        self.card_ventes['valeur'].setText(
            str(sale_stats.get('ventes_jour', 0)))
        self.card_mois['valeur'].setText(
            str(sale_stats.get('ventes_mois', 0)))
        self.card_panier['valeur'].setText(
            f"{float(sale_stats.get('panier_moyen', 0)):.2f}")
        self.card_impaye['valeur'].setText(
            f"{float(sale_stats.get('total_impayes', 0)):.2f}")

        # Stats clients
        clients = ClientController.get_all()
        self.card_clients['valeur'].setText(str(len(clients) if clients else 0))

        # Stats produits
        prod_stats = ProductController.get_dashboard_stats()
        self.card_produits['valeur'].setText(
            str(prod_stats.get('total_produits', 0)))
        nb_alertes = int(prod_stats.get('nb_alertes', 0))
        self.card_stock_bas['valeur'].setText(str(nb_alertes))
        color = "#dc2626" if nb_alertes > 0 else "#16a34a"
        self.card_stock_bas['valeur'].setStyleSheet(f"color: {color};")

    def _load_recent_sales(self):
        sales = SaleController.get_recent(8)
        statut_colors = {
            'payee':    '#16a34a', 'partielle': '#d97706',
            'en_cours': '#1976D2', 'annulee':   '#dc2626',
        }
        self.recent_table.setRowCount(0)
        for row_idx, s in enumerate(sales or []):
            self.recent_table.insertRow(row_idx)
            statut = s.get('statut', '')
            vals = [
                s.get('numero_facture', ''),
                s.get('client', ''),
                f"{float(s.get('montant_total', 0)):.2f}",
                f"{float(s.get('montant_paye', 0)):.2f}",
                statut.upper(),
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 4:
                    item.setForeground(
                        QColor(statut_colors.get(statut, '#64748b')))
                    f = item.font(); f.setBold(True); item.setFont(f)
                self.recent_table.setItem(row_idx, col, item)
        self.recent_table.resizeColumnsToContents()

    def _load_low_stock(self):
        products = ProductController.get_low_stock()
        self.stock_table.setRowCount(0)
        for row_idx, p in enumerate(products or []):
            self.stock_table.insertRow(row_idx)
            vals = [p.get('nom', ''),
                    str(p.get('stock_actuel', 0)),
                    str(p.get('stock_min', 0))]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 1:
                    item.setForeground(QColor('#dc2626'))
                    f = item.font(); f.setBold(True); item.setFont(f)
                self.stock_table.setItem(row_idx, col, item)
        if not products:
            self.stock_table.insertRow(0)
            item = QTableWidgetItem("Aucune alerte de stock")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setForeground(QColor('#16a34a'))
            self.stock_table.setItem(0, 0, item)
            self.stock_table.setSpan(0, 0, 1, 3)

    # ----------------------------------------------------------
    # Styles
    # ----------------------------------------------------------

    def _apply_styles(self):
        self.setStyleSheet("""
            QFrame#kpi_card {
                background-color: white; border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QFrame#bottom_frame {
                background-color: white; border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QTableWidget {
                border: none; font-size: 12px;
                background: white; gridline-color: #f1f5f9;
            }
            QTableWidget::item:selected {
                background-color: #dbeafe; color: #1e293b;
            }
            QHeaderView::section {
                background-color: #f8fafc; color: #475569;
                font-weight: bold; font-size: 11px; padding: 6px;
                border: none; border-bottom: 2px solid #e2e8f0;
            }
        """)

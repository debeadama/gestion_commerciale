# views/products_view.py
import os
from PyQt6 import uic
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox,
    QSpinBox, QDoubleSpinBox, QTextEdit, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from controllers.product_controller import ProductController
from controllers.category_controller import CategoryController
from controllers.auth_controller import SessionManager
from utils.pagination_widget import PaginationWidget


def _confirm(parent, title, message):
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(message)
    box.setIcon(QMessageBox.Icon.Question)
    btn_oui = box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
    box.addButton("Non", QMessageBox.ButtonRole.NoRole)
    box.exec()
    return box.clickedButton() == btn_oui


class ProductsView(QWidget):
    """Module complet de gestion des produits et du stock."""

    def __init__(self, parent=None):
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'products.ui')
        uic.loadUi(ui_path, self)
        self._connect_signals()
        self._apply_styles()
        self.load_products()

    # ----------------------------------------------------------
    # Connexion des signaux
    # ----------------------------------------------------------

    def _connect_signals(self):
        self.btn_search.clicked.connect(self._search)
        self.btn_reset.clicked.connect(self._reset)
        self.btn_add.clicked.connect(self._add_product)
        self.btn_edit.clicked.connect(self._edit_product)
        self.btn_delete.clicked.connect(self._delete_product)
        self.btn_stock.clicked.connect(self._stock_movement)
        self.btn_categories.clicked.connect(self._manage_categories)
        self.search_input.returnPressed.connect(self._search)
        self.filter_category.currentIndexChanged.connect(self._search)
        self.products_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.products_table.doubleClicked.connect(self._edit_product)
        # Pagination
        self._all_products = []
        self.pagination = PaginationWidget(page_size=50, parent=self)
        self.pagination.page_changed.connect(self._on_page_changed)
        table_parent = self.products_table.parent()
        if table_parent and table_parent.layout():
            table_parent.layout().addWidget(self.pagination)

    # ----------------------------------------------------------
    # Chargement des donnees
    # ----------------------------------------------------------

    def load_products(self, search=None, category_id=None):
        """Charge et affiche la liste des produits."""
        self._reload_categories()
        self._all_products = ProductController.get_all(search, category_id)
        count = len(self._all_products)
        self.lbl_total.setText(f"Total : {count} produit(s)")
        self.status_bar.setText(f"{count} produit(s) affiché(s)")
        self.pagination.reset(count)
        offset = self.pagination.current_offset()
        limit  = self.pagination.current_limit()
        self._populate_table(self._all_products[offset:offset + limit])

        # Alerte stock bas
        low_stock = ProductController.get_low_stock()
        if low_stock:
            self.lbl_alert.setText(
                f"  Attention : {len(low_stock)} produit(s) en stock bas !")
            self.lbl_alert.show()
        else:
            self.lbl_alert.hide()

    def _on_page_changed(self, page, offset, limit):
        self._populate_table(
            (self._all_products or [])[offset:offset + limit])

    def _reload_categories(self):
        """Recharge les categories dans le filtre."""
        current = self.filter_category.currentData()
        self.filter_category.blockSignals(True)
        self.filter_category.clear()
        self.filter_category.addItem("Toutes categories", None)
        for cat in CategoryController.get_all():
            self.filter_category.addItem(cat['nom'], cat['id'])
        for i in range(self.filter_category.count()):
            if self.filter_category.itemData(i) == current:
                self.filter_category.setCurrentIndex(i)
                break
        self.filter_category.blockSignals(False)

    def _populate_table(self, products):
        """Remplit le tableau avec les produits."""
        self.products_table.setRowCount(0)
        for row_idx, p in enumerate(products):
            self.products_table.insertRow(row_idx)

            # Calcul de la marge beneficiaire
            prix_achat = float(p.get('prix_achat', 0))
            prix_vente = float(p.get('prix_vente', 0))
            if prix_vente > 0:
                marge = ((prix_vente - prix_achat) / prix_vente) * 100
            else:
                marge = 0.0

            stock_actuel = int(p.get('stock_actuel', 0))
            stock_min    = int(p.get('stock_min', 0))
            stock_ok     = stock_actuel > stock_min

            values = [
                str(p['id']),
                p.get('nom', ''),
                p.get('categorie', ''),
                f"{prix_achat:.2f}",
                f"{prix_vente:.2f}",
                f"{marge:.1f} %",
                str(stock_actuel),
                str(stock_min),
                "OK" if stock_ok else "STOCK BAS",
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if not stock_ok:
                    item.setBackground(QColor("#fee2e2"))
                    item.setForeground(QColor("#dc2626"))
                self.products_table.setItem(row_idx, col, item)

        self.products_table.resizeColumnsToContents()
        self.products_table.setColumnHidden(0, True)

    # ----------------------------------------------------------
    # Actions
    # ----------------------------------------------------------

    def _reset(self):
        self.search_input.clear()
        self.filter_category.setCurrentIndex(0)
        self.load_products()

    def _search(self):
        term   = self.search_input.text().strip() or None
        cat_id = self.filter_category.currentData()
        self.load_products(term, cat_id)

    def _on_selection_changed(self):
        has = len(self.products_table.selectedItems()) > 0
        self.btn_edit.setEnabled(has)
        self.btn_delete.setEnabled(has)
        self.btn_stock.setEnabled(has)

    def _get_selected_id(self):
        row = self.products_table.currentRow()
        if row < 0:
            return None
        self.products_table.setColumnHidden(0, False)
        id_item = self.products_table.item(row, 0)
        self.products_table.setColumnHidden(0, True)
        return int(id_item.text()) if id_item else None

    def _add_product(self):
        dialog = ProductFormDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            success, result = ProductController.create(dialog.get_data())
            if success:
                self.load_products()
                self.status_bar.setText("Produit ajoute avec succès.")
            else:
                QMessageBox.critical(self, "Erreur", result)

    def _edit_product(self):
        product_id = self._get_selected_id()
        if not product_id:
            return
        product = ProductController.get_by_id(product_id)
        dialog  = ProductFormDialog(product_data=product, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            success, result = ProductController.update(product_id, dialog.get_data())
            if success:
                self.load_products()
                self.status_bar.setText("Produit modifie avec succès.")
            else:
                QMessageBox.critical(self, "Erreur", result)

    def _delete_product(self):
        product_id = self._get_selected_id()
        if not product_id:
            return
        row = self.products_table.currentRow()
        nom = self.products_table.item(row, 1).text()
        if _confirm(self, "Confirmation", f"Supprimér le produit : {nom} ?"):
            success, message = ProductController.delete(product_id)
            if success:
                self.load_products()
                self.status_bar.setText("Produit supprime.")
            else:
                QMessageBox.warning(self, "Impossible", message)

    def _stock_movement(self):
        product_id = self._get_selected_id()
        if not product_id:
            return
        product = ProductController.get_by_id(product_id)
        user_id = SessionManager.get_current_user()['id']
        dialog  = StockMovementDialog(product, user_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_products()
            self.status_bar.setText("Mouvement de stock enregistre.")

    def _manage_categories(self):
        dialog = CategoriesDialog(parent=self)
        dialog.exec()
        self.load_products()

    # ----------------------------------------------------------
    # Styles
    # ----------------------------------------------------------

    def _apply_styles(self):
        self.setStyleSheet("""
            QLabel#lbl_titre {
                font-size: 20px; font-weight: bold; color: #1e293b;
            }
            QLabel#lbl_total { font-size: 13px; color: #64748b; }
            QLabel#status_bar { font-size: 11px; color: #64748b; padding: 4px; }
            QLabel#lbl_alert {
                background-color: #fef3c7; color: #92400e;
                border: 1px solid #fcd34d; border-radius: 5px;
                padding: 6px 12px; font-size: 12px; font-weight: bold;
            }
            QLineEdit, QComboBox {
                border: 1px solid #cbd5e1; border-radius: 5px;
                padding: 5px 10px; font-size: 13px; background: white;
            }
            QLineEdit:focus { border-color: #1976D2; }
            QPushButton {
                border: none; border-radius: 5px; padding: 5px 10px;
                font-size: 12px; color: white; background-color: #64748b;
            }
            QPushButton:hover { background-color: #475569; }
            QPushButton#btn_add { background-color: #1976D2; font-weight: bold; }
            QPushButton#btn_add:hover { background-color: #1565C0; }
            QPushButton:disabled { background-color: #e2e8f0; color: #94a3b8; }
            QTableWidget {
                border: 1px solid #e2e8f0; border-radius: 5px;
                gridline-color: #f1f5f9; font-size: 13px; background: white;
            }
            QTableWidget::item:selected { background-color: #dbeafe; color: #1e293b; }
            QHeaderView::section {
                background-color: #f8fafc; color: #475569;
                font-weight: bold; font-size: 12px; padding: 8px;
                border: none; border-bottom: 2px solid #e2e8f0;
            }
        """)


# ──────────────────────────────────────────────────────────────
# Formulaire Ajouter / Modifier un produit
# ──────────────────────────────────────────────────────────────

class ProductFormDialog(QDialog):

    def __init__(self, product_data=None, parent=None):
        super().__init__(parent)
        is_edit = product_data is not None
        self.setWindowTitle("Modifier le produit" if is_edit else "Nouveau produit")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()
        if is_edit:
            self._fill_form(product_data)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        form.setSpacing(10)

        self.nom_input = QLineEdit()
        self.nom_input.setMinimumHeight(34)

        self.category_combo = QComboBox()
        self.category_combo.setMinimumHeight(34)
        for cat in CategoryController.get_all():
            self.category_combo.addItem(cat['nom'], cat['id'])

        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(70)

        self.prix_achat_input = QDoubleSpinBox()
        self.prix_achat_input.setMinimumHeight(34)
        self.prix_achat_input.setMaximum(9999999)
        self.prix_achat_input.setDecimals(2)

        self.prix_vente_input = QDoubleSpinBox()
        self.prix_vente_input.setMinimumHeight(34)
        self.prix_vente_input.setMaximum(9999999)
        self.prix_vente_input.setDecimals(2)

        self.stock_min_input = QSpinBox()
        self.stock_min_input.setMinimumHeight(34)
        self.stock_min_input.setMaximum(99999)
        self.stock_min_input.setValue(5)

        self.stock_actuel_input = QSpinBox()
        self.stock_actuel_input.setMinimumHeight(34)
        self.stock_actuel_input.setMaximum(99999)

        form.addRow("Nom *",         self.nom_input)
        form.addRow("Catégorie",     self.category_combo)
        form.addRow("Description",   self.description_input)
        form.addRow("Prix achat",    self.prix_achat_input)
        form.addRow("Prix vente *",  self.prix_vente_input)
        form.addRow("Stock minimum", self.stock_min_input)
        form.addRow("Stock initial", self.stock_actuel_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Enregistrer")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _fill_form(self, data):
        self.nom_input.setText(data.get('nom', ''))
        self.description_input.setText(data.get('description') or '')
        self.prix_achat_input.setValue(float(data.get('prix_achat', 0)))
        self.prix_vente_input.setValue(float(data.get('prix_vente', 0)))
        self.stock_min_input.setValue(int(data.get('stock_min', 5)))
        self.stock_actuel_input.setValue(int(data.get('stock_actuel', 0)))
        for i in range(self.category_combo.count()):
            if self.category_combo.itemData(i) == data.get('category_id'):
                self.category_combo.setCurrentIndex(i)
                break

    def _validate(self):
        if not self.nom_input.text().strip():
            QMessageBox.warning(self, "Champ requis", "Le nom est obligatoire.")
            self.nom_input.setFocus()
            return
        if self.prix_vente_input.value() <= 0:
            QMessageBox.warning(self, "Valeur invalide",
                                "Le prix de vente doit etre superieur a 0.")
            return
        self.accept()

    def get_data(self):
        return {
            'nom':          self.nom_input.text().strip(),
            'category_id':  self.category_combo.currentData(),
            'description':  self.description_input.toPlainText().strip(),
            'prix_achat':   self.prix_achat_input.value(),
            'prix_vente':   self.prix_vente_input.value(),
            'stock_min':    self.stock_min_input.value(),
            'stock_actuel': self.stock_actuel_input.value(),
        }


# ──────────────────────────────────────────────────────────────
# Mouvement de stock
# ──────────────────────────────────────────────────────────────

class StockMovementDialog(QDialog):

    def __init__(self, product, user_id, parent=None):
        super().__init__(parent)
        self.product = product
        self.user_id = user_id
        self.setWindowTitle(f"Mouvement de stock - {product['nom']}")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        info = QLabel(
            f"Produit : {self.product['nom']}\n"
            f"Stock actuel : {self.product['stock_actuel']}")
        info.setStyleSheet(
            "background: #f1f5f9; padding: 10px; border-radius: 5px;")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(10)

        self.type_combo = QComboBox()
        self.type_combo.setMinimumHeight(34)
        self.type_combo.addItem("Entree en stock", "entree")
        self.type_combo.addItem("Sortie de stock", "sortie")
        self.type_combo.addItem("Ajustement",      "ajustement")

        self.quantite_input = QSpinBox()
        self.quantite_input.setMinimumHeight(34)
        self.quantite_input.setMinimum(1)
        self.quantite_input.setMaximum(99999)

        self.motif_input = QLineEdit()
        self.motif_input.setMinimumHeight(34)
        self.motif_input.setPlaceholderText("Motif du mouvement...")

        form.addRow("Type",     self.type_combo)
        form.addRow("Quantite", self.quantite_input)
        form.addRow("Motif",    self.motif_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Valider")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate(self):
        success, message = ProductController.add_stock_movement(
            product_id     = self.product['id'],
            type_mouvement = self.type_combo.currentData(),
            quantite       = self.quantite_input.value(),
            motif          = self.motif_input.text().strip(),
            user_id        = self.user_id,
        )
        if success:
            self.accept()
        else:
            QMessageBox.warning(self, "Erreur", message)


# ──────────────────────────────────────────────────────────────
# Gestion des categories
# ──────────────────────────────────────────────────────────────

class CategoriesDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des categories")
        self.setMinimumSize(500, 400)
        self._build_ui()
        self._load_categories()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        lbl = QLabel("Catégories de produits")
        lbl.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        layout.addWidget(lbl)

        toolbar = QHBoxLayout()
        self.cat_input = QLineEdit()
        self.cat_input.setPlaceholderText("Nom de la nouvelle categorie...")
        self.cat_input.setMinimumHeight(34)

        self.btn_add_cat = QPushButton("Ajouter")
        self.btn_add_cat.setMinimumHeight(34)
        self.btn_add_cat.setStyleSheet(
            "background-color:#1976D2;color:white;border:none;"
            "border-radius:5px;padding:5px 12px;")

        self.btn_del_cat = QPushButton("Supprimer")
        self.btn_del_cat.setMinimumHeight(34)
        self.btn_del_cat.setEnabled(False)
        self.btn_del_cat.setStyleSheet(
            "background-color:#64748b;color:white;border:none;"
            "border-radius:5px;padding:5px 12px;")

        toolbar.addWidget(self.cat_input)
        toolbar.addWidget(self.btn_add_cat)
        toolbar.addWidget(self.btn_del_cat)
        layout.addLayout(toolbar)

        self.cat_table = QTableWidget()
        self.cat_table.setColumnCount(2)
        self.cat_table.setHorizontalHeaderLabels(["ID", "Nom"])
        self.cat_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cat_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.cat_table.verticalHeader().setVisible(False)
        self.cat_table.horizontalHeader().setStretchLastSection(True)
        self.cat_table.setColumnHidden(0, True)
        self.cat_table.itemSelectionChanged.connect(
            lambda: self.btn_del_cat.setEnabled(
                len(self.cat_table.selectedItems()) > 0))
        layout.addWidget(self.cat_table)

        self.btn_add_cat.clicked.connect(self._add_category)
        self.btn_del_cat.clicked.connect(self._delete_category)

        btn_close = QPushButton("Fermer")
        btn_close.setFixedWidth(100)
        btn_close.setStyleSheet(
            "background-color:#64748b;color:white;border:none;"
            "border-radius:5px;padding:6px;")
        btn_close.clicked.connect(self.accept)
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(btn_close)
        layout.addLayout(h)

    def _load_categories(self):
        cats = CategoryController.get_all()
        self.cat_table.setRowCount(0)
        for i, cat in enumerate(cats):
            self.cat_table.insertRow(i)
            self.cat_table.setItem(i, 0, QTableWidgetItem(str(cat['id'])))
            self.cat_table.setItem(i, 1, QTableWidgetItem(cat['nom']))

    def _add_category(self):
        nom = self.cat_input.text().strip()
        if not nom:
            QMessageBox.warning(self, "Champ requis",
                                "Entrez un nom de categorie.")
            return
        success, result = CategoryController.create(nom)
        if success:
            self.cat_input.clear()
            self._load_categories()
        else:
            QMessageBox.critical(self, "Erreur", result)

    def _delete_category(self):
        row = self.cat_table.currentRow()
        if row < 0:
            return
        self.cat_table.setColumnHidden(0, False)
        cat_id = int(self.cat_table.item(row, 0).text())
        self.cat_table.setColumnHidden(0, True)
        success, message = CategoryController.delete(cat_id)
        if not success:
            QMessageBox.warning(self, "Impossible", message)
        else:
            self._load_categories()

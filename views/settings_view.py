# views/settings_view.py
import os
import subprocess
from datetime import datetime

from controllers.auth_controller import SessionManager
from controllers.user_controller import UserController
from database.connection import db
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


def _confirm(parent, title, message):
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(message)
    box.setIcon(QMessageBox.Icon.Question)
    btn_oui = box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
    box.addButton("Non", QMessageBox.ButtonRole.NoRole)
    box.exec()
    return box.clickedButton() == btn_oui


class SettingsView(QWidget):
    """Module Paramètres - admin uniquement."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ensure_columns()
        self._build_ui()
        self._apply_styles()

    def _ensure_columns(self):
        """Ajouté les colonnes manquantes si elles n\'existent pas."""
        # Verifier et ajouter nom_complet si absente
        r = db.execute_query("""
            SELECT COUNT(*) AS nb FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME   = 'users'
              AND COLUMN_NAME  = 'nom_complet'
        """, fetch_one=True)
        if r and r['nb'] == 0:
            db.execute_update(
                "ALTER TABLE users ADD COLUMN nom_complet VARCHAR(100) NULL AFTER username")

        # Verifier et ajouter email si absent
        r = db.execute_query("""
            SELECT COUNT(*) AS nb FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME   = 'users'
              AND COLUMN_NAME  = 'email'
        """, fetch_one=True)
        if r and r['nb'] == 0:
            db.execute_update(
                "ALTER TABLE users ADD COLUMN email VARCHAR(150) NULL DEFAULT NULL AFTER nom_complet")
        try:
            db.execute_update(
                "CREATE TABLE IF NOT EXISTS logs ("
                "  id         INT AUTO_INCREMENT PRIMARY KEY,"
                "  user_id    INT NULL,"
                "  action     VARCHAR(100) NOT NULL,"
                "  details    TEXT,"
                "  ip_address VARCHAR(45),"
                "  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,"
                "  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL"
                ")")
        except Exception:
            pass

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(12)
        main.setContentsMargins(20, 15, 20, 15)

        lbl = QLabel("Parametres")
        lbl.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #1e293b;")
        main.addWidget(lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        main.addWidget(sep)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("settings_tabs")

        self.tab_company = CompanyTab()
        self.tabs.addTab(self.tab_company, "  Entreprise  ")

        self.tab_users = UsersTab()
        self.tabs.addTab(self.tab_users, "  Utilisateurs  ")
        # Masquer l'onglet Utilisateurs pour les managers
        if SessionManager.get_role() != 'admin':
            self.tabs.setTabVisible(1, False)

        self.tab_general = GeneralTab()
        self.tabs.addTab(self.tab_general, "  Paramètres generaux  ")

        self.tab_backup = BackupTab()
        self.tabs.addTab(self.tab_backup, "  Sauvegarde / Restauration  ")

        self.tab_logs = LogsTab()
        self.tabs.addTab(self.tab_logs, "  Journal d'activite  ")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        main.addWidget(self.tabs)

    def _on_tab_changed(self, idx):
        if idx == 1:
            self.tab_users.load()
        elif idx == 4:
            self.tab_logs.load()

    def _apply_styles(self):
        self.setStyleSheet("""
            QPushButton#btn_primary {
                background-color: #1976D2; color: white; font-weight: bold;
            }
            QPushButton#btn_primary:hover { background-color: #1565C0; }
            QPushButton#btn_danger {
                background-color: #fee2e2; color: #dc2626;
            }
            QPushButton#btn_danger:hover { background-color: #fecaca; }
            QPushButton#btn_success {
                background-color: #dcfce7; color: #16a34a;
            }
            QPushButton#btn_success:hover { background-color: #bbf7d0; }
            QLabel#section_title {
                font-size: 12px; font-weight: bold; color: #1e293b;
            }
        """)


# ──────────────────────────────────────────────────────────────
# Onglet Entreprise
# ──────────────────────────────────────────────────────────────

class CompanyTab(QWidget):

    def __init__(self):
        super().__init__()
        self._build_ui()
        self.load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        lbl = QLabel("Configuration de l'entreprise")
        lbl.setObjectName("section_title")
        layout.addWidget(lbl)

        # Logo
        logo_layout = QHBoxLayout()
        self.logo_preview = QLabel("Logo")
        self.logo_preview.setFixedSize(120, 80)
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setStyleSheet(
            "border: 2px dashed #cbd5e1; border-radius: 8px;"
            "background: #f8fafc; color: #94a3b8;")
        self.logo_path = ""

        btn_logo = QPushButton("Choisir un logo")
        btn_logo.setFixedWidth(150)
        btn_logo.clicked.connect(self._pick_logo)

        logo_layout.addWidget(self.logo_preview)
        logo_layout.addWidget(btn_logo)
        logo_layout.addStretch()
        layout.addLayout(logo_layout)

        # Formulaire
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.nom_input = QLineEdit()
        self.adresse_input = QLineEdit()
        self.tel_input = QLineEdit()
        self.email_input = QLineEdit()
        self.site_input = QLineEdit()
        self.rc_input = QLineEdit()
        self.nif_input = QLineEdit()

        form.addRow("Nom entreprise *", self.nom_input)
        form.addRow("Adresse", self.adresse_input)
        form.addRow("Telephone", self.tel_input)
        form.addRow("Email", self.email_input)
        form.addRow("Site web", self.site_input)
        form.addRow("Registre Commerce", self.rc_input)
        form.addRow("N Identification", self.nif_input)
        layout.addLayout(form)

        btn_save = QPushButton("Enregistrer")
        btn_save.setObjectName("btn_primary")
        btn_save.setFixedWidth(150)
        btn_save.clicked.connect(self.save)
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(btn_save)
        layout.addLayout(h)
        layout.addStretch()

    def _pick_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choisir un logo", "",
            "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self.logo_path = path
            px = QPixmap(path).scaled(
                120, 80,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            self.logo_preview.setPixmap(px)

    def load(self):
        try:
            params = db.execute_query("SELECT cle, valeur FROM parametres")
            data = {p['cle']: p['valeur'] for p in (params or [])}
        except Exception:
            data = {}
        self.nom_input.setText(data.get('nom_entreprise', ''))
        self.adresse_input.setText(data.get('adresse', ''))
        self.tel_input.setText(data.get('telephone', ''))
        self.email_input.setText(data.get('email', ''))
        self.site_input.setText(data.get('site_web', ''))
        self.rc_input.setText(data.get('registre_commerce', ''))
        self.nif_input.setText(data.get('nif', ''))
        logo = data.get('logo_path', '')
        if logo and os.path.exists(logo):
            px = QPixmap(logo).scaled(
                120, 80,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            self.logo_preview.setPixmap(px)
            self.logo_path = logo

    def save(self):
        if not self.nom_input.text().strip():
            QMessageBox.warning(self, "Requis",
                                "Le nom de l'entreprise est obligatoire.")
            return
        fields = {
            'nom_entreprise': self.nom_input.text().strip(),
            'adresse': self.adresse_input.text().strip(),
            'telephone': self.tel_input.text().strip(),
            'email': self.email_input.text().strip(),
            'site_web': self.site_input.text().strip(),
            'registre_commerce': self.rc_input.text().strip(),
            'nif': self.nif_input.text().strip(),
        }
        if self.logo_path:
            fields['logo_path'] = self.logo_path
        try:
            for cle, valeur in fields.items():
                db.execute_update("""
                    INSERT INTO parametres (cle, valeur)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE valeur = %s
                """, (cle, valeur, valeur))
            QMessageBox.information(self, "Succes",
                                    "Informations entreprise enregistrees.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))


# ──────────────────────────────────────────────────────────────
# Onglet Utilisateurs
# ──────────────────────────────────────────────────────────────

class UsersTab(QWidget):

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        lbl = QLabel("Gestion des utilisateurs")
        lbl.setObjectName("section_title")
        layout.addWidget(lbl)

        toolbar = QHBoxLayout()
        self.btn_add = QPushButton("+ Nouvel utilisateur")
        self.btn_add.setObjectName("btn_primary")
        self.btn_edit = QPushButton("Modifier")
        self.btn_edit.setEnabled(False)
        self.btn_del = QPushButton("Supprimer")
        self.btn_del.setObjectName("btn_danger")
        self.btn_del.setEnabled(False)
        self.btn_pwd = QPushButton("Changer mot de passe")
        self.btn_pwd.setEnabled(False)
        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_del)
        toolbar.addWidget(self.btn_pwd)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nom utilisateur", "Nom complet", "Email", "Role", "Date creation"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnHidden(0, True)
        self.table.itemSelectionChanged.connect(self._on_select)
        layout.addWidget(self.table)

        self.btn_add.clicked.connect(self._add_user)
        self.btn_edit.clicked.connect(self._edit_user)
        self.btn_del.clicked.connect(self._delete_user)
        self.btn_pwd.clicked.connect(self._change_password)

    def load(self):
        users = UserController.get_all()
        self.table.setRowCount(0)
        role_colors = {
            'admin': '#1976D2',
            'manager': '#059669',
            'vendeur': '#d97706'
        }
        for i, u in enumerate(users or []):
            self.table.insertRow(i)
            vals = [
                str(u['id']),
                u.get('username', ''),
                u.get('nom_complet') or '',
                u.get('email') or '',
                u.get('role', ''),
                str(u.get('created_at', ''))[:10],
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 4:
                    item.setForeground(
                        QColor(role_colors.get(val, '#64748b')))
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)
                self.table.setItem(i, col, item)
        self.table.resizeColumnsToContents()

    def _on_select(self):
        has = len(self.table.selectedItems()) > 0
        self.btn_edit.setEnabled(has)
        self.btn_del.setEnabled(has)
        self.btn_pwd.setEnabled(has)

    def _get_selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        self.table.setColumnHidden(0, False)
        val = self.table.item(row, 0).text()
        self.table.setColumnHidden(0, True)
        return int(val)

    def _add_user(self):
        dlg = UserFormDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            success, result = UserController.create(
                username=data['username'],
                password=data['password'],
                role=data['role'],
                nom_complet=data.get('nom_complet', ''),
                email=data.get('email', ''),
            )
            if success:
                self.load()
                QMessageBox.information(self, "Succes", "Utilisateur cree.")
            else:
                QMessageBox.critical(self, "Erreur", result)

    def _edit_user(self):
        uid = self._get_selected_id()
        if not uid:
            return
        user = UserController.get_by_id(uid)
        dlg = UserFormDialog(user_data=user, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            success, result = UserController.update(
                user_id=uid,
                username=data['username'],
                role=data['role'],
                nom_complet=data.get('nom_complet', ''),
                email=data.get('email', ''),
            )
            if success:
                self.load()
                QMessageBox.information(self, "Succes", "Utilisateur modifie.")
            else:
                QMessageBox.critical(self, "Erreur", result)

    def _delete_user(self):
        uid = self._get_selected_id()
        if not uid:
            return
        current = SessionManager.get_current_user()
        if uid == current['id']:
            QMessageBox.warning(
                self,
                "Impossible",
                "Vous ne pouvez pas supprimer votre propre compte.")
            return
        if _confirm(self, "Confirmation", "Supprimer cet utilisateur ?"):
            success, message = UserController.delete(uid)
            if success:
                self.load()
            else:
                QMessageBox.critical(self, "Erreur", message)

    def _change_password(self):
        uid = self._get_selected_id()
        if not uid:
            return
        dlg = ChangePasswordDialog(uid, parent=self)
        dlg.exec()


# ──────────────────────────────────────────────────────────────
# Onglet Parametres generaux
# ──────────────────────────────────────────────────────────────

class GeneralTab(QWidget):

    def __init__(self):
        super().__init__()
        self._build_ui()
        self.load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        lbl = QLabel("Paramètres generaux")
        lbl.setObjectName("section_title")
        layout.addWidget(lbl)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.devise_input = QLineEdit()
        self.devise_input.setPlaceholderText("ex: FCFA, EUR, USD")
        self.devise_input.setFixedWidth(200)

        self.tva_input = QDoubleSpinBox()
        self.tva_input.setRange(0, 100)
        self.tva_input.setDecimals(1)
        self.tva_input.setSuffix(" %")
        self.tva_input.setFixedWidth(120)

        self.format_combo = QComboBox()
        self.format_combo.setFixedWidth(200)
        self.format_combo.addItems(["A4", "A5", "Letter"])

        self.decimales_input = QSpinBox()
        self.decimales_input.setRange(0, 4)
        self.decimales_input.setValue(2)
        self.decimales_input.setFixedWidth(80)

        form.addRow("Devise", self.devise_input)
        form.addRow("Taux TVA", self.tva_input)
        form.addRow("Format factures", self.format_combo)
        form.addRow("Nb decimales prix", self.decimales_input)
        layout.addLayout(form)

        btn_save = QPushButton("Enregistrer")
        btn_save.setObjectName("btn_primary")
        btn_save.setFixedWidth(150)
        btn_save.clicked.connect(self.save)
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(btn_save)
        layout.addLayout(h)
        layout.addStretch()

    def load(self):
        try:
            params = db.execute_query("SELECT cle, valeur FROM parametres")
            data = {p['cle']: p['valeur'] for p in (params or [])}
        except Exception:
            data = {}
        self.devise_input.setText(data.get('devise', 'FCFA'))
        try:
            self.tva_input.setValue(float(data.get('tva', 0)))
        except Exception:
            pass
        fmt = data.get('format_facture', 'A4')
        idx = self.format_combo.findText(fmt)
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)
        try:
            self.decimales_input.setValue(int(data.get('nb_decimales', 2)))
        except Exception:
            pass

    def save(self):
        fields = {
            'devise': self.devise_input.text().strip() or 'FCFA',
            'tva': str(self.tva_input.value()),
            'format_facture': self.format_combo.currentText(),
            'nb_decimales': str(self.decimales_input.value()),
        }
        try:
            for cle, valeur in fields.items():
                db.execute_update("""
                    INSERT INTO parametres (cle, valeur)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE valeur = %s
                """, (cle, valeur, valeur))
            QMessageBox.information(self, "Succes", "Paramètres enregistres.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))


# ──────────────────────────────────────────────────────────────
# Onglet Sauvegarde / Restauration
# ──────────────────────────────────────────────────────────────

class BackupTab(QWidget):

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # Sauvegarde
        save_frame = QFrame()
        save_frame.setStyleSheet(
            "QFrame { background: #f8fafc; border: 1px solid #e2e8f0;"
            "border-radius: 8px; }")
        sv = QVBoxLayout(save_frame)
        sv.setContentsMargins(20, 15, 20, 15)
        sv.setSpacing(10)

        lbl_s = QLabel("Sauvegarde de la base de données")
        lbl_s.setObjectName("section_title")
        sv.addWidget(lbl_s)

        info_s = QLabel(
            "Genere un fichier SQL complet de la base de données. "
            "Conservez ce fichier en lieu sur.")
        info_s.setStyleSheet("color: #64748b; font-size: 11px;")
        info_s.setWordWrap(True)
        sv.addWidget(info_s)

        btn_backup = QPushButton("Sauvegarder maintenant")
        btn_backup.setObjectName("btn_success")
        btn_backup.setFixedWidth(200)
        btn_backup.clicked.connect(self._do_backup)
        sv.addWidget(btn_backup)

        self.lbl_backup_status = QLabel("")
        self.lbl_backup_status.setStyleSheet(
            "color: #16a34a; font-size: 11px;")
        sv.addWidget(self.lbl_backup_status)
        layout.addWidget(save_frame)

        # Restauration
        rest_frame = QFrame()
        rest_frame.setStyleSheet(
            "QFrame { background: #fff7f7; border: 1px solid #fecaca;"
            "border-radius: 8px; }")
        rv = QVBoxLayout(rest_frame)
        rv.setContentsMargins(20, 15, 20, 15)
        rv.setSpacing(10)

        lbl_r = QLabel("Restauration de la base de données")
        lbl_r.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #dc2626;")
        rv.addWidget(lbl_r)

        warn = QLabel(
            "ATTENTION : La restauration ecrase toutes les données actuelles. "
            "Effectuez une sauvegarde avant de restaurer.")
        warn.setStyleSheet(
            "color: #dc2626; font-size: 11px; font-weight: bold;")
        warn.setWordWrap(True)
        rv.addWidget(warn)

        btn_restore = QPushButton("Choisir un fichier et restaurer")
        btn_restore.setObjectName("btn_danger")
        btn_restore.setFixedWidth(230)
        btn_restore.clicked.connect(self._do_restore)
        rv.addWidget(btn_restore)

        self.lbl_restore_status = QLabel("")
        self.lbl_restore_status.setStyleSheet("font-size: 11px;")
        rv.addWidget(self.lbl_restore_status)
        layout.addWidget(rest_frame)
        layout.addStretch()

    def _do_backup(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Enregistrér la sauvegarde",
            f"backup_sgc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
            "SQL (*.sql)")
        if not filepath:
            return
        try:
            cfg = db.config
            cmd = ["mysqldump",
                   f"-h{cfg['host']}", f"-u{cfg['user']}",
                   f"-p{cfg['password']}", cfg['database']]
            with open(filepath, 'w', encoding='utf-8') as f:
                result = subprocess.run(cmd, stdout=f,
                                        stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                self.lbl_backup_status.setText(
                    f"Sauvegarde reussie : {filepath}")
                self.lbl_backup_status.setStyleSheet(
                    "color: #16a34a; font-size: 11px;")
                _log_action("sauvegarde",
                            "Sauvegarde base de données effectuee")
            else:
                raise Exception(result.stderr)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Sauvegarde echouee :\n{
                    str(e)}")
            self.lbl_backup_status.setText("Échec de la sauvegarde.")
            self.lbl_backup_status.setStyleSheet(
                "color: #dc2626; font-size: 11px;")

    def _do_restore(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Choisir le fichier de sauvegarde", "", "SQL (*.sql)")
        if not filepath:
            return
        if not _confirm(self, "Confirmation",
                        "Toutes les données actuelles seront ecrasees.\n"
                        "Continuer la restauration ?"):
            return
        try:
            cfg = db.config
            cmd = ["mysql",
                   f"-h{cfg['host']}", f"-u{cfg['user']}",
                   f"-p{cfg['password']}", cfg['database']]
            with open(filepath, 'r', encoding='utf-8') as f:
                result = subprocess.run(cmd, stdin=f,
                                        stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                self.lbl_restore_status.setText("Restauration reussie !")
                self.lbl_restore_status.setStyleSheet(
                    "color: #16a34a; font-size: 11px;")
                _log_action("restauration", f"Restauration depuis {filepath}")
                QMessageBox.information(
                    self, "Succes", "Base de données restauree avec succès.")
            else:
                raise Exception(result.stderr)
        except Exception as e:
            QMessageBox.critical(self, "Erreur",
                                 f"Restauration echouee :\n{str(e)}")
            self.lbl_restore_status.setText("Échec de la restauration.")
            self.lbl_restore_status.setStyleSheet(
                "color: #dc2626; font-size: 11px;")


# ──────────────────────────────────────────────────────────────
# Onglet Journal d'activite'# ────────────────────────────────────────────

class LogsTab(QWidget):

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        header = QHBoxLayout()
        lbl = QLabel("Journal d'activite")
        lbl.setObjectName("section_title")
        btn_refresh = QPushButton("Actualiser")
        btn_refresh.setFixedWidth(100)
        btn_refresh.clicked.connect(self.load)
        btn_clear = QPushButton("Effacer les logs")
        btn_clear.setObjectName("btn_danger")
        btn_clear.setFixedWidth(150)
        btn_clear.clicked.connect(self._clear_logs)
        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(btn_refresh)
        header.addWidget(btn_clear)
        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Date", "Utilisateur", "Action", "Details"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def load(self):
        try:
            logs = db.execute_query("""
                SELECT l.created_at, u.username, l.action, l.details
                FROM logs l
                LEFT JOIN users u ON l.user_id = u.id
                ORDER BY l.created_at DESC
                LIMIT 200
            """)
        except Exception:
            logs = []

        self.table.setRowCount(0)
        action_colors = {
            'connexion': '#16a34a',
            'deconnexion': '#64748b',
            'sauvegarde': '#1976D2',
            'restauration': '#dc2626',
            'erreur': '#dc2626',
        }
        for i, log in enumerate(logs or []):
            self.table.insertRow(i)
            action = log.get('action', '')
            # Formater la date en jj-mm-aaaa hh:mm:ss
            raw_date = log.get('created_at', '')
            try:
                from datetime import datetime as _dt
                if hasattr(raw_date, 'strftime'):
                    date_str = raw_date.strftime('%d-%m-%Y %H:%M:%S')
                else:
                    date_str = _dt.strptime(
                        str(raw_date)[
                            :19], '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S')
            except Exception:
                date_str = str(raw_date)[:19]
            vals = [
                date_str,
                log.get('username') or 'Systeme',
                action,
                log.get('details') or '',
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 2:
                    item.setForeground(
                        QColor(action_colors.get(action, '#1e293b')))
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)
                self.table.setItem(i, col, item)

        if not logs:
            self.table.insertRow(0)
            item = QTableWidgetItem("Aucune activite enregistree.")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setForeground(QColor('#94a3b8'))
            self.table.setItem(0, 0, item)
            self.table.setSpan(0, 0, 1, 4)

        self.table.resizeColumnsToContents()

    def _clear_logs(self):
        if _confirm(
            self,
            "Confirmation",
                "Effacer tout le journal d'activite ?"):
            try:
                db.execute_update("DELETE FROM logs")
                self.load()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))


# ──────────────────────────────────────────────────────────────
# Dialogues
# ──────────────────────────────────────────────────────────────

class UserFormDialog(QDialog):

    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        self.is_edit = user_data is not None
        self.setWindowTitle(
            "Modifier utilisateur" if self.is_edit else "Nouvel utilisateur")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._build_ui()
        if self.is_edit:
            self._fill(user_data)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self.username_input = QLineEdit()
        self.nom_complet_input = QLineEdit()
        self.email_dlg_input = QLineEdit()
        self.email_dlg_input.setPlaceholderText("exemple@email.com")
        self.role_combo = QComboBox()
        self.role_combo.addItems(['vendeur', 'manager', 'admin'])

        for w in [
                self.username_input,
                self.nom_complet_input,
                self.email_dlg_input]:
            w.setMinimumHeight(34)

        form.addRow("Nom utilisateur *", self.username_input)
        form.addRow("Nom complet", self.nom_complet_input)
        form.addRow("Email", self.email_dlg_input)
        form.addRow("Role", self.role_combo)

        if not self.is_edit:
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_input.setMinimumHeight(34)
            self.password2_input = QLineEdit()
            self.password2_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.password2_input.setMinimumHeight(34)
            form.addRow("Mot de passe *", self.password_input)
            form.addRow("Confirmer *", self.password2_input)

        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Save).setText(
            "Enregistrer")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _fill(self, data):
        self.username_input.setText(data.get('username', ''))
        self.nom_complet_input.setText(data.get('nom_complet') or '')
        self.email_dlg_input.setText(data.get('email') or '')
        idx = self.role_combo.findText(data.get('role', 'vendeur'))
        if idx >= 0:
            self.role_combo.setCurrentIndex(idx)

    def _validate(self):
        if not self.username_input.text().strip():
            QMessageBox.warning(self, "Requis",
                                "Le nom utilisateur est obligatoire.")
            return
        if not self.is_edit:
            if not self.password_input.text():
                QMessageBox.warning(self, "Requis",
                                    "Le mot de passe est obligatoire.")
                return
            if self.password_input.text() != self.password2_input.text():
                QMessageBox.warning(self, "Erreur",
                                    "Les mots de passe ne correspondent pas.")
                return
        self.accept()

    def get_data(self):
        data = {
            'username': self.username_input.text().strip(),
            'nom_complet': self.nom_complet_input.text().strip(),
            'email': self.email_dlg_input.text().strip(),
            'role': self.role_combo.currentText(),
        }
        if not self.is_edit:
            data['password'] = self.password_input.text()
        return data


class ChangePasswordDialog(QDialog):

    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Changer le mot de passe")
        self.setMinimumWidth(380)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)
        self.new_pwd = QLineEdit()
        self.new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pwd.setMinimumHeight(34)
        self.conf_pwd = QLineEdit()
        self.conf_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.conf_pwd.setMinimumHeight(34)
        form.addRow("Nouveau mot de passe *", self.new_pwd)
        form.addRow("Confirmer *", self.conf_pwd)
        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Save).setText(
            "Enregistrer")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _validate(self):
        if not self.new_pwd.text():
            QMessageBox.warning(self, "Requis", "Entrez un mot de passe.")
            return
        if self.new_pwd.text() != self.conf_pwd.text():
            QMessageBox.warning(self, "Erreur",
                                "Les mots de passe ne correspondent pas.")
            return
        success, message = UserController.change_password(
            self.user_id, self.new_pwd.text())
        if success:
            QMessageBox.information(self, "Succes", "Mot de passe modifie.")
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", message)


# ──────────────────────────────────────────────────────────────
# Utilitaire log
# ──────────────────────────────────────────────────────────────

def _log_action(action, details=''):
    """Enregistré une action dans le journal. Ne bloque jamais l'appli."""
    try:
        user = SessionManager.get_current_user()
        user_id = user['id'] if user else None
        db.execute_update(
            "INSERT INTO logs (user_id, action, details) VALUES (%s, %s, %s)",
            (user_id, action, details))
    except Exception:
        pass

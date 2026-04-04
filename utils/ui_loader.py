# utils/ui_loader.py
# Charge les fichiers .ui créés avec Qt Designer

import os

from PyQt6 import uic
from PyQt6.QtWidgets import QWidget


def load_ui(ui_filename: str, parent: QWidget = None):
    """
    Charge un fichier .ui et retourne le widget correspondant.

    Args:
        ui_filename : Nom du fichier (ex: 'main_window.ui')
        parent      : Widget parent (optionnel)

    Usage:
        ui = load_ui('clients.ui', self)
    """
    ui_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),  # racine projet
        'views', 'ui', ui_filename
    )

    if not os.path.exists(ui_path):
        raise FileNotFoundError(f"Fichier UI introuvable : {ui_path}")

    return uic.loadUi(ui_path, parent)

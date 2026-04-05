# utils/logo.py
"""
Generateur de logo SGC en pur QPainter.
Retourne un QPixmap rectangulaire pret a l'emploi - aucun fichier image necessaire.

Design : fond bleu nuit degrade, barres de croissance, courbe de tendance,
         texte "SGC" blanc a droite, sous-titre blanc casse.
"""

from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QBrush, QColor, QFont, QLinearGradient,
    QPainter, QPainterPath, QPen, QPixmap,
)


def make_logo(size: int = 72) -> QPixmap:
    """
    Cree et retourne le logo SGC en QPixmap rectangulaire.
    `size` correspond a la hauteur ; la largeur est 2.4x la hauteur.
    """
    h = size
    w = int(size * 2.4)
    r = h * 0.14

    px = QPixmap(w, h)
    px.fill(Qt.GlobalColor.transparent)

    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # ── 1. Fond degrade bleu nuit ────────────────────────────────
    grad = QLinearGradient(0, 0, w, h)
    grad.setColorAt(0.0, QColor("#1e3a5f"))
    grad.setColorAt(1.0, QColor("#0a1628"))

    path_bg = QPainterPath()
    path_bg.addRoundedRect(QRectF(0, 0, w, h), r, r)
    p.fillPath(path_bg, QBrush(grad))

    # ── 2. Zone graphique (partie gauche ~52%) ───────────────────
    chart_left  = w * 0.05
    chart_right = w * 0.52
    chart_base  = h * 0.80
    zone_w      = chart_right - chart_left

    # Bandeau accent bleu en haut
    accent_h = max(3, int(h * 0.045))
    accent_path = QPainterPath()
    accent_path.addRoundedRect(
        QRectF(chart_left, h * 0.10, zone_w, accent_h), 2, 2)
    p.fillPath(accent_path, QBrush(QColor("#1976D2")))

    # Barres de graphique
    bars = [
        (0.00, 0.28, "#1565C0"),
        (0.18, 0.42, "#1976D2"),
        (0.36, 0.35, "#1976D2"),
        (0.54, 0.56, "#42a5f5"),
        (0.72, 0.46, "#64b5f6"),
    ]
    bar_w = zone_w * 0.13

    centers_x = []
    centers_y = []

    for x_r, h_r, color in bars:
        bx = chart_left + zone_w * 0.88 * x_r
        bh = h * h_r
        by = chart_base - bh
        bar_path = QPainterPath()
        bar_path.addRoundedRect(QRectF(bx, by, bar_w, bh), 2, 2)
        p.fillPath(bar_path, QBrush(QColor(color)))
        centers_x.append(bx + bar_w / 2)
        centers_y.append(by)

    # Courbe de tendance blanche
    pen_line = QPen(QColor(255, 255, 255, 230))
    pen_line.setWidthF(max(1.5, h * 0.028))
    pen_line.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen_line.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen_line)

    curve = QPainterPath()
    curve.moveTo(QPointF(centers_x[0], centers_y[0]))
    for i in range(1, len(centers_x)):
        cx = (centers_x[i - 1] + centers_x[i]) / 2
        curve.cubicTo(
            QPointF(cx, centers_y[i - 1]),
            QPointF(cx, centers_y[i]),
            QPointF(centers_x[i], centers_y[i]),
        )
    p.drawPath(curve)

    # Points sur la courbe
    p.setPen(QPen(QColor("#ffffff")))
    p.setBrush(QBrush(QColor("#42a5f5")))
    dot_r = max(2.5, h * 0.038)
    for cx, cy in zip(centers_x, centers_y):
        p.drawEllipse(QPointF(cx, cy), dot_r, dot_r)

    # ── 3. Separateur vertical ───────────────────────────────────
    pen_sep = QPen(QColor(255, 255, 255, 45))
    pen_sep.setWidthF(1)
    p.setPen(pen_sep)
    p.drawLine(QPointF(w * 0.54, h * 0.12), QPointF(w * 0.54, h * 0.88))

    # ── 4. Texte "SGC" - blanc pur, grand ───────────────────────
    text_left = w * 0.57
    text_w    = w - text_left - w * 0.02   # ~41% de w

    font_sgc = QFont("Arial Black", max(8, int(h * 0.36)))
    font_sgc.setBold(True)
    font_sgc.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
    p.setFont(font_sgc)
    p.setPen(QPen(QColor("#ffffff")))

    sgc_rect = QRectF(text_left, h * 0.04, text_w, h * 0.54)
    p.drawText(sgc_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, "SGC")

    # ── 5. Sous-texte - blanc casse lisible ──────────────────────
    font_sub = QFont("Segoe UI", max(5, int(h * 0.125)))
    font_sub.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0)
    p.setFont(font_sub)
    p.setPen(QPen(QColor("#cfe8ff")))

    sub_rect = QRectF(text_left, h * 0.60, text_w, h * 0.34)
    p.drawText(sub_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "Gestion Commerciale")

    p.end()
    return px

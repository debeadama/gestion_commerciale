# utils/pdf_generator.py
import os
from datetime import datetime

from database.connection import db
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as pdfcanvas

#  Couleurs
DARK = colors.HexColor('#1e293b')
BLUE = colors.HexColor('#1976D2')
LIGHT = colors.HexColor('#f8fafc')
BORDER = colors.HexColor('#e2e8f0')
GRAY = colors.HexColor('#64748b')
GREEN = colors.HexColor('#16a34a')
RED = colors.HexColor('#dc2626')
WHITE = colors.white


def get_company_info():
    params = db.execute_query("SELECT cle, valeur FROM parametres")
    return {p['cle']: p['valeur'] for p in params} if params else {}


def generate_invoice_pdf(vente: dict, details: list) -> str:
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'factures')
    os.makedirs(output_dir, exist_ok=True)

    numero = vente.get('numero_facture', 'FACTURE')
    filepath = os.path.join(output_dir, f"{numero}.pdf")

    company = get_company_info()
    company_name = company.get('nom_entreprise', 'Mon Entreprise')
    company_addr = company.get('adresse', '')
    company_tel = company.get('telephone', '')
    company_mail = company.get('email', '')

    W, H = A4
    margin = 2 * cm

    #  Canvas direct pour plus de controle
    c = pdfcanvas.Canvas(filepath, pagesize=A4)

    #  BANDE BLEUE EN-TETE
    c.setFillColor(DARK)
    c.rect(0, H - 3.5 * cm, W, 3.5 * cm, fill=1, stroke=0)

    # Nom entreprise
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 18)
    c.drawString(margin, H - 1.8 * cm, company_name)

    # Ligne bleue sous le nom
    c.setFillColor(BLUE)
    c.rect(margin, H - 2.1 * cm, 6 * cm, 0.12 * cm, fill=1, stroke=0)

    # Coordonnees entreprise
    c.setFillColor(colors.HexColor('#94a3b8'))
    c.setFont('Helvetica', 8)
    coord_parts = []
    if company_addr:
        coord_parts.append(company_addr)
    if company_tel:
        coord_parts.append(f"Tel : {company_tel}")
    if company_mail:
        coord_parts.append(f"Email : {company_mail}")
    c.drawString(margin, H - 2.7 * cm, "  |  ".join(coord_parts))

    # Mot FACTURE a droite
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 28)
    c.drawRightString(W - margin, H - 1.6 * cm, "FACTURE")

    # Numero facture
    c.setFillColor(BLUE)
    c.setFont('Helvetica-Bold', 10)
    c.drawRightString(W - margin, H - 2.3 * cm, numero)

    # INFOS FACTURE (date, vendeur)
    y = H - 4.2 * cm
    bar_h = 1.8 * cm   # hauteur de la barre
    bar_y = y - 1.4 * cm  # bas du rectangle
    bar_mid = bar_y + bar_h / 2  # centre vertical

    c.setFillColor(LIGHT)
    c.roundRect(margin, bar_y, W - 2 * margin, bar_h, 5, fill=1, stroke=0)
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.roundRect(margin, bar_y, W - 2 * margin, bar_h, 5, fill=0, stroke=1)

    col_w = (W - 2 * margin) / 3
    # Formater la date en jj-mm-aaaa
    raw_date = str(vente.get('date_vente', ''))[:10]
    try:
        from datetime import datetime as _dt
        date_display = _dt.strptime(raw_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    except Exception:
        date_display = raw_date
    infos = [
        ("Date", date_display),
        ("Vendeur", vente.get('vendeur', '')),
        ("Statut", vente.get('statut', '').upper()),
    ]
    for i, (lbl, val) in enumerate(infos):
        x = margin + i * col_w + 0.5 * cm
        # Label petit en haut (centré dans la moitié haute)
        c.setFillColor(GRAY)
        c.setFont('Helvetica', 7)
        c.drawString(x, bar_mid + 0.15 * cm, lbl.upper())
        # Valeur en gras dans la moitié basse
        if lbl == "Statut":
            color_map = {
                'PAYEE': GREEN, 'PARTIELLE': colors.HexColor('#d97706'),
                'EN_COURS': BLUE, 'ANNULEE': RED
            }
            c.setFillColor(color_map.get(val, GRAY))
        else:
            c.setFillColor(DARK)
        c.setFont('Helvetica-Bold', 11)
        c.drawString(x, bar_mid - 0.45 * cm, val)

    # BLOC CLIENT
    y -= 4.8 * cm    # espace suffisant sous la barre Date/Vendeur/Statut
    client_nom = vente.get('client_nom', '')
    client_tel = vente.get('client_tel', '') or ''
    client_mail = vente.get('client_email', '') or ''
    client_adr = vente.get('client_adresse', '') or ''
    client_vil = vente.get('client_ville', '') or ''

    c.setFillColor(BLUE)
    c.rect(margin, y + 0.2 * cm, 0.3 * cm, 2.2 * cm, fill=1, stroke=0)

    c.setFillColor(GRAY)
    c.setFont('Helvetica', 7)
    c.drawString(margin + 0.6 * cm, y + 2.1 * cm, "FACTURE DE :")

    c.setFillColor(DARK)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(margin + 0.6 * cm, y + 1.5 * cm, client_nom)

    c.setFillColor(GRAY)
    c.setFont('Helvetica', 9)
    details_client = []
    if client_adr:
        details_client.append(client_adr)
    if client_vil:
        details_client.append(client_vil)
    if client_tel:
        details_client.append(f"Tel : {client_tel}")
    if client_mail:
        details_client.append(f"Email : {client_mail}")

    for idx, line in enumerate(details_client[:3]):
        c.drawString(margin + 0.6 * cm, y + 0.9 * cm - idx * 0.4 * cm, line)

    #  TABLEAU PRODUITS
    y -= 2.5 * cm

    # En-tete tableau
    c.setFillColor(DARK)
    c.roundRect(margin, y, W - 2 * margin, 0.8 * cm, 3, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 9)

    col_widths = [0.45, 0.2, 0.15, 0.2]
    headers = ['PRODUIT', 'PRIX UNITAIRE', 'QUANTITE', 'SOUS-TOTAL']
    col_x = [margin]
    for cw in col_widths[:-1]:
        col_x.append(col_x[-1] + cw * (W - 2 * margin))

    for i, (header, cx) in enumerate(zip(headers, col_x)):
        if i == 0:
            c.drawString(cx + 0.3 * cm, y + 0.25 * cm, header)
        else:
            cx_center = cx + col_widths[i] * (W - 2 * margin) / 2
            c.drawCentredString(cx_center, y + 0.25 * cm, header)

    # Lignes produits
    y -= 0.8 * cm
    row_h = 0.75 * cm
    for idx, d in enumerate(details):
        # Fond alterne
        if idx % 2 == 0:
            c.setFillColor(WHITE)
        else:
            c.setFillColor(LIGHT)
        c.rect(margin, y - row_h + 0.1 * cm,
               W - 2 * margin, row_h, fill=1, stroke=0)

        # Bordure inferieure
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.3)
        c.line(margin, y - row_h + 0.1 * cm,
               W - margin, y - row_h + 0.1 * cm)

        c.setFillColor(DARK)
        c.setFont('Helvetica', 9)

        row_vals = [
            d.get('produit', ''),
            f"{float(d.get('prix_unitaire', 0)):.2f}",
            str(d.get('quantite', 0)),
            f"{float(d.get('sous_total', 0)):.2f}",
        ]
        for i, (val, cx) in enumerate(zip(row_vals, col_x)):
            if i == 0:
                # Tronquer si trop long
                txt = val[:45] + '...' if len(val) > 45 else val
                c.drawString(cx + 0.3 * cm, y - 0.45 * cm, txt)
            else:
                c.drawCentredString(
                    cx + col_widths[i] * (W - 2 * margin) / 2,
                    y - 0.45 * cm, val)
        y -= row_h

    #  TOTAUX
    y -= 0.5 * cm
    total = float(vente.get('montant_total', 0))
    paye = float(vente.get('montant_paye', 0))
    reste = float(vente.get('montant_reste', 0))

    totaux_x = W - margin - 7 * cm
    totaux_w = 7 * cm

    def draw_total_row(cy, label, value, bold=False, color=DARK, bg=None):
        if bg:
            c.setFillColor(bg)
            c.rect(
                totaux_x,
                cy - 0.1 * cm,
                totaux_w,
                0.65 * cm,
                fill=1,
                stroke=0)
        font = 'Helvetica-Bold' if bold else 'Helvetica'
        c.setFillColor(GRAY)
        c.setFont(font, 9)
        c.drawString(totaux_x + 0.3 * cm, cy + 0.1 * cm, label)
        c.setFillColor(color)
        c.setFont(font, 10 if bold else 9)
        c.drawRightString(totaux_x + totaux_w - 0.3 * cm, cy + 0.1 * cm, value)

    draw_total_row(y, "Total", f"{total:.2f}")
    draw_total_row(y - 0.7 * cm, "Montant payé", f"{paye:.2f}", color=GREEN)
    # Fond rouge clair pour reste
    c.setFillColor(colors.HexColor('#fee2e2'))
    c.roundRect(
        totaux_x,
        y - 1.5 * cm,
        totaux_w,
        0.7 * cm,
        3,
        fill=1,
        stroke=0)
    draw_total_row(y - 1.45 * cm, "Reste à payer",
                   f"{reste:.2f}", bold=True, color=RED)

    #  TAMPON PAYEE
    if vente.get('statut') == 'payee':
        c.saveState()
        c.translate(W * 0.65, H * 0.28)   # bas-droite de la facture
        c.rotate(35)
        c.setFillColor(colors.HexColor('#16a34a'))
        c.setStrokeColor(colors.HexColor('#16a34a'))
        c.setLineWidth(3)
        c.roundRect(-3.5 * cm, -1.2 * cm, 7 * cm, 2.4 * cm, 8,
                    fill=0, stroke=1)
        c.setFont('Helvetica-Bold', 32)
        c.setFillAlpha(0.25)
        c.drawCentredString(0, -0.5 * cm, "PAYEE")
        c.restoreState()

    #  NOTES
    notes = vente.get('notes', '')
    if notes:
        ny = max(y - 2.5 * cm, 3 * cm)
        c.setFillColor(colors.HexColor('#fef3c7'))
        c.roundRect(margin, ny - 0.5 * cm, W - 2 * margin, 1 * cm,
                    5, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#92400e'))
        c.setFont('Helvetica-Bold', 8)
        c.drawString(margin + 0.3 * cm, ny, f"Note : {notes}")

    #  PIED DE PAGE
    c.setFillColor(DARK)
    c.rect(0, 0, W, 1.2 * cm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#94a3b8'))
    c.setFont('Helvetica', 7.5)
    c.drawCentredString(
        W / 2,
        0.45 * cm,
        f"Facture generee le {
            datetime.now().strftime('%d/%m/%Y a %H:%M')} — {company_name}")

    c.save()
    return filepath

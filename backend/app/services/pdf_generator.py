import io
import os
from datetime import datetime
from typing import List

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from typing import Any
from app.services.storage import upload_buffer_to_minio

class CoselecPdfBuilder:
    """Builder générique pour tous les documents PDF de l'ERP Coselec."""
    
    def __init__(self, filename: str, title: str = "", author: str = "COSELEC", topMargin: int = 40, bottomMargin: int = 40):
        self.filename = filename
        self.buffer = io.BytesIO()
        self.doc = SimpleDocTemplate(
            self.buffer, 
            pagesize=A4, 
            rightMargin=40, leftMargin=40, 
            topMargin=topMargin, bottomMargin=bottomMargin,
            title=title,
            author=author
        )
        self.styles = getSampleStyleSheet()
        self.elements = []
    
    def add_logo(self, width: int = 80, height: int = 80, centered: bool = True, space_after: int = 20):
        logo_path = os.path.join(os.path.dirname(__file__), "../../../frontend/public/logo_coselec.jfif")
        if os.path.exists(logo_path):
            img = Image(logo_path, width=width, height=height)
            if centered:
                t = Table([[img]], colWidths=[510])
                t.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
                self.elements.append(t)
            else:
                self.elements.append(img)
        else:
            align = 1 if centered else 0
            logo_style = ParagraphStyle('LogoStyle', parent=self.styles['Normal'], fontName='Helvetica-Bold', fontSize=14, textColor=colors.red, alignment=align)
            self.elements.append(Paragraph("GROUPE<br/><b>Y</b><br/>COSELEC", logo_style))
            
        if space_after:
            self.elements.append(Spacer(1, space_after))
        return self

    def add_title(self, text: str, font_size: int = 16, space_after: int = 20, centered: bool = True):
        font_name = 'Helvetica-Bold'
        alignment = 1 if centered else 0
        style_name = f'Title_{font_size}'
        if style_name not in self.styles:
            self.styles.add(ParagraphStyle(style_name, parent=self.styles['Normal'], fontName=font_name, fontSize=font_size, alignment=alignment, spaceAfter=space_after))
        
        self.elements.append(Paragraph(text, self.styles[style_name]))
        return self

    def add_paragraph(self, text: str, bold: bool = False, alignment: int = 0, leading: int = 14, space_after: int = 10, font_size: int = 10):
        font_name = 'Helvetica-Bold' if bold else 'Helvetica'
        style_name = f'Para_{font_name}_{font_size}_{alignment}_{leading}'
        if style_name not in self.styles:
            self.styles.add(ParagraphStyle(style_name, parent=self.styles['Normal'], fontName=font_name, fontSize=font_size, alignment=alignment, leading=leading, spaceAfter=space_after))
        
        self.elements.append(Paragraph(text, self.styles[style_name]))
        return self

    def add_spacer(self, height: int = 20):
        self.elements.append(Spacer(1, height))
        return self

    def add_separator(self):
        self.elements.append(Paragraph("<br/>" + "-"*90 + "<br/><br/>", self.styles['Normal']))
        return self

    def add_table(self, data: list, col_widths: list = None, row_heights: list = None, style_commands: list = None, highlight_header: bool = True):
        t = Table(data, colWidths=col_widths, rowHeights=row_heights)
        
        base_style = [
            ('BOX', (0,0), (-1,-1), 1, colors.black),
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]
        
        if highlight_header and len(data) > 0:
            base_style.extend([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ])
            
        if style_commands:
            base_style.extend(style_commands)
            
        t.setStyle(TableStyle(base_style))
        self.elements.append(t)
        return self

    def add_signatures(self, labels: List[str], height: int = 40):
        col_width = 510 / len(labels)
        data = [labels]
        t = Table(data, colWidths=[col_width]*len(labels), rowHeights=[height])
        t.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        self.elements.append(t)
        return self
        
    def add_custom_element(self, element):
        self.elements.append(element)
        return self

    def _add_footer(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        current_date = datetime.now().strftime('%d/%m/%Y %H:%M')
        canvas.drawString(doc.leftMargin, 20, f"Généré le : {current_date}")
        page_str = f"Page {doc.page}"
        x_position = doc.pagesize[0] - doc.rightMargin
        canvas.drawRightString(x_position, 20, page_str)
        canvas.restoreState()

    def build_and_upload(self) -> str:
        self.doc.build(
            self.elements, 
            onFirstPage=self._add_footer, 
            onLaterPages=self._add_footer
        )
        self.buffer.seek(0)
        try:
            return upload_buffer_to_minio(self.buffer, self.filename)
        except Exception as e:
            print(f"Error saving PDF to cloud: {e}")
            return ""

# -----------------------------------------
# DMCAR (FUEL REQUEST) PDF GENERATOR
# -----------------------------------------

def _build_dmcar_table_data(request: Any) -> Table:
    styles = getSampleStyleSheet()
    title_p = Paragraph("DEMANDE DE CARBURANT", ParagraphStyle('TitleStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, alignment=1))
    
    logo_p = Paragraph("GROUPE<br/><b>Y</b><br/>COSELEC", ParagraphStyle('LogoStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.red, alignment=1))
    logo_path = os.path.join(os.path.dirname(__file__), "../../../frontend/public/logo_coselec.jfif")
    if os.path.exists(logo_path):
        logo_p = Image(logo_path, width=60, height=60)
        
    payload = request.payload or {}
    data = [
        [logo_p, title_p, "", "", ""],
        ["DATE:", str(payload.get('request_date', request.created_at.strftime('%Y-%m-%d'))), "", "", ""],
        ["AFFAIRE:", payload.get('affaire_no', ''), "", "", ""],
        ["DOSSIER:", payload.get('dossier_no', ''), "", "", ""],
        [f"OBJET DEPLACEMENT .......................... {payload.get('trip_purpose', '')}", "", "", "", ""],
        [f"VEHICULE .............................................. {payload.get('vehicle_plate', '')}", "", "", "", ""],
        [f"DESTINATION ........................................ {payload.get('destination', '')}", "", "", "", ""],
        [f"RELEVE KILOMETRIQUE .................... {payload.get('odometer_reading', '')}", "", "", "", ""],
        [f"NOMBRE DE JOURS ............................ {payload.get('trip_days', '')}", "", "", "", ""],
        [f"QUANTITE DE CARBURANT ............... {payload.get('fuel_quantity', '')} L", "", "", "", ""],
    ]
    
    t_main = Table(data, colWidths=[130, 95, 95, 95, 95], rowHeights=[40, 20, 20, 20, 25, 25, 25, 25, 25, 25])
    t_main.setStyle(TableStyle([
        ('SPAN', (1, 0), (4, 0)),
        ('ALIGN', (0, 0), (4, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('SPAN', (1, 1), (2, 1)), ('SPAN', (3, 1), (4, 1)),
        ('SPAN', (1, 2), (2, 2)), ('SPAN', (3, 2), (4, 2)),
        ('SPAN', (1, 3), (2, 3)), ('SPAN', (3, 3), (4, 3)),
        ('SPAN', (0, 4), (4, 4)), ('SPAN', (0, 5), (4, 5)),
        ('SPAN', (0, 6), (4, 6)), ('SPAN', (0, 7), (4, 7)),
        ('SPAN', (0, 8), (4, 8)), ('SPAN', (0, 9), (4, 9)),
        ('FONTNAME', (0, 1), (0, 9), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    return t_main

def _get_signature_cell(user_obj, fallback_name: str, prefix: str = ""):
    if not user_obj:
        return fallback_name
        
    sig_url = getattr(user_obj, 'signature_url', None)
    if sig_url:
        from app.services.storage import get_file_url_from_minio
        try:
            full_url = get_file_url_from_minio(sig_url)
            # Use reportlab Image
            from reportlab.platypus import Image as RLImage
            # Adjust width and height to fit in the box (e.g., 80x40)
            return [prefix, RLImage(full_url, width=80, height=40)]
        except Exception:
            pass
            
    name = getattr(user_obj, 'name', fallback_name)
    return f"{prefix}\n{name}" if prefix else name

def _build_dmcar_sig_table(request: Any) -> Table:
    employee_cell = _get_signature_cell(getattr(request, 'requester', None), "")
    manager_cell = _get_signature_cell(getattr(request, 'manager_validator', None), "En attente", "Validé par:")
    finance_cell = _get_signature_cell(getattr(request, 'finance_validator', None), "En attente", "Validé par:")
    
    sig_data = [
        ["DEMANDEUR", "RESP. SERVICE", "VISA DIRECTION"],
        [
            employee_cell,
            manager_cell,
            finance_cell
        ]
    ]
    t_sig = Table(sig_data, colWidths=[170, 170, 170], rowHeights=[20, 50])
    t_sig.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return t_sig

def generate_dmcar_pdf(request: Any) -> str:
    filename = f"fuel_requests/DMCAR_{request.id:04d}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    builder = CoselecPdfBuilder(filename, topMargin=30, bottomMargin=30)
    
    builder.add_custom_element(_build_dmcar_table_data(request))
    builder.add_custom_element(_build_dmcar_sig_table(request))
    builder.add_separator()
    builder.add_custom_element(_build_dmcar_table_data(request))
    builder.add_custom_element(_build_dmcar_sig_table(request))
    
    return builder.build_and_upload()

# -----------------------------------------
# CAISSE PDF GENERATOR
# -----------------------------------------

def generate_caisse_pdf(data: dict) -> str:
    filename = f"caisse_vouchers/CAISSE_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    builder = CoselecPdfBuilder(filename)
    
    builder.add_logo()
    builder.add_title('COSELEC &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; "A"', font_size=12, space_after=10)
    
    dep_header = Paragraph("PIECE DE CAISSE / DEPENSE", ParagraphStyle('H', parent=builder.styles['Normal'], fontName='Helvetica-Bold', fontSize=10, alignment=1, backColor=colors.lightgrey))
    builder.add_table([[dep_header]], col_widths=[510], highlight_header=False, style_commands=[('BOTTOMPADDING', (0,0), (-1,-1), 5), ('TOPPADDING', (0,0), (-1,-1), 5)])
    
    builder.add_spacer(10)
    builder.add_paragraph(f"<b>NUM :</b> {data.get('num', '')}", font_size=10, space_after=2)
    builder.add_paragraph(f"<b>N°AFFAIRE :</b> {data.get('affaire', '')}", font_size=10, space_after=2)
    builder.add_paragraph(f"<b>N°CIA :</b> {data.get('cia', '')}", font_size=10, space_after=2)
    builder.add_paragraph(f"<b>MOYEN DE PAIEMENT :</b> {data.get('payment_method', '') or 'Non spécifié'}", font_size=10, space_after=10)
    
    depenses = data.get("depenses", [])
    t_depense_data = [["DATE", "DESIGNATION", "MONTANT"]]
    num_rows = max(4, len(depenses))
    for i in range(num_rows):
        if i < len(depenses):
            t_depense_data.append([depenses[i].get("date", ""), depenses[i].get("designation", ""), depenses[i].get("montant", "")])
        else:
            t_depense_data.append(["", "", ""])
            
    builder.add_table(t_depense_data, col_widths=[80, 330, 100], row_heights=[20] + [30]*num_rows, style_commands=[('ALIGN', (0,0), (-1,-1), 'CENTER')])
    builder.add_spacer(20)
    
    rec_header = Paragraph("PIECE DE CAISSE / RECETTE", ParagraphStyle('H', parent=builder.styles['Normal'], fontName='Helvetica-Bold', fontSize=10, alignment=1, backColor=colors.lightgrey))
    builder.add_table([[rec_header]], col_widths=[510], highlight_header=False, style_commands=[('BOTTOMPADDING', (0,0), (-1,-1), 5), ('TOPPADDING', (0,0), (-1,-1), 5)])
    builder.add_spacer(10)
    
    recettes = data.get("recettes", [])
    t_recette_data = [["DATE", "DESIGNATION", "MONTANT"]]
    num_rec_rows = max(4, len(recettes))
    for i in range(num_rec_rows):
        if i < len(recettes):
            t_recette_data.append([recettes[i].get("date", ""), recettes[i].get("designation", ""), recettes[i].get("montant", "")])
        else:
            t_recette_data.append(["", "", ""])
            
    builder.add_table(t_recette_data, col_widths=[80, 330, 100], row_heights=[20] + [30]*num_rec_rows, style_commands=[('ALIGN', (0,0), (-1,-1), 'CENTER')])
    builder.add_spacer(30)
    
    builder.add_signatures(["Service\nDemandeur", "Visa contrôleur de\ngestion", "Visa D.G.A", "Visa D.G"])
    
    return builder.build_and_upload()

# -----------------------------------------
# LEAVE CERTIFICATE PDF GENERATOR
# -----------------------------------------

def generate_leave_certificate(leave_request, employee) -> str:
    emp_name = f"{employee.first_name} {employee.last_name}" if hasattr(employee, 'first_name') else employee.name
    filename = f"leave_certificates/conge_{emp_name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    builder = CoselecPdfBuilder(filename)
    builder.add_logo(space_after=30)
    builder.add_title("ATTESTATION DE CONGE", space_after=20)
    
    content = f"""
    Nous soussignés, la Direction des Ressources Humaines de COSELEC, attestons par la présente que :<br/><br/>
    <b>M./Mme {emp_name}</b>, employé(e) au sein de notre structure, bénéficie d'un congé de type <b>{leave_request.leave_type}</b>.<br/><br/>
    Ce congé est accordé pour la période allant du <b>{leave_request.start_date.strftime('%d/%m/%Y')}</b> au <b>{leave_request.end_date.strftime('%d/%m/%Y')}</b> inclus.<br/><br/>
    """
    if getattr(leave_request, 'reason', None):
        content += f"<b>Motif :</b> {leave_request.reason}<br/><br/>"
        
    content += "La présente attestation est délivrée pour servir et valoir ce que de droit."
    
    builder.add_paragraph(content, font_size=12, leading=18, space_after=40)
    builder.add_paragraph(f"Fait à Dakar, le {datetime.now().strftime('%d/%m/%Y')}", alignment=2, space_after=40)
    builder.add_paragraph("La Direction des Ressources Humaines", bold=True, font_size=12, alignment=2)
    
    return builder.build_and_upload()

# -----------------------------------------
# PURCHASE ORDER PDF GENERATOR
# -----------------------------------------

def generate_purchase_order_pdf(order) -> str:
    filename = f"purchase_orders/BC_{order.id:04d}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    builder = CoselecPdfBuilder(filename, title=f"Bon de Commande BC-{order.id:04d}")
    
    builder.add_logo(space_after=20)
    builder.add_title(f"BON DE COMMANDE N° BC-{order.id:04d}", space_after=10)
    
    info_data = [
        [Paragraph("<b>Date:</b>", builder.styles['Normal']), Paragraph(order.created_at.strftime('%d/%m/%Y'), builder.styles['Normal'])],
        [Paragraph("<b>Statut:</b>", builder.styles['Normal']), Paragraph(order.status, builder.styles['Normal'])],
    ]
    if getattr(order, 'supplier', None):
        info_data.append([Paragraph("<b>Fournisseur:</b>", builder.styles['Normal']), Paragraph(order.supplier.name, builder.styles['Normal'])])
        info_data.append([Paragraph("<b>Code Fournisseur:</b>", builder.styles['Normal']), Paragraph(order.supplier.code or "-", builder.styles['Normal'])])

    if getattr(order, 'purchase_request', None) and getattr(order.purchase_request, 'project', None):
        info_data.append([Paragraph("<b>Projet:</b>", builder.styles['Normal']), Paragraph(order.purchase_request.project.nom, builder.styles['Normal'])])

    builder.add_table(info_data, col_widths=[100, 410], highlight_header=False, style_commands=[
        ('BOX', (0,0), (-1,-1), 0, colors.white), ('INNERGRID', (0,0), (-1,-1), 0, colors.white),
        ('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 5), ('ALIGN', (0,0), (-1,-1), 'LEFT')
    ])
    builder.add_spacer(20)
    
    line_data = [["Désignation", "Quantité", "Prix Unitaire", "Total"]]
    if getattr(order, 'lines', []) and len(order.lines) > 0:
        for line in order.lines:
            if line.designation:
                product_name = line.designation
            else:
                product_name = line.product.designation if getattr(line, 'product', None) else f"Produit #{line.product_id}"
            line_data.append([
                product_name,
                str(line.quantity),
                f"{line.unit_price:,.0f} XOF",
                f"{(line.quantity * line.unit_price):,.0f} XOF"
            ])
    else:
        line_data.append(["-", "-", "-", "-"])
        
    subtotal = float(order.total_amount or 0)
    vat_amount = subtotal * 0.18
    total_ttc = subtotal + vat_amount

    line_data.append(["", "", "Sous-total HT:", f"{subtotal:,.0f} XOF"])
    line_data.append(["", "", "TVA (18%):", f"{vat_amount:,.0f} XOF"])
    line_data.append(["", "", "Total TTC:", f"{total_ttc:,.0f} XOF"])
    
    builder.add_table(line_data, col_widths=[240, 70, 100, 100], highlight_header=True, style_commands=[
        ('ALIGN', (1,1), (-1,-4), 'CENTER'),
        ('FONTNAME', (2,-3), (2,-1), 'Helvetica-Bold'),
        ('FONTNAME', (3,-3), (3,-1), 'Helvetica-Bold'),
        ('ALIGN', (2,-3), (3,-1), 'RIGHT'),
        ('BACKGROUND', (2,-1), (3,-1), colors.lightgrey),
        ('BOX', (2,-3), (3,-1), 1, colors.black),
        ('INNERGRID', (2,-3), (3,-1), 0.25, colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,0), 1, colors.black),
        ('INNERGRID', (0,0), (-1,-4), 0.25, colors.black),
        ('BOX', (0,0), (-1,-4), 1, colors.black),
    ])
    builder.add_spacer(20)
    
    builder.add_paragraph("<b>Conditions de Paiement :</b> À 30 jours fin de mois.", font_size=9)
    builder.add_paragraph("<b>Modalités de Livraison :</b> Selon les conditions spécifiées dans notre contrat cadre.", font_size=9, space_after=40)
    
    builder.add_signatures(["Acheteur", "Direction", "Fournisseur"])
    
    return builder.build_and_upload()

# -----------------------------------------
# PROJECT REPORT PDF GENERATOR
# -----------------------------------------

def generate_project_report_pdf(project) -> str:
    filename = f"project_reports/Rapport_Projet_{project.code}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    builder = CoselecPdfBuilder(filename)
    
    builder.add_logo(space_after=20)
    builder.add_title(f"RAPPORT DE PROJET : {project.nom.upper()}", space_after=10)
    
    info_data = [
        [Paragraph("<b>Code Projet:</b>", builder.styles['Normal']), Paragraph(project.code, builder.styles['Normal'])],
        [Paragraph("<b>Statut:</b>", builder.styles['Normal']), Paragraph(project.status.value if hasattr(project.status, 'value') else str(project.status), builder.styles['Normal'])],
        [Paragraph("<b>Type:</b>", builder.styles['Normal']), Paragraph(project.project_type or "-", builder.styles['Normal'])],
    ]
    if getattr(project, 'chef_projet', None):
        info_data.append([Paragraph("<b>Chef de Projet:</b>", builder.styles['Normal']), Paragraph(f"{project.chef_projet.first_name} {project.chef_projet.last_name}", builder.styles['Normal'])])
    if getattr(project, 'client', None):
        info_data.append([Paragraph("<b>Client:</b>", builder.styles['Normal']), Paragraph(project.client.name, builder.styles['Normal'])])

    info_data.append([Paragraph("<b>Date Début Prévue:</b>", builder.styles['Normal']), Paragraph(project.date_debut_estimee.strftime('%d/%m/%Y') if project.date_debut_estimee else "-", builder.styles['Normal'])])
    info_data.append([Paragraph("<b>Date Fin Prévue:</b>", builder.styles['Normal']), Paragraph(project.date_fin_prevue.strftime('%d/%m/%Y') if project.date_fin_prevue else "-", builder.styles['Normal'])])

    builder.add_table(info_data, col_widths=[150, 360], highlight_header=False, style_commands=[
        ('BOX', (0,0), (-1,-1), 0, colors.white), ('INNERGRID', (0,0), (-1,-1), 0, colors.white),
        ('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 5), ('ALIGN', (0,0), (-1,-1), 'LEFT')
    ])
    builder.add_spacer(20)
    
    builder.add_title("Aperçu Financier", font_size=14, space_after=10, centered=False)
    budget_data = [
        ["Budget Estimé", "Budget Engagé", "Reste à Engager"],
        [f"{project.budget_estime or 0} XOF", f"{project.budget_engage or 0} XOF", f"{(project.budget_estime or 0) - (project.budget_engage or 0)} XOF"]
    ]
    builder.add_table(budget_data, col_widths=[170, 170, 170], style_commands=[
        ('BOTTOMPADDING', (0,0), (-1,-1), 8), ('TOPPADDING', (0,0), (-1,-1), 8)
    ])
    builder.add_spacer(20)
    
    builder.add_title("Jalons & Tâches", font_size=14, space_after=10, centered=False)
    milestone_data = [["Nom du Jalon", "Date", "Statut"]]
    if getattr(project, 'milestones', []):
        for m in project.milestones:
            m_status = m.status.value if hasattr(m.status, 'value') else str(m.status)
            milestone_data.append([
                m.title,
                m.due_date.strftime('%d/%m/%Y') if m.due_date else "-",
                m_status
            ])
    else:
        milestone_data.append(["Aucun jalon défini", "-", "-"])
        
    builder.add_table(milestone_data, col_widths=[250, 130, 130], style_commands=[
        ('BOTTOMPADDING', (0,0), (-1,-1), 8), ('TOPPADDING', (0,0), (-1,-1), 8)
    ])
    
    builder.add_spacer(40)
    builder.add_paragraph(f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", alignment=2, font_size=8)
    
    return builder.build_and_upload()

# -----------------------------------------
# BANK VOUCHER PDF GENERATOR
# -----------------------------------------

def generate_bank_voucher_pdf(voucher, allocations) -> str:
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    
    filename = f"bank_vouchers/PB_{voucher.id:04d}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    builder = CoselecPdfBuilder(filename, title=f"Pièce de Banque N° {voucher.id}")
    
    builder.add_logo(space_after=10)
    builder.add_title("PIECES DE BANQUE", font_size=18, space_after=20)
    
    info_data = [
        ["Numéro d'ordre", str(voucher.id)],
        ["Banque", voucher.bank_name],
        ["Numéro chèque:", voucher.check_number],
        ["Date", voucher.date.strftime('%d/%m/%Y')],
        ["Libellé", voucher.description],
        ["Num période", voucher.period_num],
    ]
    
    builder.add_table(info_data, col_widths=[120, 390], highlight_header=False, style_commands=[
        ('BOX', (0,0), (-1,-1), 0, colors.white),
        ('INNERGRID', (0,0), (-1,-1), 0, colors.white),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOX', (1,0), (1,-1), 0.5, colors.lightgrey),
        ('BACKGROUND', (1,0), (1,-1), colors.HexColor('#F8F9FA')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
    ])
    builder.add_spacer(10)
    
    yellow = colors.HexColor('#E5C765')
    montant_str = f"{voucher.amount_in_numbers:,.0f}".replace(',', ' ')
    
    dest_p = Paragraph(f"<b><i>{voucher.recipient}</i></b>", builder.styles['Normal'])
    montant_p = Paragraph(f"<b><i>{montant_str}</i></b>", builder.styles['Normal'])
    lettres_p = Paragraph(f"<b><i>{voucher.amount_in_letters}</i></b>", builder.styles['Normal'])
    
    yellow_data = [
        ["Destinataire", dest_p, "", ""],
        ["Montant en chiffre:", montant_p, "Devise:", voucher.currency],
        ["Montant en lettres:", lettres_p, "", ""]
    ]
    
    builder.add_table(yellow_data, col_widths=[120, 150, 60, 180], highlight_header=False, style_commands=[
        ('BOX', (0,0), (-1,-1), 0, colors.white), 
        ('INNERGRID', (0,0), (-1,-1), 0, colors.white),
        ('BACKGROUND', (1,0), (3,-1), yellow),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,1), (2,1), 'Helvetica-Bold'),
        ('SPAN', (1,0), (3,0)),
        ('SPAN', (1,2), (3,2)),
        ('ALIGN', (1,1), (1,1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ])
    builder.add_spacer(20)

    header_alloc = Paragraph("<b>IMPUTATION ANALYTIQUE</b>", ParagraphStyle('AllocH', parent=builder.styles['Normal'], alignment=1, fontSize=9, textColor=colors.maroon))
    builder.add_table([[header_alloc]], col_widths=[510], highlight_header=False, style_commands=[
        ('BACKGROUND', (0,0), (0,0), colors.HexColor('#DFD3C3')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.black)
    ])
    
    alloc_table_data = [
        ["Code du centre", "désignation du centre", "client", "Compte analytique", "Montant"]
    ]
    for alloc in allocations:
        # Check if alloc is a Pydantic model or SQLAlchemy model
        code = getattr(alloc, 'cost_center_code', '')
        name = getattr(alloc, 'cost_center_name', '')
        client = getattr(alloc, 'client', '')
        account = getattr(alloc, 'analytical_account', '')
        amount = getattr(alloc, 'amount', 0)
        
        alloc_table_data.append([
            code,
            name,
            client or "",
            account,
            f"{amount:,.0f}".replace(',', ' ')
        ])
        
    builder.add_table(alloc_table_data, col_widths=[90, 140, 100, 110, 70], highlight_header=False, style_commands=[
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F4F4F4')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ])
    
    builder.add_spacer(40)
    
    builder.add_signatures([
        "Visa réception\nde chèque", 
        "Visa de Contrôle\nde gestion", 
        "Visa DGA", 
        "Visa DG"
    ])

    return builder.build_and_upload()

# -----------------------------------------
# GESTION MATERIEL / INVENTAIRE PDF
# -----------------------------------------
from typing import Any

def _build_inventory_header(title: str, doc_ref: str, form_number: str) -> Table:
    """Standard header: Left=Logo, Center=Title, Right=Doc Ref & Form Number in red"""
    styles = getSampleStyleSheet()
    
    # Left: Logo
    logo_style = ParagraphStyle('LogoStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, textColor=colors.red)
    left_p = Paragraph("GROUPE<br/><b>Y</b><br/>COSELEC", logo_style)
    
    # Center: Title
    title_p = Paragraph(f"<b>{title}</b>", ParagraphStyle('TitleStyle', parent=styles['Normal'], alignment=1, fontSize=14))
    
    # Right: Ref
    ref_style = ParagraphStyle('RefStyle', parent=styles['Normal'], alignment=2, textColor=colors.red, fontSize=10, fontName='Helvetica-Bold')
    right_p = Paragraph(f"{doc_ref}<br/>{form_number}", ref_style)
    
    t = Table([[left_p, title_p, right_p]], colWidths=[100, 310, 100])
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 1, colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
    ]))
    return t

def _build_excel_table(headers: List[str], data: List[List[Any]], col_widths: List[int]) -> Table:
    table_data = [headers] + data
    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
        ('BOX', (0,0), (-1,-1), 0.25, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    return t

def generate_stock_release_pdf(movement_id: int, movement_data: Any) -> str:
    filename = f"inventory/FICHE_SORTIE_{movement_id:04d}_{datetime.now().strftime('%Y%m%d%H%M')}.pdf"
    builder = CoselecPdfBuilder(filename, topMargin=30, bottomMargin=30)
    
    # Header
    header = _build_inventory_header("FICHE DE SORTIE MATÉRIEL", "COS-AA-FO-005-V00", f"N° FS-{movement_id:04d}")
    builder.add_custom_element(header)
    builder.add_custom_element(Spacer(1, 20))
    
    # Table: Références | Désignations | Qtés demandées | Qtés livrées | Observations
    headers = ["Références", "Désignations", "Qtés demandées", "Qtés livrées", "Observations"]
    data = []
    # Using generic movement_data mapping
    items = getattr(movement_data, 'items', [])
    for item in items:
        data.append([
            item.get('ref', ''),
            item.get('designation', ''),
            str(item.get('qty_req', 0)),
            str(item.get('qty_del', 0)),
            item.get('obs', '')
        ])
    if not data:
        data.append(["-", "-", "-", "-", "-"])
        
    t_data = _build_excel_table(headers, data, [80, 190, 80, 80, 80])
    builder.add_custom_element(t_data)
    builder.add_custom_element(Spacer(1, 30))
    
    # Signatures: Visa du Magasinier (à gauche) | Visa du Chef de Projet (à droite)
    builder.add_signatures(["Visa du Magasinier", "Visa du Chef de Projet"], height=60)
    
    return builder.build_and_upload()

def generate_reception_control_pdf(reception_id: int, reception_data: Any) -> str:
    filename = f"inventory/CONTROLE_RECEPTION_{reception_id:04d}_{datetime.now().strftime('%Y%m%d%H%M')}.pdf"
    builder = CoselecPdfBuilder(filename, topMargin=30, bottomMargin=30)
    
    header = _build_inventory_header("FORMULAIRE DE CONTRÔLE DE RÉCEPTION", "COS-AA-FO-006-V00", f"N° CR-{reception_id:04d}")
    builder.add_custom_element(header)
    builder.add_custom_element(Spacer(1, 15))
    
    # Meta infos
    styles = getSampleStyleSheet()
    meta_text = (
        f"<b>Date de livraison :</b> {getattr(reception_data, 'date', '')} &nbsp;&nbsp;&nbsp; <b>Heure :</b> {getattr(reception_data, 'time', '')}<br/>"
        f"<b>Fournisseur :</b> {getattr(reception_data, 'supplier', '')}<br/>"
        f"<b>Réf Commande (PO) :</b> {getattr(reception_data, 'po_ref', '')} &nbsp;&nbsp;&nbsp; <b>N° BL/Facture :</b> {getattr(reception_data, 'bl_ref', '')}"
    )
    meta_p = Paragraph(meta_text, styles['Normal'])
    builder.add_custom_element(meta_p)
    builder.add_custom_element(Spacer(1, 15))
    
    # Table: Références | Désignations | Qtés commandées | Qtés livrées | Conforme | Remarques
    headers = ["Références", "Désignations", "Qtés CMD", "Qtés Livrées", "Conforme", "Remarques"]
    data = []
    lines = getattr(reception_data, 'lines', [])
    for line in lines:
        data.append([
            line.get('ref', ''),
            line.get('designation', ''),
            str(line.get('qty_ord', 0)),
            str(line.get('qty_del', 0)),
            "OUI" if line.get('compliant') else "NON",
            line.get('notes', '')
        ])
    if not data:
        data.append(["-", "-", "-", "-", "-", "-"])
        
    t_data = _build_excel_table(headers, data, [70, 160, 60, 60, 60, 100])
    builder.add_custom_element(t_data)
    builder.add_custom_element(Spacer(1, 30))
    
    # Signatures
    builder.add_signatures(["Visa du Magasinier", "Visa du Chef de Projet"], height=60)
    
    return builder.build_and_upload()

def generate_material_request_pdf(request_id: int, request_data: Any) -> str:
    filename = f"inventory/DEMANDE_MATERIEL_{request_id:04d}_{datetime.now().strftime('%Y%m%d%H%M')}.pdf"
    builder = CoselecPdfBuilder(filename, topMargin=30, bottomMargin=30)
    
    header = _build_inventory_header("FICHE DE DEMANDE / RETOUR MATÉRIEL", "COS-AA-FO-007-V00", f"N° DM-{request_id:04d}")
    builder.add_custom_element(header)
    builder.add_custom_element(Spacer(1, 15))
    
    # Meta infos
    styles = getSampleStyleSheet()
    meta_text = (
        f"<b>Date :</b> {getattr(request_data, 'date', '')}<br/>"
        f"<b>Demandée par :</b> {getattr(request_data, 'requester', '')} &nbsp;&nbsp;&nbsp; <b>Retournée par :</b> {getattr(request_data, 'returner', '')}<br/>"
        f"<b>Projet / Processus :</b> {getattr(request_data, 'project', '')}"
    )
    meta_p = Paragraph(meta_text, styles['Normal'])
    builder.add_custom_element(meta_p)
    builder.add_custom_element(Spacer(1, 15))
    
    # Table
    headers = ["Références", "Désignations", "Qtés demandées", "Qtés livrées", "Observations"]
    data = []
    items = getattr(request_data, 'items', [])
    for item in items:
        data.append([
            item.get('ref', ''),
            item.get('designation', ''),
            str(item.get('qty_req', 0)),
            str(item.get('qty_del', 0)),
            item.get('obs', '')
        ])
    if not data:
        data.append(["-", "-", "-", "-", "-"])
        
    t_data = _build_excel_table(headers, data, [80, 190, 80, 80, 80])
    builder.add_custom_element(t_data)
    builder.add_custom_element(Spacer(1, 30))
    
    # Signatures
    builder.add_signatures(["Magasinier", "Demandeur", "Chef de Projet"], height=60)
    
    return builder.build_and_upload()

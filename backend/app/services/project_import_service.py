import io
import re
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from app.models.project.milestone import ProjectMilestone, MilestoneStatus
from app.models.project.task import Task, TaskPriority, TaskStatus
from app.modules.stock.models.stock import Stock, StockType
from app.modules.stock.models.warehouse import Warehouse
from app.modules.stock.models.product import Product
from app.modules.stock.models.category import Category
from app.modules.users.models.user import User
from app.modules.stock.models.partner import Partner
from app.models.project.budget import ProjectBudget
from app.models.project.payment_milestone import PaymentMilestone
from app.models.project.project import Project


# ── Helpers ──────────────────────────────────────────────────────────────────

def _clean_num(val) -> float:
    """Parse a cell value that may contain spaces, 'XOF', commas, etc."""
    try:
        s = str(val).replace(" ", "").replace("\u202f", "").replace(",", ".").replace("XOF", "").strip()
        return float(s)
    except Exception:
        return 0.0


def _norm(val) -> str:
    """Normalise a cell value to a stripped uppercase string."""
    return str(val).strip().upper()


def _cell_str(val) -> str:
    """Return a clean string or '' for NaN/None."""
    s = str(val).strip()
    return "" if s.upper() in ("NAN", "NONE", "") else s


# Regex to match column headers for each section
_REGION_RE      = re.compile(r"R[ÉE]GION", re.IGNORECASE)
_DEPT_RE        = re.compile(r"D[ÉE]P(ARTEMENT)?", re.IGNORECASE)
_COMMUNE_RE     = re.compile(r"COMMUNE", re.IGNORECASE)
_LOCALITE_RE    = re.compile(r"LOCALIT[ÉE]", re.IGNORECASE)
_MONTANT_RE     = re.compile(r"MONTANT\s*TOTAL", re.IGNORECASE)
_DECOMPTE_RE    = re.compile(r"D[ÉE]COMPTE|D[ÉE]C\b", re.IGNORECASE)
_PRESTATAIRE_RE = re.compile(r"PRESTATAIRE", re.IGNORECASE)
_PT_BETON_RE    = re.compile(r"PT\s*B[ÉE]TON", re.IGNORECASE)
_PT_CIMENT_RE   = re.compile(r"PT\s*CIMENT", re.IGNORECASE)
_GRUE_RE        = re.compile(r"LOCATION\s*GRUE|GRUE", re.IGNORECASE)
_NBRE_RE        = re.compile(r"NBRE", re.IGNORECASE)
_PU_RE          = re.compile(r"PU\s*TTC", re.IGNORECASE)
_TRANSPORT_RE   = re.compile(r"TRANSPORT", re.IGNORECASE)


class ProjectImportService:
    def __init__(self, db: Session, project_id: int):
        self.db = db
        self.project_id = project_id

        default_user = self.db.query(User).first()
        if not default_user:
            raise HTTPException(status_code=400, detail="Aucun utilisateur trouvé pour être défini comme auteur des tâches.")
        self.default_user_id = default_user.id

    def _clear_existing_project_data(self):
        self.db.query(Task).filter(Task.project_id == self.project_id).delete()
        self.db.query(ProjectMilestone).filter(ProjectMilestone.project_id == self.project_id).delete()
        self.db.query(ProjectBudget).filter(ProjectBudget.project_id == self.project_id).delete()
        self.db.query(PaymentMilestone).filter(PaymentMilestone.project_id == self.project_id).delete()
        self.db.query(Stock).filter(Stock.project_id == self.project_id).delete()
        self.db.flush()

    def import_excel(self, file: UploadFile):
        self._clear_existing_project_data()
        content = file.file.read()

        try:
            excel_file = pd.ExcelFile(io.BytesIO(content))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erreur de lecture du fichier Excel: {str(e)}")

        summary = {
            "parsed_milestones": 0,
            "parsed_tasks": 0,
            "parsed_budgets": 0,
            "parsed_payment_milestones": 0,
            "parsed_stock_requirements": 0,
            "errors_or_warnings": []
        }

        planning_df = None
        budget_df = None
        planning_sheet_name = None

        for sheet_name in excel_file.sheet_names:
            name_upper = sheet_name.upper()
            if "PLANNING" in name_upper or "TACHE" in name_upper:
                planning_df = excel_file.parse(sheet_name=sheet_name, header=None)
                planning_sheet_name = sheet_name
            elif any(k in name_upper for k in ("BUDGET", "RECAP", "FINANCE", "CONTRAT")):
                budget_df = excel_file.parse(sheet_name=sheet_name, header=None)

        if planning_df is not None:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
            ws = wb[planning_sheet_name]
            self._process_planning(planning_df, ws, summary)
        else:
            summary["errors_or_warnings"].append("Onglet Planning introuvable.")

        if budget_df is not None:
            self._process_budgets(budget_df, summary)
        else:
            summary["errors_or_warnings"].append("Onglet Budgets introuvable.")

        return summary

    # ── Planning processing (unchanged logic) ─────────────────────────────────

    def _process_planning(self, df: pd.DataFrame, ws, summary: dict):
        designation_col = -1
        header_row = -1

        for i, row in df.iterrows():
            for j, val in enumerate(row):
                if str(val).strip().upper() == "DESIGNATION":
                    designation_col = j
                    header_row = i
                    break
            if header_row != -1:
                break

        if header_row == -1:
            summary["errors_or_warnings"].append("Colonne DESIGNATION introuvable dans le Planning.")
            return

        gantt_cols = list(range(designation_col + 1, len(df.columns)))

        project = self.db.query(Project).filter(Project.id == self.project_id).first()
        base_date = project.date_debut_estimee if project and project.date_debut_estimee else datetime.utcnow().date()

        current_milestone = None
        order_idx = 0

        for i in range(header_row + 1, len(df)):
            row = df.iloc[i]
            designation = str(row.get(designation_col, "")).strip()

            if not designation or designation.upper() == 'NAN':
                continue

            is_milestone = designation.isupper()

            start_offset = -1
            end_offset = -1

            for offset_idx, c in enumerate(gantt_cols):
                val = row.get(c)
                has_value = pd.notna(val) and str(val).strip() != '' and str(val).strip().upper() != 'NAN'

                cell = ws.cell(row=i + 1, column=c + 1)
                has_color = False
                if cell.fill and cell.fill.patternType == 'solid':
                    if cell.fill.fgColor:
                        if cell.fill.fgColor.rgb and cell.fill.fgColor.rgb not in ('FFFFFFFF', '00000000'):
                            has_color = True
                        elif getattr(cell.fill.fgColor, 'theme', None) is not None:
                            has_color = True
                        elif getattr(cell.fill.fgColor, 'type', None) == 'indexed' and getattr(cell.fill.fgColor, 'indexed', None) not in (64, 65):
                            has_color = True

                if has_value or has_color:
                    if start_offset == -1:
                        start_offset = offset_idx
                    end_offset = offset_idx

            if start_offset == -1:
                start_offset = 0
                end_offset = 0

            start_date = base_date + timedelta(days=7 * start_offset)
            due_date = base_date + timedelta(days=7 * (end_offset + 1))

            if is_milestone:
                ms = ProjectMilestone(
                    project_id=self.project_id,
                    title=designation[:255],
                    order_index=order_idx,
                    due_date=due_date
                )
                self.db.add(ms)
                self.db.flush()
                current_milestone = ms
                summary["parsed_milestones"] += 1
                order_idx += 1
            else:
                task = Task(
                    title=designation[:200],
                    project_id=self.project_id,
                    milestone_id=current_milestone.id if current_milestone else None,
                    author_id=self.default_user_id,
                    priority=TaskPriority.MEDIUM,
                    status=TaskStatus.TODO,
                    start_date=start_date,
                    due_date=due_date,
                )
                self.db.add(task)
                summary["parsed_tasks"] += 1

        self.db.flush()

    # ── Budget / Récap processing ──────────────────────────────────────────────

    def _process_budgets(self, df: pd.DataFrame, summary: dict):
        """
        Parse the Récap Budget sheet.

        Left main table  (per row = one partner × one localité):
          PRESTATAIRES | RÉGION | DÉPARTEMENT | COMMUNE | LOCALITÉ |
          MONTANT TOTAL | Décompte N°1 … N°5

        Right panel (per partner row, same row index):
          PRESTATAIRES | PT BÉTON | LOCATION GRUE | NBRE | PU TTC | TOTAL TRANSPORT
        """
        # ── 1.  Find the header rows ──────────────────────────────────────────
        # We look for the row containing "PRESTATAIRES" + "MONTANT TOTAL"
        # as the left-table header, and separately the row with "PT BÉTON" or
        # "LOCATION GRUE" for the right panel.

        left_header_row   = -1
        right_header_row  = -1

        # Left-table column indices
        col_prestataire_L = -1
        col_region        = -1
        col_dept          = -1
        col_commune       = -1
        col_localite      = -1
        col_montant       = -1
        col_decomptes     = []    # list of (col_index, decompte_label)

        # Right-panel column indices
        col_prestataire_R = -1
        col_pt_beton      = -1
        col_pt_ciment     = -1
        col_grue          = -1
        col_nbre          = -1
        col_pu            = -1
        col_transport     = -1

        # Scan every row for header keywords
        # Scan every row for header keywords. Since headers can be merged across rows,
        # we accumulate column indices across all header rows.
        for i, row in df.iterrows():
            vals = [_norm(v) for v in row]

            prestataire_indices = [j for j, v in enumerate(vals) if _PRESTATAIRE_RE.search(v)]
            montant_indices     = [j for j, v in enumerate(vals) if _MONTANT_RE.search(v)]
            beton_found         = any(_PT_BETON_RE.search(v) for v in vals)
            ciment_found        = any(_PT_CIMENT_RE.search(v) for v in vals)
            grue_found          = any(_GRUE_RE.search(v) for v in vals)
            transport_found     = any(_TRANSPORT_RE.search(v) for v in vals)
            
            is_header_row = (prestataire_indices or montant_indices or beton_found or ciment_found or grue_found or transport_found)

            if is_header_row:
                if prestataire_indices and montant_indices:
                    left_header_row = i
                    if col_prestataire_L == -1:
                        col_prestataire_L = prestataire_indices[0]
                    if col_montant == -1:
                        col_montant = montant_indices[0]

                for j, v in enumerate(vals):
                    if _REGION_RE.search(v) and col_region == -1:
                        col_region = j
                    elif _DEPT_RE.search(v) and col_dept == -1:
                        col_dept = j
                    elif _COMMUNE_RE.search(v) and col_commune == -1:
                        col_commune = j
                    elif _LOCALITE_RE.search(v) and col_localite == -1:
                        col_localite = j
                    elif _DECOMPTE_RE.search(v) and j not in col_decomptes:
                        col_decomptes.append(j)
                    elif _PT_BETON_RE.search(v) and col_pt_beton == -1:
                        col_pt_beton = j
                    elif _PT_CIMENT_RE.search(v) and col_pt_ciment == -1:
                        col_pt_ciment = j
                    elif _GRUE_RE.search(v) and col_grue == -1:
                        col_grue = j
                    elif _NBRE_RE.search(v) and col_nbre == -1:
                        col_nbre = j
                    elif _PU_RE.search(v) and col_pu == -1:
                        col_pu = j
                    elif _TRANSPORT_RE.search(v) and col_transport == -1:
                        col_transport = j

                if (beton_found or ciment_found or grue_found or transport_found):
                    right_header_row = i
                    if len(prestataire_indices) > 1:
                        col_prestataire_R = prestataire_indices[-1]
                    elif prestataire_indices and col_prestataire_R == -1 and col_prestataire_L != prestataire_indices[0]:
                        col_prestataire_R = prestataire_indices[0]

            # If we found the left and right headers, and the current row has no headers, it's likely the first data row
            elif left_header_row != -1 and right_header_row != -1:
                break
        # ── 2.  Parse left main table ─────────────────────────────────────────
        base_date = datetime.utcnow().date()

        # Collect left-table data rows and build an index: left_row_index → partner
        # so we can align with the right panel rows
        left_row_partners: dict[int, Partner] = {}  # df index → partner obj

        if left_header_row != -1 and col_prestataire_L != -1:
            for i in range(left_header_row + 1, len(df)):
                row = df.iloc[i]
                prestataire = _cell_str(row.get(col_prestataire_L, ""))

                if not prestataire or "TOTAL" in prestataire.upper():
                    continue
                # Stop reading main table if we hit the summary blocks (PRIX DE POSE etc.)
                if any(k in prestataire.upper() for k in ("PRIX DE", "DÉBOURS", "DEBOURS", "AUTRES", "RELIQUAT")):
                    break

                partner = self._get_or_create_partner(prestataire)
                left_row_partners[i] = partner

                region      = _cell_str(row.get(col_region,   "")) if col_region   != -1 else ""
                departement = _cell_str(row.get(col_dept,     "")) if col_dept      != -1 else ""
                commune     = _cell_str(row.get(col_commune,  "")) if col_commune   != -1 else ""
                localite    = _cell_str(row.get(col_localite, "")) if col_localite  != -1 else ""

                # MONTANT TOTAL → store as a global budget record
                if col_montant != -1:
                    mt = _clean_num(row.get(col_montant, 0))
                    if mt > 0:
                        budget = ProjectBudget(
                            project_id=self.project_id,
                            partner_id=partner.id,
                            category="Prestation (Global)",
                            allocated_amount=mt,
                            currency="XOF",
                        )
                        self.db.add(budget)
                        summary["parsed_budgets"] += 1

                # Décompte columns → one PaymentMilestone per column with a value
                for k, d_col in enumerate(col_decomptes):
                    dv = _clean_num(row.get(d_col, 0))
                    if dv > 0:
                        pm = PaymentMilestone(
                            project_id=self.project_id,
                            partner_id=partner.id,
                            title=f"Décompte N°{k + 1}",
                            amount=dv,
                            due_date=base_date + timedelta(days=30 * (k + 1)),
                            region=region or None,
                            departement=departement or None,
                            commune=commune or None,
                            localite=localite or None,
                        )
                        self.db.add(pm)
                        summary["parsed_payment_milestones"] += 1

        # ── 3.  Parse right panel ─────────────────────────────────────────────
        if right_header_row != -1:
            for i in range(right_header_row + 1, len(df)):
                row = df.iloc[i]

                # Use the partner from the aligned left-table row if possible,
                # otherwise fall back to the right-panel PRESTATAIRES column.
                if i in left_row_partners:
                    partner = left_row_partners[i]
                elif col_prestataire_R != -1:
                    pname = _cell_str(row.get(col_prestataire_R, ""))
                    if not pname or "TOTAL" in pname.upper():
                        continue
                    partner = self._get_or_create_partner(pname)
                else:
                    continue


                def _add_budget(col_idx, category, qty=None, pu=None):
                    if col_idx == -1 and category != "Transport PBA":
                        return
                    
                    val = 0
                    if col_idx != -1:
                        val = _clean_num(row.get(col_idx, 0))
                    elif category == "Transport PBA" and qty and pu:
                        val = qty * pu

                    if val > 0:
                        loc_kw = {}
                        if i in left_row_partners:
                            loc_kw = {
                                "region": _cell_str(df.iloc[i].get(col_region, "")) if col_region != -1 else "",
                                "departement": _cell_str(df.iloc[i].get(col_dept, "")) if col_dept != -1 else "",
                                "commune": _cell_str(df.iloc[i].get(col_commune, "")) if col_commune != -1 else "",
                                "localite": _cell_str(df.iloc[i].get(col_localite, "")) if col_localite != -1 else ""
                            }
                        
                        self.db.add(ProjectBudget(
                            project_id=self.project_id,
                            partner_id=partner.id,
                            category=category,
                            allocated_amount=val,
                            currency="XOF",
                            quantity=qty,
                            unit_price=pu,
                            **loc_kw
                        ))
                        summary["parsed_budgets"] += 1

                _add_budget(col_pt_beton,  "Achat Intrants - Béton")
                _add_budget(col_pt_ciment, "Achat Intrants - Ciment")
                _add_budget(col_grue,      "Location Grue")

                # Transport PBA
                nbre = 0
                pu = 0
                if col_nbre != -1:
                    nbre = _clean_num(row.get(col_nbre, 0))
                if col_pu != -1:
                    pu = _clean_num(row.get(col_pu, 0))
                    
                if col_transport != -1:
                    _add_budget(col_transport, "Transport PBA", qty=nbre if nbre else None, pu=pu if pu else None)
                elif nbre and pu:
                    _add_budget(-1, "Transport PBA", qty=nbre, pu=pu)

        self.db.flush()


    # ── Partner helper ────────────────────────────────────────────────────────

    def _get_or_create_partner(self, name: str) -> Partner:
        partner = self.db.query(Partner).filter(Partner.name == name).first()
        if not partner:
            code = "P_" + name[:5].upper() + "_" + str(datetime.now().timestamp()).replace('.', '')[-5:]
            partner = Partner(name=name, code=code)
            self.db.add(partner)
            self.db.flush()

        project = self.db.query(Project).filter(Project.id == self.project_id).first()
        if project and partner not in project.partners:
            project.partners.append(partner)
            self.db.flush()

        return partner

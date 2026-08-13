import io
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

    async def import_excel(self, file: UploadFile):
        self._clear_existing_project_data()
        content = await file.read()
        
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
            elif "BUDGET" in name_upper or "RECAP" in name_upper or "FINANCE" in name_upper:
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
            
        gantt_cols = []
        for j in range(designation_col + 1, len(df.columns)):
            gantt_cols.append(j)
            
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
                
                cell = ws.cell(row=i+1, column=c+1)
                has_color = False
                color_debug = ""
                if cell.fill and cell.fill.patternType == 'solid':
                    if cell.fill.fgColor:
                        color_debug = f"type={getattr(cell.fill.fgColor, 'type', None)} rgb={getattr(cell.fill.fgColor, 'rgb', None)} theme={getattr(cell.fill.fgColor, 'theme', None)} indexed={getattr(cell.fill.fgColor, 'indexed', None)}"
                        if cell.fill.fgColor.rgb and cell.fill.fgColor.rgb not in ('FFFFFFFF', '00000000'):
                            has_color = True
                        elif getattr(cell.fill.fgColor, 'theme', None) is not None:
                            has_color = True
                        elif getattr(cell.fill.fgColor, 'type', None) == 'indexed' and getattr(cell.fill.fgColor, 'indexed', None) not in (64, 65):
                            has_color = True
                
                with open("c:/Users/adam.guizaoui/.gemini/antigravity-ide/brain/7241c8c3-72ab-4162-93f1-f029f1178150/scratch/color_log.txt", "a", encoding="utf-8") as f:
                    if color_debug or has_value:
                        f.write(f"Row {i+1} Col {c+1} ({designation}): val='{val}' has_value={has_value} pattern={cell.fill.patternType if cell.fill else None} {color_debug} -> has_color={has_color}\n")

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

    def _process_budgets(self, df: pd.DataFrame, summary: dict):
        prestataire_col_1 = -1
        montant_total_col = -1
        avance_col = -1
        decompte_cols = []
        
        prestataire_col_2 = -1
        ciment_col = -1
        beton_col = -1
        grue_col = -1
        transport_col = -1
        
        header_row_1 = -1
        header_row_2 = -1
        
        for i, row in df.iterrows():
            row_vals = [str(x).strip().upper() for x in row]
            
            if "PRESTATAIRES" in row_vals and header_row_1 == -1:
                prestataire_col_1 = row_vals.index("PRESTATAIRES")
                if "MONTANT TOTAL" in row_vals:
                    montant_total_col = row_vals.index("MONTANT TOTAL")
                if "AVANCE DE DÉMARRAGE" in row_vals:
                    avance_col = row_vals.index("AVANCE DE DÉMARRAGE")
                elif "AVANCE DE DEMARRAGE" in row_vals:
                    avance_col = row_vals.index("AVANCE DE DEMARRAGE")
                
                for j, v in enumerate(row_vals):
                    if "DÉCOMPTE" in v or "DECOMPTE" in v:
                        decompte_cols.append(j)
                        
                header_row_1 = i
                
            if "PT CIMENT" in row_vals or "PT BETON" in row_vals:
                indices = [idx for idx, val in enumerate(row_vals) if val == "PRESTATAIRES"]
                if len(indices) > 1:
                    prestataire_col_2 = indices[-1]
                else:
                    prestataire_col_2 = indices[0] if indices else -1
                
                if "PT CIMENT" in row_vals:
                    ciment_col = row_vals.index("PT CIMENT")
                if "PT BETON" in row_vals:
                    beton_col = row_vals.index("PT BETON")
                if "LOCATION GRUE" in row_vals:
                    grue_col = row_vals.index("LOCATION GRUE")
                if "TOTAL TRANSPORT" in row_vals:
                    transport_col = row_vals.index("TOTAL TRANSPORT")
                    
                header_row_2 = i
                
        if header_row_1 != -1 and prestataire_col_1 != -1:
            for i in range(header_row_1 + 1, len(df)):
                row = df.iloc[i]
                prestataire = str(row.get(prestataire_col_1, "")).strip()
                if not prestataire or prestataire == 'NAN' or "TOTAL" in prestataire.upper():
                    continue
                    
                partner = self._get_or_create_partner(prestataire)
                
                if montant_total_col != -1:
                    mt = str(row.get(montant_total_col, "0")).replace(" ", "").replace("XOF", "")
                    try:
                        val = float(mt)
                        if val > 0:
                            budget = ProjectBudget(
                                project_id=self.project_id,
                                partner_id=partner.id,
                                category="Prestation (Global)",
                                allocated_amount=val,
                                currency="XOF"
                            )
                            self.db.add(budget)
                            summary["parsed_budgets"] += 1
                    except:
                        pass
                
                base_date = datetime.utcnow().date()
                if avance_col != -1:
                    av = str(row.get(avance_col, "0")).replace(" ", "").replace("XOF", "")
                    try:
                        val = float(av)
                        if val > 0:
                            pm = PaymentMilestone(
                                project_id=self.project_id,
                                partner_id=partner.id,
                                title="Avance de démarrage",
                                amount=val,
                                due_date=base_date + timedelta(days=30)
                            )
                            self.db.add(pm)
                            summary["parsed_payment_milestones"] += 1
                    except:
                        pass
                        
                for k, d_col in enumerate(decompte_cols):
                    dv = str(row.get(d_col, "0")).replace(" ", "").replace("XOF", "")
                    try:
                        val = float(dv)
                        if val > 0:
                            pm = PaymentMilestone(
                                project_id=self.project_id,
                                partner_id=partner.id,
                                title=f"Décompte N°{k+1}",
                                amount=val,
                                due_date=base_date + timedelta(days=30*(k+2))
                            )
                            self.db.add(pm)
                            summary["parsed_payment_milestones"] += 1
                    except:
                        pass

        if header_row_2 != -1 and prestataire_col_2 != -1:
            for i in range(header_row_2 + 1, len(df)):
                row = df.iloc[i]
                prestataire = str(row.get(prestataire_col_2, "")).strip()
                if not prestataire or prestataire == 'NAN' or "TOTAL" in prestataire.upper():
                    continue
                    
                partner = self._get_or_create_partner(prestataire)
                
                def add_intrant(col_idx, category):
                    if col_idx != -1:
                        val_str = str(row.get(col_idx, "0")).replace(" ", "").replace("XOF", "")
                        try:
                            val = float(val_str)
                            if val > 0:
                                budget = ProjectBudget(
                                    project_id=self.project_id,
                                    partner_id=partner.id,
                                    category=category,
                                    allocated_amount=val,
                                    currency="XOF"
                                )
                                self.db.add(budget)
                                summary["parsed_budgets"] += 1
                        except:
                            pass
                            
                add_intrant(ciment_col, "Achat Intrants - Ciment")
                add_intrant(beton_col, "Achat Intrants - Béton")
                add_intrant(grue_col, "Location Grue")
                add_intrant(transport_col, "Transport PBA")
                
        self.db.flush()

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

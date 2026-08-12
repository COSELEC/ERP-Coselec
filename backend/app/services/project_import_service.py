import io
import pandas as pd
from datetime import datetime
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
from datetime import timedelta

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
            "parsed_stock_requirements": 0,
            "errors_or_warnings": []
        }
        
        for sheet_name in excel_file.sheet_names:
            df = excel_file.parse(sheet_name=sheet_name)
            header_idx = self._find_header_row(df)
            financial_idx = self._find_financial_header_row(df)
            
            # Use whichever header is found first
            active_idx = header_idx if header_idx is not None else financial_idx
            
            if active_idx is not None:
                raw_cols = df.iloc[active_idx].astype(str).str.strip().str.upper()
                new_cols = []
                seen = set()
                for col in raw_cols:
                    if col in seen:
                        i = 1
                        while f"{col}_{i}" in seen:
                            i += 1
                        col = f"{col}_{i}"
                    seen.add(col)
                    new_cols.append(col)
                df.columns = new_cols
                df = df.iloc[active_idx + 1:].reset_index(drop=True)
                df = df.dropna(how='all')
                
                if header_idx is not None and "DESIGNATION" in df.columns:
                    has_quantities = any("QUANTIT" in str(col) or "TOTAL" in str(col) for col in df.columns)
                    if has_quantities:
                        self._process_quantities(df, summary)
                    else:
                        self._process_planning(df, summary)
                elif financial_idx is not None and "PRESTATAIRES" in df.columns:
                    self._process_financial_data(df, summary)
                else:
                    summary["errors_or_warnings"].append(f"Onglet ignoré: {sheet_name} (En-tête introuvable)")
            else:
                summary["errors_or_warnings"].append(f"Onglet ignoré: {sheet_name} (Aucun en-tête reconnu)")
                    
        return summary
        
    def _find_header_row(self, df: pd.DataFrame) -> int:
        for idx, row in df.iterrows():
            row_str = " ".join([str(val).upper() for val in row.values if pd.notna(val)])
            if "DESIGNATION" in row_str or "TÂCHES" in row_str:
                return idx
        return None

    def _find_financial_header_row(self, df: pd.DataFrame) -> int:
        for idx, row in df.iterrows():
            row_str = " ".join([str(val).upper() for val in row.values if pd.notna(val)])
            if "PRESTATAIRES" in row_str:
                return idx
        return None

    def _process_planning(self, df: pd.DataFrame, summary: dict):
        project = self.db.query(Project).filter(Project.id == self.project_id).first()
        base_date = project.date_debut_estimee if project and project.date_debut_estimee else datetime.utcnow().date()

        month_cols = []
        designation_idx = -1
        for i, col in enumerate(df.columns):
            col_str = str(col).strip().upper()
            if "DESIGNATION" in col_str:
                designation_idx = i
                
            if ('M' in col_str and any(c.isdigit() for c in col_str)) or 'MOIS' in col_str or col_str.isdigit():
                month_cols.append(col)
                
        if not month_cols and designation_idx != -1:
            for i in range(designation_idx + 1, len(df.columns)):
                col_str = str(df.columns[i]).strip().upper()
                if not any(x in col_str for x in ["TOTAL", "PRIX", "QTE", "QUANTIT", "UNITE", "OBSERVATION"]):
                    month_cols.append(df.columns[i])
                
        current_milestone = None
        
        for idx, row in df.iterrows():
            designation = str(row.get("DESIGNATION", "")).strip()
            if not designation or pd.isna(row.get("DESIGNATION")) or designation == 'NAN':
                continue
                
            is_milestone = designation.isupper()
            
            start_offset = 0
            end_offset = 0
            has_data = False
            
            for i, m_col in enumerate(month_cols):
                val = row.get(m_col)
                if pd.notna(val) and str(val).strip() != '' and str(val).strip().upper() != 'NAN':
                    if not has_data:
                        start_offset = i
                        has_data = True
                    end_offset = i
                    
            if not has_data:
                start_offset = 0
                end_offset = 0
                
            start_date = base_date + timedelta(days=30 * start_offset)
            due_date = base_date + timedelta(days=30 * (end_offset + 1))
            
            if is_milestone:
                current_milestone = ProjectMilestone(
                    project_id=self.project_id,
                    title=designation[:255],
                    order_index=summary["parsed_milestones"],
                    due_date=due_date, 
                )
                self.db.add(current_milestone)
                self.db.flush()
                summary["parsed_milestones"] += 1
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

    def _process_quantities(self, df: pd.DataFrame, summary: dict):
        warehouse = self._get_or_create_warehouse()
        category = self._get_or_create_default_category()
        
        total_col_idx = None
        for i, col in enumerate(df.columns):
            if "TOTAL" in str(col) or "QUANTIT" in str(col):
                total_col_idx = i
                break
                
        if total_col_idx is not None and total_col_idx < len(df.columns) - 1:
            id_vars = list(df.columns[:total_col_idx + 1])
            value_vars = list(df.columns[total_col_idx + 1:])
            
            melted_df = df.melt(id_vars=id_vars, value_vars=value_vars, var_name="Location", value_name="Quantity")
            melted_df["Quantity"] = pd.to_numeric(melted_df["Quantity"], errors="coerce").fillna(0)
            melted_df = melted_df[melted_df["Quantity"] > 0]
            
            for _, row in melted_df.iterrows():
                designation = str(row.get("DESIGNATION", "")).strip()
                if not designation or designation == 'NAN':
                    continue
                    
                product = self._get_or_create_product(designation, category.id)
                quantity = int(row["Quantity"])
                location = str(row["Location"]).strip()
                
                stock_entry = Stock(
                    product_id=product.id,
                    warehouse_id=warehouse.id,
                    project_id=self.project_id,
                    stock_type=StockType.PROJECT,
                    quantity=quantity,
                    stock_metadata={"location": location}
                )
                self.db.add(stock_entry)
                summary["parsed_stock_requirements"] += 1

    def _get_or_create_warehouse(self) -> Warehouse:
        warehouse = self.db.query(Warehouse).first()
        if not warehouse:
            warehouse = Warehouse(name="Magasin Principal", address="Automatisé", code="WH_MAIN")
            self.db.add(warehouse)
            self.db.flush()
        return warehouse
        
    def _get_or_create_default_category(self) -> Category:
        cat = self.db.query(Category).filter(Category.name == "Matériel Importé").first()
        if not cat:
            cat = Category(name="Matériel Importé", code="CAT_IMP")
            self.db.add(cat)
            self.db.flush()
        return cat

    def _get_or_create_product(self, designation: str, category_id: int) -> Product:
        product = self.db.query(Product).filter(Product.designation == designation).first()
        if not product:
            code = "P_" + designation[:5].upper() + "_" + str(datetime.now().timestamp()).replace('.', '')[-5:]
            product = Product(
                designation=designation,
                code=code,
                category_id=category_id
            )
            self.db.add(product)
            self.db.flush()
        return product

    def _process_financial_data(self, df: pd.DataFrame, summary: dict):
        if any("MONTANT TOTAL" in str(c).upper() for c in df.columns):
            self._process_recap_contrat(df, summary)
            self._extract_global_budgets(df)
        else:
            self._process_achat_intrants(df, summary)
            self._extract_global_budgets(df)

    def _extract_global_budgets(self, df: pd.DataFrame):
        keywords = ["PRIX DE POSE", "DEBOURS", "AUTRES", "RELIQUAT", "PRIX DE TRANSPORT"]
        for _, row in df.iterrows():
            for i, val in enumerate(row.values):
                val_str = str(val).strip().upper()
                for kw in keywords:
                    if val_str == kw:
                        if i + 1 < len(row.values):
                            amount_str = str(row.values[i+1]).replace("XOF", "").replace(" ", "").strip()
                            try:
                                amount = float(amount_str)
                                if amount > 0:
                                    budget = ProjectBudget(
                                        project_id=self.project_id,
                                        partner_id=None,
                                        category=kw.title(),
                                        allocated_amount=amount,
                                        currency="XOF"
                                    )
                                    self.db.add(budget)
                            except ValueError:
                                pass
        self.db.flush()

    def _process_recap_contrat(self, df: pd.DataFrame, summary: dict):
        milestone_cols = []
        for col in df.columns:
            if "AVANCE" in str(col).upper() or "DÉCOMPTE" in str(col).upper() or "DECOMPTE" in str(col).upper():
                milestone_cols.append(col)
                
        for _, row in df.iterrows():
            prestataire_name = str(row.get("PRESTATAIRES", "")).strip()
            if not prestataire_name or prestataire_name == 'NAN' or prestataire_name == 'TOTAL':
                continue
                
            partner = self._get_or_create_partner(prestataire_name)
            base_date = datetime.utcnow().date()
            
            commune = str(row.get("COMMUNES", "")).strip()
            localite = str(row.get("LOCALITES", "")).strip()
            
            location_str = ""
            if commune and localite and commune.lower() != 'nan' and localite.lower() != 'nan':
                location_str = f" - {commune} ({localite})"
            elif localite and localite.lower() != 'nan':
                location_str = f" - {localite}"
            
            months_offset = 0
            for col in milestone_cols:
                amount_str = str(row.get(col, "0")).replace("XOF", "").replace(" ", "").strip()
                try:
                    amount = float(amount_str)
                except ValueError:
                    amount = 0.0
                
                if amount > 0:
                    due_date = base_date + timedelta(days=30 * months_offset)
                    pm = PaymentMilestone(
                        project_id=self.project_id,
                        partner_id=partner.id,
                        title=f"{str(col)[:150]}{location_str}",
                        amount=amount,
                        due_date=due_date
                    )
                    self.db.add(pm)
                    months_offset += 1
                    
        self.db.flush()

    def _process_achat_intrants(self, df: pd.DataFrame, summary: dict):
        for _, row in df.iterrows():
            prestataire_name = str(row.get("PRESTATAIRES", "")).strip()
            if not prestataire_name or prestataire_name == 'NAN' or prestataire_name == 'TOTAL':
                continue
                
            partner = self._get_or_create_partner(prestataire_name)
            
            budget_mapping = {
                "PT CIMENT": "Achat Intrants - Ciment",
                "PT BETON": "Achat Intrants - Béton",
                "LOCATION GRUE": "Grues",
                "TOTAL TRANSPORT": "Transport PBA"
            }
            
            for col_keyword, cat_name in budget_mapping.items():
                actual_col = next((c for c in df.columns if col_keyword in str(c).upper()), None)
                if actual_col:
                    amount_str = str(row.get(actual_col, "0")).replace("XOF", "").replace(" ", "").strip()
                    try:
                        amount = float(amount_str)
                    except ValueError:
                        amount = 0.0
                        
                    if amount > 0:
                        budget = ProjectBudget(
                            project_id=self.project_id,
                            partner_id=partner.id,
                            category=cat_name,
                            allocated_amount=amount,
                            currency="XOF"
                        )
                        self.db.add(budget)
                        
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

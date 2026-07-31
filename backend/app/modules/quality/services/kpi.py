import pandas as pd
import io
import re
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.modules.quality.models.kpi import KPIProcessus, KPIIndicator, KPIYearlyTarget, KPIValue, KPIOperator

def get_excel_preview(file_bytes: bytes) -> list[str]:
    try:
        xls = pd.ExcelFile(io.BytesIO(file_bytes))
        return xls.sheet_names
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Excel file: {str(e)}")

def parse_target(target_str: str):
    if not isinstance(target_str, str):
        target_str = str(target_str)
    
    target_str = target_str.strip()
    if target_str.lower() in ['nan', 'none', '']:
        return None, None, None

    operator = KPIOperator.EQ
    target_num = None
    target_num_max = None
    
    # Check for between "X% à Y%" or "X à Y"
    between_match = re.search(r'([\d.,]+)%\s*(?:à|-|to)\s*([\d.,]+)%?', target_str, re.IGNORECASE)
    if not between_match:
        between_match = re.search(r'([\d.,]+)\s*(?:à|-|to)\s*([\d.,]+)', target_str, re.IGNORECASE)
    
    if between_match:
        operator = KPIOperator.BETWEEN
        target_num = float(between_match.group(1).replace(',', '.'))
        target_num_max = float(between_match.group(2).replace(',', '.'))
        return operator, target_num, target_num_max
    
    # Extract number
    num_match = re.search(r'([\d.,]+)', target_str)
    if num_match:
        target_num = float(num_match.group(1).replace(',', '.'))
        
        if '≥' in target_str or '>=' in target_str or '>' in target_str:
            operator = KPIOperator.GTE
        elif '≤' in target_str or '<=' in target_str or '<' in target_str:
            operator = KPIOperator.LTE
        
        return operator, target_num, None
    
    return None, None, None

def parse_value(value_str: str):
    if pd.isna(value_str) or value_str is None:
        return None
    if not isinstance(value_str, str):
        return float(value_str)
        
    value_str = value_str.strip()
    if value_str.lower() in ['n/a', 'na', '-', '']:
        return None
        
    num_match = re.search(r'([\d.,]+)', value_str)
    if num_match:
        return float(num_match.group(1).replace(',', '.'))
    return None

def parse_and_import_kpi(db: Session, file_bytes: bytes, sheet_name: str, year: int, month_name: str, month_index: int):
    try:
        # LECTURE SANS EN-TÊTE POUR PARER A TOUTE STRUCTURE EXCEL BIZARRE
        df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name, header=None)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read sheet {sheet_name}: {str(e)}")

    col_map = {
        "processus": -1,
        "indicateur": -1,
        "cible": -1,
        "fréquence": -1,
        "month": -1
    }
    
    from datetime import datetime
    m_str = month_name.strip().lower()
    
    # On scanne tout le document pour trouver les index des colonnes
    for col_idx in df.columns:
        for row_idx, val in df[col_idx].items():
            if pd.isna(val):
                continue
                
            val_str = str(val).strip().lower()
            
            # Check Month
            if col_map["month"] == -1:
                m_pref = month_name.split('-')[0].strip().lower() # ex: 'mai'
                y_suff = month_name.split('-')[1].strip() # ex: '26'
                
                # Si Pandas l'a parsé comme une vraie date (ex: 2026-05-01 ou 2024-05-26)
                if hasattr(val, 'month') and val.month == month_index:
                    if hasattr(val, 'year') and val.year == year:
                        col_map["month"] = col_idx
                    elif hasattr(val, 'day') and val.day == (year % 100):
                        col_map["month"] = col_idx
                # Recherche textuelle souple (ex: 'mai-26', 'mai 26', ' mai - 26')
                elif m_pref in val_str and y_suff in val_str and len(val_str) < 15:
                    col_map["month"] = col_idx
                    
            if col_map["processus"] == -1 and ('processus' == val_str or 'proc' == val_str):
                col_map["processus"] = col_idx
            if col_map["indicateur"] == -1 and ('indicateur' in val_str or 'kpi' in val_str):
                col_map["indicateur"] = col_idx
            if col_map["cible"] == -1 and ('cible' in val_str or 'objectif' in val_str):
                col_map["cible"] = col_idx
            if col_map["fréquence"] == -1 and ('fréquence' in val_str or 'frequence' in val_str or 'freq' == val_str):
                col_map["fréquence"] = col_idx

    missing = []
    if col_map["processus"] == -1: missing.append("Processus")
    if col_map["indicateur"] == -1: missing.append("Indicateurs")
    if col_map["cible"] == -1: missing.append("Cibles")
    if col_map["fréquence"] == -1: missing.append("Fréquence")
    if col_map["month"] == -1: missing.append(month_name)
    
    if missing:
        raise HTTPException(status_code=400, detail=f"Impossible de trouver les colonnes : {', '.join(missing)}")

    # Clean Processus (ffill) sur la colonne identifiée
    df[col_map["processus"]] = df[col_map["processus"]].ffill()
    
    imported_count = 0
    updated_count = 0

    for index, row in df.iterrows():
        proc_name = str(row[col_map["processus"]]).strip()
        ind_name = str(row[col_map["indicateur"]]).strip()
        
        # Ignorer les lignes vides ou les en-têtes (si la cellule contient 'indicateur')
        if pd.isna(row[col_map["indicateur"]]) or ind_name == 'nan' or not ind_name:
            continue
        if 'indicateur' in ind_name.lower() or 'performance' in ind_name.lower():
            continue
            
        freq = str(row[col_map["fréquence"]]).strip() if pd.notna(row[col_map["fréquence"]]) else None
        target_raw = str(row[col_map["cible"]]).strip() if pd.notna(row[col_map["cible"]]) else None
        val_raw = str(row[col_map["month"]]).strip() if pd.notna(row[col_map["month"]]) else None
        
        if val_raw == 'nan':
            val_raw = None

        # 1. Processus
        proc = db.query(KPIProcessus).filter(KPIProcessus.name == proc_name).first()
        if not proc:
            proc = KPIProcessus(name=proc_name)
            db.add(proc)
            db.flush()
            
        # 2. Indicator
        ind = db.query(KPIIndicator).filter(KPIIndicator.processus_id == proc.id, KPIIndicator.name == ind_name).first()
        if not ind:
            ind = KPIIndicator(processus_id=proc.id, name=ind_name)
            db.add(ind)
            db.flush()
            
        # 3. Yearly Target
        target_operator, target_numeric, target_numeric_max = parse_target(target_raw)
        
        yearly_target = db.query(KPIYearlyTarget).filter(
            KPIYearlyTarget.indicator_id == ind.id,
            KPIYearlyTarget.year == year
        ).first()
        
        if not yearly_target:
            yearly_target = KPIYearlyTarget(
                indicator_id=ind.id,
                year=year,
                frequency=freq,
                target_raw=target_raw,
                target_numeric=target_numeric,
                target_numeric_max=target_numeric_max,
                operator=target_operator
            )
            db.add(yearly_target)
        else:
            yearly_target.frequency = freq
            yearly_target.target_raw = target_raw
            yearly_target.target_numeric = target_numeric
            yearly_target.target_numeric_max = target_numeric_max
            yearly_target.operator = target_operator
            
        db.flush()
        
        # 4. Value
        val_numeric = parse_value(val_raw)
        
        val = db.query(KPIValue).filter(
            KPIValue.indicator_id == ind.id,
            KPIValue.year == year,
            KPIValue.month == month_index
        ).first()
        
        if not val:
            val = KPIValue(
                indicator_id=ind.id,
                year=year,
                month=month_index,
                value_raw=val_raw,
                value_numeric=val_numeric
            )
            db.add(val)
            imported_count += 1
        else:
            val.value_raw = val_raw
            val.value_numeric = val_numeric
            updated_count += 1
            
    db.commit()
    return imported_count, updated_count

def get_kpi_dashboard_data(db: Session, year: int):
    processus = db.query(KPIProcessus).all()
    # we need to eagerly load indicators, yearly targets (for this year), and values (for this year)
    # but we can do it via nested queries or just send the schemas
    
    result = []
    for p in processus:
        p_data = {
            "id": p.id,
            "name": p.name,
            "indicators": []
        }
        for ind in p.indicators:
            targets = [t for t in ind.yearly_targets if t.year == year]
            values = [v for v in ind.values if v.year == year]
            
            p_data["indicators"].append({
                "id": ind.id,
                "processus_id": ind.processus_id,
                "name": ind.name,
                "yearly_targets": targets,
                "values": values
            })
        if len(p_data["indicators"]) > 0:
            result.append(p_data)
            
    return result

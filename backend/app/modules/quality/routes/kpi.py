from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database.session import get_db
from app.core.security.auth import get_current_user
from app.modules.users.models.user import User

from app.modules.quality.schemas.kpi import KPIImportPreviewResponse, KPIImportResponse, KPIProcessusResponse, KPIProcessusCreate, KPIIndicatorCreate, KPIIndicatorResponse, KPIValueCreate, KPIValueResponse
from app.modules.quality.services.kpi import get_excel_preview, parse_and_import_kpi, get_kpi_dashboard_data
from app.modules.quality.models.kpi import KPIProcessus, KPIIndicator, KPIValue

router = APIRouter(prefix="/kpi", tags=["Quality KPI"])

@router.post("/upload-preview", response_model=KPIImportPreviewResponse)
def api_kpi_upload_preview(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if not any(r.name in ["Admin", "Qualité", "Qualite"] for r in current_user.roles):
        raise HTTPException(status_code=403, detail="Permission refusée")
        
    contents = file.file.read()
    sheet_names = get_excel_preview(contents)
    return {"sheet_names": sheet_names}

@router.post("/upload-parse", response_model=KPIImportResponse)
def api_kpi_upload_parse(
    file: UploadFile = File(...),
    sheet_name: str = Form(...),
    year: int = Form(...),
    month_name: str = Form(...),
    month_index: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not any(r.name in ["Admin", "Qualité"] for r in current_user.roles):
        raise HTTPException(status_code=403, detail="Permission refusée")
        
    contents = file.file.read()
    imported, updated = parse_and_import_kpi(db, contents, sheet_name, year, month_name, month_index)
    
    return {
        "message": f"Extraction réussie. {imported} KPI importés, {updated} mis à jour.",
        "imported_count": imported,
        "updated_count": updated
    }

@router.get("/dashboard/{year}", response_model=List[KPIProcessusResponse])
def api_get_kpi_dashboard(
    year: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    data = get_kpi_dashboard_data(db, year)
    return data

@router.post("/processus", response_model=KPIProcessusResponse)
def create_processus(
    data: KPIProcessusCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not any(r.name in ["Admin", "Qualité", "Qualite"] for r in current_user.roles):
        raise HTTPException(status_code=403, detail="Seule la Qualité peut créer un processus.")
    proc = KPIProcessus(**data.model_dump())
    db.add(proc)
    db.commit()
    db.refresh(proc)
    return proc

@router.post("/indicators", response_model=KPIIndicatorResponse)
def create_indicator(
    data: KPIIndicatorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not any(r.name in ["Admin", "Qualité", "Qualite"] for r in current_user.roles):
        raise HTTPException(status_code=403, detail="Seule la Qualité peut créer un indicateur.")
    ind = KPIIndicator(**data.model_dump())
    db.add(ind)
    db.commit()
    db.refresh(ind)
    return ind

@router.post("/values", response_model=KPIValueResponse)
def update_kpi_value(
    data: KPIValueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    is_qualite = any(r.name in ["Admin", "Qualité", "Qualite"] for r in current_user.roles)
    is_pilote = any(r.name in ["Pilote", "Copilote"] for r in current_user.roles)
    
    if not is_qualite and not is_pilote:
        raise HTTPException(status_code=403, detail="Permission refusée.")
        
    indicator = db.query(KPIIndicator).filter(KPIIndicator.id == data.indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicateur non trouvé.")
        
    if is_pilote and not is_qualite:
        if indicator.processus.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Vous ne pouvez renseigner que les KPIs de votre direction.")
            
    val = db.query(KPIValue).filter(
        KPIValue.indicator_id == data.indicator_id,
        KPIValue.year == data.year,
        KPIValue.month == data.month
    ).first()
    
    if val:
        val.value_raw = data.value_raw
        val.value_numeric = data.value_numeric
    else:
        val = KPIValue(**data.model_dump())
        db.add(val)
        
    db.commit()
    db.refresh(val)
    return val


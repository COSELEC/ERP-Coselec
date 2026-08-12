from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database.session import get_db
from app.core.security.auth import get_current_user
from app.modules.users.models.user import User

from app.modules.quality.schemas.kpi import KPIImportPreviewResponse, KPIImportResponse, KPIProcessusResponse
from app.modules.quality.services.kpi import get_excel_preview, parse_and_import_kpi, get_kpi_dashboard_data

router = APIRouter(prefix="/kpi", tags=["Quality KPI"])

@router.post("/upload-preview", response_model=KPIImportPreviewResponse)
async def api_kpi_upload_preview(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if not any(r.name in ["Admin", "Qualité", "Qualite"] for r in current_user.roles):
        raise HTTPException(status_code=403, detail="Permission refusée")
        
    contents = await file.read()
    sheet_names = get_excel_preview(contents)
    return {"sheet_names": sheet_names}

@router.post("/upload-parse", response_model=KPIImportResponse)
async def api_kpi_upload_parse(
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
        
    contents = await file.read()
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

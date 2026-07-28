from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any

from app.core.database import get_db
from app.modules.stock.models.stockmovement import StockMovement
from app.modules.stock.models.product import Product
from app.models.project.project import Project
from app.modules.stock.enums.movement_type import MovementType

router = APIRouter(prefix="/matrix", tags=["stock-matrix"])

@router.get("/", response_model=Dict[str, Any])
def get_stock_matrix(db: Session = Depends(get_db)):
    """
    Returns a matrix of product quantities distributed across projects.
    Rows: Products
    Columns: Projects
    Values: Net quantity currently at the project site (OUT - RETURN)
    """
    
    # 1. Fetch all products and projects to build the structure
    products = db.query(Product).all()
    projects = db.query(Project).all()
    
    # 2. Fetch stock movements linked to projects
    # OUT means sent to project (+ to project inventory)
    # RETURN or IN might mean returned from project (- to project inventory)
    movements = (
        db.query(
            StockMovement.product_id,
            StockMovement.project_id,
            StockMovement.type,
            func.sum(StockMovement.quantity).label("total_qty")
        )
        .filter(StockMovement.project_id.isnot(None))
        .group_by(StockMovement.product_id, StockMovement.project_id, StockMovement.type)
        .all()
    )
    
    # Process movements into a lookup dictionary
    # dict[product_id][project_id] = net_qty
    matrix_data: Dict[int, Dict[int, int]] = {}
    
    for mov in movements:
        pid = mov.product_id
        proj_id = mov.project_id
        
        if pid not in matrix_data:
            matrix_data[pid] = {}
        if proj_id not in matrix_data[pid]:
            matrix_data[pid][proj_id] = 0
            
        if mov.type == MovementType.OUT:
            matrix_data[pid][proj_id] += mov.total_qty
        elif mov.type == MovementType.IN:
            # Assuming IN with a project_id means returned from project
            matrix_data[pid][proj_id] -= mov.total_qty
            
    # Build final response
    # We want a format easy to parse for the frontend table
    
    response = {
        "columns": [{"id": p.id, "name": p.name} for p in projects],
        "rows": []
    }
    
    for prod in products:
        row = {
            "product_id": prod.id,
            "product_name": prod.name,
            "product_code": prod.code,
            "projects": {},
            "total_expected": 0
        }
        
        prod_total = 0
        for proj in projects:
            qty = matrix_data.get(prod.id, {}).get(proj.id, 0)
            row["projects"][str(proj.id)] = qty
            prod_total += qty
            
        row["total_expected"] = prod_total
        
        # Only include products that actually have some stock in projects
        if prod_total > 0:
            response["rows"].append(row)
            
    return response

from pydantic import BaseModel
from typing import Optional


class StockEntry(BaseModel):
    product_id: int
    warehouse_id: int
    partner_id: Optional[int] = None
    project_id: Optional[int] = None
    quantity: int


class StockExit(BaseModel):
    product_id: int
    warehouse_id: int
    partner_id: Optional[int] = None
    project_id: Optional[int] = None
    quantity: int


class StockTransfer(BaseModel):
    product_id: int

    from_warehouse_id: int
    to_warehouse_id: int

    partner_id: int
    project_id: Optional[int] = None

    quantity: int

class StockTransferToProject(BaseModel):
    product_id: int
    from_warehouse_id: int
    project_id: int
    quantity: int

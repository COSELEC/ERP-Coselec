from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProductSummary(BaseModel):
    id: int
    code: str
    designation: str

    model_config = ConfigDict(
        from_attributes=True
    )


class WarehouseSummary(BaseModel):
    id: int
    code: str
    name: str

    model_config = ConfigDict(
        from_attributes=True
    )


class PartnerSummary(BaseModel):
    id: int
    code: str
    name: str

    model_config = ConfigDict(
        from_attributes=True
    )


class StockMovementResponse(BaseModel):
    id: int

    product_id: int
    warehouse_id: int
    partner_id: int

    type: str
    quantity: int

    product: ProductSummary | None = None
    warehouse: WarehouseSummary | None = None
    partner: PartnerSummary | None = None

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

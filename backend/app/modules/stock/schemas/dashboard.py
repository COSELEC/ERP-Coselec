from pydantic import BaseModel


class DashboardResponse(BaseModel):
    products: int

    stock_rows: int

    total_quantity: int

    total_value: int

    low_stock_count: int

    out_of_stock_count: int

from fastapi import APIRouter

from app.modules.stock.routes.stocks import router as stocks_router
from app.modules.stock.routes.stockoperations import router as stockoperations_router
from app.modules.stock.routes.dashboard import router as dashboard_router
from app.modules.stock.routes.stockmovements import router as stockmovements_router
from app.modules.stock.routes.products import router as products_router
from app.modules.stock.routes.warehouses import router as warehouses_router
from app.modules.stock.routes.partners import router as partners_router
from app.modules.stock.routes.categories import router as categories_router
from app.modules.stock.routes.matrix import router as matrix_router
from app.modules.stock.routes.reception import router as reception_router
from app.modules.stock.routes.reservations import router as reservations_router

stock_router = APIRouter()
stock_router.include_router(stocks_router)
stock_router.include_router(stockoperations_router)
stock_router.include_router(dashboard_router)
stock_router.include_router(stockmovements_router)
stock_router.include_router(products_router)
stock_router.include_router(warehouses_router)
stock_router.include_router(partners_router)
stock_router.include_router(categories_router)
stock_router.include_router(matrix_router)
stock_router.include_router(reception_router)
stock_router.include_router(reservations_router)

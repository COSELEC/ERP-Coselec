from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)

from sqlalchemy.orm import Session

from app.core.security.auth import get_current_user, check_permission
from app.core.database import get_db

from app.modules.stock.models.product import Product
from app.modules.users.models.user import User

from app.modules.stock.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse
)

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.get("", response_model=list[ProductResponse])
def get_products(
    q: str | None = Query(default=None),
    skip: int = 0,
    limit: int = 50,
    _: None = Depends(check_permission("stock.read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Product)

    if q:
        query = query.filter(
            Product.designation.ilike(f"%{q}%")
        )

    return (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    _: None = Depends(check_permission("stock.read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


@router.post(
    "",
    response_model=ProductResponse,
    status_code=201
)
def create_product(
    product: ProductCreate,
    _: None = Depends(check_permission("stock.create")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing_product = (
        db.query(Product)
        .filter(Product.code == product.code)
        .first()
    )

    if existing_product:
        raise HTTPException(
            status_code=400,
            detail="Product code already exists"
        )

    new_product = Product(
        **product.model_dump()
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product: ProductUpdate,
    _: None = Depends(check_permission("stock.update")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing_product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not existing_product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    data = product.model_dump(
        exclude_unset=True
    )

    if "code" in data:
        code_exists = (
            db.query(Product)
            .filter(
                Product.code == data["code"],
                Product.id != product_id
            )
            .first()
        )

        if code_exists:
            raise HTTPException(
                status_code=400,
                detail="Product code already exists"
            )

    for key, value in data.items():
        setattr(existing_product, key, value)

    db.commit()
    db.refresh(existing_product)

    return existing_product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    _: None = Depends(check_permission("stock.delete")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully"
    }

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.core.security.auth import get_current_user, check_permission
from app.core.database import get_db

from app.modules.stock.models.category import Category
from app.modules.users.models.user import User

from app.modules.stock.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse
)

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)


@router.get("/", response_model=list[CategoryResponse])
def get_categories(
    _: None = Depends(check_permission("stock.read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Category).all()


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    _: None = Depends(check_permission("stock.read")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    return category


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=201
)
def create_category(
    category: CategoryCreate,
    _: None = Depends(check_permission("stock.create")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = (
        db.query(Category)
        .filter(Category.code == category.code)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Category code already exists"
        )

    new_category = Category(
        **category.model_dump()
    )

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return new_category


@router.put(
    "/{category_id}",
    response_model=CategoryResponse
)
def update_category(
    category_id: int,
    category: CategoryUpdate,
    _: None = Depends(check_permission("stock.update")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )

    if not existing:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    data = category.model_dump(
        exclude_unset=True
    )

    for key, value in data.items():
        setattr(existing, key, value)

    db.commit()
    db.refresh(existing)

    return existing


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    _: None = Depends(check_permission("stock.delete")),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    db.delete(category)
    db.commit()

    return {
        "message": "Category deleted successfully"
    }

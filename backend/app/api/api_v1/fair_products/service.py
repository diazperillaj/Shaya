from typing import List

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.api_v1.fair_products.schema import (
    FairProductCreate,
    FairProductUpdate,
)
from app.models.fair_product import FairProduct
from app.models.fair_sale import FairSale


class FairProductService:
    """Catálogo de productos de feria (café preparado, galletas, ...)."""

    def __init__(self, db: Session):
        self.db = db

    def get_products(self) -> List[FairProduct]:
        return self.db.query(FairProduct).order_by(FairProduct.name).all()

    def get_product_by_id(self, product_id: int) -> FairProduct:
        product = (
            self.db.query(FairProduct)
            .filter(FairProduct.id == product_id)
            .first()
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto de feria no encontrado",
            )
        return product

    def create_product(self, payload: FairProductCreate) -> FairProduct:
        self._validate_unique_name(payload.name)
        product = FairProduct(
            name=payload.name.strip(),
            default_price=payload.default_price,
        )
        try:
            self.db.add(product)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear el producto de feria",
            )
        return self.get_product_by_id(product.id)

    def update_product(
        self, product_id: int, payload: FairProductUpdate
    ) -> FairProduct:
        product = self.get_product_by_id(product_id)
        self._validate_unique_name(payload.name, exclude_id=product_id)
        product.name = payload.name.strip()
        product.default_price = payload.default_price
        try:
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar el producto de feria",
            )
        return self.get_product_by_id(product_id)

    def delete_product(self, product_id: int) -> bool:
        product = (
            self.db.query(FairProduct)
            .filter(FairProduct.id == product_id)
            .first()
        )
        if not product:
            return False

        in_use = (
            self.db.query(FairSale.id)
            .filter(FairSale.fair_product_id == product_id)
            .first()
        )
        if in_use:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "No se puede eliminar: el producto tiene ventas "
                    "registradas en ferias"
                ),
            )

        try:
            self.db.delete(product)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar el producto de feria",
            )
        return True

    def _validate_unique_name(self, name: str, exclude_id: int = None) -> None:
        query = self.db.query(FairProduct).filter(
            FairProduct.name.ilike(name.strip())
        )
        if exclude_id is not None:
            query = query.filter(FairProduct.id != exclude_id)
        if query.first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un producto de feria llamado '{name.strip()}'",
            )

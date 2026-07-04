from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.api_v1.product_expenses.schema import (
    ProductExpenseCreate,
    ProductExpenseUpdate,
)
from app.models.product import Product
from app.models.product_expense import ProductExpense, ProductExpenseCategoryEnum


class ProductExpenseService:
    """
    Servicio de costos de producción por producto (empaque, etiqueta, etc.).

    Los cambios aplican solo a procesos FUTUROS: los lotes ya producidos
    conservan su costo histórico. Para rehacer historia existe el
    endpoint admin POST /process/recalculate-costs.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_expenses(
        self, product_id: Optional[int] = None
    ) -> List[ProductExpense]:
        query = self.db.query(ProductExpense)
        if product_id is not None:
            query = query.filter(ProductExpense.product_id == product_id)
        return query.order_by(desc(ProductExpense.id)).all()

    def get_expense_by_id(self, expense_id: int) -> ProductExpense:
        expense = (
            self.db.query(ProductExpense)
            .filter(ProductExpense.id == expense_id)
            .first()
        )
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Costo de producción no encontrado",
            )
        return expense

    def create_expense(self, payload: ProductExpenseCreate) -> ProductExpense:
        self._get_product_or_404(payload.product_id)

        expense = ProductExpense(
            product_id=payload.product_id,
            category=ProductExpenseCategoryEnum(payload.category),
            amount=payload.amount,
            observations=payload.observations,
        )

        try:
            self.db.add(expense)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear el costo de producción",
            )

        return self.get_expense_by_id(expense.id)

    def update_expense(
        self, expense_id: int, payload: ProductExpenseUpdate
    ) -> ProductExpense:
        expense = self.get_expense_by_id(expense_id)

        update_data = payload.model_dump(exclude_unset=True)
        if "category" in update_data and update_data["category"] is not None:
            expense.category = ProductExpenseCategoryEnum(update_data["category"])
        if "amount" in update_data and update_data["amount"] is not None:
            expense.amount = update_data["amount"]
        if "observations" in update_data:
            expense.observations = update_data["observations"]

        try:
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar el costo de producción",
            )

        return self.get_expense_by_id(expense_id)

    def delete_expense(self, expense_id: int) -> bool:
        expense = (
            self.db.query(ProductExpense)
            .filter(ProductExpense.id == expense_id)
            .first()
        )
        if not expense:
            return False

        try:
            self.db.delete(expense)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar el costo de producción",
            )
        return True

    def _get_product_or_404(self, product_id: int) -> Product:
        product = (
            self.db.query(Product).filter(Product.id == product_id).first()
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found",
            )
        return product

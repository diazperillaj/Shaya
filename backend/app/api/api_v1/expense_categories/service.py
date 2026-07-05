from typing import List

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.api_v1.expense_categories.schema import (
    ExpenseCategoryCreate,
    ExpenseCategoryUpdate,
)
from app.models.expense_category import ExpenseCategory
from app.models.general_expense import GeneralExpense


class ExpenseCategoryService:
    """Catálogo de categorías de gastos generales (Bolsas, Nomina, ...)."""

    def __init__(self, db: Session):
        self.db = db

    def get_categories(self) -> List[ExpenseCategory]:
        return self.db.query(ExpenseCategory).order_by(ExpenseCategory.name).all()

    def get_category_by_id(self, category_id: int) -> ExpenseCategory:
        category = (
            self.db.query(ExpenseCategory)
            .filter(ExpenseCategory.id == category_id)
            .first()
        )
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría de gasto no encontrada",
            )
        return category

    def create_category(self, payload: ExpenseCategoryCreate) -> ExpenseCategory:
        self._validate_unique_name(payload.name)
        category = ExpenseCategory(name=payload.name.strip())
        try:
            self.db.add(category)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear la categoría",
            )
        return self.get_category_by_id(category.id)

    def update_category(
        self, category_id: int, payload: ExpenseCategoryUpdate
    ) -> ExpenseCategory:
        category = self.get_category_by_id(category_id)
        self._validate_unique_name(payload.name, exclude_id=category_id)
        category.name = payload.name.strip()
        try:
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar la categoría",
            )
        return self.get_category_by_id(category_id)

    def delete_category(self, category_id: int) -> bool:
        category = (
            self.db.query(ExpenseCategory)
            .filter(ExpenseCategory.id == category_id)
            .first()
        )
        if not category:
            return False

        in_use = (
            self.db.query(GeneralExpense.id)
            .filter(GeneralExpense.category_id == category_id)
            .first()
        )
        if in_use:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede eliminar: la categoría tiene gastos asociados",
            )

        try:
            self.db.delete(category)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar la categoría",
            )
        return True

    def _validate_unique_name(self, name: str, exclude_id: int = None) -> None:
        query = self.db.query(ExpenseCategory).filter(
            ExpenseCategory.name.ilike(name.strip())
        )
        if exclude_id is not None:
            query = query.filter(ExpenseCategory.id != exclude_id)
        if query.first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una categoría llamada '{name.strip()}'",
            )

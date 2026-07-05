from datetime import date
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.api.api_v1.general_expenses.schema import (
    GeneralExpenseCreate,
    GeneralExpenseUpdate,
)
from app.models.expense_category import ExpenseCategory
from app.models.general_expense import GeneralExpense
from app.models.payment_method import PaymentMethod


class GeneralExpenseService:
    """Gastos generales de la empresa (pestaña Gastos del Excel original)."""

    def __init__(self, db: Session):
        self.db = db

    # ─── Queries ──────────────────────────────────────────────────────────

    def get_expenses(
        self,
        search: Optional[str] = None,
        category_id: Optional[int] = None,
        payment_method_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[GeneralExpense]:
        query = self.db.query(GeneralExpense).options(
            joinedload(GeneralExpense.category),
            joinedload(GeneralExpense.payment_method),
        )
        if search:
            query = query.filter(GeneralExpense.description.ilike(f"%{search}%"))
        if category_id is not None:
            query = query.filter(GeneralExpense.category_id == category_id)
        if payment_method_id is not None:
            query = query.filter(
                GeneralExpense.payment_method_id == payment_method_id
            )
        if date_from is not None:
            query = query.filter(GeneralExpense.expense_date >= date_from)
        if date_to is not None:
            query = query.filter(GeneralExpense.expense_date <= date_to)
        return query.order_by(
            desc(GeneralExpense.expense_date), desc(GeneralExpense.id)
        ).all()

    def get_expense_by_id(self, expense_id: int) -> GeneralExpense:
        expense = (
            self.db.query(GeneralExpense)
            .options(
                joinedload(GeneralExpense.category),
                joinedload(GeneralExpense.payment_method),
            )
            .filter(GeneralExpense.id == expense_id)
            .first()
        )
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gasto no encontrado",
            )
        return expense

    # ─── Create / Update / Delete ─────────────────────────────────────────

    def create_expense(
        self, payload: GeneralExpenseCreate, current_user
    ) -> GeneralExpense:
        self._get_category_or_404(payload.category_id)
        if payload.payment_method_id is not None:
            self._get_payment_method_or_404(payload.payment_method_id)

        expense = GeneralExpense(
            expense_date=payload.expense_date,
            amount=payload.amount,
            category_id=payload.category_id,
            payment_method_id=payload.payment_method_id,
            description=payload.description.strip(),
            created_by=getattr(current_user, "id", None),
        )
        try:
            self.db.add(expense)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear el gasto",
            )
        return self.get_expense_by_id(expense.id)

    def update_expense(
        self, expense_id: int, payload: GeneralExpenseUpdate
    ) -> GeneralExpense:
        expense = self.get_expense_by_id(expense_id)

        update_data = payload.model_dump(exclude_unset=True)
        if update_data.get("category_id") is not None:
            self._get_category_or_404(update_data["category_id"])
            expense.category_id = update_data["category_id"]
        if update_data.get("payment_method_id") is not None:
            self._get_payment_method_or_404(update_data["payment_method_id"])
            expense.payment_method_id = update_data["payment_method_id"]
        if payload.clear_payment_method:
            expense.payment_method_id = None
        if update_data.get("expense_date") is not None:
            expense.expense_date = update_data["expense_date"]
        if update_data.get("amount") is not None:
            expense.amount = update_data["amount"]
        if update_data.get("description") is not None:
            expense.description = update_data["description"].strip()

        try:
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar el gasto",
            )
        return self.get_expense_by_id(expense_id)

    def delete_expense(self, expense_id: int) -> bool:
        expense = (
            self.db.query(GeneralExpense)
            .filter(GeneralExpense.id == expense_id)
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
                detail="Error al eliminar el gasto",
            )
        return True

    # ─── Helpers ──────────────────────────────────────────────────────────

    def _get_category_or_404(self, category_id: int) -> ExpenseCategory:
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

    def _get_payment_method_or_404(self, method_id: int) -> PaymentMethod:
        method = (
            self.db.query(PaymentMethod)
            .filter(PaymentMethod.id == method_id)
            .first()
        )
        if not method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Método de pago no encontrado",
            )
        return method

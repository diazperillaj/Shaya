from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.api_v1.process_expenses.schema import (
    ProcessExpenseCreate,
    ProcessExpenseUpdate,
)
from app.api.api_v1.processes.cost_service import ProcessCostService
from app.models.process import Process
from app.models.process_expense import ProcessExpense, ProcessExpenseCategoryEnum


class ProcessExpenseService:
    """
    Servicio de gastos de producción por proceso (transporte, mano de
    obra, etc.).

    Cada create/update/delete recalcula el unit_cost de los lotes del
    proceso afectado dentro del mismo commit, para que el costo quede
    siempre al día.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_expenses(
        self, process_id: Optional[int] = None
    ) -> List[ProcessExpense]:
        query = self.db.query(ProcessExpense)
        if process_id is not None:
            query = query.filter(ProcessExpense.process_id == process_id)
        return query.order_by(desc(ProcessExpense.id)).all()

    def get_expense_by_id(self, expense_id: int) -> ProcessExpense:
        expense = (
            self.db.query(ProcessExpense)
            .filter(ProcessExpense.id == expense_id)
            .first()
        )
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gasto de proceso no encontrado",
            )
        return expense

    def create_expense(
        self, payload: ProcessExpenseCreate, current_user
    ) -> ProcessExpense:
        self._get_process_or_404(payload.process_id)

        expense = ProcessExpense(
            process_id=payload.process_id,
            category=ProcessExpenseCategoryEnum(payload.category),
            amount=payload.amount,
            expense_date=payload.expense_date,
            observations=payload.observations,
            created_by=getattr(current_user, "id", None),
        )

        try:
            self.db.add(expense)
            self.db.flush()
            ProcessCostService(self.db).recalculate_process_costs(
                payload.process_id
            )
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear el gasto de proceso",
            )

        return self.get_expense_by_id(expense.id)

    def update_expense(
        self, expense_id: int, payload: ProcessExpenseUpdate
    ) -> ProcessExpense:
        expense = self.get_expense_by_id(expense_id)

        update_data = payload.model_dump(exclude_unset=True)
        if "category" in update_data and update_data["category"] is not None:
            expense.category = ProcessExpenseCategoryEnum(update_data["category"])
        if "amount" in update_data and update_data["amount"] is not None:
            expense.amount = update_data["amount"]
        if "expense_date" in update_data and update_data["expense_date"] is not None:
            expense.expense_date = update_data["expense_date"]
        if "observations" in update_data:
            expense.observations = update_data["observations"]

        try:
            self.db.flush()
            ProcessCostService(self.db).recalculate_process_costs(
                expense.process_id
            )
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar el gasto de proceso",
            )

        return self.get_expense_by_id(expense_id)

    def delete_expense(self, expense_id: int) -> bool:
        expense = (
            self.db.query(ProcessExpense)
            .filter(ProcessExpense.id == expense_id)
            .first()
        )
        if not expense:
            return False

        process_id = expense.process_id
        try:
            self.db.delete(expense)
            self.db.flush()
            ProcessCostService(self.db).recalculate_process_costs(process_id)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar el gasto de proceso",
            )
        return True

    def _get_process_or_404(self, process_id: int) -> Process:
        process = (
            self.db.query(Process).filter(Process.id == process_id).first()
        )
        if not process:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Process not found",
            )
        return process

from typing import List

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.api_v1.payment_methods.schema import (
    PaymentMethodCreate,
    PaymentMethodUpdate,
)
from app.models.fair_sale import FairSale
from app.models.general_expense import GeneralExpense
from app.models.payment_method import PaymentMethod
from app.models.sale import Sale


class PaymentMethodService:
    """Catálogo de métodos/lugares de pago (Efectivo, Nequi, Nu, ...)."""

    def __init__(self, db: Session):
        self.db = db

    def get_methods(self) -> List[PaymentMethod]:
        return self.db.query(PaymentMethod).order_by(PaymentMethod.name).all()

    def get_method_by_id(self, method_id: int) -> PaymentMethod:
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

    def create_method(self, payload: PaymentMethodCreate) -> PaymentMethod:
        self._validate_unique_name(payload.name)
        method = PaymentMethod(name=payload.name.strip())
        try:
            self.db.add(method)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear el método de pago",
            )
        return self.get_method_by_id(method.id)

    def update_method(
        self, method_id: int, payload: PaymentMethodUpdate
    ) -> PaymentMethod:
        method = self.get_method_by_id(method_id)
        self._validate_unique_name(payload.name, exclude_id=method_id)
        method.name = payload.name.strip()
        try:
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar el método de pago",
            )
        return self.get_method_by_id(method_id)

    def delete_method(self, method_id: int) -> bool:
        method = (
            self.db.query(PaymentMethod)
            .filter(PaymentMethod.id == method_id)
            .first()
        )
        if not method:
            return False

        in_use = (
            self.db.query(Sale.id).filter(Sale.payment_method_id == method_id).first()
            or self.db.query(FairSale.id)
            .filter(FairSale.payment_method_id == method_id)
            .first()
            or self.db.query(GeneralExpense.id)
            .filter(GeneralExpense.payment_method_id == method_id)
            .first()
        )
        if in_use:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "No se puede eliminar: el método de pago está en uso "
                    "por ventas o gastos"
                ),
            )

        try:
            self.db.delete(method)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar el método de pago",
            )
        return True

    def _validate_unique_name(self, name: str, exclude_id: int = None) -> None:
        query = self.db.query(PaymentMethod).filter(
            PaymentMethod.name.ilike(name.strip())
        )
        if exclude_id is not None:
            query = query.filter(PaymentMethod.id != exclude_id)
        if query.first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un método de pago llamado '{name.strip()}'",
            )

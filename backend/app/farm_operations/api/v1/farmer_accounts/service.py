from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.api_v1.farmers.service import format_name
from app.core.exceptions.domain import ConflictError, NotFoundError
from app.core.roles import UserRole
from app.core.security import get_password_hash
from app.farm_operations.api.v1.farmer_accounts.schema import (
    FarmerAccountCreate,
    FarmerAccountCreateFull,
)
from app.farm_operations.models import Farm
from app.models.farmer import Farmer
from app.models.person import Person
from app.models.user import User


class FarmerAccountService:
    """
    Cuentas de acceso de los caficultores (especificacion-api §3.12).

    Un caficultor con acceso es una sola persona con dos registros: el de
    caficultor y el de usuario con rol `farmer`. No hay autoregistro: las
    cuentas las crea un administrador.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_accounts(self) -> List[dict]:
        rows = (
            self.db.query(Farmer, Person, User)
            .join(Person, Farmer.person_id == Person.id)
            .outerjoin(User, User.person_id == Person.id)
            .order_by(Person.full_name)
            .all()
        )
        farms = dict(
            self.db.query(Farm.farmer_id, func.count(Farm.id)).group_by(Farm.farmer_id).all()
        )
        return [self._to_response(farmer, person, user, farms.get(farmer.id, 0)) for farmer, person, user in rows]

    def create_account(self, payload: FarmerAccountCreate) -> dict:
        farmer = self.db.query(Farmer).filter(Farmer.id == payload.farmer_id).first()
        if not farmer:
            raise NotFoundError("Caficultor no encontrado")
        if self.db.query(User.id).filter(User.person_id == farmer.person_id).first():
            raise ConflictError("Este caficultor ya tiene una cuenta de usuario")
        self._validate_username(payload.username)

        self.db.add(self._farmer_user(payload.username, payload.password, farmer.person))
        self.db.commit()
        return self._account(farmer.id)

    def create_full(self, payload: FarmerAccountCreateFull) -> dict:
        person_data = payload.person
        if person_data.document and self.db.query(Person.id).filter(Person.document == person_data.document).first():
            raise ConflictError("El documento ya existe")
        if person_data.email and self.db.query(Person.id).filter(Person.email == person_data.email).first():
            raise ConflictError("El correo ya existe")
        self._validate_username(payload.username)

        person = Person(
            full_name=format_name(person_data.full_name),
            document=person_data.document,
            phone=person_data.phone,
            email=person_data.email,
            observation=person_data.observation,
        )
        farmer = Farmer(
            farm_name=payload.farm_name,
            village=payload.village,
            municipality=payload.municipality,
            person=person,
        )
        # Persona, caficultor y usuario en una sola transacción
        self.db.add_all([farmer, self._farmer_user(payload.username, payload.password, person)])
        self.db.commit()
        return self._account(farmer.id)

    # ── Internos ──────────────────────────────────────────────────────────

    @staticmethod
    def _farmer_user(username: str, password: str, person: Person) -> User:
        return User(
            username=username,
            hashed_password=get_password_hash(password),
            role=UserRole.farmer.value,
            person=person,
        )

    def _validate_username(self, username: str) -> None:
        if self.db.query(User.id).filter(User.username == username).first():
            raise ConflictError("El nombre de usuario ya existe")

    def _account(self, farmer_id: int) -> dict:
        return next(account for account in self.get_accounts() if account["farmer_id"] == farmer_id)

    @staticmethod
    def _to_response(farmer: Farmer, person: Person, user, farms: int) -> dict:
        return {
            "farmer_id": farmer.id,
            "full_name": person.full_name,
            "document": person.document,
            "phone": person.phone,
            "farms": farms,
            "user_id": user.id if user else None,
            "username": user.username if user else None,
            "account_role": user.role if user else None,
        }

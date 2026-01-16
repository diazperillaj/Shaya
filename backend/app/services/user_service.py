from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.models.user import User
from app.models.person import Person
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash

def format_name(name: str) -> str:
    exceptions = {'de', 'del', 'la', 'las', 'los', 'y'}
    return ' '.join(
        word.capitalize() if word.lower() not in exceptions else word.lower()
        for word in name.split()
    )

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_users(self):
        return (
            self.db
            .query(User)
            .options(joinedload(User.person))
            .join(User.person)
            .order_by(Person.full_name.asc())
            .all()
        )

    def get_user_by_id(self, user_id: int) -> User:
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, user_data: UserCreate) -> User:
        # 1️⃣ Crear persona
        person = Person(
            full_name=format_name(user_data.person.full_name),
            document=user_data.person.document,
            phone=user_data.person.phone,
            email=user_data.person.email,
            observation=user_data.person.observation
        )
        # 2️⃣ Crear usuario
        user = User(
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            role=user_data.role,
            person=person
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_user(self, user_id: int, user_data: UserUpdate):
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            return None

        # 🔹 Campos simples
        if user_data.username is not None:
            user.username = user_data.username

        if user_data.role is not None:
            user.role = user_data.role

        # 🔹 Password (solo si viene)
        if user_data.password:
            user.hashed_password = get_password_hash(user_data.password)

        # 🔹 Persona
        if user_data.person:
            person = user.person

            person.full_name = format_name(user_data.person.full_name)
            person.document = user_data.person.document
            person.phone = user_data.person.phone
            person.email = user_data.person.email
            person.observation = user_data.person.observation

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int) -> bool:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        # Borra primero la persona asociada
        if user.person:
            self.db.delete(user.person)
        self.db.delete(user)
        self.db.commit()
        return True
    
    def get_users_filtered(self, search: str = None, role: str = None):
        query = self.db.query(User).options(joinedload(User.person))

        if search:
            query = query.join(User.person).filter(
                or_(
                    User.username.ilike(f"%{search}%"),
                    Person.full_name.ilike(f"%{search}%")
                )
            )

        if role:
            query = query.filter(User.role == role)

        return query.join(User.person).order_by(Person.full_name.asc()).all()
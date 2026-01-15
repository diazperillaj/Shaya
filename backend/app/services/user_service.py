from sqlalchemy.orm import Session
from app.models.user import User
from app.models.person import Person
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_users(self):
        return self.db.query(User).all()

    def get_user_by_id(self, user_id: int) -> User:
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, user_data: UserCreate) -> User:
        # 1️⃣ Crear persona
        person = Person(
            full_name=user_data.person.full_name,
            document=user_data.person.document,
            phone=user_data.person.phone,
            email=user_data.person.email,
            observation=user_data.person.observation
        )
        # 2️⃣ Crear usuario
        user = User(
            username=user_data.username,
            hashed_password=get_password_hash(user_data.hashed_password),
            role=user_data.role,
            person=person
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

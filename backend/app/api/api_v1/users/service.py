from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.models.user import User
from app.models.person import Person
from app.api.api_v1.users.schema import UserCreate, UserUpdate
from app.core.security import get_password_hash
from sqlalchemy import desc

#Manejo de excepciones
from fastapi import HTTPException, status



def raise_if_exists(query, detail: str):
    """
    Valida la existencia previa de un registro en la base de datos.

    Args:
        query: Consulta SQLAlchemy que será evaluada.
        detail (str): Mensaje de error a devolver si el registro existe.

    Raises:
        HTTPException: Si la consulta retorna un resultado.
    """

    if query.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )



def format_name(name: str) -> str:
    """
    Normaliza nombres propios respetando preposiciones y conectores.

    Convierte cada palabra a mayúscula inicial, excepto:
    'de', 'del', 'la', 'las', 'los', 'y'.

    Ejemplo:
        Entrada:  "maria de las mercedes"
        Salida:   "Maria de las Mercedes"

    Args:
        name (str): Nombre completo a formatear.

    Returns:
        str: Nombre formateado.
    """

    exceptions = {'de', 'del', 'la', 'las', 'los', 'y'}
    return ' '.join(
        word.capitalize() if word.lower() not in exceptions else word.lower()
        for word in name.split()
    )



class UserService:
    """
    Servicio encargado de la lógica de negocio relacionada con usuarios.

    Separa la lógica de persistencia de los endpoints HTTP.
    """



    def __init__(self, db: Session):
        """
        Inicializa el servicio con una sesión de base de datos.

        Args:
            db (Session): Sesión activa de SQLAlchemy.
        """

        self.db = db



    def get_users(self):
        """
        Obtiene la lista de usuarios registrados.

        Incluye la información de la persona asociada y ordena
        los resultados por ID descendente (últimos primero).

        Returns:
            List[User]: Lista de usuarios.
        """

        return (
            self.db
            .query(User)
            .options(joinedload(User.person))
            .join(User.person)
            .order_by(desc(User.id))
            .all()
        )



    def get_user_by_id(self, user_id: int) -> User:
        """
        Obtiene un usuario a partir de su identificador único.

        Args:
            user_id (int): ID del usuario.

        Returns:
            User | None: Usuario encontrado o None si no existe.
        """

        return self.db.query(User).filter(User.id == user_id).first()



    def create_user(self, user_data: UserCreate) -> User:
        """
        Crea un nuevo usuario en el sistema.

        Valida previamente:
        - Username
        - Documento
        - Correo electrónico

        Args:
            user_data (UserCreate): Datos del usuario a crear.

        Returns:
            User: Usuario creado exitosamente.

        Raises:
            HTTPException: Si alguno de los datos ya existe.
        """

        raise_if_exists(
            self.db.query(User).filter(User.username == user_data.username),
            "El usuario ya existe"
        )

        raise_if_exists(
            self.db.query(Person).filter(Person.document == user_data.person.document),
            "El documento ya existe"
        )

        raise_if_exists(
            self.db.query(Person).filter(Person.email == user_data.person.email),
            "El correo ya existe"
        )

        person = Person(
            full_name=format_name(user_data.person.full_name),
            document=user_data.person.document,
            phone=user_data.person.phone,
            email=user_data.person.email,
            observation=user_data.person.observation
        )

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
        """
        Actualiza la información de un usuario existente.

        Permite actualización parcial de datos.

        Args:
            user_id (int): ID del usuario.
            user_data (UserUpdate): Datos a modificar.

        Returns:
            User | None: Usuario actualizado o None si no existe.
        """

        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            return None

        if user_data.username is not None:
            user.username = user_data.username

        if user_data.role is not None:
            user.role = user_data.role

        if user_data.password:
            user.hashed_password = get_password_hash(user_data.password)

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
        """
        Elmina al usuario por su identificador unico.

        Valida antes si existe el usuario.

        Args:
            user_id (int): Identificador unico.

        Returns:
            Boolean: True si se elimino, false si no lo logro.
        """

        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            return False

        if user.person:
            self.db.delete(user.person)

        self.db.delete(user)
        self.db.commit()

        return True
    


    def get_users_filtered(self, search: str = None, role: str = None):
        """
        Obtiene usuarios aplicando filtros opcionales.

        Permite buscar por:
        - Username
        - Nombre completo
        - Rol
        - Correo electronico

        Args:
            search (str, opcional): Texto de búsqueda.
            role (str, opcional): Rol del usuario.

        Returns:
            List[User]: Usuarios que cumplen los criterios.
        """

        query = self.db.query(User).options(joinedload(User.person))

        if search:
            query = query.join(User.person).filter(
                or_(
                    User.username.ilike(f"%{search}%"),
                    Person.full_name.ilike(f"%{search}%"),
                    Person.email.ilike(f"%{search}%")
                )
            )

        if role:
            query = query.filter(User.role == role)

        return query.join(User.person).order_by(Person.full_name.asc()).all()
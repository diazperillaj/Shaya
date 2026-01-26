from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.models.farmer import Farmer
from app.models.person import Person
from app.api.api_v1.farmers.schema import FarmerCreate, FarmerUpdate
from sqlalchemy import desc
from typing import List

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



class FarmerService:
    """
    Servicio encargado de la lógica de negocio relacionada con caficultores.

    Separa la lógica de persistencia de los endpoints HTTP.
    """



    def __init__(self, db: Session):
        """
        Inicializa el servicio con una sesión de base de datos.

        Args:
            db (Session): Sesión activa de SQLAlchemy.
        """

        self.db = db



    def get_farmers(self) -> List[Farmer]:
        """
        Obtiene la lista de caficultores registrados.

        Incluye la información de la persona asociada y ordena
        los resultados por ID descendente (últimos primero).

        Returns:
            List[User]: Lista de caficultores.
        """

        return (
            self.db
            .query(Farmer)
            .options(joinedload(Farmer.person))
            .join(Farmer.person)
            .order_by(desc(Farmer.id))
            .all()
        )



    def get_farmer_by_id(self, farmer_id: int) -> Farmer:
        """
        Obtiene un caficultor a partir de su identificador único.

        Args:
            farmer_id (int): ID del caficultor.

        Returns:
            farmer | None: Caficultor encontrado o None si no existe.
        """

        return self.db.query(Farmer).filter(Farmer.id == farmer_id).first()



    def create_farmer(self, farmer_data: FarmerCreate) -> Farmer:
        """
        Crea un nuevo caficultor en el sistema.

        Valida previamente:
        - Documento
        - Correo electrónico

        Args:
            farmer_data (UserCreate): Datos del caficultor a crear.

        Returns:
            User: Caficultor creado exitosamente.

        Raises:
            HTTPException: Si alguno de los datos ya existe.
        """

        raise_if_exists(
            self.db.query(Person).filter(Person.document == farmer_data.person.document),
            "El documento ya existe"
        )

        raise_if_exists(
            self.db.query(Person).filter(Person.email == farmer_data.person.email),
            "El correo ya existe"
        )

        person = Person(
            full_name=format_name(farmer_data.person.full_name),
            document=farmer_data.person.document,
            phone=farmer_data.person.phone,
            email=farmer_data.person.email,
            observation=farmer_data.person.observation
        )

        farmer = Farmer(
            farm_name=farmer_data.farm_name,
            farm_location=farmer_data.farm_location,
            person=person
        )

        self.db.add(farmer)
        self.db.commit()
        self.db.refresh(farmer)
        return farmer
    


    def update_farmer(self, farmer_id: int, farmer_data: FarmerUpdate) -> Farmer:
        """
        Actualiza la información de un caficultor existente.

        Permite actualización parcial de datos.

        Args:
            farmer_id (int): ID del caficultor.
            farmer_data (UserUpdate): Datos a modificar.

        Returns:
            User | None: Caficultor actualizado o None si no existe.
        """

        farmer = self.db.query(Farmer).filter(Farmer.id == farmer_id).first()

        if farmer_data.person and farmer_data.person.document:
            raise_if_exists(
                self.db.query(Person).filter(
                    Person.document == farmer_data.person.document,
                    Person.id != farmer.person.id
                ),
                "El documento ya existe"
            )
            
        if farmer_data.person and farmer_data.person.email:
            raise_if_exists(
                self.db.query(Person).filter(
                    Person.email == farmer_data.person.email,
                    Person.id != farmer.person.id
                ),
                "El correo ya existe"
            )
        
        if not farmer:
            return None

        if farmer_data.farm_location is not None:
            farmer.farm_location = farmer_data.farm_location

        if farmer_data.farm_name is not None:
            farmer.farm_name = farmer_data.farm_name

        if farmer_data.person:
            person = farmer.person

            person.full_name = format_name(farmer_data.person.full_name)
            person.document = farmer_data.person.document
            person.phone = farmer_data.person.phone
            person.email = farmer_data.person.email
            person.observation = farmer_data.person.observation

        self.db.commit()
        self.db.refresh(farmer)
        return farmer



    def delete_farmer(self, farmer_id: int) -> bool:
        """
        Elmina al caficultor por su identificador unico.

        Valida antes si existe el caficultor.

        Args:
            farmer_id (int): Identificador unico.

        Returns:
            Boolean: True si se elimino, false si no lo logro.
        """

        farmer = self.db.query(Farmer).filter(Farmer.id == farmer_id).first()

        if not farmer:
            return False

        if farmer.person:
            self.db.delete(farmer.person)

        self.db.delete(farmer)
        self.db.commit()

        return True
    



    def get_farmers_filtered(self, search: str = None) -> List[Farmer]:
        """
        Obtiene caficultores aplicando filtros opcionales.

        Permite buscar por:
        - Nombre completo
        - Correo electronico

        Args:
            search (str, opcional): Texto de búsqueda.

        Returns:
            List[Farmer]: Caficultores que cumplen los criterios.
        """

        query = self.db.query(Farmer).options(joinedload(Farmer.person))

        if search:
            query = query.join(Farmer.person).filter(
                or_(
                    Person.full_name.ilike(f"%{search}%"),
                    Person.email.ilike(f"%{search}%")
                )
            )


        return query.join(Farmer.person).order_by(Person.full_name.asc()).all()
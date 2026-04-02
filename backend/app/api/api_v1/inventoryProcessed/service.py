from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.models.customer import Customer
from app.models.person import Person
from app.api.api_v1.customers.schema import CustomerCreate, CustomerUpdate
from sqlalchemy import desc
from typing import List

#Manejo de excepciones
from fastapi import HTTPException, status



def raise_if_exists(query, detail: str):
    """
    Valida la existencia previa de un registro en la base de datos.

    Args:`
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



class CustomerService:
    """
    Servicio encargado de la lógica de negocio relacionada con clientes.

    Separa la lógica de persistencia de los endpoints HTTP.
    """



    def __init__(self, db: Session):
        """
        Inicializa el servicio con una sesión de base de datos.

        Args:
            db (Session): Sesión activa de SQLAlchemy.
        """

        self.db = db



    def get_customers(self) -> List[Customer]:
        """
        Obtiene la lista de clientes registrados.

        Incluye la información de la persona asociada y ordena
        los resultados por ID descendente (últimos primero).

        Returns:
            List[Customer]: Lista de clientes.
        """

        return (
            self.db
            .query(Customer)
            .options(joinedload(Customer.person))
            .join(Customer.person)
            .order_by(desc(Customer.id))
            .all()
        )



    def get_customer_by_id(self, customer_id: int) -> Customer:
        """
        Obtiene un cliente a partir de su identificador único.

        Args:
            customer_id (int): ID del cliente.

        Returns:
            customer | None: Cliente encontrado o None si no existe.
        """

        return self.db.query(Customer).filter(Customer.id == customer_id).first()



    def create_customer(self, customer_data: CustomerCreate) -> Customer:
        """
        Crea un nuevo cliente en el sistema.

        Valida previamente:
        - Documento
        - Correo electrónico

        Args:
            customer_data (CustomerCreate): Datos del cliente a crear.

        Returns:
            Customer: Cliente creado exitosamente.

        Raises:
            HTTPException: Si alguno de los datos ya existe.
        """

        raise_if_exists(
            self.db.query(Person).filter(Person.document == customer_data.person.document),
            "El documento ya existe"
        )

        raise_if_exists(
            self.db.query(Person).filter(Person.email == customer_data.person.email),
            "El correo ya existe"
        )

        person = Person(
            full_name=format_name(customer_data.person.full_name),
            document=customer_data.person.document,
            phone=customer_data.person.phone,
            email=customer_data.person.email,
            observation=customer_data.person.observation
        )

        customer = Customer(
            customerType=customer_data.customerType,
            address=customer_data.address,
            city=customer_data.city,
            person=person
        )

        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer
    


    def update_customer(self, customer_id: int, customer_data: CustomerUpdate) -> Customer:
        """
        Actualiza la información de un cliente existente.

        Permite actualización parcial de datos.

        Args:
            customer_id (int): ID del cliente.
            customer_data (UserUpdate): Datos a modificar.

        Returns:
            Customer | None: Cliente actualizado o None si no existe.
        """

        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()


        if customer_data.person and customer_data.person.document:
            raise_if_exists(
                self.db.query(Person).filter(
                    Person.document == customer_data.person.document,
                    Person.id != customer.person.id
                ),
                "El documento ya existe"
            )
            
        if customer_data.person and customer_data.person.email:
            raise_if_exists(
                self.db.query(Person).filter(
                    Person.email == customer_data.person.email,
                    Person.id != customer.person.id
                ),
                "El correo ya existe"
            )
        

        if not customer:
            return None

        if customer_data.customerType is not None:
            customer.customerType = customer_data.customerType

        if customer_data.address is not None:
            customer.address = customer_data.address
        
        if customer_data.city is not None:
            customer.city = customer_data.city

        if customer_data.person:
            person = customer.person

            person.full_name = format_name(customer_data.person.full_name)
            person.document = customer_data.person.document
            person.phone = customer_data.person.phone
            person.email = customer_data.person.email
            person.observation = customer_data.person.observation

        self.db.commit()
        self.db.refresh(customer)
        return customer



    def delete_customer(self, customer_id: int) -> bool:
        """
        Elmina al cliente por su identificador unico.

        Valida antes si existe el cliente.

        Args:
            customer_id (int): Identificador unico.

        Returns:
            Boolean: True si se elimino, false si no lo logro.
        """

        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()

        if not customer:
            return False

        if customer.person:
            self.db.delete(customer.person)

        self.db.delete(customer)
        self.db.commit()

        return True
    



    def get_customers_filtered(self, search: str = None) -> List[Customer]:
        """
        Obtiene clientes aplicando filtros opcionales.

        Permite buscar por:
        - Nombre completo
        - Correo electronico
        - Ciudad
        - Direccion

        Args:
            search (str, opcional): Texto de búsqueda.

        Returns:
            List[Customer]: Clientes que cumplen los criterios.
        """

        query = self.db.query(Customer).options(joinedload(Customer.person))

        if search:
            query = query.join(Customer.person).filter(
                or_(
                    Person.full_name.ilike(f"%{search}%"),
                    Person.email.ilike(f"%{search}%"),
                    Customer.address.ilike(f"%{search}%"),
                    Customer.city.ilike(f"%{search}%")
                )
            )


        return query.join(Customer.person).order_by(Person.full_name.asc()).all()
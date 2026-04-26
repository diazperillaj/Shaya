from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.models.product import Product
from app.api.api_v1.products.schema import ProductCreate, ProductUpdate
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



class ProductService:
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



    def get_products(self) -> List[Product]:
        """
        Obtiene la lista de productos registrados.

        Incluye la información de la persona asociada y ordena
        los resultados por ID descendente (últimos primero).

        Returns:
            List[User]: Lista de caficultores.
        """

        return (
            self.db
            .query(Product)
            .order_by(desc(Product.id))
            .all()
        )



    def get_product_by_id(self, product_id: int) -> Product:
        """
        Obtiene un producto a partir de su identificador único.

        Args:
            product_id (int): ID del producto.

        Returns:
            product | None: Producto encontrado o None si no existe.
        """

        return self.db.query(Product).filter(Product.id == product_id).first()



    def create_product(self, product_data: ProductCreate) -> Product:
        """
        Crea un nuevo producto en el sistema.

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


        product = Product(
            name=product_data.name,
            quantity=product_data.quantity,
            type=product_data.type,
            description=product_data.description
        )

        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    


    def update_product(self, product_id: int, product_data: ProductUpdate) -> Product:
        """
        Actualiza la información de un caficultor existente.

        Permite actualización parcial de datos.

        Args:
            farmer_id (int): ID del caficultor.
            farmer_data (UserUpdate): Datos a modificar.

        Returns:
            User | None: Caficultor actualizado o None si no existe.
        """

        product = self.db.query(Product).filter(Product.id == product_id).first()

        if product_data.name is not None:
            product.name = product_data.name

        if product_data.quantity is not None:
            product.quantity = product_data.quantity

        if product_data.type is not None:
            product.type = product_data.type

        if product_data.description is not None:
            product.description = product_data.description

        self.db.commit()
        self.db.refresh(product)
        return product


    def delete_product(self, product_id: int) -> bool:
        """
        Elmina al caficultor por su identificador unico.

        Valida antes si existe el caficultor.

        Args:
            farmer_id (int): Identificador unico.

        Returns:
            Boolean: True si se elimino, false si no lo logro.
        """

        product = self.db.query(Product).filter(Product.id == product_id).first()

        if not product:
            return False

        self.db.delete(product)
        self.db.commit()

        return True
    



    def get_products_filtered(self, search: str = None) -> List[Product]:
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

        query = self.db.query(Product)

        if search:
            query = query.join(Product.person).filter(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%")
                )
            )


        return query.join(Product.person).all()
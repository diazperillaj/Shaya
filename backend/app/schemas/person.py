from pydantic import BaseModel, EmailStr, StringConstraints
from typing import Optional
from typing_extensions import Annotated


"""
Módulo de esquemas Pydantic para la entidad Person.

Este módulo define los esquemas utilizados para:
- Validar datos de entrada (creación de personas)
- Estructurar datos de salida (respuestas de la API)

Las validaciones estrictas se aplican únicamente en los esquemas de entrada.
"""


# =========================
# Tipos reutilizables
# =========================

"""
Phone

Tipo de dato reutilizable para números telefónicos.

Reglas:
- Debe ser un string
- Solo permite caracteres numéricos
- Debe contener exactamente 10 dígitos

Ejemplo válido:
- "3124567890"

Ejemplos inválidos:
- "312456789"   (menos de 10 dígitos)
- "31245abc90"  (contiene letras)
"""
Phone = Annotated[
    str,
    StringConstraints(pattern=r'^\d{10}$')
]


"""
Document

Tipo de dato reutilizable para documentos de identificación.

Reglas:
- Debe ser un string
- Solo permite caracteres numéricos
- Longitud variable (uno o más dígitos)

Ejemplo válido:
- "1023456789"

Ejemplos inválidos:
- "ABC123"
- "123-456"
"""
Document = Annotated[
    str,
    StringConstraints(pattern=r'^\d+$')
]


# =========================
# Schemas de entrada
# =========================

class PersonCreate(BaseModel):
    """
    Esquema utilizado para la creación de una persona.

    Este modelo se usa en operaciones de entrada (POST / PUT) y
    aplica validaciones estrictas sobre los campos.

    Attributes:
        full_name (str): Nombre completo de la persona.
        document (Document): Documento de identificación (solo números).
        phone (Phone): Número telefónico de 10 dígitos.
        email (EmailStr): Correo electrónico válido.
        observation (Optional[str]): Observaciones adicionales (opcional).
    """

    full_name: str
    document: Document
    phone: Phone
    email: EmailStr
    observation: Optional[str] = None


# =========================
# Schemas de salida
# =========================

class PersonResponse(BaseModel):
    """
    Esquema utilizado para las respuestas de la API relacionadas con personas.

    Este modelo refleja la estructura de los datos almacenados en la base de datos
    y NO aplica validaciones estrictas de formato, evitando errores de validación
    en las respuestas.

    Attributes:
        id (int): Identificador único de la persona.
        full_name (str): Nombre completo.
        document (str): Documento de identificación.
        phone (str): Número telefónico.
        email (EmailStr): Correo electrónico.
        observation (Optional[str]): Observaciones adicionales.
    """

    id: int
    full_name: str
    document: str
    phone: str
    email: EmailStr
    observation: Optional[str] = None

    class Config:
        orm_mode = True

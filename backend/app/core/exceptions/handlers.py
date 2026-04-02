from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

ERRORS = {
    "document": "El documento debe ser un valor numérico",
    "rol": "Rol inválido. Debe ser 'admin' o 'user'",
    "phone": "El número debe ser un valor númerico de 10 caracteres",
    "password": "La contraseña debe tener al menos 6 caracteres",
    "username": "El usuario debe contener al menos 4 caracteres"
}

def raise_error(detail: str, status_code: int = 400):
    """
    Genera una respuesta JSON de error estandarizada.

    Args:
        detail (str): Mensaje descriptivo del error.
        status_code (int): Código HTTP (por defecto 400).

    Returns:
        JSONResponse: Respuesta de error formateada.
    """

    return JSONResponse(
        status_code=status_code,
        content={"detail": detail}
    )

def register_exception_handlers(app):
    """
    Registra los manejadores globales de excepciones de la aplicación.

    Centraliza el manejo de errores de validación y de integridad
    provenientes de FastAPI y SQLAlchemy.

    Args:
        app: Instancia de FastAPI.
    """

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Maneja errores de validación de solicitudes HTTP.

        Traduce los errores técnicos de Pydantic a mensajes
        personalizados y legibles para el cliente.
        """

        for error in exc.errors():
            field = error["loc"][-1]

            if field in ERRORS:
                return raise_error(ERRORS[field])


    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        """
        Maneja errores de integridad de base de datos.

        Detecta violaciones de claves únicas y devuelve
        mensajes amigables al cliente.
        """
        
        msg = str(exc.orig)

        if "users_username_key" in msg:
            detail = "El nombre de usuario ya existe"
        elif "persons_email_key" in msg:
            detail = "El correo ya está registrado"
        else:
            detail = "Error de integridad en la base de datos"

        return JSONResponse(
            status_code=400,
            content={"detail": detail}
        )

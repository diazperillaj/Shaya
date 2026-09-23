class DomainError(Exception):
    """
    Error de una regla de negocio, independiente de FastAPI.

    Los servicios lanzan esta excepción (o una subclase) sin conocer HTTP, y
    el manejador global la traduce a una respuesta con `status_code` y
    `detail`. Así la misma lógica funciona desde la API, los scripts y las
    pruebas.
    """

    status_code: int = 400

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class NotFoundError(DomainError):
    """El recurso no existe o está fuera del alcance del usuario."""

    status_code = 404


class ConflictError(DomainError):
    """La operación choca con el estado actual (p. ej. cerrar algo ya cerrado)."""

    status_code = 409


class PermissionDeniedError(DomainError):
    """El usuario no tiene permiso para la operación."""

    status_code = 403

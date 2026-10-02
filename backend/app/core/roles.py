from enum import Enum


class UserRole(str, Enum):
    """
    Roles de usuario del sistema.

    - `admin` y `user`: personal de Shaya, con acceso a los módulos del
      negocio (ventas, inventario, gastos…).
    - `farmer`: caficultor externo. Solo accede al módulo de cultivo y
      únicamente a sus propias fincas. Su cuenta se crea desde el módulo de
      cultivo, enlazada a su registro de caficultor.
    """

    admin = "admin"
    user = "user"
    farmer = "farmer"


class StaffRole(str, Enum):
    """Roles del personal de Shaya: los únicos que administra el módulo de Usuarios."""

    admin = "admin"
    user = "user"


# Roles admitidos por cada control de acceso
STAFF_ROLES = frozenset(role.value for role in StaffRole)
FARM_ROLES = frozenset({UserRole.admin.value, UserRole.farmer.value})

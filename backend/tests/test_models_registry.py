"""
El registro central carga todos los modelos por sí solo.

Se prueba en un intérprete nuevo: en esta sesión de pytest la app ya importó
los modelos por otros caminos y ocultaría un olvido del registro.
"""

import subprocess
import sys

CHECK = """
import pkgutil, sys
from sqlalchemy.orm import configure_mappers

from app import models_registry
import app.models
import app.farm_operations.models

configure_mappers()

packages = {"app.models": app.models, "app.farm_operations.models": app.farm_operations.models}
missing = [
    f"{prefix}.{module.name}"
    for prefix, package in packages.items()
    for module in pkgutil.iter_modules(package.__path__)
    if f"{prefix}.{module.name}" not in sys.modules
]
assert not missing, f"Modelos fuera del registro: {missing}"
"""


def test_registry_alone_loads_every_model():
    result = subprocess.run(
        [sys.executable, "-c", CHECK], capture_output=True, text=True
    )

    assert result.returncode == 0, result.stderr

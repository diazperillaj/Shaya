"""
Servicios transversales del módulo de cultivo.

Lógica que cruza recursos (alcance por finca, resolución de alertas…). No
dependen de FastAPI: lanzan errores de dominio (`app/core/exceptions/domain`)
para poder reutilizarse desde la API, los scripts y las pruebas.
"""

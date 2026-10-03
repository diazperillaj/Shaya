"""
Modelos ORM del módulo de cultivo.

Todo modelo nuevo del módulo se importa aquí; el registro central
(`app/models_registry.py`) importa este paquete.
"""

from app.farm_operations.models.alert_config import AlertConfig  # noqa: F401
from app.farm_operations.models.climate_record import ClimateRecord  # noqa: F401
from app.farm_operations.models.crop_cycle import CropCycle  # noqa: F401
from app.farm_operations.models.day_labor import DayLabor  # noqa: F401
from app.farm_operations.models.drying import Drying, DryingHumidityCheck, DryingInput  # noqa: F401
from app.farm_operations.models.employee import Employee  # noqa: F401
from app.farm_operations.models.farm import Farm  # noqa: F401
from app.farm_operations.models.harvest import Harvest, HarvestWork  # noqa: F401
from app.farm_operations.models.labors import (  # noqa: F401
    CulturalPractice,
    Fertilization,
    FloweringRecord,
    Irrigation,
    PestMonitoring,
    PhytosanitaryApp,
    SoilAnalysis,
)
from app.farm_operations.models.plot import Plot, PlotEvent  # noqa: F401
from app.farm_operations.models.quality_eval import QualityEval  # noqa: F401
from app.farm_operations.models.supply import Supply  # noqa: F401
from app.farm_operations.models.wet_processing import WetProcessing, WetProcessingInput  # noqa: F401

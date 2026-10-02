from typing import Optional

from sqlalchemy.orm import Session

from app.farm_operations.api.v1.alert_configs.schema import AlertConfigValues
from app.farm_operations.models import AlertConfig
from app.farm_operations.services import alerts
from app.farm_operations.services.access import FarmAccess


class AlertConfigService:
    """
    Configuración de alertas en dos niveles: finca (aplica a todos sus lotes)
    y lote (sobreescribe a la finca).
    """

    def __init__(self, db: Session, access: FarmAccess):
        self.db = db
        self.access = access

    def resolved_for_farm(self, farm_id: int) -> dict:
        farm = self.access.get_farm(farm_id)
        return {
            "farm_id": farm.id,
            "plot_id": None,
            "values": self._resolved(("farm", self._config(farm_id=farm.id))),
        }

    def resolved_for_plot(self, plot_id: int) -> dict:
        plot = self.access.get_plot(plot_id)
        return {
            "farm_id": plot.farm_id,
            "plot_id": plot.id,
            "values": self._resolved(
                ("plot", self._config(plot_id=plot.id)),
                ("farm", self._config(farm_id=plot.farm_id)),
            ),
        }

    def save_for_farm(self, farm_id: int, payload: AlertConfigValues) -> dict:
        farm = self.access.get_farm(farm_id)
        self._save(payload, farm_id=farm.id)
        return self.resolved_for_farm(farm.id)

    def save_for_plot(self, plot_id: int, payload: AlertConfigValues) -> dict:
        plot = self.access.get_plot(plot_id)
        self._save(payload, plot_id=plot.id)
        return self.resolved_for_plot(plot.id)

    def delete_for_plot(self, plot_id: int) -> None:
        """Quita el override del lote: vuelve a heredar de la finca."""
        plot = self.access.get_plot(plot_id)
        config = self._config(plot_id=plot.id)
        if config is not None:
            self.db.delete(config)
            self.db.commit()

    # ── Internos ──────────────────────────────────────────────────────────

    @staticmethod
    def _resolved(own_level, *lower_levels) -> dict:
        """
        Valor efectivo de cada parámetro y el que heredaría el nivel propio
        si no tuviera valor (para mostrarlo en el formulario).
        """
        effective = alerts.resolve(own_level, *lower_levels)
        inherited = alerts.resolve(*lower_levels)
        return {
            name: {
                **effective[name],
                "inherited_value": inherited[name]["value"],
                "inherited_source": inherited[name]["source"],
            }
            for name in alerts.PARAMETERS
        }

    def _config(self, farm_id: Optional[int] = None, plot_id: Optional[int] = None) -> Optional[AlertConfig]:
        query = self.db.query(AlertConfig)
        if farm_id is not None:
            return query.filter(AlertConfig.farm_id == farm_id).first()
        return query.filter(AlertConfig.plot_id == plot_id).first()

    def _save(self, payload: AlertConfigValues, farm_id: Optional[int] = None, plot_id: Optional[int] = None) -> None:
        """Reemplaza los valores del nivel; si todos quedan en null, la fila sobra."""
        config = self._config(farm_id=farm_id, plot_id=plot_id)
        values = payload.model_dump()

        if all(value is None for value in values.values()):
            if config is not None:
                self.db.delete(config)
                self.db.commit()
            return

        if config is None:
            config = AlertConfig(farm_id=farm_id, plot_id=plot_id)
            self.db.add(config)
        for name, value in values.items():
            setattr(config, name, value)
        self.db.commit()

"""
Piezas compartidas del entrenamiento y la evaluación (generador-sintetico-ml
§5 y §7). Solo desarrollo: usa pandas, que no entra a la imagen de
producción.
"""

import json
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.farm_operations.ml.features import CATEGORICAL_MASK, FEATURE_NAMES, FEATURES, to_matrix, vocabularies
from scripts.farm_ml.dataset import TARGETS

TARGET_LABELS = {
    "score": "Puntaje SCA",
    "defects_pct": "Defectos (%)",
    "yield_factor": "Factor de rendimiento",
}
FOLDS = 5
SEED = 0
# Fijos y decididos antes de evaluar: sin búsqueda de hiperparámetros sobre los datos de prueba
GBM_PARAMS = {
    "max_iter": 400,
    "learning_rate": 0.05,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 40,
    "l2_regularization": 1.0,
    "random_state": SEED,
}


@dataclass
class Dataset:
    frame: pd.DataFrame
    meta: dict
    records: list[dict]
    vocab: dict[str, list[str]]
    X: np.ndarray
    groups: np.ndarray

    def y(self, target: str) -> np.ndarray:
        return self.frame[target].to_numpy(dtype=float)


def load(path: Path, vocab: dict | None = None) -> Dataset:
    frame = pd.read_parquet(path)
    meta_path = Path(path).with_suffix(".json")
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    records = [
        {name: (None if value is None or (isinstance(value, float) and np.isnan(value)) else value)
         for name, value in row.items()}
        for row in frame[list(FEATURE_NAMES)].to_dict("records")
    ]
    vocab = vocab or vocabularies(records)
    return Dataset(frame, meta, records, vocab, to_matrix(records, vocab), frame["farm_id"].to_numpy())


def gbm() -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(categorical_features=CATEGORICAL_MASK, **GBM_PARAMS)


def linear() -> Pipeline:
    """Regresión lineal (ridge) con indicadores de faltante y categorías en one-hot."""
    numeric = [i for i, f in enumerate(FEATURES) if not f.categorical]
    categorical = [i for i, f in enumerate(FEATURES) if f.categorical]
    prepare = ColumnTransformer([
        ("numeric", make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler()), numeric),
        ("categorical", make_pipeline(SimpleImputer(strategy="most_frequent"),
                                      OneHotEncoder(handle_unknown="ignore")), categorical),
    ])
    return Pipeline([("prepare", prepare), ("model", Ridge(alpha=1.0))])


def dummy() -> DummyRegressor:
    return DummyRegressor(strategy="mean")


MODELS = {"gbm": gbm, "linear": linear, "dummy": dummy}


def folds(groups: np.ndarray) -> list[tuple[np.ndarray, np.ndarray]]:
    """GroupKFold por finca: ninguna finca de prueba se vio en el entrenamiento (G4)."""
    return list(GroupKFold(n_splits=FOLDS).split(np.zeros(len(groups)), groups=groups))


def fit(factory, X: np.ndarray, y: np.ndarray):
    with warnings.catch_warnings():
        # Columnas sin ningún dato en un fold (p. ej. una temperatura que casi nadie mide)
        warnings.simplefilter("ignore", UserWarning)
        return factory().fit(X, y)


def predict(model, X: np.ndarray) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return model.predict(X)


def cross_validate(data: Dataset, splits, models=("gbm", "linear", "dummy")) -> dict:
    """
    Predicciones fuera de muestra por modelo y target, y los modelos de cada
    fold (para importancias y la evaluación por etapas).
    """
    result = {name: {t: np.full(len(data.frame), np.nan) for t in TARGETS} for name in models}
    fitted = {name: {t: [] for t in TARGETS} for name in models}
    for train, test in splits:
        for target in TARGETS:
            y = data.y(target)
            for name in models:
                model = fit(MODELS[name], data.X[train], y[train])
                result[name][target][test] = predict(model, data.X[test])
                fitted[name][target].append(model)
    return {"predictions": result, "models": fitted}


def metrics(y: np.ndarray, prediction: np.ndarray) -> dict:
    return {
        "mae": float(mean_absolute_error(y, prediction)),
        "rmse": float(np.sqrt(mean_squared_error(y, prediction))),
        "r2": float(r2_score(y, prediction)),
    }


def fold_metrics(y: np.ndarray, prediction: np.ndarray, splits) -> list[dict]:
    return [metrics(y[test], prediction[test]) for _, test in splits]

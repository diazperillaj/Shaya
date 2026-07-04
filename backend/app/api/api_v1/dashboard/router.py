from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.api_v1.auth.dependencies import get_current_user
from app.api.api_v1.dashboard.schema import (
    CoffeePriceResponse,
    DashboardCharts,
    DashboardKPIs,
)
from app.api.api_v1.dashboard.service import DashboardService
from app.core.db.session import get_db

router = APIRouter()


@router.get("/kpis", response_model=DashboardKPIs)
def get_kpis(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return DashboardService(db).get_kpis()


@router.get("/charts", response_model=DashboardCharts)
def get_charts(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return DashboardService(db).get_charts()


@router.get("/coffee-price", response_model=CoffeePriceResponse)
def get_coffee_price(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return DashboardService(db).get_coffee_price()

from datetime import date, datetime, timedelta, timezone

# Las fechas del cultivo son las del calendario del caficultor. El servidor
# corre en UTC, así que `date.today()` ya marca el día siguiente desde las
# 7 p. m. en Colombia. Colombia no tiene horario de verano: UTC−5 todo el año.
BUSINESS_TZ = timezone(timedelta(hours=-5), "America/Bogota")


def business_today() -> date:
    """Fecha de hoy en Colombia."""
    return datetime.now(BUSINESS_TZ).date()


def business_date(moment: datetime) -> date:
    """Fecha en Colombia de un instante guardado con zona horaria."""
    return moment.astimezone(BUSINESS_TZ).date()

"""
Catálogos del mundo sintético: lugares, nombres, insumos y precios.

No son reglas agronómicas (esas viven en `rules.py`): dan verosimilitud a
los registros que se navegan en la aplicación. Los precios son series
simuladas, no históricos oficiales.
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Municipality:
    name: str
    department: str
    latitude: float
    longitude: float
    harvest_month: int   # mes de inicio de la cosecha principal
    harvest_day: int


# Zona centro: cosecha principal en octubre; zona sur: en abril–mayo.
MUNICIPALITIES = [
    Municipality("Chinchiná", "Caldas", 4.98, -75.60, 10, 1),
    Municipality("Salamina", "Caldas", 5.40, -75.49, 10, 10),
    Municipality("Santuario", "Risaralda", 5.07, -75.96, 10, 5),
    Municipality("Jardín", "Antioquia", 5.60, -75.82, 10, 15),
    Municipality("Andes", "Antioquia", 5.66, -75.88, 10, 10),
    Municipality("Pijao", "Quindío", 4.33, -75.70, 9, 25),
    Municipality("Socorro", "Santander", 6.47, -73.26, 10, 20),
    Municipality("Pitalito", "Huila", 1.85, -76.05, 4, 15),
    Municipality("Acevedo", "Huila", 1.80, -75.89, 4, 10),
    Municipality("La Plata", "Huila", 2.39, -75.89, 4, 25),
    Municipality("Planadas", "Tolima", 3.20, -75.64, 5, 1),
    Municipality("Inzá", "Cauca", 2.55, -76.06, 4, 20),
    Municipality("Buesaco", "Nariño", 1.38, -77.16, 5, 10),
    Municipality("La Unión", "Nariño", 1.60, -77.13, 5, 5),
]

VILLAGES = [
    "El Diamante", "La Palma", "Alto Bonito", "El Recreo", "La Esmeralda", "San Antonio",
    "Las Mercedes", "El Cedral", "Buenos Aires", "La Floresta", "Santa Elena", "El Tablazo",
    "La Ceiba", "Monserrate", "El Silencio", "Guayabal",
]

# Nombres de fincas reales tomados de datos abiertos (solo la columna «Nombre del
# predio o finca», sin ningún dato de sus dueños), depurados: sin duplicados, sin
# registros que no son nombres («LOTE 2», «NO TIENE»), sin nombres de personas y
# con la ortografía normalizada. Cada finca sintética usa uno distinto, así que
# el número de fincas no puede superar el de nombres.
#   - Alcaldía de Pajarito (Boyacá), «SPAE», datos.gov.co/d/qas9-5tya, CC BY-SA 4.0
#   - Alcaldía de Sevilla (Valle del Cauca), «Caracterización de productores
#     agropecuarios registrados en el SPEA», datos.gov.co/d/4p2c-mk37, CC BY 4.0
FARM_NAMES = [
    # Pajarito (Boyacá)
    "Alcaravanes", "Alejandría", "Alejandrina", "Altamira", "Aposento Alto", "Arrayanes",
    "Balconcitos", "Barranco Pelado", "Bello Lugar", "Brasilia", "Buenaventura", "Buena Vista",
    "Buenos Aires", "Candelas", "Chupadera", "Clavelitos", "Conguta", "El Diviso", "El Alcaraván",
    "El Alto", "El Arbolito", "El Arriero", "El Ceibito", "El Chirriador", "El Cielo", "El Encanto",
    "El Espejo", "El Estadero", "El Guayabo", "El Mango", "El Milagro", "El Miradero", "El Mirador",
    "El Morro", "El Palmar", "El Paraíso", "El Pedregal", "El Porvenir", "El Recuerdo", "El Reposo",
    "El Retiro", "El Rosal", "El Topito", "El Triángulo", "El Triunfo", "El Vergel", "Caminito",
    "Corinto", "El Hoyo", "Guamal", "La Reserva", "Mundo Nuevo", "Quebrada Negra", "Gaviotas",
    "Guadales", "Guaira", "Golconda", "La Cabaña", "La Cascada", "La Esperanza", "La Esquina",
    "La Faldita", "La Guinea", "La Maravilla", "La Orquídea", "La Palestina", "La Palma",
    "La Palmera", "La Playita", "La Pradera", "La Primavera", "La Providencia", "La Provincia",
    "La Quinta", "La Reforma", "La Rodadera", "La Sabana", "La Siberia", "La Unión", "La Vega",
    "La Victoria", "La Villita", "La Virgen", "Laguna Negra", "Las Brisas", "Las Cruces",
    "Las Delicias", "Las Gaviotas", "Las Maravillas", "Las Mesetas", "Las Quebradas", "Los Laureles",
    "El Limonal", "Loma Redonda", "Los Arbolitos", "Los Cedros", "Los Cerros", "Los Guayabitos",
    "Los Higuerones", "Los Naranjos", "Magavita", "Montealegre", "Naranjitos", "Peñalta",
    "Potreritos", "Potrero Largo", "Puerto Nuevo", "Quebrada Honda", "Rancho Alegre", "El Remanso",
    "El Cogollo", "San Antonio", "San Fernando", "San Joaquín", "San Lorenzo", "San Pablo",
    "San Roque", "Santa Bárbara", "Santa Helena", "Santa Inés", "Santa Isabel", "Santa Marta",
    "Santa Teresa", "Sierra Morena", "El Temblador", "Versalles", "Villa Esperanza", "Villa Isabel",
    "Villa María", "Villa Rosa", "Villanueva", "Yucatán", "Brisas del Paraíso",
    # Sevilla (Valle del Cauca)
    "Agua Bonita", "Alto Bonito", "Bélgica", "Bella Vista", "Campo Alegre", "Campo Hermoso",
    "El Brillante", "El Jazmín", "El Paraje", "El Rocío", "El Silencio", "El Sombrío", "El Edén",
    "La Argelia", "La Gloria", "La Granja", "La Montañita", "Villa Luz", "La Bonita", "La Fe",
    "La Florida", "La Fortuna", "La Frontera", "La Granjita", "La Luna", "La Rivera",
    "La Sabanita", "La Secreta", "La Tulia", "Los Alpes", "Miraflores", "Los Guaduales", "Lutecia",
    "Vista Hermosa",
]

PLOT_NAMES = [
    "El Alto", "La Cañada", "El Guamal", "La Loma", "El Bajo", "La Quebrada", "El Plan",
    "La Ladera", "El Nacedero", "La Vega", "El Filo", "Los Guaduales",
]

FIRST_NAMES = [
    "José", "Luis", "Carlos", "Jorge", "Andrés", "Juan", "Miguel", "Diego", "Fabio", "Hernán",
    "Wilson", "Édgar", "Ómar", "Alirio", "Libardo", "María", "Luz", "Gloria", "Martha", "Rosa",
    "Ana", "Blanca", "Nubia", "Yolanda", "Sandra", "Dora", "Leidy", "Paola",
]

SURNAMES = [
    "Gómez", "Rodríguez", "López", "Martínez", "García", "Hernández", "Ramírez", "Muñoz",
    "Rojas", "Osorio", "Giraldo", "Cardona", "Valencia", "Ospina", "Quintero", "Salazar",
    "Arango", "Zapata", "Castaño", "Bedoya", "Molina", "Rendón", "Chantre", "Imbachí",
]

STORAGE_PLACES = ["Bodega de la finca", "Beneficiadero", "Casa de la finca", "Cuarto de secado"]
FLOATS_METHODS = ["Tanque", "Zaranda", "Tolva con agua"]
FERMENTATION_CRITERIA = ["Prueba de tacto", "Prueba del palote", "Medición de pH"]
IRRIGATION_METHODS = ["Aspersión", "Goteo", "Manguera", "Microaspersión"]
LABORATORIES = ["Laboratorio de suelos de la cooperativa", "Laboratorio agrícola regional"]
OTHER_PESTS = ["Cochinilla", "Minador", "Mal rosado", "Mancha de hierro"]


@dataclass(frozen=True)
class SupplyInfo:
    name: str
    supply_type: str       # SupplyTypeEnum
    unit: str
    composition: str
    nitrogen: float        # fracción de N del producto (nutrición del ciclo)
    price_2021: float      # COP por unidad


SUPPLIES = {
    "compound": SupplyInfo("Fertilizante compuesto 17-6-18-2", "fertilizer", "kg", "N 17 % · P 6 % · K 18 % · Mg 2 %", 0.17, 2800),
    "urea": SupplyInfo("Urea", "fertilizer", "kg", "N 46 %", 0.46, 2400),
    "dap": SupplyInfo("DAP 18-46-0", "fertilizer", "kg", "N 18 % · P 46 %", 0.18, 3200),
    "kcl": SupplyInfo("Cloruro de potasio", "fertilizer", "kg", "K 60 %", 0.0, 2600),
    "foliar": SupplyInfo("Fertilizante foliar con elementos menores", "fertilizer", "L", "N 10 % · elementos menores", 0.10, 18000),
    "beauveria": SupplyInfo("Beauveria bassiana (biológico)", "phytosanitary", "kg", "Hongo entomopatógeno", 0.0, 42000),
    "cyproconazole": SupplyInfo("Cyproconazol", "phytosanitary", "L", "Cyproconazol 100 g/L", 0.0, 95000),
    "copper": SupplyInfo("Oxicloruro de cobre", "phytosanitary", "kg", "Cobre 50 %", 0.0, 32000),
    "glyphosate": SupplyInfo("Glifosato", "herbicide", "L", "Glifosato 480 g/L", 0.0, 24000),
}

# Precio de referencia de la carga de pergamino seco (125 kg), COP, por año.
# Serie simulada con la forma de los últimos años; no es un histórico oficial.
CARGA_PRICE = {2018: 1_300_000, 2019: 1_400_000, 2020: 1_550_000, 2021: 1_750_000, 2022: 2_150_000,
               2023: 1_700_000, 2024: 2_250_000, 2025: 2_850_000, 2026: 2_650_000, 2027: 2_700_000}

# Tarifa de recolección por kg de cereza y valor del jornal, año base 2021
PICKING_RATE_2021 = 650.0
DAY_WAGE_2021 = 45_000.0
YEARLY_INCREASE = 0.08


def _year_fraction(day: date) -> float:
    return day.year + (day.timetuple().tm_yday - 1) / 365.0


def carga_price(day: date) -> float:
    """Precio de la carga interpolado entre los anclajes anuales (mitad de año)."""
    x = _year_fraction(day) - 0.5
    years = sorted(CARGA_PRICE)
    if x <= years[0]:
        return CARGA_PRICE[years[0]]
    for y0, y1 in zip(years, years[1:]):
        if x <= y1:
            return CARGA_PRICE[y0] + (CARGA_PRICE[y1] - CARGA_PRICE[y0]) * (x - y0) / (y1 - y0)
    return CARGA_PRICE[years[-1]]


def inflation(day: date) -> float:
    return (1.0 + YEARLY_INCREASE) ** (_year_fraction(day) - 2021.0)


def picking_rate(day: date) -> float:
    """Tarifa por kg de cereza, redondeada a 10 pesos."""
    return round(PICKING_RATE_2021 * inflation(day) / 10.0) * 10.0


def day_wage(day: date) -> float:
    """Valor del jornal, redondeado a 1.000 pesos."""
    return round(DAY_WAGE_2021 * inflation(day) / 1000.0) * 1000.0


def supply_price(key: str, day: date) -> float:
    return SUPPLIES[key].price_2021 * inflation(day)

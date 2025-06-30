from enum import Enum


class ProductTypeEnum(str, Enum):
    CONSU = "consu"  # Producto consumible (no se gestiona inventario)
    SERVICE = "service"  # Producto tipo servicio (no material)

from enum import Enum


class ProductTypeEnum(str, Enum):
    consu = "consu"  # Producto consumible (no se gestiona inventario)
    service = "service"  # Producto tipo servicio (no material)

from enum import Enum


class AddressTypeEnum(str, Enum):
    CONTACT = "contact"  # Detalles de contacto (CEO, CFO, etc.)
    INVOICE = "invoice"  # Dirección de facturación
    DELIVERY = "delivery"  # Dirección de entrega/envío
    PRIVATE = "private"  # Dirección privada (solo visible a usuarios autorizados)
    OTHER = "other"  # Otras direcciones (subsidiarias, etc.)

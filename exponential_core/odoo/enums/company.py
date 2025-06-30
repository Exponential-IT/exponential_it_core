from enum import Enum


class CompanyTypeEnum(str, Enum):
    COMPANY = "company"  # Empresa (jurídica)
    PERSON = "person"  # Persona natural

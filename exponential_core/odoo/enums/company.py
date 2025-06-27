from enum import Enum


class CompanyTypeEnum(str, Enum):
    company = "company"  # Empresa (jurídica)
    person = "person"  # Persona natural

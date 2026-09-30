import re
from typing import Optional
from pydantic import BaseModel, ValidationError, field_validator

SEPARATORS = re.compile(r'[\s-]')


def compact(value):
    return SEPARATORS.sub('', value or '').upper()


def group(value, size, separator):
    return separator.join(value[i:i + size] for i in range(0, len(value), size))


def format_iban(value):
    value = compact(value)
    if len(value) <= 4:
        return value
    return f'{value[:4]} {group(value[4:], 8, " ")}'


def format_pfj(value):
    return group(compact(value), 8, '-')


def format_isin(value):
    return group(compact(value), 4, ' ')


def first_error(exc: ValidationError):
    error = exc.errors()[0]
    return str(error.get('ctx', {}).get('error', error['msg']))


class BankAccountIdentifiers(BaseModel):
    account_number_iban: str
    account_number_pfj: Optional[str] = None

    @field_validator('account_number_iban', mode='before')
    @classmethod
    def validate_iban(cls, value):
        value = compact(value)
        if value.startswith('HU'):
            if not re.fullmatch(r'HU\d{26}', value):
                raise ValueError('A Hungarian IBAN must be HU followed by 26 digits.')
        elif not re.fullmatch(r'[A-Z]{2}\d{2}[A-Z0-9]{11,30}', value):
            raise ValueError('IBAN must be a 2-letter country code, 2 check digits and 11 to 30 letters or digits.')
        return value

    @field_validator('account_number_pfj', mode='before')
    @classmethod
    def validate_pfj(cls, value):
        value = compact(value)
        if not value:
            return None
        if not re.fullmatch(r'\d{16}|\d{24}', value):
            raise ValueError('PFJ must contain 16 or 24 digits.')
        return value


class SecurityIdentifier(BaseModel):
    isin: str

    @field_validator('isin', mode='before')
    @classmethod
    def validate_isin(cls, value):
        value = compact(value)
        if value.startswith('HU'):
            if not re.fullmatch(r'HU\d{10}', value):
                raise ValueError('A Hungarian ISIN must be HU followed by 10 digits.')
        elif not re.fullmatch(r'[A-Z]{2}[A-Z0-9]{9}\d', value):
            raise ValueError('ISIN must be a 2-letter country code, 9 letters or digits and a check digit.')
        return value

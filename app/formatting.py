from decimal import Decimal


def format_amount(value, decimals=2):
    if value is None:
        return ''
    amount = Decimal(value).quantize(Decimal(1).scaleb(-decimals))
    return f'{amount:,.{decimals}f}'.replace(',', ' ')


def format_rate(value, min_decimals=2):
    if value is None:
        return ''
    amount = Decimal(value).quantize(Decimal('0.000001'))
    integer, fraction = f'{amount:,.6f}'.replace(',', ' ').split('.')
    fraction = fraction.rstrip('0').ljust(min_decimals, '0')
    return f'{integer}.{fraction}' if fraction else integer

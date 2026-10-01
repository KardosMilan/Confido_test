from decimal import Decimal


def format_amount(value, decimals=2):
    if value is None:
        return ''
    amount = Decimal(value).quantize(Decimal(1).scaleb(-decimals))
    return f'{amount:,.{decimals}f}'.replace(',', ' ')

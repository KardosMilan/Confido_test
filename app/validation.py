from datetime import date, datetime

MIN_DATE = date(1900, 1, 1)
MAX_DATE = date(2100, 12, 31)


def parse_form_date(value, label, required=False):
    value = (value or '').strip()
    if not value:
        return None, f'{label} is required!' if required else None
    try:
        parsed = datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None, f'{label} must be a valid date (YYYY-MM-DD)!'
    if not MIN_DATE <= parsed <= MAX_DATE:
        return None, f'{label} must be between {MIN_DATE.isoformat()} and {MAX_DATE.isoformat()}!'
    return parsed, None

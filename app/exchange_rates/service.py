from datetime import datetime, timedelta
from decimal import Decimal
from app.extensions import db
from app.models import Currency, ExchangeRate, ExchangeRateUpdate, ManagedAssets
from app.exchange_rates.mnb import fetch_rates, MNBError
from app.data_entry.routes import report_date_options

LOOKBACK_DAYS = 10
RATE_QUANTUM = Decimal('0.000001')


def asset_currencies():
    return (
        Currency.query
        .join(ManagedAssets, ManagedAssets.currency_id == Currency.id)
        .filter(Currency.code != 'HUF')
        .distinct()
        .order_by(Currency.code)
        .all()
    )


def rate_on_or_before(day_rates, target):
    candidates = [day for day in day_rates if target - timedelta(days=LOOKBACK_DAYS) < day <= target]
    return day_rates[max(candidates)] if candidates else None


def log_update(status, updated_count=0, message=None):
    entry = ExchangeRateUpdate(run_at=datetime.utcnow(), status=status, updated_count=updated_count, message=message[:1000] if message else None)
    db.session.add(entry)
    db.session.commit()
    return entry


def update_exchange_rates():
    currencies = asset_currencies()
    if not currencies:
        return log_update('Success', 0, 'No foreign currency assets to update.')

    report_dates = report_date_options()
    start = min(report_dates) - timedelta(days=LOOKBACK_DAYS)
    end = max(report_dates)

    try:
        rates = fetch_rates([currency.code for currency in currencies], start, end)
    except MNBError as exc:
        db.session.rollback()
        return log_update('Failed', 0, str(exc))

    existing = {
        (rate.currency_id, rate.rate_date): rate
        for rate in ExchangeRate.query.filter(ExchangeRate.currency_id.in_([currency.id for currency in currencies]))
    }
    now = datetime.utcnow()
    updated = 0
    missing = []

    for currency in currencies:
        for report_date in report_dates:
            current = existing.get((currency.id, report_date))
            if current is not None and current.source == 'Manual':
                continue

            value = rate_on_or_before(rates.get(currency.code, {}), report_date)
            if value is None:
                missing.append(f'{currency.code}/HUF {report_date.isoformat()}')
                continue

            value = value.quantize(RATE_QUANTUM)
            if current is None:
                db.session.add(ExchangeRate(currency_id=currency.id, rate_date=report_date, rate=value, source='MNB', updated_at=now))
                updated += 1
            elif Decimal(current.rate).quantize(RATE_QUANTUM) != value:
                current.rate = value
                current.updated_at = now
                current.updated_by = None
                updated += 1

    if missing:
        return log_update('Failed', updated, 'No MNB rate for: ' + ', '.join(missing))
    return log_update('Success', updated)

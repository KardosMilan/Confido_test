import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal, InvalidOperation
import requests

MNB_URL = 'http://www.mnb.hu/arfolyamok.asmx'
SOAP_ACTION = 'http://www.mnb.hu/webservices/MNBArfolyamServiceSoap/GetExchangeRates'
ENVELOPE = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="http://www.mnb.hu/webservices/">
  <soap:Body>
    <web:GetExchangeRates>
      <web:startDate>{start}</web:startDate>
      <web:endDate>{end}</web:endDate>
      <web:currencyNames>{currencies}</web:currencyNames>
    </web:GetExchangeRates>
  </soap:Body>
</soap:Envelope>"""


class MNBError(Exception):
    pass


def fetch_rates(currency_codes, start_date, end_date, timeout=30):
    body = ENVELOPE.format(
        start=start_date.isoformat(),
        end=end_date.isoformat(),
        currencies=','.join(sorted(currency_codes)),
    )
    try:
        response = requests.post(
            MNB_URL,
            data=body.encode('utf-8'),
            headers={'Content-Type': 'text/xml; charset=utf-8', 'SOAPAction': f'"{SOAP_ACTION}"'},
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise MNBError(f'MNB request failed: {exc}') from exc

    try:
        envelope = ET.fromstring(response.content)
        result = next(element for element in envelope.iter() if element.tag.endswith('GetExchangeRatesResult'))
        rates_root = ET.fromstring(result.text or '<MNBExchangeRates/>')
    except (ET.ParseError, StopIteration) as exc:
        raise MNBError(f'Unexpected MNB response: {exc}') from exc

    rates = {}
    try:
        for day in rates_root.findall('Day'):
            day_date = date.fromisoformat(day.get('date'))
            for rate in day.findall('Rate'):
                unit = Decimal(rate.get('unit') or '1')
                value = Decimal((rate.text or '').strip().replace(',', '.'))
                rates.setdefault(rate.get('curr'), {})[day_date] = value / unit
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise MNBError(f'Unexpected MNB rate format: {exc}') from exc
    return rates

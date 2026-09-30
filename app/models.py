from app.extensions import db
from enum import Enum
from datetime import datetime
from flask_login import UserMixin
from app.extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(100), nullable=True)
    picture = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<User {self.email}>'

class AccountType(str, Enum):
    CURRENT = "Current Account"
    SECURITIES = "Securities Account"

class AssetType(str, Enum):
    SECURITIES = "Securities"
    EQUITY_INTERESTS = "Equity Interests"
    RECEIVABLES = "Receivables"
    LIABILITIES = "Liabilities"

ASSET_TYPE_FIELDS = {
    AssetType.SECURITIES.value: ('isin', 'nominal_value', 'price_decimals'),
    AssetType.EQUITY_INTERESTS.value: ('nominal_value',),
    AssetType.RECEIVABLES.value: (),
    AssetType.LIABILITIES.value: (),
}

TRUST_FIELDS = ('trust_name', 'contract_number', 'tax_number', 'contract_date', 'end_date', 'riporting_currency', 'status')
ACCOUNT_FIELDS = ('trust_id', 'bank_id', 'currency_id', 'type', 'account_number_iban', 'account_number_pfj', 'bank_account_name', 'contract_date', 'end_date', 'status')
ASSET_FIELDS = ('asset_type', 'asset_name', 'currency_id', 'isin', 'nominal_value', 'price_decimals')


def copy_fields(source, target, fields):
    for field in fields:
        setattr(target, field, getattr(source, field))

class Currency(db.Model):
    __tablename__ = 'currency'
    
    id = db.Column(db.Integer, primary_key=True)               
    code = db.Column(db.String(3), unique=True, nullable=False)  
    name = db.Column(db.String(50), nullable=False)              
    symbol = db.Column(db.String(10), nullable=False)            
    decimals = db.Column(db.Integer, nullable=False, default=2)

def seed_currencies():
    if Currency.query.first() is None:
        currencies_data = [
            {"code": "HUF", "name": "Magyar forint", "symbol": "Ft", "decimals": 0},
            {"code": "EUR", "name": "Euró", "symbol": "€", "decimals": 2},
            {"code": "USD", "name": "Amerikai dollár", "symbol": "$", "decimals": 2},
            {"code": "GBP", "name": "Angol font", "symbol": "£", "decimals": 2},
            {"code": "CHF", "name": "Svájci frank", "symbol": "CHF", "decimals": 2},
            {"code": "JPY", "name": "Japán jen", "symbol": "¥", "decimals": 0},
            {"code": "CAD", "name": "Kanadai dollár", "symbol": "CA$", "decimals": 2},
            {"code": "AUD", "name": "Ausztrál dollár", "symbol": "A$", "decimals": 2},
            {"code": "PLN", "name": "Lengyel zloty", "symbol": "zł", "decimals": 2},
            {"code": "CZK", "name": "Cseh korona", "symbol": "Kč", "decimals": 2},
            {"code": "RON", "name": "Román lej", "symbol": "lei", "decimals": 2},
            {"code": "BGN", "name": "Bolgár leva", "symbol": "лв", "decimals": 2},
            {"code": "RSD", "name": "Szerb dinár", "symbol": "din.", "decimals": 2},
            {"code": "BAM", "name": "Bosnyák konvertibilis márka", "symbol": "KM", "decimals": 2},
            {"code": "DKK", "name": "Dán korona", "symbol": "kr", "decimals": 2},
            {"code": "SEK", "name": "Svéd korona", "symbol": "kr", "decimals": 2},
            {"code": "NOK", "name": "Norvég korona", "symbol": "kr", "decimals": 2},
            {"code": "ISK", "name": "Izlandi korona", "symbol": "kr", "decimals": 0},
            {"code": "ALL", "name": "Albán lek", "symbol": "L", "decimals": 2},
            {"code": "MKD", "name": "Macedón dénár", "symbol": "ден", "decimals": 2},
            {"code": "MDL", "name": "Moldáv lej", "symbol": "L", "decimals": 2},
            {"code": "UAH", "name": "Ukrán hrivnya", "symbol": "₴", "decimals": 2},
            {"code": "GEL", "name": "Grúz lari", "symbol": "₾", "decimals": 2},
            {"code": "AMD", "name": "Örmény dram", "symbol": "֏", "decimals": 2},

            {"code": "TRY", "name": "Török líra", "symbol": "₺", "decimals": 2},
            {"code": "ILS", "name": "Izraeli új sékel", "symbol": "₪", "decimals": 2},
            {"code": "AED", "name": "EAE-dirham", "symbol": "AED", "decimals": 2},
            {"code": "SAR", "name": "Szaúdi riyal", "symbol": "SR", "decimals": 2},
            {"code": "QAR", "name": "Katari riyal", "symbol": "QR", "decimals": 2},
            {"code": "KWD", "name": "Kuvaiti dinár", "symbol": "KD", "decimals": 3},
            {"code": "BHD", "name": "Bahreini dinár", "symbol": "BD", "decimals": 3},
            {"code": "OMR", "name": "Ománi rial", "symbol": "RO", "decimals": 3},
            {"code": "JOD", "name": "Jordán dinár", "symbol": "JD", "decimals": 3},
            {"code": "IQD", "name": "Iraki dinár", "symbol": "IQD", "decimals": 3},
            {"code": "LBP", "name": "Libanoni font", "symbol": "L£", "decimals": 2},
            {"code": "EGP", "name": "Egyiptomi font", "symbol": "E£", "decimals": 2},
            {"code": "MAD", "name": "Marokkói dirham", "symbol": "MAD", "decimals": 2},
            {"code": "DZD", "name": "Algériai dinár", "symbol": "DA", "decimals": 2},
            {"code": "TND", "name": "Tunéziai dinár", "symbol": "DT", "decimals": 3},

            {"code": "CNY", "name": "Kínai jüan", "symbol": "¥", "decimals": 2},
            {"code": "INR", "name": "Indiai rúpia", "symbol": "₹", "decimals": 2},
            {"code": "SGD", "name": "Szingapúri dollár", "symbol": "S$", "decimals": 2},
            {"code": "HKD", "name": "Hongkongi dollár", "symbol": "HK$", "decimals": 2},
            {"code": "KRW", "name": "Dél-koreai von", "symbol": "₩", "decimals": 0},
            {"code": "THB", "name": "Thaiföldi bat", "symbol": "฿", "decimals": 2},
            {"code": "MYR", "name": "Maláj ringgit", "symbol": "RM", "decimals": 2},
            {"code": "IDR", "name": "Indonéz rúpia", "symbol": "Rp", "decimals": 2},
            {"code": "PHP", "name": "Fülöp-szigeteki peso", "symbol": "₱", "decimals": 2},
            {"code": "VND", "name": "Vietnámi dong", "symbol": "₫", "decimals": 0},
            {"code": "PKR", "name": "Pakisztáni rúpia", "symbol": "Rs", "decimals": 2},
            {"code": "BDT", "name": "Bangladesi taka", "symbol": "৳", "decimals": 2},
            {"code": "LKR", "name": "Srí Lanka-i rúpia", "symbol": "Rs", "decimals": 2},
            {"code": "NPR", "name": "Nepáli rúpia", "symbol": "Rs", "decimals": 2},
            {"code": "NZD", "name": "Új-zélandi dollár", "symbol": "NZ$", "decimals": 2},
            {"code": "TWD", "name": "Új tajvani dollár", "symbol": "NT$", "decimals": 2},
            {"code": "KZT", "name": "Kazah tenge", "symbol": "₸", "decimals": 2},
            {"code": "UZS", "name": "Uzbég szom", "symbol": "soʻm", "decimals": 2},
            {"code": "KGS", "name": "Kirgiz szom", "symbol": "som", "decimals": 2},
            {"code": "TJS", "name": "Tádzsik szomoni", "symbol": "SM", "decimals": 2},
            {"code": "TMT", "name": "Türkmenisztáni manat", "symbol": "TMT", "decimals": 2},
            {"code": "MNT", "name": "Mongol tugrik", "symbol": "₮", "decimals": 2},
            {"code": "MOP", "name": "Makaói pataca", "symbol": "MOP$", "decimals": 2},
            {"code": "KHR", "name": "Kambodzsai riel", "symbol": "៛", "decimals": 2},
            {"code": "LAK", "name": "Laoszi kip", "symbol": "₭", "decimals": 2},
            {"code": "MMK", "name": "Mianmari kjé", "symbol": "K", "decimals": 2},
            {"code": "FJD", "name": "Fidzsi-szigeteki dollár", "symbol": "FJ$", "decimals": 2},
            {"code": "PGK", "name": "Pápua új-guineai kina", "symbol": "K", "decimals": 2},

            {"code": "MXN", "name": "Mexikói peso", "symbol": "Mex$", "decimals": 2},
            {"code": "BRL", "name": "Brazil real", "symbol": "R$", "decimals": 2},
            {"code": "ARS", "name": "Argentin peso", "symbol": "ARS$", "decimals": 2},
            {"code": "CLP", "name": "Chilei peso", "symbol": "CLP$", "decimals": 0},
            {"code": "COP", "name": "Kolumbiai peso", "symbol": "COL$", "decimals": 2},
            {"code": "PEN", "name": "Perui sol", "symbol": "S/", "decimals": 2},
            {"code": "UYU", "name": "Uruguayi peso", "symbol": "$U", "decimals": 2},
            {"code": "PYG", "name": "Paraguayi guaraní", "symbol": "₲", "decimals": 0},
            {"code": "BOB", "name": "Bolíviai boliviano", "symbol": "Bs.", "decimals": 2},
            {"code": "CRC", "name": "Costa Rica-i colón", "symbol": "₡", "decimals": 2},
            {"code": "DOP", "name": "Dominikai peso", "symbol": "RD$", "decimals": 2},
            {"code": "GTQ", "name": "Guatemalai quetzal", "symbol": "Q", "decimals": 2},
            {"code": "HNL", "name": "Hondurasi lempira", "symbol": "L", "decimals": 2},
            {"code": "NIO", "name": "Nicaraguai córdoba", "symbol": "C$", "decimals": 2},
            {"code": "PAB", "name": "Panamai balboa", "symbol": "B/.", "decimals": 2},
            {"code": "JM", "name": "Jamaicai dollár", "symbol": "J$", "decimals": 2},
            {"code": "TTD", "name": "Trinidad és Tobago-i dollár", "symbol": "TT$", "decimals": 2},
            {"code": "BBD", "name": "Barbadosi dollár", "symbol": "Bds$", "decimals": 2},
            {"code": "BSD", "name": "Bahamai dollár", "symbol": "B$", "decimals": 2},
            {"code": "XCD", "name": "Kelet-karibi dollár", "symbol": "EC$", "decimals": 2},
            {"code": "HTG", "name": "Haiti gourde", "symbol": "G", "decimals": 2},
            {"code": "VES", "name": "Venezuelai bolívar", "symbol": "Bs.S", "decimals": 2},

            {"code": "ZAR", "name": "Dél-afrikai rand", "symbol": "R", "decimals": 2},
            {"code": "NGN", "name": "Nigériai naira", "symbol": "₦", "decimals": 2},
            {"code": "KES", "name": "Keniai shilling", "symbol": "KSh", "decimals": 2},
            {"code": "GHS", "name": "Ghánai cedi", "symbol": "GH₵", "decimals": 2},
            {"code": "TZS", "name": "Tanzániai shilling", "symbol": "TSh", "decimals": 2},
            {"code": "UGX", "name": "Ugandai shilling", "symbol": "USh", "decimals": 0},
            {"code": "ETB", "name": "Etióp birr", "symbol": "Br", "decimals": 2},
            {"code": "ZMW", "name": "Zambiai kwacha", "symbol": "ZK", "decimals": 2},
            {"code": "BWP", "name": "Botswanai pula", "symbol": "P", "decimals": 2},
            {"code": "MUR", "name": "Mauritiusi rúpia", "symbol": "₨", "decimals": 2},
            {"code": "NAM", "name": "Namíbiai dollár", "symbol": "N$", "decimals": 2},
            {"code": "RWF", "name": "Ruandai frank", "symbol": "RF", "decimals": 0},
            {"code": "XAF", "name": "Közép-afrikai CFA-frank", "symbol": "FCFA", "decimals": 0},
            {"code": "XOF", "name": "Nyugat-afrikai CFA-frank", "symbol": "CFA", "decimals": 0},
            {"code": "MZN", "name": "Mozambiki metical", "symbol": "MT", "decimals": 2},
            {"code": "AOA", "name": "Angolai kwanza", "symbol": "Kz", "decimals": 2},

            {"code": "XPF", "name": "CFP-frank", "symbol": "FCFP", "decimals": 0},
            {"code": "RUB", "name": "Orosz rubel", "symbol": "₽", "decimals": 2},
            {"code": "BYN", "name": "Fehérorosz rubel", "symbol": "Br", "decimals": 2},
            {"code": "AFN", "name": "Afgán afghani", "symbol": "؋", "decimals": 2},
            {"code": "AZN", "name": "Azeri manat", "symbol": "₼", "decimals": 2},
            {"code": "MVR", "name": "Maldív-szigeteki rufiyaa", "symbol": "Rf", "decimals": 2},
            {"code": "LYD", "name": "Líbiai dinár", "symbol": "LD", "decimals": 3},
            {"code": "BZD", "name": "Belize-i dollár", "symbol": "BZ$", "decimals": 2},
            {"code": "BMD", "name": "Bermudai dollár", "symbol": "BD$", "decimals": 2},
            {"code": "KYD", "name": "Kajmán-szigeteki dollár", "symbol": "CI$", "decimals": 2},
            {"code": "GIP", "name": "Gibraltári font", "symbol": "£", "decimals": 2},
            {"code": "AWG", "name": "Arubai florin", "symbol": "Afl.", "decimals": 2},
            {"code": "ANG", "name": "Holland antilláki forint", "symbol": "NAƒ", "decimals": 2},
            {"code": "CVE", "name": "Zöld-foki escudo", "symbol": "CVE", "decimals": 2},
            {"code": "GMD", "name": "Gambiai dalasi", "symbol": "D", "decimals": 2},
            {"code": "GNF", "name": "Guineai frank", "symbol": "FG", "decimals": 0},
            {"code": "DJF", "name": "Dzsibuti frank", "symbol": "Fdj", "decimals": 0},
            {"code": "KMF", "name": "Comore-i frank", "symbol": "CF", "decimals": 0},
            {"code": "LSL", "name": "Lesothói loti", "symbol": "L", "decimals": 2},
            {"code": "LRD", "name": "Libériai dollár", "symbol": "L$", "decimals": 2},
            {"code": "MGA", "name": "Madagaszkári ariary", "symbol": "Ar", "decimals": 2},
            {"code": "MWK", "name": "Malawi kwacha", "symbol": "MK", "decimals": 2},
            {"code": "MRU", "name": "Mauritániai ouguiya", "symbol": "UM", "decimals": 2},
            {"code": "NAD", "name": "Namíbiai dollár", "symbol": "N$", "decimals": 2},
            {"code": "SCR", "name": "Seychelle-i rúpia", "symbol": "SR", "decimals": 2},
            {"code": "SLL", "name": "Sierra Leone-i leone", "symbol": "Le", "decimals": 2},
            {"code": "SOS", "name": "Szomáli shilling", "symbol": "Sh.So.", "decimals": 2},
            {"code": "SZL", "name": "Szváziföldi lilangeni", "symbol": "L", "decimals": 2},
            {"code": "TOP", "name": "Tongai paʻanga", "symbol": "T$", "decimals": 2},
            {"code": "VUV", "name": "Vanuatui vatu", "symbol": "VT", "decimals": 0},
            {"code": "WST", "name": "Szamoai tala", "symbol": "WS$", "decimals": 2}
        ]

        for item in currencies_data:
            db.session.add(Currency(
                code=item["code"], 
                name=item["name"], 
                symbol=item["symbol"],
                decimals=item["decimals"]
            ))

        db.session.commit()

class RiportDate(db.Model):
    __tablename__ = 'riport_date'
    riport_id = db.Column('Riport ID', db.Integer, primary_key=True)
    ev = db.Column('Ev', db.Integer)
    honap = db.Column('Honap', db.Integer)
    honap_utolso_napja = db.Column('HonapUtolsoNapja', db.Date)
    account_balances = db.relationship('BankAccountBalance', backref='riport_date', lazy=True)

class Bank(db.Model):
    __tablename__ = 'bank'
    bank_id = db.Column('BANK ID', db.Integer, primary_key=True)
    bank_name = db.Column('Bank Name', db.String(100))
    region = db.Column('Region', db.String(50))
    bank_accounts = db.relationship('BankAccount', backref='bank', lazy=True)

INITIAL_BANKS = [
    {"bank_id": 1, "name": "OTP Bank Nyrt.", "region": "Hungary"},
    {"bank_id": 2, "name": "K&H Bank Zrt.", "region": "Hungary"},
    {"bank_id": 3, "name": "Erste Bank Hungary Zrt.", "region": "Hungary"},
    {"bank_id": 4, "name": "Raiffeisen Bank Zrt.", "region": "Hungary"},
    {"bank_id": 5, "name": "UniCredit Bank Hungary Zrt.", "region": "Hungary"},
    {"bank_id": 6, "name": "MBH Bank Nyrt.", "region": "Hungary"},
    {"bank_id": 7, "name": "CIB Bank Zrt.", "region": "Hungary"},
    {"bank_id": 8, "name": "Gránit Bank Zrt.", "region": "Hungary"},
    {"bank_id": 9, "name": "MagNet Bank Zrt.", "region": "Hungary"},
    {"bank_id": 10, "name": "Polgári Bank Zrt.", "region": "Hungary"},
    {"bank_id": 11, "name": "Takarékbank Zrt.", "region": "Hungary"},
    {"bank_id": 12, "name": "Eximbank Zrt.", "region": "Hungary"},
    {"bank_id": 13, "name": "MFB Zrt.", "region": "Hungary"},
    {"bank_id": 14, "name": "KDB Bank Europe", "region": "Hungary"},
    {"bank_id": 15, "name": "Sberbank Hungary (inactive)", "region": "Hungary"},
    {"bank_id": 17, "name": "Deutsche Bank", "region": "EU"},
    {"bank_id": 18, "name": "Commerzbank", "region": "EU"},
    {"bank_id": 19, "name": "DZ Bank", "region": "EU"},
    {"bank_id": 20, "name": "KfW", "region": "EU"},
    {"bank_id": 21, "name": "BNP Paribas", "region": "EU"},
    {"bank_id": 22, "name": "Crédit Agricole", "region": "EU"},
    {"bank_id": 23, "name": "Société Générale", "region": "EU"},
    {"bank_id": 24, "name": "La Banque Postale", "region": "EU"},
    {"bank_id": 25, "name": "BPCE", "region": "EU"},
    {"bank_id": 26, "name": "Natixis", "region": "EU"},
    {"bank_id": 27, "name": "ING Bank", "region": "EU"},
    {"bank_id": 28, "name": "ABN AMRO", "region": "EU"},
    {"bank_id": 29, "name": "Rabobank", "region": "EU"},
    {"bank_id": 30, "name": "SNS Bank", "region": "EU"},
    {"bank_id": 31, "name": "UniCredit", "region": "EU"},
    {"bank_id": 32, "name": "Intesa Sanpaolo", "region": "EU"},
    {"bank_id": 33, "name": "Banco BPM", "region": "EU"},
    {"bank_id": 34, "name": "Monte dei Paschi di Siena", "region": "EU"},
    {"bank_id": 35, "name": "UBI Banca", "region": "EU"},
    {"bank_id": 36, "name": "Santander", "region": "EU"},
    {"bank_id": 37, "name": "BBVA", "region": "EU"},
    {"bank_id": 38, "name": "CaixaBank", "region": "EU"},
    {"bank_id": 39, "name": "Sabadell", "region": "EU"},
    {"bank_id": 40, "name": "Bankinter", "region": "EU"},
    {"bank_id": 41, "name": "Nordea", "region": "EU"},
    {"bank_id": 42, "name": "Danske Bank", "region": "EU"},
    {"bank_id": 43, "name": "SEB", "region": "EU"},
    {"bank_id": 44, "name": "Swedbank", "region": "EU"},
    {"bank_id": 45, "name": "DNB", "region": "EU"},
    {"bank_id": 46, "name": "KBC Group", "region": "EU"},
    {"bank_id": 47, "name": "Belfius", "region": "EU"},
    {"bank_id": 48, "name": "Bank of Ireland", "region": "EU"},
    {"bank_id": 49, "name": "AIB Group", "region": "EU"},
    {"bank_id": 50, "name": "Permanent TSB", "region": "EU"},
    {"bank_id": 51, "name": "PKO Bank Polski", "region": "EU"},
    {"bank_id": 52, "name": "Bank Pekao", "region": "EU"},
    {"bank_id": 53, "name": "mBank", "region": "EU"},
    {"bank_id": 54, "name": "ING Poland", "region": "EU"},
    {"bank_id": 55, "name": "Česká spořitelna", "region": "EU"},
    {"bank_id": 56, "name": "ČSOB", "region": "EU"},
    {"bank_id": 57, "name": "Komerční banka", "region": "EU"},
    {"bank_id": 58, "name": "Erste Group", "region": "EU"},
    {"bank_id": 59, "name": "Raiffeisen Bank International", "region": "EU"},
    {"bank_id": 60, "name": "Banca Transilvania", "region": "EU"},
    {"bank_id": 61, "name": "BRD Groupe Société Générale", "region": "EU"},
    {"bank_id": 62, "name": "Alpha Bank", "region": "EU"},
    {"bank_id": 63, "name": "Eurobank", "region": "EU"},
    {"bank_id": 64, "name": "National Bank of Greece", "region": "EU"},
    {"bank_id": 65, "name": "OP Financial Group", "region": "EU"},
    {"bank_id": 66, "name": "LBBW", "region": "EU"},
    {"bank_id": 67, "name": "BayernLB", "region": "EU"},
    {"bank_id": 68, "name": "Helaba", "region": "EU"},
    {"bank_id": 69, "name": "N26 Bank", "region": "EU"},
    {"bank_id": 70, "name": "Revolut Bank", "region": "EU"},
    {"bank_id": 71, "name": "Monzo Bank", "region": "EU"},
    {"bank_id": 72, "name": "Starling Bank", "region": "EU"},
    {"bank_id": 73, "name": "HSBC Europe", "region": "EU"},
    {"bank_id": 74, "name": "Barclays Europe", "region": "EU"},
    {"bank_id": 75, "name": "Lloyds Bank Europe", "region": "EU"},
    {"bank_id": 76, "name": "TSB Bank", "region": "EU"},
    {"bank_id": 78, "name": "JPMorgan Chase", "region": "USA"},
    {"bank_id": 79, "name": "Bank of America", "region": "USA"},
    {"bank_id": 80, "name": "Citigroup", "region": "USA"},
    {"bank_id": 81, "name": "Wells Fargo", "region": "USA"},
    {"bank_id": 82, "name": "Goldman Sachs", "region": "USA"},
    {"bank_id": 83, "name": "Morgan Stanley", "region": "USA"},
    {"bank_id": 84, "name": "U.S. Bank", "region": "USA"},
    {"bank_id": 85, "name": "PNC Bank", "region": "USA"},
    {"bank_id": 86, "name": "Capital One", "region": "USA"},
    {"bank_id": 87, "name": "TD Bank USA", "region": "USA"},
    {"bank_id": 88, "name": "Truist Bank", "region": "USA"},
    {"bank_id": 89, "name": "State Street Bank", "region": "USA"},
    {"bank_id": 90, "name": "Charles Schwab Bank", "region": "USA"},
    {"bank_id": 91, "name": "HSBC Bank USA", "region": "USA"},
    {"bank_id": 92, "name": "BMO Harris Bank", "region": "USA"},
    {"bank_id": 93, "name": "Fifth Third Bank", "region": "USA"},
    {"bank_id": 94, "name": "KeyBank", "region": "USA"},
    {"bank_id": 95, "name": "Regions Bank", "region": "USA"},
    {"bank_id": 96, "name": "Huntington Bank", "region": "USA"},
    {"bank_id": 97, "name": "Citizens Bank", "region": "USA"},
    {"bank_id": 98, "name": "Ally Bank", "region": "USA"},
    {"bank_id": 99, "name": "Synchrony Bank", "region": "USA"},
    {"bank_id": 100, "name": "Discover Bank", "region": "USA"},
    {"bank_id": 101, "name": "First Republic Bank", "region": "USA"},
    {"bank_id": 102, "name": "Silicon Valley Bank", "region": "USA"},
    {"bank_id": 103, "name": "Signature Bank", "region": "USA"},
    {"bank_id": 104, "name": "Comerica Bank", "region": "USA"},
    {"bank_id": 105, "name": "Zions Bank", "region": "USA"},
    {"bank_id": 106, "name": "M&T Bank", "region": "USA"},
    {"bank_id": 107, "name": "BB&T", "region": "USA"},
    {"bank_id": 108, "name": "SunTrust Bank", "region": "USA"},
    {"bank_id": 109, "name": "First Horizon Bank", "region": "USA"},
    {"bank_id": 110, "name": "Umpqua Bank", "region": "USA"},
    {"bank_id": 111, "name": "PacWest Bank", "region": "USA"},
    {"bank_id": 112, "name": "Western Alliance Bank", "region": "USA"},
    {"bank_id": 113, "name": "East West Bank", "region": "USA"},
    {"bank_id": 114, "name": "Valley National Bank", "region": "USA"},
    {"bank_id": 115, "name": "Popular Bank", "region": "USA"},
    {"bank_id": 116, "name": "Ameris Bank", "region": "USA"},
    {"bank_id": 117, "name": "Wintrust Bank", "region": "USA"},
    {"bank_id": 118, "name": "Old National Bank", "region": "USA"},
    {"bank_id": 119, "name": "Associated Bank", "region": "USA"},
    {"bank_id": 120, "name": "Frost Bank", "region": "USA"},
    {"bank_id": 121, "name": "Prosperity Bank", "region": "USA"},
    {"bank_id": 122, "name": "Pinnacle Bank", "region": "USA"},
    {"bank_id": 123, "name": "Webster Bank", "region": "USA"},
    {"bank_id": 124, "name": "New York Community Bank", "region": "USA"},
    {"bank_id": 125, "name": "Cathay Bank", "region": "USA"},
    {"bank_id": 126, "name": "BankUnited", "region": "USA"},
    {"bank_id": 127, "name": "First Citizens Bank", "region": "USA"},
    {"bank_id": 128, "name": "South State Bank", "region": "USA"},
    {"bank_id": 129, "name": "UMB Bank", "region": "USA"},
    {"bank_id": 130, "name": "Glacier Bank", "region": "USA"},
    {"bank_id": 131, "name": "BOK Financial", "region": "USA"},
    {"bank_id": 132, "name": "Atlantic Union Bank", "region": "USA"},
    {"bank_id": 133, "name": "Hancock Whitney Bank", "region": "USA"},
    {"bank_id": 134, "name": "Synovus Bank", "region": "USA"},
    {"bank_id": 135, "name": "Trustmark Bank", "region": "USA"},
    {"bank_id": 136, "name": "Cadence Bank", "region": "USA"},
    {"bank_id": 137, "name": "Arvest Bank", "region": "USA"},
    {"bank_id": 138, "name": "Fulton Bank", "region": "USA"},
    {"bank_id": 139, "name": "Flagstar Bank", "region": "USA"},
    {"bank_id": 140, "name": "Heritage Bank", "region": "USA"},
    {"bank_id": 141, "name": "City National Bank", "region": "USA"},
    {"bank_id": 142, "name": "Bank of Hawaii", "region": "USA"},
    {"bank_id": 143, "name": "First Midwest Bank", "region": "USA"},
    {"bank_id": 144, "name": "Union Bank USA", "region": "USA"},
    {"bank_id": 145, "name": "Sterling National Bank", "region": "USA"},
    {"bank_id": 146, "name": "Chemical Bank", "region": "USA"},
    {"bank_id": 147, "name": "TCF Bank", "region": "USA"},
    {"bank_id": 148, "region": "USA", "name": "IberiaBank"},
    {"bank_id": 149, "region": "USA", "name": "People’s United Bank"},
    {"bank_id": 150, "region": "USA", "name": "Great Western Bank"},
    {"bank_id": 151, "region": "USA", "name": "Santander Bank USA"},
    {"bank_id": 152, "region": "USA", "name": "Rabobank USA"},
    {"bank_id": 153, "region": "USA", "name": "MUFG Union Bank"},
    {"bank_id": 154, "region": "USA", "name": "Mizuho Bank USA"},
    {"bank_id": 155, "region": "USA", "name": "Sumitomo Mitsui Bank USA"},
    {"bank_id": 156, "region": "USA", "name": "BNP Paribas USA"},
    {"bank_id": 157, "region": "USA", "name": "Deutsche Bank USA"},
    {"bank_id": 158, "region": "USA", "name": "Credit Suisse USA"},
    {"bank_id": 159, "region": "USA", "name": "UBS Bank USA"},
    {"bank_id": 160, "region": "USA", "name": "Barclays Bank USA"},
    {"bank_id": 161, "region": "USA", "name": "HSBC Private Bank USA"},
    {"bank_id": 162, "region": "USA", "name": "American Express Bank"},
    {"bank_id": 163, "region": "USA", "name": "Metropolitan Commercial Bank"},
    {"bank_id": 164, "region": "USA", "name": "Customers Bank"},
    {"bank_id": 165, "region": "USA", "name": "Cross River Bank"},
    {"bank_id": 166, "region": "USA", "name": "Axos Bank"},
    {"bank_id": 167, "region": "USA", "name": "Varo Bank"},
    {"bank_id": 168, "region": "USA", "name": "Chime Bank"},
    {"bank_id": 169, "region": "USA", "name": "SoFi Bank"},
    {"bank_id": 170, "region": "USA", "name": "Green Dot Bank"},
    {"bank_id": 171, "region": "USA", "name": "Radius Bank"},
    {"bank_id": 172, "region": "USA", "name": "Simple Bank"},
    {"bank_id": 173, "region": "USA", "name": "Current Bank"},
    {"bank_id": 174, "region": "USA", "name": "One Finance Bank"},
    {"bank_id": 175, "region": "USA", "name": "Aspiration Bank"},
    {"bank_id": 176, "region": "USA", "name": "LendingClub Bank"},
    {"bank_id": 177, "region": "USA", "name": "NorthOne Bank"},
    {"bank_id": 178, "region": "USA", "name": "NBKC Bank"},
    {"bank_id": 179, "region": "USA", "name": "Live Oak Bank"},
    {"bank_id": 180, "region": "USA", "name": "Redwood Credit Union"},
    {"bank_id": 181, "region": "USA", "name": "Navy Federal Credit Union"},
    {"bank_id": 182, "region": "USA", "name": "Alliant Credit Union"},
    {"bank_id": 183, "region": "USA", "name": "Golden 1 Credit Union"},
    {"bank_id": 184, "region": "USA", "name": "Boeing Employees Credit Union"},
    {"bank_id": 185, "region": "USA", "name": "SchoolsFirst Federal CU"},
    {"bank_id": 186, "region": "USA", "name": "America First Credit Union"},
    {"bank_id": 187, "region": "USA", "name": "Pentagon Federal Credit Union"},
    {"bank_id": 188, "region": "USA", "name": "Suncoast Credit Union"},
    {"bank_id": 189, "region": "USA", "name": "SECU Credit Union"},
    {"bank_id": 190, "region": "USA", "name": "Desjardins Bank USA"},
    {"bank_id": 191, "region": "USA", "name": "FirstBank USA"},
    {"bank_id": 192, "region": "USA", "name": "MidFirst Bank"},
    {"bank_id": 193, "region": "USA", "name": "Independent Bank"},
    {"bank_id": 194, "region": "USA", "name": "Hometown Bank"},
    {"bank_id": 195, "region": "USA", "name": "Liberty Bank"},
    {"bank_id": 196, "region": "USA", "name": "Community Bank USA"},
    {"bank_id": 197, "region": "USA", "name": "Farmers Bank"},
    {"bank_id": 198, "region": "USA", "name": "Heritage Community Bank"},
    {"bank_id": 199, "region": "USA", "name": "First National Bank"},
    {"bank_id": 200, "region": "USA", "name": "Security Bank"},
    {"bank_id": 201, "region": "USA", "name": "Citizens National Bank"},
    {"bank_id": 202, "region": "USA", "name": "Peoples Bank"},
    {"bank_id": 203, "region": "CH", "name": "Vontobel Bank"}
]

def seed_banks():
    if Bank.query.first() is None:
        for b in INITIAL_BANKS:
            db.session.add(Bank(bank_id=b["bank_id"], bank_name=b["name"], region=b["region"]))
        db.session.commit()



class BankAccountBalance(db.Model):
    __tablename__ = 'bank_account_balance'
    account_id = db.Column('Bank Account ID', db.Integer, db.ForeignKey('bank_account.Account ID'), primary_key=True)
    riport_id = db.Column('Riport ID', db.Integer, db.ForeignKey('riport_date.Riport ID'), primary_key=True)
    balance = db.Column('Balance', db.Numeric(18, 3))
    state = db.Column('State', db.String(50))
    inspector_1 = db.Column('Inspector 1', db.Integer, db.ForeignKey('users.id'), nullable=True)
    inspector_2 = db.Column('Inspector 2', db.Integer, db.ForeignKey('users.id'), nullable=True)
    approval_time = db.Column('ApprovalTime', db.DateTime, default=datetime.utcnow)

    inspector_1_user = db.relationship('User', foreign_keys=[inspector_1])
    inspector_2_user = db.relationship('User', foreign_keys=[inspector_2])

class BankAccountPendingBalance(db.Model):
    __tablename__ = 'bank_account_pending_balance'
    account_id = db.Column('Bank Account ID', db.Integer, db.ForeignKey('bank_account.Account ID'), primary_key=True)
    riport_id = db.Column('Riport ID', db.Integer, db.ForeignKey('riport_date.Riport ID'), primary_key=True)
    balance = db.Column('Balance', db.Numeric(18, 3))
    state = db.Column('State', db.String(50))
    inspector_1 = db.Column('Inspector 1', db.Integer, db.ForeignKey('users.id'), nullable=True)
    inspector_2 = db.Column('Inspector 2', db.Integer, db.ForeignKey('users.id'), nullable=True)
    approval_time = db.Column('ApprovalTime', db.DateTime, default=datetime.utcnow)

    account = db.relationship('BankAccount', foreign_keys=[account_id], back_populates='pending_balances')
    riport_date = db.relationship('RiportDate', foreign_keys=[riport_id])
    inspector_1_user = db.relationship('User', foreign_keys=[inspector_1])

class BankAccount(db.Model):
    __tablename__ = 'bank_account'
    account_id = db.Column('Account ID', db.Integer, primary_key=True)
    trust_id = db.Column('Trust ID', db.Integer, db.ForeignKey('managed_trusts.Trust ID'), nullable=True)
    bank_id = db.Column('Bank ID', db.Integer, db.ForeignKey('bank.BANK ID'), nullable=True)
    currency_id = db.Column('Currency', db.Integer, db.ForeignKey('currency.id'), nullable=True)
    type = db.Column('Type', db.String(50))
    account_number_iban = db.Column('Account number (IBAN)', db.String(34))
    account_number_pfj = db.Column('Account number (PFJ)', db.String(50))
    bank_account_name = db.Column('Bank account name', db.String(100))
    contract_date = db.Column('Contract Date', db.Date)
    end_date = db.Column('End of Management Date', db.Date)
    status = db.Column('Status', db.String(50))
    state = db.Column('State', db.String(50))
    inspector_1 = db.Column('Inspector 1', db.Integer, db.ForeignKey('users.id'), nullable=True)
    inspector_2 = db.Column('Inspector 2', db.Integer, db.ForeignKey('users.id'), nullable=True)
    approval_time = db.Column('ApprovalTime', db.DateTime, default=datetime.utcnow)
    

    currency = db.relationship('Currency', foreign_keys=[currency_id])
    inspector_1_user = db.relationship('User', foreign_keys=[inspector_1])
    inspector_2_user = db.relationship('User', foreign_keys=[inspector_2])
    balances = db.relationship('BankAccountBalance', backref='bank_account', lazy=True)
    pending_balances = db.relationship('BankAccountPendingBalance', back_populates='account', lazy=True)
    pending_changes = db.relationship('BankAccountPending', back_populates='original', cascade='all, delete-orphan')
    trust = db.relationship('ManagedTrusts', foreign_keys=[trust_id])


class ManagedTrusts(db.Model):
    __tablename__ = 'managed_trusts'
    trust_id = db.Column('Trust ID', db.Integer, primary_key=True)
    trust_name = db.Column('Trust Name', db.String(100))
    contract_number = db.Column('Contract number', db.String(50))
    tax_number = db.Column('Tax number', db.String(50))
    contract_date = db.Column('Contract Date', db.Date)
    end_date = db.Column('End of Management Date', db.Date, nullable=True)
    riporting_currency = db.Column('Riporting currency', db.Integer, db.ForeignKey('currency.id'), nullable=True)
    status = db.Column('Status', db.String(50))
    state = db.Column('State', db.String(50))
    inspector_1 = db.Column('Inspector 1', db.Integer, db.ForeignKey('users.id'), nullable=True)
    inspector_2 = db.Column('Inspector 2', db.Integer, db.ForeignKey('users.id'), nullable=True)
    approval_time = db.Column('ApprovalTime', db.DateTime, default=datetime.utcnow)

    bank_accounts = db.relationship('BankAccount', backref='managed_trust', lazy=True)
    pending_changes = db.relationship('ManagedTrustsPending', back_populates='original', cascade='all, delete-orphan')
    reports = db.relationship('Report', back_populates='trust')
    currency = db.relationship('Currency', foreign_keys=[riporting_currency])
    inspector_1_user = db.relationship('User', foreign_keys=[inspector_1])
    inspector_2_user = db.relationship('User', foreign_keys=[inspector_2])



class BankAccountPending(db.Model):
    __tablename__ = 'bank_account_pending'
    account_id = db.Column('Account ID', db.Integer, primary_key=True)
    original_account_id = db.Column('Original Account ID', db.Integer, db.ForeignKey('bank_account.Account ID'), nullable=True)
    trust_id = db.Column('Trust ID', db.Integer, db.ForeignKey('managed_trusts.Trust ID'), nullable=True)
    bank_id = db.Column('Bank ID', db.Integer, db.ForeignKey('bank.BANK ID'), nullable=True)
    currency_id = db.Column('Currency', db.Integer, db.ForeignKey('currency.id'), nullable=True)
    type = db.Column('Type', db.String(50))
    account_number_iban = db.Column('Account number (IBAN)', db.String(34))
    account_number_pfj = db.Column('Account number (PFJ)', db.String(50))
    bank_account_name = db.Column('Bank account name', db.String(100))
    contract_date = db.Column('Contract Date', db.Date)
    end_date = db.Column('End of Management Date', db.Date)
    status = db.Column('Status', db.String(50))
    state = db.Column('State', db.String(50))
    inspector_1 = db.Column('Inspector 1', db.Integer, db.ForeignKey('users.id'), nullable=True)
    inspector_2 = db.Column('Inspector 2', db.Integer, db.ForeignKey('users.id'), nullable=True)
    approval_time = db.Column('ApprovalTime', db.DateTime, default=datetime.utcnow)
    

    currency = db.relationship('Currency', foreign_keys=[currency_id])
    bank = db.relationship('Bank', foreign_keys=[bank_id])
    inspector_1_user = db.relationship('User', foreign_keys=[inspector_1])
    trust = db.relationship('ManagedTrusts', foreign_keys=[trust_id])
    original = db.relationship('BankAccount', foreign_keys=[original_account_id], back_populates='pending_changes')


class ManagedTrustsPending(db.Model):
    __tablename__ = 'managed_trusts_pending'
    trust_id = db.Column('Trust ID', db.Integer, primary_key=True)
    original_trust_id = db.Column('Original Trust ID', db.Integer, db.ForeignKey('managed_trusts.Trust ID'), nullable=True)
    trust_name = db.Column('Trust Name', db.String(100))
    contract_number = db.Column('Contract number', db.String(50))
    tax_number = db.Column('Tax number', db.String(50))
    contract_date = db.Column('Contract Date', db.Date)
    end_date = db.Column('End of Management Date', db.Date, nullable=True)
    riporting_currency = db.Column('Riporting currency', db.Integer, db.ForeignKey('currency.id'), nullable=True)
    status = db.Column('Status', db.String(50))
    state = db.Column('State', db.String(50))
    inspector_1 = db.Column('Inspector 1', db.Integer, db.ForeignKey('users.id'), nullable=True)
    inspector_2 = db.Column('Inspector 2', db.Integer, db.ForeignKey('users.id'), nullable=True)
    approval_time = db.Column('ApprovalTime', db.DateTime, default=datetime.utcnow)

    currency = db.relationship('Currency', foreign_keys=[riporting_currency])
    inspector_1_user = db.relationship('User', foreign_keys=[inspector_1])
    inspector_2_user = db.relationship('User', foreign_keys=[inspector_2])
    original = db.relationship('ManagedTrusts', foreign_keys=[original_trust_id], back_populates='pending_changes')


class ManagedAssets(db.Model):
    __tablename__ = 'managed_assets'
    asset_id = db.Column('asset ID', db.Integer, primary_key=True)
    asset_type = db.Column('Asset Type', db.String(50))
    asset_name = db.Column('asset Name', db.String(100))
    currency_id = db.Column('Currency', db.Integer, db.ForeignKey('currency.id'), nullable=True)
    isin = db.Column('ISIN', db.String(12))
    nominal_value = db.Column('Nominal Value', db.Numeric(18, 2))
    price_decimals = db.Column('Price Decimals', db.Integer)
    state = db.Column('State', db.String(50))
    inspector_1 = db.Column('Inspector 1', db.Integer, db.ForeignKey('users.id'), nullable=True)
    inspector_2 = db.Column('Inspector 2', db.Integer, db.ForeignKey('users.id'), nullable=True)
    approval_time = db.Column('ApprovalTime', db.DateTime, default=datetime.utcnow)

    currency = db.relationship('Currency', foreign_keys=[currency_id])
    inspector_1_user = db.relationship('User', foreign_keys=[inspector_1])
    inspector_2_user = db.relationship('User', foreign_keys=[inspector_2])
    pending_changes = db.relationship('ManagedAssetsPending', back_populates='original', cascade='all, delete-orphan')


class ManagedAssetsPending(db.Model):
    __tablename__ = 'managed_assets_pending'
    asset_id = db.Column('asset ID', db.Integer, primary_key=True)
    original_asset_id = db.Column('Original Asset ID', db.Integer, db.ForeignKey('managed_assets.asset ID'), nullable=True)
    asset_type = db.Column('Asset Type', db.String(50))
    asset_name = db.Column('asset Name', db.String(100))
    currency_id = db.Column('Currency', db.Integer, db.ForeignKey('currency.id'), nullable=True)
    isin = db.Column('ISIN', db.String(12))
    nominal_value = db.Column('Nominal Value', db.Numeric(18, 2))
    price_decimals = db.Column('Price Decimals', db.Integer)
    state = db.Column('State', db.String(50))
    inspector_1 = db.Column('Inspector 1', db.Integer, db.ForeignKey('users.id'), nullable=True)
    inspector_2 = db.Column('Inspector 2', db.Integer, db.ForeignKey('users.id'), nullable=True)
    approval_time = db.Column('ApprovalTime', db.DateTime, default=datetime.utcnow)

    currency = db.relationship('Currency', foreign_keys=[currency_id])
    inspector_1_user = db.relationship('User', foreign_keys=[inspector_1])
    inspector_2_user = db.relationship('User', foreign_keys=[inspector_2])
    original = db.relationship('ManagedAssets', foreign_keys=[original_asset_id], back_populates='pending_changes')


class Report(db.Model):
    __tablename__ = 'reports'
    report_id = db.Column('Report ID', db.Integer, primary_key=True)
    report_name = db.Column('Report Name', db.String(100), nullable=False)
    trust_id = db.Column('Trust ID', db.Integer, db.ForeignKey('managed_trusts.Trust ID'), nullable=True)
    report_date = db.Column('Report Date', db.Date)
    description = db.Column('Description', db.String(500))
    created_by = db.Column('Created By', db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column('Created At', db.DateTime, default=datetime.utcnow)
    updated_by = db.Column('Updated By', db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_at = db.Column('Updated At', db.DateTime, default=datetime.utcnow)

    trust = db.relationship('ManagedTrusts', foreign_keys=[trust_id], back_populates='reports')
    created_by_user = db.relationship('User', foreign_keys=[created_by])
    updated_by_user = db.relationship('User', foreign_keys=[updated_by])

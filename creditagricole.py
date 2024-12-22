from datetime import datetime, timedelta

from creditagricole_particuliers import Authenticator, Accounts
from constant import *
import urllib.parse
import requests


class CreditAgricoleAuthenticator(Authenticator):
    def __init__(self, username, password, ca_region):
        """custom authenticator class"""
        self.url = "https://www.credit-agricole.fr"
        self.ssl_verify = True
        self.username = username
        self.password = password
        self.department = "none"
        self.regional_bank_url = "ca-" + ca_region
        self.cookies = None

        self.authenticate()


class CreditAgricoleClient:

    def __init__(self, logger):
        self.logger = logger
        self.department = BANK_DEPARTMENT_DEFAULT
        self.account_id = BANK_ACCOUNT_ID_DEFAULT
        self.password = BANK_PASSWORD_DEFAULT
        self.enabled_accounts = IMPORT_ACCOUNT_ID_LIST_DEFAULT
        self.get_transactions_period = GET_TRANSACTIONS_PERIOD_DAYS_DEFAULT
        self.max_transactions = MAX_TRANSACTIONS_PER_GET_DEFAULT
        self.region_id = None
        self.session = None

    def validate(self):
        if self.department == BANK_DEPARTMENT_DEFAULT:
            self.logger.error("Please set your bank account department.")
        self.region_id = CreditAgricoleRegion.get_ca_region(self.department)
        if self.region_id is None:
            self.logger.error("Unknown department number. Please contact the developers.")
        if len(self.region_id) > 1:
            msg = "Unfortunately your department number is not enough to know what is your CA region. Please replace your department number by one of the following CA region :\n"
            for ca_reg in self.region_id:
                msg = msg + "-> " + BANK_DEPARTMENT_FIELD + " = " + ca_reg + " (if your accounts are managed by Credit Agricole " + CA_REGIONS[ca_reg] + ")\n\r"
            self.logger.error(msg)
        else:
            self.region_id = self.region_id[0]
        if not self.account_id.isdigit() or len(self.account_id) != len(BANK_ACCOUNT_ID_DEFAULT) or self.account_id == BANK_ACCOUNT_ID_DEFAULT:
            self.logger.error("Your bank account ID must be a 11 long digit.")
        if not self.password.isdigit() or len(self.password) != len(BANK_PASSWORD_DEFAULT) or self.password == BANK_PASSWORD_DEFAULT:
            self.logger.error("Your bank password must be a 6 long digit.")
        if self.enabled_accounts == IMPORT_ACCOUNT_ID_LIST_DEFAULT:
            self.logger.error("Please set your account ID list to import.")
        if not self.get_transactions_period.isdigit() or int(self.get_transactions_period) < 0:
            self.logger.error("Your transactions's get period must be a positive number.")
        if not self.max_transactions.isdigit() or int(self.max_transactions) < 0:
            self.logger.error("The maximum number of transactions to get must be a positive number.")

    def init_session(self):
        password_list = []
        for i in range(len(self.password)):
            password_list.append(int(self.password[i]))
        self.session = CreditAgricoleAuthenticator(username=self.account_id, password=password_list, ca_region=self.region_id)

    def get_accounts(self):
        accounts = []
        for account in Accounts(session=self.session):
            if account.numeroCompte in [x.strip() for x in self.enabled_accounts.split(",")]:
                accounts.append(account)
        return accounts

    def get_transactions(self, account_id):
        account = Accounts(session=self.session).search(num=account_id)

        current_date = datetime.today()
        previous_date = current_date - timedelta(days=int(self.get_transactions_period))
        date_stop_ = current_date.strftime('%Y-%m-%d')
        date_start_ = previous_date.strftime('%Y-%m-%d')

        return [op.descr for op in account.get_operations(count=int(self.max_transactions), date_start=date_start_, date_stop=date_stop_)]


class CreditAgricoleRegion:

    def __init__(self, ca_region):

        self.name = CA_REGIONS[ca_region]
        self.longitude = None
        self.latitude = None

        # Find the bank region location
        address = "Credit Agricole " + self.name + ", France"
        url = 'https://nominatim.openstreetmap.org/search.php?q=' + urllib.parse.quote(address) + '&format=jsonv2'
        openstreetmap_headers = {'User-Agent': 'credit-agricole-importer'}
        response = requests.get(url, headers=openstreetmap_headers).json()

        if len(response) > 0 and "lon" in response[0] and "lat" in response[0]:
            self.longitude = str(response[0]['lon'])
            self.latitude = str(response[0]['lat'])

    @staticmethod
    def get_ca_region(department_id: str):
        if department_id in CA_REGIONS.keys():
            return [department_id]
        department_id = str(int(department_id)) if department_id.isdigit() else department_id
        for key, value in DEPARTMENTS_TO_CA_REGIONS.items():
            if department_id in key:
                return value
        return None


CA_REGIONS = {
    "alpesprovence": "Alpes Provence",
    "alsace-vosges": "Alsace Vosges",
    "anjou-maine": "Anjou Maine",
    "aquitaine": "Aquitaine",
    "atlantique-vendee": "Atlantique Vendée",
    "briepicardie": "Brie Picardie",
    "centrest": "Centre Est",
    "centrefrance": "Centre France",
    "centreloire": "Centre Loire",
    "centreouest": "Centre Ouest",
    "cb": "Champagne Bourgogne",
    "cmds": "Charente Maritime Deux-Sèvres",
    "charente-perigord": "Charente Périgord",
    "corse": "Corse",
    "cotesdarmor": "Côtes d'Armor",
    "des-savoie": "Des Savoie",
    "finistere": "Finistère",
    "franchecomte": "Franche Comté",
    "guadeloupe": "Guadeloupe",
    "illeetvilaine": "Ille et Vilaine",
    "languedoc": "Languedoc",
    "loirehauteloire": "Loire Haute-Loire",
    "lorraine": "Lorraine",
    "martinique": "Martinique",
    "morbihan": "Morbihan",
    "norddefrance": "Nord de France",
    "nord-est": "Nord Est",
    "nmp": "Nord Midi Pyrénées",
    "normandie": "Normandie",
    "normandie-seine": "Normandie Seine",
    "paris": "Paris",
    "pca": "Provence Côte d'Azur",
    "pyrenees-gascogne": "Pyrénées Gascogne",
    "reunion": "Réunion",
    "sudmed": "Sud Méditerranée",
    "sudrhonealpes": "Sud Rhône Alpes",
    "toulouse31": "Toulouse",
    "tourainepoitou": "Touraine Poitou",
    "valdefrance": "Val de France",
}

DEPARTMENTS_TO_CA_REGIONS = {
    ('20', '2A', '2B'): ['corse'],
    ('1', '71'): ['centrest'],
    ('2', '8', '51'): ['nord-est'],
    ('4', '6', '83'): ['pca'],
    ('5', '13', '84'): ['alpesprovence'],
    ('10', '21', '52', '89'): ['cb'],
    ('11', '30', '34', '48'): ['languedoc'],
    ('12', '46', '81', '82'): ['nmp'],
    ('14', '50'): ['normandie'],
    ('53', '61'): ['normandie', 'anjou-maine'],
    ('15', '23', '63', '03', '19'): ['centrefrance'],
    ('16', '24'): ['charente-perigord'],
    ('17', '79'): ['cmds'],
    ('18', '58'): ['centreloire'],
    ('56',): ['morbihan'],
    ('45',): ['briepicardie', 'centreloire'],
    ('22',): ['cotesdarmor'],
    ('25', '39', '70', '90'): ['franchecomte'],
    ('26', '38', '69', '7'): ['centrest', 'sudrhonealpes'],
    ('27', '76'): ['normandie-seine'],
    ('28', '41'): ['valdefrance'],
    ('29',): ['finistere'],
    ('31',): ['toulouse31'],
    ('32',): ['aquitaine', 'pyrenees-gascogne'],
    ('33', '40', '47'): ['aquitaine'],
    ('35',): ['illeetvilaine'],
    ('36', '87'): ['centreouest'],
    ('37', '86'): ['tourainepoitou'],
    ('54', '55', '57'): ['lorraine'],
    ('67', '68', '88'): ['alsace-vosges'],
    ('42', '43'): ['loirehauteloire'],
    ('44', '85'): ['atlantique-vendee'],
    ('11', '30', '34', '48',): ['languedoc'],
    ('49', '72'): ['anjou-maine'],
    ('59', '62'): ['norddefrance'],
    ('64', '65'): ['pyrenees-gascogne'],
    ('66', '9'): ['sudmed'],
    ('73', '74'): ['des-savoie'],
    ('75', '91', '92', '93', '94', '95', '78'): ['paris'],
    ('60',): ['briepicardie', 'paris'],
    ('80', '77'): ['briepicardie'],
    ('971',): ['guadeloupe'],
    ('972', '973'): ['martinique'],
    ('974',): ['reunion']
}

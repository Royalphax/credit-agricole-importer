from datetime import datetime, timedelta

from creditagricole_particuliers import Authenticator, Accounts
from constant import *
import urllib.parse
import requests


class CreditAgricoleClient:

    def __init__(self, logger):
        self.logger = logger
        self.department = BANK_DEPARTMENT_DEFAULT
        self.account_id = BANK_ACCOUNT_ID_DEFAULT
        self.password = BANK_PASSWORD_DEFAULT
        self.enabled_accounts = IMPORT_ACCOUNT_ID_LIST_DEFAULT
        self.get_transactions_period = GET_TRANSACTIONS_PERIOD_DAYS_DEFAULT
        self.max_transactions = MAX_TRANSACTIONS_PER_GET_DEFAULT
        self.session = None

    def validate(self):
        if self.department == BANK_DEPARTMENT_DEFAULT:
            self.logger.error("Please set your bank account region.")
        if self.department not in CreditAgricoleRegion.DEPARTMENTS_TO_REGIONS.keys():
            self.logger.error("This department doesn't exist.")
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
        self.session = Authenticator(username=self.account_id, password=password_list, department=self.department)

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

    REGIONS = {
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

    DEPARTMENTS_TO_REGIONS = {
        '01': 'sudrhonealpes',
        '02': 'briepicardie',
        '05': 'alpesprovence',
        '06': 'alpesprovence',
        '07': 'sudrhonealpes',
        '08': 'nord-est',
        '09': 'pyrenees-gascogne',
        '10': 'nord-est',
        '11': 'languedoc',
        '13': 'alpesprovence',
        '14': 'normandie',
        '15': 'cmds',
        '16': 'charente-perigord',
        '17': 'centreouest',
        '18': 'centreloire',
        '21': 'centrefrance',
        '22': 'cotesdarmor',
        '24': 'aquitaine',
        '25': 'franchecomte',
        '26': 'sudrhonealpes',
        '27': 'normandie',
        '28': 'centrest',
        '29': 'finistere',
        '30': 'languedoc',
        '31': 'pyrenees-gascogne',
        '32': 'pyrenees-gascogne',
        '33': 'aquitaine',
        '34': 'sudmed',
        '35': 'illeetvilaine',
        '36': 'centrest',
        '37': 'centrest',
        '37': 'tourainepoitou',
        '38': 'sudrhonealpes',
        '39': 'franchecomte',
        '40': 'aquitaine',
        '40': 'pyrenees-gascogne',
        '41': 'centrest',
        '41': 'tourainepoitou',
        '42': 'loirehauteloire',
        '42': 'sudrhonealpes',
        '43': 'cmds',
        '43': 'loirehauteloire',
        '44': 'atlantique-vendee',
        '45': 'centrest',
        '47': 'aquitaine',
        '48': 'languedoc',
        '48': 'sudmed',
        '49': 'anjou-maine',
        '50': 'normandie',
        '51': 'nord-est',
        '52': 'nord-est',
        '53': 'anjou-maine',
        '54': 'lorraine',
        '55': 'lorraine',
        '55': 'nord-est',
        '56': 'morbihan',
        '57': 'lorraine',
        '57': 'nord-est',
        '58': 'centrefrance',
        '59': 'norddefrance',
        '60': 'briepicardie',
        '61': 'normandie',
        '62': 'norddefrance',
        '63': 'loirehauteloire',
        '64': 'pyrenees-gascogne',
        '66': 'languedoc',
        '66': 'sudmed',
        '67': 'alsace-vosges',
        '67': 'nord-est',
        '68': 'alsace-vosges',
        '68': 'nord-est',
        '69': 'loirehauteloire',
        '69': 'sudrhonealpes',
        '70': 'franchecomte',
        '71': 'centrefrance',
        '72': 'anjou-maine',
        '73': 'des-savoie',
        '73': 'sudrhonealpes',
        '74': 'des-savoie',
        '74': 'sudrhonealpes',
        '75': 'paris',
        '76': 'normandie',
        '76': 'normandie-seine',
        '77': 'valdefrance',
        '79': 'centreouest',
        '80': 'briepicardie',
        '83': 'pca',
        '84': 'pca',
        '85': 'atlantique-vendee',
        '86': 'centreouest',
        '86': 'tourainepoitou',
        '88': 'lorraine',
        '88': 'nord-est',
        '971': 'guadeloupe',
        '972': 'martinique',
        '974': 'reunion',
        '9A': 'cb',
        '9B': 'cb'
    }        

    def __init__(self, department_id):
        if department_id not in self.DEPARTMENTS_TO_REGIONS.keys():
            raise ValueError("This department doesn't exist.")

        region_id = self.DEPARTMENTS_TO_REGIONS[department_id]

        if region_id not in self.REGIONS.keys():
            raise ValueError("This Credit Agricole region doesn't exist.")

        self.name = self.REGIONS[region_id]
        self.longitude = None
        self.latitude = None

        # Find the bank region location
        address = "Credit Agricole " + self.name + ", France"
        url = 'https://nominatim.openstreetmap.org/search.php?q=' + urllib.parse.quote(address) +'&format=jsonv2'
        response = requests.get(url).json()
        if len(response) > 0 and "lon" in response[0] and "lat" in response[0]:
            self.longitude = str(response[0]['lon'])
            self.latitude = str(response[0]['lat'])

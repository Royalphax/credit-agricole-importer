from creditagricole import CreditAgricoleRegion
from tool import *
import requests
import time
import locale

from constant import *

_TRANSACTIONS_ENDPOINT = 'api/v1/transactions'
_ACCOUNTS_ENDPOINT = 'api/v1/accounts'
_BUDGETS_ENDPOINT = 'api/v1/budgets'


class Firefly3Client:
    def __init__(self):
        self.a_rename_transaction = {}
        self.aa_tags = {}
        self.aa_account = {}
        self.aa_category = {}
        self.aa_budget = {}

        self.token = PERSONAL_TOKEN_DEFAULT
        self.hostname = HOSTNAME_DEFAULT
        self.name_format = ACCOUNTS_NAME_FORMAT_DEFAULT
        self.headers = None

    def _post(self, endpoint, payload):
        response = requests.post("{}{}".format(self.hostname, endpoint), json=payload, headers=self.headers)
        if response.status_code != 200:
            raise ValueError("Request to your Firefly3 instance failed. Please double check your personal token.")
        return response.json()

    def _get(self, endpoint, params=None):
        response = requests.get("{}{}".format(self.hostname, endpoint), params=params, headers=self.headers)
        if response.status_code != 200:
            raise ValueError("Request to your Firefly3 instance failed. Please double check your personal token.")
        return response.json()

    def validate(self):
        if self.hostname == HOSTNAME_DEFAULT:
            print("WARN: The firefly3 instance HOSTNAME is the demo website.")
        if len(self.token) != len(PERSONAL_TOKEN_DEFAULT) or self.token == PERSONAL_TOKEN_DEFAULT:
            raise ValueError("Your firefly3 personal token isn't 980 characters long or isn't set.")
        if len(self.name_format) == 0 or BANK_ACCOUNT_NAME_PLACEHOLDER not in self.name_format:
            raise ValueError(
                "Your firefly3 accounts name format must contain the bank account name placeholder: " + BANK_ACCOUNT_NAME_PLACEHOLDER + ".")

        if self.hostname[-1] != "/":
            self.hostname = self.hostname + "/"

        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + self.token,
        }

    def init_auto_assign_values(self, a_rename_transaction_section, aa_budget_section, aa_category_section, aa_account_section, aa_tags_section):
        for key in a_rename_transaction_section.keys():
            self.a_rename_transaction[key] = [e.strip() for e in a_rename_transaction_section.get(key, "").split(",")]
        for key in aa_budget_section.keys():
            self.aa_budget[key] = [e.strip() for e in aa_budget_section.get(key, "").split(",")]
        for key in aa_category_section.keys():
            self.aa_category[key] = [e.strip() for e in aa_category_section.get(key, "").split(",")]
        for key in aa_account_section.keys():
            self.aa_account[key] = [e.strip() for e in aa_account_section.get(key, "").split(",")]
        for key in aa_tags_section.keys():
            self.aa_tags[key] = [e.strip() for e in aa_tags_section.get(key, "").split(",")]

    def get_budget_id(self, name, create_if_not_exists=True):
        budgets = self._get(_BUDGETS_ENDPOINT).get("data")
        for budget in budgets:
            if budget["attributes"]["name"] == name:
                return budget["id"]
        if create_if_not_exists:
            return self._post(_BUDGETS_ENDPOINT, {"name": name}).get("data")["id"]
        return "-1"

    def get_account_id(self, account_number):
        accounts = self._get(_ACCOUNTS_ENDPOINT).get("data")
        for account in accounts:
            if account["attributes"]["account_number"] == account_number:
                return account["id"]
        return "-1"

    def get_accounts(self, account_type="asset"):
        return self._get(_ACCOUNTS_ENDPOINT, params={"type": account_type}).get("data")

    def create_account(self, name, region, account_number, family_code):
        payload = {
            "name": self.name_format.replace(BANK_ACCOUNT_NAME_PLACEHOLDER, name),
            "type": "asset",
            "account_number": account_number
        }

        # Classify account from family code
        if family_code == "1":
            payload["account_role"] = "defaultAsset"
        elif family_code == "3":
            payload["account_role"] = "savingAsset"

        ca_region = CreditAgricoleRegion(region)
        if ca_region.latitude is not None and ca_region.longitude is not None:
            payload["latitude"] = ca_region.latitude
            payload["longitude"] = ca_region.longitude
            payload["zoom_level"] = 6

        return self._post(endpoint=_ACCOUNTS_ENDPOINT, payload=payload)


class Firefly3Transactions:
    def __init__(self, f3_cli):
        self.f3_cli = f3_cli
        self.payloads = []

    def __len__(self):
        return len(self.payloads)

    def add_transaction(self, ca_payload, account_id):
        payload = {"transactions": [{}]}

        transaction_name = ca_payload["libelleOperation"].strip()
        transaction = payload["transactions"][0]

        renames = get_key_from_value(self.f3_cli.a_rename_transaction, transaction_name)
        transaction["description"] = renames[0] if len(renames) > 0 else transaction_name

        locale.setlocale(locale.LC_TIME, "en_GB")
        date = time.mktime(time.strptime(ca_payload["dateOperation"], '%b %d, %Y %H:%M:%S %p'))
        transaction["date"] = time.strftime("%Y-%m-%d", time.gmtime(date))

        transaction["amount"] = abs(ca_payload["montant"])
        transaction["currency_code"] = ca_payload["idDevise"]

        accounts = get_key_from_value(self.f3_cli.aa_account, transaction_name)
        if ca_payload["montant"] > 0:
            transaction["type"] = "deposit"
            transaction["source_name"] = accounts[0] if len(accounts) > 0 else "Cash account"
            transaction["destination_id"] = int(account_id)
        else:
            transaction["type"] = "withdrawal"
            transaction["source_id"] = int(account_id)
            transaction["destination_name"] = accounts[0] if len(accounts) > 0 else "Cash account"

        budgets = get_key_from_value(self.f3_cli.aa_budget, transaction_name)
        if len(budgets) != 0:
            transaction["budget_id"] = self.f3_cli.get_budget_id(budgets[0])

        categories = get_key_from_value(self.f3_cli.aa_category, transaction_name)
        if len(categories) != 0:
            transaction["category_name"] = categories[0]

        tags = [ca_payload["libelleTypeOperation"].strip()]
        for tag in get_key_from_value(self.f3_cli.aa_tags, transaction_name):
            tags.append(tag)
        transaction["tags"] = tags
        self.payloads.append(payload)

    def post(self):
        for payload in self.payloads:
            print(".", end='')
            self.f3_cli._post(endpoint=_TRANSACTIONS_ENDPOINT, payload=payload)

from creditagricole import CreditAgricoleRegion
from tool import *
import requests
import time
import json

from constant import *

_TRANSACTIONS_ENDPOINT = 'api/v1/transactions'
_ACCOUNTS_ENDPOINT = 'api/v1/accounts'
_BUDGETS_ENDPOINT = 'api/v1/budgets'


class Firefly3Client:
    def __init__(self, logger, debug):
        self.logger = logger
        self.debug = debug
        self.a_rename_transaction = {}
        self.aa_tags = {}
        self.aa_account = {}
        self.aa_category = {}
        self.aa_budget = {}

        self.token = PERSONAL_TOKEN_DEFAULT
        self.hostname = HOSTNAME_DEFAULT
        self.name_format = ACCOUNTS_NAME_FORMAT_DEFAULT
        self.auto_detect_transfers = bool(AUTO_DETECT_TRANSFERS_DEFAULT)
        self.transfer_source_transaction = TRANSFER_SOURCE_TRANSACTION_NAME_DEFAULT.strip().split(",")
        self.transfer_destination_transaction = TRANSFER_DESTINATION_TRANSACTION_NAME_DEFAULT.strip().split(",")
        self.headers = None

    def _post(self, endpoint, payload):
        response = requests.post("{}{}".format(self.hostname, endpoint), json=payload, headers=self.headers)
        if response.status_code != 200:
            self.logger.error("Request to your Firefly3 instance failed. Please double check your personal token. Error : " + str(response.json()))
        return response.json()

    def _get(self, endpoint, params=None):
        response = requests.get("{}{}".format(self.hostname, endpoint), params=params, headers=self.headers)
        if response.status_code != 200:
            self.logger.error("Request to your Firefly3 instance failed. Please double check your personal token. Error : " + str(response.json()))
        return response.json()

    def validate(self):
        if self.hostname == HOSTNAME_DEFAULT:
            self.logger.log("WARN: The firefly3 instance HOSTNAME is the demo website.")
        if len(self.token) != len(PERSONAL_TOKEN_DEFAULT) or self.token == PERSONAL_TOKEN_DEFAULT:
            self.logger.error("Your firefly3 personal token isn't 980 characters long or isn't set.")
        if len(self.name_format) == 0 or BANK_ACCOUNT_NAME_PLACEHOLDER not in self.name_format:
            self.logger.error("Your firefly3 accounts name format must contain the bank account name placeholder: " + BANK_ACCOUNT_NAME_PLACEHOLDER + ".")

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
    def __init__(self, f3_cli, account_id):
        self.f3_cli = f3_cli
        self.account_id = int(account_id)
        self.payloads = []
        self.transfer_out = {}
        self.transfer_in = {}

    def __len__(self):
        count = 0
        for transfer_list in [self.transfer_in, self.transfer_out]:
            for date in transfer_list:
                count = count + len(transfer_list[date])
        return len(self.payloads) + count

    def add_transaction(self, ca_payload):
        self.f3_cli.logger.log(str(ca_payload), debug=True, other_tag="[CA PAYLOAD]")

        payload = {"transactions": [{}]}

        transaction_name = ' '.join(ca_payload["libelleOperation"].strip().split())
        transaction = payload["transactions"][0]

        renames = get_key_from_value(self.f3_cli.a_rename_transaction, transaction_name)
        transaction["description"] = renames[0] if len(renames) > 0 else transaction_name

        date = time.mktime(time.strptime(ca_payload["dateOperation"], '%b %d, %Y, %H:%M:%S %p'))
        transaction["date"] = time.strftime("%Y-%m-%dT%T", time.gmtime(date))

        transaction["amount"] = abs(ca_payload["montant"])
        transaction["currency_code"] = ca_payload["idDevise"]

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

        notes = "---------- MORE DETAILS ----------"
        for key in ca_payload.keys():
            notes = notes + '\n\n' + str(key) + ": " + str(ca_payload[key]).strip()
        transaction["notes"] = notes[:-2]

        is_transfer = True
        if self.f3_cli.auto_detect_transfers and is_in_list(self.f3_cli.transfer_source_transaction, transaction_name):

            key = transaction["date"]
            if key not in self.transfer_out:
                self.transfer_out[key] = []
            self.transfer_out[key].append(payload)

        elif self.f3_cli.auto_detect_transfers and is_in_list(self.f3_cli.transfer_destination_transaction, transaction_name):

            key = transaction["date"]
            if key not in self.transfer_in:
                self.transfer_in[key] = []
            self.transfer_in[key].append(payload)

        else:
            is_transfer = False

            accounts = get_key_from_value(self.f3_cli.aa_account, transaction_name)
            if ca_payload["montant"] > 0:
                transaction["type"] = "deposit"
                transaction["source_name"] = accounts[0] if len(accounts) > 0 else "Cash account"
                transaction["destination_id"] = self.account_id
            else:
                transaction["type"] = "withdrawal"
                transaction["source_id"] = self.account_id
                transaction["destination_name"] = accounts[0] if len(accounts) > 0 else "Cash account"

            self.payloads.append(payload)

        self.f3_cli.logger.log(str(payload), debug=True, other_tag=("" if not is_transfer else "[TRANSFER]"))

    def post(self):
        #final_payload = {"transactions": []}
        #for i in range(len(self.payloads)):
        #    final_payload["transactions"].append(self.payloads[i]["transactions"][0])
        #print(final_payload)
        #self.f3_cli._post(endpoint=_TRANSACTIONS_ENDPOINT, payload=final_payload)

        for payload in self.payloads:
            res = self.f3_cli._post(endpoint=_TRANSACTIONS_ENDPOINT, payload=payload)
            if not self.f3_cli.debug:
                self.f3_cli.logger.log(".", end='')
            self.f3_cli.logger.log(str(res), debug=True)

    @staticmethod
    def post_transfers(f3transactions_list, f3_cli):
        payloads = []
        detected_transfers = 0

        # Loop through all transaction packages
        for f3_from_transactions in f3transactions_list:
            # Count detected transfers for later test
            detected_transfers = detected_transfers + len(f3_from_transactions) - len(f3_from_transactions.payloads)
            # Loop through dates of outgoing transfers of the above transaction package
            for date_out in f3_from_transactions.transfer_out.keys():
                # Loop through outgoing transfers for the above date
                for transfer_out in f3_from_transactions.transfer_out[date_out]:
                    # Get the amount
                    amount_out = transfer_out["transactions"][0]["amount"]
                    # Now loop through other transaction packages
                    for f3_to_transactions in f3transactions_list:
                        # If the above transaction package is the same than the first one, skip  it
                        if f3_to_transactions.account_id == f3_from_transactions.account_id:
                            continue
                        # Loop through dates of incoming transfers
                        for date_in in f3_to_transactions.transfer_in.keys():
                            # If the incoming transfer date is the same than our outgoing transfer date, check amounts
                            if date_in == date_out:
                                # Loop through incoming transfers
                                for transfer_in in f3_to_transactions.transfer_in[date_in]:
                                    # Get the amount
                                    amount_in = transfer_in["transactions"][0]["amount"]
                                    # If incoming transfer amount is the same than outgoing transfer amount,
                                    # it means that we found a corresponding incoming transfer for our outgoing transfer
                                    if amount_in == amount_out:
                                        transfer_out["transactions"][0]["type"] = "transfer"
                                        # We clarify the transfer payload (who's the source and destination)
                                        transfer_out["transactions"][0]["source_id"] = f3_from_transactions.account_id
                                        transfer_out["transactions"][0]["destination_id"] = f3_to_transactions.account_id
                                        # We rename the transaction
                                        transfer_out["transactions"][0]["description"] = "Personal transfer"
                                        # We save the payload to push it later
                                        payloads.append(transfer_out)

        # Check amount of transfers
        if detected_transfers % 2 != 0 or len(payloads) * 2 != detected_transfers:
            f3_cli.logger.log_newline("WARN: Wrong quantity of transfers detected (" + str(detected_transfers) + ") for " + str(len(payloads)) + " payload(s). You must double check your \"transfer-source-transaction-name\" and \"transfer-destination-transaction-name\" because some transfers hadn't been recognized.")

        # Now push each payload
        for payload in payloads:
            res = f3_cli._post(endpoint=_TRANSACTIONS_ENDPOINT, payload=payload)
            if not f3_cli.debug:
                f3_cli.logger.log(".", end='')
            f3_cli.logger.log(str(res), debug=True)




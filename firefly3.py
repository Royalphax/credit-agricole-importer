from creditagricole import CreditAgricoleRegion
from tool import *
import requests
import time
from collections import defaultdict
import copy
import json
from datetime import datetime
from constant import *

_TRANSACTIONS_ENDPOINT = 'api/v1/transactions'
_ACCOUNTS_ENDPOINT = 'api/v1/accounts'
_BUDGETS_ENDPOINT = 'api/v1/budgets'


class GetOrPostException(Exception):
    def __init__(self, message, response_json):
        super().__init__(message)
        self.response_json = response_json

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
        self.headers = None

    def _post(self, endpoint, payload):
        response = requests.post("{}{}".format(self.hostname, endpoint), json=payload, headers=self.headers)
        response_json = response.json()
        if response.status_code != 200:
            raise GetOrPostException("POST-Request to your Firefly3 instance failed. Please double check your personal token.", response_json)            
        return response_json

    def _get(self, endpoint, params=None):
        response = requests.get("{}{}".format(self.hostname, endpoint), params=params, headers=self.headers)
        response_json = response.json()
        if response.status_code != 200:
            raise GetOrPostException("GET-Request to your Firefly3 instance failed. Please double check your personal token.", response_json)
        return response_json

    def validate(self):
        if self.hostname == HOSTNAME_DEFAULT:
            self.logger.log("WARN: The firefly3 instance HOSTNAME is the demo website.")
        if self.token == PERSONAL_TOKEN_DEFAULT:
            self.logger.error("Your firefly3 personal token isn't set.")
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

    def get_budgets(self):
        return self._get(_BUDGETS_ENDPOINT).get("data")

    def create_budget(self, name):
        return self._post(_BUDGETS_ENDPOINT, {"name": name}).get("data")

    def get_accounts(self, account_type = "asset"):
        return self._get(_ACCOUNTS_ENDPOINT, params = {"type": account_type}).get("data")

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


class Firefly3Importer:

    def __len__(self):
        return len(self.withdrawals.keys()) + len(self.deposits.keys())

    def __init__(self, f3_cli, account_id, ca_transactions):
        self.f3_cli = f3_cli
        self.account_id = int(account_id)
        self.withdrawals = {}
        self.deposits = {}
        self.budgets = {}
        self.budgets = {}

        for budget in f3_cli.get_budgets():
            budget_key = budget.get('attributes').get('name')
            self.budgets.update({ 
                budget_key: budget
            })

        for ca_transaction in ca_transactions: 
            f3_cli.logger.log(str(ca_transaction), debug=True)

            f3_transaction = self.ca_to_f3(ca_transaction)
            f3_transaction_type = f3_transaction.get('type')
            f3_transaction_external_id = f3_transaction.get('external_id')
            if f3_transaction_type == 'withdrawal':
                self.withdrawals[f3_transaction_external_id] = f3_transaction
            if f3_transaction_type == 'deposit':
                self.deposits[f3_transaction_external_id] = f3_transaction

            f3_cli.logger.log(str(f3_transaction), debug=True)

    def ca_to_f3(self, ca_transaction):
        transaction_name = ' '.join(ca_transaction["libelleOperation"].strip().split())

        external_id = str(ca_transaction["fitid"]).strip()

        renames = get_key_from_value(self.f3_cli.a_rename_transaction, transaction_name)
        description = renames[0] if len(renames) > 0 else transaction_name

        date = time.mktime(time.strptime(ca_transaction["dateOperation"], '%b %d, %Y, %H:%M:%S %p'))
        date = time.strftime("%Y-%m-%dT%T", time.gmtime(date))

        amount = abs(ca_transaction["montant"])
        currency_code = ca_transaction["idDevise"]

        budgets = get_key_from_value(self.f3_cli.aa_budget, transaction_name)
        budget_id = self.f3_cli.get_budget_id(budgets[0]) if len(budgets) != 0 else None

        categories = get_key_from_value(self.f3_cli.aa_category, transaction_name)        
        category_name = categories[0] if len(categories) != 0 else None

        tags = []
        tags.append(self.remove_unnecessary_spaces(ca_transaction["libelleTypeOperation"]))
        for tag in get_key_from_value(self.f3_cli.aa_tags, transaction_name):
            tags.append(tag)

        notesLines = ["---------- MORE DETAILS ----------"]
        for key in ca_transaction.keys():
            noteLine = str(key) + ": " + str(ca_transaction[key]).strip()
            notesLines.append(noteLine)
        notes = '\n\n'.join(notesLines)

        accounts = get_key_from_value(self.f3_cli.aa_account, transaction_name)

        isWithdrawal = ca_transaction["montant"] < 0
        isDeposit = ca_transaction["montant"] > 0

        type = "withdrawal" if isWithdrawal else "deposit" if isDeposit else None
        subject_name = accounts[0] if len(accounts) > 0 else "Cash account"
        source_id = self.account_id if isWithdrawal else None
        source_name = subject_name if isDeposit else None
        destination_id = self.account_id if isDeposit else None
        destination_name = subject_name if isWithdrawal else None
        internal_reference = self.remove_unnecessary_spaces(ca_transaction["referenceClient"])

        # in some transactions, like "ca_codeTypeOperation == '00'" (VIREMENT EN VOTRE FAVEUR) this could be a nice way to identify the destination name of the transaction
        #subject_name = self.libelleOperation_without_referenceClient(self.remove_unnecessary_spaces(ca_transaction.get('libelleOperation')), internal_reference)

        # not used except if you look into the notes. but isn't that an important field ?!
        #additional_information = self.remove_unnecessary_spaces(ca_transaction["libelleComplementaire"])

        return {
            'internal_reference': internal_reference,
            'description': description,
            'amount': amount,
            'currency_code': currency_code,
            'type': type,
            'source_id': source_id,
            'source_name': source_name,
            'destination_id': destination_id,
            'destination_name': destination_name,
            'budget_id': budget_id,
            'date': date,
            'external_id':external_id,
            'category_name': category_name,
            'tags': tags,
            'notes': notes,    
        }

    @staticmethod
    def remove_unnecessary_spaces(string):
        return ' '.join(string.strip().split())

    @staticmethod
    def libelleOperation_without_referenceClient(libelleOperation, referenceClient):
        # Split the cleaned string by spaces
        splitted = libelleOperation.split()

        # Iterate over the split results and join them by spaces
        for i in range(1, len(splitted) + 1):
            cleaned_libelleOperation = ' '.join(splitted[:i])
            recombined_libelleOperation = f'{cleaned_libelleOperation} {referenceClient}'[:len(libelleOperation)]

            if recombined_libelleOperation == libelleOperation:
                return cleaned_libelleOperation
        return libelleOperation

    @staticmethod
    def extract_transfers(f3_transactions, f3_cli):
        transfers = []
        annulations = []
        withdrawals = {}
        deposits = {}

        for f3_transaction in f3_transactions:
            withdrawals.update(f3_transaction.withdrawals.copy())
            deposits.update(f3_transaction.deposits.copy())

        # searching for transfers
        for withdrawal_fitid, withdrawal in withdrawals.items():
            # the fitid/external_id of transfers always differ by 1
            deposit_fitid = str(int(withdrawal_fitid) + 1)
            deposit = deposits.get(deposit_fitid)

            date = withdrawal.get('date')
            amount = withdrawal.get('amount')
            description = withdrawal.get('description')

            isTransfer = deposit != None and withdrawal.get('source_id') != deposit.get('destination_id')
            # if we found a deposit with the fitid 1 higher than the withdrawal, and source != destination
            if isTransfer:                        
                type = 'transfer'
                category_name = withdrawal.get('category_name')
                currency_code = withdrawal.get('currency_code')
                budget_id = withdrawal.get('budget_id')
                source_id = withdrawal.get('source_id')
                source_name = withdrawal.get('source_name')
                destination_id = deposit.get('destination_id')
                destination_name = deposit.get('destination_name')
                tags = list(set(withdrawal.get('tags', []) + deposit.get('tags', [])))
                internal_reference = withdrawal.get('internal_reference')            
                external_id = f"{withdrawal.get('external_id')}-{deposit.get('external_id')}" # storing here both external_ids so that we can find and delete the source trasactions later on
                notes = ', '.join([withdrawal.get('notes'), deposit.get('notes')])

                f3_cli.logger.log(f"transfer detected => [{date}] '{description}': {amount}")
                transfer = {
                    'description': description,
                    'category_name':category_name,
                    'date': date,
                    'type': type,
                    'amount': amount,
                    'currency_code': currency_code,
                    'budget_id': budget_id,
                    'source_id': source_id,
                    'source_name': source_name,
                    'destination_id': destination_id,
                    'destination_name': destination_name,
                    'tags': tags,
                    'internal_reference': internal_reference,
                    'external_id': external_id,
                    'notes': notes,
                }
                transfers.append(transfer)

            isAnnulation = deposit != None and deposit.get('codeTypeOperation') == "81"
            if isAnnulation:
                f3_cli.logger.log(f"annulation detected => [{date}] '{description}': {amount}")
                annulations.append({
                    'external_id': external_id,
                })

        for transfer in (transfers + annulations):
            for f3_transaction in f3_transactions:
                external_id = transfer.get('external_id')
                fitids = external_id.split('-')
                withdrawal_fitid = fitids[0]
                if withdrawal_fitid in f3_transaction.withdrawals.keys():
                    del f3_transaction.withdrawals[withdrawal_fitid]
                deposit_fitid = fitids[1]
                if deposit_fitid in f3_transaction.deposits.keys():
                    del f3_transaction.deposits[deposit_fitid]

        return transfers

    @staticmethod
    def doImport(f3_importer_list, f3_cli):
        transactions = []

        if f3_cli.auto_detect_transfers:
            transfers = Firefly3Importer.extract_transfers(f3_importer_list, f3_cli)
            transactions.extend(transfers)

        for f3_importer in f3_importer_list:
            transactions.extend(f3_importer.withdrawals.values())
            transactions.extend(f3_importer.deposits.values())

        transactions_len = len(transactions)

        if transactions_len > 0:
            f3_cli.logger.log(f'-> Pushing {transactions_len} transactions to Firefly3 instance.')
            sorted_transactions = sorted(transactions, key=lambda x: x['date'])
            for transaction in sorted_transactions:
                duplicates_count = 0;

                try:
                    print(f"[{transaction.get('date')}] ({transaction.get('external_id')}) {transaction.get('type')}: {transaction.get('amount')} | {transaction.get('description')}")
                    res = f3_cli._post(endpoint=_TRANSACTIONS_ENDPOINT, payload={
                        "error_if_duplicate_hash": "true",
                        "transactions": [transaction]
                    })
                    f3_cli.logger.log(str(res), debug=True)
                except GetOrPostException as e:
                    message = e.response_json.get('message')
                    if not "Duplicate of transaction " in str(message):
                        print(transaction)
                        raise Exception(message)
                    f3_cli.logger.log(f'skipped duplicate_ {transaction}', debug=True)
                    duplicates_count += 1

                if duplicates_count == 1:
                    f3_cli.logger.log('1 duplicate skipped')        
                elif duplicates_count > 1:
                    f3_cli.logger.log(f'{duplicates_count} duplicates skipped')                 
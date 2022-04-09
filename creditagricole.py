from creditagricole_particuliers import Authenticator, Accounts
from constant import *


class CreditAgricoleClient:

    def __init__(self):
        self.region = BANK_REGION_DEFAULT
        self.account_id = BANK_ACCOUNT_ID_DEFAULT
        self.password = BANK_PASSWORD_DEFAULT
        self.enabled_accounts = IMPORT_ACCOUNT_ID_LIST_DEFAULT
        self.session = None

    def validate(self):
        if self.region == BANK_REGION_DEFAULT:
            raise ValueError("Please set your bank account region.")
        if not self.account_id.isdigit() or len(self.account_id) != len(BANK_ACCOUNT_ID_DEFAULT) or self.account_id == BANK_ACCOUNT_ID_DEFAULT:
            raise ValueError("Your bank account ID must be a 11 long digit.")
        if not self.password.isdigit() or len(self.password) != len(BANK_PASSWORD_DEFAULT) or self.password == BANK_PASSWORD_DEFAULT:
            raise ValueError("Your bank password must be a 6 long digit.")
        if self.enabled_accounts == IMPORT_ACCOUNT_ID_LIST_DEFAULT:
            raise ValueError("Please set your account ID list to import.")

    def init_session(self):
        password_list = []
        for i in range(len(self.password)):
            password_list.append(int(self.password[i]))
        self.session = Authenticator(username=self.account_id, password=password_list, region=self.region)

    def get_accounts(self):
        accounts = []
        for account in Accounts(session=self.session):
            if account.numeroCompte in self.enabled_accounts:
                accounts.append(account)
        return accounts

    def get_transactions(self, account_id):
        # search account
        account = Accounts(session=self.session).search(num=account_id)

        operations = account.get_operations()

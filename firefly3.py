import requests

from constant import *

_TRANSACTIONS_ENDPOINT = 'api/v1/transactions'
_ACCOUNTS_ENDPOINT = 'api/v1/accounts'


class Firefly3Client():
    def __init__(self):
        self.token = PERSONAL_TOKEN_DEFAULT
        self.url = URL_DEFAULT
        self.headers = None

    def validate(self):
        if self.url == URL_DEFAULT:
            print("WARN: The firefly3 instance URL is the demo website.")
        if len(self.token) != len(PERSONAL_TOKEN_DEFAULT) or self.token == PERSONAL_TOKEN_DEFAULT:
            raise ValueError("Your firefly3 personal token isn't 980 characters long or isn't set.")

    def init_session(self):
        if self.url[-1] != "/":
            self.url = self.url + "/"
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + self.token,
        }

    def get_accounts(self):
        pass

    def create_account(self):
        pass

    def create_transaction(self):
        self.push("transactions", None)

    def push(self, type, payload):
        payload = {'transactions': [payload]}
        response = requests.post(self.push_url, headers=self.headers, json=payload).json()
        print(response)

class Firefly3Transaction:
    def __init__(self):
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + firefly_token,
        }

    def __len__(self):
        return len(self.list)

    def process(self):
        pass

    def push_transaction(self, payload):
        payload = {'transactions': [payload]}
        response = requests.post(self.push_url, headers=self.headers, json=payload).json()
        print(response)


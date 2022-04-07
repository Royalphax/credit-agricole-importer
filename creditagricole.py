from creditagricole_particuliers import Authenticator


class CreditAgricole:

    def __init__(self):
        self.region = "paris"
        self.account_id = "XXXXXXXXXXX"
        self.password = "XXXXXX"
        self.session = None

    def init_session(self):
        password_list = []
        for i in range(len(self.password)):
            password_list.append(int(self.password[i]))
        self.session = Authenticator(username=self.account_id, password=password_list, region=self.region)

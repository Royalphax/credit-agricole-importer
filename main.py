import configparser, os
from creditagricole import CreditAgricoleClient
from firefly3 import Firefly3Client
from constant import *

if __name__ == '__main__':

    config = configparser.ConfigParser()

    if not os.path.exists(CONFIG_FILE):

        # INIT CONFIG FIRST TIME (CREATE IT)
        config.add_section(SETTINGS_SECTION)
        config.set(SETTINGS_SECTION, IMPORT_TRANSACTIONS_FIELD, IMPORT_TRANSACTIONS_DEFAULT)
        config.set(SETTINGS_SECTION, IMPORT_ACCOUNTS_FIELD, IMPORT_ACCOUNTS_DEFAULT)
        config.set(SETTINGS_SECTION, IMPORT_ACCOUNT_ID_LIST_FIELD, IMPORT_ACCOUNT_ID_LIST_DEFAULT)
        config.add_section(CREDENTIALS_SECTION)
        config.set(CREDENTIALS_SECTION, BANK_REGION_FIELD, BANK_REGION_DEFAULT)
        config.set(CREDENTIALS_SECTION, BANK_ACCOUNT_ID_FIELD, BANK_ACCOUNT_ID_DEFAULT)
        config.set(CREDENTIALS_SECTION, BANK_PASSWORD_FIELD, BANK_PASSWORD_DEFAULT)
        config.add_section(FIREFLY3_SECTION)
        config.set(FIREFLY3_SECTION, URL_FIELD, URL_DEFAULT)
        config.set(FIREFLY3_SECTION, PERSONAL_TOKEN_FIELD, PERSONAL_TOKEN_DEFAULT)

        with open(CONFIG_FILE, 'w') as file:
            config.write(file)
            file.flush()
            file.close()

        print("Config file '" + CONFIG_FILE + "' created ! Please fill it and start this script again.")

    else:

        # INIT CONFIG
        config.read(CONFIG_FILE)
        settings_section = config[SETTINGS_SECTION]
        user_account_section = config[CREDENTIALS_SECTION]
        firefly3_section = config[FIREFLY3_SECTION]

        # INIT CREDIT AGRICOLE
        ca_cli = CreditAgricoleClient()
        ca_cli.region = str(user_account_section.get(BANK_REGION_FIELD, BANK_REGION_DEFAULT))
        ca_cli.account_id = str(user_account_section.get(BANK_ACCOUNT_ID_FIELD, BANK_ACCOUNT_ID_DEFAULT))
        ca_cli.password = str(user_account_section.get(BANK_PASSWORD_FIELD, BANK_PASSWORD_DEFAULT))
        ca_cli.enabled_accounts = str(user_account_section.get(IMPORT_ACCOUNT_ID_LIST_FIELD, IMPORT_ACCOUNT_ID_LIST_DEFAULT)).split(",")
        ca_cli.validate()
        ca_cli.init_session()

        # INIT FIREFLY3
        f3_cli = Firefly3Client()
        f3_cli.url = str(firefly3_section.get(URL_FIELD, URL_DEFAULT))
        f3_cli.token = str(firefly3_section.get(PERSONAL_TOKEN_FIELD, PERSONAL_TOKEN_DEFAULT))
        f3_cli.validate()
        f3_cli.init_session()

        # PROCESS 1 : IMPORT ACCOUNTS
        if bool(settings_section.get(IMPORT_ACCOUNTS_FIELD, IMPORT_ACCOUNTS_DEFAULT)):
            print("Importing new accounts ... ")
            for account in ca_cli.get_accounts():
                # Tester si le compte existe du coté de firefly
                # Si oui : ne rien faire
                # Si non : le créer
                pass


            # Loop through accounts on firefly and on credit agricole, add missing ones (use compte id)

        # PROCESS 2 : IMPORT TRANSACTIONS
        if bool(settings_section.get(IMPORT_TRANSACTIONS_FIELD, IMPORT_TRANSACTIONS_DEFAULT)):
            print("Importing new transactions ... ")
            # Loop through accounts on firefly and on credit agricole, add missing ones (use compte id)

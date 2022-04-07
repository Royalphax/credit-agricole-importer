import configparser, os
from creditagricole import CreditAgricole
from firefly3 import Firefly3
from constant import *

if __name__ == '__main__':

    config = configparser.ConfigParser()

    if not os.path.exists(CONFIG_FILE):

        # INIT CONFIG FIRST TIME (CREATE IT)
        config.add_section(SETTINGS_SECTION)
        config.set(SETTINGS_SECTION, IMPORT_ACCOUNTS_FIELD, "False")
        config.set(SETTINGS_SECTION, IMPORT_ACCOUNT_IDS_LIST_FIELD, "XXXXXXXXXXX,XXXXXXXXXXX,XXXXXXXXXXX")
        config.add_section(CREDENTIALS_SECTION)
        config.set(CREDENTIALS_SECTION, BANK_REGION_FIELD, "paris")
        config.set(CREDENTIALS_SECTION, BANK_ACCOUNT_ID_FIELD, "XXXXXXXXXXX")
        config.set(CREDENTIALS_SECTION, BANK_PASSWORD_FIELD, "XXXXXX")
        config.add_section(FIREFLY3_SECTION)
        config.set(FIREFLY3_SECTION, OAUTH2_TOKEN_FIELD, "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")

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
        credit_agricole = CreditAgricole()
        credit_agricole.region = str(user_account_section.get(BANK_REGION_FIELD, "paris"))
        credit_agricole.account_id = str(user_account_section.get(BANK_ACCOUNT_ID_FIELD, "XXXXXXXXXXX"))
        credit_agricole.password = str(user_account_section.get(BANK_PASSWORD_FIELD, "XXXXXX"))

        if not credit_agricole.account_id.isdigit() or not credit_agricole.password.isdigit():
            raise ValueError("Your account ID or password must be a digit.")

        credit_agricole.init_session()

        # INIT FIREFLY3
        firefly_3 = Firefly3()
        firefly_3.token = str(firefly3_section.get(OAUTH2_TOKEN_FIELD, "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"))

        if len(firefly_3.token) is not 40 or firefly_3.token is "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX":
            raise ValueError("Your OAUTH2 token isn't 40 characters long or not set.")

        firefly_3.init()

        # PROCESS 1 : IMPORT ACCOUNTS

        if settings_section.get(IMPORT_ACCOUNTS_FIELD, "True") == "True":
            print("Importing new accounts ... ")
            # Loop through accounts on firefly and on credit agricole, add missing ones (use compte id)

        # PROCESS 2 : IMPORT TRANSACTIONS

import configparser
import os

from constant import *
from creditagricole import CreditAgricoleClient
from firefly3 import Firefly3Client, Firefly3Transactions

if __name__ == '__main__':

    config = configparser.ConfigParser()

    # Check if config file exists
    if not os.path.exists(CONFIG_FILE):

        # First time : init config file
        config.add_section(SETTINGS_SECTION)
        config.set(SETTINGS_SECTION, IMPORT_ACCOUNT_ID_LIST_FIELD, IMPORT_ACCOUNT_ID_LIST_DEFAULT)
        config.set(SETTINGS_SECTION, GET_TRANSACTIONS_PERIOD_DAYS_FIELD, GET_TRANSACTIONS_PERIOD_DAYS_DEFAULT)
        config.set(SETTINGS_SECTION, MAX_TRANSACTIONS_PER_GET_FIELD, MAX_TRANSACTIONS_PER_GET_DEFAULT)
        config.add_section(CREDENTIALS_SECTION)
        config.set(CREDENTIALS_SECTION, BANK_REGION_FIELD, BANK_REGION_DEFAULT)
        config.set(CREDENTIALS_SECTION, BANK_ACCOUNT_ID_FIELD, BANK_ACCOUNT_ID_DEFAULT)
        config.set(CREDENTIALS_SECTION, BANK_PASSWORD_FIELD, BANK_PASSWORD_DEFAULT)
        config.add_section(FIREFLY3_SECTION)
        config.set(FIREFLY3_SECTION, ACCOUNTS_NAME_FORMAT_FIELD, ACCOUNTS_NAME_FORMAT_DEFAULT)
        config.set(FIREFLY3_SECTION, HOSTNAME_FIELD, HOSTNAME_DEFAULT)
        config.set(FIREFLY3_SECTION, PERSONAL_TOKEN_FIELD, PERSONAL_TOKEN_DEFAULT)
        config.add_section(A_RENAME_TRANSACTION_SECTION)
        config.add_section(AA_BUDGET_SECTION)
        config.add_section(AA_CATEGORY_SECTION)
        config.add_section(AA_ACCOUNT_SECTION)
        config.add_section(AA_TAGS_SECTION)

        with open(CONFIG_FILE, 'w') as file:
            config.write(file)
            file.flush()
            file.close()

        print("Config file '" + CONFIG_FILE + "' created ! Please fill it and start this script again.")
        print("Wiki page to help you : https://github.com/Royalphax/credit-agricole-importer/wiki/Config-file")

    else:

        # Read config and init sections
        config.read(CONFIG_FILE)
        settings_section = config[SETTINGS_SECTION]
        user_account_section = config[CREDENTIALS_SECTION]
        firefly3_section = config[FIREFLY3_SECTION]
        a_rename_transaction_section = config[A_RENAME_TRANSACTION_SECTION]
        aa_budget_section = config[AA_BUDGET_SECTION]
        aa_category_section = config[AA_CATEGORY_SECTION]
        aa_account_section = config[AA_ACCOUNT_SECTION]
        aa_tags_section = config[AA_TAGS_SECTION]

        # Init CreditAgricole instance
        ca_cli = CreditAgricoleClient()
        ca_cli.region = str(user_account_section.get(BANK_REGION_FIELD, BANK_REGION_DEFAULT))
        ca_cli.account_id = str(user_account_section.get(BANK_ACCOUNT_ID_FIELD, BANK_ACCOUNT_ID_DEFAULT))
        ca_cli.password = str(user_account_section.get(BANK_PASSWORD_FIELD, BANK_PASSWORD_DEFAULT))
        ca_cli.enabled_accounts = str(settings_section.get(IMPORT_ACCOUNT_ID_LIST_FIELD, IMPORT_ACCOUNT_ID_LIST_DEFAULT))
        ca_cli.get_transactions_period = str(settings_section.get(GET_TRANSACTIONS_PERIOD_DAYS_FIELD, GET_TRANSACTIONS_PERIOD_DAYS_DEFAULT))
        ca_cli.max_transactions = str(settings_section.get(MAX_TRANSACTIONS_PER_GET_FIELD, MAX_TRANSACTIONS_PER_GET_DEFAULT))
        ca_cli.validate()
        ca_cli.init_session()

        # Init Firefly3 instance
        f3_cli = Firefly3Client()
        f3_cli.name_format = str(firefly3_section.get(ACCOUNTS_NAME_FORMAT_FIELD, ACCOUNTS_NAME_FORMAT_DEFAULT))
        f3_cli.hostname = str(firefly3_section.get(HOSTNAME_FIELD, HOSTNAME_DEFAULT))
        f3_cli.token = str(firefly3_section.get(PERSONAL_TOKEN_FIELD, PERSONAL_TOKEN_DEFAULT))
        f3_cli.init_auto_assign_values(a_rename_transaction_section, aa_budget_section, aa_category_section, aa_account_section, aa_tags_section)
        f3_cli.validate()

        # Start main process
        print("Process started")

        # Get Firefly3 accounts numbers
        f3_accounts = f3_cli.get_accounts(account_type="asset")
        f3_accounts_number = [account.get("attributes").get("account_number") for account in f3_accounts]

        # Loop through existing CreditAgricole accounts declared in config file
        for account in ca_cli.get_accounts():

            name = account.account['libelleProduit']
            print("-> '" + name + "' account n°" + account.numeroCompte)

            # Check if CreditAgricole account is already on Firefly3
            if account.numeroCompte not in f3_accounts_number:

                print("  -> Creating account ... ", end='')
                if account.grandeFamilleCode == "7":
                    # 7 is generally for investment accounts
                    print("Not an asset account!")
                    continue

                account_id = f3_cli.create_account(name, ca_cli.region, account.numeroCompte, account.grandeFamilleCode).get("data")["id"]
                print("Done!")
            else:
                account_id = f3_cli.get_account_id(account.numeroCompte)

            print("  -> Retrieving transactions ", end='')

            # Init a new set of transactions for Firefly3
            transactions = Firefly3Transactions(f3_cli)

            # Loop through CreditAgricole transactions
            for ca_transaction in ca_cli.get_transactions(account.numeroCompte):
                transactions.add_transaction(ca_transaction, account_id)
                print(".", end='')

            print(" " + str(len(transactions)) + " found!")

            if len(transactions) > 0:
                print("  -> Pushing data to Firefly3 instance ", end='')
                # Push transactions to Firefly3
                transactions.post()
                print(" Done!")

import configparser
import os

from constant import *
from creditagricole import CreditAgricoleClient
from firefly3 import Firefly3Client, Firefly3Transactions
from collections import defaultdict
from logger import Logger

if __name__ == '__main__':

    # Init logger
    logger = Logger()

    # Init config parser
    config = configparser.ConfigParser()

    # Check if config file exists
    if not os.path.exists(CONFIG_FILE):

        # First time : init config file
        config.add_section(SETTINGS_SECTION)
        config.set(SETTINGS_SECTION, SAVE_LOGS_FIELD, SAVE_LOGS_DEFAULT)
        config.set(SETTINGS_SECTION, MAX_LOG_FILES_FIELD, MAX_LOG_FILES_DEFAULT)
        config.set(SETTINGS_SECTION, DEBUG_FIELD, DEBUG_DEFAULT)
        config.set(SETTINGS_SECTION, AUTO_DETECT_TRANSFERS_FIELD, AUTO_DETECT_TRANSFERS_DEFAULT)

        config.add_section(CREDIT_AGRICOLE_SECTION)
        config.set(CREDIT_AGRICOLE_SECTION, BANK_DEPARTMENT_FIELD, BANK_DEPARTMENT_DEFAULT)
        config.set(CREDIT_AGRICOLE_SECTION, BANK_ACCOUNT_ID_FIELD, BANK_ACCOUNT_ID_DEFAULT)
        config.set(CREDIT_AGRICOLE_SECTION, BANK_PASSWORD_FIELD, BANK_PASSWORD_DEFAULT)
        config.set(CREDIT_AGRICOLE_SECTION, IMPORT_ACCOUNT_ID_LIST_FIELD, IMPORT_ACCOUNT_ID_LIST_DEFAULT)
        config.set(CREDIT_AGRICOLE_SECTION, GET_TRANSACTIONS_PERIOD_DAYS_FIELD, GET_TRANSACTIONS_PERIOD_DAYS_DEFAULT)
        config.set(CREDIT_AGRICOLE_SECTION, MAX_TRANSACTIONS_PER_GET_FIELD, MAX_TRANSACTIONS_PER_GET_DEFAULT)
        config.set(CREDIT_AGRICOLE_SECTION, TRANSFER_SOURCE_TRANSACTION_NAME_FIELD, TRANSFER_SOURCE_TRANSACTION_NAME_DEFAULT)
        config.set(CREDIT_AGRICOLE_SECTION, TRANSFER_DESTINATION_TRANSACTION_NAME_FIELD, TRANSFER_DESTINATION_TRANSACTION_NAME_DEFAULT)

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

        logger.log("Config file '" + CONFIG_FILE + "' created ! Please fill it and start this script again.")
        logger.log("Wiki page to help you : https://github.com/Royalphax/credit-agricole-importer/wiki/Config-file")

    else:

        # Read config and init sections
        config.read(CONFIG_FILE)
        settings_section = config[SETTINGS_SECTION]
        credit_agricole_section = config[CREDIT_AGRICOLE_SECTION]
        firefly3_section = config[FIREFLY3_SECTION]
        a_rename_transaction_section = config[A_RENAME_TRANSACTION_SECTION]
        aa_budget_section = config[AA_BUDGET_SECTION]
        aa_category_section = config[AA_CATEGORY_SECTION]
        aa_account_section = config[AA_ACCOUNT_SECTION]
        aa_tags_section = config[AA_TAGS_SECTION]
        
        # Init global settings        
        debug = settings_section.get(DEBUG_FIELD, DEBUG_DEFAULT) == "True"
        logger.debug = debug
        save_logs = settings_section.get(SAVE_LOGS_FIELD, SAVE_LOGS_DEFAULT) == "True"
        max_logs = int(settings_section.get(MAX_LOG_FILES_FIELD, MAX_LOG_FILES_DEFAULT))

        # Init CreditAgricole instance
        ca_cli = CreditAgricoleClient(logger)
        ca_cli.department = credit_agricole_section.get(BANK_DEPARTMENT_FIELD, BANK_DEPARTMENT_DEFAULT)
        ca_cli.account_id = credit_agricole_section.get(BANK_ACCOUNT_ID_FIELD, BANK_ACCOUNT_ID_DEFAULT)
        ca_cli.password = credit_agricole_section.get(BANK_PASSWORD_FIELD, BANK_PASSWORD_DEFAULT)
        ca_cli.enabled_accounts = credit_agricole_section.get(IMPORT_ACCOUNT_ID_LIST_FIELD, IMPORT_ACCOUNT_ID_LIST_DEFAULT)
        ca_cli.get_transactions_period = credit_agricole_section.get(GET_TRANSACTIONS_PERIOD_DAYS_FIELD, GET_TRANSACTIONS_PERIOD_DAYS_DEFAULT)
        ca_cli.max_transactions = credit_agricole_section.get(MAX_TRANSACTIONS_PER_GET_FIELD, MAX_TRANSACTIONS_PER_GET_DEFAULT)
        ca_cli.validate()
        ca_cli.init_session()

        # Init Firefly3 instance
        f3_cli = Firefly3Client(logger, debug)
        f3_cli.name_format = firefly3_section.get(ACCOUNTS_NAME_FORMAT_FIELD, ACCOUNTS_NAME_FORMAT_DEFAULT)
        f3_cli.hostname = firefly3_section.get(HOSTNAME_FIELD, HOSTNAME_DEFAULT)
        f3_cli.token = firefly3_section.get(PERSONAL_TOKEN_FIELD, PERSONAL_TOKEN_DEFAULT)
        f3_cli.auto_detect_transfers = settings_section.get(AUTO_DETECT_TRANSFERS_FIELD, AUTO_DETECT_TRANSFERS_DEFAULT) == "True"
        f3_cli.transfer_source_transaction = credit_agricole_section.get(TRANSFER_SOURCE_TRANSACTION_NAME_FIELD, TRANSFER_SOURCE_TRANSACTION_NAME_DEFAULT).strip().split(",")
        f3_cli.transfer_destination_transaction = credit_agricole_section.get(TRANSFER_DESTINATION_TRANSACTION_NAME_FIELD, TRANSFER_DESTINATION_TRANSACTION_NAME_DEFAULT).strip().split(",")
        f3_cli.init_auto_assign_values(a_rename_transaction_section, aa_budget_section, aa_category_section, aa_account_section, aa_tags_section)
        f3_cli.validate()

        # Start main process
        logger.log("Process started, debug=" + str(debug) + ", save_logs=" + str(save_logs))

        # Get Firefly3 accounts numbers
        f3_accounts = f3_cli.get_accounts(account_type="asset")
        f3_accounts_number = [account.get("attributes").get("account_number") for account in f3_accounts]

        # Keep track of transactions for each account
        account_transactions = []

        accounts = ca_cli.get_accounts()
        account_name_counts = defaultdict(int)

        # Detect duplicate account names
        for account in accounts:
            account_name_counts[account.account['libelleProduit']] += 1

        # Loop through existing CreditAgricole accounts declared in config file
        for account in accounts:
            if account_name_counts[account.account['libelleProduit']] > 1:
                name = f"{account.account['libelleProduit']} [{account.numeroCompte}]"
            else:
                name = account.account['libelleProduit']

            logger.log("-> '" + name + "' account n°" + account.numeroCompte)

            # Check if CreditAgricole account is already on Firefly3
            if account.numeroCompte not in f3_accounts_number:

                logger.log("  -> Creating account ... ", end='')
                if account.grandeFamilleCode == "7":
                    # 7 is generally for investment accounts
                    logger.log("Not an asset account!")
                    continue

                account_id = f3_cli.create_account(name, ca_cli.department, account.numeroCompte, account.grandeFamilleCode).get("data")["id"]
                logger.log("Done!")
            else:
                account_id = f3_cli.get_account_id(account.numeroCompte)

            logger.log("  -> Retrieving transactions ", end=('\n\r' if debug else ''))

            # Init a new set of transactions for Firefly3
            transactions = Firefly3Transactions(f3_cli, account_id)

            # Loop through CreditAgricole transactions
            for ca_transaction in ca_cli.get_transactions(account.numeroCompte):
                transactions.add_transaction(ca_transaction)
                if not debug:
                    logger.log(".", end='')

            logger.log(" " + str(len(transactions)) + " found!")

            if len(transactions) > 0:
                logger.log("  -> Pushing data to Firefly3 instance ", end=('\n\r' if debug else ''))
                # Push transactions to Firefly3
                transactions.post()
                logger.log(" Done!")

            account_transactions.append(transactions)

        if f3_cli.auto_detect_transfers:
            logger.log("-> Pushing transfers to Firefly3 instance ", end=('\n\r' if debug else ''))
            Firefly3Transactions.post_transfers(account_transactions, f3_cli)
            logger.log(" Done!")

        if save_logs:
            logger.write_log(max_logs)


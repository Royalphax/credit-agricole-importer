import configparser
import os
import time

import tool
from constant import *
from creditagricole import CreditAgricoleClient
from firefly3 import Firefly3Client, Firefly3Importer
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
        f3_cli.init_auto_assign_values(a_rename_transaction_section, aa_budget_section, aa_category_section, aa_account_section, aa_tags_section)
        f3_cli.validate()

        # Start main process and timer
        start_time = time.time()
        logger.log("Process started, debug=" + str(debug) + ", save_logs=" + str(save_logs))

        # Get Firefly3 accounts by number
        f3_account_dict = {}
        for f3_account in f3_cli.get_accounts():
            account_key = f3_account.get('attributes').get('account_number')
            f3_account_dict.update({account_key: f3_account})

        # Get Credit-Agricole accounts and Detect duplicate account names
        ca_account_dict = {}
        account_name_counts = defaultdict(int)
        for ca_account in ca_cli.get_accounts():
            account_key = ca_account.account.get('libelleProduit')
            ca_numeroCompte = ca_account.numeroCompte
            account_name_counts[account_key] += 1
            ca_account_dict.update({ca_numeroCompte: ca_account})

        f3_importer_list = []
        # Loop through existing CreditAgricole accounts declared in config file
        for ca_numeroCompte, ca_account in ca_account_dict.items():
            account_key = ca_account.account.get('libelleProduit')
            if account_name_counts[account_key] > 1:
                name = f"{account_key} [{ca_numeroCompte}]"
            else:
                name = account_key

            logger.log(f"-> '{name}' account n°{ca_numeroCompte}")

            # Check if CreditAgricole account is already on Firefly3
            if ca_numeroCompte in f3_account_dict.keys():
                f3_account = f3_account_dict.get(ca_numeroCompte)
            else:
                logger.log("  -> Creating account ... ", end='')
                if ca_account.grandeFamilleCode == "7":  # 7 is generally for investment accounts
                    logger.log("Not an asset account!")
                    continue

                f3_account = f3_cli.create_account(name, ca_cli.region_id, ca_numeroCompte, ca_account.grandeFamilleCode).get('data')
                f3_account_dict.update({ca_numeroCompte: f3_account})
                logger.log("OK")
            f3_account_id = f3_account.get('id')

            logger.log("  -> Retrieving transactions ... ", end=('\n\r' if debug else ''))
            ca_transactions = ca_cli.get_transactions(ca_numeroCompte)

            # Init a new set of transactions for Firefly3
            f3_importer = Firefly3Importer(f3_cli, f3_account_id, ca_transactions)
            f3_importer_list.append(f3_importer)

            logger.log(str(len(f3_importer)) + " found!")

        Firefly3Importer.do_import(f3_importer_list, f3_cli)

        end_time = time.time()
        logger.log(f"Process ended, time elapsed: {tool.convert_time((end_time - start_time))}")

        if save_logs:
            logger.write_log(max_logs)


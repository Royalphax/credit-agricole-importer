![python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) 
![GitHub release (latest by date)](https://img.shields.io/github/v/release/royalphax/credit-agricole-importer?color=brightgreen)
![GitHub Repo stars](https://img.shields.io/github/stars/royalphax/credit-agricole-importer?color=yellow)
![GitHub issues](https://img.shields.io/github/issues/royalphax/credit-agricole-importer?color=yellow)

# Credit Agricole Importer for FireflyIII

Automatic import of [Credit Agricole](https://www.credit-agricole.fr/) accounts and transactions into [FireflyIII](https://github.com/firefly-iii/firefly-iii) personal finance manager, 
made with use of [python-creditagricole-particuliers](https://github.com/dmachard/python-creditagricole-particuliers).

# ⚠️ Important notice 10.24.2025
This project originally relied heavily on the [creditagricole-particuliers](https://files.pythonhosted.org/packages/3c/f1/6c2cd1be9ee3dcf90425239ad93ebca6be3a80b8c1bfbd9439a642a4a5a6/creditagricole_particuliers-0.14.3.tar.gz) library, which has since been voluntarily removed by its author for legal reasons, as they did not wish to be associated with any use that could potentially conflict with French law, a position we fully understand and respect. This event serves as a sobering reminder that our money does not truly belong to us and that open banking remains a distant promise. What began as an experiment in transparency and empowerment ultimately revealed the structural limits of both. I want to express my deep gratitude to all contributors who supported and believed in this project.

## Features
- Auto import choosen accounts
- Auto import transactions from customizable period
- Limit number of transactions to import
- Auto assign budget, category, tags, expense/revenue account on transactions depending on their description<b>*</b>
  - And even auto rename them!<b>*</b>

<b>*</b>_Although these functionalities are available in the FireflyIII dashboard with [automated rules](https://docs.firefly-iii.org/how-to/firefly-iii/features/rules/), they have been integrated into credit-agricole-importer. This integration allows for the execution of these actions directly through the application, bypassing the need for the [FireflyIII](https://github.com/firefly-iii/firefly-iii) instance._

## How to install

### Install requirements
* Stable and working release :
```
cd /path/you/want
wget https://github.com/Royalphax/credit-agricole-importer/archive/refs/tags/v0.3.1.zip
unzip v0.3.1.zip
cd credit-agricole-importer-0.3.1
pip install -r requirements.txt
```
* or Latest version of the code :
```
cd /path/you/want
git clone https://github.com/Royalphax/credit-agricole-importer.git
cd credit-agricole-importer
pip install -r requirements.txt
```
### Usage
```
python main.py
```

During the first run it will automatically create the ```config.ini``` file. To help you to fill it, [here is a Wiki Page](https://github.com/Royalphax/credit-agricole-importer/wiki/Config-file).

After you successfully filled the config file, each time you run ```main.py```, it will import your transactions.

### Auto run this script

To automatically import your transactions on a daily, monthly or weekly basis, I recommend using `crontab`. [Here is an example of a tutorial](https://www.tutorialspoint.com/unix_commands/crontab.htm).

## FAQ

### How can I get my FireflyIII `personal-token` ?

Use [Personal Access Token](https://docs.firefly-iii.org/how-to/firefly-iii/features/api/#personal-access-token_1) in your FireflyIII instance Profile menu.

### Are my Credit Agricole credentials safe ?

When it comes to storing your credentials in the ```config.ini``` file, it's crucial to ensure that this file is not accessible from public addresses. You should make every effort to secure your host machine as effectively as possible. **However, please note that I cannot be held responsible if someone manages to steal your credentials.** 

If any system security experts happen to come across this, please don't hesitate to initiate a discussion with me on how we can enhance our storage methods. Your insights and expertise would be greatly appreciated.

### Can anybody contribute ?

Certainly! If you have any improvement ideas or wish to implement new features yourself, please don't hesitate to do so. I'm open to pull requests, but I do take a thorough and meticulous approach when reviewing them before merging. **Your contributions are highly appreciated!** 😃

## Donate ☕

In the spirit of collaboration, this project thrives thanks to the dedicated efforts of its contributors. I encourage you to explore their profiles and acknowledge their valuable contributions. However, if you'd like to show your appreciation with a small token of support, you can buy me a coffee through the following link  [here](https://www.paypal.com/donate/?hosted_button_id=JK6FX89RB8K5Y).

# Credit Agricole Importer for FireflyIII

Automatic import of Credit Agricole accounts and transactions into FireflyIII personal finance manager, 
made with use of [python-creditagricole-particuliers](https://github.com/dmachard/python-creditagricole-particuliers).

## Features
- Auto import choosen accounts
- Auto import transactions from customizable period
- Limit number of transactions to import
- Auto assign budget, category, tags, expense/revenue account on transactions depending on their description*
  - And even auto rename them!*

_*These features are already features of FireflyIII thanks to [automated rules](https://docs.firefly-iii.org/firefly-iii/pages-and-features/rules/). I also implemented them to be quickly able to create my rules directly in the config file._

## How to install

### Install requirements
```
cd /path/you/want
git clone https://github.com/Royalphax/credit-agricole-importer.git
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

Use [Personal Access Token](https://docs.firefly-iii.org/api/api) in your FireflyIII instance Profile menu.

### Are my Credit Agricole credentials safe ?

As far as your credentials are stored in the ```config.ini``` file, you must be sure that this file is not accessible from public adresses. You may secure your host machine as best as you can. **In any case, I'm not responsible if someone stole your credentials.** And if any system security expert go through here, feel free to open a discussion with me if you have any idea to improve how credentials are stored.

### Can anybody contribute ?

Of course yes, If you have any improvement ideas, or you want to implement new features by yourself, don't hesitate. I'm also very open to pull requests 😃

## Donate ☕

If you found this project useful, you can thank me by buying me a coffee [here](https://www.paypal.com/donate/?hosted_button_id=JK6FX89RB8K5Y). Enter your email address and I will send you a picture of the coffee you bought from me!

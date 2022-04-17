# Credit Agricole Importer for FireflyIII

Automatic import of Credit Agricole accounts and transactions into FireflyIII personal finance manager, 
made with use of [python-creditagricole-particuliers](https://github.com/dmachard/python-creditagricole-particuliers).

## Features
- Auto import choosen accounts
- Auto import transactions from customizable period
- Limit number of transactions to import
- Auto assign budget, category, tags, expense/revenue account on transactions depending on their description*
  - And even auto rename them!*

*These features are already features of FireflyIII thanks to [automated rules](https://docs.firefly-iii.org/firefly-iii/pages-and-features/rules/). I also implemented them to be quickly able to create my rules directly in the config file.

## How to install

### Install requirements
```pip install -r requirements.txt```

### Usage
```python main.py```

During the first run it will automatically create the ```config.ini``` file. To help you to fill it, [here is a Wiki Page](https://github.com/Royalphax/credit-agricole-importer/wiki/Config-file).

After you successfully filled the config file, each time you run ```main.py```, it will import your transactions.

### Getting your FireflyIII token

Use [Personal Access Token](https://docs.firefly-iii.org/api/api) in your FireflyIII instance Profile menu.

## FAQ

### Are my Credit Agricole credentials safe ?

As far as your credentials are stored in the ```config.ini``` file, you must be sure that this file is not accessible from public adresses. You may secure your host machine as best as you can. **In any case, I'm not responsible if someone stole your credentials.** And if any system security expert go through here, feel free to open a discussion with me if you have any idea to improve how credentials are stored.

### Can anybody contribute ?

Of course yes, If you have any improvement ideas, or you want to implement new features by yourself, don't hesitate. I'm very open to pull requests :)

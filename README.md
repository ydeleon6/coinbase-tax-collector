# coinbase-tax-collector
Looks at your Coinbase transactions csv file and finds your taxable events.

## Setup
Install the dependencies in the requirements.txt file using pip. Run the below command from your projects root directory.
```sh
$ > pip install -r requirements.txt
```

## How it works

Pass the file path to your coinubase csv as the first argument.
```sh
$ > python coinbase-tax-collector.py ./AllCoinbaseTransactions.csv
```

# Coinbase Tax Collector
Looks at your Coinbase transactions csv file and finds all your taxable events.

## Setup
This project was developed using Python 3.10.

Install the dependencies in the requirements.txt file using `pip`. Run the below command from your projects root directory.
```sh
$ > pip install -r requirements.txt
```

## How it works

Pass the file path to your coinubase csv as the first argument and the cost method as the second argument.
Your choices for cost method are either LIFO or FIFO.

```sh
$ > python coinbase-tax-collector.py ./capital-gains-test.csv LIFO
```

The included test csv matches a couple examples described here
* https://coinledger.io/blog/cryptocurrency-tax-calculations-fifo-and-lifo-costing-methods-explained
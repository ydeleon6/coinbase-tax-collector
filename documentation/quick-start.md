# Quickstart 

Coinbase Tax Collector is a Python script that reads your Coinbase transaction history CSV file, identifies all taxable transactions, and calculates your capital gains or losses. This quickstart will help you use Coinbase Tax Collector to get the information you need to complete Form 1099-B when filing your taxes.

## Prerequisites

Coinbase Tax Collector requires the following:

* Python version 3.10 or newer
* Dependencies from the [requirements.txt file](https://github.com/ydeleon6/coinbase-tax-collector/blob/main/requirements.txt)

See Installation for details.

## Instructions

### 1. Install all prerequisites.

See Installation for more details.

### 2. Run the Coinbase Tax Collector script.

Copy and paste the code below, passing the file path to your Coinbase CSV as the first argument.

```sh
$ > python coinbase-tax-collector.py <file path of your CSV file>
```

### 3.  Note your capital gain or loss value in the output CSV.

Review the output CSV for the calculated capital gain or loss value.
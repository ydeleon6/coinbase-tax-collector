# Quickstart for macOS

Coinbase Tax Collector is a Python script that reads your Coinbase transaction history report CSV file, identifies all taxable transactions, and calculates your capital gains or losses. If you are a macOS user, this quickstart will help you use Coinbase Tax Collector to get the information you need to complete Form 1099-B when filing your taxes.

## Prerequisites

Coinbase Tax Collector requires the following:

* Python version 3.10 or newer
* Dependencies from the [requirements.txt file](https://github.com/ydeleon6/coinbase-tax-collector/blob/main/requirements.txt)

See [Installation](https://github.com/mdoming10/coinbase-tax-collector/blob/main/documentation/installation.md) for more details.

## Instructions

### 1. Install all [prerequisites](https://github.com/mdoming10/coinbase-tax-collector/blob/main/documentation/installation.md).

### 2. Download your Coinbase transaction history report CSV.

See [this article](https://help.coinbase.com/en/commerce/managing-account/transaction-reporting#download-reports) for step-by-step instructions on downloading your Coinbase CSV.

Take note of the file path of your Coinbase CSV.

### 2. Run the Coinbase Tax Collector script.

Copy and paste the code below into the terminal:

```sh
$ > python3 coinbase-tax-collector.py <file path of your CSV file>
```

### 3.  Note your capital gain or loss value in the output CSV.

Coinbase Tax Collector generates a CSV and provides you with the total calculated capital gain or loss value.


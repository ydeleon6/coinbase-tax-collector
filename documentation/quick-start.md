# Quickstart for macOS

Coinbase Tax Collector is a Python script that reads your Coinbase transaction history report CSV file, identifies all taxable transactions, and calculates your capital gains or losses. If you are a macOS user, this quickstart will help you use Coinbase Tax Collector to get the information you need to complete Form 1099-B when filing your taxes.

## Prerequisites

Coinbase Tax Collector requires the following:

* Python version 3.10 or newer
* Dependencies from the [requirements.txt file](https://github.com/ydeleon6/coinbase-tax-collector/blob/main/requirements.txt)

See [Installation](https://github.com/mdoming10/coinbase-tax-collector/blob/main/documentation/installation.md) for more details.

## Instructions

1. Install all [prerequisites](https://github.com/mdoming10/coinbase-tax-collector/blob/main/documentation/installation.md).

2. Download your Coinbase transaction history report CSV.

    a. Download your Coinbase CSV. See [this article](https://help.coinbase.com/en/commerce/managing-account/transaction-reporting#download-reports) for step-by-step instructions on downloading your Coinbase CSV.

    b. Take note of the file path of your Coinbase CSV.

3. Run the Coinbase Tax Collector script.

    a. Copy and paste the code below into the terminal:

    ```sh
    $ > python3 coinbase-tax-collector.py <file path of your CSV file>
    ```

    b. After running the code above, Coinbase Tax Collector will produce a new CSV file.

4.  Review your capital gain or loss value in the output CSV.

    a. Open the new output CSV file.

    b. Look at [location in spreadsheet?] to review the total caculated capital gain or loss value.


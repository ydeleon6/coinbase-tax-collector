# Quickstart for macOS

Coinbase Tax Collector (CTC) is a Python script that reads your Coinbase transaction history report CSV file, identifies all taxable transactions, and calculates your capital gains or losses. It allows you to select from among two accounting methods for calculating your tax responsiblity: Last-In, First-Out (LIFO) or First-In, First-Out (FIFO).

If you are a macOS user, this quickstart will help you use CTC to get the information you need to complete Form 1099-B when filing your taxes.

## Prerequisites

CTC requires the following:

* Python version 3.10 or newer
* Dependencies from the [requirements.txt file](https://github.com/ydeleon6/coinbase-tax-collector/blob/main/requirements.txt)

See [Installation](https://github.com/mdoming10/coinbase-tax-collector/blob/main/documentation/installation.md) for more details.

## Instructions

1. Install all [prerequisites](https://github.com/mdoming10/coinbase-tax-collector/blob/main/documentation/installation.md).

2. Download your Coinbase transaction history report CSV.

    a. Download your Coinbase CSV by following the step-by-step instructions in [this article](https://help.coinbase.com/en/commerce/managing-account/transaction-reporting#download-reports).

    b. Note the file path of your Coinbase CSV.

3. Run the CTC script.

    a. Decide which accounting method to use. Your options are either LIFO or FIFO.
    
    b. Copy and paste the code below into the terminal:

    ```sh
    $ > python3 coinbase-tax-collector.py <file path of your Coinbase CSV file> <accounting method>
    ```

    c. After running the code above, CTC will print results in the terminal and produce a new CSV file titled taxable-events.csv.

4.  Review your capital gain or loss value.

    a. Review output in the terminal.
    
    b. Alternatively, review taxable-events.csv. Open the file and see column K.


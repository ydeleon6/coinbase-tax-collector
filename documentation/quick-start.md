# Quickstart for macOS

## Overview

This quickstart is intended for macOS users who understand how to use Mac Terminal to install software and navigate directories. It will cover how to install the Coinbase Tax Collector (CTC) and caculate your capital gains or losses.

The quickstart covers the following:

- [Requirements](#requirements)
- [Install and Verify Python](#install-and-verify-python)
- [Fork and Clone the CTC Repository](#fork-and-clone-the-ctc-repository)
- [Install Dependencies](#install-dependencies)
- [Run the Script](#run-the-script)

## Requirements

CTC requires the following:

* Python version 3.10 or newer

## Install and Verify Python

1. Download the latest version of Python [here](https://www.python.org/downloads/).

2. Run the installer when prompted.

3. Verify that Python 3 was installed by entering the command below into Terminal:

    ```sh
    $ > python3 --version
    ```

## Fork and Clone the CTC Repository

1. Fork and clone the repository by following these [step-by-step instructions](https://docs.github.com/en/get-started/quickstart/fork-a-repo#forking-a-repository).

## Install Dependencies

1. Navigate to the CTC's directory on your computer. 

2. Install all dependencies in the requirements.txt file by entering this command into Terminal:

    ```sh
    $ > pip3 install -r requirements.txt
    ```

## Run the Script

1. Download your Coinbase transaction history report CSV.

    a. Download your Coinbase CSV by following the step-by-step instructions in [this help article from Coinbase](https://help.coinbase.com/en/commerce/managing-account/transaction-reporting#download-reports).

    b. Note the file path of your Coinbase CSV.

2. Run the CTC script.

    a. Decide which accounting method to use. Your options are either LIFO or FIFO.
    
    b. Enter the command below into Terminal:

    ```sh
    $ > python3 coinbase-tax-collector.py <file path of your Coinbase CSV file> <LIFO | FIFO>
    ```

    Example:

    ```sh
    $ > python3 coinbase-tax-collector.py ./capital-gains-test.csv FIFO
    ```

    c. After running the code above, CTC will print results in Terminal and produce a new CSV file named **taxable-events.csv**.
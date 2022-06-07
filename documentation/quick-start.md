# Quickstart for macOS

## Overview

This quickstart is intended for macOS users who need to use Coinbase Tax Collector (CTC) to calculate their capital gain or loss value to complete Form 1099-B during tax season. Users should understand how to use the command line to install software and navigate directories. 

This quickstart covers the following:

- [Requirements](#requirements)
- [Install and Verify Python](#install-and-verify-python)
- [Fork and Clone the CTC Repository](#fork-and-clone-the-ctc-repository)
- [Install Dependencies](#install-dependencies)
- [Run the Script](#run-the-script)

## Requirements

CTC requires the following:

* Python version 3.10 or newer

## Install and Verify Python

1. Install the latest version of Python.

    a. Download the latest Python version [here](https://www.python.org/downloads/).

    b. Run the installer when prompted.

    c. Enter this command in the terminal to verify Python 3 was installed:

    ```sh
    $ > python3 --version
    ```

## Fork and Clone the CTC Repository

1. Fork and clone the repository by following these [step-by-step instructions](https://docs.github.com/en/get-started/quickstart/fork-a-repo#forking-a-repository).

## Install Dependencies

1. Navigate to the CTC's directory on your computer. 

2. Install all dependencies in the requirements.txt file by entering this command in the terminal:

    ```sh
    $ > pip3 install -r requirements.txt
    ```

## Run the Script

1. Download your Coinbase transaction history report CSV.

    a. Download your Coinbase CSV by following the step-by-step instructions in [this help article from Coinbase](https://help.coinbase.com/en/commerce/managing-account/transaction-reporting#download-reports).

    b. Note the file path of your Coinbase CSV.

2. Run the CTC script.

    a. Decide which accounting method to use. Your options are either LIFO or FIFO.
    
    b. Enter the command below into the terminal:

    ```sh
    $ > python3 coinbase-tax-collector.py <file path of your Coinbase CSV file> <FIFO | LIFO>
    ```

    Example:

    ```sh
    $ > python3 coinbase-tax-collector.py ./capital-gains-test.csv FIFO
    ```

    c. After running the code above, CTC will print results in the terminal and produce a new CSV file named **taxable-events.csv**.
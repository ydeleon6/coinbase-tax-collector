# Coinbase Tax Collector

## Overview

Coinbase users who sell, convert, or spend cryptocurrencies through their accounts must report their activity on their federal (and possibly state) tax returns. This activity may result in capital gains or losses, potentially affecting how much they owe in taxes. Coinbase natively provides users with a Gains/Loss report with these figures, but the report uses only a single available accounting method: Highest-In, First-Out (HIFO).

Those who prefer accounting methods not supported by Coinbase, including Last-In, First-Out (LIFO) and First-In, First-Out (FIFO), can use the Coinbase Tax Collector (CTC) to calculate their capital gains or losses. 

## How it Works

CTC is a Python script developed using Python 3.10 that works by reading your Coinbase transaction history report CSV file, identifying taxable transactions, and calculating your capital gains or losses. At a high level, the script determines gains/losses as follows: 

1) Identifies taxable events, including sales, conversions, and expenses
2) Notes how much you paid for your cryptocurrency (I.e., the cost basis)
3) Notes the value of your cryptocurrency at the point of sale, conversion, or expense 
4) Subtracts the cost basis from the sale/conversion/expense price

A profit at the time of sale, conversion, or expense results in a capital gain, while a loss results in a capital loss. CTC further accounts for other factors that affect how capital gain and loss are determined, such as the accounting method you've chosen and the length of time you possessed your cryptocurrency before selling/converting/spending.

## Documentation

Users who are comfortable using the command line to navigate directories and install software can refer to the Quickstarts for getting started with CTC. Users with little to no comfort with the command line should refer to the Getting Started Guides.

- [Quickstart macOS](./documentation/quick-start.md) 
- Quickstart Windows (forthcoming)
- Getting Started Guide macOS (forthcoming)
- Getting Started Guide Windows (forthcoming)

## License

This project is licensed under the Apache License 2.0.
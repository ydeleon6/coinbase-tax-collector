#!/usr/bin/python
import sys
from argparse import ArgumentError
from operator import contains
from cryptocurrency.coinbase import CoinbaseAccount, TaxableSalesCsvWriter, TotalCapitalGainsTaxCalculator,\
	 ConsoleOutputWriter, CoinbaseTaxCalculator, formatMoney
from cryptocurrency.utils import FIFO, LIFO

CSV_OUTPUT_PATH = r'taxable-events.csv'

args_length = len(sys.argv)
if args_length == 1:
	raise ArgumentError(message="Missing input file path")

csvFilePath = str(sys.argv[1])
isFifo = contains(sys.argv, "FIFO")

taxMethod = None
if isFifo:
	taxMethod = FIFO
else:
	taxMethod = LIFO

account = CoinbaseAccount(tax_method=taxMethod)
account.load_transactions(csvFilePath)

csvWriter = TaxableSalesCsvWriter(CSV_OUTPUT_PATH, account.sales[0].keys())
consoleWriter = ConsoleOutputWriter()
salesCalculator = TotalCapitalGainsTaxCalculator()

visitors = [csvWriter, consoleWriter, salesCalculator]

calculator = CoinbaseTaxCalculator(account, visitors)
calculator.calculate()

csvWriter.shutdown()

resultAction = "Gains"
if salesCalculator.totalGains < 0:
	resultAction = "Losses"
print("")
print("Total Capital {}: {} USD".format(resultAction, formatMoney(round(salesCalculator.totalGains, 2))))
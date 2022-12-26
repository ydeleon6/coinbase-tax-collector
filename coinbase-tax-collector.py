#!/usr/bin/env python3
import sys
from argparse import ArgumentError
from operator import contains
from cryptocurrency.coinbase import CoinbaseAccount, TaxableSalesCsvWriter, TotalCapitalGainsTaxCalculator,\
	 ConsoleOutputWriter, CoinbaseTaxCalculator, formatMoney
from cryptocurrency.models import FIFO, LIFO

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

decorators = [csvWriter, salesCalculator]

calculator = CoinbaseTaxCalculator(account, decorators)
calculator.calculate()

csvWriter.shutdown()

print("")

for year in salesCalculator.taxByYear.keys():
	taxForYear = salesCalculator.taxByYear[year]
	resultAction = "Gains"
	if taxForYear < 0:
		resultAction = "Losses"
	print("Total Capital {} for {}: {} USD".format(resultAction, year, formatMoney(round(taxForYear, 2))))
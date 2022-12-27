#!/usr/bin/env python3
import sys
from argparse import ArgumentError, ArgumentParser
from operator import contains
from cryptocurrency.coinbase import CoinbaseAccount, TaxableSalesCsvWriter, TotalCapitalGainsTaxCalculator,\
	 ConsoleOutputWriter, CoinbaseTaxCalculator, formatMoney
from cryptocurrency.models import FIFO, LIFO

CSV_OUTPUT_PATH = r'taxable-events.csv'

parser = ArgumentParser(description="A program used to calculate capital gains tax on Coinbase.")
parser.add_argument("input", type=str)
parser.add_argument("method", type=str)
parser.add_argument('--output', "-o", action='store_true')
parser.add_argument("--debug", type=bool)
args = parser.parse_args()

csvFilePath = args.input

if csvFilePath is None:
	raise ArgumentError(message="Missing input file path")

isFifo = contains(args.method, "FIFO")

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

if args.output is True:
	decorators.append(consoleWriter)

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
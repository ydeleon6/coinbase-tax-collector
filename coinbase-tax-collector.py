#!/usr/bin/env python3
import logging
from argparse import ArgumentError, ArgumentParser
from operator import contains
from cryptocurrency.coinbase import CoinbaseAccount, TaxableSalesCsvWriter, TotalCapitalGainsTaxCalculator,\
	 ConsoleOutputWriter, CoinbaseTaxCalculator, formatMoney, CoinbasePro
from cryptocurrency.models import FIFO, LIFO

CSV_OUTPUT_PATH = r'taxable-events.csv'

parser = ArgumentParser(description="A program used to calculate capital gains tax on Coinbase.")
parser.add_argument("input", type=str)
parser.add_argument("method", type=str)
parser.add_argument('--output', "-o", action='store_true')
parser.add_argument("--debug", action='store_true')

args = parser.parse_args()

csvFilePath = args.input

if csvFilePath is None:
	raise ArgumentError(message="Missing input file path")

isFifo = contains(args.method, "FIFO")
logLevel = logging.INFO

if args.debug == True:
	logLevel = logging.DEBUG

# logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logLevel)
logging.basicConfig(format='[%(levelname)s]: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logLevel)

taxMethod = None
if isFifo:
	taxMethod = FIFO
else:
	taxMethod = LIFO

account = CoinbaseAccount(tax_method=taxMethod)
account.load_transactions(csvFilePath)

coinbasePro = CoinbasePro(account)
coinbasePro.load_transactions_from_fills(r'/Users/ydeleon/Downloads/coinbase-pro-fills.csv')
# coinbasePro.load_transactions_from_account(r'/Users/ydeleon/Downloads/coinbase-pro-account.csv')
account.reconcile()

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
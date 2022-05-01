#!/usr/bin/python
import argparse
import sys
import csv
from operator import contains
from cryptocurrency.coinbase import CoinbaseAccount
from cryptocurrency.common import FIFO

CSV_OUTPUT_PATH = r'taxable-events.csv'

parser = argparse.ArgumentParser(description='Calculate taxable events from your Coinbase transactions.')
parser.add_argument("input", help='The filepath to your Coinbase transactions CSV file.')

args = parser.parse_args()

csvFilePath = args.input
isVerbose = contains(sys.argv, "--verbose")

def log(sale):
	print()
	print("Transaction Date: {DateSold}".format(**sale))
	print("Date {Asset} was last acquired and bought: [{LastAcquired}] ${LastPurchasePrice}".format(**sale))
	print("Cost Basis: ${CostBasis} {Currency}".format(**sale))
	print("Price of {Asset} at Transaction: ${SpotPrice} {Currency}".format(**sale))
	print("You sold {Quantity} of {Asset} for ${Total} {Currency} (fees: {Fees}). Gains are ${Gains} {Currency}".format(**sale))

def calculateCoinbaseCapitalGains():
	account = CoinbaseAccount(tax_method=FIFO)
	account.load_transactions(csvFilePath)

	totalGains = 0.0

	with open(CSV_OUTPUT_PATH, 'w') as outFile:
		writer = csv.DictWriter(outFile, fieldnames=(account.sales[0].keys()), dialect='unix')
		writer.writeheader()

		for sale in account.sales:
			if isVerbose:
				log(sale)
			totalGains += sale['Gains']
			writer.writerow(sale)
	return totalGains

totalGains = calculateCoinbaseCapitalGains()
print("Total Capital Gains: ${} USD".format(round(totalGains, 2)))
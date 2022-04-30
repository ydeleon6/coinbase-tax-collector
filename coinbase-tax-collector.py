#!/usr/bin/python
from argparse import ArgumentError
import sys
import csv
from cryptocurrency.coinbase import CoinbaseAccount
from cryptocurrency.utils import FIFO

CSV_OUTPUT_PATH = r'taxable-events.csv'

args_length = len(sys.argv)
if args_length == 1:
	raise ArgumentError(message="Missing input file path")

csvFilePath = str(sys.argv[1])

def calculateCoinbaseCapitalGains():
	account = CoinbaseAccount(tax_method=FIFO)
	account.load_transactions(csvFilePath)

	totalGains = 0.0

	with open(CSV_OUTPUT_PATH, 'w') as outFile:
		writer = csv.DictWriter(outFile, fieldnames=(account.sales[0].keys()), dialect='unix')
		writer.writeheader()

		for sale in account.sales:
			print()
			print("Transaction Date: {DateSold}".format(**sale))
			print("Date {Asset} was last acquired and bought: [{LastAcquired}] ${LastPurchasePrice}".format(**sale))
			print("Cost Basis: ${CostBasis} {Currency}".format(**sale))
			print("Price of {Asset} at Transaction: ${SpotPrice} {Currency}".format(**sale))
			print("You sold {Quantity} of {Asset} for ${Total} {Currency} (fees: {Fees}). Gains are ${Gains} {Currency}".format(**sale))
			totalGains += sale['Gains']
			writer.writerow(sale)
	return totalGains

totalGains = calculateCoinbaseCapitalGains()
print("Total Capital Gains: ${} USD".format(round(totalGains, 2)))
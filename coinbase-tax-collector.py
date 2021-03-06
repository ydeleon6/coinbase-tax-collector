#!/usr/bin/python
from argparse import ArgumentError
from operator import contains
import sys
import csv
from cryptocurrency.coinbase import CoinbaseAccount
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

def formatMoney(amount):
	return "${:,.2f}".format(amount)

def calculateCoinbaseCapitalGains():
	account = CoinbaseAccount(tax_method=taxMethod)
	account.load_transactions(csvFilePath)

	totalGains = 0.0

	with open(CSV_OUTPUT_PATH, 'w') as outFile:
		writer = csv.DictWriter(outFile, fieldnames=(account.sales[0].keys()), dialect='unix')
		writer.writeheader()

		# Add up capital gains.
		for sale in account.sales:
			totalGains += sale['Gains']
			# format money amounts for the console.
			sale['LastPurchasePrice']  = formatMoney(sale['LastPurchasePrice'])
			sale['SpotPrice']  = formatMoney(sale['SpotPrice'])
			sale['CostBasis']  = formatMoney(sale['CostBasis'])
			sale['Total']  = formatMoney(sale['Total'])
			sale['Gains']  = formatMoney(sale['Gains'])
			sale['Fees']  = formatMoney(sale['Fees'])

			print()
			print("Transaction Date: {DateSold}".format(**sale))
			print("Date {Asset} was last acquired and bought: [{LastAcquired}] {LastPurchasePrice}".format(**sale))
			print("Cost Basis: {CostBasis} {Currency}".format(**sale))
			print("Price of {Asset} at Transaction: {SpotPrice} {Currency}".format(**sale))
			print("You sold {Quantity} of {Asset} for {Total} {Currency} (fees: {Fees}). Gains are {Gains} {Currency}".format(**sale))
			writer.writerow(sale)
	return totalGains

totalGains = calculateCoinbaseCapitalGains()
print("Total Capital Gains: {} USD".format(formatMoney(round(totalGains, 2))))
#!/usr/bin/python
import sys
from argparse import ArgumentError
from operator import contains
from cryptocurrency.coinbase import CoinbaseAccount
from cryptocurrency.utils import FIFO, LIFO, CsvTaxableEventFileWriter, PdfTaxableEventFileWriter

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

# TODO: Separate short term from long-term taxable events.
shortTermSales = []
longTermSales = []

account = CoinbaseAccount(tax_method=taxMethod)
account.load_transactions(csvFilePath)

fileWriter = PdfTaxableEventFileWriter(account.sales)
csvWriter = CsvTaxableEventFileWriter(account.sales, 'taxable-sales.csv')

csvWriter.write()
fileWriter.write()
import re
import csv
from .common import FIFO, CryptoAccount, TaxableTransaction


class CoinbaseTransaction(TaxableTransaction):
	"""Represents a transaction in Coinbase."""
	def __init__(self, timestamp, type, assetName, quantity, currency, spotPrice, subtotal, total, fees, notes):
		super().__init__(timestamp, type, assetName, quantity, currency, spotPrice, subtotal, total, fees)
		self.notes = notes

	def getTransactionsFromNotes(self):
		"""
		Read the notes field and build additional transactions if applicable.
		"""
		#TODO: Do we switch the regex? Can we get info from other transaction types?
		CONVERSION_REGEX = r"^Converted ([0-9,]*.[0-9]*) ([A-Z]*) to ([0-9,]*.[0-9]*) ([A-Z]*)"
		matches = re.search(CONVERSION_REGEX, self.notes)
		groups = matches.groups()
		splitFee = self.fees / 2
		sellQty = groups[0].replace(',', '')
		sellTxn = CoinbaseTransaction(self.timestamp, 'Sell', groups[1], sellQty, 'USD', self.spotPriceAtSale, self.subtotal, self.total, splitFee, '')
		# calculate Buy price by using buy quantity, sell subtotal
		buyQty = groups[2].replace(',', '')
		buyPriceAtConversion = self.subtotal / float(buyQty)
		buyTxn = CoinbaseTransaction(self.timestamp, 'Buy', groups[3], buyQty, 'USD', buyPriceAtConversion, self.subtotal, self.total, splitFee, '')
		return (sellTxn, buyTxn)

class CoinbaseAccount(CryptoAccount):
	"""Tracks your total Coinbase history and all the CryptoCurrency balances."""
	def __init__(self, tax_method = FIFO) -> None:
		super.__init__(tax_method)

	def trackTransaction(self, txn: CoinbaseTransaction):
		"""Track the transaction and adjust any running totals, quantities, etc as necessary."""
		if txn.type == 'Convert':
			innerTxns = txn.getTransactionsFromNotes()
			self._handleSaleTxn(innerTxns[0])
			self._handleBuyTxn(innerTxns[1])
		elif txn.type == 'Buy':
			self._handleBuyTxn(txn)
		elif txn.type == 'Sell':
			self._handleSaleTxn(txn)
		elif txn.type == 'Receive':
			self._handleReceive(txn)
		elif txn.type == 'Coinbase Earn' or txn.type == 'Rewards Income':
			self._handleIncome(txn)
		elif txn.type == 'Send' or txn.type == 'CardSpend':
			self._handleSend(txn)
		else:
			raise Exception("Unknown transaction type of "+txn.type)

	def load_transactions(self, csvFilePath):
		"""Read the Coinbase transactions CSV and load them into memory."""
		self.transactions = []

		with open(csvFilePath, 'r') as csvfile:
			filecontent = csv.reader(csvfile)
			linenum = 0
			for row in filecontent:
				linenum += 1
				if linenum == 1:
					continue # skip headers
				self.transactions.append(CoinbaseTransaction(*row))

		def getTimestamp(txn):
			return txn.timestamp

		self.transactions.sort(key=getTimestamp)

		for txn in self.transactions:
			self.trackTransaction(txn)

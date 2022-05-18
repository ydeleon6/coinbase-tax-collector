import re
import csv
from .utils import FIFO, Purchase, PurchasesQueue, TaxableSale


class CoinbaseTransaction:
	"""Represents a transaction in Coinbase."""
	def __init__(self, timestamp, type, assetName, quantity, currency, spotPrice, subtotal, total, fees, notes):
		if quantity == '' or quantity is None:
			quantity = '0'
		if spotPrice == '' or spotPrice is None:
			spotPrice = '0'
		if subtotal == '' or subtotal is None:
			subtotal = '0'
		if total == '' or total is None:
			total = '0'
		if fees == '' or fees is None:
			fees = '0'
		self.timestamp = timestamp
		self.type = type
		self.assetName = assetName
		self.spotPriceCurrency = currency
		self.quantity = float(quantity)
		self.spotPriceAtSale = float(spotPrice)
		self.subtotal = float(subtotal)
		self.total = float(total)
		self.fees = float(fees)
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


class CryptoAssetBalance:
	"""Track the current account balance of CryptoCurrency for a given asset."""
	def __init__(self, assetName, costBasisSetting = 0):
		self.assetName = assetName
		self.balance = 0.0
		self.lastAcquiredDate = ''
		self.lastKnownPurchasePrice = 0
		self.costBasisSetting =  costBasisSetting
		self.purchases = PurchasesQueue(assetName, costBasisSetting)


class CoinbaseAccount:
	sales: list[TaxableSale]
	income: list[TaxableSale]
	"""Tracks your total coinbase history and all the CryptoCurrency balances."""
	def __init__(self, tax_method = FIFO) -> None:
		self.balances = dict()
		self.sales = []
		self.income = []
		self.tax_method = tax_method

	def _getBalance(self, assetName: str):
		"""Look up the given asset's balance and return it."""
		assetBalance = self.balances.get(assetName)
		if assetBalance is None:
			assetBalance = CryptoAssetBalance(assetName, self.tax_method)
			self.balances[assetName] = assetBalance
		return assetBalance

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

	def _handleBuyTxn(self, txn: CoinbaseTransaction):
		"""Adjust balance from the current buy transaction."""
		assetBalance = self._getBalance(txn.assetName)
		assetBalance.balance += txn.quantity
		assetBalance.lastAcquiredDate = txn.timestamp
		assetBalance.lastKnownPurchasePrice = round(txn.spotPriceAtSale, 3)
		assetBalance.purchases.enqueue(Purchase(txn.spotPriceAtSale, txn.quantity, txn.subtotal))

	def _handleSaleTxn(self, txn: CoinbaseTransaction):
		"""Adjust balance from the current sale transaction."""
		assetBalance = self._getBalance(txn.assetName)
		costbasis = assetBalance.purchases.getCostBasis(txn.quantity) + txn.fees
		gains = txn.total - costbasis
		sale = {
			'dateSold': txn.timestamp,
			'lastAcquired': assetBalance.lastAcquiredDate,
			'lastPurchasePrice': assetBalance.lastKnownPurchasePrice,
			'quantity': txn.quantity,
			'asset': txn.assetName,
			'spotPrice': txn.spotPriceAtSale,
			'originalCost': txn.subtotal,
			'currency': txn.spotPriceCurrency,
			'costBasis': costbasis,
			'total': txn.total,
			'gains': gains,
			'fees': txn.fees,
		}
		self.sales.append(TaxableSale(**sale))
		assetBalance.balance -= txn.quantity

	def _handleIncome(self, txn: CoinbaseTransaction):
		"""Adjust balance based on the amount received from Coinbase."""
		assetBalance = self._getBalance(txn.assetName)
		assetBalance.balance += txn.quantity
		assetBalance.lastAcquiredDate = txn.timestamp
		income = {
			'DateReceived': txn.timestamp,
			'Quantity': txn.quantity,
			'Asset': txn.assetName,
			'SpotPrice': txn.spotPriceAtSale,
			'Currency': txn.spotPriceCurrency,
			'Total': txn.subtotal, # don't count fees.
			'Fees': txn.fees
		}
		self.income.append(income)
		assetBalance.purchases.enqueue(Purchase(txn.spotPriceAtSale, txn.quantity, 0.0))


	def _handleSend(self, txn: CoinbaseTransaction):
		"""Adjust balance based on the amount sent out from Coinbase."""
		assetBalance = self._getBalance(txn.assetName)
		assetBalance.balance -= txn.quantity

	def _handleReceive(self, txn: CoinbaseTransaction):
		"""Adjust balance based on the amount received into Coinbase from outside."""
		assetBalance = self._getBalance(txn.assetName)
		assetBalance.balance += txn.quantity
		assetBalance.lastAcquiredDate = txn.timestamp
		assetBalance.purchases.enqueue(Purchase(txn.spotPriceAtSale, txn.quantity, 0.0))

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

	def calculateCapitalGains(self):
		totalGains = 0
		for sale in self.sales:
			totalGains += sale.gains
		return round(totalGains, 2)

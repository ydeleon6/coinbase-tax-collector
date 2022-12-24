import re
import csv
from datetime import datetime
from .utils import FIFO, Purchase, PurchasesQueue


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

	def _formatTimeString(self, timestr):
		"""Format the timestamp into mm/DD/YYYY HH:MM:SS format."""
		poop = datetime.strptime(timestr,'%Y-%m-%dT%H:%M:%SZ')
		return poop.strftime("%m/%d/%Y %H:%M")

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
		assetBalance.lastAcquiredDate = self._formatTimeString(txn.timestamp)
		assetBalance.lastKnownPurchasePrice = round(txn.spotPriceAtSale, 3)
		assetBalance.purchases.enqueue(Purchase(txn.spotPriceAtSale, txn.quantity, txn.subtotal))

	def _handleSaleTxn(self, txn: CoinbaseTransaction) -> dict:
		"""Adjust balance from the current sale transaction."""
		assetBalance = self._getBalance(txn.assetName)
		costbasis = assetBalance.purchases.getCostBasis(txn.quantity) + txn.fees
		gains = txn.total - costbasis
		sale = {
			'DateSold': self._formatTimeString(txn.timestamp),
			'LastAcquired': assetBalance.lastAcquiredDate,
			'LastPurchasePrice': assetBalance.lastKnownPurchasePrice,
			'Quantity': txn.quantity,
			'Asset': txn.assetName,
			'SpotPrice': txn.spotPriceAtSale,
			'OriginalCost': txn.subtotal,
			'Currency': txn.spotPriceCurrency,
			'CostBasis': costbasis,
			'Total': txn.total,
			'Gains': round(gains, 2),
			'Fees': txn.fees,
		}
		self.sales.append(sale)
		assetBalance.balance -= txn.quantity
		return sale

	def _handleIncome(self, txn: CoinbaseTransaction):
		"""Adjust balance based on the amount received from Coinbase."""
		assetBalance = self._getBalance(txn.assetName)
		assetBalance.balance += txn.quantity
		income = {
			'DateReceived': self._formatTimeString(txn.timestamp),
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
		assetBalance.lastAcquiredDate = self._formatTimeString(txn.timestamp)
		# assetBalance.lastKnownPurchasePrice = round(txn.spotPriceAtSale, 3) # You need to determine if it's your wallet. If not, track this. Else 
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

def formatMoney(amount):
	isNegative = amount < 0
	moneyText = "{:,.2f}".format(abs(amount))

	sign = ""
	if isNegative:
		sign = "-"
	return "{}${}".format(sign, moneyText)

def getLossOrGainText(amount):
	resultAction = "Gains"
	if amount < 0:
		resultAction = "Losses"
	return resultAction

class SalesVisitor():
	"""
	The base class for visiting the TaxableSales object.
	"""
	def accept(self, sale):
		pass

	def shutdown(self):
		pass

class CoinbaseTaxCalculator():
	visitors: list[SalesVisitor]
	account = CoinbaseAccount

	def __init__(self, account: CoinbaseAccount, visitors) -> None:
		self.account = account
		self.visitors = visitors

	def calculate(self):
		for sale in self.account.sales:
			self.visit(sale)

	def visit(self, sale: dict):
		for visitor in self.visitors:
			visitor.accept(sale)


class TaxableSalesCsvWriter(SalesVisitor):
	"""
	Write taxable sales to a CSV file.
	"""
	def __init__(self, filename, columnNames) -> None:
		self.output_file = open(filename, 'w')
		self.writer = csv.DictWriter(self.output_file, fieldnames=columnNames, dialect='unix')
		self.writer.writeheader()

	def accept(self, sale):
		self.writer.writerow(sale)

	def shutdown(self):
		if not self.output_file.closed:
			self.output_file.close()

class ConsoleOutputWriter(SalesVisitor):
	"""
	Output the taxable sale to the console.
	"""
	def accept(self, sale):
		updatedSale = dict(**sale)
		updatedSale['LossOrGain'] = getLossOrGainText(sale['Gains'])
		updatedSale['LastPurchasePrice']  = formatMoney(sale['LastPurchasePrice'])
		updatedSale['SpotPrice']  = formatMoney(sale['SpotPrice'])
		updatedSale['CostBasis']  = formatMoney(sale['CostBasis'])
		updatedSale['Total']  = formatMoney(sale['Total'])
		updatedSale['Gains']  = formatMoney(sale['Gains'])
		updatedSale['Fees']  = formatMoney(sale['Fees'])

		print()
		print("Transaction Date: {DateSold}".format(**updatedSale))
		print("Date {Asset} was last acquired and bought: [{LastAcquired}] {LastPurchasePrice}".format(**updatedSale))
		print("Cost Basis: {CostBasis} {Currency}".format(**updatedSale))
		print("Price of {Asset} at Transaction: {SpotPrice} {Currency}".format(**updatedSale))
		print("You sold {Quantity} of {Asset} for {Total} {Currency} (fees: {Fees}). {LossOrGain} are {Gains} {Currency}"\
			.format(**updatedSale))

class TotalCapitalGainsTaxCalculator(SalesVisitor):
	def __init__(self) -> None:
		self.totalGains = 0.0

	def accept(self, sale):
		self.totalGains += sale['Gains']
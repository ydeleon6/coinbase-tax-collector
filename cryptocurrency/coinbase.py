import csv
from cryptocurrency.models import CryptoAssetBalance, CoinbaseTransaction, Purchase, FIFO
from cryptocurrency.utils import formatMoney, formatTimeString, getLossOrGainText, getCostBasis


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

	# TODO: This could be visitor pattern maybe? Each txn. can have a TransactionVisitor,
	# .     and the TransactionVisitor would accept sale/buy/etc... actions
	def trackTransaction(self, txn: CoinbaseTransaction):
		"""Track the transaction and adjust any running totals, quantities, etc as necessary."""
		if txn.type == 'Convert':
			innerTxns = txn.getTransactionsFromNotes()
			self._handleSaleTxn(innerTxns[0])
			self._handleBuyTxn(innerTxns[1])
		elif txn.type == 'Buy' or txn.type=='ConvertBuy' or txn.type == 'CardBuyBack':
			self._handleBuyTxn(txn)
		elif txn.type == 'Sell' or txn.type == 'ConvertSell' or txn.type == 'Advanced Trade Sell':
			self._handleSaleTxn(txn)
		elif txn.type == 'Receive' or txn.type == 'Learning Reward':
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
		assetBalance.lastAcquiredDate = formatTimeString(txn.timestamp)
		assetBalance.lastKnownPurchasePrice = round(txn.spotPriceAtSale, 3)
		assetBalance.purchases.enqueue(Purchase(txn.spotPriceAtSale, txn.quantity, txn.subtotal))

	def _handleSaleTxn(self, txn: CoinbaseTransaction) -> dict:
		"""Adjust balance from the current sale transaction."""
		assetBalance = self._getBalance(txn.assetName)
		costbasis = getCostBasis(assetBalance.purchases, txn)
		# print("Cost Basis for {} is {}.".format(txn, costbasis))
		gains = txn.total - costbasis
		sale = {
			'DateSold': txn.timestamp,
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
			'DateReceived': formatTimeString(txn.timestamp),
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
		assetBalance.lastAcquiredDate = formatTimeString(txn.timestamp)
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

class SalesDecorator():
	"""
	The base class for decorating the TaxableSales dictionary.
	"""
	def execute(self, sale: dict):
		"""Execute an action on the sale."""
		pass

	def shutdown(self):
		"""Shutdown any necessary resources."""
		pass

class CoinbaseTaxCalculator():
	decorators: list[SalesDecorator]
	account = CoinbaseAccount

	def __init__(self, account: CoinbaseAccount, decorators: list[SalesDecorator]) -> None:
		self.account = account
		self.decorators = decorators

	def calculate(self):
		for sale in self.account.sales:
			self.decorate(sale)

	def decorate(self, sale: dict):
		for decorator in self.decorators:
			decorator.execute(sale)

class TaxableSalesCsvWriter(SalesDecorator):
	"""
	Write taxable sales to a CSV file.
	"""
	def __init__(self, filename, columnNames) -> None:
		self.output_file = open(filename, 'w')
		self.writer = csv.DictWriter(self.output_file, fieldnames=columnNames, dialect='unix')
		self.writer.writeheader()

	def execute(self, sale):
		self.writer.writerow(sale)

	def shutdown(self):
		if not self.output_file.closed:
			self.output_file.close()

class ConsoleOutputWriter(SalesDecorator):
	"""
	Output the taxable sale to the console.
	"""
	def execute(self, sale):
		updatedSale = dict(**sale)
		updatedSale['LossOrGain'] = getLossOrGainText(sale['Gains'])
		updatedSale['LastPurchasePrice']  = formatMoney(sale['LastPurchasePrice'])
		updatedSale['SpotPrice']  = formatMoney(sale['SpotPrice'])
		updatedSale['CostBasis']  = formatMoney(sale['CostBasis'])
		updatedSale['Total']  = formatMoney(sale['Total'])
		updatedSale['Gains']  = formatMoney(sale['Gains'])
		updatedSale['Fees']  = formatMoney(sale['Fees'])
		updatedSale['DateSold'] = formatTimeString(sale['DateSold'])

		print()
		print("Transaction Date: {DateSold}".format(**updatedSale))
		print("Date {Asset} was last acquired and bought: [{LastAcquired}] {LastPurchasePrice}".format(**updatedSale))
		print("Cost Basis: {CostBasis} {Currency}".format(**updatedSale))
		print("Price of {Asset} at Transaction: {SpotPrice} {Currency}".format(**updatedSale))
		print("You sold {Quantity} of {Asset} for {Total} {Currency} (fees: {Fees}). {LossOrGain} are {Gains} {Currency}"\
			.format(**updatedSale))

class TotalCapitalGainsTaxCalculator(SalesDecorator):
	def __init__(self) -> None:
		self.totalGains = 0.0
		self.taxByYear = dict()

	def execute(self, sale):
		self.totalGains += sale['Gains']
		taxYear = sale['DateSold'].year
		
		if self.taxByYear.get(taxYear) is None:
			self.taxByYear[taxYear] = 0.0
		
		self.taxByYear[taxYear] += sale['Gains']
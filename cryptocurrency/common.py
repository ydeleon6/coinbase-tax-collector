import datetime


FIFO = 0 # First in, first out
LIFO = 1 # Last in, first out
SPID_METHOD = 2
WEIGHTED_AVERAGE_METHOD = 3 # Allowed outside the U.S.

class Queue():
	"""Using Python Lists as a FIFO Queue"""
	def __init__(self, queueMethod = 0):
		self.queue = []
		self.queuingMethod = queueMethod

	def enqueue(self, value):
		# Inserting to the end of the queue
		self.queue.append(value)

	def dequeue(self):
		# Remove the furthest element from the top,
		# since the Queue is a FIFO structure
		if (self.queuingMethod == FIFO):
			return self.queue.pop(0)
		return self.queue.pop() # else return LIFO

	def peek(self):
		if len(self.queue) == 0:
			return None
		if self.queuingMethod == FIFO:
			return self.queue[0]
		return self.queue[len(self.queue) - 1]

	def length(self):
		return len(self.queue)

class Purchase:
	"""Tracks the price of a unit at time of a purchase."""
	def __init__(self, costOfUnit, quantity, realSubTotal = None) -> None:
		self.pricePerUnit = costOfUnit
		self.quantity = quantity
		if realSubTotal is None:
			self.subtotal = costOfUnit * quantity
		else: # used to override a purchase price when things are given to you like rewards, income, wallet transfers, etc.
			self.subtotal = realSubTotal

class PurchasesQueue(Queue):
	"""Tracks all historical purchases for a specific Crypto asset."""
	def __init__(self, assetName, costBasisSetting):
		super().__init__(costBasisSetting)
		self.assetName = assetName
		self.costBasisSetting = costBasisSetting

	@property
	def total_assets(self):
		total = 0.0
		for item in self.queue:
			total += item.quantity
		return total

	def getCostBasis(self, quantity) -> float:
		"""The price you paid to acquire all these shares."""
		# You should always be able to get this because you actually
		# do have a reference for how much you paid for you quantity.
		# So when you use this for calculating a baseline for a future sale,
		# All you have to do is figure out how much you're "selling" (e.g. 0.5 algo)
		# and calculate how much you spent on it, going oldest to newest (FIFO)
		# e.g. [ (0.5, $50,000), (1, $10,000)... ] # current purchases
		# TX1 - If I sold 1 BTC, then cost basis is (0.5 * 50k) + (0.5 * 10.000) = $30k
		# TX2 - if I sold 0.5 BTC, then cost basis is (0.5 * 10k) = $5k # the 0.5 was remaining. 
		if self.length() == 0:
			raise Exception("How did I acquire {asset} w/o buying it (or income)?".format(asset=self.assetName))

		if self.costBasisSetting == WEIGHTED_AVERAGE_METHOD:
			return self.getWeightedAverageCostPerShare(quantity)

		totalCostBasis = 0.0
		quantityRetrieved = 0.0
		quantityRemaining = quantity

		print("Total {} - {}".format(self.assetName, self.total_assets))
		#TODO: Improve rounding? I'm capping at 10 to avoid rounding issues.
		while quantityRetrieved < quantity:
			purchase = self.peek()
			if purchase is None:
				msg = "Cannot account for {} {} in your purchases/receives".format(quantityRemaining, self.assetName)
				raise Exception(msg)
			if purchase.quantity <= quantityRemaining: # if your last/first purchase is a smaller amount than you want, pop it so we can grab the next one.
				self.dequeue()
				quantityRetrieved = round(quantityRetrieved + purchase.quantity, 10)
				quantityRemaining = round(quantityRetrieved - purchase.quantity, 10)
				totalCostBasis += purchase.subtotal
			else:	# your first/last purchase contained more than you want, so modify it in place.
				purchase.quantity = round(purchase.quantity - quantity, 2)
				quantityRetrieved = quantity
				quantityRemaining = 0
				totalCostBasis = round(totalCostBasis + (quantityRetrieved * purchase.pricePerUnit), 10) # TODO: should - fees here too I think.
		return totalCostBasis

	# https://www.fool.com/knowledge-center/how-to-calculate-weighted-average-price-per-share.aspx
	def getWeightedAverageCostPerShare(self, quantity) -> float:
		"""Calculate the average cost of this asset amongst all your purchases."""
		total = 0.0
		quantity = 0.0
		for price in self.queue:
			quantity += price.quantity
			total += price.pricePerUnit * price.quantity # price total is inclusive of quantity (e.g. costPerShare * quantity)
		if quantity == 0:
			return 0.0
		return float(total / quantity)


class TaxableTransaction:
	"""Represents a basic taxable transaction."""
	def __init__(self, timestamp, type, assetName, quantity, currency, spotPrice, subtotal, total, fees):
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

class CryptoAssetBalance:
	"""Track the current account balance of CryptoCurrency for a given asset."""
	def __init__(self, assetName, costBasisSetting = 0):
		self.assetName = assetName
		self.balance = 0.0
		self.lastAcquiredDate = ''
		self.lastKnownPurchasePrice = 0
		self.costBasisSetting =  costBasisSetting
		self.purchases = PurchasesQueue(assetName, costBasisSetting)


class CryptoAccount:
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

	def _handleBuyTxn(self, txn: TaxableTransaction):
		"""Adjust balance from the current buy transaction."""
		assetBalance = self._getBalance(txn.assetName)
		assetBalance.balance += txn.quantity
		assetBalance.lastAcquiredDate = self._formatTimeString(txn.timestamp)
		assetBalance.lastKnownPurchasePrice = round(txn.spotPriceAtSale, 3)
		assetBalance.purchases.enqueue(Purchase(txn.spotPriceAtSale, txn.quantity, txn.subtotal))

	def _handleSaleTxn(self, txn: TaxableTransaction):
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

	def _handleIncome(self, txn: TaxableTransaction):
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

	def _handleSend(self, txn: TaxableTransaction):
		"""Adjust balance based on the amount sent out from Coinbase."""
		assetBalance = self._getBalance(txn.assetName)
		assetBalance.balance -= txn.quantity

	def _handleReceive(self, txn: TaxableTransaction):
		"""Adjust balance based on the amount received into Coinbase from outside."""
		assetBalance = self._getBalance(txn.assetName)
		assetBalance.balance += txn.quantity
		assetBalance.lastAcquiredDate = self._formatTimeString(txn.timestamp)
		# assetBalance.lastKnownPurchasePrice = round(txn.spotPriceAtSale, 3) # You need to determine if it's your wallet. If not, track this. Else 
		assetBalance.purchases.enqueue(Purchase(txn.spotPriceAtSale, txn.quantity, 0.0))
	# This could be cool, then override the one in the child to convert it to the write format.
	# def load_transactions(self, csvFilePath):
	# 	"""Read the Coinbase transactions CSV and load them into memory."""
	# 	self.transactions = []

	# 	with open(csvFilePath, 'r') as csvfile:
	# 		filecontent = csv.reader(csvfile)
	# 		linenum = 0
	# 		for row in filecontent:
	# 			linenum += 1
	# 			if linenum == 1:
	# 				continue # skip headers
	# 			self.transactions.append(CoinbaseTransaction(*row))

	# 	def getTimestamp(txn):
	# 		return txn.timestamp

	# 	self.transactions.sort(key=getTimestamp)

	# 	for txn in self.transactions:
	# 		self.trackTransaction(txn)
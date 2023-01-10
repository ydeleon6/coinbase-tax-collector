import re
import logging
from datetime import datetime

FIFO = 0 # First in, first out
LIFO = 1 # Last in, first out
SPID_METHOD = 2
WEIGHTED_AVERAGE_METHOD = 3 # Allowed outside the U.S.

logger = logging.getLogger("models")

class CoinbaseTransaction:
	"""Represents a taxable transaction in Coinbase."""
	def __init__(self, timestamp, txnType, assetName, quantity, currency, spotPrice, subtotal, total, fees, notes):
		"""Create a new coinbase transaction"""
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
		if type(timestamp) is datetime:
			self.timestamp = timestamp
		else:
			self.timestamp = datetime.strptime(timestamp,'%Y-%m-%dT%H:%M:%SZ')
		self.type = txnType
		self.assetName = assetName
		self.spotPriceCurrency = currency
		self.quantity = abs(float(quantity))
		self.spotPriceAtSale = float(spotPrice)
		self.subtotal = float(subtotal)
		self.total = abs(float(total))
		self.fees = float(fees)
		self.notes = notes

	def __str__(self) -> str:
		return ("[{type}] {quantity} {assetName} @ ${spotPriceAtSale} per {assetName}").format(**(self.__dict__))

	def getTransactionsFromNotes(self):
		"""
		Read the notes field and build additional transactions if applicable.
		"""
		#TODO: Do we switch the regex? Can we get info from other transaction types?
		CONVERSION_REGEX = r"^Converted ([0-9,]*.[0-9]*) ([A-Z]*) to ([0-9,]*.[0-9]*) ([A-Z]*)"
		matches = re.search(CONVERSION_REGEX, self.notes)
		groups = matches.groups()
		# splitFee = self.fees / 2
		sellQty = groups[0].replace(',', '')
		sellTxn = CoinbaseTransaction(self.timestamp, 'ConvertSell', groups[1], sellQty, 'USD', self.spotPriceAtSale, self.subtotal, self.total, self.fees, '')
		# calculate Buy price by using buy quantity, sell subtotal
		buyQty = groups[2].replace(',', '')
		buyPriceAtConversion = self.subtotal / float(buyQty)
		buyTxn = CoinbaseTransaction(self.timestamp, 'ConvertBuy', groups[3], buyQty, 'USD', buyPriceAtConversion, self.subtotal, self.total, 0, '')
		return (sellTxn, buyTxn)

# portfolio,trade id,product,side,created at,size,size unit,price,fee,total,price/fee/total unit
class CoinbaseProFill(CoinbaseTransaction):
	"""Tracks a filled market order on CoinbasePro."""
	def __init__(self,portfolio,trade_id,product,side,created_at,size,size_unit,price,fee,total,currency) -> None:
		self.portfolio = portfolio
		self.trade_id = trade_id
		self.pool = product
		txnType = ''
		if side == 'BUY':
			txnType = 'Buy'
		elif side == 'SELL':
			txnType = 'Sell'
		else:
			txnType = side
		timestamp = datetime.strptime(created_at,'%Y-%m-%dT%H:%M:%S.%fZ')
		super().__init__(timestamp,txnType,size_unit,size,currency,price,'',total,fee,'')

# portfolio,type,time,amount,balance,amount/balance unit,transfer id,trade id,order id
class CoinbaseProAccountHistory(CoinbaseTransaction):
	def __init__(self,portfolio,type,time,amount,balance,unit,transfer_id,trade_id,order_id) -> None:
		self.portfolio = portfolio
		# self.deposit doesn't help us at this time.
		txnType = ''
		if type == 'match':
			#TODO: look at fills / timestamp to confirm which way money went. 
			pass
		elif type == 'withdrawal':
			txnType = 'Send'
		timestamp = datetime.strptime(time,'%Y-%m-%dT%H:%M:%S.%fZ')
		# I shouldn't care about how much the price of something was if I sent it
		# between wallets, I want to base it on roughly how much I paid for it 
		# initially.
		super().__init__(timestamp, txnType, unit, amount,'USD',0,0,0,0,'')

class CryptoAssetBalance:
	"""Track the current account balance of CryptoCurrency for a given asset."""
	def __init__(self, assetName, costBasisSetting = 0):
		self.assetName = assetName
		self.current_balance = 0.0
		self.lastAcquiredDate = ''
		self.lastKnownPurchasePrice = 0
		self.costBasisSetting =  costBasisSetting
		self.purchases = PurchasesQueue(assetName, costBasisSetting)
		self.balance = 0.0

	# @property
	# def balance(self):
	# 	return self.current_balance

	# @balance.setter
	# def balance(self, bal):
	# 	logger.debug(bal)
	# 	new_balance = self.current_balance + bal
	# 	if new_balance < 0:
	# 		logger.warn("Cannot lower %s below 0 by %f", self.assetName, new_balance)
	# 		raise ValueError("Cannot reduce balance below 0 on Coinbase.")
	# 	else:
	# 		logger.debug("Increasing %s balance by %d", self.assetName, bal)
	# 	self.current_balance += bal

class Queue():
	"""Using Python Lists as a FIFO Queue"""
	def __init__(self, queueMethod = FIFO):
		self.queue = []
		self.queuingMethod = queueMethod

	def enqueue(self, value):
		"""Insert an item to the queue."""
		self.queue.append(value)

	def dequeue(self):
		"""Remove the furthest item from the start of the queue."""
		if (self.queuingMethod == FIFO):
			return self.queue.pop(0)
		return self.queue.pop() # else return LIFO

	def replace_item(self, item):
		if self.queuingMethod == FIFO:
			self.queue[0] = item
		else:
			self.queue[self.length - 1] = item

	def peek(self):
		"""Return (but do not remove) the next item in the Queue."""
		if len(self.queue) == 0:
			return None
		if self.queuingMethod == FIFO:
			return self.queue[0]
		return self.queue[len(self.queue) - 1]

	@property
	def length(self):
		"""The number of items in the Queue."""
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

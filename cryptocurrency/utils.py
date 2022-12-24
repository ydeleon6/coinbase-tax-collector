FIFO = 0 # First in, first out
LIFO = 1 # Last in, first out
SPID_METHOD = 2
WEIGHTED_AVERAGE_METHOD = 3 # Allowed outside the U.S.

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

	def peek(self):
		"""Return (but do not remove) the next item in the Queue."""
		if len(self.queue) == 0:
			return None
		if self.queuingMethod == FIFO:
			return self.queue[0]
		return self.queue[len(self.queue) - 1]

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

	def getCostBasis(self, quantity) -> float:
		"""The price you paid to acquire all these shares."""
		# You should always be able to get this because you actually
		# do have a reference for how much you paid for your quantity.
		# So when you use this for calculating a baseline for a future sale,
		# All you have to do is figure out how much you're "selling" (e.g. 0.5 algo)
		# and calculate how much you spent on it, going oldest to newest (FIFO)
		# e.g. [ (0.5, $50,000), (1, $10,000)... ] # current purchases
		# TX1 - If I sold 1 BTC, then cost basis is (0.5 * 50k) + (0.5 * 10.000) = $30k
		# TX2 - if I sold 0.5 BTC, then cost basis is (0.5 * 10k) = $5k # the 0.5 was remaining. 
		if self.length() == 0:
			raise Exception("How did I acquire {asset} w/o buying it (or income)?".format(asset=self.assetName))

		# if self.costBasisSetting == WEIGHTED_AVERAGE_METHOD:
		# 	return self.getWeightedAverageCostPerShare(quantity)

		totalCostBasis = 0.0
		quantityRetrieved = 0.0
		quantityRemaining = quantity

		#TODO: Improve rounding? I'm capping at 10 decimal places to avoid rounding issues.
		while quantityRetrieved < quantity:
			purchase = self.peek()
			if purchase is None:
				msg = "Cannot account for {} {} in your purchases/receives".format(quantityRemaining, self.assetName)
				raise Exception(msg)
			if purchase.quantity <= quantityRemaining: # if your last/first purchase is a smaller amount than you want, pop it so we can grab the next one.
				purchase = self.dequeue()
				quantityRetrieved += round(purchase.quantity, 10)
				totalCostBasis += purchase.subtotal
				quantityRemaining = quantity - quantityRetrieved
			else:	# your first/last purchase contained more than you want, so modify it in place.
				purchase.quantity = round(purchase.quantity - quantityRemaining, 10)
				quantityRetrieved += quantityRemaining
				totalCostBasis = round(totalCostBasis + (quantityRemaining * purchase.pricePerUnit), 10) # TODO: should - fees here too I think.
				quantityRemaining = 0
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
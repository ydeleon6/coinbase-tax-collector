import logging
from datetime import datetime
from cryptocurrency.models import CoinbaseTransaction, TransactionType, PurchasesQueue, Purchase


logger = logging.getLogger("utils")

def formatTimeString(timestamp: datetime):
	"""Format the timestamp into mm/DD/YYYY HH:MM:SS format."""
	return timestamp.strftime("%m/%d/%Y %H:%M")

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

def getCostBasis(queue: PurchasesQueue, txn: CoinbaseTransaction) -> tuple[float,float]:
	"""The price you paid to acquire all these shares.Returns the current cost basis, along
	with the quantiy remaining (if any)"""
	# You should always be able to get this because you actually
	# do have a reference for how much you paid for your quantity.
	# So when you use this for calculating a baseline for a future sale,
	# All you have to do is figure out how much you're "selling" (e.g. 0.5 algo)
	# and calculate how much you spent on it, going oldest to newest (FIFO)
	# e.g. [ (0.5, $50,000), (1, $10,000)... ] # current purchases
	# TX1 - If I sold 1 BTC, then cost basis is (0.5 * 50k) + (0.5 * 10.000) = $30k
	# TX2 - if I sold 0.5 BTC, then cost basis is (0.5 * 10k) = $5k # the 0.5 was remaining.
	if txn.type == TransactionType.LEARN or txn.type == TransactionType.EARN:
		return (txn.subtotal, 0) # it was a gift
	elif queue.length == 0:
		logger.error("You have no more %s. Cannot account for %f. Perhaps missing txn?", \
			txn.assetName, txn.quantity)
		return (-1, txn.quantity)

	quantity = float(txn.quantity)
	quantityRemaining = float(txn.quantity)
	totalCostBasis = 0.0
	quantityRetrieved = 0.0
	DEFAULT_DECIMALS = 6
	logger.debug(" ")

	logger.debug("Looking for {} {} amongst {} transactions.".format(quantity, txn.assetName, queue.length))

	while quantityRemaining > 0:
		purchase: Purchase = queue.peek()
		logger.debug("Target %f: Current Total: %f: Amount Left: %f", quantity, quantityRetrieved, quantityRemaining)
		# just figured out the issue, its possible Coinbase sells _more_ crypto 
		# than you own to cover spread (e.g. you convert $5 of BCH, if the price 
		# goes down they'll just enough crypto for you within some tolerance?.)
		if queue.length == 0 and txn.fees >= (quantityRemaining * txn.spotPriceAtSale):
			logger.debug("TXN Type was %s and the missing %f %s was likely covered by fees.", txn.type, quantityRemaining, txn.assetName)
			quantityRemaining = 0 # clear out the rest
			quantityRetrieved += quantityRemaining
			totalCostBasis = txn.subtotal
		elif queue.length == 0 and quantityRemaining != quantityRetrieved:
			msg = "Looking for {} {} in your purchases/receives. Found {} of {} so far. Perhaps missing a transaction?"\
				.format(quantityRemaining, txn.assetName, quantityRetrieved, quantity)
			logger.error(msg)
			break
		elif purchase.quantity <= quantityRemaining: # if the transaction contains a smaller amount than you want, pop it so we can use all of it and grab the next one.
			purchase = queue.dequeue()
			qty = round(purchase.quantity, DEFAULT_DECIMALS)
			quantityRetrieved += qty
			quantityRemaining = round(quantityRemaining - qty, DEFAULT_DECIMALS)
			logger.debug("Found %f, taking the entire contents. Still looking for %f.", qty, quantityRemaining)
			totalCostBasis += purchase.subtotal # use subtotal in case we paid something different than spotPrice * qty
		elif purchase.quantity > quantityRemaining:	# the transaction contained more than you want, so modify it in place.
			qty = round(purchase.quantity, DEFAULT_DECIMALS)
			oldQuantity = float(qty)
			newQuantity = round(oldQuantity - quantityRemaining, DEFAULT_DECIMALS) # only had 25 ADA left to look for, trans. had 100 - so 75 is left
			logger.debug("Found %f. modifying the last transaction in place by %f to %f", oldQuantity, quantityRemaining, newQuantity)
			purchase.quantity = newQuantity
			totalCostBasis += (quantityRemaining * purchase.pricePerUnit - txn.fees)
			quantityRemaining = 0
			quantityRetrieved += newQuantity
			queue.replace_item(purchase) # update item in place.

	return (totalCostBasis, quantityRemaining)

# https://www.fool.com/knowledge-center/how-to-calculate-weighted-average-price-per-share.aspx
def getWeightedAverageCostPerShare(queue: PurchasesQueue, quantity) -> float:
	"""Calculate the average cost of this asset amongst all your purchases."""
	total = 0.0
	quantity = 0.0
	for purchase in queue:
		quantity += purchase.quantity
		total += purchase.pricePerUnit * purchase.quantity # price total is inclusive of quantity (e.g. costPerShare * quantity)
	if quantity == 0:
		return 0.0
	return float(total / quantity)
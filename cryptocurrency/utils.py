import logging
from datetime import datetime
from cryptocurrency.models import CoinbaseTransaction, PurchasesQueue


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

def getCostBasis(queue: PurchasesQueue, txn: CoinbaseTransaction) -> float:
	"""The price you paid to acquire all these shares."""
	# You should always be able to get this because you actually
	# do have a reference for how much you paid for your quantity.
	# So when you use this for calculating a baseline for a future sale,
	# All you have to do is figure out how much you're "selling" (e.g. 0.5 algo)
	# and calculate how much you spent on it, going oldest to newest (FIFO)
	# e.g. [ (0.5, $50,000), (1, $10,000)... ] # current purchases
	# TX1 - If I sold 1 BTC, then cost basis is (0.5 * 50k) + (0.5 * 10.000) = $30k
	# TX2 - if I sold 0.5 BTC, then cost basis is (0.5 * 10k) = $5k # the 0.5 was remaining. 
	if queue.length == 0:
		raise Exception("How did I acquire {asset} w/o buying it (or income)?".format(asset=queue.assetName))

	quantity = float(txn.quantity)
	totalCostBasis = 0.0
	quantityRetrieved = 0.0
	quantityRemaining = float(quantity)
	logger.debug(" ")

	logger.debug("Looking for {} {} amongst {} transactions.".format(quantity, txn.assetName, queue.length))

	while True:
		purchase = queue.peek()
		logger.debug("Target %f: Current Total: %f: Amount Left: %f", quantity, quantityRetrieved, quantityRemaining)
		# just figured out the issue, its possible Coinbase sells _more_ crypto 
		# than you own to cover spread (e.g. you convert $5 of BCH, if the price 
		# goes down they'll just enough crypto for you within some tolerance?.)
		if queue.length == 0 and txn.fees >= (quantityRemaining * txn.spotPriceAtSale):
			logger.debug("TXN Type was %s and the missing %f %s was likely covered by fees.", txn.type, quantityRemaining, txn.assetName)
			quantityRemaining = 0 # clear out the rest
			quantityRetrieved += quantityRemaining
			totalCostBasis = txn.subtotal
			break
		elif queue.length == 0:
			msg = "Looking for {} {} in your purchases/receives. Found {} of {} so far. Perhaps missing a transaction?"\
				.format(quantityRemaining, txn.assetName, quantityRetrieved, quantity)
			logger.error(msg)
			break
		elif purchase.quantity <= quantityRemaining: # if the transaction contains a smaller amount than you want, pop it so we can use all of it and grab the next one.
			purchase = queue.dequeue()
			quantityRetrieved += purchase.quantity
			quantityRemaining -= float(purchase.quantity)
			logger.debug("Found {}, taking the entire contents and looking for {}.".format(purchase.quantity, quantityRemaining))
			totalCostBasis += (purchase.quantity * purchase.pricePerUnit)
		elif purchase.quantity > quantityRemaining:	# the transaction contained more than you want, so modify it in place.
			currentQuantity = str(purchase.quantity)
			modifiedPurchase = purchase
			modifiedPurchase.quantity = purchase.quantity - quantityRemaining # only had 25 ADA left to look for, trans. had 100 - so 75 is left
			logging.debug("Found {}. modifying the last transaction in place by {} from {}".format(currentQuantity, quantityRemaining, modifiedPurchase.quantity))
			quantityRetrieved += purchase.quantity
			totalCostBasis += quantityRemaining * purchase.pricePerUnit # TODO: should - fees here too I think.
			queue.replace_item(modifiedPurchase)
			break

	return totalCostBasis

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
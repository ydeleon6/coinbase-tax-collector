import csv
from datetime import datetime
from typing import overload
from fillpdf import fillpdfs

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
		# do have a reference for how much you paid for your quantity.
		# So when you use this for calculating a baseline for a future sale,
		# all you have to do is figure out how much you're "selling" (e.g. 0.5 algo)
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

		#TODO: Improve rounding? I'm capping at 10 decimal places to avoid rounding issues.
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

class CustomDate:
	def __init__(self, timestamp) -> None:
		self.timestamp = None
		if timestamp != '':
			self.timestamp = datetime.strptime(timestamp,'%Y-%m-%dT%H:%M:%SZ')

	def toLongDateString(self):
		"""Format the timestamp into mm/DD/YYYY HH:MM:SS format."""
		if self.timestamp is None:
			return ''
		return self.timestamp.strftime("%m/%d/%Y %H:%M")

	def toShortDateString(self):
		"""Format the timestamp into mm/DD/YY format."""
		if self.timestamp is None:
			return ''
		return self.timestamp.strftime("%m/%d/%Y")

	def __str__(self) -> str:
		return self.toLongDateString()

def formatMoneyString(amount):
	return "{:,.2f}".format(amount)

class TaxableSale:
	"""A Taxable sale information."""
	def __init__(self, dateSold, lastAcquired, lastPurchasePrice, quantity,
		asset, spotPrice, originalCost, currency, costBasis, total, gains, fees) -> None:
		self.date_sold = CustomDate(dateSold)
		self.last_acquired = CustomDate(lastAcquired)
		self.last_purchase_price = lastPurchasePrice
		self.quantity = quantity
		self.asset = asset
		self.spot_price = round(spotPrice, 2)
		self.original_cost = round(originalCost, 2)
		self.currency = currency
		self.cost_basis = round(costBasis, 2)
		self.total = round(total, 2)
		self.gains = round(gains, 2)
		self.fees = fees

# def __str__(self):
	# 	return """
	# 	Transaction Date: {date_sold}
	# 	"Date {asset} was last acquired and bought: [{last_acquired}] {last_purchase_price}".format(**sale))
	# 	print("Cost Basis: {cost_basis} {currency}".format(**sale))
	# 	print("Price of {asset} at Transaction: {spot_price} {currency}".format(**sale))
	# 	print("You sold {auantity} of {asset} for {total} {currency} (fees: {fees}). Gains are {gains} {currency}".format(**sale))

class TaxableSalesFileWriterBase:
	"""Base class for writing taxable sales to an output file."""
	def __init__(self, taxable_events: list[TaxableSale], output_path) -> None:
		self.taxable_events = taxable_events
		self.output_path = output_path
		self.cancel = False

	def write_row(self, sale: TaxableSale):
		"""Write a single sale to the file. This function is a generator
		to align with how PDF export works."""
		pass

	def close(self):
		"""Close the file writer."""
		pass

	def write(self):
		"""Write all events to the output file(s)."""
		for event in self.taxable_events:
			if self.cancel:
				break
			self.write_row(event)
		self.close()

class CsvTaxableEventFileWriter(TaxableSalesFileWriterBase):
	"""Write the taxable events to a CSV file format."""
	def __init__(self, taxable_events, output_path) -> None:
		super().__init__(taxable_events, output_path)
		self.file_handle = open(self.output_path, 'w', newline='')
		headers = ["DateAcquired", "DateSold", "PricePerUnit","Quantity","Asset","SpotPrice", "OriginalCost", "CostBasis","Total","Gains"]
		self.csv_writer = csv.DictWriter(self.file_handle, fieldnames=headers)
		self.csv_writer.writeheader()

	def write_row(self, sale: TaxableSale):
		salesDict = {
			'DateSold': sale.date_sold.toLongDateString(),
			'DateAcquired': sale.last_acquired.toLongDateString(),
			'PricePerUnit': sale.last_purchase_price,
			'Quantity': sale.quantity,
			'Asset': sale.asset,
			'SpotPrice': sale.spot_price,
			'OriginalCost': sale.original_cost,
			'CostBasis': sale.cost_basis,
			'Total': sale.total,
			'Gains': sale.gains,
		}
		self.csv_writer.writerow(salesDict)

	def close(self):
		super().close()
		self.file_handle.close()

SHORT_TERM_SALES_PAGE_IDX = 1
LONG_TERM_SALES_PAGE_IDX = 2

class PdfTaxableEventFileWriter(TaxableSalesFileWriterBase):
	"""Write the taxable events to a PDF in the Form 8949 for US Taxes file format."""
	def __init__(self, taxable_events: list[TaxableSale]) -> None:
		super().__init__(taxable_events, 'output.pdf')
		self.current_page = 0
		self.current_fields = dict()
		self.current_row = 0
		self.cancel = False
		self.rowGenerator = self._fillRowItem()

	# override base write_row()
	def write_row(self, sale: TaxableSale):
		super().write_row(sale)
		try:
			next(self.rowGenerator)
		except (StopIteration):
			self.rowGenerator = self._fillRowItem()
			print("Resetting the generator.")
			return None

	def _fillRowItem(self):
		"""A generator that progressively writes to the next row of fields on the PDF."""
		rowModulus = 8
		maxPageRowLength = 14
		lastCell = rowModulus * maxPageRowLength
		#TODO: Update to differentiate on long term / short term.
		self.current_fields = self._openNewPage(SHORT_TERM_SALES_PAGE_IDX)
		fieldList = list(self.current_fields)
		adjustedIndex = 0
		sales = []

		for i, key in enumerate(fieldList):
			if i < 5:
				continue

			adjustedIndex = i - 5 # easier for me to reason about the row indexes this way

			if i != 0 and adjustedIndex % rowModulus == 0:
				if adjustedIndex == lastCell:
					# fill the last 4 fields of the page which are totaling total proceeds, costs, and gains.
					print("No more space to print sales, getting a new page.")
					self.flush(sales, i, fieldList)
					yield -1
				else:
					sale = self.taxable_events[self.current_row]
					yield self._updateFieldRow(i, fieldList, sale)
					sales.append(sale)

	def flush(self, sales: list[TaxableSale], startIndex: int, fieldList: list):
		totalProceedsFieldKey = fieldList[startIndex]
		totalCostBasisFieldKey = fieldList[startIndex+1]
		emptyFieldKey = fieldList[startIndex+2]
		totalAdjustmentsFieldKey = fieldList[startIndex+3]
		totalGainsOrLossesFieldKey = fieldList[startIndex+4]

		totalProceeds = 0
		totalCostBasis = 0
		totalGainsOrLosses = 0

		for sale in sales:
			totalProceeds += sale.total
			totalCostBasis += sale.cost_basis
			totalGainsOrLosses += sale.gains

		self.current_fields[totalProceedsFieldKey] = round(totalProceeds, 2)
		self.current_fields[totalCostBasisFieldKey] = round(totalCostBasis, 2)
		self.current_fields[emptyFieldKey] = ''
		self.current_fields[totalAdjustmentsFieldKey] = 0
		self.current_fields[totalGainsOrLossesFieldKey] = round(totalGainsOrLosses, 2)
		self._writePage()

	def enterSaleItem(self, sale: TaxableSale, keyList: list):
		for i, key in enumerate(keyList):
			if i == 0:
				self.current_fields[key] = "{} {}".format(sale.quantity, sale.asset)
			elif i == 1:
				self.current_fields[key] = sale.last_acquired.toShortDateString()
			elif i == 2:
				self.current_fields[key] = sale.date_sold.toShortDateString()
			elif i == 3:
				self.current_fields[key] = sale.total
			elif i == 4:
				self.current_fields[key] = sale.cost_basis
			elif i == 5:
				self.current_fields[key] = ''
			elif i == 6:
				self.current_fields[key] = ''
			elif i == 7:
				self.current_fields[key] = sale.gains
		# Advance the row counter for the next sale item.
		self.current_row += 1

	def _updateFieldRow(self, rowStart, fieldList, sale: TaxableSale):
		rowEnd = rowStart + 8 # 8 fields in every row, arrays start at 0
		keysForCurrentRow = fieldList[rowStart:rowEnd]
		self.enterSaleItem(sale, keysForCurrentRow)
		return rowStart

	def _writePage(self):
		fillpdfs.write_fillable_pdf('f8949.pdf', 'output_{}.pdf'.format(self.current_page), self.current_fields, flatten=False)

	def _openNewPage(self, page):
		self.current_page += 1
		return fillpdfs.get_form_fields('f8949.pdf', sort=False, page_number=page)

	def close(self):
		self._writePage()

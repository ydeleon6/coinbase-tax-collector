import json
import requests
from http.client import HTTPException
from urllib.parse import urljoin

class TransactionPage:
	def __init__(self) -> None:
		self.afterDate = None
		self.beforeDate = None
		self.size = 100
		self.nextPageToken = None

INDEXER_URL = 'https://algoindexer.algoexplorerapi.io'

class AccountsIndexer:
	def __init__(self, address: str) -> None:
		self.baseUrl = urljoin(INDEXER_URL, '/v2/accounts/'+address)
		self.address = address

	def isEmpty(self, option):
		return option == '' or option is None

	def getAccountTransactions(self, options: TransactionPage):
		"""
		Reads a list of transactions from the Algorand Indexer API with the given page options.
		"""
		url = self.baseUrl + '/transactions?'

		if self.isEmpty(options.beforeDate) is False:
			url += '&before-time={}'.format(options.beforeDate)

		if self.isEmpty(options.size) is False:
			url += '&limit={}'.format(options.size)

		if self.isEmpty(options.nextPageToken) is False:
			url += '&next={}'.format(options.nextPageToken)

		print(url)
		res = requests.get(url)

		if res.ok is False:
			raise HTTPException("Failed to read transactions for account. HTTP Status {}".format(res.status_code))
		body = json.loads(res.content)
		return body

	def saveTransactions(self, year, filepath):
		"""
		Saves all transactions up to the specified year to a file. The transactions are 
		sorted chronologically.
		"""
		nextYear = int(year) + 1
		options = TransactionPage()
		#options.afterDate = '{}-01-01T00:00:00Z'.format(year)
		options.beforeDate = '{}-01-01T00:00:00Z'.format(nextYear)

		result = self.getAccountTransactions(options)
		options.nextPageToken = result.get('next-token')
		allTransactions = result.get('transactions')

		while options.nextPageToken is not None:
			result = self.getAccountTransactions(options)
			options.nextPageToken = result.get('next-token')
			transactions = result.get('transactions')
			allTransactions.extend(transactions)

		def getBlockTime(txn):
			return int(txn.get('round-time'))

		allTransactions.sort(key=getBlockTime)

		with open(filepath, 'w') as outputFile:
			for txn in allTransactions:
				txnStr = json.dumps(txn)
				outputFile.write(txnStr)
				outputFile.write("\n")

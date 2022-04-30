import json
import requests
from datetime import datetime
from http.client import HTTPException
from urllib.parse import urljoin


class TransactionPage:
	def __init__(self) -> None:
		self.afterDate = None
		self.beforeDate = None
		self.size = 100
		self.nextPageToken = None

class AlgorandTransaction:
	def __init__(self, txnDict):
		self.timestamp = datetime.fromtimestamp(txnDict.get('round-time'))
		self.fee = txnDict.get('fee')
		self.id = txnDict.get('id')
		self.senderRewards = int(txnDict.get('sender-rewards'))
		self.txnType = txnDict.get('tx-type')
		self.closeRewards = int(txnDict.get('close-rewards'))
		self.closingAmount = int(txnDict.get('closing-amount'))
		self.confirmedRound = int(txnDict.get('confirmed-round'))
		self.firstValid = int(txnDict.get('first-valid'))
		self.genesisHash = txnDict.get('genesis-hash')
		self.genesisId = txnDict.get('genesis-id')
		self.intraRoundOffset = txnDict.get('intra-round-offset')
		self.lastValid = txnDict.get('last-valid')
		self.transactionInfo = self.getTransaction(txnDict)
		self.receiverRewards = int(txnDict.get('receiver-rewards'))
		self.sender = txnDict.get('sender')
		self.signature = txnDict.get('signature')

	def getTransaction(self, txnDict: dict):
		if txnDict.get('asset-transfer-transaction') is not None:
			return txnDict.get('asset-transfer-transaction')
		if txnDict.get('payment-transaction') is not None:
			return txnDict.get('payment-transaction')
		if txnDict.get('application-transaction') is not None:
			return txnDict.get('application-transaction')

		raise Exception('Unknown transaction type')

def isEmpty(option):
	return option == '' or option is None

INDEXER_URL = 'https://algoindexer.algoexplorerapi.io'

def getAccountTransactions(address, options: TransactionPage):
	"""
	Reads a list of transactions from the Algorand Indexer API with the given page options.
	"""
	baseTransactionUrl = urljoin(INDEXER_URL, '/v2/accounts/'+address+'/transactions')
	if isEmpty(options.afterDate) is False:
		baseTransactionUrl += '?after-time={}'.format(options.afterDate)

	if isEmpty(options.beforeDate) is False:
		baseTransactionUrl += '&before-time={}'.format(options.beforeDate)

	if isEmpty(options.size) is False:
		baseTransactionUrl += '&limit={}'.format(options.size)

	if isEmpty(options.nextPageToken) is False:
		baseTransactionUrl += '&next={}'.format(options.nextPageToken)

	print(baseTransactionUrl)
	res = requests.get(baseTransactionUrl)
	if res.ok is False:
		raise HTTPException("Failed to read transactions for account. HTTP Status {}".format(res.status_code))
	body = json.loads(res.content)
	return body


def saveTransactions(address, year, filepath):
	"""
	Saves all transactions to a file. The transactions are 
	sorted chronologically.
	"""
	nextYear = int(year) + 1
	options = TransactionPage()
	options.afterDate = '{}-01-01T00:00:00Z'.format(year)
	options.beforeDate = '{}-01-01T00:00:00Z'.format(nextYear)

	result = getAccountTransactions(address, options)
	options.nextPageToken = result.get('next-token')
	allTransactions = result.get('transactions')

	while options.nextPageToken is not None:
		result = getAccountTransactions(address, options)
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

def readTransactions(filepath):
	"""
	Reads all transactions from the file.
	"""
	transactions = []
	with open(filepath, 'r') as infile:
		for line in infile.readlines():
			txnDict = json.loads(line)
			poop = AlgorandTransaction(txnDict)
			transactions.append(poop)
	return transactions

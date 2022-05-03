import json
from datetime import datetime
from itertools import groupby
from operator import contains
from ..common import TaxableTransaction, CryptoAccount, CryptoAssetBalance


class AccountTransaction:
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
		self.group = txnDict.get('group')

	def getTransaction(self, txnDict: dict):
		if txnDict.get('asset-transfer-transaction') is not None:
			return txnDict.get('asset-transfer-transaction')
		if txnDict.get('payment-transaction') is not None:
			return txnDict.get('payment-transaction')
		if txnDict.get('application-transaction') is not None:
			return txnDict.get('application-transaction')

		raise Exception('Unknown transaction type')


class AlgorandTransaction(TaxableTransaction):
	"""A taxable event on the Algorand blockchain."""
	def __init__(self, timestamp, type, assetName, quantity, currency, spotPrice, subtotal, total, fees):
		super().__init__(timestamp, type, assetName, quantity, currency, spotPrice, subtotal, total, fees)
		self.groupedTxns = dict()

class AlgorandAccount(CryptoAccount):
	def __init__(self, address, tax_method=0) -> None:
		super().__init__(tax_method)
		self.address: str = address
		self.transactions: list[AccountTransaction] = []
		self.groupedTxns: list[TransactionGroup] = []

	def load_from_csv(self, filepath):
		"""
		Reads all transactions from the file into Python objects.
		"""
		with open(filepath, 'r') as infile:
			for line in infile.readlines():
				txnDict = json.loads(line)
				accountTxn = AccountTransaction(txnDict)
				self.transactions.append(accountTxn)
		return self

	def group(self):
		"""Group transactions into smaller sublists by their group identifier (if-present)."""
		for key, result in groupby(self.transactions, key=lambda txn: txn.group):
			if key is None:
				continue #we'll do this later.
			groupedTxns = list(result)
			groupedTxns.sort(key=lambda txn: txn.timestamp)
			self.groupedTxns.append(TransactionGroup(key, groupedTxns))
		return self

class TransactionGroup:
	"""A group of AccountTransactions submitted in a single account signature."""
	def __init__(self, group: str, transactions: list[AccountTransaction]) -> None:
		self.group = group
		self.transactions = transactions

	def group_by_type(self):
		grouped = dict()
		for key,result in groupby(self.transactions, key=lambda txn: txn.txnType):
			grouped[key] = result #list(result)
		return grouped

	def convert_to_tax_event(self):
		print("-----------")
		print(self.group)
		print(len(self.transactions))

class Strategy:
	def can_handle(self, txnGroup: TransactionGroup):
		return False

class YieldlyStrategy(Strategy):
	def __init__(self) -> None:
		super().__init__()
		self.applicationId = 233725850

	def can_handle(self, txnGroup: TransactionGroup):
		txns = txnGroup.group_by_type()
		if contains(txns, 'appl'):
			for txn in txns:
				innerTxn = txn.getTransaction()
				if innerTxn['application-id'] == self.applicationId:
					return True
		return False

class GroupAnalyzer:
	"""Look at the group of transactions and try to pinpoint if
	a taxable transaction happened."""
	def __init__(self, txnGroup: TransactionGroup) -> None:
		self.txnGroup = txnGroup
from cryptocurrency.algorand import api, models

ADDRESS = '2YMNE7EDI2IHL7DFF3S5KTHYEY5QEZUNCOBVZPL5YJHNHSARBG6MGCLONE'
algorandTransactionsFile = r'algo_transactions.txt'

accountIndexer = api.AccountsIndexer(ADDRESS)

# Save all the accounts transactions to a file.
# accountIndexer.saveTransactions(2021, algorandTransactionsFile)

account = models.AlgorandAccount(ADDRESS, 0)\
	.load_from_csv(algorandTransactionsFile)\
	.group()

# Read all transactions from the file into memory
for txnGroup in account.groupedTxns:
	txnGroup.convert_to_tax_event()

# On-chain taxable events aren't totally easy to gather. We have to know
# who is sending us stuff, and under what scenario. Like Coinbase, we are
# sent crypto as payments (income) vs. trading (short-sale).
# My javascript program has a rough idea, but you could check the apps.
# 1) check to see what the transaction is about
# 2) check the type
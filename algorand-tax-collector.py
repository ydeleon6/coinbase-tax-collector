from cryptocurrency.algorand import saveTransactions, readTransactions

def getAlgorandTransactions():
	address = '2YMNE7EDI2IHL7DFF3S5KTHYEY5QEZUNCOBVZPL5YJHNHSARBG6MGCLONE'
	algorandTransactionsFile = r'C:\\Sourcecode\\helper-scripts\\python\\algo_transactions.txt'
	saveTransactions(address, 2021, algorandTransactionsFile)
	algoTransactions = readTransactions(algorandTransactionsFile)
	print("Found {} transactions".format(len(algoTransactions)))
	return algoTransactions

algorandTransactions = getAlgorandTransactions()

# loop to get all transactions in memory, then sort and write to CSV.

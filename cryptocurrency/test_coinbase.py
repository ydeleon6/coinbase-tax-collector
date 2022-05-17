from cryptocurrency.coinbase import CoinbaseAccount
from cryptocurrency.utils import LIFO, FIFO

def getAccount(taxmethod):
    account = CoinbaseAccount(tax_method=taxmethod)
    account.load_transactions('capital-gains-test.csv')
    return account

def test_FIFO_capital_gains():
    # Arrange
    account = getAccount(FIFO)

    # Act
    totalGains = account.calculateCapitalGains()
    expectedGains = 40750.5

    # Assert
    assert totalGains == expectedGains

def test_LIFO_capital_gains():
    # Arrange
    account = getAccount(LIFO)

    # Act
    totalGains = account.calculateCapitalGains()
    expectedGains = 10500.5

    # Assert
    assert totalGains == expectedGains
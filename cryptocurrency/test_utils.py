import logging
from datetime import datetime
from cryptocurrency.utils import PurchasesQueue, getCostBasis
from cryptocurrency.models import Queue, FIFO, LIFO, Purchase, \
    PurchasesQueue, CoinbaseTransaction

def test_fifo_queue():
    queue = Queue(FIFO)
    queue.enqueue(1)
    queue.enqueue(2)
    queue.enqueue(3)

    result = queue.dequeue()

    assert result == 1
    assert queue.peek() == 2

def test_lifo_queue():
    queue = Queue(LIFO)
    queue.enqueue(1)
    queue.enqueue(2)
    queue.enqueue(3)

    result = queue.dequeue()

    assert result == 3
    assert queue.peek() == 2

def test_purchases_fifo_costbasis():
    asset = "BTC"
    purchases = PurchasesQueue(asset, FIFO)
    purchases.enqueue(Purchase(100, 1))
    purchases.enqueue(Purchase(300, 1))
    amountSold = 1.5
    sale = CoinbaseTransaction(datetime.now(), "Sell", asset,\
        amountSold, "USD", 600, 900, 900, 0, "")
    (costBasis, qtyRemaining) = getCostBasis(purchases, sale)
    
    assert costBasis == 250
    assert purchases.length == 1
    assert qtyRemaining == 0

def test_purchases_lifo_costbasis():
    asset = "BTC"
    purchases = PurchasesQueue(asset, LIFO)
    purchases.enqueue(Purchase(100, 1))
    purchases.enqueue(Purchase(300, 1))
    amountSold = 1.5
    sale = CoinbaseTransaction(datetime.now(), "Sell", asset,\
        amountSold, "USD", 600, 900, 900, 0, "")
    (costBasis, qtyRemaining) = getCostBasis(purchases, sale)
    
    assert costBasis == 350
    assert purchases.length == 1
    assert qtyRemaining == 0

def test_purchases_missing_txns(caplog):
    asset = "ETH"
    amountSold = 3
    purchases = PurchasesQueue(asset, FIFO)
    purchases.enqueue(Purchase(1000, 1))
    purchases.enqueue(Purchase(3000, 1))

    sale = CoinbaseTransaction(datetime.now(), "Sell", asset,\
        amountSold, "USD", 600, 900, 900, 0, "") 

    with caplog.at_level(logging.ERROR):
        (costBasis, qtyRemaining) = getCostBasis(purchases, sale)

    assert 'Looking for 1.0 ETH in your purchases/receives. '+\
        'Found 2.0 of 3.0 so far. Perhaps missing a transaction?' in caplog.text
    assert qtyRemaining == 1

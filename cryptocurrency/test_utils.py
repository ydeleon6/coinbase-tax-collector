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
    costBasis = getCostBasis(purchases, sale)
    
    assert costBasis == 250
    assert purchases.length == 1

def test_purchases_lifo_costbasis():
    asset = "BTC"
    purchases = PurchasesQueue("BTC", LIFO)
    purchases.enqueue(Purchase(100, 1))
    purchases.enqueue(Purchase(300, 1))
    amountSold = 1.5
    sale = CoinbaseTransaction(datetime.now(), "Sell", asset,\
        amountSold, "USD", 600, 900, 900, 0, "")
    costBasis = getCostBasis(purchases, sale)
    
    assert costBasis == 350
    assert purchases.length == 1

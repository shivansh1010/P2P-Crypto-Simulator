from constants import *
from uuid import uuid4
# from peer import Peer

class Transaction:
    def __init__(self, ts, amount, sender, receiver):
        self.id = uuid4()
        self.type = "normal"
        self.timestamp = ts
        self.sender_id = sender.id
        self.receiver_id = receiver.id
        self.size = TRANSACTION_SIZE
        self.amount = amount

        def __str__(self): 
             return (
            f"{self.id}: {self.sender_id} pays {self.receiver_id} {self.amount} coins."
        )                 
           

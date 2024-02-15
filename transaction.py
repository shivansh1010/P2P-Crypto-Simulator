from constants import *
from uuid import uuid4
# from node import Node

class Transaction:
    def __init__(self, ts, amount, sender_id, receiver_id):
        self.id = uuid4()
        self.timestamp = ts
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.size = TRANSACTION_SIZE
        self.amount = amount

        def __str__(self): 
             return (
            f"{self.id}: {self.sender_id} pays {self.receiver_id} {self.amount} coins."
        )                 
           

from constants import *
from uuid import uuid4

class Transaction:
    def __init__(self, amount, sender, receiver):
        self.id = uuid4()
        self.type = "normal"
        self.sender_id = sender.id
        self. receiver_id = receiver.id
        self.size = TRANSACTION_SIZE
        self.amount = amount

        def __str__(self): 
             return (
            f"{self.id}: {self.sender_id} pays {self.receiver_id} "
            f"{self.amount} coins."
        )                 
           

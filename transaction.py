"""module to represent a transaction in the blockchain network"""

from uuid import uuid4


class Transaction:
    """class to represent a transaction in the blockchain network"""
    def __init__(self, ts, amount, sender_id, receiver_id):
        """"method to initialize attributes of transaction"""
        self.id = uuid4()
        self.timestamp = ts
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.amount = float(amount)

    def __str_v2__(self):
        if self.sender_id is None:
            return f"{self.id}: {self.receiver_id} mines {self.amount} coins"
        return f"{self.id}: {self.sender_id} pays {self.receiver_id} {self.amount} coins"

    def __str__(self):
        if self.sender_id is None:
            return f"{self.receiver_id} mines {self.amount} coins"
        return f"{self.sender_id} pays {self.receiver_id} {self.amount} coins"

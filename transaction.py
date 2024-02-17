from uuid import uuid4


class Transaction:
    def __init__(self, ts, amount, sender_id, receiver_id):
        self.id = uuid4()
        self.timestamp = ts
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.amount = float(amount)

    def __str__(self): 
        if self.sender_id == None:
            return (f"{self.id}: {self.receiver_id} mines {self.amount} coins")
        return (f"{self.id}: {self.sender_id} pays {self.receiver_id} {self.amount} coins")                 
           

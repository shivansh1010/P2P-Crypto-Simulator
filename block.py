from uuid import uuid4
import time
from hashlib import sha256

class Block:
    def __init__(self, prev_hash, miner_id):
        self.id = uuid4()
        self.type = "normal"
        self.timestamp = time.time()
        self.prev_hash = prev_hash
        self.txns = set()
        self.size = 1
        self.miner_id = miner_id
        self.hash = ""
        self.txn_hash = ""
        self.balance = list()

class GenesisBlock:
    def __init__(self, n):
        self.id = uuid4()
        self.type = "genesis"
        self.timestamp = time.time()
        self.balance = [1000]*n

    def get_hash(self):
        return sha256(str(self.id).encode()).hexdigest()

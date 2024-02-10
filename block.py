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

    def blockHash(self):
        if self.hash != "":
            return self.hash
        
        if self.txn_hash == "":
            txns_string = ""
            for txn in self.txns:
                txns_string += str(txn) 
            self.txn_hash = sha256(txns_string.encode()).hexdigest()  
        
        block_content = str(self.id) + self.prev_hash + self.txn_hash
        self.hash = sha256(block_content.encode()).hexdigest()

        return self.hash
        

class GenesisBlock:
    def __init__(self, n):
        self.id = uuid4()
        self.type = "genesis"
        self.timestamp = time.time()
        self.balance = [1000]*n

    def get_hash(self):
        return sha256(str(self.id).encode()).hexdigest()

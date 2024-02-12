from uuid import uuid4
import time
from hashlib import sha256

from constants import *

class Block:
    def __init__(self, timestamp, prev_hash, miner_id):
        self.id = uuid4()
        self.type = "normal"
        self.timestamp = timestamp
        self.prev_hash = prev_hash
        self.txns = set()
        self.size = 1
        self.miner_id = miner_id
        self.hash = ""
        self.txn_hash = ""
        self.mined_amount = 0
        self.balance = list()

    def block_Hash(self):
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
    
    def add_txn(self, txn):
        if(len(self.txns) >= self.size-1):
            print("Block is full")
        else:
            self.txns.add(txn)
            self.mined_amount += TXN_FEE
        

class GenesisBlock:
    def __init__(self, n):
        self.id = uuid4()
        self.type = "genesis"
        self.timestamp = time.time()
        self.balance = [1000]*n

    def block_hash(self):
        return sha256(str(self.id).encode()).hexdigest()

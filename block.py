from uuid import uuid4
import time
from hashlib import sha256

from constants import *

class Block:
    def __init__(self, creation_time, prev_hash, height, transactions, mine_time = -1):

        self.prev_hash = prev_hash
        self.creation_time = creation_time
        self.height = height # uuid4() # -> using id so that we can use this at height
        self.txns = transactions

        # these are not included in the block-hash
        self.hash = self.block_hash() # unique ID for every block
        self.mine_time = mine_time

    def block_hash(self):
        # txns_string = ""
        # for txn in self.txns:
        #     txns_string += str(txn) 
        # txn_hash = sha256(txns_string.encode()).hexdigest()  
        
        # block_content = str(self.height) + str(self.prev_hash) + txn_hash
        self.hash = sha256(str(self).encode()).hexdigest()[:7]

        return self.hash
    
    def __str__(self):
        return (
            f"Block {self.height} {self.prev_hash} {self.creation_time} {[str(txn) for txn in self.txns]}"
        )
    
    # def add_txn(self, txn):
    #     if(len(self.txns) >= self.size-1):
    #         print("Block is full")
    #     else:
    #         self.txns.add(txn)
    #         self.mined_amount += TXN_FEE
        

# class GenesisBlock:
#     def __init__(self, n):
#         self.id = uuid4()
#         self.type = "genesis"
#         self.timestamp = time.time()
#         self.balance = [1000]*n

#     def block_hash(self):
#         return sha256(str(self.id).encode()).hexdigest()

from hashlib import sha256


class Block:
    def __init__(self, creation_time, prev_hash, height, transactions, mine_time = 0.0):

        self.prev_hash = prev_hash
        self.creation_time = creation_time
        self.height = height 
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
        self.hash = sha256(str(self).encode()).hexdigest()[:10]

        return self.hash
    
    def __str__(self):
        return (
            f"Block {self.height} {self.prev_hash} {self.creation_time} {[str(txn) for txn in self.txns]}"
        )

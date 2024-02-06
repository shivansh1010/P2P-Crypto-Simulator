from uuid import uuid4

class Block:
    def __init__(self, prev_hash, miner_id):
        self.id = uuid4()
        self.type = "normal"
        self.prev_hash = prev_hash
        self.txns = set()
        self.size = 1
        self.miner_id = miner_id
        self.hash = ""
        self.txn_hash = ""
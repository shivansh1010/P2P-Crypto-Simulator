"""Module to represent a block in the blockchain"""

from hashlib import sha256


class Block:
    """Class to represent a block in the blockchain"""
    def __init__(self, creation_time, prev_hash, height, transactions, mine_time=0.0):

        self.prev_hash = prev_hash
        self.creation_time = creation_time
        self.height = height  # height of block in chain from genesis block
        self.txns = transactions

        # these are not included in the block-hash
        self.hash = self.block_hash()  # unique ID for every block
        self.mine_time = mine_time

    def block_hash(self):
        """method to calculate hash of a block"""
        # txns_string = ""
        # for txn in self.txns:
        #     txns_string += str(txn)
        # txn_hash = sha256(txns_string.encode()).hexdigest()

        # block_content = str(self.height) + str(self.prev_hash) + txn_hash
        self.hash = sha256(str(self).encode()).hexdigest()[:32]

        return self.hash

    def __str__(self):
        return f"Block {self.height} {self.prev_hash} {self.creation_time} {[txn.__str_v2__() for txn in self.txns]}"

    def __str_v2__(self):
        return f"{self.hash},{self.height},{self.mine_time},{len(self.txns)},{self.prev_hash}"

    @property
    def hash_s(self):
        """Shortened hash for display"""
        return self.hash[:7]

    @property
    def prev_hash_s(self):
        """Shortened prev_hash for display"""
        return self.prev_hash[:7] if self.prev_hash != -1 else -1

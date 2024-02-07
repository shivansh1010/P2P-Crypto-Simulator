from block import GenesisBlock
from copy import deepcopy

class Blockchain:
    def __init__(self, n):
        self.genesis = GenesisBlock(n)
        self.num_blocks = 1
        self.chain = [self.genesis]

    def get_last_block(self):
        return self.chain[-1]
    
    def add_block(self, block):
        new_block = deepcopy(block)
        
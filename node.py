import random
import string
import numpy as np
from collections import deque
from constants import *
from transaction import Transaction
from events import Event
from block import Block
from collections import defaultdict
import time
from copy import deepcopy
from math import isclose


class Node:
    def __init__(self, id, is_slow, is_low_cpu, network, genesis):
        self.id = id
        self.is_slow = is_slow
        self.is_low_cpu = is_low_cpu
        # self.coins = 1000
        self.neighbors = set()
        self.txn_pool = set() # Set of transactions that have to be processed
        self.txn_registry = set() # Set of all the transactions seen 
        self.pending_blocks = set() # Set of blocks whose previous block hasn't arrived

        self.hashing_power = 0
        self.network = network

        # self.balances = defaultdict(dict) # Block_hash -> {Node_id -> Balance} # only mined blocks are added here
        self.block_hash_being_mined = None
        self.genesis_block = deepcopy(genesis)

        # Hash of Leaf Block of the Longest Branch in blockchain. We'll always mine with this block as parent.
        self.longest_leaf_hash = self.genesis_block.hash 
        self.block_registry = {self.genesis_block.hash: self.genesis_block} # Hash -> Block

    def __str__(self):
        return f"{self.id}"

    def add_neighbor(self, neighbor):
        self.neighbors.add(neighbor)

    def remove_neighbor(self, neighbor):
        if neighbor in self.neighbors:
            self.neighbors.remove(neighbor)

    def get_neighbors(self):
        return list(self.neighbors)
    


    def compute_delay(self, msg_size, receiver_id):
        if self.is_slow or self.network.nodes[receiver_id].is_slow:
            link_speed = self.network.slow_node_link_speed
        else:
            link_speed = self.network.fast_node_link_speed

        transmission_delay = (msg_size * 8) / (link_speed * 1024)
        queueing_delay = np.random.exponential((float(self.network.queuing_delay_constant)) / (link_speed * 1024))

        return self.network.prop_delay + transmission_delay + queueing_delay

    def transaction_create(self):
        """method to add an txn_create event in the FUTURE"""
        event_timestamp = self.network.time + np.random.exponential(self.network.mean_interarrival_time_sec)
        self.network.event_queue.push(Event(event_timestamp, self.id, self.id, "txn_create", data=None))

    def transaction_create_handler(self, event_timestamp):
        """method to create a txn and handle it"""
        receiver_id = random.choice(self.get_neighbors())
        while self.id == receiver_id:
            receiver_id = random.choice(self.get_neighbors())
        amount = round(random.uniform(0, float(self.get_amount(self.id))), 6)
        txn = Transaction(event_timestamp, amount, self.id, receiver_id)

        print(str(txn))
        self.txn_pool.add(txn)
        self.txn_registry.add(txn)
        self.transaction_broadcast(txn)
        self.transaction_create()

    def transaction_receive_handler(self, txn, source_node_id):
        """method to handle txn receive event"""
        if txn in self.txn_registry:
            return
        self.txn_pool.add(txn)
        self.txn_registry.add(txn)
        self.transaction_broadcast(txn, source_node_id)

    def transaction_broadcast(self, txn, source_node_id=None):
        """ broadcast fuction. Broadcast txn to all neighbours, except the node from which it came from"""
        for node_id in self.get_neighbors():
            # dont send back to the node from which txn came
            if source_node_id and node_id == source_node_id:
                continue
            delay = self.compute_delay(self.network.transaction_size, node_id)
            self.network.event_queue.push(Event(txn.timestamp + delay, self.id, node_id, "txn_recv", data=txn))

    def get_amount(self, node):
        """return balance of node, obtained from traversing blockchain"""
        # TODO: obtain from traversing blockchain
        # return node.coins

        total_balance = 0.0
        curr_block = self.longest_leaf_hash
        while curr_block != -1:
            for txn in self.block_registry[curr_block].txns:
                if node == txn.receiver_id:
                    total_balance += txn.amount
                if node == txn.sender_id:
                    total_balance -= txn.amount
            curr_block = self.block_registry[curr_block].prev_hash
        return total_balance
    
    def get_balances(self, blockHash):
        balances = {}
        curr_block = blockHash
        while curr_block != -1:
            for txn in self.block_registry[curr_block].txns:
                balances[txn.receiver_id] = balances.get(txn.receiver_id, 0) + txn.amount
                balances[txn.sender_id] = balances.get(txn.sender_id, 0) - txn.amount
            curr_block = self.block_registry[curr_block].prev_hash
        return balances
    
    def is_transaction_valid(self, txn):
        """method to check if txn is valid"""
        return True



    # def updates_balances(self, hash):
    #     """"""
    #     if hash in self.balances: # already included in the balances
    #         return
    #     block_balance = {}
    #     parent_hash = self.block_registry[hash].prev_hash
    #     if parent_hash not in self.balances:
    #         parent_balance = self.balances[parent_hash]
    #         for txn in self.block_registry[hash].txns:
    #             if txn.sender_id != -1:
    #                 block_balance[txn.sender_id] -= txn.amount
    #                 block_balance[txn.receiver_id] += txn.amount
        

    def block_create(self):
        """method to create a block and start mining"""

        parent_block_hash = self.longest_leaf_hash
        parent_block_height = self.block_registry[parent_block_hash].height
        coinbase_txn = Transaction(self.network.time, self.network.mining_reward, None, self.id)
        txns_to_include = [coinbase_txn]

                
        # update the balances cache
        # true_balances = self.balances[parent_block_hash].copy()
        # for txn in self.txn_pool:
        #     sender = txn.sender_id
        #     receiver = txn.receiver_id
        #     true_balances[sender] -= txn.amount
        #     true_balances[receiver] += txn.amount
        # self.balances[parent_block_hash] = true_balances


        true_balances = self.get_balances(parent_block_hash)        
        # true_balances = self.balances[parent_block_hash].copy()
        for txn in self.txn_pool:
            # Assuming honest block creator, Validate transaction
            sender = txn.sender_id
            receiver = txn.receiver_id
            
            if true_balances.get(sender, 0) >= txn.amount: # care about the floating point comparison error
                # true_balances[sender] = true_balances.get(sender, 0) - txn.amount
                # true_balances[receiver] = true_balances.get(receiver, 0) + txn.amount
                txns_to_include.append(txn)
            # else:
            #     print(f"Invalid Transaction: while block creation, skipping this transaction")
            
            if len(txns_to_include) >= self.network.max_txn_in_block:
                break

        block = Block(self.network.time, parent_block_hash, parent_block_height + 1, txns_to_include)
        timestamp = self.network.time + np.random.exponential(self.network.mean_mining_time_sec / self.hashing_power) # use hashing power here
        
        self.network.event_queue.push(Event(timestamp, self.id, self.id, "blk_mine", data=block))
        self.block_hash_being_mined = block.hash

    def block_mine_handler(self, block):
        """method to create a block and handle it"""

        # the next two if condition are equivalent in this simulation
        # check if this block is still on the same longest chain
        if block.hash != self.block_hash_being_mined:
            return
        if block.height <= self.block_registry[self.longest_leaf_hash].height:
            return



        # update the balances cache
        parent_block_hash = self.longest_leaf_hash
        true_balances = self.get_balances(parent_block_hash)
        # true_balances = self.balances[parent_block_hash].copy()
        # # UNCOMMENT
        # for txn in self.txn_pool:
        #     sender = txn.sender_id
        #     receiver = txn.receiver_id
        #     true_balances[sender] -= txn.amount
        #     true_balances[receiver] += txn.amount
        # self.balances[block.hash] = true_balances


        # block sucessfully mined now
        block.mine_time = self.network.time
        self.block_registry[block.hash] = block
        self.longest_leaf_hash = block.hash


        for txn in list(block.txns)[1:]:
            self.txn_pool.remove(txn)

        print(str(block.txns[0]))
        self.block_broadcast(block)
        self.block_create()

    def process_pending_blocks(self, block):
        for pending_blk in self.pending_blocks:
            if pending_blk.prev_hash == block.hash:
                self.pending_blocks.remove(pending_blk)
                self.block_receive_handler(pending_blk, self.id)
                break
    
    def block_receive_handler(self, block, source_node_id):
        """method to handle block receive event"""

        # print(f'node {self.id} blk_recv {block.hash}')

        if self.id == source_node_id:
            return
        
        if block.hash in self.block_registry:
            return
        
        last_block_hash = self.longest_leaf_hash
        last_block = self.block_registry[last_block_hash]

        # Add to pending blocks if previous block not received
        if block.prev_hash not in self.block_registry:
            self.pending_blocks.add(block)
            return
        
        # Validate Block
        if not self.is_block_valid(block):
            return
         
        # Add to block registry
        self.block_registry[block.hash] = deepcopy(block)

        # Check if this is a parent of some pending block and add them
        self.process_pending_blocks(block)

        # Find the longest chain and add the block accordingly
        if block.height > last_block.height:
            if block.prev_hash != last_block_hash:
                print(f"{self.id} Changing mining branch from {self.longest_leaf_hash} to {block.prev_hash}")
            self.longest_leaf_hash = block.hash

        # Restart block mining
        self.block_hash_being_mined = None
        self.block_create()
        
        # Broadcast Block
        self.block_broadcast(block, source_node_id)
       

    def is_block_valid(self, block):
        """method to check if block is valid"""
        # last_block_hash = self.blockchain_leaves[-1]
        # last_block = self.block_registry[last_block_hash]
        # true_balances = last_block.balances.copy()


        # Validate Previous Hash
        # if block.prev_hash not in self.block_registry:
        #     print(f"Invalid Block: Previous hash not found: {block.height}, {block.prev_hash}")
        #     return False
        
        # Validate Previous Block height
        prev_blk_hash = block.prev_hash
        prev_blk = self.block_registry[prev_blk_hash]
        if prev_blk.height + 1 != block.height:
            print(f"Invalid Block: Invalid Index {block.height}")
            return False
        
        # Validate Hash
        if block.hash != block.block_hash():
            print(f"Invalid Block: Hash mismatch {block.height}")
            return False

        # Validate Coinbase Transaction
        if len(block.txns) < 1:
            print(f"Invalid Block: No Transactions {block.height}")
            return False
        
        if len(block.txns) > self.network.max_txn_in_block:
            print(f"Invalid Block: Block size exceeded limit {block.height}")
            return False
        
        # Check if the mining reward is correct
        coinbase_txn = block.txns[0]
        if coinbase_txn.amount > self.network.mining_reward: # Max Mining Reward
            print(f"Invalid Block: Mining fee more than maximum mining fee, {coinbase_txn}")
            return False
        

        # Validate Transactions
        true_balances = self.get_balances(prev_blk_hash)
        # true_balances = self.balances[prev_blk_hash].copy()
        for txn in block.txns[1:]:
            sender = txn.sender_id
            receiver = txn.receiver_id
            if true_balances.get(sender, 0) < txn.amount:
                print(f"Invalid Block: insufficient sender({sender}) balance, cache:{true_balances[sender]}, txn:{txn.amount}")
                return False
            
            # true_balances[sender] -= txn.amount
            # true_balances[receiver] += txn.amount

        # Block Valid, Update the balances
        # self.balances[block.hash] = true_balances
        
        # # Validate Balances
        # for node, balance in block.balances.items():
        #     if(true_balances[node]!=balance):
        #         print(f"Invalid Block: Wrong Balance of node {node.id}")
        #         return False
        
        return True
            

    def block_broadcast(self, block, source_node_id=None):
        """method to broadcast block"""
        # print(f'node {self.id} sending to neighbors')
        for node_id in self.get_neighbors():
            if source_node_id and node_id == source_node_id:
                continue
            block_size = len(block.txns) * self.network.transaction_size
            delay = self.compute_delay(block_size, node_id)
            self.network.event_queue.push(Event(self.network.time + delay, self, node_id, "blk_recv", data=block))

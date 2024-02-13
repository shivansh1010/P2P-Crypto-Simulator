import random
import string
import numpy as np
from collections import deque
from constants import *
from transaction import Transaction
from events import Event
from block import Block, GenesisBlock
import time


class Node:
    def __init__(self, id, is_slow, is_low_cpu, network):
        self.id = id
        self.is_slow = is_slow
        self.is_low_cpu = is_low_cpu
        self.coins = 1000
        self.neighbors = set()
        self.txn_pool = set()
        self.hashing_power = 0
        self.network = network
        self.balances = {} # Node -> Balance
     
        self.genesis_block = Block(self.network.time, -1, -1, [])

        self.blockchain_leaves = [self.genesis_block.hash] # Hash of block_chain leaves
        self.block_registry = {self.genesis_block.hash: self.genesis_block} # Hash -> Block
        

    def add_neighbor(self, neighbor):
        self.neighbors.add(neighbor)

    def remove_neighbor(self, neighbor):
        if neighbor in self.neighbors:
            self.neighbors.remove(neighbor)

    def get_neighbors(self):
        return list(self.neighbors)
    

    def compute_delay(self, msg_size, receiver):
        if(self.is_slow or receiver.is_slow):
            link_speed = self.network.slow_node_link_speed
        else:
            link_speed = self.network.fast_node_link_speed

        transmission_delay = (msg_size * 8) / (link_speed * 1024)
        queueing_delay = np.random.exponential((float(self.network.queuing_delay_constant)) / (link_speed * 1024))

        return self.network.prop_delay + transmission_delay + queueing_delay

    def transaction_create(self):
        """method to add an txn_create event in the FUTURE"""
        event_timestamp = self.network.time + np.random.exponential(self.network.mean_interarrival_time_sec)
        self.network.event_queue.push(Event(event_timestamp, self, self, "txn_create", data=None))

    def transaction_create_handler(self, event_timestamp):
        """method to create a txn and handle it"""
        receiver = random.choice(self.get_neighbors())
        while self.id == receiver.id:
            receiver = random.choice(self.get_neighbors())
        amount = round(random.uniform(0, self.get_amount(self)), 6)
        txn = Transaction(event_timestamp, amount, self, receiver)

        self.txn_pool.add(txn)
        self.transaction_broadcast(txn)
        self.transaction_create()

    def transaction_receive_handler(self, txn, source_node):
        """method to handle txn receive event"""
        if txn in self.txn_pool:
            return
        self.txn_pool.add(txn)
        self.transaction_broadcast(txn, source_node)

    def transaction_broadcast(self, txn, source_node=None):
        """ broadcast fuction. Broadcast txn to all neighbours, except the node from which it came from"""
        for node in self.get_neighbors():
            # dont send back to the node from which txn came
            if source_node and node.id == source_node.id:
                continue
            delay = self.compute_delay(self.network.transaction_size, node)
            self.network.event_queue.push(Event(txn.timestamp + delay, self, node, "txn_recv", data=txn))


    def get_amount(self, node):
        """return balance of node, obtained from traversing blockchain"""
        # TODO: obtain from traversing blockchain
        return node.coins
    
    def is_transaction_valid(self, txn):
        """method to check if txn is valid"""
        return True




    def block_create(self):
        """method to add an blk_create event in the FUTURE"""

        timestamp = self.network.time + np.random.exponential(self.network.mean_mining_time_sec)
        self.network.event_queue.push(
            Event(timestamp, self, self, "blk_create", data=None)
        )

    def block_create_handler(self, event_timestamp):
        """method to create a block and handle it"""
        txns_to_include = []
        prev_hash = ''
        block = Block(event_timestamp, -1, -1, [])

        for txn in list(block.txns)[1:]:
            self.txn_pool.remove(txn)
        self.block_broadcast(block)
        self.block_create()

    def block_receive_handler(self, block, source_node):
        """method to handle block receive event"""
        if self.id == source_node.id:
            return
        # do something

    def is_block_valid(self, block):
        """method to check if block is valid"""
        last_block_hash = self.blockchain_leaves[-1]
        last_block = self.block_registry[last_block_hash]
        # true_balances = last_block.balances.copy()

        true_balances = self.balances.copy()

        # Validate Previous Hash
        # if(block.prev_hash != last_block_hash):
        #     print(f"Invalid Block: Previous hash mismatch: {block.id}")
        #     return False
        
        # Validate Hash
        if(block.hash != block.block_Hash()):
            print(f"Invalid Block: Hash mismatch {block.id}")
            return False

        # Validate Transactions
        for txn in block.txns[1:]:
            sender = txn.sender_id
            receiver = txn.receiver_id
            if(true_balances[sender] < txn.amount):
                print(f"Invalid Transaction: {txn}")
                return False
            
            true_balances[sender] -= txn.amount
            true_balances[receiver] += txn.amount
        
        # Validate Balances
        for node, balance in block.balances.items():
            if(true_balances[node]!=balance):
                print(f"Invalid Block: Wrong Balance of node {node.id}")
                return False
        
        return True
            

    def block_broadcast(self, block, source_node=None):
        """method to broadcast block"""
        for node in self.get_neighbors():
            if source_node and node.id == source_node.id:
                continue
            delay = 0 #self.compute_delay(self.network.block_size, node)
            self.network.event_queue.push(Event(self.network.time + delay, self, node, "blk_recv", data=block))

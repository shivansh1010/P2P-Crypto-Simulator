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

        balances = {}
        for node in self.network.nodes:
            balances[node] = self.network.node_starting_balance
        self.genesis_block = Block(self.network.time, -1, -1, balances)

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
        """method to create future txn"""
        receiver = random.choice(self.get_neighbors())
        while self.id == receiver.id:
            receiver = random.choice(self.get_neighbors())
        amount = round(random.uniform(0, self.get_amount(self)), 6)
        # time to wait before generating next txn
        # delay = np.random.exponential(self.simulator.txn_time)
        timestamp = self.network.time + np.random.exponential(self.network.mean_interarrival_time_sec)
        txn = Transaction(timestamp, amount, self, receiver)
        self.network.event_queue.push(Event(timestamp, self, self, "txn_create", data=txn))

    def transaction_create_handler(self, txn, source_node):
        """method to handle txn create event"""
        self.txn_pool.add(txn)
        self.transaction_broadcast(txn, source_node)
        self.transaction_create()

    def transaction_receive_handler(self, txn, source_node):
        """method to handle txn receive event"""
        if txn in self.txn_pool:
            return
        self.txn_pool.add(txn)
        self.transaction_broadcast(txn, source_node)

    def transaction_broadcast(self, txn, source_node=None):
        """ broadcast fuction """
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


    # def send_msg(self, event_queue, sender, receiver, msg, msg_type):
    #     if(msg_type == "txn"):
    #         msg_size = TRANSACTION_SIZE
    #     elif(msg_type == "block"):
    #         msg_size = msg.size

    #     delay = self.compute_delay(msg_size, receiver)
    #     new_event = Event(time.time() + delay, self, receiver, "msg_rcv", data=msg)
    #     event_queue.push(new_event)


    # def broadcast(self, event_queue, msg, msg_type):
    #     for receiver in  self.neighbors:
    #         self.send_msg(self, event_queue, receiver, msg, msg_type)

    # def receive_msg(self, event_queue, sender, msg, msg_type):
    #     if(msg_type == "txn"):
    #         if(msg in self.txn_pool):
    #             return
            
    #         self.txn_pool.add(msg)
    #         self.broadcast(event_queue, msg, msg_type)


    def block_create(self):
        """method to create FUTURE block"""
        # take current timestamp from "self.network.time"
        txns_to_include = []
        prev_hash = ''
        timestamp = self.network.time + np.random.exponential(self.network.mean_mining_time_sec)
        block = Block(timestamp, '', self.id)
        # check if the block is valid
        self.network.event_queue.push(
            Event(timestamp, self, self, "blk_create", data=block)
        )

    def block_create_handler(self, block, source_node):
        """method to handle block create event"""
        # do some checks
        for txn in list(block.txns)[1:]: # not to include reward txn
            self.txn_pool.remove(txn)
        self.block_broadcast(block, source_node)
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
        true_balances = last_block.balances

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

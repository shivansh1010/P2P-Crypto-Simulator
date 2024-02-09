import random
import string
import numpy as np
from collections import deque
from constants import *
from transaction import Transaction
from events import Event
import time


class Peer:
    def __init__(self, peer_id, is_slow, is_low_cpu, network):
        self.id = peer_id
        self.peer_id = peer_id
        self.is_slow = is_slow
        self.is_low_cpu = is_low_cpu
        self.coins = 1000
        self.neighbors = set()
        self.txn_pool = set()
        self.hashing_power = 0
        self.network = network

    def add_neighbor(self, neighbor):
        self.neighbors.add(neighbor)

    def remove_neighbor(self, neighbor):
        if neighbor in self.neighbors:
            self.neighbors.remove(neighbor)

    def get_neighbors(self):
        return list(self.neighbors)
    
    def compute_delay(self, msg_size, receiver):
        if(self.is_slow or receiver.is_slow):
            link_speed = SLOW_LINK_SPEED
        else:
            link_speed = FAST_LINK_SPEED

        queueing_delay = np.random.exponential((float(96)) / (link_speed * 1024))
        transmission_delay = (msg_size * 8) / (link_speed * 1024)

        total_delay = PROP_DELAY + queueing_delay + transmission_delay
        return total_delay

    def transaction_create(self):
        """method to create future txn"""
        receiver = random.choice(self.get_neighbors())
        while self.peer_id == receiver.peer_id:
            receiver = random.choice(self.get_neighbors())
        amount = round(random.uniform(0, self.get_amount(self)), 6)
        # time to wait before generating next txn
        # delay = np.random.exponential(self.simulator.txn_time)
        timestamp = time.time()
        txn = Transaction(timestamp, amount, self, receiver)
        self.network.event_queue.push(Event(txn.timestamp, self, "txn_create", data=txn))

    def transaction_create_handler(self, txn, source_node):
        """method to handle txn create event"""
        self.txn_pool.add(txn)
        self.transaction_broadcast(txn, source_node)
        self.transaction_create()

    def transaction_receive_handler(self, txn, source_node):
        """method to handle txn receive event"""
        self.txn_pool.add(txn)
        self.transaction_broadcast(txn, source_node)

    def transaction_broadcast(self, txn, source_node=None):
        """ broadcast fuction """
        for node in self.get_neighbors():
            if source_node and node.peer_id == source_node.peer_id:
                continue
            delay = self.compute_delay(TRANSACTION_SIZE, node)
            self.network.event_queue.push(Event(txn.timestamp + delay, node, "txn_recv", data=txn))


    def get_amount(self, peer):
        """return balance of peer, obtained from traversing blockchain"""
        return peer.coins


    def send_msg(self, event_queue, sender, receiver, msg, msg_type):
        if(msg_type == "txn"):
            msg_size = TRANSACTION_SIZE
        elif(msg_type == "block"):
            msg_size = msg.size

        delay = self.compute_delay(msg_size, receiver)
        new_event = Event(time.time() + delay, receiver, "msg_rcv", data=msg)
        event_queue.push(new_event)


    def broadcast(self, event_queue, msg, msg_type):
        for receiver in  self.neighbors:
            self.send_msg(self, event_queue, receiver, msg, msg_type)

    def receive_msg(self, event_queue, sender, msg, msg_type):
        if(msg_type == "txn"):
            if(msg in self.txn_pool):
                return
            
            self.txn_pool.add(msg)
            self.broadcast(event_queue, msg, msg_type)

    def get_next_event_timestmp(self):
        return random.expovariate(0.2)
        

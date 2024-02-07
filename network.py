import random
import string
import numpy as np
from collections import deque
from constants import *
from transaction import Transaction
from events import Event
import time


class Peer:
    def __init__(self, peer_id, is_slow, is_low_cpu):
        self.peer_id = peer_id
        self.is_slow = is_slow
        self.is_low_cpu = is_low_cpu
        self.coins = 1000  # Initial coins
        self.neighbors = set()
        self.txn_pool = set()
        self.hashing_power = 0

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

    def generate_transaction(self, event_queue, peers):
        receiver = random.choice(peers)
        while(self.peer_id == receiver.peer_id):
            receiver = random.choice(peers)

        amount = random.randint(1, self.coins) #NEED TO REMOVE SELF.COINS, THIS SHOULD COME FROM BLOCKCHAIN

        txn = Transaction(amount, self, receiver)
        self.txn_pool.append(txn)
        # broadcast to neighbors
        self.broadcast(event_queue, txn, "txn")
        
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
        

class Network:
    def __init__(self, n, z0, z1):
        self.n = n
        self.z0 = z0
        self.z1 = z1
        self.peers = []
        self.neighbor_constraint = False
        self.connected_graph = False
        self.slow_peers = 0
        self.low_cpu_peers = 0

        self.create_peers()
        self.create_network_topology()
        self.set_hashing_power()

    def create_peers(self):
        for i in range(self.n):
            speed_threshold = np.random.uniform(0, 1)
            cpu_threshold = np.random.uniform(0, 1)
            is_slow = speed_threshold <= self.z0
            is_low_cpu = cpu_threshold <= self.z1
            if is_slow:
                self.slow_peers += 1
            if is_low_cpu:
                self.low_cpu_peers += 1
            peer = Peer(i, is_slow, is_low_cpu)
            self.peers.append(peer)


    def set_hashing_power(self):
        high_cpu_peers = self.n - self.low_cpu_peers

        low_hash_power = 1/(10*high_cpu_peers + self.low_cpu_peers)
        high_hash_power = 10*low_hash_power

        for peer in self.peers:
            if peer.is_low_cpu:
                peer.hashing_power = low_hash_power
            else:
                peer.hashing_power = high_hash_power



    def build_neighbors(self, peer):
        num_neighbors = random.randint(3, 6)
        # print(f"{peer.peer_id} NEIGHBORS: {num_neighbors}")
        available_peers = [p for p in self.peers if p != peer and len(p.neighbors) < 6 and p not in peer.neighbors]
        random.shuffle(available_peers)
        
        for _ in range(num_neighbors - len(peer.neighbors)):
            if available_peers:
                neighbor = available_peers.pop()
                # print(f"{neighbor.peer_id} added as neighbor of {peer.peer_id}")
                peer.add_neighbor(neighbor)
                neighbor.add_neighbor(peer)
            else:
                return
            
        self.neighbor_constraint = True
    
    def reset_network(self):
        for peer in self.peers:
            peer.neighbors.clear()
        self.neighbor_constraint = False
        self.connected_graph = False

    def create_network_topology(self):
        print("Building network... \n")
        while not (self.connected_graph and self.neighbor_constraint):
            self.reset_network()

            for peer in self.peers:
                self.build_neighbors(peer)

            if not (self.neighbor_constraint):
                print("Not every node has 3-6 neighbors, rebuilding... \n")
                continue

            self.connected_graph = self.is_connected_graph()
            if not (self.connected_graph):
                print("Network topology not connected, rebuilding... \n")

        print("Network created \n")

    def is_connected_graph(self):
        visited = set()
        queue = deque([self.peers[0]]) 
        while queue:
            current_peer = queue.popleft()
            visited.add(current_peer)
            for neighbor in current_peer.get_neighbors():
                if neighbor not in visited:
                    queue.append(neighbor)
        return len(visited) == len(self.peers)
    
    def display_network(self):
        for peer in self.peers:
            neighbors = peer.get_neighbors()
            neighbor_ids = [neighbor.peer_id for neighbor in neighbors]
            print(f"Peer {peer.peer_id} is connected to: {neighbor_ids}")




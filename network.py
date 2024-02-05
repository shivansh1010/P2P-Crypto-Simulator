import random
import string
import numpy as np
from collections import deque
from constants import *


class Peer:
    def __init__(self, peer_id, is_slow, is_low_cpu):
        self.peer_id = peer_id
        self.is_slow = is_slow
        self.is_low_cpu = is_low_cpu
        self.coins = 1000  # Initial coins
        self.neighbors = set()

    def add_neighbor(self, neighbor):
        self.neighbors.add(neighbor)

    def remove_neighbor(self, neighbor):
        if neighbor in self.neighbors:
            self.neighbors.remove(neighbor)

    def get_neighbors(self):
        return list(self.neighbors)
    
    def compute_delay(self, msg_size, receiver, prop_delay):
        if(self.is_slow or receiver.is_slow):
            link_speed = SLOW_LINK_SPEED
        else:
            link_speed = FAST_LINK_SPEED

        queueing_delay = np.random.exponential((float(96)) / (link_speed * 1024))
        transmission_delay = (msg_size * 8) / (link_speed * 1024)

        total_delay = prop_delay + queueing_delay + transmission_delay
        return total_delay

    def generate_transaction(self, peers):
        txn_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        receiver = random.choice(peers)
        amount = random.randint(1, self.coins)
        if amount <= self.coins:
            self.coins -= amount
            return f"TxnID: {txn_id}, {self.peer_id} pays {receiver.peer_id} {amount} coins"
        else:
            return None
    
    def get_next_event_timestmp(self):
        return random.expovariate(0.2)
        

class Network:
    def __init__(self, n, z0, z1):
        self.n = n
        self.z0 = z0
        self.z1 = z1
        self.prop_delay  = np.random.uniform(MIN_PROP_DELAY, MAX_PROP_DELAY) 
        self.peers = []
        self.neighbor_constraint = False
        self.connected_graph = False

        self.create_peers()
        self.create_network_topology()

    def create_peers(self):
        slow_peers, low_cpu_peers = 0, 0
        for i in range(self.n):
            speed_threshold = np.random.uniform(0, 1)
            cpu_threshold = np.random.uniform(0, 1)
            is_slow = speed_threshold <= self.z0
            is_low_cpu = cpu_threshold <= self.z1
            if is_slow:
                slow_peers += 1
            if is_low_cpu:
                low_cpu_peers += 1
            peer = Peer(i, is_slow, is_low_cpu)
            self.peers.append(peer)

        fast_peers = self.n - slow_peers
        high_cpu_peers = self.n - low_cpu_peers


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




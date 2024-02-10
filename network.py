import random
import string
import numpy as np
from collections import deque
from constants import *
# from transaction import Transaction
from events import Event, EventQueue
from peer import Peer
import time


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

        self.event_queue = EventQueue()
        self.time = 0

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
            peer = Peer(i, is_slow, is_low_cpu, self)
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


    def start_simulation(self, n, z0, z1, txn_time, mining_time, simulation_until):
        # push initial timestamps of every peer to the queue

        for peer in self.peers:
            peer.transaction_create()
            # self.event_queue.push(Event(0, peer, "blk_mine"))

        while True:
            # get next event
            # self.event_queue.print()
            if not self.event_queue.queue.empty():
                event = self.event_queue.pop()
            else:
                print("No more events")
                break

            # print(event)
            # time.sleep(event.time - current_time)
            # process event
            if event.time > simulation_until:
                print ("Simulation time is up")
                break

            print(str(event))

            if event.type == "txn_create":
                event.receiver.transaction_create_handler(event.data, event.sender)
            elif event.type == "txn_recv":
                event.receiver.transaction_receive_handler(event.data, event.sender)
                
            elif event.type == "block":
                # process block
                print(f"Block event at time {event.time} for peer {event.receiver.peer_id}")
                pass
            else:
                print("Unknown event type")
                break
                
            # add to event queue
            # self.event_queue.push(Event(event.time + event.peer.get_next_event_timestmp(), 
            #                     event.peer, "transaction"))
            self.time = event.time

        print(f"Events in eventqueue: {self.event_queue.queue.qsize()}")





import random
import string
import numpy as np
from collections import deque
from constants import *
# from transaction import Transaction
from events import Event, EventQueue
from node import Node
import time


class Network:
    def __init__(self, config, type):

        # self.n = n
        # self.z0 = z0
        # self.z1 = z1
        self.nodes = []
        self.neighbor_constraint = False
        self.connected_graph = False
        self.num_slow_nodes = 0
        self.num_low_cpu_nodes = 0

        if type == 'toml':
            #simulation
            self.total_nodes = int(config['simulation']['total_nodes'])
            self.execution_time = int(config['simulation']['execution_time'])
            self.percent_slow_nodes = float(config['simulation']['percent_slow_nodes'])
            self.percent_low_cpu_nodes = float(config['simulation']['percent_low_cpu_nodes'])

            #node
            self.min_neighbors = int(config['node']['min_neighbors'])
            self.max_neighbors = int(config['node']['max_neighbors'])
            
            # transaction
            self.size = int(config['transaction']['size'])
            self.mean_interarrival_time_sec = int(config['transaction']['mean_interarrival_time_sec'])
            
            # network
            self.min_light_prop_delay = float(config['network']['min_light_prop_delay'])
            self.max_light_prop_delay = float(config['network']['max_light_prop_delay'])
            self.slow_node_link_speed = int(config['network']['slow_node_link_speed'])
            self.fast_node_link_speed = int(config['network']['fast_node_link_speed'])
            self.queuing_delay_constant = int(config['network']['queuing_delay_constant'])
            
        else:
            print("Unknown config type")
            return


    def show_parameters(self):
        print(f" Simulation time: {self.execution_time}")
        print(f" Total nodes: {self.total_nodes}")
        print(f" Slow nodes percent: {self.percent_slow_nodes}")
        print(f" Low cpu nodes percent: {self.percent_low_cpu_nodes}")
        print(f" Min neighbors: {self.min_neighbors}")
        print(f" Max neighbors: {self.max_neighbors}")
        print(f" Transaction size: {self.size}")
        print(f" Mean interarrival time: {self.mean_interarrival_time_sec}")
        print(f" Min light prop delay: {self.min_light_prop_delay}")
        print(f" Max light prop delay: {self.max_light_prop_delay}")
        print(f" Slow node link speed: {self.slow_node_link_speed}")
        print(f" Fast node link speed: {self.fast_node_link_speed}")
        print(f" Queuing delay constant: {self.queuing_delay_constant}")
        

    def prepare_simulation(self):
        self.create_nodes()
        self.create_network_topology()
        self.set_hashing_power()

        self.event_queue = EventQueue()
        self.time = 0


    def create_nodes(self):
        for i in range(self.total_nodes):
            speed_threshold = np.random.uniform(0, 1)
            cpu_threshold = np.random.uniform(0, 1)
            is_slow = speed_threshold <= self.percent_slow_nodes
            is_low_cpu = cpu_threshold <= self.percent_low_cpu_nodes

            if is_slow:
                self.num_slow_nodes += 1
            if is_low_cpu:
                self.num_low_cpu_nodes += 1
            node = Node(i, is_slow, is_low_cpu, self)
            self.nodes.append(node)


    def set_hashing_power(self):
        high_cpu_nodes = self.total_nodes - self.num_low_cpu_nodes
        low_hash_power = 1/(10*high_cpu_nodes + self.num_low_cpu_nodes)
        high_hash_power = 10*low_hash_power

        for node in self.nodes:
            if node.is_low_cpu:
                node.hashing_power = low_hash_power
            else:
                node.hashing_power = high_hash_power


    def build_neighbors(self, node):
        num_neighbors = random.randint(3, 6)
        # print(f"{node.id} NEIGHBORS: {num_neighbors}")
        available_nodes = [p for p in self.nodes if p != node and len(p.neighbors) < 6 and p not in node.neighbors]
        random.shuffle(available_nodes)
        
        for _ in range(num_neighbors - len(node.neighbors)):
            if available_nodes:
                neighbor = available_nodes.pop()
                # print(f"{neighbor.id} added as neighbor of {node.id}")
                node.add_neighbor(neighbor)
                neighbor.add_neighbor(node)
            else:
                return

        self.neighbor_constraint = True
    

    def reset_network(self):
        for node in self.nodes:
            node.neighbors.clear()
        self.neighbor_constraint = False
        self.connected_graph = False


    def create_network_topology(self):
        print("Building network... \n")
        while not (self.connected_graph and self.neighbor_constraint):
            self.reset_network()

            for node in self.nodes:
                self.build_neighbors(node)

            if not (self.neighbor_constraint):
                print("Not every node has 3-6 neighbors, rebuilding... \n")
                continue

            self.connected_graph = self.is_connected_graph()
            if not (self.connected_graph):
                print("Network topology not connected, rebuilding... \n")

        print("Network created \n")


    def is_connected_graph(self):
        visited = set()
        queue = deque([self.nodes[0]]) 
        while queue:
            current_node = queue.popleft()
            visited.add(current_node)
            for neighbor in current_node.get_neighbors():
                if neighbor not in visited:
                    queue.append(neighbor)
        return len(visited) == len(self.nodes)
    

    def display_network(self):
        for node in self.nodes:
            neighbors = node.get_neighbors()
            neighbor_ids = [neighbor.id for neighbor in neighbors]
            print(f"Node {node.id} is connected to: {neighbor_ids}")


    def start_simulation(self):
        # push initial timestamps of every node to the queue

        for node in self.nodes:
            node.transaction_create()
            # self.event_queue.push(Event(0, node, "blk_mine"))

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
            if event.time > self.execution_time:
                print ("Simulation time is up")
                break

            print(str(event))

            if event.type == "txn_create":
                event.receiver.transaction_create_handler(event.data, event.sender)
            elif event.type == "txn_recv":
                event.receiver.transaction_receive_handler(event.data, event.sender)
                
            elif event.type == "block":
                # process block
                print(f"Block event at time {event.time} for node {event.receiver.id}")
                pass
            else:
                print("Unknown event type")
                break
                
            # add to event queue
            # self.event_queue.push(Event(event.time + event.node.get_next_event_timestmp(), 
            #                     event.node, "transaction"))
            self.time = event.time

        print(f"Events in eventqueue: {self.event_queue.queue.qsize()}")





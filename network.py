""""class to handle functions related to network and simulating the blockchain"""

import random
import os
from collections import deque
import numpy as np
from graphviz import Digraph

from transaction import Transaction
from events import EventQueue
from node import Node
from block import Block


class Network:
    """Network class to execute simlation using a discrete-events"""
    def __init__(self, config, type):
        """ "memeber to initialize attributes of network"""
        self.nodes = []
        self.neighbor_constraint = False
        self.connected_graph = False
        self.num_slow_nodes = 0
        self.num_low_cpu_nodes = 0
        self.time = 0
        self.event_queue = None

        if type == "toml":
            # simulation
            self.total_nodes = int(config["simulation"]["total_nodes"])
            self.execution_time = int(config["simulation"]["execution_time"])
            self.percent_slow_nodes = float(config["simulation"]["percent_slow_nodes"])
            self.percent_low_cpu_nodes = float(config["simulation"]["percent_low_cpu_nodes"])
            self.output_dir = config["simulation"]["output_dir"]

            # node
            self.min_neighbors = int(config["node"]["min_neighbors"])
            self.max_neighbors = int(config["node"]["max_neighbors"])

            # transaction
            self.transaction_size = int(config["transaction"]["size"])
            self.mean_interarrival_time_sec = int(config["transaction"]["mean_interarrival_time_sec"])

            # network
            self.min_light_prop_delay = float(config["network"]["min_light_prop_delay"])
            self.max_light_prop_delay = float(config["network"]["max_light_prop_delay"])
            self.slow_node_link_speed = float(config["network"]["slow_node_link_speed"])
            self.fast_node_link_speed = float(config["network"]["fast_node_link_speed"])
            self.queuing_delay_constant = int(config["network"]["queuing_delay_constant"])

            # mining
            self.mean_mining_time_sec = int(config["mining"]["mean_mining_time_sec"])
            self.mining_reward = int(config["mining"]["mining_reward"])
            self.max_txn_in_block = int(config["mining"]["max_txn_in_block"])

        else:
            print("Unknown config type")

        # derived
        self.prop_delay = random.uniform(self.min_light_prop_delay, self.max_light_prop_delay)

    def show_parameters(self):
        """method to display parameters of network"""

        print(f" Simulation time: {self.execution_time}")
        print(f" Total nodes: {self.total_nodes}")
        print(f" Slow nodes percent: {self.percent_slow_nodes}")
        print(f" Low cpu nodes percent: {self.percent_low_cpu_nodes}")
        print(f" Min neighbors: {self.min_neighbors}")
        print(f" Max neighbors: {self.max_neighbors}")
        print(f" Transaction size: {self.transaction_size}")
        print(f" Mean interarrival time: {self.mean_interarrival_time_sec}")
        print(f" Min light prop delay: {self.min_light_prop_delay}")
        print(f" Max light prop delay: {self.max_light_prop_delay}")
        print(f" Slow node link speed: {self.slow_node_link_speed}")
        print(f" Fast node link speed: {self.fast_node_link_speed}")
        print(f" Queuing delay constant: {self.queuing_delay_constant}")
        print(f" Mean mining time: {self.mean_mining_time_sec}")

    def prepare_simulation(self):
        """method to create P2P network"""
        self.create_nodes()
        self.create_network_topology()
        self.set_hashing_power()
        self.event_queue = EventQueue()
        self.time = 0

    def create_nodes(self):
        """method to create nodes of the network"""

        # Create coinbase transactions to initialize balances
        genesis_transactions = [Transaction(self.time, 1000, None, id) for id in range(self.total_nodes)]
        genesis = Block(self.time, -1, 0, genesis_transactions)
        for i in range(self.total_nodes):
            speed_threshold = np.random.uniform(0, 1)
            cpu_threshold = np.random.uniform(0, 1)
            is_slow = speed_threshold <= (self.percent_slow_nodes / 100.0)
            is_low_cpu = cpu_threshold <= (self.percent_low_cpu_nodes / 100.0)

            if is_slow:
                self.num_slow_nodes += 1
            if is_low_cpu:
                self.num_low_cpu_nodes += 1
            node = Node(i, is_slow, is_low_cpu, self, genesis)
            self.nodes.append(node)

    def create_network_topology(self):
        """method to build connections between nodes"""

        print("Building network... \n")
        while not (self.connected_graph and self.neighbor_constraint):
            self.reset_network()

            for node in self.nodes:
                self.build_neighbors(node)

            if not self.neighbor_constraint:
                print("Not every node has 3-6 neighbors, rebuilding... \n")
                continue

            self.connected_graph = self.is_connected_graph()
            if not self.connected_graph:
                print("Network topology not connected, rebuilding... \n")

        print("Network created \n")

    def reset_network(self):
        """method to delete network connections"""
        for node in self.nodes:
            node.neighbors.clear()
        self.neighbor_constraint = False
        self.connected_graph = False

    def build_neighbors(self, node):
        """method to create neighbors of a node"""

        num_neighbors = random.randint(self.min_neighbors, self.max_neighbors)
        # print(f"{node.id} NEIGHBORS: {num_neighbors}")
        available_nodes = [
            p for p in self.nodes if p != node and len(p.neighbors) < self.max_neighbors and p not in node.neighbors
        ]
        random.shuffle(available_nodes)

        for _ in range(num_neighbors - len(node.neighbors)):
            if available_nodes:
                neighbor = available_nodes.pop()
                # print(f"{neighbor.id} added as neighbor of {node.id}")
                node.add_neighbor(neighbor.id)
                neighbor.add_neighbor(node.id)
            else:
                return

        self.neighbor_constraint = True

    def is_connected_graph(self):
        """method to check if network is connected"""
        visited = set()
        queue = deque([self.nodes[0].id])
        while queue:
            current_node_id = queue.popleft()
            current_node = self.nodes[current_node_id]
            visited.add(current_node_id)
            for neighbor in current_node.get_neighbors():
                if neighbor not in visited:
                    queue.append(neighbor)
        return len(visited) == len(self.nodes)

    def set_hashing_power(self):
        """ "method to set hashing power of nodes"""

        # High hash power = 10 x Low hash power
        high_cpu_nodes = self.total_nodes - self.num_low_cpu_nodes
        low_hash_power = 1 / (10 * high_cpu_nodes + self.num_low_cpu_nodes)
        high_hash_power = 10 * low_hash_power

        for node in self.nodes:
            if node.is_low_cpu:
                node.hashing_power = low_hash_power
            else:
                node.hashing_power = high_hash_power

    def display_network(self):
        """method to display the network"""
        for node in self.nodes:
            neighbor_ids = node.get_neighbors()
            print(
                f"Node {node.id} [{'SLOW' if node.is_slow else 'FAST'}, {'LOW-CPU' if node.is_low_cpu else 'HIGH-CPU'}] is connected to: {neighbor_ids}"
            )

    def start_simulation(self):
        """method to start simulation"""

        print(f" == Genesis block: {self.nodes[0].genesis_block.hash} == \n")

        for node in self.nodes:
            node.transaction_create()
            node.block_create()

        while True:
            if not self.event_queue.queue.empty():
                event = self.event_queue.pop()
            else:
                print("No more events")
                break

            # Update current time
            self.time = event.time
            receiver = self.nodes[event.receiver_id]

            if event.time > self.execution_time:
                print("Simulation time is up")
                break

            if event.type == "txn_create":
                print(str(event))
                receiver.transaction_create_handler(event.time)
            elif event.type == "txn_recv":
                receiver.transaction_receive_handler(event.data, event.sender_id)
            elif event.type == "blk_mine":
                print(str(event))
                receiver.block_mine_handler(event.data)
            elif event.type == "blk_recv":
                print(str(event))
                receiver.block_receive_handler(event.data, event.sender_id)
            else:
                print("Unknown event type")
                break

        print(f"Events in eventqueue: {self.event_queue.queue.qsize()}")

        for node in self.nodes:
            print(f" node {node.id} has blocks: {[block for block in node.block_registry.keys()]}")
            print(f" node {node.id} has longest chain at height: {node.block_registry[node.longest_leaf_hash].height}")

    def create_plot(self):
        """method to visualize blockchain"""

        d = Digraph(
            "simulation", node_attr={"fontname": "Arial", "shape": "record", "style": "filled", "fillcolor": "#FFFFE0"}
        )
        d.graph_attr["rankdir"] = "LR"
        for i, node in enumerate(reversed(self.nodes)):
            with d.subgraph(
                name=f"cluster_outer_{i}"
            ) as outer:  # Adding a cluster inside cluster to increase margin between them
                outer.attr(style="invis")
                with outer.subgraph(name=f"cluster_{i}", graph_attr={"margin": "30"}) as c:
                    c.attr(
                        style="filled",
                        color="none",
                        fillcolor="#E6F7FF",
                        labelloc="b",
                        labeljust="l",
                        label=f'< <FONT POINT-SIZE="20"><B>Node {node.id}</B></FONT> >',
                    )
                    for block in node.block_registry.values():
                        miner = block.txns[0].receiver_id if block.txns else "Satoshi"
                        label = f"{block.hash_s} | MineTime= {round(block.mine_time, 2)} | {{ Height={block.height} | Miner = {miner} }} | IncludedTxns={len(block.txns)}"
                        c.node(f"{node.id}-{block.hash}", label=label)
                        if block.prev_hash != -1:
                            c.edge(f"{node.id}-{block.prev_hash}", f"{node.id}-{block.hash}")

        d.view(directory=self.output_dir)

    def dump_to_file(self):
        """dump all the blocks of each node to a separate file"""
        path = os.path.join(os.path.dirname(__file__), self.output_dir)
        if not os.path.exists(path):
            os.makedirs(path)
        for node in self.nodes:
            with open(f"{path}/node_{node.id}.csv", "w", encoding="utf-8") as f:
                f.write("block_hash,height,mine_time,included_transactions,prev_hash\n")
                for block in node.block_registry.values():
                    f.write(f"{block.__str_v2__()}\n")

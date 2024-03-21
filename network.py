""""class to handle functions related to network and simulating the blockchain"""

import random
import os
import time
from collections import deque
import numpy as np
from graphviz import Digraph

from events import EventQueue
from node import Node
from node_adversary import AdversaryNode
from block import Block
from logger import log


class Network:
    """Network class to execute simlation using a discrete-events"""

    instance = None  # used to include time in log statements

    def __init__(self, config, type):
        """member to initialize attributes of network"""
        Network.instance = self  # used to include time in log statements

        self.nodes = []
        self.neighbor_constraint = False
        self.connected_graph = False
        self.num_slow_nodes = 0
        self.num_low_cpu_nodes = 0
        self.time = 0.0
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
            self.adversary_one_mining_power = float(config["node"]["adversary_one_mining_power"])
            self.adversary_two_mining_power = float(config["node"]["adversary_two_mining_power"])

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
        print("Simulation parameters:")
        print(f" -- Simulation time: {self.execution_time}")
        print(f" -- Total nodes: {self.total_nodes}")
        print(f" -- Slow nodes percent: {self.percent_slow_nodes}")
        print(f" -- Low cpu nodes percent: {self.percent_low_cpu_nodes}")
        print(f" -- Output directory: {self.output_dir}")
        print(f" -- Min neighbors: {self.min_neighbors}")
        print(f" -- Max neighbors: {self.max_neighbors}")
        print(f" -- Adversary one mining power: {self.adversary_one_mining_power}")
        print(f" -- Adversary two mining power: {self.adversary_two_mining_power}")
        print(f" -- Transaction size: {self.transaction_size}")
        print(f" -- Mean interarrival time: {self.mean_interarrival_time_sec}")
        print(f" -- Min light prop delay: {self.min_light_prop_delay}")
        print(f" -- Max light prop delay: {self.max_light_prop_delay}")
        print(f" -- Slow node link speed: {self.slow_node_link_speed}")
        print(f" -- Fast node link speed: {self.fast_node_link_speed}")
        print(f" -- Queuing delay constant: {self.queuing_delay_constant}")
        print(f" -- Mean mining time: {self.mean_mining_time_sec}")
        print(f" -- Mining reward: {self.mining_reward}")
        print(f" -- Max txns in block: {self.max_txn_in_block}")
        print(f" -- Random prop delay for this simulation: {round(self.prop_delay, 3)}")
        print()

    def prepare_simulation(self):
        """method to create P2P network"""
        self.create_nodes()
        self.create_network_topology()
        self.set_hashing_power()
        self.event_queue = EventQueue()
        self.time = 0

    def create_nodes(self):
        """method to create nodes of the network"""

        print("Creating nodes...")
        # Create coinbase transactions to initialize balances
        genesis_transactions = []
        genesis = Block(self.time, -1, 0, genesis_transactions)
        for i in range(self.total_nodes - 2):
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

        # Create adversary nodes
        node = AdversaryNode(self.total_nodes - 2, False, False, self, genesis)
        node.hashing_power = self.adversary_one_mining_power / 100.0
        self.nodes.append(node)
        node = AdversaryNode(self.total_nodes - 1, False, False, self, genesis)
        node.hashing_power = self.adversary_two_mining_power / 100.0
        self.nodes.append(node)

    def create_network_topology(self):
        """method to build connections between nodes"""

        print("Building network...")
        while not (self.connected_graph and self.neighbor_constraint):
            self.reset_network()

            for node in self.nodes:
                self.build_neighbors(node)

            if not self.neighbor_constraint:
                log.warning("Not every node has 3-6 neighbors, rebuilding...")
                continue

            self.connected_graph = self.is_connected_graph()
            if not self.connected_graph:
                log.warning("Network topology not connected, rebuilding...")

        print("Network created successfully")

    def reset_network(self):
        """method to delete network connections"""
        for node in self.nodes:
            node.neighbors.clear()
        self.neighbor_constraint = False
        self.connected_graph = False

    def build_neighbors(self, node):
        """method to create neighbors of a node"""

        num_neighbors = random.randint(self.min_neighbors, self.max_neighbors)
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

        print("Setting hashing power for each node...")
        # High hash power = 10 x Low hash power
        high_cpu_nodes = self.total_nodes - self.num_low_cpu_nodes
        total_honest_hashing_power = 1 - (self.adversary_one_mining_power + self.adversary_two_mining_power) / 100
        low_hash_power = total_honest_hashing_power / (10 * high_cpu_nodes + self.num_low_cpu_nodes)
        high_hash_power = 10 * low_hash_power

        for node in self.nodes:
            if isinstance(node, AdversaryNode):
                continue
            elif node.is_low_cpu:
                node.hashing_power = low_hash_power
            else:
                node.hashing_power = high_hash_power

    def display_network(self):
        """method to display the network"""
        print()
        for node in self.nodes:
            neighbor_ids = node.get_neighbors()
            print(
                f"Node {node.id} [{'slow' if node.is_slow else 'fast'}, "
                f"{'low-cpu' if node.is_low_cpu else 'high-cpu'}, "
                f"hash-power={round(node.hashing_power, 3)}] is connected to: {neighbor_ids}"
            )
        print()

    def start_simulation(self):
        """method to start simulation"""

        print(f" -- Genesis block: {self.nodes[0].genesis_block.hash}\n")

        start_time = time.time()
        log.info("Simulation starts...")
        for node in self.nodes:
            node.transaction_create()
            node.block_create()

        while True:
            if not self.event_queue.queue.empty():
                event = self.event_queue.pop()
            else:
                log.info("No more events in event queue. Exiting Simulation.")
                break

            # Update current time
            self.time = event.time
            receiver = self.nodes[event.receiver_id]

            if event.time > self.execution_time:
                log.info("Simulation time is up. Exiting Simulation.")
                break

            if event.type == "txn_create":
                # log.debug(str(event))
                receiver.transaction_create_handler(event.time)
            elif event.type == "txn_recv":
                # log.debug(str(event))
                receiver.transaction_receive_handler(event.data, event.sender_id)
            elif event.type == "blk_mine":
                # log.debug(str(event))
                receiver.block_mine_handler(event.data)
            elif event.type == "blk_recv":
                # log.debug(str(event))
                receiver.block_receive_handler(event.data, event.sender_id)
            else:
                log.warning("Unknown event type")
                break

        end_time = time.time()
        print(f"\nSimulation time: {round(end_time - start_time, 3)} seconds")

    def display_info(self):
        """display info about the simulation"""
        print("Events currently in event queue: ", self.event_queue.queue.qsize())

        all_blocks = set()
        for node in self.nodes:
            all_blocks = all_blocks.union(set(node.block_registry.keys()))
        print(f"Total number of blocks mined by all nodes: {len(all_blocks)}")

        # for node in self.nodes:
        # print(f" node {node.id} has blocks: {list(node.block_registry.keys())}")
        # print(f"Node {node.id} has longest chain at height: {node.block_registry[node.longest_leaf_hash].height}, hash {node.longest_leaf_hash[:7]}"
        print()
        print("Ratio of mined blocks included in longest chain to total mined blocks by the node:")
        for node in self.nodes:
            accepted_self_mined_blocks = 0
            total_mined_blocks = 0
            for block in node.block_registry.values():
                if len(block.txns) == 0:
                    continue
                if block.txns[0].receiver_id == node.id:
                    total_mined_blocks += 1

            curr_block_hash = node.longest_leaf_hash
            while curr_block_hash != -1:
                curr_block = node.block_registry[curr_block_hash]
                if len(curr_block.txns) == 0:
                    break
                if curr_block.txns[0].receiver_id == node.id:
                    accepted_self_mined_blocks += 1
                curr_block_hash = node.block_registry[curr_block_hash].prev_hash
            ratio = round(
                accepted_self_mined_blocks / total_mined_blocks if total_mined_blocks != 0 else float("inf"), 4
            )
            cpu_type = "low-cpu" if node.is_low_cpu else "high-cpu"
            node_type = "slow" if node.is_slow else "fast"
            print(
                f"Node {node.id} ({cpu_type}, {node_type}):  {accepted_self_mined_blocks} / {total_mined_blocks} = {ratio}"
            )
        print()

    def create_plot(self):
        """method to visualize blockchain"""

        print("Creating plot of blockchain of each node...")
        d = Digraph("simulation", node_attr={"fontname": "Arial", "shape": "record", "style": "filled"})
        d.graph_attr["rankdir"] = "LR"
        adversary_node_ids = []
        for node in self.nodes:
            if isinstance(node, AdversaryNode):
                adversary_node_ids.append(node.id)

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
                        fillcolor = "#FFBBBB" if miner == adversary_node_ids[0] else "#FFFFDD"
                        fillcolor = "#BBBBFF" if miner == adversary_node_ids[1] else fillcolor
                        c.node(f"{node.id}-{block.hash}", label=label, _attributes={"fillcolor": fillcolor})
                        if block.prev_hash != -1:
                            c.edge(f"{node.id}-{block.prev_hash}", f"{node.id}-{block.hash}", dir="back")

        d.view(directory=self.output_dir)

    def dump_to_file(self):
        """dump all the blocks of each node to a separate file"""

        print("Dumping blocks of each node to a separate file...")
        path = os.path.join(os.path.dirname(__file__), self.output_dir)
        if not os.path.exists(path):
            os.makedirs(path)
        for node in self.nodes:
            with open(f"{path}/node_{node.id}.csv", "w", encoding="utf-8") as f:
                f.write("block_hash,height,mine_time,included_transactions,prev_hash\n")
                for block in node.block_registry.values():
                    f.write(f"{block.__str_v2__()}\n")

""""class to handle functions related to node"""

import random
from copy import deepcopy
import numpy as np

from transaction import Transaction
from events import Event
from block import Block
from logger import log


class Node:
    """Node class to handle functions related to node"""

    def __init__(self, id, is_slow, is_low_cpu, network, genesis):
        """method to initialize attributes of node"""
        self.id = id
        self.is_slow = is_slow
        self.is_low_cpu = is_low_cpu
        self.neighbors = set()  # Set of nodes that are connected to this node
        self.txn_pool = {}  # uuid -> txn, Dict of transactions that have to be processed
        self.txn_registry = set()  # Set of ids of all the transactions seen
        self.pending_blocks = set()  # Set of blocks whose previous block hasn't arrived

        self.hashing_power = 0
        self.network = network
        self.block_hash_being_mined = None
        self.genesis_block = deepcopy(genesis)

        # Hash of Leaf Block of the Longest Branch in blockchain. We'll always mine on this chain
        self.longest_leaf_hash = self.genesis_block.hash
        self.block_registry = {self.genesis_block.hash: self.genesis_block}  # Hash -> Block

    def __str__(self):
        return f"{self.id}"

    def add_neighbor(self, neighbor):
        """method to add a neighbor to the node's neighbor list"""
        self.neighbors.add(neighbor)

    def remove_neighbor(self, neighbor):
        """method to remove a neighbor from the node's neighbor list"""
        if neighbor in self.neighbors:
            self.neighbors.remove(neighbor)

    def get_neighbors(self):
        """method to return the list of neighbors of the node"""
        return list(self.neighbors)

    def compute_delay(self, msg_size, receiver_id):
        """ "method to compute delay for sending messages"""
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
        self_balance = round(float(self.get_amount(self.id)), 4)
        amount = round(random.uniform(0.0, self_balance), 4)
        txn = Transaction(event_timestamp, amount, self.id, receiver_id)

        log.debug(
            "Txn_create -> sender %s, receiver %s, amount %s, sender_balance %s",
            txn.sender_id,
            txn.receiver_id,
            txn.amount,
            self_balance,
        )
        self.txn_pool[txn.id] = txn
        self.txn_registry.add(txn.id)
        self.transaction_broadcast(txn)
        self.transaction_create()

    def transaction_receive_handler(self, txn, source_node_id):
        """method to handle txn receive event"""
        if txn.id in self.txn_registry or txn.id in self.txn_pool:
            return
        # Commented out to reduce log verbosity
        # log.debug(
        #     "Txn_recv -> sender %s, receiver %s, amount %s, txn_time %s",
        #     txn.sender_id,
        #     txn.receiver_id,
        #     txn.amount,
        #     txn.timestamp,
        # )
        self.txn_pool[txn.id] = txn
        self.txn_registry.add(txn.id)
        self.transaction_broadcast(txn, source_node_id)

    def transaction_broadcast(self, txn, source_node_id=None):
        """broadcast fuction. Broadcast txn to all neighbours, except the node from which it came from"""
        for node_id in self.get_neighbors():
            # dont send back to the node from which txn came
            if source_node_id and node_id == source_node_id:
                continue
            delay = self.compute_delay(self.network.transaction_size, node_id)
            self.network.event_queue.push(
                Event(txn.timestamp + delay, self.id, node_id, "txn_recv", data=deepcopy(txn))
            )

    def get_amount(self, node):
        """return balance of node, obtained from traversing blockchain"""
        total_balance = 0.0
        curr_block = self.longest_leaf_hash
        while curr_block != -1:
            for txn in self.block_registry[curr_block].txns:
                if node == txn.receiver_id:
                    total_balance += txn.amount
                if node == txn.sender_id:
                    total_balance -= txn.amount
            curr_block = self.block_registry[curr_block].prev_hash

        for txn in self.txn_pool.values():
            if node == txn.receiver_id:
                total_balance += txn.amount
            if node == txn.sender_id:
                total_balance -= txn.amount

        return max(0.0, total_balance)

    def get_balances(self, block_hash):
        """ "returns a dictionary containing balances of each node"""

        balances = {}
        for node in self.network.nodes:
            balances[node.id] = 0.0

        curr_block = block_hash
        while curr_block != -1:
            for txn in self.block_registry[curr_block].txns:
                balances[txn.receiver_id] = balances.get(txn.receiver_id, 0) + txn.amount
                balances[txn.sender_id] = balances.get(txn.sender_id, 0) - txn.amount
            curr_block = self.block_registry[curr_block].prev_hash
        if None in balances:
            del balances[None]
        return balances

    def block_create(self):
        """method to create a block and start mining"""

        parent_block_hash = self.longest_leaf_hash
        parent_block_height = self.block_registry[parent_block_hash].height
        coinbase_txn = Transaction(self.network.time, self.network.mining_reward, None, self.id)
        txns_to_include = [coinbase_txn]

        true_balances = self.get_balances(parent_block_hash)
        for txn in self.txn_pool.values():
            # Assuming honest block creator, Validate transaction
            sender = txn.sender_id
            if round(true_balances.get(sender, 0), 4) >= txn.amount:
                txns_to_include.append(txn)
                true_balances[txn.sender_id] -= txn.amount
                true_balances[txn.receiver_id] += txn.amount
            else:
                log.warning(
                    "Invalid Txn while mining, Insufficient balance: sender %s, receiver %s, amount %s, sender_balance %s, time %s",
                    txn.sender_id,
                    txn.receiver_id,
                    txn.amount,
                    true_balances.get(sender, 0),
                    txn.timestamp,
                )

            # Don't exceed maximum block size limit
            if len(txns_to_include) >= self.network.max_txn_in_block:
                break

        # Create the block with transactions
        block = Block(self.network.time, parent_block_hash, parent_block_height + 1, deepcopy(txns_to_include))
        # Introduce mining delay
        timestamp = self.network.time + np.random.exponential(self.network.mean_mining_time_sec / self.hashing_power)

        # Schedule the block mine event
        self.network.event_queue.push(Event(timestamp, self.id, self.id, "blk_mine", data=block))
        self.block_hash_being_mined = block.hash

    def block_mine_handler(self, block):
        """method to create a block and handle it"""

        if block.hash != self.block_hash_being_mined:
            return
        if block.height <= self.block_registry[self.longest_leaf_hash].height:
            return

        # block sucessfully mined now
        block.mine_time = self.network.time

        log.info(
            "Blk_mine -> miner %s, height %s, hash %s, prev_hash %s, mine_time %s",
            self.id,
            block.height,
            block.hash_s,
            block.prev_hash_s,
            round(block.mine_time, 3),
        )

        # Add the block hash to block registry
        self.block_registry[block.hash] = block
        # Update longest chain's leaf
        self.longest_leaf_hash = block.hash

        # Remove the block transactions from transaction pool
        for txn in list(block.txns)[1:]:
            # self.txn_pool.remove(txn)
            del self.txn_pool[txn.id]

        # Print the coinbase transaction
        # log.debug(str(block.txns[0]))
        log.debug("Coinbase -> receiver %s, amount %s", block.txns[0].receiver_id, block.txns[0].amount)

        # Broadcast the block to neighbors
        self.block_broadcast(block)
        self.block_create()

    def process_pending_blocks(self, block):
        """ "if the parent block arrives after the child, remove the child block from pending blocks and process it"""
        for pending_blk in self.pending_blocks:
            if pending_blk.prev_hash == block.hash:
                self.pending_blocks.remove(pending_blk)
                self.block_receive_handler(pending_blk, self.id)
                break

    def block_receive_handler(self, block, source_node_id):
        """method to handle block receive event"""

        # Ensure loopless forwarding
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

        log.debug(
            "Blk_recv -> miner %s, height %s, hash %s, prev_hash %s, mine_time %s",
            self.id,
            block.height,
            block.hash_s,
            block.prev_hash_s,
            block.mine_time,
        )

        # Add to block registry
        self.block_registry[block.hash] = block

        # Remove these txns from txn_pool
        for txn in list(block.txns)[1:]:
            if txn.id in self.txn_pool:
                del self.txn_pool[txn.id]

        # Find the longest chain and add the block accordingly
        if block.height > last_block.height:

            if block.prev_hash != last_block_hash:
                old_branch = self.longest_leaf_hash
                new_branch = block.prev_hash
                log.info(
                    "Node %s changing mining branch from %s to %s", self.id, self.longest_leaf_hash, block.prev_hash
                )

                while old_branch != new_branch:
                    old_block = self.block_registry[old_branch]
                    new_block = self.block_registry[new_branch]

                    # Undo transactions of old branch
                    for txn in old_block.txns[1:]:
                        self.txn_pool[txn.id] = txn
                    # Redo transactions of new branch
                    for txn in new_block.txns[1:]:
                        if txn in self.txn_pool:
                            del self.txn_pool[txn.id]

                    old_branch = old_block.prev_hash
                    new_branch = new_block.prev_hash

            self.longest_leaf_hash = block.hash

        # Check if this is a parent of some pending block and add them
        self.process_pending_blocks(block)

        # Restart block mining
        self.block_hash_being_mined = None
        self.block_create()

        # Broadcast Block
        self.block_broadcast(block, source_node_id)

    def is_block_valid(self, block):
        """method to check if block is valid"""

        # Validate Previous Block height
        prev_blk_hash = block.prev_hash
        prev_blk = self.block_registry[prev_blk_hash]
        if prev_blk.height + 1 != block.height:
            log.warning("Received Invalid Block: Invalid Index %s", block.height)
            return False

        # Validate Hash
        if block.hash != block.block_hash():
            log.warning("Received Invalid Block: Hash mismatch %s", block.height)
            return False

        # Validate Coinbase Transaction
        if len(block.txns) < 1:
            log.warning("Received Invalid Block: No Transactions %s", block.height)
            return False

        if len(block.txns) > self.network.max_txn_in_block:
            log.warning("Received Invalid Block: Block size exceeded limit %s", block.height)
            return False

        # Check if the mining reward is correct
        coinbase_txn = block.txns[0]
        if coinbase_txn.amount > self.network.mining_reward:  # Max Mining Reward
            log.warning("Received Invalid Block: Mining fee more than maximum mining fee, %s", coinbase_txn)
            return False

        # Validate Transactions
        true_balances = self.get_balances(prev_blk_hash)
        for txn in block.txns[1:]:
            sender = txn.sender_id
            if round(true_balances.get(sender, 0), 4) < txn.amount:
                log.warning(
                    "Received Invalid Block: insufficient sender(%s) balance, cache:%s, txn:%s",
                    sender,
                    true_balances[sender],
                    txn.amount,
                )
                return False
            else:
                true_balances[txn.sender_id] -= txn.amount
                true_balances[txn.receiver_id] += txn.amount
        return True

    def block_broadcast(self, block, source_node_id=None):
        """method to broadcast block"""
        for node_id in self.get_neighbors():
            if source_node_id and node_id == source_node_id:
                continue
            block_size = len(block.txns) * self.network.transaction_size
            delay = self.compute_delay(block_size, node_id)
            self.network.event_queue.push(
                Event(self.network.time + delay, self, node_id, "blk_recv", data=deepcopy(block))
            )

""""class to handle functions related to adversary node that mines selfishly"""

from copy import deepcopy
from collections import deque
import numpy as np

from node import Node
from transaction import Transaction
from events import Event
from block import Block
from logger import log


class AdversaryNode(Node):
    """AdversaryNode class to handle functions related to adversary node"""

    def __init__(self, id, is_slow, is_low_cpu, network, genesis):
        """method to initialize extra attributes of adversary node"""
        super().__init__(id, is_slow, is_low_cpu, network, genesis)
        self.private_chain = deque()
        self.l_v_c_hash = self.genesis_block.hash
        self.last_adversary_block_mined_hash = None


    def block_create(self):
        """method to create a block and start mining"""

        # parent block is the either last privately mined block or last block of lvc
        if self.last_adversary_block_mined_hash is None:
            parent_block_hash = self.l_v_c_hash
        else:
            parent_block_hash = self.last_adversary_block_mined_hash
        log.debug("Adversary %s -> mining block on parent block %s", self.id, parent_block_hash[:7])

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
                # log.warning(
                #     "Invalid Txn while mining, Insufficient balance: sender %s, receiver %s, amount %s, sender_balance %s, time %s",
                #     txn.sender_id,
                #     txn.receiver_id,
                #     txn.amount,
                #     round(true_balances.get(sender, 0), 4),
                #     round(txn.timestamp, 3),
                # )
                pass
                # true_balances = self.get_balances(parent_block_hash)

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
        # if block.height <= self.block_registry[self.l_v_c_hash].height:
        #     return

        # block sucessfully mined now
        block.mine_time = self.network.time

        log.info(
            "Adversary %s -> blk_mined, height %s, hash %s, prev_hash %s, mine_time %s",
            self.id,
            block.height,
            block.hash_s,
            block.prev_hash_s,
            round(block.mine_time, 3),
        )

        # Remove the block transactions from transaction pool
        for txn in list(block.txns)[1:]:
            # self.txn_pool.remove(txn)
            if txn in self.txn_pool:
                del self.txn_pool[txn.id]

        # Print the coinbase transaction
        # log.debug(str(block.txns[0]))
        # log.debug("Coinbase -> receiver %s, amount %s", block.txns[0].receiver_id, block.txns[0].amount)
        # log.info(block.txns[0].__str_v2__())

        self.block_registry[block.hash] = block

        # Broadcast the block to neighbors
        block_lead = block.height - self.block_registry[self.l_v_c_hash].height
        log.debug("Adversary %s -> block lead is %s, last_block_mined %s", self.id, block_lead, self.last_adversary_block_mined_hash)
        # going from 0' state to 1' state
        if block_lead == 1 and self.last_adversary_block_mined_hash is not None:
            block.release_time = self.network.time
            self.block_broadcast(block)
        else:
            # Add the block hash to private queue
            self.private_chain.append(block.hash)
            private_chain_str = [block_hash[:7] for block_hash in self.private_chain]
            log.debug("Adversary %s -> adding block to private chain, chain length is %s %s", self.id, len(self.private_chain), private_chain_str)
        self.last_adversary_block_mined_hash = block.hash

        # Restart block mining
        self.block_create()


    def block_receive_handler(self, block, source_node_id=None):
        """method to handle block receive event"""

        # Ensure loopless forwarding
        if source_node_id and self.id == source_node_id:
            return
        if block.hash in self.block_registry:
            return

        last_block_hash = self.l_v_c_hash
        last_block = self.block_registry[last_block_hash]

        # Add to pending blocks if previous block not received
        if block.prev_hash not in self.block_registry:
            self.pending_blocks.add(block)
            return

        # Validate Block
        if not self.is_block_valid(block):
            return

        log.debug(
            "Adversary %s -> blk_receive, height %s, hash %s, prev_hash %s, mine_time %s",
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
                old_branch = self.l_v_c_hash
                new_branch = block.prev_hash
                log.info(
                    "Adversary %s -> changing mining branch from %s to %s", self.id, self.l_v_c_hash, block.hash
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

                # sort the txn_pool here according to timestamp
                self.txn_pool = dict(sorted(self.txn_pool.items(), key=lambda x: x[1].timestamp))

            self.l_v_c_hash = block.hash

        # Check if this is a parent of some pending block and add them
        self.process_pending_blocks(block)

        # If it's a fork on lvc, ignore
        if block.height <= last_block.height:
            return

        # find block lead
        if self.last_adversary_block_mined_hash is not None:
            last_adversary_block_mined = self.block_registry[self.last_adversary_block_mined_hash]
            block_lead = last_adversary_block_mined.height - self.block_registry[self.l_v_c_hash].height
        else:
            block_lead = 0
        log.debug("Adversary %s -> block lead is %s, last_block_mined %s", self.id, block_lead, self.last_adversary_block_mined_hash)

        # if block_lead < 0:
        
        if block_lead < 2:
            self.block_release_all()
            self.last_adversary_block_mined_hash = None
        else:
            self.block_release_one()

        self.block_hash_being_mined = None
        self.block_create()
        # dont Broadcast Block
        # self.block_broadcast(block, source_node_id)

    def block_broadcast(self, block, source_node_id=None):
        """method to broadcast block"""

        log.debug(
            "Adversary %s -> blk_brdcast, miner %s, height %s, hash %s, prev_hash %s, mine_time %s",
            self.id,
            block.txns[0].receiver_id,
            block.height,
            block.hash_s,
            block.prev_hash_s,
            block.mine_time,
        )
        if block.release_time == 0.0:
            log.warning("Block release time not set")
        for node_id in self.get_neighbors():
            if source_node_id and node_id == source_node_id:
                continue

            self.l_v_c_hash = block.hash
            block_size = len(block.txns) * self.network.transaction_size
            delay = self.compute_delay(block_size, node_id)
            self.network.event_queue.push(
                Event(self.network.time + delay, self.id, node_id, "blk_recv", data=deepcopy(block))
            )
            log.debug("Adversary %s -> block %s sent to node %s", self.id, block.hash_s, node_id)

    def block_release_one(self):
        """method to release only one block at start of the private chain"""
        block = self.block_registry[self.private_chain.popleft()]
        block.release_time = self.network.time
        self.block_broadcast(block)

    def block_release_all(self):
        """method to release all blocks in private chain to public chain"""
        while self.private_chain:
            block_hash = self.private_chain.popleft()
            block = self.block_registry[block_hash]
            block.release_time = self.network.time
            self.block_broadcast(block)

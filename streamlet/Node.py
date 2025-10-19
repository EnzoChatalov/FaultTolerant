from collections import defaultdict
from common import TransactionGenerator, Block, Message, MessageType, Transaction
import time


class Node:
    def __init__(self, node_id, num_nodes, delta):
        self.node_id = node_id
        self.num_nodes = num_nodes
        self.delta = delta

        self.pending_txs = []
        self.blockchain = {}
        self.votes = defaultdict(set) 
        self.notarized = set()
        self.finalized = set()

        genesis = Block("0", 0, 0, [])

        self.blockchain[genesis.hash] = genesis

    def run_epoch(self, epoch):
        leader = epoch % self.num_nodes

        if self.node_id == leader:
            self.pending_txs = TransactionGenerator().generateTransaction(3)
            print(self.pending_txs)
            prev_block = self.chain[-1]
            new_block = Block(prev_block.hash, epoch, prev_block.length + 1, self.pending_txs)
            content = {}
            content["new_block"] = new_block
            content["parent_chain"] = self.longest_notarized_chain()
            msg = Message(MessageType.PROPOSE, content, self.node_id)
            #urb.broadcast(msg)
            #msg
    
    def Echoing():
        return null
    
    def on_receive(self, message):
        if message.msg_type == MessageType.PROPOSE:
            self.handle_propose(message)
        elif message.msg_type == MessageType.VOTE:
            self.handle_vote(message)
        elif message.msg_type == MessageType.ECHO:
            #urb.broadcast?
            return True

    def handle_propose(self, message):
        block = message.content["new_block"]
        parent_chain = message.content["parent_chain"]

        # Update local blockchain with missing parent blocks
        for b in parent_chain:
            if b.hash not in self.blockchain:
                self.blockchain[b.hash] = b

        # Only vote if parent is notarized and block extends longest notarized chain
        if parent_chain[-1].hash in self.notarized:
            self.blockchain[block.hash] = block
            if block.length > len(self.longest_notarized_chain()):
                vote = Message(MessageType.VOTE, block.copy_without_txs(), self.node_id)
                #urb.broadcast(vote)

    
    def handle_vote(self, message):
        block = message.content
        self.votes[block.hash].add(message.sender)
        if len(self.votes[block.hash]) > self.n // 2:
            self.notarized.add(block.hash)
            self.check_finalization(block)

    def check_finalization(self, block):
        # Simplified: finalize if 3 consecutive notarized blocks
        chain = self.longest_notarized_chain()
        if len(chain) >= 3:
            to_finalize = chain[-2]
            if to_finalize.hash not in self.finalized:
                self.finalized.add(to_finalize.hash)
                print(f"Node {self.node_id}: Finalized block {to_finalize.length}-{to_finalize.epoch}")
    
    def longest_notarized_chain(self):
        # placeholder: just return chain from genesis through notarized
        chain = [b for b in self.blockchain.values() if b.hash in self.notarized or b.length == 0]
        return sorted(chain, key=lambda b: b.length)

    def start(self):
        epoch = 1
        while True:
            start_time = time.time()

            self.run_epoch(epoch)
            epoch += 1

            elapsed = time.time() - start_time
            if elapsed < 2:
                time.sleep(2 - elapsed)
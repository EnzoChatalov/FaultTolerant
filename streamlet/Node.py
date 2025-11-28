from collections import defaultdict
from queue import Queue
import socket
from network.Server import Server
from network.multicast import Multicast
from common.TransactionGenerator import TransactionGenerator
from common.Block import Block 
from common.Message import Message
from common.MessageType import MessageType
from common.Transaction import Transaction
import time, threading
import copy


class Node:
    def __init__(self, node_id, delta, nodes):
        self.node_id = int(node_id)
        self.delta = delta
        self.nodes = nodes

        self.peers = [n for n in nodes if int(n["id"]) != self.node_id]
        self.n = len(nodes)

        self.pending_txs = []
        self.blockchain = {}
        self.votes = defaultdict(set) 
        self.notarized = []
        self.finalized = []

        # network components
        #self.queue = Queue()
        #self.server = Server(self.nodes[self.node_id - 1][1], self.queue)
        #self.multicast = Multicast(self.other_nodes, self.node_id)

        self.queue = Queue()
        my_entry = next(n for n in self.nodes if int(n["id"]) == self.node_id)
        self.server = Server(my_entry["host"], my_entry["port"], self.queue)
        # Multicast expects list of (host, port, id)
        peer_tuples = [(p["host"], p["port"], int(p["id"])) for p in self.peers]
        self.multicast = Multicast(peer_tuples, self.node_id)

        genesis = Block("0", 0, 0, [])
        self.blockchain[genesis.hash] = genesis
        # "Notarize" the genesis
        self.notarized.append(genesis.hash)
        self.finalized.append(genesis.hash)

    def start(self):
        print(f"[Node {self.node_id}] starting server on {self.server.host}:{self.server.port}")
        server_thread = threading.Thread(target=self.server.run)
        server_thread.start()
        

        self.wait_for_other_nodes(timeout=20)

        #loop_thread = threading.Thread(target=self.loop)
        #loop_thread.start()
        message_thread = threading.Thread(target=self.handle_messages, daemon=True)
        message_thread.start()

        try:
            self.loop()  # run main loop in main thread
        except KeyboardInterrupt:
            print(f"[Node {self.node_id}] Shutting down.")

        server_thread.join()
        message_thread.join()
        #loop_thread.join()

    def loop(self):
        epoch = 1
        time_epoch = self.delta * 2
        next_epoch_start = time.time()

        while True:
            start_time = time.time()
            self.run_epoch(epoch)
            elapsed = time.time() - start_time

            next_epoch_start += time_epoch
            sleep_time = max(0, next_epoch_start - time.time())
            #print(f"[Node {self.node_id}] Epoch {epoch} took {elapsed:.3f}s, sleeping {sleep_time:.3f}s")
            time.sleep(sleep_time)
            epoch += 1

    def run_epoch(self, epoch):
        leader = (epoch - 1) % len(self.nodes)

        if self.node_id == leader + 1:
            self.pending_txs = TransactionGenerator().generateTransaction(3)
            prev_block = max(self.blockchain.values(), key=lambda b: b.length)
            parent_hash = prev_block.hash
            new_block = Block(parent_hash, epoch, prev_block.length + 1, self.pending_txs)
            content = {"new_block": new_block, "parent_chain": self.notarized}

            msg = Message(MessageType.PROPOSE, content, self.node_id)
            print(f"[Node {self.node_id}] Broadcasting PROPOSE for epoch {epoch}\n")
            self.votes[new_block.hash].add(self.node_id)
            self.multicast.broadcast(msg)
    
    def on_receive(self, message):
        if message.msg_type == MessageType.PROPOSE:
            self.handle_propose(message)
        elif message.msg_type == MessageType.VOTE:
            self.handle_vote(message)

    def handle_propose(self, message):

        if self.multicast.seenMessage(message):
            return
        
        block = message.content["new_block"]
        parent_chain = message.content["parent_chain"]
        #echo
        self.multicast.broadcast(message)

        print(f"[Node {self.node_id}] Handling received block from {message.sender_id}: {block.hash} for epoch {block.epoch}")

        """for b in parent_chain:
            if b.hash not in self.blockchain:
                self.blockchain[b.hash] = b"""

        if parent_chain[-1] in self.notarized:
            if block.length + 1 > len(self.notarized):
                vote = Message(MessageType.VOTE, block, self.node_id)
                print(f"[Node {self.node_id}] Voting for block {block.hash}\n")

                if len(self.nodes) == 2:
                    self.blockchain[block.hash] = block
                    self.notarized.append(block.hash)
                    self.check_finalization()

                self.votes[block.hash].add(self.node_id)
                self.multicast.broadcast(vote)

    
    def handle_vote(self, message):

        if self.multicast.seenMessage(message):
            return
         
        block = message.content
        self.votes[block.hash].add(message.sender_id)
        self.multicast.broadcast(message)
        #print("Checking Voting ", self.node_id)
        #print("Hash ", block.hash)
        if len(self.votes[block.hash]) > len(self.nodes) // 2 and block.hash not in self.notarized:
            print(f"[Node {self.node_id}] Notarized block {block.hash}")
            self.notarized.append(block.hash)
            print(f"[Node {self.node_id}] Notarized chain {self.notarized}\n")
            self.check_finalization()
            self.blockchain[block.hash] = block
            # After handling and notorizing the block we can delete the pending transactions
            pending_txs = []

    def check_finalization(self):
        chain = self.notarized
        #print("Checking Finalization ", self.node_id)
        if len(chain) >= 3:
            to_finalize = chain[-2]
            if to_finalize not in self.finalized:
                self.finalized.append(to_finalize)
                #print(f"[Node {self.node_id}] Finalized block {to_finalize}")
                #print(f"Blockchain: ", self.blockchain)
                #print(f"Notarized: ", self.notarized)
                print(f"[Node {self.node_id}] Finalized chain: {self.finalized}\n")

    def wait_for_other_nodes(self, timeout=10):
        start = time.time()
        required = [(p["host"], p["port"]) for p in self.peers]

        while True:
            ready = 0
            for host, port in required:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                try:
                    s.connect((host, port))
                    ready += 1
                except:
                    pass
                finally:
                    s.close()

            if ready == len(required):
                print(f"[Node {self.node_id}] All peers are online.\n")
                return
            if time.time() - start > timeout:
                print(f"[Node {self.node_id}] Warning: Not all peers ready after {timeout}s, continuing anyway.")
                return
            time.sleep(1)

    def handle_messages(self):
        while True:
            msg = self.queue.get()  # blocks until message arrives
            self.on_receive(msg)
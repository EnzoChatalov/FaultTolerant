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
import json
import random

class Node:
    def __init__(self, node_id, delta, nodes):

        self.confusion_start = 0
        self.confusion_duration = 2
        self.crashed = False  # indicates whether the node is currently "crashed"

        
        self.current_epoch = 0
        self.epoch_lock = threading.Lock()


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
        
        self.mempool = []

        # network components
        #self.queue = Queue()
        #self.server = Server(self.nodes[self.node_id - 1][1], self.queue)
        #self.multicast = Multicast(self.other_nodes, self.node_id)

        self.queue = Queue()
        my_entry = next(n for n in self.nodes if int(n["id"]) == self.node_id)
        self.server = Server(my_entry["host"], my_entry["port"], self.queue, self)
        # Multicast expects list of (host, port, id)
        self.peer_tuples = [(p["host"], p["port"], int(p["id"])) for p in self.peers]
        self.multicast = Multicast(self.peer_tuples, self.node_id, self)

        self.load_blockchain()  # Load blockchain from disk if exists

        if not self.blockchain:
            genesis = Block("0", 0, 0, [])
            self.blockchain[genesis.hash] = genesis
            # "Notarize" the genesis
            self.notarized.append(genesis.hash)
            self.finalized.append(genesis.hash)
        else:
            last_hash = list(self.blockchain)[-1]
            last_block = self.blockchain[last_hash]
            print(last_block.epoch)
            print(self.finalized)
            self.current_epoch = last_block.epoch

    def start(self):
        print(f"[Node {self.node_id}] starting server on {self.server.host}:{self.server.port}")
        server_thread = threading.Thread(target=self.server.run)
        server_thread.start()
        

        self.wait_for_other_nodes(timeout=20)
        
        #crash simulation thread
        crash_thread = threading.Thread(target=Node.random_crash_simulation, args=(self,), daemon=True)
        crash_thread.start()
        
        #msg handling thread
        message_thread = threading.Thread(target=self.handle_messages, daemon=True)
        message_thread.start()

        self.request_unblock()
        self.teste()

        try:
            self.loop()  # run main loop in main thread
        except KeyboardInterrupt:
            print(f"[Node {self.node_id}] Shutting down.")

        server_thread.join()
        message_thread.join()
        crash_thread.join()

    def loop(self):
        epoch = self.current_epoch + 1
        time_epoch = self.delta * 2
        next_epoch_start = time.time()

        while True:
            with self.epoch_lock:
                self.current_epoch = epoch
                
            start_time = time.time()
            self.run_epoch(epoch)
            elapsed = time.time() - start_time
            
            ##epoch, timeout??

            next_epoch_start += time_epoch
            sleep_time = max(0, next_epoch_start - time.time())
            #print(f"[Node {self.node_id}] Epoch {epoch} took {elapsed:.3f}s, sleeping {sleep_time:.3f}s")
            time.sleep(sleep_time)
            print(self.votes)
            epoch += 1

    def get_leader(self, epoch):
        if epoch < self.confusion_start or epoch >= self.confusion_start + self.confusion_duration - 1:
        # normal leader: round-robin
           return int(self.nodes[(epoch-1) % self.n]["id"])
        else:
        # confusion mode: deterministic by epoch to create forks
            return epoch % self.n

   
    def run_epoch(self, epoch):
        BLOCK_SIZE = 3
        if self.crashed:
            print(f"[Node {self.node_id}] Skipping epoch {epoch} (crashed)")
            return

        leader = self.get_leader(epoch)

        if self.node_id == leader:
            txs = []
            while self.mempool and len(txs) < BLOCK_SIZE:
                txs.append(self.mempool.pop(0))
            
            if len(txs) < BLOCK_SIZE:
                needed = BLOCK_SIZE - len(txs)
                tx_generator = TransactionGenerator()
                fake_txs = tx_generator.generateTransaction(needed)
                txs.extend(fake_txs)      
                
                
            self.pending_txs = txs
            
            prev_block = max(self.blockchain.values(), key=lambda b: b.length)
            parent_hash = prev_block.hash
            new_block = Block(parent_hash, epoch, prev_block.length + 1, self.pending_txs)
            print("PROPOSING", self.get_longest_notarized_chain())
            content = {"new_block": new_block, "parent_chain": self.get_longest_notarized_chain()}

            msg = Message(MessageType.PROPOSE, content, self.node_id)
            print(f"[Node {self.node_id}] Broadcasting PROPOSE for epoch {epoch}\n")
            self.votes[new_block.hash].add(self.node_id)
            self.multicast.broadcast(msg)
            vote = Message(MessageType.VOTE, new_block, self.node_id)
            self.multicast.broadcast(vote)
    
    def on_receive(self, message):
        if message.msg_type == MessageType.PROPOSE:
            self.handle_propose(message)
        elif message.msg_type == MessageType.VOTE:
            self.handle_vote(message)
        elif message.msg_type == MessageType.BLOCKCHAIN_REQUEST:
            self.handle_blockchainRequest(message)
        elif message.msg_type == MessageType.BLOCKCHAIN_RESPONSE:
            self.handle_blockchainResponse(message)
        elif message.msg_type == MessageType.UNBLOCK_REQUEST:
            self.handle_unblock(message)
    
    def teste(self):
        msg = Message(MessageType.BLOCKCHAIN_REQUEST, "", self.node_id)
        self.multicast.broadcast(msg)
    
    def handle_blockchainRequest(self, message):
        blockchain = [self.blockchain[hash].to_dict() for hash in self.notarized]

        sender_host = None
        sender_port = None

        for host, port, pid in self.peer_tuples:
            if pid == message.sender_id:
                sender_host = host
                sender_port = port

        msg = Message(MessageType.BLOCKCHAIN_RESPONSE, blockchain, self.node_id)

        self.server.send(sender_host, sender_port, msg)

    def handle_blockchainResponse(self, message):
        incoming_chain = message.content  # list of block dicts in order
        print("BLOCKCHAIN_RESPONSE received:", len(incoming_chain), "blocks")

        for b_dict in incoming_chain:
            block = Block.from_dict(b_dict)
            h = block.hash

            # 1. Add to blockchain dictionary if missing
            if h not in self.blockchain:
                self.blockchain[h] = block

            # 2. Maintain notarized order
            if h not in self.notarized:
                self.notarized.append(h)

            # 3. Maintain finalized order
            """if h not in self.finalized:
                self.finalized.append(h)"""

        print(f"[Node {self.node_id}] Updated blockchain:")
        print(f"  blockchain size = {len(self.blockchain)}")
        print(f"  notarized size  = {len(self.notarized)}")
        print(f"  finalized size  = {len(self.finalized)}")

        # Save updated state
        #self.save_blockchain()
    
    def request_unblock(self):
        msg = Message(MessageType.UNBLOCK_REQUEST, self.server.port, self.node_id)
        self.multicast.broadcast(msg)
        
    def handle_unblock(self, message):
        self.server.unblock(message.content)


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

        # Check parent notarization
        print("Parent chain", parent_chain)
        print("Longest notarized chain", self.get_longest_notarized_chain())
        temp = self.get_longest_notarized_chain()
        temp.append(block.hash)
        if self.chain_extends_hashes(temp, parent_chain):
           print(f"[Node {self.node_id}] Rejected block {self.get_longest_notarized_chain()[-1]}: parent {parent_chain[-1]} not notarized")
           return
         
         # Add the received block to blockchain if missing
        """if block.hash not in self.blockchain:
           self.blockchain[block.hash] = block"""

         # Vote if the block extends the longest notarized chain
        max_notarized_length = max([self.blockchain[h].length for h in self.notarized])
        if block.length > max_notarized_length:
           vote = Message(MessageType.VOTE, block, self.node_id)
           print(f"[Node {self.node_id}] Voting for block {block.hash}")
           self.votes[block.hash].add(self.node_id)
           self.multicast.broadcast(vote)
        else:
           print(f"[Node {self.node_id}] Not voting for block {block.hash}, does not extend longest notarized chain")   

    
    def handle_vote(self, message):
        
        if self.multicast.seenMessage(message):
            return
         
        block = message.content
        
        if block.hash not in self.blockchain:
            self.blockchain[block.hash] = block

        self.votes[block.hash].add(message.sender_id)
        self.multicast.broadcast(message)
        #print("Checking Voting ", self.node_id)
        #print("Hash ", block.hash)
        if len(self.votes[block.hash]) > len(self.nodes) // 2 and block.hash not in self.notarized:
            print(f"[Node {self.node_id}] Notarized block {block.hash}")
            self.notarized.append(block.hash)
            self.blockchain[block.hash] = block
            
            last_5 = list(self.notarized)[-5:]
            print(f"[Node {self.node_id}] Notarized chain (last {len(last_5)} hashes): {last_5}\n")
           
            self.check_finalization()

    def check_finalization(self):
      # sort notarized blocks by epoch
      notarized_blocks = [self.blockchain[h] for h in self.notarized]
      notarized_blocks.sort(key=lambda b: b.epoch)

    # iterate and finalize the middle block of every 3 consecutive epochs
      for i in range(len(notarized_blocks) - 2):
          b1, b2, b3 = notarized_blocks[i], notarized_blocks[i+1], notarized_blocks[i+2]
          if b2.prev_hash == b1.hash and b3.prev_hash == b2.hash and b1.epoch + 1 == b2.epoch and b2.epoch + 1 == b3.epoch:
                if b2.hash not in self.finalized:
                    self.finalize_chain(b2.hash)

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
            if self.crashed:
                time.sleep(0.1)
                print("SLEPT")
                continue    
            
            if self.queue.qsize() > 0:
                current_epoch = self.get_current_epoch()
                
                if current_epoch < self.confusion_start or current_epoch > self.confusion_start + self.confusion_duration:
                    msg = self.queue.get()  # blocks until message arrives
                    self.on_receive(msg)
                else:
                    time.sleep(0.1)
            else:
                time.sleep(0.1)  
                    
    def on_receive_client(self, tx):
       self.mempool.append(tx)
       
    def get_current_epoch(self):
        with self.epoch_lock:
           return self.current_epoch

    def save_blockchain(self, filename=None):
        if filename is None:
          filename = f"blockchain_node{self.node_id}.json"

        with open(filename, "w") as f:
            chain_list = [self.blockchain[h].to_dict() for h in sorted(self.notarized, key=lambda h: self.blockchain[h].epoch)] #[self.blockchain[hash].to_dict() for hash in self.finalized]
            json.dump(chain_list, f, indent=2)
        print(f"[Node {self.node_id}] Saved blockchain to disk, {len(self.finalized)} blocks")      

    def load_blockchain(self, filename=None):
        if filename is None:
           filename = f"blockchain_node{self.node_id}.json"
        try:
            with open(filename, "r") as f:
               chain_list = json.load(f)
               for b_dict in chain_list:
                    block = Block.from_dict(b_dict)
                    self.blockchain[block.hash] = block
                    #self.finalized.append(block.hash)
                    self.notarized.append(block.hash)
            print(f"[Node {self.node_id}] Loaded blockchain from disk, {len(self.finalized)} blocks")
        except FileNotFoundError:
            print(f"[Node {self.node_id}] No blockchain file found, starting fresh")

    def random_crash_simulation(node, num_crashes=3):
        crashes = 0
        while crashes < num_crashes:
          time.sleep(random.randint(5, 20))  # uptime before crash
          node.crashed = True
          print(f"[Node {node.node_id}] Crashed!")
          time.sleep(random.randint(2, 5))  # downtime
          print(f"[Node {node.node_id}] Recovered!")
          #node.teste()
          node.crashed = False
          #node.catch_up_blockchain()  # Optional
          crashes += 1

    def catch_up_blockchain(self):
      """
      After recovering from a crash, ask peers for missing finalized blocks.
      """
      print(f"[Node {self.node_id}] Catching up blockchain...")
    
    # Gather all finalized block hashes known locally
      known_hashes = set(self.finalized)

      for host, port, peer_id in [(p["host"], p["port"], int(p["id"])) for p in self.peers]:
          try:
              # Connect to peer
              s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
              s.settimeout(2)
              s.connect((host, port))

            # Request blockchain data
              request_msg = json.dumps({"type": "BLOCKCHAIN_REQUEST", "sender": self.node_id}).encode()
              s.sendall(request_msg)

            # Receive response
              data = s.recv(10_000_000)  # adjust buffer as needed
              chain_list = json.loads(data.decode())
              print("chain list", chain_list)

            # Add missing blocks
              for b_dict in chain_list:
                  block = Block.from_dict(b_dict)
                  if block.hash not in self.blockchain:
                      self.blockchain[block.hash] = block
                  if block.hash not in self.notarized:
                      self.notarized.append(block.hash)
                  if block.hash not in self.finalized:
                      self.finalized.append(block.hash)
            
              s.close()
          except Exception as e:
              print(f"[Node {self.node_id}] Could not catch up from {host}:{port} ({e})")

      print(f"[Node {self.node_id}] Catch up complete. Finalized blocks: {len(self.finalized)}")
      self.save_blockchain()

    def get_longest_notarized_chain(self):
        return self.get_longest_chain(self.notarized)

    def get_longest_finalized_chain(self):
        return self.get_longest_chain(self.finalized)

    def get_longest_chain(self, block_hashes):
        """
        Given a set/list of block hashes (notarized or finalized),
        return the longest valid chain as a **list of block hashes** 
        from genesis → head.
        """

        best_head = None
        best_len = -1

        # Find best head block
        for h in block_hashes:
            if h not in self.blockchain:
                continue
            b = self.blockchain[h]

            # Verify reachability to genesis
            curr = b
            reachable = True
            seen = set()

            while curr.prev_hash != "0":
                if curr.prev_hash not in self.blockchain:
                    reachable = False
                    break
                curr = self.blockchain[curr.prev_hash]

                if curr.hash in seen:  # cycle detection
                    reachable = False
                    break
                seen.add(curr.hash)

            if reachable and b.length > best_len:
                best_len = b.length
                best_head = h

        if best_head is None:
            return []

        # Reconstruct chain (head → genesis)
        chain = []
        curr = self.blockchain[best_head]

        while curr is not None:
            chain.append(curr.hash)   # ⬅️ append hash instead of block
            if curr.prev_hash == "0":
                break
            curr = self.blockchain.get(curr.prev_hash)

        chain.reverse()
        return chain

    def finalize_chain(self, h):
        # Collect ancestors first
        chain = []
        curr_hash = h

        while curr_hash != "0":
            if curr_hash in self.finalized:
                break  # stop at the first already-finalized ancestor

            chain.append(curr_hash)
            curr_hash = self.blockchain[curr_hash].prev_hash

        # Now finalize in correct (oldest → newest) order
        for block_hash in reversed(chain):
            self.finalized.append(block_hash)
            b = self.blockchain[block_hash]
            print(f"[Node {self.node_id}] Finalized block {b.hash} (epoch {b.epoch})")

        self.save_blockchain()

    def chain_extends_hashes(self, base_chain_hashes, candidate_chain_hashes):
        if not base_chain_hashes:
            return True  # Empty base chain is always extended

        if not candidate_chain_hashes:
            return False

        # Base chain head
        base_head = base_chain_hashes[-1]

        if base_head not in candidate_chain_hashes:
            return False  # candidate chain doesn't contain the base chain

        # Candidate prefix up to base head
        index_in_candidate = candidate_chain_hashes.index(base_head)
        candidate_prefix = candidate_chain_hashes[:index_in_candidate + 1]

        return candidate_prefix == base_chain_hashes
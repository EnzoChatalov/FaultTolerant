import hashlib
import json

class Block:
    def init(self, prev_hash, epoch, lenght, transactions):
        self.prev_hash = prev_hash
        self.epoch = epoch
        self.length = lenght
        self.transactions = transactions

    def calculate_hash(self):
        # Convert block data into a canonical (deterministic) string
        block_string = json.dumps({
            'previous_hash': self.prev_hash,
            'epoch': self.epoch,
            'length': self.length,
            'transactions': self.transactions
        }, sort_keys=True)

        # Compute SHA-256 digest
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

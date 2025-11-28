import hashlib
import json

class Block:
    def __init__(self, prev_hash, epoch, lenght, transactions):
        self.prev_hash = prev_hash
        self.epoch = epoch
        self.length = lenght
        self.transactions = transactions or []
        self.hash = self.calculate_hash() 

    def calculate_hash(self):
        tx_list = []
        for tx in self.transactions:
            if hasattr(tx, "to_dict"):
                tx_list.append(tx.to_dict())
            else:
                tx_list.append(tx)

        # Convert block data into a canonical (deterministic) string
        block_string = json.dumps({
            'previous_hash': self.prev_hash,
            'epoch': self.epoch,
            'length': self.length,
            'transactions': tx_list
        }, sort_keys=True)

        # Compute SHA-256 digest
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()
    
    def copy_without_txs(self):
        """Return a shallow copy of this block without transactions (for votes)."""
        return Block(self.prev_hash, self.epoch, self.length, [])
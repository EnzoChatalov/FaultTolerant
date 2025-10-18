class Block:
    def init(self, prev_hash, epoch, lenght, transactions):
        self.prev_hash = prev_hash
        self.epoch = epoch
        self.length = lenght
        self.transactions = transactions
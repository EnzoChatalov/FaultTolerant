class Transaction:
    def __init__(self, sender, receiver, transaction_id, amount):
        self.sender = sender
        self.receiver = receiver
        self.transaction_id = transaction_id
        self.amount = amount
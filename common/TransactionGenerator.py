import random
from .Transaction import Transaction

class TransactionGenerator:
    def generateTransaction(self, num_transactions):
        transactions = []

        for t in range(0, transactions):
            sender = TransactionGenerator.random_with_N_digits(9)
            receiver = TransactionGenerator.random_with_N_digits(9)
            transaction_id = TransactionGenerator.random_with_N_digits(4)
            amount = random.randint(1, 1000)
            transactions.append(Transaction(sender, receiver, transaction_id, amount))
        
        return transactions
    
    @staticmethod
    def random_with_N_digits(n):
        range_start = 10**(n-1)
        range_end = (10**n)-1
        return random.randint(range_start, range_end)
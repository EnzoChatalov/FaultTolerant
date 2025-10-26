from network.Server import Server
class Multicast():
    def __init__(self, nodes, id):
        self.nodes = nodes
        self.id = id
        self.seen_messages = set()

    def broadcast(self, message):
        if message.id not in self.seen_messages:
            self.seen_messages.add(message.id)
            for host, port in self.nodes:
                Server.send(host, port, message)

    def seenMessage(self, message):
        if message.id in self.seen_messages:
            return True
        
        return False
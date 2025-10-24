from network.Server import Server
class Multicast():
    def __init__(self, nodes, id):
        self.nodes = nodes
        self.id = id
        self.seen_messages = set()

    def broadcast(self, message):
        if message.id not in self.seen_messages:
            self.seen_messages.add(message.id)
            for node in self.nodes:
                Server.send(node.host, node.port, message)
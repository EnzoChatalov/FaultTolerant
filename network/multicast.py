from network.Server import Server
class Multicast():
    def __init__(self, nodes, id, node):
        self.nodes = nodes
        self.id = id
        self.seen_messages = set()
        self.node = node

    def broadcast(self, message):
        if message.id not in self.seen_messages:
            self.seen_messages.add(message.id)
            for host, port, _id in self.nodes:
                self.node.server.send(host, port, message)

    def seenMessage(self, message):
        return message.id in self.seen_messages

from queue import Queue
import sys
from streamlet import Node
import threading, time
import sys

nodes = sys.argv[0]
epoch = sys.argv[1]

seconds = epoch * 2

def main():
    node_id = int(sys.argv[1])
    num_nodes = 5
    nodeList = [('"localhost"', 5000 + i) for i in range(num_nodes)]
    msgQueue = Queue()
    port = nodes[node_id][1]
    server = Server(port, msgQueue)
    server.start()
    multicast = Multicast(nodeList, node_id)
    node = Node()




def run_node(node_id):
    node = Node(node_id, NODES, network, D)
    for e in range(1, EPOCHS + 1):
        node.generate_tx()
        node.run_epoch(e)
        time.sleep(2 * D)

threads = []
for n in NODES:
    t = threading.Thread(target=run_node, args=(n,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()
import sys
from streamlet.Node import Node
import sys

def main():
    node_id = int(sys.argv[1])
    num_nodes = 5
    delta = 2
    nodeList = [('127.0.0.1', 5000 + i + 1) for i in range(num_nodes)]
    node = Node(node_id, delta, nodeList)

    node.start()
    
if __name__ == "__main__":
    main()
import sys
from streamlet.Node import Node
import json


def load_config(path):
    with open(path, "r") as f:
        return json.load(f)["nodes"]

def main():
    if len(sys.argv) < 1:
        print("Usage: python main.py <node_id>")
        sys.exit(1)

    node_id = int(sys.argv[1])
    config_path = "ports.json"
    nodes = load_config(config_path)
    delta = 2

    #num_nodes = 5
    #nodeList = [('127.0.0.1', 5000 + i + 1) for i in range(num_nodes)]
    
    node = Node(node_id, delta, nodes)
    node.start()
    
if __name__ == "__main__":
    main()
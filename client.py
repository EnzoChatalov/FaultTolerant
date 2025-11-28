import socket
import json
import uuid

def send_transaction(node_host, node_port, sender, receiver, amount):
    tx = {
        "type": "TRANSACTION",
        "sender": sender,
        "receiver": receiver,
        "amount": amount,
        "transaction_id": str(uuid.uuid4())
    }

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((node_host, node_port))
        s.sendall((json.dumps(tx) + "\n").encode())
        s.close()
        print("✓ Transaction sent!")
    except Exception as e:
        print(f"[ERROR] {e}")


def main():
    print("=== Streamlet Interactive Client ===")
    print("Submit transactions to your nodes.")
    print("Press Ctrl+C to exit.\n")

    node_host = input("Enter node host (default 127.0.0.1): ").strip()
    if node_host == "":
        node_host = "127.0.0.1"

    node_port = input("Enter node port (default 5000): ").strip()
    if node_port == "":
        node_port = 5000
    else:
        node_port = int(node_port)

    while True:
        print("\n--- New Transaction ---")

        sender = input("Sender: ").strip()
        receiver = input("Receiver: ").strip()
        amount = input("Amount: ").strip()

        try:
            amount = float(amount)
        except:
            print("Amount must be a number.")
            continue

        send_transaction(node_host, node_port, sender, receiver, amount)


if __name__ == "__main__":
    main()

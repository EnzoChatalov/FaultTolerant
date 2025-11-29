import tkinter as tk
from tkinter import messagebox
import socket
import pickle
import struct
import json

# Load nodes from JSON file
with open("ports.json", "r") as f:
    data = json.load(f)
    
NODES = data["nodes"]    

class ClientGUI:
    def __init__(self, master):
        self.master = master
        master.title("Streamlet Transaction Client")

        # Labels and inputs
        tk.Label(master, text="Sender ID:").grid(row=0, column=0)
        self.sender_entry = tk.Entry(master)
        self.sender_entry.grid(row=0, column=1)

        tk.Label(master, text="Receiver ID:").grid(row=1, column=0)
        self.receiver_entry = tk.Entry(master)
        self.receiver_entry.grid(row=1, column=1)

        tk.Label(master, text="Amount:").grid(row=2, column=0)
        self.amount_entry = tk.Entry(master)
        self.amount_entry.grid(row=2, column=1)

        tk.Label(master, text="Node to send to:").grid(row=3, column=0)
        self.node_var = tk.StringVar(master)
        self.node_var.set(NODES[0]["id"])
        tk.OptionMenu(master, self.node_var, *[n["id"] for n in NODES]).grid(row=3, column=1)

        # Submit button
        tk.Button(master, text="Submit Transaction", command=self.submit_transaction).grid(row=4, columnspan=2, pady=10)

    def submit_transaction(self):
        sender = self.sender_entry.get()
        receiver = self.receiver_entry.get()
        amount = self.amount_entry.get()
        node_id = int(self.node_var.get())

        if not sender or not receiver or not amount:
            messagebox.showwarning("Input Error", "All fields are required!")
            return

        try:
            amount = float(amount)
        except ValueError:
            messagebox.showwarning("Input Error", "Amount must be a number!")
            return

        # Transaction as a dictionary (pickle-safe)
        tx_message = {
            "msg_type": "CLIENT_TX",
            "content": {
                "sender": sender,
                "receiver": receiver,
                "amount": amount
            }
        }

        # Send transaction to the selected node
        node = next(n for n in NODES if n["id"] == node_id)
        try:
            data = pickle.dumps(tx_message, protocol=pickle.HIGHEST_PROTOCOL)
            length_prefix = struct.pack("!I", len(data))
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((node["host"], node["port"]))
            s.sendall(length_prefix + data)
            s.close()
            messagebox.showinfo("Success", f"Transaction sent to Node {node_id}")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to send transaction: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    gui = ClientGUI(root)
    root.mainloop()

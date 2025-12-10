# FaultTolerant

## Contributors  
Group 6:  
- Enzo Chatalov nº 54414  
- Yuliya Sasinskaya nº 66416  
- Matouš Macák nº 66722  

---

## How to Run

### 1. Start the Streamlet Nodes  
Make sure you are inside the `/FaultTolerant` folder, then run:

`python launcher.py`
 

This will start 5 nodes/processes automatically.
To terminate a node, press Ctrl + C in its terminal.

### 2. Run the Client Software

Run the client GUI with:

`python client.py`

In the GUI, enter the following:
- Sender ID (integer only)
- Receiver ID (integer only)
- Amount
- Node to send to

Then click Submit Transaction.

## Limitations
- The number of nodes and delta value must be changed manually in main.py.

- The client does not confirm transaction receipt; it only sends the transaction (although the node’s terminal will show when a transaction is received).

- There is a grace period of 20 seconds when starting the first node to allow the other nodes to initialize, ensuring the distributed system starts without errors.

- No authentication or security is implemented (plain TCP, pickle-based).
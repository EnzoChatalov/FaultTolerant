# FaultTolerant
# Contributors
Group 6:
 Enzo Chatalov nº 54414
 Yuliya Sasinskaya nº66416
 Matouš Macák nº66722

# How to run
In the case of 5 nodes/processes: start 5 terminals, run in each terminal "python main.py [num_node]", where num_node starts at 1 and you increment it by 1 for each terminal.

# Limitations
We change the number of nodes and the delta manually inside our main.py.
We have to correctly input the node number in our terminals.
There is a grace period of 20 seconds when we start the first node to also setup the other ones, so that our distributed system starts without any issues or erros.

TOPOLOGIA 1
========================================

first, run a console from the pox directory and set up the remote controller:

> ./pox.py forwarding.l2_learning openflow.spanning_tree --no-flood --hold-down openflow.discovery host_tracker

or

> ./pox.py log.level forwarding.l2_learning openflow.spanning_tree --no-flood --hold-down openflow.discovery host_tracker

or

> ./pox.py log.level --debug forwarding.l2_learning openflow.spanning_tree --no-flood --hold-down openflow.discovery host_tracker

then, on a different console set up the configuration and run the test ping all

> sudo mn --custom topo1.py --topo topo1,switch_level=3,host_amount=4 --mac --arp --switch ovsk --controller remote


TOPOLOGIA 2
========================================

first, run a console from the pox directory and set up the remote controller:

> ./pox.py misc.firewall forwarding.l2_learning

or

> ./pox.py log.level misc.firewall forwarding.l2_learning

or

> ./pox.py log.level --debug misc.firewall forwarding.l2_learning

then, on a different console set up the configuration and run the test ping all

> sudo mn --custom ./topo2.py --topo topo2,11 --switch ovsk --controller remote


WIRESHARK
========================================

filtro
(openflow or openflow_v1 or openflow_v4 or openflow_v5 or openflow_v6 or icmp)
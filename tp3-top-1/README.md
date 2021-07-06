sudo ./pox.py forwarding.l2_learning openflow.spanning_tree --no-flood --hold-down openflow.discovery host_tracker

sudo mn --custom topology1.py --topo topology1,switch_level=3,host_number=4 --mac --arp --switch ovsk --controller remote

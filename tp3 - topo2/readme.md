sudo mn --custom ./topo2.py --topo mytopo,11 --switch ovsk --controller remote --test pingall

./pox.py log.level misc.firewall forwarding.l2_learning

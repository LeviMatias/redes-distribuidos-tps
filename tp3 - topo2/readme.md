first, run a console from the pox directory and set up the remote controller:

> ./pox.py log.level misc.firewall forwarding.l2_learning

or

> ./pox.py log.level --debug misc.firewall forwarding.l2_learning

then, on a different console set up the configuration and run the test ping all

sudo mn --custom ./topo1.py --topo mytopo,11 --switch ovsk --controller remote --test pingall

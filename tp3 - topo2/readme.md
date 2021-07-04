<<<<<<< HEAD
first, run a console from the pox directory and set up the remote controller:

> ./pox.py log.level misc.firewall forwarding.l2_learning

or
=======
sudo mn --custom ./topo2.py --topo mytopo,11 --switch ovsk --controller remote --test pingall
>>>>>>> 48b83a19e64f06f1bcb40de366bfa01bd7dd3474

> ./pox.py log.level --debug misc.firewall forwarding.l2_learning

then, on a different console set up the configuration and run the test ping all

sudo mn --custom ./topo1.py --topo mytopo,11 --switch ovsk --controller remote --test pingall

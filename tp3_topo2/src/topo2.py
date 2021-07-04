"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- switch --- host, host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname("__file__"))))


from mininet.topo import Topo
from src.host_generator import get_host

class MyTopo( Topo ):

    def build( self, nswitches ):
        "Create custom topo."

        switches = []
        prevswitch = None
        for i in range(0, nswitches):
            switch = self.addSwitch("s"+str(i))
            switches.append(switch)
            if prevswitch:
                self.addLink(prevswitch, switch)
            prevswitch = switch

        # Adding hosts
        host, ip = get_host(1)
        h1 = self.addHost( host, ip=ip)

        host, ip = get_host(2)
        h2 = self.addHost( host, ip=ip)

        host, ip = get_host(3)
        h3 = self.addHost( host, ip=ip)

        host, ip = get_host(4)
        h4 = self.addHost( host, ip=ip)

        self.addLink(h1, switches[0])
        self.addLink(h2, switches[0])

        self.addLink(h3, switches[-1])
        self.addLink(h4, switches[-1])

        #"Create custom topo."

def start(nswitches = 3):
    return MyTopo(nswitches)

topos = { 'mytopo': start }
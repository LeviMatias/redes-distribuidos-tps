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
from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox . lib . revent import *
from pox . lib . util import dpidToStr
from pox . lib . addresses import EthAddr
from collections import namedtuple

# Add your imports here ...
log = None
# Add your global variables here ...
class Firewall ( EventMixin ) :
    def __init__ ( self ) :
        log = core . getLogger ()
        self . listenTo ( core . openflow )
        log . debug ( " Enabling Firewall Module " )

    def _handle_ConnectionUp ( self , event ) :
        print(event)
        print("wowowowo")
        # Add your logic here ...

    def launch ():
        # Starting the Firewall module
        core.registerNew( Firewall )

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
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )
        self.addLink(h1, switches[0])
        self.addLink(h2, switches[0])

        h3 = self.addHost( 'h3' )
        h4 = self.addHost( 'h4' )
        self.addLink(h3, switches[-1])
        self.addLink(h4, switches[-1])

        #"Create custom topo."

def start(nswitches = 3):
    return MyTopo(nswitches)

topos = { 'mytopo': start }
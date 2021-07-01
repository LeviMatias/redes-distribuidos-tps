"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- switch --- host, host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname("__file__"))))

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.addresses import EthAddr
from collections import namedtuple
import os

from mininet.topo import Topo
from mininet.node import OVSSwitch, Controller, RemoteController

class Firewall ( EventMixin ) :
    def __init__ ( self ) :
        log = core . getLogger ()
        self . listenTo ( core . openflow )
        log . debug ( " Enabling Firewall Module " )
        print("eeeeeeeeeeeeee")

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
        h1 = self.addHost( 'h1', ip='10.0.0.1', mac='00:00:00:00:00:01' )
        h2 = self.addHost( 'h2', ip='10.0.0.2', mac='00:00:00:00:00:02' )
        self.addLink(h1, switches[0])
        self.addLink(h2, switches[0])

        h3 = self.addHost( 'h3', ip='10.0.0.3', mac='00:00:00:00:00:03' )
        h4 = self.addHost( 'h4', ip='10.0.0.4', mac='00:00:00:00:00:04' )
        self.addLink(h3, switches[-1])
        self.addLink(h4, switches[-1])

        #"Create custom topo."

def start(nswitches = 3):
    core.registerNew(Firewall)
    return MyTopo(nswitches)

topos = { 'mytopo': start }
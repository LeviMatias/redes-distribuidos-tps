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

from host_generator import get_host

log = core.getLogger()

class Firewall ( EventMixin ) :

    def __init__ ( self ) :
        log = core . getLogger ()
        self . listenTo ( core . openflow )
        log.debug( " Enabling Firewall Module " )

    def _handle_ConnectionUp ( self , event ) :
        pass
        # Add your logic here ...

    def block(self, packet):
        # Halt the event, stopping l2_learning from seeing it
        # (and installing a table entry for it)
        core.getLogger("blocker").debug("Blocked %s <-> %s", packet.srcport, packet.dstport)
        packet.halt = True

    def rule1(self, packet):

        if (packet.dstport == 80):
            self.block(packet)

    def rule2(self, packet):

        udpp = packet.find('udp')

        if not udpp: return # Not UDP

        if udpp.dstport != 5001: return # Not port 5001

        _, ip = get_host(1)
        if udpp.srcip != ip: return # Not port h1

        self.block(packet)

    def _handle_PacketIn (self, event):

        packet = event.parsed

        self.rule1(packet)
        if not event.halt:
            log.debug( "pass rule 1" )

        self.rule2(packet)
        if not event.halt:
            log.debug( "pass rule 2" )

def launch ():
    # Starting the Firewall module
    core.registerNew( Firewall )
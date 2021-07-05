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

log = core.getLogger()

class Firewall ( EventMixin ) :
    def __init__ ( self ) :
        log = core . getLogger ()
        self . listenTo ( core . openflow )
        log.debug( " Enabling Firewall Module " )

    def _handle_ConnectionUp ( self , event ) :
        pass
        # Add your logic here ...
    
    def get_ip(self, event):
        log.debug("MAC", event.parsed.src.to_str())# mac
        return event.parsed.next.srcip.ipv4.toStr() #ip

    def block(self, event):
        # Halt the event, stopping l2_learning from seeing it
        # (and installing a table entry for it)
        core.getLogger("blocker").debug("Blocked %s <-> %s", udpp.srcport, udpp.dstport)
        event.halt = True

    def rule1(self, event):
        p = event.parsed.find('udp')
        if not p:
            p = event.parsed.find('tcp')
        if not p:
            return
        
        if (p.dstport == 80):
            block(event)

    def rule2(self, event):
        udpp = event.parsed.find('udp')
        if not udpp: return # Not UDP
        # check dst port
        ip = self.get_ip(event)
        log.debug(ip)
        if ip == '10.0.0.1' and udpp.dstport == 5001:
           block(event)

    def _handle_PacketIn (self, event):
        self.rule1(event)
        if not event.halt:
            log.debug( "pass rule 1" )
        self.rule2(event)
        if not event.halt:
            log.debug( "pass rule 2" )


def launch ():
    # Starting the Firewall module
    core.registerNew( Firewall )
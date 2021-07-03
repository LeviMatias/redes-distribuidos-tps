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
        log . debug ( " Enabling Firewall Module " )
        print("eeeeeeeeeeeeee")

    def _handle_ConnectionUp ( self , event ) :
        print(event)
        print("wowowowo")
        # Add your logic here ...

def launch ():
    # Starting the Firewall module
    core.registerNew( Firewall )
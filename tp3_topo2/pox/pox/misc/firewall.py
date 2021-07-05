from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
from pox.lib.revent import EventMixin

from pox.host_generator import get_host

log = core.getLogger()

class Firewall(EventMixin):

    def __init__(self):
        log = core.getLogger()
        self.listenTo(core.openflow)
        log.debug(" Enabling Firewall Module ")

    def _handle_ConnectionUp(self, event):

        connection = event.connection

        self.send_rule(connection, self.rule1)
        self.send_rule(connection, self.rule2)

        #rule3:
        h1 = 1
        h2 = 2
        # disconnect host1 --> host2
        self.send_rule(connection, self.__make_disconnect, [h1, h2])
        # disconnect host2 --> host1
        self.send_rule(connection, self.__make_disconnect, [h2, h1])

        log.info("Firewall rules installed on %s", event.dpid)

    def send_rule(self, connection, rule, args=None):

        # create rule
        msg = of.ofp_flow_mod()
        match = of.ofp_match()

        # rule settings
        match = rule(match, args)

        # assign and send rule
        msg.match = match
        msg.priority = 10
        connection.send(msg)

    def rule1(self, match, _):
        match.tp_dst = 80
        return match

    def rule2(self, match, _):
        match.nw_proto = pkt.ipv4.UDP_PROTOCOL
        match.tp_dst = 5001
        match.nw_src = get_host(1)[1]
        return match

    def __make_disconnect(self, match, args):

        h1 = args[0]
        h2 = args[1]

        match.nw_src = get_host(h1)[1]
        match.nw_dst = get_host(h2)[1]
        return match

def launch ():
    # Starting the Firewall module
    core.registerNew( Firewall )
from openflow.libopenflow_01 import OFP_DEFAULT_PRIORITY, OFP_FLOW_PERMANENT
from config_reader import ConfigReader
from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import EventMixin

from config_reader import ConfigReader

log = core.getLogger()
rules = ConfigReader().read()


class Firewall(EventMixin):

    def __init__(self):
        log = core.getLogger()
        self.listenTo(core.openflow)
        log.debug(" Enabling Firewall Module ")

    def _handle_ConnectionUp(self, event):

        connection = event.connection

        for rule in rules:
            self.send_rule(connection, rule)

        log.info("Firewall rules installed on %s", event.dpid)

    def send_rule(self, connection, rule):

        # create rule
        msg = of.ofp_flow_mod()

        # assign and send rule
        msg.match = rule
        msg.command = of.ofp_flow_mod_command_rev_map['OFPFC_ADD']
        msg.priority = OFP_DEFAULT_PRIORITY
        msg.idle_timeout = OFP_FLOW_PERMANENT
        msg.hard_timeout = OFP_FLOW_PERMANENT
        #msg.out_port = of.ofp_port_rev_map['OFPP_NONE']
        #msg.actions.append(action)
        connection.send(msg)

def launch ():
    # Starting the Firewall module
    core.registerNew( Firewall )
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

        for match, action in rules:
            self.send_rule(connection, match, action)

        log.info("Firewall rules installed on %s", event.dpid)

    def send_rule(self, connection, match, action):

        # create rule
        msg = of.ofp_flow_mod()

        # assign and send rule
        msg.match = match
        msg.priority = 10
        msg.actions.append(action)
        connection.send(msg)

def launch ():
    # Starting the Firewall module
    core.registerNew( Firewall )
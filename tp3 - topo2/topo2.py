"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- switch --- host, host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.topo import Topo

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
    return MyTopo(nswitches)

topos = { 'mytopo': start }
"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- switch --- host, host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.topo import Topo
# from hosts import IPs, MACs
# hardcoded for now
IPs = ['10.0.0.1', '10.0.0.2', '10.0.0.3', '10.0.0.4']
MACs = ['00:00:00:00:00:01', '00:00:00:00:00:02', '00:00:00:00:00:03', '00:00:00:00:00:04']

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
        h1 = self.addHost( 'h1', ip = IPs[0], mac = MACs[0] )
        h2 = self.addHost( 'h2', ip = IPs[1], mac = MACs[1]  )
        self.addLink(h1, switches[0])
        self.addLink(h2, switches[0])

        h3 = self.addHost( 'h3', ip = IPs[2], mac = MACs[2] )
        h4 = self.addHost( 'h4', ip = IPs[3], mac = MACs[3] )
        self.addLink(h3, switches[-1])
        self.addLink(h4, switches[-1])

        #"Create custom topo."

def start(nswitches = 3):
    return MyTopo(nswitches)

topos = { 'mytopo': start }
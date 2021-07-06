"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- switch --- host, host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.topo import Topo

def get_host(host_number):
    
    if host_number < 10:
        mac_host_number = '0'+str(host_number)
    else:
        mac_host_number = str(host_number)

    return 'h'+str(host_number), '10.0.0.'+str(host_number), '00:00:00:00:00:'+mac_host_number

class Topo2( Topo ):

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
        h, ip, mac = get_host(1)
        h1 = self.addHost( h, ip=ip, mac=mac)
        
        h, ip, mac = get_host(2)
        h2 = self.addHost( h, ip=ip, mac=mac)

        h, ip, mac = get_host(3)
        h3 = self.addHost( h, ip=ip, mac=mac)

        h, ip, mac = get_host(4)
        h4 = self.addHost( h, ip=ip, mac=mac)

        self.addLink(h1, switches[0])
        self.addLink(h2, switches[0])

        self.addLink(h3, switches[-1])
        self.addLink(h4, switches[-1])


def start(nswitches = 3):
    return Topo2(nswitches)

topos = { 'topo2': start }

from mininet.topo import Topo
import math

def get_host(host_number):
    
    if host_number < 10:
        mac_host_number = '0'+str(host_number)
    else:
        mac_host_number = str(host_number)

    return 'h'+str(host_number), '10.0.0.'+str(host_number), '00:00:00:00:00:'+mac_host_number

def get_switch_amount(switch_level):
    sum = math.pow(2, switch_level - 1)
    while (0 < switch_level - 1) :
        sum = sum + math.pow(2, switch_level - 1)
        switch_level -= 1
    return int(sum)

class Topo1(Topo):

    def build( self, switch_level, host_amount):

        if host_amount > 4:
            host_amount = 4

        if host_amount < 1:
            host_amount = 1

        if switch_level > 3:
            switch_level = 3

        if switch_level < 1:
            switch_level = 1

        self.switch_counter = 1

        network_left_switch, network_right_switch = self.make_network(switch_level)
        hosts = self.make_hosts(host_amount)

        # connect hosts to network
        self.connect_evenly_to_endpoints(hosts, network_left_switch, network_right_switch)
  
    def make_network(self, level=1):

        if level==1:
            only_switch = self.create_switch()
            left_switch = only_switch
            right_switch = only_switch
        else:
            left_switch = self.create_switch()
            right_switch = self.create_switch()

            # recursive magic
            network_left_switch1, network_right_switch1 = self.make_network(level-1)
            network_left_switch2, network_right_switch2 = self.make_network(level-1) 

            nodes = [left_switch, right_switch]
            self.connect_evenly_to_endpoints(nodes, network_left_switch1, network_right_switch1)
            self.connect_evenly_to_endpoints(nodes, network_left_switch2, network_right_switch2)

        return left_switch, right_switch

    def create_switch(self):
        switch = self.addSwitch("s"+str(self.switch_counter))
        self.switch_counter += 1
        return switch

    def connect_evenly_to_endpoints(self, nodes, left_end_point, right_end_point):
        for i, node in enumerate(nodes):
            if i % 2 == 0:
                self.addLink(node, left_end_point)
            else:
                self.addLink(node, right_end_point)

    def make_hosts(self, amount):
        hosts = []
        for i in range(1, amount+1):
            h, ip, mac = get_host(i)
            hosts.append(self.addHost( h, ip=ip, mac=mac))
        return hosts

def start(switch_level=3, host_amount=4):
    return Topo1(switch_level, host_amount)

topos = {'topo1': start}

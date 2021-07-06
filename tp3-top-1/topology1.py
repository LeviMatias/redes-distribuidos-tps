from mininet.topo import Topo
import math


def get_switch_amount(switch_level):
    sum = math.pow(2, switch_level - 1)
    while (0 < switch_level - 1) :
        sum = sum + math.pow(2, switch_level - 1)
        switch_level -= 1
    return int(sum)


class Topology1(Topo):


    def __init__( self, half_ports = 2, **opts ):
        Topo.__init__(self, **opts)

        switch_level = opts['switch_level']
        host_number = opts['host_number']

        switches = self.create_switches(switch_level)

        self.add_switch_links(switches, switch_level)
        self.add_hosts(switches)


    def create_switches(self, switch_level):
        switch_amount = get_switch_amount(switch_level)
        switch_number = 1
        switches = []
        for i in range(1, switch_amount + 1):
            new_switch = self.addSwitch('sw' + str(switch_number))
            switches.append(new_switch)
            switch_number += 1
        return switches


    def add_switch_links(self, switches, switch_level):
        switch_counter = 0
        for i in range(0, switch_level - 1):
            for j in range(0, int(math.pow(2, i))):
                switch_counter += 1
                print("switch_counter", switch_counter)
                print("first", switch_counter * 2)
                print("second", switch_counter * 2 + 1)
                self.addLink(switches[switch_counter - 1], switches[switch_counter * 2 - 1])
                #self.addLink(switches[switch_counter - 1], switch_counter * 2)

        for i in range((switch_level - 1), 0, -1):
            level_switch = int(math.pow(2, i))
            for j in range(0, level_switch):
                switch_counter += 1
                print("switch_counter", switch_counter)
                print("first", switch_counter + (level_switch - j) + math.floor(j / 2))
                self.addLink(switches[switch_counter - 1], switches[switch_counter + (level_switch - j) + math.floor(j / 2) - 1])
        

    def add_hosts(self, switches):
        print("Add hosts")


topos = {'topology1': Topology1}

import pox.lib.packet as pkt
import pox.openflow.libopenflow_01 as of

import json
from host_generator import get_host

class ConfigReader:

    def __init__(self):
        self.config_name = 'rule_config'
        self.path = '../'+self.config_name

    def read(self):

        rules = self.load(self.path)
        rules = self.map_rules(rules)
        rules = self.build_rules(rules)

        return rules

    def load(self, path):
        with open(path+'.json', 'r') as f:
        #with open('./'+self.config_name+'.json', 'r') as f:
        #with open('/home/axelmpm/Repos/INTRO/redes-distribuidos-tps/tp3_topo2/rule_config.json', 'r') as f:
            rules = json.load(f)
        return rules

    def map_rules(self, rules):
        return {rule: self.map_params(params)
                for rule, params in rules.items()}
    
    def map_params(self, params):
        return {param: self.__map_param(param, value)
                for param, value in params.items()}

    def __map_param(self, param, value):

        if param == "dl_type":
            if value == "ip":
                return pkt.ethernet.IP_TYPE
            elif value == "ip6":
                return pkt.ethernet.IPV6_TYPE
            else:
                return pkt.ethernet.IP_TYPE

        elif param == "nw_proto":
            if value == "tcp":
                return pkt.ipv4.TCP_PROTOCOL
            elif value == "udp":
                return pkt.ipv4.UDP_PROTOCOL
            elif value == "icmp":
                return pkt.ipv4.ICMP_PROTOCOL
            else:
                return None

        elif param == "nw_src" or param == "nw_dst":
            if value == 'none':
                return None
            else:
                host_num = int(value.replace('host',''))
                _, ip, _ = get_host(host_num)
                return ip

        elif param == "tp_src" or param == "tp_dst":
            if value == 'none':
                return None
            else:
                port_num = int(value)
                return port_num
        else:
            return None

    def build_rules(self,rules):

        built_rules = []
        for _, params in rules.items():
            match = of.ofp_match(
                dl_type = params['dl_type'],
                nw_proto = params['nw_proto'],
                nw_src = params['nw_src'],
                nw_dst = params['nw_dst'],
                tp_src = params['tp_src'],
                tp_dst = params['tp_dst'],
            )

            built_rules.append(match)
        return built_rules

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import udp
from ryu.lib.packet import tcp
from ryu.lib.packet import icmp
import threading
from time import *
import random

global lock
global time
global lock2
global time2
global lock3
global time3
global lock4
global time4
lock = 0
time=1
lock2= 0
time2=1
lock3 = 0
time3=1
lock4= 0
time4=1

class TrafficSlicing(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]


    def locker():
        global lock
        global time
        while time > 0:
            lock=1
            time=time-1
            sleep(1)
            while time == 0:
                lock=0
                sleep(1)

    t = threading.Thread(target = locker)
    t.start()

    def locker2():
        global lock2
        global time2
        while time2 > 0:
            lock2=1
            time2=time2-1
            sleep(1)
            while time2 == 0:
                lock2=0
                sleep(1)

    t2 = threading.Thread(target = locker2)
    t2.start()    

    def locker3():
        global lock3
        global time3
        while time3 > 0:
            lock3=1
            time3=time3-1
            sleep(1)
            while time3 == 0:
                lock3=0
                sleep(1)

    t3 = threading.Thread(target = locker3)
    t3.start()   

    def locker4():
        global lock4
        global time4
        while time4 > 0:
            lock4=1
            time4=time4-1
            sleep(1)
            while time4 == 0:
                lock4=0
                sleep(1)

    t4 = threading.Thread(target = locker4)
    t4.start()     



    def __init__(self, *args, **kwargs):
        super(TrafficSlicing, self).__init__(*args, **kwargs)

        # outport = self.mac_to_port[dpid][mac_address]
        self.mac_to_port = {
            1: {"00:00:00:00:00:01": 4, "00:00:00:00:00:02": 5, "00:00:00:00:00:03": 6},
            4: {"00:00:00:00:00:04": 4, "00:00:00:00:00:05": 5, "00:00:00:00:00:06": 6},
        }
        self.slice_Vport = 9999
        self.slice_FTPport = 21


        # outport = self.slice_ports[dpid][slicenumber]
        self.slice_ports = {
            1: {1: 1, 2: 2, 3: 3},
            4: {1: 1, 2: 2, 3: 3}
        }
        self.end_swtiches = [1, 4]

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match, instructions=inst
        )
        datapath.send_msg(mod)

    def add_flow_timeout(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match, instructions=inst, idle_timeout= 5, hard_timeout= 55
        )
        datapath.send_msg(mod)


    def _send_package(self, msg, datapath, in_port, actions):
        data = None
        ofproto = datapath.ofproto
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data,
        )
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        global time
        global time2
        global lock
        global lock2
        global lock3
        global time3
        global lock4
        global time4

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        if dpid in self.mac_to_port:
            if dst in self.mac_to_port[dpid]:
                out_port = self.mac_to_port[dpid][dst]
                actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

                if (pkt.get_protocol(udp.udp) and pkt.get_protocol(udp.udp).dst_port == self.slice_Vport):
                    time=60
                    actions.insert(0,parser.OFPActionSetQueue(2))

                elif (pkt.get_protocol(tcp.tcp) and pkt.get_protocol(tcp.tcp).dst_port == self.slice_FTPport):
                    time2=60
                    actions.insert(0,parser.OFPActionSetQueue(2))

                elif (pkt.get_protocol(udp.udp) and pkt.get_protocol(udp.udp).dst_port != self.slice_Vport):
                    if lock==1:
                        actions.insert(0,parser.OFPActionSetQueue(1))
                    elif lock==0:
                        actions.insert(0,parser.OFPActionSetQueue(0))

                elif (pkt.get_protocol(tcp.tcp) and pkt.get_protocol(tcp.tcp).dst_port != self.slice_FTPport):
                    if lock2==1:
                        actions.insert(0,parser.OFPActionSetQueue(1))
                    elif lock2==0:
                        actions.insert(0,parser.OFPActionSetQueue(0))

                    
                match = datapath.ofproto_parser.OFPMatch(eth_dst=dst)
                self.add_flow_timeout(datapath, 1, match, actions)
                self._send_package(msg, datapath, in_port, actions)

            elif (pkt.get_protocol(udp.udp) and pkt.get_protocol(udp.udp).dst_port == self.slice_Vport):
                time3=60
                if lock4==1:
                    slice_number = 3
                elif lock4==0:
                    slice_number = random.randrange(2,4)
                out_port = self.slice_ports[dpid][slice_number]
                match = datapath.ofproto_parser.OFPMatch(
                    in_port=in_port,
                    eth_dst=dst,
                    eth_type=ether_types.ETH_TYPE_IP,
                    ip_proto=0x11,  # udp
                    udp_dst=self.slice_Vport,
                )

                actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                actions.insert(0,parser.OFPActionSetQueue(2))
                self.add_flow_timeout(datapath, 1, match, actions)
                self._send_package(msg, datapath, in_port, actions)


            elif (pkt.get_protocol(tcp.tcp) and pkt.get_protocol(tcp.tcp).dst_port == self.slice_FTPport):
                time4=60
                if lock3==1:
                    slice_number = 2
                elif lock3==0:
                    slice_number = random.randrange(2,4)
                out_port = self.slice_ports[dpid][slice_number]
                match = datapath.ofproto_parser.OFPMatch(
                    in_port=in_port,
                    eth_dst=dst,
                    eth_src=src,
                    eth_type=ether_types.ETH_TYPE_IP,
                    ip_proto=0x06,  # tcp
                    tcp_dst=self.slice_FTPport,
                )
                actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                actions.insert(0,parser.OFPActionSetQueue(2))
                self.add_flow_timeout(datapath, 1, match, actions)
                self._send_package(msg, datapath, in_port, actions)


            elif (pkt.get_protocol(udp.udp) and pkt.get_protocol(udp.udp).dst_port != self.slice_Vport):
                time3=60
                if lock4==1:
                    slice_number = 3
                elif lock4==0:
                    slice_number = random.randrange(2,4)
                out_port = self.slice_ports[dpid][slice_number]
                match = datapath.ofproto_parser.OFPMatch(
                    in_port=in_port,
                    eth_dst=dst,
                    eth_src=src,
                    eth_type=ether_types.ETH_TYPE_IP,
                    ip_proto=0x11,  # udp
                    udp_dst=pkt.get_protocol(udp.udp).dst_port,
                )
                actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                if lock==1:
                    actions.insert(0,parser.OFPActionSetQueue(1))
                elif lock==0:
                    actions.insert(0,parser.OFPActionSetQueue(0))

                self.add_flow_timeout(datapath, 1, match, actions)
                self._send_package(msg, datapath, in_port, actions)

            elif (pkt.get_protocol(tcp.tcp) and pkt.get_protocol(tcp.tcp).dst_port != self.slice_FTPport):
                time4=60
                if lock3==1:
                    slice_number = 2
                elif lock3==0:
                    slice_number = random.randrange(2,4)
                out_port = self.slice_ports[dpid][slice_number]
                match = datapath.ofproto_parser.OFPMatch(
                    in_port=in_port,
                    eth_dst=dst,
                    eth_src=src,
                    eth_type=ether_types.ETH_TYPE_IP,
                    ip_proto=0x06,  # tcp
                    tcp_dst=pkt.get_protocol(tcp.tcp).dst_port,
                )
                actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                if lock2==1:
                    actions.insert(0,parser.OFPActionSetQueue(1))
                elif lock2==0:
                    actions.insert(0,parser.OFPActionSetQueue(0))
                self.add_flow_timeout(datapath, 1, match, actions)
                self._send_package(msg, datapath, in_port, actions)

            elif pkt.get_protocol(icmp.icmp):
                slice_number = 1
                out_port = self.slice_ports[dpid][slice_number]
                match = datapath.ofproto_parser.OFPMatch(
                    in_port=in_port,
                    eth_dst=dst,
                    eth_src=src,
                    eth_type=ether_types.ETH_TYPE_IP,
                    ip_proto=0x01,  # icmp
                )
                actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                self.add_flow_timeout(datapath, 1, match, actions)
                self._send_package(msg, datapath, in_port, actions)

        elif dpid not in self.end_swtiches:
            out_port = ofproto.OFPP_FLOOD
            actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
            actions.insert(0,parser.OFPActionSetQueue(1))
            match = datapath.ofproto_parser.OFPMatch(in_port=in_port)
            self.add_flow(datapath, 1, match, actions)
            self._send_package(msg, datapath, in_port, actions)
            

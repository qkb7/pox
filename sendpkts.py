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
# from scapy.all import *
import time
import threading
import sys
import numpy as np
import matplotlib.pyplot as plt


### Classes ###
class Flow():
    def __init__(self, bytes_left=0, rate=0, duration=0):
        self.bytes_left = bytes_left
        self.rate = rate
        self.duration = duration


### Functions ###
def generateFlows(_sim_time, _client_rate):
    num_flows = _sim_time * _client_rate

    # See https://docs.scipy.org/doc/numpy-1.15.0/reference/generated/numpy.random.pareto.html for generating samples with numpy pareto; specifically, using the formula below to obtain classical pareto from the pareto2/lomax dist

    # generate sizes
    xm1 = 10.0  # scale
    a1 = 1.2  # shape
    sizes = sorted((np.random.pareto(a1, num_flows) + 1) * xm1)

    # generate durations
    xm2 = 0.001
    a2 = 1.5
    durs = sorted((np.random.pareto(a2, num_flows) + 1) * xm2)

    # sort/match to create flows
    flows = [None]*num_flows
    for i in range(num_flows):
        flows[i] = Flow(sizes[i], sizes[i]/durs[i], durs[i])

    cdf_sz = calc_cdf_fast(sizes)
    cdf_durs = calc_cdf_fast(durs)
    plt.plot(sizes, cdf_sz, color='green')
    plt.plot(durs, cdf_durs, color='red')
    plt.show()

    return flows


def calc_cdf_fast(arr):
    cdf = []
    for val in arr:
        count = 0
        for other_val in arr:
            if other_val <= val:
                count += 1
        cdf.append(float(count*1.0/len(arr)))
    return cdf


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
    sim_time = 180  # in seconds
    client_rate = 1000  # new incoming flows per second
    flows = generateFlows(sim_time, client_rate)
    exit(0)
    num_flooders = 1
    nf = len(flows)/num_flooders  # evenly divide flows for each flooder

    flooders = [None]*num_flooders
    for i in range(num_flooders):
        flooders[i] = threading.Thread(
            target=flood, args=(flows[int(i*nf):int((i+1)*nf)], i))
        flooders[i].start()

    # wait for flooders to finish
    for i in range(num_flooders):
        flooders[i].join()

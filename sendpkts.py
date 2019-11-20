#!/usr/bin/env python3.7
#
# File: sendpkts.py
#
# Description   : flooder script
# Created by    : Quinn Burke (qkb5007@psu.edu)
# Date          : November 2019
# Last Modified : November 2019


### Imports ###
from random import randint, shuffle
# from scapy.all import *
import time
import threading
import sys
import numpy as np
import matplotlib.pyplot as plt


### Classes ###
class Flow():
    def __init__(self, bytes_left=0, rate=0, duration=0, src_ip=None):
        self.bytes_left = bytes_left
        self.rate = rate
        self.duration = duration
        self.src_ip = src_ip


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
    used_ips = list()
    for i in range(num_flows):
        src_ip = "10.%s.%s.%s" % (str(randint(0, 255)), str(randint(0, 255)), str(randint(12, 99)))
        while src_ip in used_ips:
            src_ip = "10.%s.%s.%s" % (str(randint(0, 255)), str(randint(0, 255)), str(randint(12, 99)))
        used_ips.append(src_ip)
        flows[i] = Flow(sizes[i], sizes[i]/durs[i], durs[i], src_ip)

    gr = plt.GridSpec(1, 7, wspace=0.4, hspace=0.3)

    cdf_sz = calc_cdf_fast(sizes)
    plt.subplot(gr[:, :3])
    plt.xlabel('Flow size (B)')
    plt.ylabel('Cumulative Probability')
    plt.title('Flow Sizes')
    plt.plot(sizes, cdf_sz, color='green')

    cdf_durs = calc_cdf_fast(durs)
    plt.subplot(gr[:, 4:])
    plt.xlabel('Durations (s)')
    plt.ylabel('Cumulative Probability')
    plt.title('Flow Durations')
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


# def flood(_flows, flooder_idx):
def flood(_sim_time, _client_rate, _flows, _collection_interval):
    # print("flows: ", _flows, "\nflooder_idx: ", flooder_idx)
    # for i in range(1000):
    #     # print("[Flooder %d]: sending packets toward target 10.0.0.100..." %
    #     #       flooder_idx)
    #     print("[Flooder]: sending packets toward target 10.0.0.100...")
    #     # pkt = IP(src="10.%s.%s.%s" % (str(randint(0, 255)), str(
    #     #     randint(0, 255)), str(randint(12, 99))), dst="10.0.0.100")/ICMP()
    #     pkt = IP(src="10.%s.%s.%s" % (str(randint(0, 255)), str(randint(0, 255)), str(
    #         randint(12, 99))), dst="10.0.0.100")/ICMP()/Raw(load='0'*1472)  # max load is size 1472 because of 28 bytes ICMP packet, so everything can fit into 1500 MTU
    #     print(pkt.summary(), "(len: ", len(pkt), ")")
    #     # send(pkt, count=10, inter=0.1, iface="uph-eth0")
    #     send(pkt, count=1000000, iface="uph-eth0")

    active_flows = list()
    shuffle(_flows) # shuffle them randomly
    for i in range(_sim_time):
        # add new flows to active_flows list
        for i in range(_client_rate):
            # do this before updating existing flows (as opposed to simulator's order) so we dont have to update separately
            # add _client_rate flows to the active list so we can update activity below
            active_flows.add(_flows.pop())

        # update existing flows
        total_send_bytes = 0
        for flow in active_flows:
            if flow.duration == 0: # from ~line 563 in Simulator.java
                active_flows.remove(flow) # just remove (removed first in the simulator but we do it here)
            elif flow.duration <= (1.0/_collection_interval):
                total_send_bytes += flow.bytes_left # dump rest of bytes
                flow.bytes_left = 0 # update these to get removed next iteration
                flow.duration = 0
            elif flow.duration > (1.0/_collection_interval):
                if flow.bytes_left == 0: # line 617 (constant average rate)
                    active_flows.remove(flow)
                elif flow.bytes_left <= flow.rate:
                    total_send_bytes += flow.bytes_left # dump rest of bytes
                    flow.bytes_left = 0 # update these to get removed next iteration
                    flow.duration = 0
                elif flow.bytes_left > flow.rate:
                    total_send_bytes += flow.rate # dump rest of bytes
                    flow.bytes_left -= flow.rate
                    flow.duration -= (1.0/_collection_interval) # 1s collection interv granularity currently
                else
                    active_flows.remove(flow) # just remove (?)
            else:
                active_flows.remove(flow) # just remove (?)

        # send the flows toward the edge switch (ups) connecting to the servers (h1-h10)
        # do we want to update the flows then send, or do we want to update the flows and send at the same time above? We want to send with respect to each source so aggregating them here with total_send_bytes may not be the correct way;


        print("[Flooder]: sending packets toward target 10.0.0.100...")
        pkt = IP(src="10.%s.%s.%s" % (str(randint(0, 255)), str(randint(0, 255)), str(
            randint(12, 99))), dst="10.0.0.100")/ICMP()/Raw(load='0'*1472)  # 1500 byte MTU
        print(pkt.summary(), "(len: ", len(pkt), ")")
        # send(pkt, count=10, inter=0.1, iface="uph-eth0")
        send(pkt, count=1000000, iface="uph-eth0")


        time.sleep(1)


if __name__ == '__main__':
    # start = time.time_ns()
    # f = [0]*1800000
    # for i in range(1800000):
    #     f[i] = i
    # print("elapsed: ", str((time.time_ns()-start)/1e9), "s")
    # print("len: ", str(len(f)))
    # # print("f: ", f)
    # exit(0)

    # Note: only one server known to flooders "10.0.0.100"
    sim_time = 180  # in seconds
    client_rate = 10  # new incoming flows per second
    collection_interval = 1.0
    flows = generateFlows(sim_time, client_rate)
    # num_flooders = 1
    # nf = len(flows)/num_flooders  # evenly divide flows for each flooder
    # flooders = [None]*num_flooders
    # for i in range(num_flooders):
    #     flooders[i] = threading.Thread(
    #         target=flood, args=(flows[int(i*nf):int((i+1)*nf)], i))
    #     flooders[i].start()

    # # wait for flooders to finish
    # for i in range(num_flooders):
    #     flooders[i].join()
    flood(sim_time, client_rate, flows, collection_interval)

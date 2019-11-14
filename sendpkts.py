from random import randint
from scapy.all import *
for i in range(1000):
    pkt = IP(src="10.0.0.%s" % str(randint(0, 255)), dst="10.0.0.100")/ICMP()
    print(pkt.summary(), "(len: ", len(pkt) , ")")
    send(pkt, count=2, inter=0.1, iface="h2-eth0")
    # sr1(pkt, timeout=2, iface="docker0")
    #sr(IP(dst="192.169.0.1-255")/ICMP(), timeout=2, iface="docker0")

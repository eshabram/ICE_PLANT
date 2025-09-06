#!/usr/bin/env python3
import socket, struct

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Bind directly to usb0
server.setsockopt(socket.SOL_SOCKET, 25, b"usb0\0")  # 25 = SO_BINDTODEVICE
server.bind(('', 67))


# Always hand out this lease
OFFER_IP = '192.168.7.1'
ROUTER_IP = '192.168.7.2'   # Pi side
SUBNET_MASK = '255.255.255.0'

def ip2bytes(ip):
    return socket.inet_aton(ip)

print("ICE_PLANT: DHCP responder running on usb0")

while True:
    data, addr = server.recvfrom(1024)
    print(f"DHCP packet from {addr}, length={len(data)}")
    if data[236:240] != b'\x63\x82\x53\x63':  # magic cookie
        continue

    xid = data[4:8]
    mac = data[28:34]

    msgtype = None
    for i in range(240, len(data)):
        if data[i] == 53:  # DHCP Message Type
            msgtype = data[i+2]
            break

    if msgtype in (1, 3):  # DISCOVER or REQUEST
        # Build OFFER/ACK
        packet = b''
        packet += b'\x02'              # BOOTREPLY
        packet += b'\x01'              # HTYPE Ethernet
        packet += b'\x06'              # HLEN
        packet += b'\x00'              # HOPS
        packet += xid                  # XID
        packet += b'\x00\x00'          # SECS
        packet += b'\x00\x00'          # FLAGS
        packet += b'\x00\x00\x00\x00'  # CIADDR
        packet += ip2bytes(OFFER_IP)   # YIADDR (offered to client)
        packet += ip2bytes(ROUTER_IP)  # SIADDR
        packet += b'\x00\x00\x00\x00'  # GIADDR
        packet += mac + b'\x00'*10     # CHADDR
        packet += b'\x00'*192          # BOOTP legacy
        packet += b'\x63\x82\x53\x63'  # Magic cookie

        # DHCP options
        packet += b'\x35\x01' + (b'\x02' if msgtype == 1 else b'\x05')  # Message type: OFFER=2, ACK=5
        packet += b'\x36\x04' + ip2bytes(ROUTER_IP)                     # Server identifier
        packet += b'\x01\x04' + ip2bytes(SUBNET_MASK)                   # Subnet mask
        packet += b'\x03\x04' + ip2bytes(ROUTER_IP)                     # Router
        packet += b'\x06\x04' + ip2bytes(ROUTER_IP)                     # DNS
        packet += b'\x33\x04' + struct.pack("!I", 3600)                 # Lease time (1 hour)
        packet += b'\xff'                                               # End

        try:
            server.sendto(packet, ('255.255.255.255', 68))
        except OSError as e:
            if e.errno == 101:  # Network unreachable
                print("usb0 not ready yet, ignoring")
                continue
            else:
                raise


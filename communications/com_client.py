import json
import socket
import struct
import time
from select import select

from communications.com_constants import *
from communications.com_link import Link
from communications.common import ComRGR, ComMsg


class ComClient(ComRGR):

    # check if server is already linked
    def __check_server(self, name, token):



    # CALLBACK (return true to stop network loop)
    def __register(self, msg, addr, port):
        # check this is a discovery message
        if 'topic' not in msg or 'nekot' not in msg or 'name' not in msg:
            print("Skip useless message")
            return False

        if msg['topic'] != TOPIC_REGISTERED:
            print("Skip useless message")
            return False



                # store server information
                self.__srvr_name = msg['server']
                self.__srvr_addr = addr
                self.__srvr_port = port
                print(f"Client received DISCOVER message (server:'{self.__srvr_name}' @({self.__srvr_addr},{self.__srvr_port}).")
                # Send back REGISTER message
                msg['topic' ] = 'REGISTER'
                msg['client'] = (socket.gethostname(), self._MCASTSocket.getsockname())
                self.send(msg)
            return True
        return False

    def _set_MCAST(self):
        try:
            self._MCASTSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            ttl = struct.pack('b', 1)
            self._MCASTSocket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        except socket.error as se:
            print(se)
            exit(1)

    def __init__(self,
                 mcast_addr=ComRGR.COM_MCAST_GRP,
                 mcast_port=ComRGR.COM_MCAST_PRT,
                 timeout=5):
        super().__init__(mcast_addr, mcast_port, timeout)
        self.__server = {
            'name' : None,
            'token': None
        }


    def register(self):
        print("Start registering...")
        # Send register message
        msg = ComMsg()
        msg['topic'] = 'REGISTER'
        self.send(msg)
        # wait for server to send ACK
        self._process(self.__register)
        print("End of registering")

    def send(self, msg):
        print(f"Sending multicast {msg}...")
        sent = self._MCASTSocket.sendto(msg.byte_data, (self._mcast_grp, self._mcast_prt))
        if sent < 0:
            print("[ERROR] Impossible to send message !")
            exit(1)

    def receive(self):
        result = super()._internal_receive()
        if result is not None:
            # Check if this message was for us : the sender
            # must be the server found during the registering step
            msg, addr, port = result
            print(f"Received {msg} from ({addr},{port}).")
        return result


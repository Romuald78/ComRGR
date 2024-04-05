import json
import socket
import struct
from select import select

from communications.com_constants import *
from communications.com_link import Link
from communications.common import ComRGR, ComMsg


class ComServer(ComRGR):

    # create client key
    @staticmethod
    def __create_key(addr, port):
        return f"{addr}-{port}"

    # check the sender is one of the registered clients
    def __check_client(self, addr, port):
        key = ComServer.__create_key(addr, port)
        return key in self.__clients

    # CALLBACK (return true to stop network loop)
    def __add_client(self, msg, addr, port):
        # check params
        if 'topic' not in msg or 'token' not in msg or 'name' not in msg:
            print("Skip useless message")
            return False
        if msg['topic'] not in [TOPIC_REGISTER, TOPIC_VALID]:
            print("Skip useless message")
            return False

        # get key and check if this is a creation or an update
        if self.__check_client(addr, port):
            print(f"Updating client ({addr}, {port}).")
        else:
            print(f"Adding client ({addr}, {port}).")
        # update client structure
        key = ComServer.__create_key(addr, port)
        self.__clients[key] = {
            'name' : msg['name'],
            'token': msg['token'],
            'addr' : addr,
            'port' : port,
            'valid': False
        }

        # Sending REGISTERED message
        msg = ComMsg()
        msg['topic'] = TOPIC_REGISTERED
        msg['nekot'] = msg['token'][::-1]
        msg['name' ] = socket.gethostname()
        self.send(msg, key)
        return False

    def __remove_client(self):
        # TODO
        pass

    def _set_MCAST(self):
        try:
            self._MCASTSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            group = socket.inet_aton(self._mcast_grp)
            mreq = struct.pack('4sL', group, socket.INADDR_ANY)
            self._MCASTSocket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            self._MCASTSocket.bind(('', self._mcast_prt))
        except socket.error as msg:
            print(msg)
            exit(1)

    def __init__(self,
                 mcast_addr=ComRGR.COM_MCAST_GRP,
                 mcast_port=ComRGR.COM_MCAST_PRT,
                 timeout=5):
        super().__init__(mcast_addr, mcast_port, timeout)
        # # Locals
        self.__clients = {}

    def discover(self):
        print("Start discovering...")
        # waiting for register messages
        self._process(self.__add_client)

    def send(self, msg, key):
        print(f"Sending {msg} to ({key})...")
        addr = self.__clients[key]['addr']
        port = self.__clients[key]['port']
        sent = self._MCASTSocket.sendto(msg.byte_data, (addr, port))
        if sent < 0:
            print("[ERROR] Impossible to send message !")
            exit(1)

    def receive(self):
        result = super()._internal_receive()
        if result is not None:
            # Check if this message was for us :
            # the sender must be one of the registered clients
            msg, addr, port = result
            print(f"Received {msg} from ({addr},{port}).")
        return result

import json
import socket
import struct
import time
from select import select

from communications.com_constants import *
from communications.com_link import Link
from communications.common import ComRGR, ComMsg


class ComClient(ComRGR):

    def __log(self, msg, log_type):
        super()._log(msg, LOG_CLIENT, log_type)

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
        self.__server = None

    def is_registered(self):
        return self.__server is not None

    def register(self):
        # Send register message
        msg = ComMsg()
        msg['topic'] = 'REGISTER'
        self.send(msg)

    def send(self, msg):
        # Always add the local token in the message before sending it
        msg['token'] = self._token
        # Prepare specific data
        tkn = TOKEN_MULTI
        if self.__server is not None:
            tkn = self.__server['token']
        self._internal_prepare(msg, tkn)
        # Send message to server (multicast)
        self.__log(f"multicast {msg}.", LOG_INF)
        sent = self._MCASTSocket.sendto(msg.byte_data, (self._mcast_grp, self._mcast_prt))
        if sent < 0:
            self.__log("Impossible to send message !", LOG_ERR)
            exit(1)

    def receive(self):
        result = super()._internal_receive()
        if result is not None:
            msg, addr, port = result
            self.__log(f"received {msg}.", LOG_INF)
            # check this is a discovery message
            if msg['topic'] == TOPIC_REGISTERED:
                if self.__server is None:
                    # store server information
                    self.__server = {
                        'name' : msg['name'],
                        'addr' : addr,
                        'port' : port,
                        'token': msg['token']
                    }
                    # Send VALID message back
                    msg2 = ComMsg()
                    msg2['topic'] = TOPIC_VALID
                    self.send(msg2)
                else:
                    # ignore message
                    self.__log(f"ignore '{TOPIC_REGISTERED}' message.", LOG_WRN)

                # message processed
                result = None
        return result


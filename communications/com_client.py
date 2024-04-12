import json
import socket
import struct
import time
from select import select

from communications.com_constants import *
from communications.common import ComRGR, ComMsg


class ComClient(ComRGR):

    def __log(self, msg, log_type, way_out=None):
        super()._log(msg, LOG_CLIENT, log_type, way_out)

    def _set_MCAST(self):
        try:
            self._MCASTSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            ttl = struct.pack('b', 1)
            self._MCASTSocket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        except socket.error as se:
            print(se)
            exit(1)

    def _set_DRCT(self):
        try:
            addr = self.__server['addr']
            port = self.__server['port']
            self._DRCTSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            self._DRCTSocket.connect((addr, port))

        except socket.error as msg:
            self.__log(msg, LOG_ERR)
            exit(1)

    def __init__(self,
                 mcast_addr=ComRGR.COM_MCAST_GRP,
                 mcast_port=ComRGR.COM_MCAST_PRT,
                 timeout=5):
        super().__init__(mcast_addr, mcast_port, ComRGR.COM_SERVER_PRT, timeout)
        self.__server = None

    @property
    def id(self):
        res = None
        if self.__server is not None:
            if 'id' in self.__server:
                res = self.__server['id']
        return res

    def is_registered(self):
        return self.__server is not None

    def register(self):
        # Wait for any registering message coming from server
        # flush any other message because registering
        # is handled inside the receive method
        self.receive()
        # Send register message if needed
        if  not self.is_registered():
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
        # if direct connection is established
        if self.__server is not None:
            # Send message to server (direct)
            id = self.__server['id']
            id = f" (cli #{id})"
            self.__log(f"{msg['topic']}{id}", LOG_MSG, LOG_WAY_OUT)
            addr = self.__server['addr']
            port = self.__server['port']
            sent = self._DRCTSocket.sendto(msg.byte_data, (addr, port))
        else:
            # Send message to server (multicast)
            self.__log(f"{msg['topic']}", LOG_INF, LOG_WAY_OUT)
            sent = self._MCASTSocket.sendto(msg.byte_data, (self._mcast_grp, self._mcast_prt))
        if sent < 0:
            self.__log("Impossible to send message !", LOG_ERR)
            exit(1)

    def receive(self):
        result = None
        try:
            result = super()._internal_receive()
        except Exception as ex:
            self.__log("Connection with server lost.", LOG_ERR)
            self.__log(f"{ex}", LOG_ERR)
            # reset server state
            self.__server = None
        if result is not None:
            msg, addr, port = result
            id = ''
            if self.is_registered():
                id = self.__server['id']
                id = f" (cli #{id})"
            self.__log(f"{msg['topic']}{id}", LOG_MSG, LOG_WAY_IN)
            # check this is a discovery message
            if msg['topic'] == TOPIC_REGISTERED:
                if self.__server is None:
                    # store server information
                    self.__server = {
                        'name' : msg['name'],
                        'addr' : addr,
                        'port' : self._drct_prt,
                        'token': msg['token'],
                        'id'   : msg['id']
                    }
                    # Establish direct connection with server
                    self._set_DRCT()
                    # Send VALID message back
                    msg2 = ComMsg()
                    msg2['topic'] = TOPIC_VALID
                    self.send(msg2)
                else:
                    # ignore message
                    self.__log(f"ignore '{TOPIC_REGISTERED}' message.", LOG_WRN)
        return result


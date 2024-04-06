import json
import socket
import struct
import sys
from select import select

from communications.com_constants import *
from communications.com_link import Link
from communications.common import ComRGR, ComMsg


class ComServer(ComRGR):

    # create client key
    @staticmethod
    def __create_key(addr, port):
        return f"{addr}-{port}"

    # CALLBACK (return true to stop network loop)
    def __update_client(self, msg, addr, port):
        # Locals
        key    = ComServer.__create_key(addr, port)
        rgstr  = msg['topic'] == TOPIC_REGISTER
        vld    = msg['topic'] == TOPIC_VALID
        resend = False
        cli    = None
        # Update key
        if key in self.__clients:
            cli = self.__clients[key]
        # REGISTER MESSAGE
        if rgstr:
            if cli is None:
                # add new client
                self.__clients[key] = {
                    'name'   : msg['name'],
                    'token'  : msg['token'],
                    'addr'   : addr,
                    'port'   : port,
                    'counter': 0,
                    'valid'  : False
                }
                resend = True
            elif not vld:
                # Resend REGISTERED message for not valid clients
                resend = True
            else:
                # ignore message
                self.__log(f"ignore '{TOPIC_REGISTER}' message.", LOG_WRN)
            # (re)send REGISTERED message
            # Send REGISTERED message
            msg2 = ComMsg()
            msg2['topic'] = TOPIC_REGISTERED
            self.send_one(msg2, key)
        elif vld:
            if cli is not None and not cli['valid']:
                cli['valid'] = True
            else:
                # ignore message
                self.__log(f"ignore '{TOPIC_VALID}' message.", LOG_WRN)

    def __remove_client(self, key):
        if key in self.__clients:
            self.__log(f"remove client {key}", LOG_INF)
            del self.__clients[key]

    def __log(self, msg, log_type):
        super()._log(msg, LOG_SERVER, log_type)

    def _set_MCAST(self):
        try:
            self._MCASTSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            group = socket.inet_aton(self._mcast_grp)
            mreq = struct.pack('4sL', group, socket.INADDR_ANY)
            self._MCASTSocket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            self._MCASTSocket.bind(('', self._mcast_prt))
        except socket.error as msg:
            self.__log(msg, LOG_ERR)
            exit(1)

    def __init__(self,
                 mcast_addr=ComRGR.COM_MCAST_GRP,
                 mcast_port=ComRGR.COM_MCAST_PRT,
                 timeout=5):
        super().__init__(mcast_addr, mcast_port, timeout)
        # # Locals
        self.__clients = {}

    def send_one(self, msg, key):
        # Always add the local token in the message before sending it
        msg['token'] = self._token
        # Prepare specific data
        self._internal_prepare(msg, self.__clients[key]['token'])
        # Send message to one
        self.__log(f"send {msg} to ({key}).", LOG_INF)
        addr = self.__clients[key]['addr']
        port = self.__clients[key]['port']
        sent = self._MCASTSocket.sendto(msg.byte_data, (addr, port))
        if sent < 0:
            self.__log("Impossible to send one message !", LOG_ERR)
            exit(1)

    def send_all(self, msg):
        # Always add the local token in the message before sending it
        msg['token'] = self._token
        # Prepare specific data
        self._internal_prepare(msg, TOKEN_MULTI)
        # Send message to all
        self.__log(f"send {msg} to all.", LOG_INF)
        # TODO : try to use the multicast to send data to all clients
        #        instead of a loop
        #        sent = self._MCASTSocket.sendto(msg.byte_data, (self._mcast_grp, self._mcast_prt))
        #        if sent < 0:
        #            self.__log("Impossible to send multicast message !", LOG_ERR)
        #            exit(1)
        for key in self.__clients:
            self.send_one(msg, key)

    def receive(self):
        result = super()._internal_receive()
        if result is not None:
            msg, addr, port = result
            # the sender must be one of the registered clients
            self.__log(f"Received {msg} from ({addr},{port}).", LOG_INF)

            # handle client REGISTERING if needed
            if msg['topic'] in [TOPIC_REGISTER, TOPIC_VALID]:
                self.__update_client(msg, addr, port)
                result = None
        return result

    @property
    def nb_clients(self):
        return len(self.__clients)

    @property
    def nb_valid(self):
        v = 0
        for k in self.__clients:
            if self.__clients[k]['valid']:
                v += 1
        return v

    def client_key(self, i):
        keys = list(self.__clients.keys())
        return keys[i]

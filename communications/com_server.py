import datetime
import json
import socket
import struct
import sys
from select import select

from communications.com_constants import *
from communications.common import ComRGR, ComMsg
from datetime import datetime


class ComServer(ComRGR):

    # create client key
    @staticmethod
    def __create_key(addr, token):
        return f"{addr}-{token}"

    # CALLBACK (return true to stop network loop)
    def __update_client(self, msg, addr, port):
        # Locals
        rgstr  = msg['topic'] == TOPIC_REGISTER
        vld    = msg['topic'] == TOPIC_VALID
        token  = msg['token']
        resend = False
        cli    = None
        # Update key
        key = ComServer.__create_key(addr, token)
        if key in self.__clients:
            cli = self.__clients[key]
        # REGISTER MESSAGE
        if rgstr:
            if cli is None:
                # increase nb of registered clients
                # since the beginning
                self.__max_client_nb += 1
                # add new client
                self.__clients[key] = {
                    'name'     : msg['name'],
                    'id'       : self.__max_client_nb,
                    'token'    : msg['token'],
                    'addr'     : addr,
                    'port'     : port,
                    'counter'  : 0,
                    'valid'    : False,
                    'last_seen': datetime.now()
                }
                resend = True
            elif not vld:
                # Resend REGISTERED message for not valid clients
                resend = True
            else:
                # ignore message
                self.__log(f"ignore '{TOPIC_REGISTER}' message", LOG_WRN)
            # (re)send REGISTERED message
            if resend:
                msg2 = ComMsg()
                msg2['topic']    = TOPIC_REGISTERED
                msg2['id']       = self.__clients[key]['id']
                msg2['drct_prt'] = self._drct_prt
                self.send_one(msg2, key)
        elif vld:
            if cli is not None and not cli['valid']:
                # set valid + update addr/port (direct socket)
                self.__clients[key]['valid'] = True
                self.__clients[key]['addr' ] = addr
                self.__clients[key]['port' ] = port
            else:
                # ignore message
                self.__log(f"ignore '{TOPIC_VALID}' message", LOG_WRN)

    def __remove_client(self, key):
        if key in self.__clients:
            self.__log(f"remove client {key}", LOG_INF)
            del self.__clients[key]

    def __log(self, msg, log_type, way_out=None):
        super()._log(msg, LOG_SERVER, log_type, way_out)

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

    def _set_DRCT(self):
        try:
            self._DRCTSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            self._DRCTSocket.bind(('', self._drct_prt))
        except socket.error as msg:
            self.__log(msg, LOG_ERR)
            exit(1)

    def __init__(self,
                 mcast_addr=ComRGR.COM_MCAST_GRP,
                 mcast_port=ComRGR.COM_MCAST_PRT,
                 timeout=5):
        super().__init__(mcast_addr,
                         mcast_port,
                         ComRGR.COM_SERVER_PRT,
                         timeout)
        # Locals
        self.__clients = {}
        # Create specific socket for direct communication
        self._set_DRCT()
        # Nb clients
        self.__max_client_nb = 0

    def __check_connectivity(self):
        keys_to_remove = []
        for key in self.__clients:
            before = self.__clients[key]['last_seen']
            now    = datetime.now()
            if (now - before).seconds > LAST_SEEN_TIMEOUT:
                # this client can be removed from the client list
                # because it has been too long we have heard from it
                keys_to_remove.append(key)
        for key in keys_to_remove:
            self.__log(f"remove client {self.__clients[key]}", LOG_WRN)
            del self.__clients[key]

    def __update_connectivity(self, msg, addr, port):
        token = msg['token']
        key = self.__create_key(addr, token)
        if key in self.__clients:
            id = self.__clients[key]['id']
            self.__log(f"update connectivity (#{id})", LOG_INF)
            self.__clients[key]['last_seen'] = datetime.now()
            return key
        return None

    def send_one(self, msg, key):
        # Always add the local token in the message before sending it
        msg['token'] = self._token
        # Prepare specific data
        self._internal_prepare(msg, self.__clients[key]['token'])
        # Send message to one
        id = self.__clients[key]['id']
        self.__log(f"{msg['topic']} to (#{id})", LOG_MSG, LOG_WAY_OUT)
        addr = self.__clients[key]['addr']
        port = self.__clients[key]['port']
        # check if this is a direct message or a MULTICAST answer
        if self.__clients[key]['valid']:
            sent = self._DRCTSocket.sendto(msg.byte_data, (addr, port))
        else:
            sent = self._MCASTSocket.sendto(msg.byte_data, (addr, port))
        if sent < 0:
            self.__log("Impossible to send one message !", LOG_ERR)
            exit(1)

    def send_all(self, msg):
        # Always add the local token in the message before sending it
        msg['token'] = self._token
        # Prepare specific data
        self._internal_prepare(msg, TOKEN_MULTI)
        # Send message to all (one by one)
        for key in self.__clients:
            self.send_one(msg, key)

    def receive(self):
        result = super()._internal_receive()
        if result is not None:
            msg, addr, port = result
            # update connectivity
            key = self.__update_connectivity(msg, addr, port)

            # the sender must be one of the registered clients
            if key is not None:
                id = self.__clients[key]['id']
                self.__log(f"{msg['topic']} from (#{id})", LOG_MSG, LOG_WAY_IN)

            # handle client REGISTERING if needed
            if msg['topic'] in [TOPIC_REGISTER, TOPIC_VALID]:
                self.__update_client(msg, addr, port)
        else:
            # in case there is no message to process
            # we update the client information
            self.__check_connectivity()
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

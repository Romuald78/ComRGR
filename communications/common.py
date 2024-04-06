import pickle
import socket
import sys
from random import randint
from select import select

from communications.com_constants import *


class ComRGR:


    COM_MCAST_GRP  = "224.25.26.27"
    COM_MCAST_PRT  = 12345
    COM_SERVER_PRT = 54321
    COM_VERSION = 'v0.1'

    def _log(self, msg, src, log_type):
        clr = LOG_CLR[log_type]
        txt = f"{CLR_NAME}{src}{clr}{log_type} {msg}"
        print(txt, file=sys.stderr)

    def _set_MCAST(self):
        raise NotImplementedError()

    def __init__(self, mcast_addr, mcast_port, timeout):
        self._MCASTSocket = None
        self._mcast_grp = mcast_addr
        self._mcast_prt = mcast_port
        self._timeout   = timeout
        self._token     = str(randint(100000000, 999999999))
        self._set_MCAST()
        print(f"Starting {socket.gethostname()} as {self.__class__.__name__}...")

    def _internal_prepare(self, msg, dest_token):
        msg['nekot'] = dest_token[::-1]

    def _internal_receive(self):
        result = None
        ins, outs, excs = select([self._MCASTSocket], [self._MCASTSocket], [])
        if ins:
            dataPair = self._MCASTSocket.recvfrom(1280)
            data   = dataPair[0]
            # print(len(data), file=sys.stderr)
            addr   = dataPair[1][0]
            port   = dataPair[1][1]
            try:
                msg    = ComMsg(data)
            except Exception as ex:
                print(ex, file=sys.stderr)
                print(dataPair, file=sys.stderr)
                exit(99)
            result = (msg, addr, port)

        return result


class ComMsg:

    @staticmethod
    def __serialize(data_dict):
        return bytearray(pickle.dumps(data_dict))

    @staticmethod
    def __unserialize(data_bytes):
        return pickle.loads(data_bytes)

    # payload is a dictionary with all useful data
    # Be careful the while data do not exceed 1024
    def __init__(self, data_bytes=None):
        if data_bytes is not None:
            self.__data = ComMsg.__unserialize(data_bytes)
        else:
            self.__data = {
                'name' : socket.gethostname()
            }

    @property
    def byte_data(self):
        return ComMsg.__serialize(self.__data)

    def __iter__(self):
        return self.__data.__iter__()

    def __getitem__(self, item):
        return self.__data[item]

    def __setitem__(self, item, value):
        self.__data[item] = value

    def __str__(self):
        return str(self.__data)

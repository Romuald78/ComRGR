import pickle
import socket
import sys
from random import randint
from select import select

from communications.com_constants import *


class ComRGR:

    COM_MCAST_GRP  = "224.25.26.27"
    COM_MCAST_PRT  = 23456
    COM_SERVER_PRT = 12345
    COM_VERSION    = 'v0.1'

    @staticmethod
    def wait_ENTER():
        res = False
        i, o, e = select([sys.stdin], [], [], 0.1)
        if i:
            usr = sys.stdin.readline()
            res = True
        return res

    @staticmethod
    def __one_receive(sckt):
        result = None
        # Check if socket exists
        if sckt is not None:
            # First check if there is something coming from the direct socket
            ins, outs, excs = select([sckt], [sckt], [])
            if ins:
                dataPair = sckt.recvfrom(1280)
                data = dataPair[0]
                addr = dataPair[1][0]
                port = dataPair[1][1]
                try:
                    msg = ComMsg(data)
                    result = (msg, addr, port)
                except Exception as ex:
                    print(ex, file=sys.stderr)
                    print(sckt)
                    print(dataPair, file=sys.stderr)
                    exit(99)
        return result

    def _log(self, msg, src, log_type, way_out=None):
        clr = LOG_CLR[log_type]
        way = {LOG_WAY_OUT:'[>]', LOG_WAY_IN:'[<]', None: '   '}[way_out]
        txt = f"{CLR_NAME}{src}{CLR_FLOW}{way}{clr}{msg}{CLR_NONE}"
        print(txt, file=sys.stderr)

    def _set_MCAST(self):
        raise NotImplementedError()

    def _set_DRCT(self):
        raise NotImplementedError()

    def __init__(self, mcast_addr, mcast_port, drct_port, timeout):
        self._MCASTSocket = None
        self._mcast_grp   = mcast_addr
        self._mcast_prt   = mcast_port
        self._DRCTSocket  = None
        self._drct_prt    = drct_port

        self._timeout   = timeout
        self._token     = str(randint(100000000, 999999999))
        self._set_MCAST()
        print(f"Starting {socket.gethostname()} as {self.__class__.__name__} with token '{self._token}'...")

    def _internal_prepare(self, msg, dest_token):
        msg['nekot'] = dest_token[::-1]

    def _internal_receive(self):
        # Check DIRECT message
        result = ComRGR.__one_receive(self._DRCTSocket )
        # If no direct message, check MULTICAST message
        if result is None:
            result = ComRGR.__one_receive(self._MCASTSocket)
        # return message if any
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

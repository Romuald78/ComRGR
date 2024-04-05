import json
import pickle
import socket
import time
from random import randint
from select import select


class ComRGR:

    COM_MCAST_GRP  = "224.25.26.27"
    COM_MCAST_PRT  = 12345
    COM_SERVER_PRT = 54321
    COM_VERSION = 'v0.1'

    def _set_MCAST(self):
        raise NotImplementedError()

    def _reset_MCAST(self):
        raise NotImplementedError()

    def _process(self, callback):
        # start time measurement (timeout)
        start_time = time.time()
        # wait for answers
        while(True):
            result = self._internal_receive()
            if result is not None:
                msg, addr, port = result
                if callback(msg, addr, port):
                    break
            else:
                # make the server waits a while
                time.sleep(0.05)
            # check timeout
            end_time = time.time()
            if end_time - start_time > self._timeout:
                break

    def __init__(self, mcast_addr, mcast_port, timeout):
        self._MCASTSocket = None
        self._mcast_grp = mcast_addr
        self._mcast_prt = mcast_port
        self._timeout   = timeout
        self._set_MCAST()
        print(f"Starting {socket.gethostname()} as {self.__class__.__name__}...")

    def _internal_receive(self):
        result = None
        ins, outs, excs = select([self._MCASTSocket], [self._MCASTSocket], [])
        if ins:
            dataPair = self._MCASTSocket.recvfrom(1024)
            data   = dataPair[0]
            addr   = dataPair[1][0]
            port   = dataPair[1][1]
            msg    = ComMsg(data)
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
            self.__data = {}

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

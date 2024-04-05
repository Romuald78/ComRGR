import sys
import time
from random import randint

from communications.com_client import ComClient
from communications.com_server import ComServer
from communications.common import ComMsg

if __name__ == '__main__':

    # check role
    role = None
    if len(sys.argv) > 1:
        if sys.argv[1] in ["server", "client"]:
            role = sys.argv[1]
        else:
            print("Bad client/server argument")
            exit(1)

    # launch process
    if role == "server":
        cs = ComServer(timeout=3600)
        cs.discover()

        # msg = ComMsg()
        # msg['topic'] = "INFO"
        # msg['data' ] = "info message to transmit"
        # cs.send(msg)
        #
        # result = None
        # while True:
        #     result = cs.receive()
        #     if result is not None:
        #         print("forwarding", result[0], result[1], result[2])
        #         # TODO : test : SEND TO SPECIFIC CLIENT
        #         cs.send(result[0])
        #     time.sleep(0.05)

    elif role == "client":
        cc = ComClient(timeout=10)
        cc.register()

        # result = None
        # first = True
        # while True:
        #     result = cc.receive()
        #     if result is not None:
        #         print("received", result[0], result[1], result[2])
        #         if first:
        #             msg = ComMsg()
        #             msg['token'] = randint(100000, 999999)
        #             print(f"Client sending token {msg['token']}...")
        #             cc.send(msg)
        #             first = False
        #
        #     time.sleep(0.05)


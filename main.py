import select
import sys
import time

from communications.com_client    import ComClient
from communications.com_constants import *
from communications.com_server    import ComServer
from communications.common import ComMsg, ComRGR

if __name__ == '__main__':

    # check role
    role = None
    if len(sys.argv) > 1:
        if sys.argv[1] in ["server", "client"]:
            role = sys.argv[1]
        else:
            print("Bad client/server argument")
            exit(1)

    # ===============================================
    # SERVER
    # ===============================================
    if role == "server":

        cs = ComServer()
        print("WAITING for clients to join game...")

        waiting_for_clients = True
        while waiting_for_clients:
            # Flags for external events (message or keyboard)
            received_msg = False
            received_usr = False

            # Receive any message from clients
            result = cs.receive()
            # Process message if needed
            if result is not None:
                msg, addr, port = result
                received_msg = True

            # Receive any input on key
            if ComRGR.wait_ENTER():
                received_msg        = True
                waiting_for_clients = False

            # wait if no action performed
            if not received_msg and not received_usr:
                time.sleep(SERVER_REGISTER_SLEEP)

        # Now server has started com with registered clients only
        print("Game has STARTED : waiting for continuous messages...")

        msg = ComMsg()
        msg['topic']   = 'TEST_ALL'
        msg['counter'] = 0
        msg['data']    = 'abcdefghijklmnopqrstuvwxyz'
        cs.send_all(msg)

        while True:
            # Receive any message from clients
            result = cs.receive()
            # Process message or wait
            if result is not None:
                msg, addr, port = result
                if msg['topic'] == 'TEST_CLIENT':
                    msg2 = ComMsg()
                    msg2['topic'  ] = 'TEST_ONE'
                    msg2['counter'] = msg['counter'] + 1
                    msg2['data'   ] = 'abcdefghijklmnopqrstuvwxyz'[::-1]
                    cs.send_one(msg2, addr, port)
            else:
                time.sleep(DIRECT_COM_SLEEP)


    # ===============================================
    # CLIENT
    # ===============================================
    elif role == "client":
        cc = ComClient()
        print("Started REGISTERING phase...")

        # Wait to be fully registered
        while not cc.is_registered():
            # Send register message
            cc.register()
            # Wait for a while
            time.sleep(CLIENT_REGISTER_SLEEP)

        print("REGISTERED successfully. Wait for 2 seconds...")
        print("Game has STARTED : waiting for continuous messages...")
        while True:
            # Receive any message from clients
            result = cc.receive()
            # Process message or wait
            if result is not None:
                msg, addr, port = result
                if msg['topic'] == 'TEST_ONE' or msg['topic'] == 'TEST_ALL':
                    if msg['counter'] >= 500*2:
                        break
                    msg2 = ComMsg()
                    msg2['topic'  ] = 'TEST_CLIENT'
                    msg2['counter'] = msg['counter'] + 1
                    msg2['data'   ] = 'abcdefghijklmnopqrstuvwxyz'[::-1]
                    cc.send(msg2)
            else:
                time.sleep(DIRECT_COM_SLEEP)


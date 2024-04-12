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

        count = 100
        while True:
            # Receive any message from clients
            result = cs.receive()
            # Process message or wait
            if result is not None:
                msg, addr, port = result
            elif count>0:
                msg = ComMsg()
                msg['topic'] = 'TEST_ALL'
                msg['data'] = 'abcdefghijklmnopqrstuvwxyz'
                cs.send_all(msg)
                count -= 1

                time.sleep(DIRECT_COM_SLEEP)

            else:
                break

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
        time.sleep(2)
        print("Game has STARTED : waiting for continuous messages...")
        count = 100
        while True:
            # Receive any message from clients
            result = cc.receive()
            # Process message or wait
            if result is not None:
                msg, addr, port = result
            elif count>0:
                msg = ComMsg()
                msg['topic'] = 'TEST_SERVER'
                msg['data'] = 'abcdefghijklmnopqrstuvwxyz'[::-1]
                cc.send(msg)
                count -= 1

                time.sleep(DIRECT_COM_SLEEP)
            else:
                break


import sys
import time

from communications.com_client import ComClient
from communications.com_constants import COM_SLEEP, TOPIC_VALID
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

    # ===============================================
    # SERVER
    # ===============================================
    if role == "server":
        maxi = 1
        if len(sys.argv) > 2:
            maxi = int(sys.argv[2])
            maxi = min(20, maxi)

        debug = True
        cs = ComServer()
        print(f"maximum clients = {maxi}")
        while True:
            print(f"{cs.nb_valid}/{cs.nb_clients}")

            # Receive any message from clients
            result = cs.receive()
            # Process message or wait
            if result is not None:
                msg, addr, port = result
            else:
                time.sleep(COM_SLEEP)

            # send one global message to all clients
            if cs.nb_valid >= maxi and debug:
                start = time.time()
                # Build message with number
                msg = ComMsg()
                msg['topic'] = 'SEND_ALL'
                msg['data'] = bytearray(1000)
                cs.send_all(msg)
                debug = False
                break

        end = time.time()
        print(f"Sent messages to {cs.nb_clients} clients in {end-start} sec.")
        start = end
        maxi = cs.nb_clients
        count = 0
        while  count<maxi :
            # Receive any message from clients
            result = cs.receive()
            # Process message or wait
            if result is not None:
                msg, addr, port = result
                if msg['topic'] == 'ANSWER_SERVER':
                    count += 1
            else:
                time.sleep(COM_SLEEP)
        end = time.time()
        print(f"Received messages from {count} clients in {end-start} sec.")


    # ===============================================
    # CLIENT
    # ===============================================
    elif role == "client":
        cc = ComClient()
        while True:
            # Send register message if needed
            if not cc.is_registered():
                cc.register()

            # Receive any message from server
            result = cc.receive()
            # Process message or wait
            if result is not None:
                # Process message
                msg, addr, port = result
                if msg['topic'] == 'SEND_ALL':
                    msg2 = ComMsg()
                    msg2['topic'] = 'ANSWER_SERVER'
                    msg2['data' ] = bytearray(1000)
                    cc.send(msg2)
                    break
            else:
                # Wait
                time.sleep(COM_SLEEP)

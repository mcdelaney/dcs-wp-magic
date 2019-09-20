#!/bin/python3
import logging
import sys
import socket
import select
from dcs import core, wp_ctrl

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

RECV_BUFFER = 4096
PORT = 8888
HOST = '127.0.0.1'



def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((HOST, PORT))
    except socket.error as msg:
        log.error(f'Bind failed. Error Code : {str(msg[0])} message: {msg[1]}')
        sys.exit()

    CONNECTION_LIST = []
    server_socket.listen(10)
    CONNECTION_LIST.append(server_socket)
    log.info('Socket now listening')
    while True:
            read_sockets, write_sockets, error_sockets = select.select(
                CONNECTION_LIST, [], [])
            for sock in read_sockets:
                # New connection
                if sock == server_socket:
                    # Handle the case in which there is a new connection recieved through server_socket
                    sockfd, addr = server_socket.accept()
                    log.info('Accepting socket connection...')
                    CONNECTION_LIST.append(sockfd)
                # Some incoming message from a client
                else:
                    # Data recieved from client, process it
                    try:
                        # In Windows, sometimes when a TCP program closes abruptly,
                        # a &quot;Connection reset by peer&quot; exception will be thrown
                        data = sock.recv(RECV_BUFFER)
                        if data:
                            log.info(data)
                            wp_ctrl.update_coord()
                    except:
                        sock.close()
                        CONNECTION_LIST.remove(sock)
                        continue

    server_socket.close()


if __name__=="__main__":
    main()

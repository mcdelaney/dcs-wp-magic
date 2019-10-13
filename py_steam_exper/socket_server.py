#!/usr/bin/env python3
"""Example socket server to test stream processing."""
import socket
import logging

logging.basicConfig(level=logging.INFO)
HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)


def main():
    """Send data to client."""
    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, PORT))
        log.info('Socket bound to %s:%s...', HOST, PORT)
        sock.listen()
        log.info('Listening on socket...')
        conn, addr = sock.accept()
        log.info('Connection on socket accepted...')
        with conn:
            log.info('Connected by %s...', addr)
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                conn.sendall(data)

if __name__ == "__main__":
    main()

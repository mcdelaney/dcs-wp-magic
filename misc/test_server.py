import logging
# HOST = 'localhost'
# PORT = 5555
#
#
# def open_connection():
#     con = False
#     while not con:
#         try:
#             sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             sock.connect((HOST, PORT))
#             log.info('Socket connection opened...sending handshake...')
#             sock.sendall(HANDSHAKE)
#             con = True
#         except:
#             log.info('Socket connection failed....will retry')
#             time.sleep(5)
#     return sock

logging.basicConfig(level=logging.INFO)

import socketserver

class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        # self.data = self.request.recv(1024).strip()
        # logging.info("{} wrote:".format(self.client_address[0]))
        # logging.info(self.data)

        with open('tests/data/raw_sink.txt', 'r') as fp_:
            for line in fp_:
                logging.info(line)
                self.request.sendall(line)


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        server.serve_forever()

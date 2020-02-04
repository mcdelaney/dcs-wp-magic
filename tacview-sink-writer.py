"""
Tacview client methods.
Results are parsed into usable format, and then written to a local sqlite
database.
"""
import argparse
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("tacview-reader")
LOG.setLevel(logging.INFO)

# This is what you have to send to tacview server to start the connection
HANDSHAKE = ('\n'.join(["XtraLib.Stream.0",
                       'Tacview.RealTimeTelemetry.0',
                       "tacview_reader",
                       "", ]) + "\0").encode('utf-8')
REF_TIME_FMT = '%Y-%m-%dT%H:%M:%SZ'
COORD_KEYS = ['lon', 'lat', 'alt', 'roll', 'pitch', 'yaw', 'u_coord',
              'v_coord', 'heading']


class SocketReader:
    """Read from Tacview socket."""

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def open_connection(self):
        """
        Initialize the socket connection and write handshake data.
        If connection fails, wait 3 seconds and retry.
        """
        while True:
            LOG.info('Attempting connection at %s:%s...',
                     self.host, self.port)

            # open_connection returns a Reader and a Writer object
            # letting you write and read from the socket.
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port)
            LOG.info('Socket connection opened...sending handshake...')
            self.writer.write(HANDSHAKE)

            # Try to read one line.  If it works, break from the loop
            await self.reader.readline()
            LOG.info("Connection opened successfully!")
            break


async def main(host, port, file_sink):
    """Main method to consume stream."""
    LOG.info("Starting consumer...")
    sink_file = open(file_sink, "wb")
    sock = SocketReader(host, port)
    await sock.open_connection()
    try:
        while True:
            # while True just means: do this forever, basically.
            tacview_line = await sock.reader.readline()
            tacview_line = tacview_line.decode().strip()
            LOG.debug(tacview_line)
            # We'll also write this data to a txt file so we can look at it later.
            if tacview_line[0] == "#":
                tacview_line =  "\n" + tacview_line
            tacview_line = tacview_line + "{[]}"
            sink_file.write(tacview_line.encode("UTF-8"))
        # Close the open tacview file on the way out.
    except Exception as err:
        sink_file.close()
        raise err


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='147.135.8.169',
                        help="Remote IP to connect. Default: Hoggit Gaw")
    parser.add_argument('--port', default=42674,
                        help="Remote port to connect.")
    parser.add_argument('--file_sink', default="./beam-input.txt",
                        help="File path to txt sink.")
    args = parser.parse_args()
    asyncio.run(main(args.host, args.port, args.file_sink))

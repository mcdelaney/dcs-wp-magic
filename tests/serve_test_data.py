"""Socket Perf Test.
"""
import argparse
import asyncio
from asyncio.log import logging
import sys

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger('test_server')
LOG.setLevel(logging.DEBUG)
# N = -1


async def handle_req(reader, writer):
    """Send data."""
    try:
        handshake = await reader.read(4026)
        LOG.info(handshake.decode())
        with open('tests/data/raw_sink.txt', 'r') as fp_:
            for i, line in enumerate(fp_):
                if N != -1 and N <= i:
                    break
                writer.write(line.encode('utf-8'))
                LOG.info(line)

        LOG.info("All lines sent...draining...")
        await writer.drain()
        LOG.info("Socket drained...closing...")
        writer.close()
        LOG.info("Writer closed...exiting...")
    except (ConnectionResetError, BrokenPipeError):
        pass


async def serve_test_data():
    """Read from Tacview socket."""
    LOG.info('Attempting connection at 127.0.0.1:5555...')
    server = await asyncio.start_server(handle_req, "127.0.0.1", "5555")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('-n', type=int, default=-1)
    ARGS = PARSER.parse_args()
    N = ARGS.n
    loop = asyncio.get_event_loop()
    try:
        asyncio.run(serve_test_data())
    except KeyboardInterrupt:
        loop.stop()
        sys.exit(0)

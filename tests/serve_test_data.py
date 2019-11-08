"""Socket Perf Test.
"""
import argparse
import asyncio
from asyncio.log import logging
import sys

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger('test_server')
LOG.setLevel(logging.INFO)


async def handle_req(reader, writer):
    """Send data."""
    try:
        with open('tests/data/raw_sink.txt', 'r') as fp_:
            lines = fp_.readlines()

        handshake = await reader.read(4026)
        LOG.info(handshake.decode())
        LOG.info("Handshake complete...serving data...")
        for line in lines:
            writer.write(line.encode('utf-8'))
            await writer.drain()
            LOG.debug(line)

        LOG.info("All lines sent...closing...")
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
    loop = asyncio.get_event_loop()
    try:
        asyncio.run(serve_test_data())
    except KeyboardInterrupt:
        loop.stop()
        sys.exit(0)

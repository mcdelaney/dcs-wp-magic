"""Socket Perf Test.
"""
import asyncio
from asyncio.log import logging
import sys

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger('test_server')
LOG.setLevel(logging.DEBUG)


async def handle_req(reader, writer):
    """Send data."""
    handshake = await reader.read(4026)
    LOG.info(handshake.decode())
    with open('tests/data/raw_sink.txt', 'r') as fp_:
        lines = fp_.readlines()
    i = 0
    while i < 50:
        writer.write(lines[i].encode('utf-8'))
        LOG.info(lines[i])
        i += 1

    await writer.drain()
    writer.close()


async def serve_test_data(host='127.0.0.1', port=5555):
    """Read from Tacview socket."""
    LOG.info('Attempting connection at %s:%s...', host, port)
    server = await asyncio.start_server(handle_req, host, port)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(serve_test_data())
    except KeyboardInterrupt:
        sys.exit(0)

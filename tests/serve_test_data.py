#!/usr/bin/env python3
"""Socket Perf Test.
"""
import argparse
import asyncio
from asyncio.log import logging
import sys
from pathlib import Path

from google.cloud import storage

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger('test_server')
LOG.setLevel(logging.INFO)


def get_test_file() -> None:
    """Download test tacview file from GCS."""
    local_path = Path("tests/data/tacview-test.txt")
    if local_path.exists():
        LOG.info("Cached file found...not downloading...")
        return
    local_path.parent.mkdir(exist_ok=True)
    LOG.info("Downloading tacview test file...")
    client = storage.Client()
    bucket = client.get_bucket('horrible-server')
    blob = bucket.get_blob("tacview/Tacview-20200125-120912-DCS-Operation Snowfox v123.txt.acmi")
    blob.download_to_filename(local_path)
    LOG.info("Tacview test file downloaded successfully...")


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
    get_test_file()
    loop = asyncio.get_event_loop()
    try:
        asyncio.run(serve_test_data())
    except KeyboardInterrupt:
        loop.stop()
        sys.exit(0)

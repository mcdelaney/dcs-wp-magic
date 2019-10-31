import asyncio
from asyncio.log import logging
from dcs import tacview

logging.basicConfig(level=logging.INFO)


async def main():
    """Start event loop to consume stream."""
    sock = tacview.client.SocketReader('localhost', 9999, debug=True)
    await sock.open_connection()
    while True:
        try:
            obj = await sock.read_stream()
            if obj != "":
                logging.info(obj)
        except Exception as err:
            logging.error(err)
            raise err


if __name__ == '__main__':
    asyncio.run(main())

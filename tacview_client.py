"""
Client methods to consume a stream from Tacview.
Results are parsed into usable format, and then written to a local sqlite
database.
"""
import asyncio

from dcs.tacview import run_server


def main():
    asyncio.run(run_server())


if __name__ == "__main__":
    main()

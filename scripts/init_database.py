#!/usr/bin/env python

from dcs.common.db_postgres import drop_and_recreate_tables

if __name__ == "__main__":
    drop_and_recreate_tables()


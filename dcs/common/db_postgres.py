"""Model definitions for database."""
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy import schema
import asyncpg


PG_URL = 'postgresql://0.0.0.0:5432/dcs?user=prod&password=pwd'
engine = sa.create_engine(PG_URL)
metadata = sa.MetaData()


Session = sa.Table(
    "session",
    metadata,
    sa.Column('session_id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('start_time', sa.TIMESTAMP()),
    sa.Column('datasource', sa.String()),
    sa.Column('author', sa.String()),
    sa.Column('title', sa.String()),
    sa.Column('lat', sa.Numeric()),
    sa.Column('lon', sa.Numeric()),
    sa.Column('time_offset', sa.Numeric())
)

Impact = sa.Table(
    "impact",
    metadata,
    sa.Column('session_id', sa.INTEGER()),
    sa.Column('killer', sa.INTEGER()),
    sa.Column('target', sa.INTEGER()),
    sa.Column('weapon', sa.INTEGER()),
    sa.Column('time_offset', sa.Numeric()),
    # sa.Column('killed', sa.INTEGER()),
    sa.Column('impact_dist', sa.Numeric())
)


Object = sa.Table(
    "object",
    metadata,
    sa.Column('id', sa.INTEGER(), primary_key=True, unique=True),
    sa.Column('session_id', sa.Integer(), sa.ForeignKey('session.session_id')),
    sa.Column('name', sa.String()),
    sa.Column('color', sa.String()),
    sa.Column('country', sa.String()),
    sa.Column('grp', sa.String()),
    sa.Column('pilot', sa.String()),
    sa.Column('type', sa.String()),
    sa.Column('alive', sa.INTEGER()),
    sa.Column('coalition', sa.String()),
    sa.Column('first_seen', sa.Float()),
    sa.Column('last_seen', sa.Float()),

    sa.Column('lat', sa.Float()),
    sa.Column('lon', sa.Float()),
    sa.Column('alt', sa.Float(), ),
    sa.Column('roll', sa.Float()),
    sa.Column('pitch', sa.Float()),
    sa.Column('yaw', sa.Float()),
    sa.Column('u_coord', sa.Float()),
    sa.Column('v_coord', sa.Float()),
    sa.Column('heading', sa.Float()),
    sa.Column('updates', sa.INTEGER()),
    sa.Column('velocity_kts', sa.Float()),

    sa.Column('impacted', sa.INTEGER()),
    sa.Column('impacted_dist', sa.Float()),

    sa.Column('parent', sa.INTEGER()),
    sa.Column('parent_dist', sa.Float()),
    sa.Column('updates', sa.Integer())
)

Event = sa.Table(
    "event",
    metadata,
    sa.Column('id', sa.INTEGER(), sa.ForeignKey('object.id')),
    sa.Column('session_id', sa.INTEGER()),
            #   , sa.ForeignKey('session.session_id')),
    sa.Column('last_seen', sa.Float()),
    sa.Column('alive', sa.INTEGER()),
    sa.Column('lat', sa.Float()),
    sa.Column('lon', sa.Float()),
    sa.Column('alt', sa.Float()),

    sa.Column('roll', sa.Float()),
    sa.Column('pitch', sa.Float()),
    sa.Column('yaw', sa.Float()),
    sa.Column('u_coord', sa.Float()),
    sa.Column('v_coord', sa.Float()),
    sa.Column('heading', sa.Float()),
    # dist_m, sa.Float()
    sa.Column('velocity_kts', sa.Float()),
    # sa.Column('secs_since_last_seen', sa.Float()),
    sa.Column('updates', sa.INTEGER())
)


async def init_db(db_path: Path=None, drop=True):
    """Initialize the database and execute create table statements."""
    DB = await asyncpg.connect(PG_URL)

    if drop:
        for table in [Session, Object, Event, Impact]:
            await DB.execute(f"drop table if exists {table.name} CASCADE")

    for table in [Session, Object, Event, Impact]:
        await DB.execute(str(schema.CreateTable(table)))

    await DB.execute(
        """
        CREATE VIEW obj_events AS
            SELECT * FROM event evt
            INNER JOIN (SELECT id, session_id, name, color, pilot, first_seen,
                        type, grp, coalition, impacted, parent
                            --,time_offset AS last_offset
                        FROM object) obj
            USING (id, session_id)
        """)

    await DB.execute(
        """
        CREATE OR REPLACE VIEW parent_summary AS
            SELECT session_id, pilot, name, type, parent, count(*) total,
                count(impacted) as impacts
            FROM (SELECT parent, name, type, impacted, session_id
                  FROM object
                  WHERE parent is not null AND name IS NOT NULL
                  ) objs
            INNER JOIN (
                SELECT id as parent, pilot, session_id
                FROM object where pilot is not NULL
            ) pilots
            USING (parent, session_id)
            GROUP BY session_id, name, type, parent, pilot
        """)

    await DB.execute(
        "DROP TABLE IF EXISTS event_t_ CASCADE;"
        "CREATE UNLOGGED TABLE IF NOT EXISTS event_temp (LIKE event INCLUDING DEFAULTS);"
        )

"""Test tacview parser."""
import datetime as dt
import pytest
from dcs import tacview


REF = tacview.Ref()
REF.lat = 1.0
REF.lon = 1.0
REF.time = dt.datetime.now()

@pytest.fixture
def db_connection():
    """Fixture to generate a database."""
    from dcs import db
    conn = db.create_connection()
    db.create_db(conn)
    return conn


def test_update_string():
    """Test that update strings are parsed properly."""
    update_string = "1a,T=123.45|678.09|234.2"
    prev_skipped = []
    correct_resp = {'id': '1a',
                    'lat': 679.09,
                    'lastseen': None,
                    'long': 124.45,
                    'alive': True,
                    'alt': 234.2}

    parsed = tacview.parse_line(obj=update_string, ref=REF, last_seen=None,
                                prev_skipped=prev_skipped)
    assert parsed == correct_resp


def test_update_prev_skipped():
    """Test that update strings are parsed properly."""
    update_string = "1a,T=123.45|678.09|234.2"
    prev_skipped = ['1a']
    correct_resp = None

    parsed = tacview.parse_line(obj=update_string, ref=REF, last_seen=None,
                                prev_skipped=prev_skipped)
    assert parsed == correct_resp

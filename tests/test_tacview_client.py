"""Test tacview parser."""
import datetime as dt
import pytest
from dcs import tacview
from dcs.common import db


@pytest.fixture
def conn():
    """Fixture to generate a database."""
    from dcs.common import db
    # conn = db.create_connection()
    conn = db.init_db()
    # db.create_db(conn)
    return conn


@pytest.fixture
def ref_obj():
    ref_obj = tacview.Ref()
    ref_obj.lat = 1.0
    ref_obj.long = 1.0
    ref_obj.time = dt.datetime.now()
    return ref_obj


def test_update_string(ref_obj):
    """Test that update strings are parsed properly."""
    update_string = "1b,T=123.45|678.09|234.2"
    correct_resp = {'id': '1b',
                    'lat': 679.09,
                    'long': 124.45,
                    'alt': 234.2}
    parsed = tacview.parse_line(obj=update_string, ref=ref_obj,
                                       last_seen=None)
    assert parsed == correct_resp


def test_update_partial_loc(ref_obj):
    update_string = "3008d0a,T=||1019.73"
    parsed = tacview.parse_line(obj=update_string, ref=ref_obj,
                                last_seen=None)
    correct_resp = {'id': '3008d0a',
                    'lat': '',
                    'long': '',
                    'alt': 1019.73}
    assert parsed == correct_resp


def test_new_entry(ref_obj):
    new_string = "802,T=6.3596289|5.139203|342.67|||7.3|729234.25|-58312.28|,"\
    "Type=Ground+Static+Aerodrome,Name=FARP,Color=Blue,"\
    "Coalition=Enemies,Country=us"
    parsed = tacview.parse_line(obj=new_string, ref=ref_obj,
                                       last_seen=0)
    assert True


def test_new_entry_insert(ref_obj, conn):
    new_string = "4001,T=4.6361975|6.5404775|1487.59|||357.8|-347259.72|380887.44|,"\
    "Type=Ground+Heavy+Armor+Vehicle+Tank,Name=BTR-80,"\
    "Group=New Vehicle Group #041,Color=Red,Coalition=Enemies,Country=ru"
    parsed = tacview.parse_line(obj=new_string, ref=ref_obj,
                                       last_seen=0)
    db.insert_new_rec(conn, parsed)
    result = conn.execute(f"SELECT * FROM enemies where id = {parsed['id']}")
    db_result = dict(result.fetchone())
    for key, val in db_result.items():
        assert val == parsed[key]

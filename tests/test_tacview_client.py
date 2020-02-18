"""Test tacview parser."""
import datetime as dt
import pytest
from dcs import tacview
import time
from dcs.common.db import Object, Event


@pytest.fixture
def ref_obj():
    """Fixture to generate a database and ref."""
    from dcs.common import db as dbtools
    conn = dbtools.init_db()
    time.sleep(0.01)
    ref = tacview.Ref()
    ref.parse_ref_obj("ReferenceLatitude=1.0")
    ref.parse_ref_obj("ReferenceLongitude=1.0")
    ref.parse_ref_obj("DataSource=Mission")
    ref.parse_ref_obj("Title=GoodMission")
    ref.parse_ref_obj("Author=Bob")
    ref.parse_ref_obj(f"ReferenceTime=2019-01-01T12:12:01Z")
    ref.update_time("#1.01")
    return ref


def test_update_string(ref_obj):
    """Test that update strings are parsed properly."""
    new_string = "802,T=6.3596289|5.139203|342.67|||7.3|729234.25|-58312.28|,"\
    "Type=Ground+Static+Aerodrome,Name=FARP,Color=Blue,"\
    "Coalition=Enemies,Country=us"
    parsed_orig = tacview.line_to_obj(raw_line=new_string, ref=ref_obj)
    parsed_orig.reset_update_fields()
    update_string = "802,T=123.45|678.09|234.2"
    correct_resp = {'id': int('802', 16),
                    'lat': 679.09,
                    'lon': 124.45,
                    'alt': 234.2}
    parsed = tacview.line_to_obj(raw_line=update_string, ref=ref_obj)
    parsed = parsed.to_dict()
    for key, value in correct_resp.items():
        assert value == parsed[key]


def test_new_entry_insert(ref_obj):
    """Test that new records are inserted correctly"""
    new_string = "4001,T=4.6361975|6.5404775|1487.59|||357.8|-347259.72|380887.44|,"\
    "Type=Ground+Heavy+Armor+Vehicle+Tank,Name=BTR-80,"\
    "Group=New Vehicle Group #041,Color=Red,Coalition=Enemies,Country=ru"
    update_queue = tacview.Queue()
    parsed = tacview.line_to_obj(raw_line=new_string, ref=ref_obj)

    update_queue.put_nowait(parsed)
    tacview.update_records(update_queue)
    parsed = parsed.to_dict()
    db_result = Object.select().where(Object.id == parsed['id']).dicts().get()
    for key, val in db_result.items():
        try:
            parsed_val = parsed['key']
        except KeyError as err:
            if val is None:
                continue
        assert val == parsed[key]

    event = Event.select().where(Event.id == parsed['id']).dicts().get()
    for key, val in event.items():
        try:
            parsed_val = parsed['key']
        except KeyError as err:
            if val is None:
                continue
        assert val == parsed[key]


def test_new_entry_without_alt(ref_obj):
    """Test that a new record with no altitude is assigned 1.0."""
    new_string = "4001,T=4.6361975|6.5404775|||357.8|-347259.72|380887.44|,"\
    "Type=Ground+Heavy+Armor+Vehicle+Tank,Name=BTR-80,"\
    "Group=New Vehicle Group #041,Color=Red,Coalition=Enemies,Country=ru"
    parsed = tacview.line_to_obj(raw_line=new_string, ref=ref_obj)
    assert parsed.alt == 1.0

"""Shared config settings for the app."""

DB_LOC = "data/dcs.db"

# Tacview server settings
CLIENT = 'someone_somewhere'
PASSWORD = '0'
# HOST = '127.0.0.1'
presets = {
    'PGAW': '147.135.9.159:42674',  # PGAW,
    'GAW': '147.135.8.169:42674',  # Hoggit Gaw
    'LOCALHOST': '127.0.0.1:42674',  # Hoggit Gaw
    'A-Horrible-Server': '68.194.86.85:42674'
}

HOST = '147.135.8.169'  # Hoggit Gaw
PORT = 42674
START_UNITS = [CLIENT, "CVN-74", "Stennis"]

EXCLUDED_TYPES = [
    'Air+FixedWing', '', 'Ground+Light+Human+Air+Parachutist',
    "Air+Rotorcraft", "Ground+Static+Aerodrome", 'Navaid+Static+Bullseye',
    "Misc+Shrapnel", 'Misc+Decoy+Chaff', 'Misc+Decoy+Flare', 'weapon+Missile',
    'Weapon+Missile', 'Weapon+Bomb', 'Projectile+Shell', 'Misc+Container'
]

COALITION = "Enemies"

MAX_DIST = 1000

CATS = {
    'MOBILE_CP': ["S-300PS 54K6 cp", "SKP-11", "Hawk pcp"],
    'RADAR': [
        "S-300PS 40B6M tr",
        "S-300PS 40B6MD sr",
        "S-300PS 64H6E sr",
        "Kub 1S91 str",
        "snr s-125 tr",
        "1L13 EWR",
        "Dog Ear radar",
        "SA-11 Buk SR 9S18M1",
        "SA-18 Igla-S comm",
        "SNR_75V",
        "Silkworm_SR",
        "Hawk tr",
        "Hawk cwar",
        "55G6 EWR",
        "Hawk sr",
    ],
    'SAM': [
        "S-300PS 5P85C ln", "S-300PS 5P85D ln", "Kub 2P25 ln",
        "SA-11 Buk LN 9A310M1", 'Tor 9A331', "Hawk ln", "5p73 s-125 ln",
        "Osa 9A33 ln", "Strela-10M3", "Strela-1 9P31", 'S_75M_Volhov',
        'hy_launcher'
    ],
    "AAA": [
        "ZSU-23-4 Shilka", "2S6 Tunguska", "Ural-375 ZU-23",
        "ZU-23 Emplacement Closed", "SA-18 Igla-S manpad",
        "ZU-23 Closed Insurgent", "Igla manpad INS"
    ],
    'ARMOR': [
        "Ural-375 PBU", "BMP-2", "T-72B", "SAU Msta", "BMP-1", "BMD-1",
        "BTR-80", "Ural-375", "SAU Gvozdika", "T-55", "Uragan_BM-27",
        "Ural-4320T", "ATZ-10", "Grad-URAL", "KrAZ6322"
    ],
    "INFANTRY": [
        "Infantry AK", "Land Rover", "Zil-4331", "Land_Rover_101_FC",
        "Land_Rover_109_S3"
    ],
}

CAT_ORDER = {
    'MOBILE_CP': 1,
    'RADAR': 2,
    "SAM": 3,
    'Unknown': 4,
    'AAA': 5,
    'ARMOR': 6,
    'INFANTRY': 7
}

CAT_LOOKUP = {}
for key, val in CATS.items():
    for i in val:
        CAT_LOOKUP[i] = key

PROJECT_ID = 'dcs-analytics-257714'

STREAM_PROTOCOL = "XtraLib.Stream.0"
TACVIEW_PROTOCOL = 'Tacview.RealTimeTelemetry.0'
HANDSHAKE_TERMINATOR = "\0"

HANDSHAKE = ('\n'.join([STREAM_PROTOCOL, TACVIEW_PROTOCOL, CLIENT, PASSWORD]) +
             HANDSHAKE_TERMINATOR).encode('utf-8')

COORD_KEYS = [
    'lon', 'lat', 'alt', 'roll', 'pitch', 'yaw', 'u_coord', 'v_coord',
    'heading'
]

REF_TIME_FMT = '%Y-%m-%dT%H:%M:%SZ'
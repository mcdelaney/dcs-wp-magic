
START_UNITS = ["someone_somewhere", "CVN-74", "Stennis"]
EXCLUDED_EXPORT = [
                  'Ground+Light+Human+Air+Parachutist',
                  'Air+FixedWing',
                  "Air+Rotorcraft",
                  "Misc+Shrapnel",
                  'Weapon+Missile',
                  'weapon+Missile',
                  'Projectile+Shell',
                  'Misc+Container'
]

EXCLUDED_TYPES = ['Air+FixedWing',
                   '',
                  "Air+Rotorcraft",
                  "Ground+Static+Aerodrome",
                  "Misc+Shrapnel",
                  'weapon+Missile',
                  'Weapon+Missile',
                  'Projectile+Shell',
                  'Misc+Container']

EXCLUDED_PILOTS = ["FARP"]
COALITION = "Enemies"

MAX_DIST = 1000

CATS = {
    'MOBILE_CP': ["S-300PS 54K6 cp", "SKP-11"],
    'RADAR': [
        "S-300PS 40B6M tr", "S-300PS 40B6MD sr", "S-300PS 64H6E sr",
        "Kub 1S91 str", "snr s-125 tr", "1L13 EWR", "Dog Ear radar",
        "SA-11 Buk SR 9S18M1", "SA-18 Igla-S comm", "SNR_75V"
    ],
    'SAM': [
        "S-300PS 5P85C ln", "S-300PS 5P85D ln", "Kub 2P25 ln",
        "SA-11 Buk LN 9A310M1", 'Tor 9A331',
        "5p73 s-125 ln", "Osa 9A33 ln", "Strela-10M3", "Strela-1 9P31",
        'S_75M_Volhov'
    ],
    "AAA": [
        "ZSU-23-4 Shilka", "2S6 Tunguska", "Ural-375 ZU-23",
        "ZU-23 Emplacement Closed", "SA-18 Igla-S manpad",
        "ZU-23 Closed Insurgent"],
    'ARMOR': ["Ural-375 PBU", "BMP-2", "T-72B", "SAU Msta", "BMP-1", "BMD-1",
              "BTR-80", "Ural-375 ZU-23 Insurgent"],
    "INFANTRY": ["Infantry AK", "Land Rover", "Zil-4331", "Land_Rover_101_FC"],
}

CAT_ORDER = {'MOBILE_CP': 1,
             'RADAR': 2,
             "SAM": 3,
             'Unknown': 4,
             'AAA': 5,
             'ARMOR': 6,
             'INFANTRY': 7}

CAT_LOOKUP = {}
for k, v in CATS.items():
    for i in v:
        CAT_LOOKUP[i] = k

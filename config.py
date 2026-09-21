# Patch bay layout. Bays are listed top of rack -> bottom.
#
# Each entry spans `width` ports. `top` / `bottom` are the jack labels,
# `normalled` marks a normalled top -> bottom pair.
# Optional keys (ignored by the label generator, used by generate_html.py):
#   category - Category enum (enums.py): colour grouping in the HTML view
#   note     - open question / reminder shown in the HTML view
#   pending  - on a spare ("-") entry: what the ports are reserved for. Shown in the HTML view only;
#              printed labels stay blank.
#   rack      - (on a bay) starts a new physical rack; following bays stay in it
#   jack_type - (on a bay) JackType enum (enums.py): MIDI (5-pin DIN), SWITCH (rocker) or ETHERNET (RJ45)
#               drawing in the HTML view

from enums import Category, JackType

ROOMS = [
    "Kitchen", "Bath Up", "Bath Dn", "Den", "Gallery",
    "Master Bed", "Guest Bed", "Office", "Front Deck", "Back Deck",
]

# Each room: stereo send, L over R in one column. Room mic returns stay off this
# TRS bay (phantom power) - they'll get their own XLR patch bay later.
room_sends = [
    {"normalled": False, "top": f"{room} L", "bottom": f"{room} R", "width": 1, "category": Category.ROOMS}
    for room in ROOMS
]

config = [
  {
    "label_name": "1",
    "rack": "Main rack",
    "entries": [
        {"normalled": False, "top": "Tanzbar Out L", "bottom": "Tanzbar Out R", "width": 1, "category": Category.INSTRUMENTS},
        {"normalled": False, "top": "Sub 37 Out", "bottom": "-", "width": 1, "category": Category.INSTRUMENTS},
        {"normalled": False, "top": "Fuzz In", "bottom": "Fuzz Out", "width": 1, "category": Category.INSTRUMENTS},
        {"normalled": False, "top": "MXR Dist In", "bottom": "MXR Dist Out", "width": 1, "category": Category.INSTRUMENTS},
        {"normalled": False, "top": "-", "bottom": "-", "width": 5, "category": Category.INSTRUMENTS, "pending": "Instruments & pedals"},
        {"normalled": False, "top": "LA-2A In", "bottom": "LA-2A Out", "width": 1, "category": Category.OUTBOARD},
        {"normalled": False, "top": "UA 550 In", "bottom": "UA 550 Out", "width": 1, "category": Category.OUTBOARD},
        {"normalled": False, "top": "DBX 160 Link", "bottom": "DBX 160 Link", "width": 1, "category": Category.OUTBOARD},
        {"normalled": False, "top": "SSL Fusion In L/R", "bottom": "SSL Fusion Out L/R", "width": 2, "category": Category.OUTBOARD},
        {"normalled": False, "top": "API L/R In", "bottom": "API L/R Out", "width": 2, "category": Category.OUTBOARD},
        {"normalled": False, "top": "Dbx 160A L/R In", "bottom": "Dbx 160A L/R Out", "width": 2, "category": Category.OUTBOARD},
        {"normalled": False, "top": "D-Comp L/R In", "bottom": "D-Comp L/R Out", "width": 2, "category": Category.OUTBOARD},
        {"normalled": False, "top": "902 De-esser IN 1-2", "bottom": "902 De-esser OUT 1-2", "width": 2, "category": Category.OUTBOARD},
        {"normalled": False, "top": "Art Comp In L/R", "bottom": "Art Comp Out L/R", "width": 2, "category": Category.OUTBOARD},
    ]
  },
  {
    "label_name": "2",
    "entries": [
        {"normalled": True, "top": "Ghost Channel Insert Send 1-16", "bottom": "Ghost Channel Insert Return 1-16", "width": 16, "category": Category.CONSOLE},
        {"normalled": False, "top": "Group 1 - 8 Insert Send", "bottom": "Group 1 - 8 Insert Return", "width": 8, "category": Category.GROUPS},
    ]
  },
  {
    "label_name": "3",
    "entries": [
        {"normalled": True, "top": "Ghost Channel Insert Send 17-32", "bottom": "Ghost Channel Insert Return 17-32", "width": 16, "category": Category.CONSOLE},
        {"normalled": True, "top": "Aux 1 Out", "bottom": "EMT 140 In", "width": 1, "category": Category.FX},
        {"normalled": True, "top": "Aux 2 Out", "bottom": "PCM60 In", "width": 1, "category": Category.FX},
        {"normalled": True, "top": "Aux 3 Out", "bottom": "SDE 1000 In", "width": 1, "category": Category.FX},
        {"normalled": True, "top": "Aux 4 Out", "bottom": "Moog DLY In", "width": 1, "category": Category.FX},
        {"normalled": True, "top": "Aux 5 / 6 Out", "bottom": "-", "width": 2, "category": Category.FX},
        {"normalled": True, "top": "Aux 7 Out L/R", "bottom": "-", "width": 2, "category": Category.FX},
    ]
  },
  {
    "label_name": "4",
    "entries": [
        {"normalled": True, "top": "Worm hole Matched to Left Side Patch bay 1-16 top", "bottom": "Console Line In 1-16", "width": 16, "category": Category.CONSOLE},
        {"normalled": False, "top": "Aux 8 Out L/R", "bottom": "-", "width": 2, "category": Category.FX},
        {"normalled": False, "top": "Moog DLY Out", "bottom": "-", "width": 1, "category": Category.FX},
        {"normalled": False, "top": "-", "bottom": "-", "width": 3},
        {"normalled": True, "top": "Main Insert Send", "bottom": "Main Insert Return", "width": 2, "category": Category.GROUPS},
    ]
  },
  {
    "label_name": "5",
    "entries": [
        {"normalled": True, "top": "Worm hole Matched to Left Side Patch bay 1-16 bottom", "bottom": "Console Line In 17-32", "width": 16, "category": Category.CONSOLE},
        {"normalled": False, "top": "-", "bottom": "-", "width": 8},
    ]
  },
  {
    "label_name": "6",
    "entries": [
        {"normalled": True, "top": "Apollo #1 1-16 Out", "bottom": "Ghost 1-16 Tape In", "width": 16, "category": Category.CONSOLE},
        {"normalled": False, "top": "-", "bottom": "-", "width": 6},
        {"normalled": False, "top": "-", "bottom": "-", "width": 2},
    ]
  },
  {
    "label_name": "7",
    "entries": [
        {"normalled": True, "top": "Apollo #2 17-32 Out", "bottom": "Ghost 17-32 Tape In", "width": 16, "category": Category.CONSOLE},
        {"normalled": True, "top": "EMT 140 Return L/R", "bottom": "FX 1 In L/R", "width": 2, "category": Category.FX},
        {"normalled": True, "top": "PCM60 Return L/R", "bottom": "FX 2 In L/R", "width": 2, "category": Category.FX},
        {"normalled": True, "top": "SDE 1000 Return", "bottom": "FX 3 In L/R", "width": 2, "category": Category.FX},
        {"normalled": False, "top": "-", "bottom": "FX 4 In L/R", "width": 2, "category": Category.FX},
    ]
  },
  {
    "label_name": "8",
    "entries": [
        {"normalled": True, "top": "Ghost 1-16 Tape Send", "bottom": "Apollo #1 1-16 In", "width": 16, "category": Category.CONSOLE},
        {"normalled": True, "top": "Control Room Out L/R", "bottom": "Yamaha Monitors In", "width": 2, "category": Category.MONITORING},
        {"normalled": True, "top": "Alt CRM Out L", "bottom": "Mix Cube In", "width": 1, "category": Category.MONITORING},
        {"normalled": True, "top": "Alt CRM Out R", "bottom": "-", "width": 1, "category": Category.MONITORING},
        {"normalled": True, "top": "Studio A O/P L/R", "bottom": "Headamp Pro Input", "width": 2, "category": Category.MONITORING},
        {"normalled": True, "top": "Studio Phones B L/R Out", "bottom": "Meyer Mains In L/R", "width": 2, "category": Category.MONITORING},
    ]
  },
  {
    "label_name": "9",
    "entries": [
        {"normalled": True, "top": "Ghost 17-32 Tape Send", "bottom": "Apollo #2 17-32 In", "width": 16, "category": Category.CONSOLE},
        {"normalled": True, "top": "Apollo 2 Track Out", "bottom": "Ghost 2 Track A Input", "width": 2, "category": Category.TWO_TRACK},
        {"normalled": True, "top": "Record Player Out", "bottom": "Ghost 2 Track B Input", "width": 2, "category": Category.TWO_TRACK},
        {"normalled": True, "top": "Ghost Mix Out L/R", "bottom": "-", "width": 2, "category": Category.TWO_TRACK},
        {"normalled": False, "top": "-", "bottom": "Phones Amp In L/R", "width": 2, "category": Category.MONITORING},
    ]
  },
  {
    "label_name": "10",
    "entries": room_sends + [
        {"normalled": False, "top": "Basement Snake A, B, C, D", "bottom": "Basement Snake E, F, G, H", "width": 4, "category": Category.TIE_LINES},
        {"normalled": False, "top": "-", "bottom": "-", "width": 2},
        {"normalled": False, "top": "Group 1 - 8 Out", "bottom": "Hearback In 1 - 8", "width": 8, "category": Category.GROUPS},
    ]
  },
  {
    "label_name": "11-amp-rack",
    "rack": "Amp rack",
    "entries": [
        {"normalled": True, "top": "L / R Audio Source Out", "bottom": "DBX Drive Rack L/R IN", "width": 2, "category": Category.AMP},
        {"normalled": True, "top": "DBX High Out L/R",       "bottom": "High Amp In L/R",       "width": 2, "category": Category.AMP},
        {"normalled": True, "top": "DBX Mid Out L/R",        "bottom": "Mid Amp In L/R",        "width": 2, "category": Category.AMP},
        {"normalled": True, "top": "DBX Low Out L/R",        "bottom": "Low Amp In L/R",        "width": 2, "category": Category.AMP},
        {"normalled": True, "top": "-",                      "bottom": "-",                     "width": 16},
    ]
  },
  {
    "label_name": "ethernet",
    "rack": "Ethernet",
    "jack_type": JackType.ETHERNET,
    "single_row": True,
    "port_count": 20,
    "entries": [
        {"normalled": False, "top": "Hearback Out 1-8", "width": 8, "category": Category.NETWORK},
    ] + [
        {"normalled": False, "top": room, "width": 1, "category": Category.NETWORK} for room in ROOMS
    ] + [
        {"normalled": False, "top": "-", "width": 2},
    ]
  },
  {
    "label_name": "midi",
    "rack": "MIDI",
    "jack_type": JackType.MIDI,
    "single_row": True,
    "port_count": 22,
    "entries": [
        {"normalled": False, "top": f"MIDI {n}", "width": 1, "category": Category.MIDI,
         **({"note": "Channel labels needed for all 22 MIDI jacks"} if n == 1 else {})}
        for n in range(1, 23)
    ]
  },
  {
    "label_name": "power-switches",
    "rack": "Power switches",
    "jack_type": JackType.SWITCH,
    "single_row": True,
    "port_count": 10,
    "entries": [
        {"normalled": False, "top": f"Switch {n}", "width": 1, "category": Category.POWER,
         **({"note": "Label what each of the 10 power switches turns on"} if n == 1 else {})}
        for n in range(1, 11)
    ]
  },
]


# Physical equipment racks (front elevation, top rack unit first).
# Only used by generate_html.py.
#   u / size - starting rack unit and height in U
#   patch    - text to search for in patch bay labels, to show where the unit is patched
#   slots    - individual labels on a multi-channel unit (None = not labelled yet)
#   movable  - could be moved to another rack
#   plan     - planned change
gear_racks = [
  {
    "name": "Rack 1",
    "units": [
        {"u": 1,  "size": 1, "name": "Power conditioner",      "category": Category.POWER},
        {"u": 2,  "size": 1, "name": "Switch panel",           "category": Category.POWER, "patch": "Switch"},
        {"u": 3,  "size": 1, "name": "Apollo 16 #1",           "category": Category.CONSOLE, "patch": "Apollo #1",
         "plan": "Replacing both Apollos with one 1U unit"},
        {"u": 4,  "size": 1, "name": "Apollo 16 #2",           "category": Category.CONSOLE, "patch": "Apollo #2",
         "plan": "Replacing both Apollos with one 1U unit"},
        {"u": 5,  "size": 1, "name": "API 2500 compressor",    "category": Category.OUTBOARD, "patch": "API"},
        {"u": 6,  "size": 2, "name": "D-Comp",                 "category": Category.OUTBOARD, "patch": "D-Comp"},
        {"u": 8,  "size": 1, "name": "dbx 902 de-esser ×2",    "category": Category.OUTBOARD, "patch": "902"},
        {"u": 9,  "size": 1, "name": "Lexicon PCM 60 reverb",  "category": Category.FX,       "patch": "PCM"},
        {"u": 10, "size": 1, "name": "SDE 1000 delay",         "category": Category.FX,       "patch": "SDE 1000"},
        {"u": 11, "size": 2, "name": "dbx 160 compressors",    "category": Category.OUTBOARD, "patch": "160"},
        {"u": 13, "size": 1, "name": "EMT reverb remote",      "category": Category.FX,       "movable": True},
        {"u": 14, "size": 1, "name": "Headphone amp",          "category": Category.MONITORING, "patch": "Phones Amp", "movable": True},
        {"u": 15, "size": 1, "name": "MIDI patch bay",         "category": Category.MIDI, "patch": "MIDI"},
        {"u": 16, "size": 2, "name": "Computer shelf",         "category": Category.COMPUTER},
        {"u": 18, "size": 1, "name": "",                       "note": "U18 not listed - empty?"},
        {"u": 19, "size": 2, "name": "Soundcraft Ghost power supply", "category": Category.POWER, "movable": True},
    ]
  },
]


# Where each physical patch bay unit is mounted right now: position -> the unit's bay number in
# previous_config.py (its layout before the reorg). Positions not listed are empty; units not
# listed are out of the rack. Update this as units are moved; the move plan starts from here.
installed_units = {
    "2": "4",
    "3": "6",
    "4": "1",
    "5": "7",
    "6": "8",
    "7": "3",
    "8": "2",
    "9": "5",
    "10": "10",
    "11-amp-rack": "11-amp-rack",
}

# True: never move a unit that is already mounted; the plan only fills empty positions and
# lists card flips. False: the plan may move mounted units if that saves card flips.
keep_installed_units = True

# Cards flipped since the original layout: unit (previous_config bay) -> {port: normalled now}.
# The move plan uses these instead of the original settings for those ports.
card_changes = {
    "6": {19: True, 20: True, 21: True, 22: True, 23: True, 24: True},
}

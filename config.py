# Patch bay layout. Bays are listed top of rack -> bottom.
#
# Each entry spans `width` ports. `top` / `bottom` are the jack labels,
# `normalled` marks a normalled top -> bottom pair.
# Optional keys (ignored by the label generator, used by generate_html.py):
#   category - Category enum (enums.py): colour grouping in the HTML view
#   note     - open question / reminder shown in the HTML view
#   info     - a plain fact about this port, shown as a marker and in the hover text
#   info_at  - which row carries the info marker: "top" (default) or "bottom"
#   in_use   - False: labelled but not connected yet (dimmed, no rear checkbox in the HTML view)
#   pending  - on a spare ("-") entry: what the ports are reserved for. Shown in the HTML view only;
#              printed labels stay blank.
#   rack      - (on a bay) starts a new physical rack; following bays stay in it
#   in_use   - (on a bay) False: not in use yet; no printed label, marked "Not in use" in the HTML view
#   track_rear - (on a bay) rear-panel "plugged in" checkboxes in the HTML view (on by default for bays 1-10;
#               ethernet, MIDI, power switches and the amp rack opt in)
#   jack_type - (on a bay) JackType enum (enums.py): MIDI (5-pin DIN), SWITCH (rocker) or ETHERNET (RJ45)
#               drawing in the HTML view

from enums import Category, JackType, MidiPort, Need, CableKind

# Every place with a cable run to it. The decks get a speaker cable from an amp, so they have
# no patch bay send and no network drop; everything else gets a stereo send, a mono return and Cat5.
ROOMS = [
    "Kitchen", "Bath Up", "Bath Dn", "Den", "Gallery",
    "Master Bed", "Guest Bed", "Office", "Record Player", "Front Deck", "Back Deck",
]
SPEAKER_ONLY = ["Front Deck", "Back Deck"]
# Questions with nowhere better to live, shown in the HTML view's open questions.
open_questions = []
SEND_ROOMS = [r for r in ROOMS if r not in SPEAKER_ONLY]

# Cable runs that aren't a standard room: (name, CableKind, where it lands, does it get patched).
special_runs = [
    {"name": "Reverb · EMT plate", "runs": [
        ("Send", CableKind.XLR, "EMT 140 In", True),
        ("Return L", CableKind.XLR, "EMT 140 Return L/R", True),
        ("Return R", CableKind.XLR, "EMT 140 Return L/R", True),
        ("Motor control · 5-pin", CableKind.CAT5, "EMT remote, Rack 1 U13 - Cat5e cable for the 5-pin motor run", False),
    ]},
]

# Each room: stereo send, L over R in one column. Room mic returns stay off this
# TRS bay (phantom power) - they'll get their own XLR patch bay later.
room_sends = [
    {"normalled": False, "top": f"{room} L", "bottom": f"{room} R", "width": 1, "category": Category.ROOMS}
    for room in SEND_ROOMS
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
        {"normalled": True, "top": "Worm hole Matched to Left Side Patch bay 1-16 top", "bottom": "Console Line In 1-16", "width": 16, "category": Category.CONSOLE,
         "info": "Top row is the worm hole to the left-side bay - not wired yet. The Console Line In jacks below are in use.", "info_at": "top"},
        {"normalled": False, "top": "Aux 8 Out L/R", "bottom": "-", "width": 2, "category": Category.FX},
        {"normalled": False, "top": "SDE 1000 Return",      "bottom": "-",                   "width": 1, "category": Category.FX},
        {"normalled": False, "top": "Moog DLY Out", "bottom": "-", "width": 1, "category": Category.FX},
        {"normalled": False, "top": "-",                     "bottom": "-",                   "width": 2},
        {"normalled": True, "top": "Main Insert Send", "bottom": "Main Insert Return", "width": 2, "category": Category.GROUPS},
    ]
  },
  {
    "label_name": "5",
    "entries": [
        {"normalled": True, "top": "Worm hole Matched to Left Side Patch bay 1-16 bottom", "bottom": "Console Line In 17-32", "width": 16, "category": Category.CONSOLE,
         "info": "Top row is the worm hole to the left-side bay - not wired yet. The Console Line In jacks below are in use.", "info_at": "top"},
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
        {"normalled": False, "top": "-", "bottom": "FX 3 In L/R", "width": 2, "category": Category.FX},
        {"normalled": False, "top": "-", "bottom": "FX 4 In L/R", "width": 2, "category": Category.FX},
    ]
  },
  {
    "label_name": "8",
    "entries": [
        {"normalled": True, "top": "Ghost 1-16 Tape Send", "bottom": "Apollo #1 1-16 In", "width": 16, "category": Category.CONSOLE},
        {"normalled": True, "top": "Control Room Out L/R", "bottom": "Yamaha Monitors In", "width": 2, "category": Category.MONITORING},
        {"normalled": True, "top": "Alt CRM Out L", "bottom": "Mix Cube In", "width": 1, "category": Category.MONITORING,
         "info": "Avantone Active MixCube: the lamp in its rear power switch is dead. The speaker and its supply "
                 "are fine - the switch just doesn't light up, so don't go chasing a dead unit.",
         "info_at": "bottom"},
        {"normalled": True, "top": "Alt CRM Out R", "bottom": "-", "width": 1, "category": Category.MONITORING},
        {"normalled": True, "top": "Studio A O/P L/R", "bottom": "Headamp Pro Input", "width": 2, "category": Category.MONITORING},
        {"normalled": True, "top": "Studio Phones B L/R Out", "bottom": "Meyer Mains In L/R", "width": 2, "category": Category.MONITORING},
    ]
  },
  {
    "label_name": "9",
    "entries": [
        {"normalled": True, "top": "Ghost 17-32 Tape Send", "bottom": "Apollo #2 17-32 In", "width": 16, "category": Category.CONSOLE},
        {"normalled": True, "top": "Apollo 2 Track Out", "bottom": "Ghost 2 Track A Input", "width": 2, "category": Category.TWO_TRACK,
         "info": "Bay to the Ghost 2 Track A input is 2x unshielded TRS cables, about 6 ft, inside the rack.",
         "info_at": "bottom"},
        {"normalled": True, "top": "Record Player Out", "bottom": "Ghost 2 Track B Input", "width": 2, "category": Category.TWO_TRACK},
        {"normalled": False, "top": "Ghost MIX O/P L/R", "bottom": "-", "width": 2, "category": Category.TWO_TRACK},
        {"normalled": False, "top": "Ghost MIX B O/P L/R", "bottom": "-", "width": 2, "category": Category.TWO_TRACK},
    ]
  },
  {
    "label_name": "10",
    "entries": room_sends + [
        {"normalled": False, "top": "Front Porch", "bottom": "Back Porch", "width": 1, "category": Category.ROOMS,
         "info": "Mono line sends, one per porch, feeding the amp that drives the porch speakers.",
         "info_at": "top"},
        {"normalled": False, "top": "Basement Snake A, B, C, D", "bottom": "Basement Snake E, F, G, H", "width": 4, "category": Category.TIE_LINES},
        {"normalled": False, "top": "-", "bottom": "-", "width": 2},
        {"normalled": False, "top": "Group 1 - 8 Out", "bottom": "Hearback In 1 - 8", "width": 8, "category": Category.GROUPS},
    ]
  },
  {
    "label_name": "11-amp-rack",
    "rack": "Amp rack",
    "track_rear": True,
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
    "track_rear": True,
    "single_row": True,
    "port_count": 20,
    "entries": [
        {"normalled": False, "top": "Hearback Out 1-8", "width": 8, "category": Category.NETWORK},
    ] + [
        {"normalled": False, "top": room, "width": 1, "category": Category.NETWORK, "in_use": False} for room in SEND_ROOMS
    ] + [
        {"normalled": False, "top": "-", "width": 3},
    ]
  },
  {
    "label_name": "midi",
    "in_use": False,
    "rack": "MIDI",
    "jack_type": JackType.MIDI,
    "track_rear": True,
    "single_row": True,
    "port_count": 22,
    "entries": [
        {"normalled": False, "top": "-", "width": 22, "category": Category.MIDI,
         "pending": "MIDI patch bay - label it once the instruments are installed"},
    ]
  },
  {
    "label_name": "power-switches",
    "rack": "Power switches",
    "jack_type": JackType.SWITCH,
    "track_rear": True,
    "single_row": True,
    "port_count": 10,
    "entries": [
        {"normalled": False, "top": "Monitors",   "width": 1, "category": Category.POWER},
        {"normalled": False, "top": "-",          "width": 1},
        {"normalled": False, "top": "API 2500",   "width": 1, "category": Category.POWER},
        {"normalled": False, "top": "D-Comp",     "width": 1, "category": Category.POWER},
        {"normalled": False, "top": "dbx 902",    "width": 1, "category": Category.POWER},
        {"normalled": False, "top": "PCM 60",     "width": 1, "category": Category.POWER},
        {"normalled": False, "top": "SDE 1000",   "width": 1, "category": Category.POWER},
        {"normalled": False, "top": "dbx 160 #1", "width": 1, "category": Category.POWER},
        {"normalled": False, "top": "dbx 160 #2", "width": 1, "category": Category.POWER},
        {"normalled": False, "top": "Headamp",    "width": 1, "category": Category.POWER},
    ]
  },
]


# Physical equipment racks (front elevation, top rack unit first).
# Only used by generate_html.py.
#   u / size - starting rack unit and height in U
#   patch    - text to search for in patch bay labels, to show where the unit is patched
#   bay      - label_name of a patch bay this unit IS (links to that whole bay)
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
        {"u": 14, "size": 1, "name": "Headphone amp",          "category": Category.MONITORING, "patch": "Headamp Pro Input", "movable": True},
        {"u": 15, "size": 1, "name": "Headphone power supply", "category": Category.POWER},
        {"u": 16, "size": 1, "name": "MIDI patch bay",         "category": Category.MIDI, "bay": "midi"},
        {"u": 17, "size": 1, "name": "Hearback unit",          "category": Category.MONITORING, "patch": "Hearback"},
        {"u": 18, "size": 1, "name": "Ethernet patch bay",     "category": Category.NETWORK, "bay": "ethernet"},
        {"u": 19, "size": 2, "name": "Soundcraft Ghost power supply", "category": Category.POWER},
    ]
  },
]


# Where each physical patch bay unit is mounted right now: position -> the unit's bay number in
# previous_config.py (its layout before the reorg). Positions not listed are empty; units not
# listed are out of the rack. Update this as units are moved; the move plan starts from here.
installed_units = {
    "1": "9",
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
    "5": {23: False, 24: False},
    "6": {19: True, 20: True, 21: True, 22: True, 23: True, 24: True},
    "9": {1: False, 2: False, 10: False, 11: False, 12: False, 13: False, 14: False, 15: False, 16: False, 18: False},
    "10": {11: False, 12: False, 13: False, 14: False},
}


# Instruments that need MIDI, tracked in the HTML view (checkbox per port).
#   ports   - (MidiPort, Need) pairs
#   jacks   - optional {MidiPort: MIDI patch bay jack number} once assigned
#   note    - reminder shown in the list
midi_instruments = [
    {"name": "Moog Sub 37", "ports": [(MidiPort.IN, Need.REQUIRED), (MidiPort.OUT, Need.REQUIRED)]},
    {"name": "Waldorf Streichfett", "ports": [(MidiPort.IN, Need.REQUIRED), (MidiPort.OUT, Need.LOW)]},
    {"name": "MFB Tanzbar", "ports": [(MidiPort.IN, Need.REQUIRED), (MidiPort.OUT, Need.LOW)],
     "note": "Check which MIDI ports it has"},
    {"name": "Sim n Tonic", "ports": [(MidiPort.IN, Need.REQUIRED)],
     "note": "Check which MIDI ports it has"},
    {"name": "Oberheim OB-X8", "ports": [(MidiPort.IN, Need.REQUIRED), (MidiPort.OUT, Need.REQUIRED)]},
    {"name": "Oberheim OB-6", "ports": [(MidiPort.IN, Need.REQUIRED), (MidiPort.OUT, Need.REQUIRED)]},
]


# Soundcraft Ghost centre (master) section rear panel, in the order the manual lists it.
# All jacks are 1/4"; "wired" is the patch bay label this jack goes to, if any.
# "wiring" is how the manual says each jack is wired.
ghost_rear = [
    {"group": "Inputs", "short": "TRS balanced",
     "wiring": "tip signal +, ring signal −, sleeve ground", "jacks": [
        {"label": "FX 1 L/R", "category": Category.FX, "wired": "FX 1 In L/R"},
        {"label": "FX 2 L/R", "category": Category.FX, "wired": "FX 2 In L/R"},
        {"label": "FX 3 L/R", "category": Category.FX, "wired": "FX 3 In L/R"},
        {"label": "FX 4 L/R", "category": Category.FX, "wired": "FX 4 In L/R"},
        {"label": "2TK A I/P L/R", "category": Category.TWO_TRACK, "wired": "Ghost 2 Track A Input"},
        {"label": "2TK B I/P L/R", "category": Category.TWO_TRACK, "wired": "Ghost 2 Track B Input"},
    ]},
    {"group": "Outputs", "short": "TRS ground-comp",
     "wiring": "tip signal +, ring ground sense, sleeve ground; the TS unbalanced ones are "
               "tip signal +, ring not used, sleeve ground", "jacks": [
        {"label": "GRP 1-8", "category": Category.GROUPS, "wired": "Group 1 - 8 Out", "count": 8},
        {"label": "AUX 1", "category": Category.FX, "wired": "Aux 1 Out", "count": 1},
        {"label": "AUX 2", "category": Category.FX, "wired": "Aux 2 Out", "count": 1},
        {"label": "AUX 3", "category": Category.FX, "wired": "Aux 3 Out", "count": 1},
        {"label": "AUX 4", "category": Category.FX, "wired": "Aux 4 Out", "count": 1},
        {"label": "AUX 5 / 6", "category": Category.FX, "wired": "Aux 5 / 6 Out", "count": 2},
        {"label": "AUX 7 L/R", "category": Category.FX, "wired": "Aux 7 Out L/R"},
        {"label": "AUX 8 L/R", "category": Category.FX, "wired": "Aux 8 Out L/R"},
        {"label": "MIX O/P L/R", "category": Category.TWO_TRACK, "wired": "Ghost MIX O/P L/R"},
        {"label": "MIX B O/P L/R", "category": Category.TWO_TRACK, "wired": "Ghost MIX B O/P L/R"},
        {"label": "CRM O/P L/R", "category": Category.MONITORING, "short": "TS unbalanced", "wired": "Control Room Out L/R"},
        {"label": "ALT O/P L/R", "category": Category.MONITORING, "short": "TS unbalanced", "wired": "Alt CRM Out L"},
        {"label": "STU O/P A L/R", "category": Category.MONITORING, "wired": "Studio A O/P L/R"},
        {"label": "STU PHNS B L/R", "category": Category.MONITORING, "short": "TS unbalanced", "wired": "Studio Phones B L/R Out"},
    ]},
    {"group": "Inserts", "short": "TRS insert",
     "wiring": "tip RETURN, ring SEND, sleeve ground - the opposite of the usual tip-send wiring", "jacks": [
        {"label": "GRP INS 1-8", "category": Category.GROUPS, "wired": "Group 1 - 8 Insert Send", "count": 8},
        {"label": "MIX INS L/R", "category": Category.CONSOLE, "wired": "Main Insert Send"},
    ]},
]

# Odd jobs that don't belong to a bay, a cable run or a rack unit.
todos = [
    "Find the screws for all the cover plates",
    "Gather every cover plate in one place",
    "Work out which rooms are missing cover plates - Kitchen and Guest Bed are, the rest unknown",
    "Go back to every black-flagged XLR run and terminate it once the parts arrive",
    "Identify the stray XLR sticking out of the loom behind the desk (Steve found it) - it comes from one "
    "of the rooms, but which one is unknown. Tone it out and label both ends",
]


# Compromises made during the build that aren't tied to one port. Anything with an "info"
# key on a patch bay entry is listed alongside these automatically.
compromises = [
    {"where": "Room XLR runs", "what":
        "While spooling out the cable, every XLR run from a room to the console is flagged with black tape at "
        "BOTH ends - room side and console side - because the parts to finish them aren't here yet. Anything "
        "without a black flag was soldered and jacked into the patch bay as it was pulled. So: black flag = "
        "still to terminate."},
]


# Faults to work through in a console service session. Tick them off in the HTML view.
console_issues = [
    {"where": "Channel 6", "noticed": "2026-09-25",
     "symptom": "Intermittent - passes no signal unless the source is hot, and tapping the channel brings it "
                "back. Suspect a dry solder joint or dirty contact rather than a dead stage."},
]

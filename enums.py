"""Enumerations used in config.py. Values are the plain strings the HTML view uses as CSS hooks."""
from enum import Enum


class _StrEnum(str, Enum):
    def __str__(self):
        return self.value


class Category(_StrEnum):
    """Colour grouping of a patch bay entry or rack unit in the HTML view."""
    CONSOLE = "console"
    ROOMS = "rooms"
    TIE_LINES = "tielines"
    OUTBOARD = "outboard"
    INSTRUMENTS = "instruments"
    FX = "fx"
    MONITORING = "monitoring"
    TWO_TRACK = "twotrack"
    GROUPS = "groups"
    AMP = "amp"
    NETWORK = "network"
    POWER = "power"
    COMPUTER = "computer"
    MIDI = "midi"


class JackType(_StrEnum):
    """How a bay's jacks are drawn in the HTML view (1/4" TRS unless set)."""
    TRS = "trs"
    MIDI = "midi"
    SWITCH = "switch"
    ETHERNET = "ethernet"


class MidiPort(_StrEnum):
    """A 5-pin MIDI connection on an instrument."""
    IN = "In"
    OUT = "Out"
    THRU = "Thru"


class Need(_StrEnum):
    """How much an instrument's MIDI connection matters."""
    REQUIRED = "required"
    LOW = "low priority"

"""Sanity checks for config.py. Both generators call validate() before producing anything."""
import sys

from enums import Category, JackType

BAY_KEYS = {"label_name", "entries", "port_count", "single_row", "rack", "jack_type"}
ENTRY_KEYS = {"normalled", "top", "bottom", "width", "category", "note", "pending"}
UNIT_KEYS = {"u", "size", "name", "category", "patch", "slots", "movable", "plan", "note", "image"}
DEFAULT_PORTS = 24


def _spare(text):
    return text is None or str(text).strip() in ("", "-")


def _enum_hint(enum, value):
    match = next((m for m in enum if m.value == str(value).lower()), None)
    choices = ", ".join(f"{enum.__name__}.{m.name}" for m in enum)
    return f"use {enum.__name__}.{match.name}" if match else f"expected one of: {choices}"


def check_bays(bays, where="config"):
    problems, seen = [], set()
    for b_i, bay in enumerate(bays):
        name = bay.get("label_name", f"#{b_i + 1}")
        at = f"{where}: bay {name}"
        if name in seen:
            problems.append(f"{at}: duplicate label_name")
        seen.add(name)
        for key in set(bay) - BAY_KEYS:
            problems.append(f"{at}: unknown key '{key}'")
        if "jack_type" in bay and not isinstance(bay["jack_type"], JackType):
            problems.append(f"{at}: jack_type {bay['jack_type']!r} - {_enum_hint(JackType, bay['jack_type'])}")
        single = bay.get("single_row", False)
        port, ports = 1, bay.get("port_count", DEFAULT_PORTS)
        for entry in bay.get("entries", []):
            width = entry.get("width")
            span = f"{at}, port {port}"
            for key in set(entry) - ENTRY_KEYS:
                problems.append(f"{span}: unknown key '{key}'")
            if not isinstance(width, int) or width < 1:
                problems.append(f"{span}: width must be a positive whole number, got {width!r}")
                width = 1
            if not isinstance(entry.get("normalled"), bool):
                problems.append(f"{span}: normalled must be True or False")
            if not isinstance(entry.get("top"), str):
                problems.append(f"{span}: missing top label")
            if not single and not isinstance(entry.get("bottom"), str):
                problems.append(f"{span}: missing bottom label")
            if "category" in entry and not isinstance(entry["category"], Category):
                problems.append(f"{span}: category {entry['category']!r} - {_enum_hint(Category, entry['category'])}")
            if "pending" in entry and not (_spare(entry.get("top")) and (single or _spare(entry.get("bottom")))):
                problems.append(f"{span}: 'pending' only goes on a spare ('-') entry")
            port += width
        if port - 1 != ports:
            problems.append(f"{at}: entries cover {port - 1} ports, bay has {ports}")
    return problems


def check_gear(racks):
    problems = []
    for rack in racks:
        used = {}
        for unit in rack.get("units", []):
            at = f"gear rack {rack.get('name')}: U{unit.get('u')} {unit.get('name') or '(empty)'}"
            for key in set(unit) - UNIT_KEYS:
                problems.append(f"{at}: unknown key '{key}'")
            if "category" in unit and not isinstance(unit["category"], Category):
                problems.append(f"{at}: category {unit['category']!r} - {_enum_hint(Category, unit['category'])}")
            for u in range(unit.get("u", 0), unit.get("u", 0) + unit.get("size", 1)):
                if u in used:
                    problems.append(f"{at}: overlaps {used[u]} at U{u}")
                used[u] = unit.get("name") or "(empty)"
    return problems


def check_installed(installed, bays, previous_bays):
    problems = []
    positions = {b["label_name"] for b in bays}
    units = {b["label_name"] for b in previous_bays}
    for pos, unit in installed.items():
        if pos not in positions:
            problems.append(f"installed_units: position {pos!r} is not a bay in config")
        if unit not in units:
            problems.append(f"installed_units: unit {unit!r} is not a bay in previous_config")
    dupes = {u for u in installed.values() if list(installed.values()).count(u) > 1}
    for unit in sorted(dupes):
        problems.append(f"installed_units: unit {unit!r} is mounted in two places")
    return problems


def check_card_changes(changes, previous_bays):
    problems = []
    sizes = {b["label_name"]: b.get("port_count", DEFAULT_PORTS) for b in previous_bays}
    for unit, ports in changes.items():
        if unit not in sizes:
            problems.append(f"card_changes: unit {unit!r} is not a bay in previous_config")
            continue
        for port, normalled in ports.items():
            if not isinstance(port, int) or not 1 <= port <= sizes[unit]:
                problems.append(f"card_changes: unit {unit!r} has no port {port!r}")
            if not isinstance(normalled, bool):
                problems.append(f"card_changes: unit {unit!r} port {port}: use True or False")
    return problems


def validate(bays, gear_racks=(), installed=None, previous_bays=(), card_changes=None):
    problems = check_bays(bays) + check_gear(gear_racks)
    if installed is not None:
        problems += check_installed(installed, bays, previous_bays)
    problems += check_card_changes(card_changes or {}, previous_bays)
    if problems:
        print("config.py has problems:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        sys.exit(1)

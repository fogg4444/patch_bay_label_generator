"""Render config.py as a single self-contained HTML view of every patch bay."""
from datetime import date
from html import escape
import re
import os

from config import (config as all_configs, gear_racks, installed_units, keep_installed_units, card_changes,
                    midi_instruments, ROOMS, SPEAKER_ONLY, special_runs, open_questions,
                    ghost_rear, todos, compromises)
from enums import Category, JackType, Need, CableKind
from previous_config import config as previous_configs

output_path = "html_output/patch_bay.html"

expected_count = 24

switch_svg = ('<svg viewBox="0 0 20 30" aria-hidden="true"><rect x="1" y="1" width="18" height="28" rx="2.5" fill="#0c0d0e" stroke="#9aa1a6" stroke-width="1.5"/>'
              '<rect x="4" y="4" width="12" height="11" rx="1.5" fill="#3a4046"/><rect x="4" y="15" width="12" height="11" rx="1.5" fill="#23272b"/>'
              '<rect x="8.5" y="7" width="3" height="5" rx=".8" fill="#b9bec2"/><circle cx="10" cy="20.5" r="2.4" fill="none" stroke="#6b7278" stroke-width="1.2"/></svg>')
rj45_svg = '<svg viewBox="0 0 26 24" aria-hidden="true"><rect x="1" y="1" width="24" height="22" rx="1.5" fill="#9aa1a6"/><path d="M3.5 3.5h19v12.5h-5v3.5h-9v-3.5h-5z" fill="#0c0d0e"/><rect x="5.30" y="5" width="1.1" height="4.2" fill="#c9a34a"/><rect x="7.35" y="5" width="1.1" height="4.2" fill="#c9a34a"/><rect x="9.40" y="5" width="1.1" height="4.2" fill="#c9a34a"/><rect x="11.45" y="5" width="1.1" height="4.2" fill="#c9a34a"/><rect x="13.50" y="5" width="1.1" height="4.2" fill="#c9a34a"/><rect x="15.55" y="5" width="1.1" height="4.2" fill="#c9a34a"/><rect x="17.60" y="5" width="1.1" height="4.2" fill="#c9a34a"/><rect x="19.65" y="5" width="1.1" height="4.2" fill="#c9a34a"/></svg>'
din_svg = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="11" fill="#9aa1a6"/><circle cx="12" cy="12" r="9.2" fill="#0c0d0e"/><rect x="10.4" y="2.2" width="3.2" height="3.4" rx=".6" fill="#9aa1a6"/><circle cx="17.20" cy="12.00" r="1.25" fill="#b9bec2"/><circle cx="15.68" cy="15.68" r="1.25" fill="#b9bec2"/><circle cx="12.00" cy="17.20" r="1.25" fill="#b9bec2"/><circle cx="8.32" cy="15.68" r="1.25" fill="#b9bec2"/><circle cx="6.80" cy="12.00" r="1.25" fill="#b9bec2"/></svg>'
console_bucket = 16  # left-side console buckets; divider drawn after this port

categories = {
    Category.CONSOLE:     ("Console core",          "#4f86e8"),
    Category.ROOMS:       ("Room sends",            "#ec6a55"),
    Category.TIE_LINES:   ("Tie lines",             "#6fa3b5"),
    Category.OUTBOARD:    ("Outboard",              "#e3a02f"),
    Category.INSTRUMENTS: ("Instruments & pedals",  "#d467ad"),
    Category.FX:          ("Aux sends & FX",        "#2fb39f"),
    Category.MONITORING:  ("Monitoring",            "#9a73e0"),
    Category.TWO_TRACK:   ("2-track",               "#8fb935"),
    Category.GROUPS:      ("Groups & mix bus",      "#d8c23a"),
    Category.AMP:         ("Amp rack",              "#8b929c"),
    Category.NETWORK:     ("Network",               "#4fb1dc"),
    Category.POWER:       ("Power",                 "#c75a5a"),
    Category.COMPUTER:    ("Computer",              "#7c8ea3"),
    Category.MIDI:        ("MIDI",                  "#b98a5c"),
}


def is_spare(text):
    return text is None or text.strip() in ("", "-")


def grid_col(port, port_count):
    """Grid column for a 1-indexed port; 24-port bays get a divider column after port 16."""
    if port_count == expected_count and port > console_bucket:
        return port + 1
    return port


def span(start, width, port_count):
    return f"{grid_col(start, port_count)} / {grid_col(start + width - 1, port_count) + 1}"


def render_bay(bay):
    port_count = bay.get("port_count", expected_count)
    single_row = bay.get("single_row", False)
    jack_svg = {JackType.MIDI: din_svg, JackType.SWITCH: switch_svg, JackType.ETHERNET: rj45_svg}.get(bay.get("jack_type"))
    jack_kind = bay.get("jack_type", "")
    has_divider = port_count == expected_count
    template = (f"repeat({console_bucket}, minmax(0, 1fr)) var(--divider) repeat({port_count - console_bucket}, minmax(0, 1fr))"
                if has_divider else f"repeat({port_count}, minmax(0, 1fr))")

    rows = ["numbers", "tape-top", "jacks-top"] if single_row else \
           ["numbers", "tape-top", "jacks-top", "norm", "jacks-bottom", "tape-bottom"]
    row_of = {name: i + 1 for i, name in enumerate(rows)}

    cells = ['<span class="split" style="grid-column:17;grid-row:1 / -1"></span>'] if has_divider else []
    for port in range(1, port_count + 1):
        cells.append(f'<span class="num" style="grid-area:{row_of["numbers"]} / {grid_col(port, port_count)}">{port}</span>')

    spare_ports = 0
    normalled_ports = 0
    # Rear-panel "plugged in" checkboxes: main rack bays by default, others opt in with track_rear
    wiring = bay.get("track_rear", bay["label_name"].isdigit() and not single_row)
    wired_total = [0]
    port = 1
    for entry in bay["entries"]:
        width = entry["width"]
        cat = entry.get("category", "")
        top, bottom = entry.get("top", "-"), entry.get("bottom", "-")
        spare = is_spare(top) and (single_row or is_spare(bottom))
        if spare:
            cat = "spare"
            spare_ports += width
        normalled = entry.get("normalled") and not spare
        pending = entry.get("pending")
        note = entry.get("note")
        if not single_row and not entry.get("normalled") and is_spare(top) and not is_spare(bottom):
            # Neutrik NYS-SPP-L1 "turned" card: with no plug in the rear top jack,
            # the front top jack is tied to the bottom line.
            note = ((note + " ") if note else "") + (
                "Card is turned but nothing is wired to the rear top jack, so the front top jack is "
                f"connected to {bottom}. Only patch into it if you mean to feed {bottom}.")
        port_range = f"{port}" if width == 1 else f"{port}-{port + width - 1}"
        tip = f"Bay {bay['label_name']} · port {port_range}\nTop: {top}"
        if not single_row:
            tip += f"\nBottom: {bottom}\n{'Normalled' if normalled else 'Not normalled'}"
        if pending:
            tip += f"\nReserved for: {pending}"
        if entry.get("in_use") is False:
            tip += "\nNot in use yet"
        info = entry.get("info")
        if info:
            tip += f"\n{info}"
        if note:
            tip += f"\nNote: {note}"
        cols = span(port, width, port_count)
        norm_state = "spare" if spare else ("normalled" if normalled else "open")
        common = f'data-cat="{cat}" data-norm="{norm_state}"{" data-pending" if pending else ""} title="{escape(tip)}"'
        flag = ""
        info_row = "tape-bottom" if entry.get("info_at") == "bottom" else "tape-top"
        info_mark = f'<i class="info-mark" title="{escape(info)}" aria-label="{escape(info)}">i</i>' if info else ""
        if note:
            note_id = f"note-{bay['label_name']}-{port}"
            flag = (f'<button type="button" class="flag" popovertarget="{note_id}" aria-label="Open question">?</button>'
                    f'<div popover id="{note_id}" class="pop"><b>Bay {escape(bay["label_name"])} · port {port_range}</b>{escape(note)}</div>')

        def tape(text, row):
            cls = "tape blank" if is_spare(text) else ("tape idle" if entry.get("in_use") is False else "tape")
            label = "" if is_spare(text) else escape(text)
            if is_spare(text) and pending:
                cls += " pending"
                pc = categories.get(entry.get("category"), ("", "var(--spare)"))[1]
                label = f'<em style="--pc:{pc}">Reserved · {escape(pending)}</em>'
            anchor = f' id="port-{bay["label_name"]}-{port}"' if row == "tape-top" else ""
            here = (flag if row == "tape-top" else "") + (info_mark if row == info_row else "")
            room = (" has-flag" if (flag and row == "tape-top") else "") + (" has-info" if (info_mark and row == info_row) else "")
            return (f'<div class="{cls}{room}"{anchor} {common} style="grid-row:{row_of[row]};grid-column:{cols}">'
                    f'<span>{label}</span>{here}</div>')

        cells.append(tape(top, "tape-top"))
        if not single_row:
            cells.append(tape(bottom, "tape-bottom"))
            if normalled:
                word = "Normalled" if width >= 2 else "N"
                cells.append(f'<div class="norm on" {common} style="grid-row:{row_of["norm"]};grid-column:{cols}"><span>{word}</span></div>')
                normalled_ports += width
            elif not spare:
                cells.append(f'<div class="norm off" {common} style="grid-row:{row_of["norm"]};grid-column:{cols}"></div>')
        def jack_attrs(text):
            """Unused jacks get no category colour."""
            unused = is_spare(text) or entry.get("in_use") is False
            return common.replace(f'data-cat="{cat}"', 'data-cat="spare"', 1) if unused else common

        def jack(extra, text, row, c, p, side, inner=""):
            """A jack; on wiring bays, a used jack is a toggle for 'plugged in'."""
            area = f'style="grid-area:{row_of[row]} / {c}"'
            if wiring and not is_spare(text) and entry.get("in_use", True):
                wire_id = f"bay-{bay['label_name']}-{side}-{p}"
                attrs = jack_attrs(text).replace('title="', 'title="Click to mark the rear jack plugged in&#10;', 1)
                wired_total[0] += 1
                where = "top" if side == "t" else "bottom"
                return (f'<button type="button" class="jack wire{extra}" data-wire="{wire_id}" data-bay="{escape(bay["label_name"])}" '
                        f'aria-pressed="false" aria-label="Bay {escape(bay["label_name"])} {where} port {p} rear: {escape(text)}" '
                        f'{attrs} {area}>{inner}</button>')
            return f'<span class="jack{extra}" {jack_attrs(text)} {area}>{inner}</span>'

        for p in range(port, port + width):
            c = grid_col(p, port_count)
            n = " normalled" if normalled else ""
            if jack_svg:
                cells.append(jack(f" drawn {jack_kind}", top, "jacks-top", c, p, "t", jack_svg))
            else:
                cells.append(jack(n, top, "jacks-top", c, p, "t"))
            if not single_row:
                cells.append(jack(n + " lower", bottom, "jacks-bottom", c, p, "b"))
        port += width

    kind = "Single row" if single_row else f"{port_count} × 2"
    stats = ['<span class="idle-pill">Not in use</span>'] if bay.get("in_use") is False else []
    stats += [kind, f"<b>{spare_ports}</b> spare"]
    if not single_row:
        stats.append(f"<b>{normalled_ports}</b> normalled")
    if wiring:
        stats.append(f'<b class="wired-count" data-bay="{escape(bay["label_name"])}">0</b>/{wired_total[0]} rear plugged in')
    stats_html = "".join(f"<p>{x}</p>" for x in stats)
    return f"""
<section class="bay" id="bay-{escape(bay['label_name'])}">
  <header class="bay-head">
    <h2{'' if bay['label_name'][0].isdigit() else ' class="named"'}>{escape(bay['label_name'].replace('-', ' '))}</h2>
    {stats_html}
  </header>
  <div class="scroll"><div class="panel{' has-divider' if has_divider else ''}{' idle' if bay.get('in_use') is False else ''}" style="grid-template-columns:{template}">
    {''.join(cells)}
  </div></div>
  <details class="bay-note-wrap">
    <summary>Notes</summary>
    <textarea class="bay-note" data-bay="{escape(bay['label_name'])}" rows="2" placeholder="Notes for this bay…"
      aria-label="Notes for bay {escape(bay['label_name'])}"></textarea>
  </details>
</section>"""


def render_racks():
    racks = []
    for bay in all_configs:
        if bay.get("rack") or not racks:
            racks.append((bay.get("rack", "Rack"), []))
        racks[-1][1].append(bay)
    return "".join(
        f'<section class="rack-group"><h2 class="rack-name">{escape(name)}</h2>'
        f'<div class="rack">{"".join(render_bay(b) for b in bays)}</div></section>'
        for name, bays in racks)


def bay_title(label_name):
    return f"Bay {label_name}" if label_name[0].isdigit() else label_name.replace("-", " ").title()


def patch_locations(needle):
    """Bay/port ranges whose labels mention `needle`."""
    found = []
    for bay in all_configs:
        ports, port = [], 1
        for e in bay["entries"]:
            text = f'{e.get("top", "")} {e.get("bottom", "")}'.lower()
            if needle.lower() in text:
                ports += range(port, port + e["width"])
            port += e["width"]
        if ports:
            found.append(f'{bay_title(bay["label_name"])} · {port_ranges(ports)}')
    return found


def render_gear_rack(rack):
    rows = []
    for unit in rack["units"]:
        u, size = unit["u"], unit["size"]
        cat = unit.get("category", "spare")
        units_label = f"U{u}" if size == 1 else f"U{u}–{u + size - 1}"
        badges = []
        if unit.get("movable"):
            badges.append('<span class="badge move">Could move</span>')
        if unit.get("plan"):
            badges.append(f'<span class="badge plan">{escape(unit["plan"])}</span>')
        if unit.get("note"):
            badges.append(f'<span class="badge q">? {escape(unit["note"])}</span>')
        slots = ""
        if unit.get("slots"):
            slots = '<div class="slots">' + "".join(
                f'<span class="slot{" tbd" if s is None else ""}">{escape(s) if s else i + 1}</span>'
                for i, s in enumerate(unit["slots"])) + "</div>"
        patched = ""
        if unit.get("bay"):
            bay = next(b for b in all_configs if b["label_name"] == unit["bay"])
            ports = bay.get("port_count", expected_count)
            patched = (f'<p class="patched">Patch bay: <a href="#bay-{escape(bay["label_name"])}">'
                       f'{escape(bay_title(bay["label_name"]))} · 1–{ports}</a></p>')
        elif unit.get("patch"):
            locs = patch_locations(unit["patch"])
            patched = ('<p class="patched">Patch bay: ' + ", ".join(escape(l) for l in locs) + "</p>") if locs else \
                      '<p class="patched none">Not on the patch bay</p>'
        name = escape(unit["name"]) if unit["name"] else "Empty"
        rows.append(f"""
      <div class="ru{' empty' if not unit['name'] else ''}" data-cat="{cat}" style="grid-row:{u} / span {size}">
        <span class="ru-num">{units_label}</span>
        <div class="face">
          <div class="face-main"><b>{name}</b>{''.join(badges)}</div>
          {slots}{patched}
        </div>
      </div>""")
    total = max(x["u"] + x["size"] - 1 for x in rack["units"])
    return f"""
<section class="gear-rack">
  <h2 class="rack-name">{escape(rack['name'])} · equipment ({total}U)</h2>
  <div class="elevation" style="grid-template-rows:repeat({total}, var(--u))">{''.join(rows)}
  </div>
</section>"""


def normal_states(bay, spare_is_free):
    """Per-port normalled flag; None where the port is spare and its setting doesn't matter."""
    states = []
    for e in bay["entries"]:
        free = spare_is_free and is_spare(e.get("top")) and is_spare(e.get("bottom"))
        states += [None if free else bool(e["normalled"])] * e["width"]
    return states


def unit_card_states(unit):
    """A physical unit's cards now: its original layout plus any recorded card_changes."""
    states = normal_states(unit, False)
    for port, normalled in card_changes.get(unit["label_name"], {}).items():
        states[port - 1] = normalled
    return states


def with_racks(configs):
    rack, out = "Rack", []
    for bay in configs:
        rack = bay.get("rack", rack)
        if not bay.get("single_row"):
            out.append((rack, bay))
    return out


def port_ranges(ports):
    ranges, start = [], None
    for i, p in enumerate(ports):
        if start is None:
            start = p
        if i == len(ports) - 1 or ports[i + 1] != p + 1:
            ranges.append(f"{start}" if start == p else f"{start}–{p}")
            start = None
    return ", ".join(ranges)


def plan_unit_moves():
    """Assign each existing patch bay unit to a new position (same rack only), minimising
    normalling cards to flip, then distance moved. Returns (rows, flips_moving, flips_in_place)."""
    old, new = with_racks(previous_configs), with_racks(all_configs)
    rows, total, in_place = [], 0, 0
    for rack in dict.fromkeys(r for r, _ in new):
        units = [(i, b) for i, (r, b) in enumerate(old) if r == rack]
        slots = [(j, b) for j, (r, b) in enumerate(new) if r == rack]
        if len(units) != len(slots):
            continue

        def flips(unit, slot):
            return [p + 1 for p, (a, b) in enumerate(zip(unit_card_states(unit), normal_states(slot, True)))
                    if b is not None and a != b]

        # Fewest card flips first, then fewest units to move from where they're mounted now.
        mounted = set(installed_units.values())

        def move_cost(u, sl):
            if installed_units.get(sl["label_name"]) == u["label_name"]:
                return 0
            if keep_installed_units and (u["label_name"] in mounted or sl["label_name"] in installed_units):
                return 10 ** 9  # locked: don't move mounted units or displace them
            return 1

        cost = [[len(flips(u, sl)) * 1000 + move_cost(u, sl) for si, sl in slots] for ui, u in units]
        best = {0: (0, [])}  # bitmask of used units -> (cost, assignment); slots filled in order
        for k in range(len(slots)):
            nxt = {}
            for mask, (c, assign) in best.items():
                for u in range(len(units)):
                    if not mask & (1 << u):
                        cand = (c + cost[u][k], assign + [u])
                        m = mask | (1 << u)
                        if m not in nxt or cand[0] < nxt[m][0]:
                            nxt[m] = cand
            best = nxt
        _, assign = min(best.values())
        for k, u in enumerate(assign):
            unit, slot = units[u][1], slots[k][1]
            f = flips(unit, slot)
            want = normal_states(slot, True)
            to_n = [p for p in f if want[p - 1]]
            to_t = [p for p in f if p not in to_n]
            # Ports that were unused in the old layout: their real card position was never recorded.
            known = card_changes.get(unit["label_name"], {})
            unknown = [i + 1 for i, s in enumerate(normal_states(unit, True))
                       if s is None and want[i] is not None and (i + 1) not in known]
            check_n = [p for p in unknown if want[p - 1] and p not in f]
            check_t = [p for p in unknown if not want[p - 1] and p not in f]
            total += len(f)
            in_place += len(flips(units[k][1], slot))  # as if every unit went back to its old position
            rows.append((rack, slot["label_name"], unit["label_name"], unit["entries"][0].get("top", ""), to_n, to_t,
                         check_n, check_t))
    return rows, total, in_place


def render_moves():
    rows, total, in_place = plan_unit_moves()
    body = []
    tasks = 0
    where = {u: pos for pos, u in installed_units.items()}
    for rack, pos, unit, was, to_n, to_t, check_n, check_t in rows:
        moved = installed_units.get(pos) != unit
        now = f"now at bay {where[unit]}" if unit in where else "not mounted"
        work = []
        if to_n:
            work.append(f'<span class="flip on">Ports {port_ranges(to_n)} → normalled</span>')
        if to_t:
            work.append(f'<span class="flip off">Ports {port_ranges(to_t)} → not normalled</span>')
        def check_text(ports, state):
            one = len(ports) == 1
            return f'Check {"port" if one else "ports"} {port_ranges(ports)} {"is" if one else "are"} {state}'
        if check_n:
            work.append(f'<span class="flip check">{check_text(check_n, "normalled")}</span>')
        if check_t:
            work.append(f'<span class="flip check">{check_text(check_t, "not normalled")}</span>')
        needs_work = moved or to_n or to_t or check_n or check_t
        task_id = f"bay-{pos}-from-{unit}"
        if needs_work:
            tasks += 1
            check = (f'<input type="checkbox" class="move-check" id="{escape(task_id)}" data-task="{escape(task_id)}" '
                     f'aria-label="Bay {escape(pos)} done">')
        else:
            check = '<span class="nothing" title="Nothing to do">–</span>'
        body.append(f"""<tr class="{'moved' if moved else 'stays'}">
          <td class="done-cell">{check}</td>
          <td><label for="{escape(task_id)}"><b>Bay {escape(pos)}</b></label><small>{escape(rack)}</small></td>
          <td>{f'Unit from old bay {escape(unit)}' if moved else 'Already in place'}<small>{escape(now)} · old layout: {escape(was)}</small></td>
          <td>{''.join(work) or '<span class="flip none">No cards to flip</span>'}</td>
        </tr>""")
    return f"""
<details class="moves" id="moves">
  <summary><h2>Moving the patch bay units</h2><span class="archived">Archived · all units in place</span></summary>
  <p class="lead">Move whole units instead of re-setting normalling channel by channel. With the moves below you flip
  <b>{total}</b> normalling cards; keeping every unit in its old position would mean flipping <b>{in_place}</b>.
  Units already in the right place are marked "Already in place"; where units are mounted now comes from
  <code>installed_units</code> in <code>config.py</code>.
  Units only move within their own rack, and spare ports don't count.</p>
  <p class="lead">Reading a card: <b>normalled</b> (standard) has the grey jack on the <b>front bottom</b> row;
  <b>not normalled</b> (turned) has the grey jack on the <b>rear top</b> row. "Check" means the old layout had that
  port unused, so its card position was never recorded. Look at it before mounting the unit.</p>
  {f'<p class="progress" id="move-progress" data-total="{tasks}"><b>0</b> of {tasks} done</p>' if tasks else '<p class="progress">Every unit is mounted and every card is set. Nothing left to do.</p>'}
  <div class="scroll"><table>
    <thead><tr><th><span class="visually-hidden">Done</span></th><th>Position</th><th>Unit to put there</th><th>Normalling cards to flip</th></tr></thead>
    <tbody>{''.join(body)}</tbody>
  </table></div>
</details>"""


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def render_midi_list():
    rows, total = [], 0
    for inst in midi_instruments:
        ports = inst["ports"]
        for i, (port, need) in enumerate(ports):
            total += 1
            task = f"{slug(inst['name'])}-{slug(port.value)}"
            jack = inst.get("jacks", {}).get(port)
            first = i == 0
            name_cell = (f'<td rowspan="{len(ports)}" class="inst"><b>{escape(inst["name"])}</b>'
                         + (f'<small>{escape(inst["note"])}</small>' if inst.get("note") else "") + "</td>") if first else ""
            rows.append(f"""<tr class="{'first' if first else ''}">
          <td class="done-cell"><input type="checkbox" class="midi-check" id="midi-{task}" data-task="{task}"
            aria-label="{escape(inst['name'])} MIDI {port.value} connected"></td>
          {name_cell}
          <td><label for="midi-{task}">MIDI {escape(port.value)}</label></td>
          <td><span class="need {'low' if need == Need.LOW else 'req'}">{escape(need.value.capitalize())}</span></td>
          <td>{f'MIDI patch bay jack {jack}' if jack else '<span class="tbd">Not assigned</span>'}</td>
        </tr>""")
    return f"""
<section class="midi-list" id="midi-list">
  <h2>MIDI hookups</h2>
  <p class="progress" id="midi-progress"><b>0</b> of {total} connected</p>
  <div class="scroll"><table>
    <thead><tr><th><span class="visually-hidden">Connected</span></th><th>Instrument</th><th>Port</th><th>Priority</th><th>MIDI patch bay</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table></div>
</section>"""


def find_port(label):
    """Where a label sits: (bay label_name, port, "top"/"bottom"), or None."""
    for bay in all_configs:
        port = 1
        for e in bay["entries"]:
            for side in ("top", "bottom"):
                if e.get(side) == label:
                    span = f"{port}" if e["width"] == 1 else f"{port}–{port + e['width'] - 1}"
                    return bay["label_name"], port, "" if bay.get("single_row") else side, span
            port += e["width"]
    return None


def where_is(label, fallback):
    at = find_port(label)
    return f"{bay_title(at[0])} · port {at[3]} {at[2]}".rstrip() if at else fallback


def cable_runs(room):
    """Cables to one room: (name, kind, where it lands, how it ends, patched console, patched room)."""
    runs = []
    if room in SPEAKER_ONLY:
        runs.append(("Speaker", CableKind.SPEAKER, "Amp out to the speaker - not on a patch bay", "", False, False))
    else:
        for side, label in (("Send L", f"{room} L"), ("Send R", f"{room} R")):
            runs.append((side, CableKind.XLR, where_is(label, "Not on a bay yet"),
                         "XLR at the room, TRS into the patch bay", True, True))
        runs.append(("Return", CableKind.XLR, "Loom on the floor - no patching yet", "XLR both ends", False, True))
    at = find_port(room)
    if at:
        runs.append(("Network", CableKind.CAT5, f"Ethernet · jack {at[1]}", "", True, True))
    return runs


# (id, column heading, tooltip verb, applies to every run or only to patched ones)
# (id, column heading, tooltip, when it applies: always / "console" / "room")
CABLE_STEPS = (("pull", "Pull", "Pull the cable", "always"),
               ("room", "Terminated room end", "Room end soldered onto its connector", "always"),
               ("rack", "Terminated console end", "Console end soldered onto its connector", "always"),
               ("patch-room", "Patched room side", "Plugged in at the room plate", "room"),
               ("patch", "Patched console side", "Plugged into the patch bay", "console"))


def render_room_cables():
    cards, total = [], 0
    places = [(room, cable_runs(room)) for room in ROOMS]
    places += [(extra["name"], [(n, k, "", "", patched, False) for n, k, w, patched in extra["runs"]])
               for extra in special_runs]
    for room, runs in places:
        rows, room_total = [], 0
        for name, kind, where, ends, patched, patched_room in runs:
            cells = []
            for step, step_name, verb, applies in CABLE_STEPS:
                if (applies == "console" and not patched) or (applies == "room" and not patched_room):
                    cells.append('<td><span class="na" title="Nothing to patch here">–</span></td>')
                    continue
                total += 1
                room_total += 1
                task = f"{slug(room)}-{slug(name)}-{step}"
                if kind == CableKind.CAT5:
                    verb = verb.replace("Solder", "Terminate")
                group = "solder" if step in ("room", "rack") else ("patch" if step.startswith("patch") else step)
                cells.append(f'<td><input type="checkbox" class="cable-check" id="cable-{task}" data-task="{task}" '
                             f'data-room="{slug(room)}" data-group="{group}" data-kind="{slug(kind)}" '
                             f'title="{escape(room)} · {escape(name)} · {escape(verb)}" '
                             f'aria-label="{escape(room)} {escape(name)}: {escape(verb)}"></td>')
            rows.append('<tr><th scope="row"><span class="row-label"><b>' + escape(name) + '</b>'
                        + '<span class="kind ' + slug(kind) + '">' + kind + '</span></span></th>' + "".join(cells) + '</tr>')
        cards.append('<article class="room-card"><header><h3>' + escape(room) + '</h3>'
                     + f'<span class="room-count" data-room="{slug(room)}" hidden></span></header>'
                     + '<table><thead><tr><td></td>' + "".join(f'<th scope="col" title="{escape(v)}">{escape(h)}</th>' for _, h, v, _ in CABLE_STEPS) + '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
                     + f'<textarea class="room-note" data-room="{slug(room)}" rows="2" placeholder="Notes…" '
                       f'aria-label="Notes for {escape(room)}"></textarea></article>')
    lead = ("Two XLR sends, one XLR return and one Cat5 per room. Each cable: pull it, terminate both ends "
            "onto their connectors, then patch it in at the room plate and at the console - <b>%d</b> tasks in all. "
            "A dash means there is nothing to patch there: the returns live in a floor loom and the deck "
            "speaker runs never touch a bay." % total)
    return ('<section class="cables" id="cables"><h2>Cable pulls to each room</h2>'
            f'<p class="lead">{lead}</p>'
            '<div class="cable-bars">'
            '<div class="wire-progress" data-group="pull">'
            '<div class="wp-label"><b class="wp-pct">0%</b> cable runs pulled <span class="wp-count"></span></div>'
            '<div class="wp-track" role="progressbar" aria-label="Cable runs pulled" aria-valuemin="0" aria-valuemax="100" '
            'aria-valuenow="0"><div class="wp-fill"></div></div></div>'
            '<div class="wire-progress" data-group="pull" data-kind="xlr">'
            '<div class="wp-label"><b class="wp-pct">0%</b> XLR runs pulled <span class="wp-count"></span></div>'
            '<div class="wp-track" role="progressbar" aria-label="XLR runs pulled" aria-valuemin="0" aria-valuemax="100" '
            'aria-valuenow="0"><div class="wp-fill"></div></div></div>'
            '<div class="wire-progress" data-group="solder">'
            '<div class="wp-label"><b class="wp-pct">0%</b> ends soldered <span class="wp-count"></span></div>'
            '<div class="wp-track" role="progressbar" aria-label="Cable ends soldered" aria-valuemin="0" aria-valuemax="100" '
            'aria-valuenow="0"><div class="wp-fill"></div></div></div>'
            '<div class="wire-progress" data-group="patch">'
            '<div class="wp-label"><b class="wp-pct">0%</b> patched in <span class="wp-count"></span></div>'
            '<div class="wp-track" role="progressbar" aria-label="Cables patched in" aria-valuemin="0" aria-valuemax="100" '
            'aria-valuenow="0"><div class="wp-fill"></div></div></div>'
            '<div class="wire-progress total" data-group="all">'
            '<div class="wp-label"><b class="wp-pct">0%</b> of everything <span class="wp-count"></span></div>'
            '<div class="wp-track" role="progressbar" aria-label="All cable tasks" aria-valuemin="0" aria-valuemax="100" '
            'aria-valuenow="0"><div class="wp-fill"></div></div></div>'
            '</div>'
            f'<div class="room-grid">{"".join(cards)}</div></section>')


def render_ghost_rear():
    groups = []
    for block in ghost_rear:
        jacks = []
        for j in block["jacks"]:
            count = j.get("count", 2 if "L/R" in j["label"] else 1)
            at = find_port(j["wired"]) if j.get("wired") else None
            to = f'{bay_title(at[0])} · {at[3]}' if at else "not patched"
            kind = j.get("short", block.get("short", ""))
            wires = ""
            if at:
                side = "b" if at[2] == "bottom" else "t"
                wires = ' data-wires="' + ",".join(
                    f"bay-{at[0]}-{side}-{n}" for n in range(at[1], at[1] + count)) + '"' 

            jacks.append(
                f'<li data-cat="{j.get("category", "spare")}"{wires} title="{escape(j["label"])} - {escape(to)}">'
                + '<span class="gj-jacks">' + "".join("<i></i>" for _ in range(count)) + "</span>"
                + f'<b>{escape(j["label"])}</b>'
                + (f'<span class="gj-kind">{escape(kind)}</span>' if kind else '')
                + f'<small>{escape(to)}</small>'
                + '</li>')
        gid = slug(block["group"])
        wiring = f'<p class="gj-wiring">{escape(block["wiring"])}</p>' if block.get("wiring") else ""
        groups.append(f'<div class="gj-group" id="gj-{gid}" data-group="{gid}">'
                      f'<h3>{escape(block["group"])}</h3>{wiring}<ul>{"".join(jacks)}</ul></div>')
    tabs = "".join(
        f'<button type="button" class="gj-tab" data-show="{slug(b["group"])}" aria-pressed="false">'
        f'{escape(b["group"])}</button>' for b in ghost_rear)
    tabs += '<button type="button" class="gj-tab" data-show="all" aria-pressed="true">All</button>'
    return f"""
<section class="ghost" id="ghost-rear">
  <h2>Soundcraft Ghost · centre section rear</h2>
  <p class="lead">Every jack on the master section's rear panel, in the order the manual lists them - all ¼".
  Grey means nothing on the patch bay carries it yet.</p>
  <div class="gj-tabs" role="group" aria-label="Which jacks to show">{tabs}</div>
  <div class="gj-panel">{''.join(groups)}</div>
</section>"""


XLR_VIEWS = [
    ("Male · front", "pins facing you", {"tl": 1, "tr": 2, "b": 3}),
    ("Male · solder side", "cups facing you", {"tl": 2, "tr": 1, "b": 3}),
    ("Female · front", "holes facing you", {"tl": 2, "tr": 1, "b": 3}),
    ("Female · solder side", "cups facing you", {"tl": 1, "tr": 2, "b": 3}),
]
PIN_FILL = {1: "var(--pin-gnd)", 2: "var(--pin-hot)", 3: "var(--pin-cold)"}


def xlr_figure():
    parts = []
    for i, (title, sub, pins) in enumerate(XLR_VIEWS):
        cx, cy = 88 + i * 168, 104
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="56" fill="none" stroke="currentColor" stroke-width="2"/>')
        parts.append(f'<rect x="{cx - 13}" y="{cy - 58}" width="26" height="9" rx="3" fill="currentColor" opacity=".35"/>')
        for key, (dx, dy) in (("tl", (-27, -19)), ("tr", (27, -19)), ("b", (0, 35))):
            n = pins[key]
            parts.append(f'<circle cx="{cx + dx}" cy="{cy + dy}" r="17" fill="{PIN_FILL[n]}" stroke="currentColor" stroke-width="1.5"/>')
            parts.append(f'<text x="{cx + dx}" y="{cy + dy + 5}" text-anchor="middle" font-size="15" font-weight="700" fill="#10151a">{n}</text>')
        parts.append(f'<text x="{cx}" y="188" text-anchor="middle" font-size="13" font-weight="600" fill="currentColor">{title}</text>')
        parts.append(f'<text x="{cx}" y="205" text-anchor="middle" font-size="11.5" fill="currentColor" opacity=".7">{sub}</text>')
    return "".join(parts)


def trs_figure():
    return (
        '<line x1="34" y1="70" x2="470" y2="70" stroke="currentColor" stroke-width="1" opacity=".25"/>'
        '<path d="M34 70 q10 -21 28 -21 h16 v42 h-16 q-18 0 -28 -21 z" fill="var(--pin-hot)" stroke="currentColor" stroke-width="1.5"/>'
        '<rect x="78" y="49" width="10" height="42" fill="currentColor" opacity=".35"/>'
        '<rect x="88" y="49" width="40" height="42" fill="var(--pin-cold)" stroke="currentColor" stroke-width="1.5"/>'
        '<rect x="128" y="49" width="10" height="42" fill="currentColor" opacity=".35"/>'
        '<rect x="138" y="49" width="118" height="42" fill="var(--pin-gnd)" stroke="currentColor" stroke-width="1.5"/>'
        '<rect x="256" y="40" width="150" height="60" rx="8" fill="none" stroke="currentColor" stroke-width="2"/>'
        '<text x="331" y="75" text-anchor="middle" font-size="12" fill="currentColor">solder lugs</text>'
        '<line x1="56" y1="44" x2="56" y2="22" stroke="currentColor" stroke-width="1.2"/>'
        '<text x="56" y="16" text-anchor="middle" font-size="12.5" font-weight="600" fill="currentColor">Tip</text>'
        '<line x1="108" y1="44" x2="108" y2="22" stroke="currentColor" stroke-width="1.2"/>'
        '<text x="108" y="16" text-anchor="middle" font-size="12.5" font-weight="600" fill="currentColor">Ring</text>'
        '<line x1="197" y1="96" x2="197" y2="120" stroke="currentColor" stroke-width="1.2"/>'
        '<text x="197" y="134" text-anchor="middle" font-size="12.5" font-weight="600" fill="currentColor">Sleeve</text>'
        '<text x="331" y="120" text-anchor="middle" font-size="11.5" fill="currentColor" opacity=".75">tip · ring · sleeve lugs inside</text>'
    )


def render_solder():
    """Pinouts for the XLR-to-TRS cables, for anyone with an iron in hand."""
    xlr_fig = xlr_figure()
    trs_fig = trs_figure()
    return f"""
<section class="solder" id="solder">
  <h2>Soldering · XLR to TRS</h2>
  <p class="lead">Hot is XLR pin 2 to the tip, cold is pin 3 to the ring, shield is pin 1 to the sleeve.
  Hold a connector with the two pins up and the single pin down, and read the view that matches what you are
  looking at - the solder side is the mirror of the front. Every connector has the numbers moulded beside
  each contact; trust those over any drawing.</p>
  <p class="pin-key">
    <span class="pk hot">2 · hot (+)</span>
    <span class="pk cold">3 · cold (−)</span>
    <span class="pk gnd">1 · shield</span>
  </p>
  <figure>
    <svg viewBox="0 0 680 215" role="img"
         aria-label="XLR 3-pin numbering seen from the front and from the solder side, for male and female connectors">
      {xlr_fig}
    </svg>
    <figcaption>XLR numbering flips left to right between the front of a connector and its solder side.</figcaption>
  </figure>
  <figure>
    <svg viewBox="0 0 490 145" role="img"
         aria-label="A quarter-inch TRS plug: tip is hot, ring is cold, sleeve is shield">
      {trs_fig}
    </svg>
    <figcaption>A ¼" TRS plug, tip first. The sleeve lug is the big one nearest the cable clamp.</figcaption>
  </figure>
  <table class="solder-map">
    <thead><tr><th>XLR</th><th>Signal</th><th>TRS</th><th>Wire</th></tr></thead>
    <tbody>
      <tr><td>Pin 2</td><td>Hot, +</td><td>Tip</td><td>Usually red or white</td></tr>
      <tr><td>Pin 3</td><td>Cold, −</td><td>Ring</td><td>Usually black or blue</td></tr>
      <tr><td>Pin 1</td><td>Shield</td><td>Sleeve</td><td>Braid or drain wire</td></tr>
    </tbody>
  </table>
  <ul class="solder-notes">
    <li><b>Ghost inserts are backwards from most desks:</b> tip is RETURN and ring is SEND on GRP INS and MIX INS.
      An insert cable built for another console will have send and return swapped here.</li>
    <li><b>Ghost outputs are ground compensated:</b> tip signal +, ring ground sense, sleeve ground. Wire them as TRS;
      a TS plug shorts the ring and throws that away. CRM, ALT and STU PHNS B are the plain unbalanced exceptions.</li>
    <li><b>Going unbalanced on purpose?</b> Leave the ring unconnected at the source end rather than shorting it
      to sleeve, and keep the shield on sleeve at both ends.</li>
    <li><b>Check before you trust it:</b> buzz tip, ring and sleeve against pins 2, 3 and 1 with a meter once the
      first cable is done, then build the rest to match.</li>
  </ul>
</section>"""


def render_compromises():
    """Every shortcut taken in the build: the info markers on the bays, plus anything in config."""
    items = []
    for bay in all_configs:
        port = 1
        for e in bay["entries"]:
            if e.get("info"):
                w = e["width"]
                rng = f"{port}" if w == 1 else f"{port}–{port + w - 1}"
                side = " bottom" if e.get("info_at") == "bottom" else " top"
                items.append((f'{bay_title(bay["label_name"])} · port {rng}{side}', e["info"]))
            port += e["width"]
    items += [(c.get("where", "Elsewhere"), c["what"]) for c in compromises]
    if not items:
        return ""
    rows = "".join(f'<li><b>{escape(where)}</b><span>{escape(text)}</span></li>' for where, text in items)
    return f"""
<section class="crimes" id="crimes">
  <h2>Imperfect crimes</h2>
  <p class="lead">Shortcuts taken during the build, so nobody has to rediscover them with a meter.
  Ones tied to a port also show as an <b>i</b> on that bay.</p>
  <ul class="crime-list">{rows}</ul>
</section>"""


def render_todos():
    items = "".join(
        f'<li><input type="checkbox" class="todo-check" id="todo-{i}" data-task="todo-{i}">'
        + f'<label for="todo-{i}">{escape(t)}</label></li>'
        for i, t in enumerate(todos))
    return f"""
<section class="todos" id="todos">
  <h2>To do</h2>
  <p class="progress" id="todo-progress"><b>0</b> of {len(todos)} done</p>
  <ul class="todo-list">{items}</ul>
  <textarea class="room-note todo-note" data-room="general" rows="3" placeholder="Anything else…"
    aria-label="General notes"></textarea>
</section>"""


def render_notes():
    items = [f'<li><span class="q-general">General</span> <span>{escape(q)}</span></li>' for q in open_questions]
    for bay in all_configs:
        port = 1
        for entry in bay["entries"]:
            if entry.get("note"):
                w = entry["width"]
                rng = f"{port}" if w == 1 else f"{port}–{port + w - 1}"
                items.append(f'<li><a href="#bay-{escape(bay["label_name"])}">{escape(bay_title(bay["label_name"]))}, port {rng}</a>'
                             f' <span>{escape(entry["note"])}</span></li>')
            port += entry["width"]
    return "".join(items)


def render_legend():
    used = {e.get("category") for b in all_configs for e in b["entries"]}
    chips = [f'<button type="button" class="chip" data-cat="{key}" aria-pressed="false" style="--c:{color}">{escape(name)}</button>'
             for key, (name, color) in categories.items() if key in used]
    chips.append('<button type="button" class="chip" data-cat="spare" aria-pressed="false" style="--c:var(--spare)">Spare</button>')
    chips.append('<button type="button" class="chip pending-chip" data-flag="pending" aria-pressed="false" style="--c:var(--engrave)">Reserved</button>')
    chips.append('<button type="button" class="chip" data-flag="unplugged" aria-pressed="false" style="--c:var(--plugged)">Rear not plugged in yet</button>')
    chips.append('<span class="chip-sep" aria-hidden="true"></span>')
    chips.append('<button type="button" class="chip norm-chip" data-norm="normalled" aria-pressed="false" style="--c:var(--norm)">Normalled</button>')
    chips.append('<button type="button" class="chip norm-chip open" data-norm="open" aria-pressed="false" style="--c:var(--engrave)">Not normalled</button>')
    return "".join(chips)


def total_spare():
    total = 0
    for bay in all_configs:
        for e in bay["entries"]:
            if is_spare(e.get("top")) and (bay.get("single_row") or is_spare(e.get("bottom"))):
                total += e["width"]
    return total


def build_html():
    cat_css = "".join(f'[data-cat="{k}"]{{--c:{c}}}' for k, (_, c) in categories.items())
    bay_count = len(all_configs)
    return f"""<title>Studio Carquinez Patch Bay</title>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Bungee+Tint&family=IBM+Plex+Mono:wght@400;500&family=Nunito:ital,wght@0,400;0,600;0,700;1,400&display=swap">
<style>
:root {{
  --ground: #e6e8e4;
  --ink: #1a1d1f;
  --muted: #5c6360;
  --line: #c9ccc6;
  --panel: #1d2023;
  --panel-edge: #33383c;
  --engrave: #a9b0b4;
  --tape: #f6f5ef;
  --tape-ink: #141414;
  --jack: #0c0d0e;
  --jack-ring: #6b7278;
  --spare: #7d8488;
  --focus: #2b6de0;
  --display: #754f3b;
  --accent: #b8705a;
  --plugged: #34a36a;
  --norm: #5f666b;
  --norm-2: #4a5055;
  --divider: 14px;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --ground: #202020; --ink: #ece7e4; --muted: #a49c98; --line: #343130;
    --panel: #1b1b1b; --panel-edge: #403c3a; --focus: #ffb787;
    --display: #e4bcbc; --accent: #ffb787;
  }}
}}
:root[data-theme="dark"] {{
  --ground: #202020; --ink: #ece7e4; --muted: #a49c98; --line: #343130;
  --panel: #1b1b1b; --panel-edge: #403c3a; --focus: #ffb787;
  --display: #e4bcbc; --accent: #ffb787;
}}
{cat_css}
[data-cat="spare"] {{ --c: var(--spare); }}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--ground); color: var(--ink);
  font: 14.5px/1.55 "Nunito", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}}
.wrap {{ max-width: 1280px; margin: 0 auto; padding-inline: 16px; padding-block: 28px 56px; }}
.top {{ display: flex; flex-wrap: wrap; gap: 8px 32px; align-items: end; justify-content: space-between;
        border-bottom: 1px solid var(--line); padding-bottom: 16px; }}
h1 {{ font: 400 clamp(26px, 3.4vw, 38px)/1.12 "Bungee Tint", "Barlow Condensed", sans-serif;
      letter-spacing: .01em; margin: 0; text-wrap: balance; color: var(--display); }}
.meta {{ margin: 6px 0 0; color: var(--muted); }}
.stats {{ display: flex; gap: 24px; margin: 0; font-variant-numeric: tabular-nums; }}
.stats div {{ display: grid; }}
.stats dt {{ font: 600 11px/1.2 "IBM Plex Sans", sans-serif; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }}
.stats dd {{ margin: 0; font: 600 26px/1.1 "Barlow Condensed", sans-serif; }}
.view-toggle {{ display: flex; align-items: center; gap: 12px; margin: 16px 0 2px; flex-wrap: wrap; }}
.flip-btn {{
  font: 600 13px/1 "Nunito", system-ui, sans-serif; color: var(--ground); background: var(--ink); cursor: pointer;
  border: 0; border-radius: 999px; padding: 9px 16px; display: inline-flex; align-items: center; gap: 8px;
}}
.flip-btn:hover {{ background: var(--accent); }}
.flip-btn:focus-visible {{ outline: 2px solid var(--focus); outline-offset: 2px; }}
.flip-btn .flip-icon {{ font-size: 15px; display: inline-block; transition: transform .5s ease; }}
body.rear .flip-btn {{ background: var(--accent); color: #221008; }}
body.rear .flip-btn .flip-icon {{ transform: rotate(180deg); }}
.view-state {{ font-size: 12.5px; color: var(--muted); }}
.legend {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 12px 0 6px; }}
.chip {{
  font: 500 12.5px/1 "IBM Plex Sans", sans-serif; color: var(--ink); cursor: pointer;
  background: transparent; border: 1px solid var(--line); border-radius: 999px; padding: 7px 11px 7px 9px;
  display: inline-flex; align-items: center; gap: 7px;
}}
.chip::before {{ content: ""; width: 10px; height: 10px; border-radius: 2px; background: var(--c); }}
.chip.pending-chip::before {{ background: transparent; border: 1px dashed var(--muted); }}
.chip.norm-chip::before {{ background: repeating-linear-gradient(-45deg, var(--norm) 0 3px, var(--norm-2) 3px 6px); }}
.chip.norm-chip.open::before {{ background: transparent; border: 1px dashed var(--muted); }}
.chip-sep {{ width: 1px; background: var(--line); margin: 2px 6px; }}
.chip[aria-pressed="true"] {{ border-color: var(--c); box-shadow: inset 0 0 0 1px var(--c); }}
.chip:focus-visible {{ outline: 2px solid var(--focus); outline-offset: 2px; }}
.hint {{ color: var(--muted); font-size: 12.5px; margin: 0 0 20px; }}
.racks {{ display: grid; gap: 0; }}
.racks > .rack-group + .rack-group {{ margin-top: 56px; }}
.sec-head {{ cursor: pointer; user-select: none; }}
/* A collapsed section is just its heading: no leftover gaps. */
.rack-group:has(> .sec-head[aria-expanded="false"]),
.gear-rack:has(> .sec-head[aria-expanded="false"]),
.ghost:has(> .sec-head[aria-expanded="false"]),
.cables:has(> .sec-head[aria-expanded="false"]),
.midi-list:has(> .sec-head[aria-expanded="false"]),
.todos:has(> .sec-head[aria-expanded="false"]),
.notes:has(> .sec-head[aria-expanded="false"]),
.crimes:has(> .sec-head[aria-expanded="false"]),
.solder:has(> .sec-head[aria-expanded="false"]) {{ margin-top: 14px; padding-top: 0; }}
.sec-head[aria-expanded="false"] {{ margin-bottom: 0; }}
.racks > .rack-group + .rack-group:has(> .sec-head[aria-expanded="false"]) {{ margin-top: 10px; }}
.sec-head::before {{ content: "▾"; display: inline-block; width: 14px; font-size: .75em; color: var(--muted);
  transition: transform .15s; }}
.sec-head[aria-expanded="false"]::before {{ transform: rotate(-90deg); }}
.sec-head:hover {{ color: var(--ink); }}
.sec-head:focus-visible {{ outline: 2px solid var(--focus); outline-offset: 3px; }}
.rack-name {{ color: var(--accent); margin: 0 0 12px; font: 700 15px/1 "Barlow Condensed", sans-serif; letter-spacing: .12em; text-transform: uppercase;
  color: var(--muted); display: flex; align-items: center; gap: 12px; }}
.rack-name::after {{ content: ""; flex: 1; height: 1px; background: var(--line); }}
.rack {{ display: grid; gap: 0; }}
.rack .bay {{ padding: 14px 0 16px; border-bottom: 2px solid var(--line); }}
.rack .bay:first-child {{ padding-top: 4px; }}
.rack .bay:last-child {{ border-bottom: 0; }}
.bay {{ display: grid; grid-template-columns: 72px minmax(0, 1fr); gap: 4px 12px; align-items: stretch; }}
.bay-note-wrap {{ grid-column: 2; }}
.bay-note-wrap summary {{
  display: flex; align-items: center; gap: 6px; cursor: pointer; list-style: none; width: 100%;
  font: 600 10.5px/1 "Nunito", system-ui, sans-serif; letter-spacing: .06em; text-transform: uppercase;
  color: var(--muted); padding: 6px 8px; border: 1px dashed transparent; border-radius: 3px;
}}
.bay-note-wrap summary:hover {{ border-color: var(--panel-edge); color: var(--ink); }}
.bay-note-wrap summary::-webkit-details-marker {{ display: none; }}
.bay-note-wrap summary::before {{ content: "▸"; font-size: 11px; transition: transform .15s; }}
.bay-note-wrap[open] summary::before {{ transform: rotate(90deg); }}
.bay-note-wrap summary:focus-visible {{ outline: 2px solid var(--focus); outline-offset: 2px; }}
.bay-note-wrap.has-text summary {{ color: var(--accent); }}
.bay-note-wrap.has-text summary::after {{ content: "•"; }}
.bay-note {{
  width: 100%; margin-top: 4px; resize: vertical; min-height: 30px; border: 1px dashed var(--panel-edge);
  border-radius: 3px; background: transparent; color: var(--ink); padding: 4px 7px;
  font: 400 12px/1.4 "Nunito", system-ui, sans-serif;
}}
.bay-note::placeholder {{ color: var(--muted); opacity: .7; }}
.bay-note:focus-visible {{ outline: 2px solid var(--focus); outline-offset: 1px; border-style: solid; }}
.bay-note.saving {{ border-color: var(--plugged); }}
.bay-note:placeholder-shown {{ min-height: 26px; }}
.bay-head {{ display: flex; flex-direction: column; justify-content: center; }}
.bay-head h2 {{ margin: 0; color: var(--ink); font: 700 26px/1 "Barlow Condensed", sans-serif; text-transform: uppercase; letter-spacing: .02em; }}
.bay-head p {{ margin: 1px 0 0; font-size: 11px; color: var(--muted); line-height: 1.3; white-space: nowrap; }}
.bay-head h2 + p {{ margin-top: 4px; }}
.bay-head h2.named {{ font-size: 15px; line-height: 1.05; overflow-wrap: anywhere; }}
.bay-head b {{ font-weight: 600; color: var(--ink); }}
.scroll {{ overflow-x: auto; perspective: 1400px; }}
.panel {{
  transform-style: preserve-3d; transition: transform .55s cubic-bezier(.4, 0, .2, 1);
  min-width: 980px; display: grid; column-gap: 3px; row-gap: 3px;
  background: var(--panel); border: 1px solid var(--panel-edge); border-radius: 3px;
  padding: 6px 10px 8px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.06);
}}
body.rear .panel {{ transform: rotateY(180deg); }}
.panel > * {{ transition: transform .55s cubic-bezier(.4, 0, .2, 1); }}
body.rear .panel > * {{ transform: rotateY(180deg); }}
.num {{ font: 500 9.5px/1 "IBM Plex Mono", monospace; color: var(--engrave); text-align: center; padding: 2px 0 1px;
        font-variant-numeric: tabular-nums; }}
.tape {{
  position: relative; min-height: 36px; display: flex; align-items: center; justify-content: center;
  background: var(--tape); color: var(--tape-ink); border-radius: 1px;
  box-shadow: inset 0 3px 0 var(--c, transparent);
  padding: 5px 3px 3px; text-align: center; overflow: hidden;
  font: 500 10.5px/1.12 "IBM Plex Mono", "Andale Mono", monospace; letter-spacing: -.01em;
  transition: opacity .15s;
}}
.tape span {{ overflow-wrap: anywhere; }}
.tape.pending em {{ font: italic 500 10px/1.15 "IBM Plex Sans", sans-serif; color: var(--pc, var(--engrave)); letter-spacing: 0; }}
.tape.blank {{ background: transparent; box-shadow: inset 0 0 0 1px var(--panel-edge); }}
.tape.blank.pending {{ box-shadow: none; border: 1px dashed #6b7278; }}
.tape.has-info {{ padding-left: 16px; }}
.tape.has-flag {{ padding-right: 16px; }}
.info-mark {{
  position: absolute; top: 4px; left: 3px; width: 13px; height: 13px; border-radius: 50%;
  background: #6b7278; color: #f3f4f5; font: 700 9px/13px "Nunito", sans-serif; font-style: normal; text-align: center;
}}
.flag {{
  position: absolute; top: 4px; right: 3px; width: 15px; height: 15px; border-radius: 50%; border: 0; padding: 0; cursor: pointer;
  background: #f0b429; color: #1a1400; font: 700 9.5px/15px "IBM Plex Sans", sans-serif; font-style: normal; text-align: center;
}}
.flag:hover {{ filter: brightness(1.1); }}
.flag:focus-visible {{ outline: 2px solid var(--focus); outline-offset: 2px; }}
.pop {{
  position: fixed; inset: auto; margin: 0; max-width: min(280px, calc(100vw - 32px));
  background: var(--ground); color: var(--ink); border: 1px solid var(--line); border-left: 3px solid #f0b429;
  border-radius: 3px; padding: 10px 12px; box-shadow: 0 8px 24px rgba(0,0,0,.25);
  font: 400 13px/1.45 "IBM Plex Sans", system-ui, sans-serif; text-align: left;
}}
.pop b {{ display: block; font: 600 11px/1.3 "IBM Plex Sans", sans-serif; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); margin-bottom: 4px; }}
.jack {{
  justify-self: center; width: 20px; height: 20px; border-radius: 50%; position: relative;
  background: radial-gradient(circle, var(--jack) 0 36%, #2a2e32 38% 58%, var(--jack-ring) 60% 100%);
  box-shadow: 0 0 0 2px var(--c, transparent);
  transition: opacity .15s;
}}
.jack.drawn {{ width: 30px; height: 30px; background: none; }}
.jack.drawn.ethernet {{ width: 30px; height: 28px; border-radius: 2px; }}
.jack.drawn.switch {{ width: 22px; height: 33px; border-radius: 3px; }}
.jack.drawn svg {{ display: block; width: 100%; height: 100%; }}
.jack[data-cat="spare"] {{ box-shadow: none; opacity: .45; }}
button.jack {{ border: 0; padding: 0; cursor: pointer; font: inherit; }}
.jack.wire:hover {{ filter: brightness(1.35); }}
.jack.wire:focus-visible {{ outline: 2px solid var(--focus); outline-offset: 2px; }}
.jack.wire[aria-pressed="true"]:not(.drawn) {{ background: radial-gradient(circle, #eaf7ef 0 30%, var(--plugged) 34% 100%); }}
.jack.wire.drawn[aria-pressed="true"] {{ box-shadow: 0 0 0 2px var(--plugged); }}
.jack.wire[aria-pressed="true"]::after {{
  content: "✓"; position: absolute; right: -5px; top: -6px; width: 11px; height: 11px; border-radius: 50%;
  background: var(--plugged); color: #fff; font: 700 8px/11px "IBM Plex Sans", sans-serif; text-align: center;
}}
.wire-progress {{ margin: 14px 0 4px; display: grid; gap: 6px; }}
.wp-label {{ font-size: 13px; color: var(--muted); font-variant-numeric: tabular-nums; }}
.wp-label b {{ font: 700 22px/1 "Barlow Condensed", sans-serif; color: var(--ink); margin-right: 4px; }}
.wp-track {{ height: 10px; border-radius: 999px; background: var(--line); overflow: hidden; }}
.wp-fill {{ height: 100%; width: 0; background: var(--plugged); border-radius: 999px; transition: width .3s ease; }}
@media (prefers-reduced-motion: reduce) {{ .wp-fill {{ transition: none; }} }}
.idle-pill {{ display: inline-block; font-size: 10.5px; font-weight: 600; padding: 1px 7px; border-radius: 999px;
  border: 1px dashed var(--muted); color: var(--muted); margin-bottom: 2px; }}
.panel.idle .tape, .tape.idle {{ opacity: .45; }}
.stats dd small {{ font-size: 14px; color: var(--muted); font-weight: 500; }}
.norm {{
  height: 16px; display: flex; align-items: center; justify-content: center; border-radius: 2px;
  font: 600 8.5px/1 "IBM Plex Sans", sans-serif; letter-spacing: .1em; text-transform: uppercase; white-space: nowrap; overflow: hidden;
  transition: opacity .15s;
}}
.norm.on {{
  color: #e2e5e7; background: repeating-linear-gradient(-45deg, var(--norm) 0 5px, var(--norm-2) 5px 10px);
}}
.norm.on span {{ background: var(--norm); padding: 1px 4px; border-radius: 2px; }}
.norm.off {{ height: 8px; align-self: center; border: 1px dashed #3f454a; }}
.jack[data-norm="normalled"] {{ box-shadow: 0 0 0 2px var(--c), 0 0 0 3.5px var(--norm-2); }}
.split {{ justify-self: center; width: 1px; background: var(--panel-edge); margin-block: 2px; }}
body.focusing .tape, body.focusing .jack, body.focusing .norm {{ opacity: .15; }}
body.focusing .hit {{ opacity: 1; }}
.moves {{ margin-top: 64px; max-width: 980px; }}
.ghost {{ margin-top: 56px; }}
.ghost h2 {{ color: var(--accent); font: 700 20px/1 "Barlow Condensed", sans-serif; text-transform: uppercase;
  letter-spacing: .03em; margin: 0 0 8px; }}
.ghost .lead {{ margin: 0 0 14px; color: var(--muted); max-width: 68ch; }}
.gj-tabs {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 10px; }}
.gj-tab {{
  font: 600 12px/1 "Nunito", system-ui, sans-serif; color: var(--ink); background: transparent; cursor: pointer;
  border: 1px solid var(--line); border-radius: 999px; padding: 7px 13px;
}}
.gj-tab[aria-pressed="true"] {{ background: var(--ink); color: var(--ground); border-color: var(--ink); }}
.gj-tab:focus-visible {{ outline: 2px solid var(--focus); outline-offset: 2px; }}
.gj-panel {{
  display: grid; gap: 18px; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  background: var(--panel); border: 1px solid var(--panel-edge); border-radius: 4px; padding: 14px 16px 16px;
}}
.gj-group h3 {{ margin: 0 0 8px; font: 700 12px/1 "Barlow Condensed", sans-serif; letter-spacing: .12em;
  text-transform: uppercase; color: var(--engrave); }}
.gj-wiring {{ margin: -3px 0 10px; font: 400 10px/1.4 "IBM Plex Mono", monospace; color: var(--engrave); opacity: .85; }}
.gj-kind {{
  justify-self: start; font: 600 9px/1.5 "Nunito", sans-serif; letter-spacing: .03em; color: var(--engrave);
  border: 1px solid var(--panel-edge); border-radius: 999px; padding: 0 7px; white-space: nowrap;
}}
.gj-group ul {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 7px; }}
.gj-group li {{ display: grid; grid-template-columns: auto 1fr; gap: 3px 10px; align-items: center; color: #e4e6e3; }}
.gj-group li > b, .gj-group li > .gj-kind, .gj-group li > small {{ grid-column: 2; }}
.gj-jacks {{ display: flex; gap: 3px; grid-row: span 3; align-self: center; }}
.gj-jacks i {{
  position: relative; width: 14px; height: 14px; border-radius: 50%;
  background: radial-gradient(circle, var(--jack) 0 36%, #2a2e32 38% 58%, var(--jack-ring) 60% 100%);
  box-shadow: 0 0 0 1.5px var(--c, var(--spare));
}}
.gj-group b {{ font: 600 12.5px/1.2 "IBM Plex Mono", monospace; align-self: end; }}
.gj-group small {{ font-size: 10.5px; color: var(--engrave); align-self: start; }}
.gj-group li[title$="not patched"] {{ opacity: .6; }}
.gj-group li.connected .gj-jacks i {{
  background: radial-gradient(circle, #eaf7ef 0 30%, var(--plugged) 34% 100%); box-shadow: 0 0 0 1.5px var(--plugged);
}}
.gj-group li.connected .gj-jacks i::after {{
  content: "✓"; position: absolute; right: -4px; top: -5px; width: 10px; height: 10px; border-radius: 50%;
  background: var(--plugged); color: #fff; font: 700 7px/10px "Nunito", sans-serif; text-align: center;
}}
.solder {{ margin-top: 56px; max-width: 760px; --pin-hot: #e8836a; --pin-cold: #79c2e4; --pin-gnd: #c9ccc6; }}
.solder h2 {{ color: var(--accent); font: 700 20px/1 "Barlow Condensed", sans-serif; text-transform: uppercase;
  letter-spacing: .03em; margin: 0 0 6px; }}
.solder .lead {{ margin: 0 0 10px; color: var(--muted); max-width: 68ch; }}
.pin-key {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 14px; }}
.pk {{ font: 600 11.5px/1 "Nunito", sans-serif; padding: 5px 10px; border-radius: 999px; color: #10151a; }}
.pk.hot {{ background: var(--pin-hot); }}
.pk.cold {{ background: var(--pin-cold); }}
.pk.gnd {{ background: var(--pin-gnd); }}
.solder figure {{ margin: 0 0 18px; }}
.solder svg {{ width: 100%; max-width: 680px; height: auto; color: var(--ink); }}
.solder figcaption {{ margin-top: 4px; font-size: 12px; color: var(--muted); }}
.solder-map {{ border-collapse: collapse; width: 100%; max-width: 520px; font-size: 13.5px; margin-bottom: 16px; }}
.solder-map th {{ text-align: left; font: 600 11px/1.2 "Nunito", sans-serif; letter-spacing: .08em;
  text-transform: uppercase; color: var(--muted); padding: 6px 10px; border-bottom: 1px solid var(--line); }}
.solder-map td {{ padding: 7px 10px; border-bottom: 1px solid var(--line); }}
.solder-notes {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 9px; max-width: 68ch; }}
.solder-notes li {{ color: var(--muted); font-size: 13.5px; padding-left: 14px; position: relative; }}
.solder-notes li::before {{ content: "–"; position: absolute; left: 0; color: var(--accent); }}
.solder-notes b {{ color: var(--ink); }}
.crimes {{ margin-top: 56px; max-width: 760px; }}
.crimes h2 {{ color: var(--accent); font: 700 20px/1 "Barlow Condensed", sans-serif; text-transform: uppercase;
  letter-spacing: .03em; margin: 0 0 6px; }}
.crimes .lead {{ margin: 0 0 12px; color: var(--muted); max-width: 68ch; }}
.crime-list {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }}
.crime-list li {{ display: grid; grid-template-columns: 170px 1fr; gap: 12px; padding-bottom: 10px;
  border-bottom: 1px solid var(--line); }}
.crime-list b {{ font: 600 12.5px/1.4 "IBM Plex Mono", monospace; color: var(--ink); }}
.crime-list span {{ color: var(--muted); font-size: 13.5px; }}
@media (max-width: 640px) {{ .crime-list li {{ grid-template-columns: 1fr; gap: 2px; }} }}
.todos {{ margin-top: 56px; max-width: 680px; }}
.todos h2 {{ color: var(--accent); font: 700 20px/1 "Barlow Condensed", sans-serif; text-transform: uppercase;
  letter-spacing: .03em; margin: 0 0 6px; }}
.todo-list {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }}
.todo-list li {{ display: grid; grid-template-columns: 20px 1fr; gap: 10px; align-items: start; }}
.todo-list label {{ cursor: pointer; font-size: 14px; }}
.todo-list li.done label {{ text-decoration: line-through; opacity: .55; }}
.todo-check {{ width: 17px; height: 17px; accent-color: var(--plugged); cursor: pointer; margin: 2px 0 0; }}
.todo-check:focus-visible {{ outline: 2px solid var(--focus); outline-offset: 2px; }}
.todo-note {{ margin-top: 14px; min-height: 66px; }}
.cables {{ margin-top: 56px; }}
.cables h2 {{ color: var(--accent); font: 700 20px/1 "Barlow Condensed", sans-serif; text-transform: uppercase; letter-spacing: .03em; margin: 0 0 8px; }}
.cables .lead {{ margin: 0 0 4px; color: var(--muted); max-width: 68ch; }}
.cables .lead b {{ color: var(--ink); }}
.cable-bars {{ display: grid; gap: 12px 28px; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  margin: 14px 0 20px; max-width: 900px; }}
.cables .wire-progress {{ margin: 0; gap: 4px; }}
.cables .wp-label {{ font-size: 12.5px; }}
.cables .wp-label b {{ font-size: 18px; }}
.cables .wire-progress.total .wp-label b {{ color: var(--plugged); }}
.room-grid {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); }}
.room-card {{ border: 1px solid var(--line); border-radius: 4px; padding: 10px 12px 12px; background: var(--ground);
  min-width: 0; overflow: hidden; }}
.room-card header {{ display: flex; align-items: baseline; justify-content: space-between; gap: 8px;
  border-bottom: 1px solid var(--line); padding-bottom: 6px; margin-bottom: 6px; }}
.room-card h3 {{ margin: 0; font: 600 15px/1.2 "Barlow Condensed", sans-serif; letter-spacing: .04em; text-transform: uppercase; }}
.room-count {{ font-size: 12px; color: var(--muted); font-variant-numeric: tabular-nums; }}
.room-card.done {{ border-color: var(--plugged); }}
.room-card.done .room-count {{ color: var(--plugged); font-weight: 600; }}
.room-card table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
.room-card thead th {{ font: 600 9px/1.25 "IBM Plex Sans", sans-serif; letter-spacing: .04em; text-transform: uppercase;
  color: var(--muted); padding: 0 4px 5px; text-align: center; width: 58px; line-height: 1.25; }}
.room-card .na {{ color: var(--muted); opacity: .6; }}
.room-card tbody th {{ text-align: left; font-weight: 400; padding: 6px 8px 6px 0; border-top: 1px solid var(--line); }}
.room-card tbody th .row-label {{ display: flex; align-items: baseline; gap: 6px; min-width: 0; }}
.room-card tbody th .row-label b {{ flex: 1; }}
.room-card tbody th .kind {{ flex: none; width: 52px; text-align: center; }}
.room-card tbody td {{ text-align: center; padding: 6px 5px; border-top: 1px solid var(--line); }}
.room-card tbody th b {{ font-weight: 600; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.room-card tbody th small {{ display: block; color: var(--muted); font-size: 10.5px; font-variant-numeric: tabular-nums; }}
.room-card tbody th small.ends {{ font-style: italic; }}
.kind {{ font: 600 9px/1.6 "IBM Plex Sans", sans-serif; letter-spacing: .03em; text-transform: uppercase;
  padding: 1px 4px; border-radius: 999px; box-sizing: border-box; }}
.kind.xlr {{ background: #9a73e0; color: #fff; }}
.kind.cat5 {{ background: #4fb1dc; color: #10222b; }}
.kind.speaker {{ background: #e3a02f; color: #221802; }}
.kind.7-pin, .kind[class*="pin"] {{ background: #ec6a55; color: #2a0d08; }}
.cable-check {{ width: 16px; height: 16px; accent-color: var(--plugged); cursor: pointer; margin: 0; }}
.cable-check:focus-visible {{ outline: 2px solid var(--focus); outline-offset: 2px; }}
.room-card tr.done th b, .room-card tr.done th small {{ text-decoration: line-through; opacity: .6; }}
.room-note {{
  width: 100%; margin-top: 8px; resize: vertical; min-height: 40px; border: 1px dashed var(--line); border-radius: 3px;
  background: transparent; color: var(--ink); padding: 5px 6px; font: 400 12px/1.4 "IBM Plex Sans", system-ui, sans-serif;
}}
.room-note::placeholder {{ color: var(--muted); }}
.room-note:focus-visible {{ outline: 2px solid var(--focus); outline-offset: 1px; border-style: solid; }}
.room-note.saving {{ border-color: var(--plugged); }}
.midi-list {{ margin-top: 48px; max-width: 820px; }}
.midi-list h2 {{ color: var(--accent); font: 700 20px/1 "Barlow Condensed", sans-serif; text-transform: uppercase; letter-spacing: .03em; margin: 0 0 8px; }}
.midi-list table {{ width: 100%; min-width: 560px; border-collapse: collapse; font-size: 13.5px; }}
.midi-list th {{ text-align: left; font: 600 11px/1.2 "IBM Plex Sans", sans-serif; letter-spacing: .08em; text-transform: uppercase;
  color: var(--muted); padding: 8px 10px; border-bottom: 1px solid var(--line); }}
.midi-list td {{ padding: 7px 10px; vertical-align: top; }}
.midi-list tr.first td {{ border-top: 1px solid var(--line); }}
.midi-list td.inst small {{ display: block; color: var(--muted); font-size: 11.5px; margin-top: 2px; }}
.midi-list td.done-cell {{ width: 34px; text-align: center; }}
.midi-list label {{ cursor: pointer; }}
.midi-list tr.done td:not(.done-cell):not(.inst) {{ opacity: .45; }}
.midi-list tr.done label {{ text-decoration: line-through; }}
.midi-check {{ width: 18px; height: 18px; accent-color: var(--ink); cursor: pointer; margin: 1px 0 0; }}
.midi-check:focus-visible {{ outline: 2px solid var(--focus); outline-offset: 2px; }}
.need {{ font-size: 12px; padding: 2px 8px; border-radius: 999px; }}
.need.req {{ background: var(--ink); color: var(--ground); }}
.need.low {{ border: 1px dashed var(--muted); color: var(--muted); }}
.midi-list .tbd {{ color: var(--muted); }}
.moves summary {{ display: flex; align-items: baseline; gap: 12px; cursor: pointer; list-style: none; padding: 8px 0;
  border-top: 1px solid var(--line); }}
.moves summary::-webkit-details-marker {{ display: none; }}
.moves summary::before {{ content: "▸"; color: var(--muted); font-size: 12px; transition: transform .15s; }}
.moves[open] summary::before {{ transform: rotate(90deg); }}
.moves summary:focus-visible {{ outline: 2px solid var(--focus); outline-offset: 2px; }}
.moves summary h2 {{ margin: 0; }}
.moves .archived {{ font-size: 12px; color: var(--muted); }}
.moves h2 {{ color: var(--accent); font: 700 20px/1 "Barlow Condensed", sans-serif; text-transform: uppercase; letter-spacing: .03em; margin: 0 0 8px; }}
.moves .lead {{ margin: 0 0 14px; color: var(--muted); max-width: 68ch; }}
.moves .lead b {{ color: var(--ink); font-variant-numeric: tabular-nums; }}
.moves table {{ width: 100%; min-width: 620px; border-collapse: collapse; font-size: 13.5px; }}
.moves th {{ text-align: left; font: 600 11px/1.2 "IBM Plex Sans", sans-serif; letter-spacing: .08em; text-transform: uppercase; color: var(--muted);
  padding: 8px 10px; border-bottom: 1px solid var(--line); }}
.moves td {{ padding: 9px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }}
.moves td.done-cell {{ width: 34px; text-align: center; }}
.move-check {{ width: 18px; height: 18px; accent-color: var(--ink); cursor: pointer; margin: 1px 0 0; }}
.move-check:focus-visible {{ outline: 2px solid var(--focus); outline-offset: 2px; }}
.moves .nothing {{ color: var(--muted); }}
.moves tr.done td:not(.done-cell) {{ opacity: .45; }}
.moves tr.done td:nth-child(2) b {{ text-decoration: line-through; }}
.moves label {{ cursor: pointer; }}
.progress {{ margin: 0 0 12px; font-size: 13px; color: var(--muted); font-variant-numeric: tabular-nums; }}
.progress b {{ color: var(--ink); }}
.visually-hidden {{ position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }}
.moves td small {{ display: block; color: var(--muted); font-size: 11.5px; margin-top: 2px; }}
.moves tr.stays td:nth-child(2) {{ color: var(--muted); }}
.flip {{ display: inline-block; margin: 0 6px 4px 0; padding: 2px 8px; border-radius: 999px; font-size: 12px; font-variant-numeric: tabular-nums; }}
.flip.on {{ background: repeating-linear-gradient(-45deg, var(--norm) 0 5px, var(--norm-2) 5px 10px); color: #e2e5e7; }}
.flip.off {{ border: 1px dashed var(--muted); }}
.flip.check {{ border: 1px solid #b8923a; color: var(--ink); }}
.flip.none {{ color: var(--muted); padding-left: 0; }}
.gear {{ margin-top: 56px; display: grid; gap: 48px; }}
.gear:has(.sec-head[aria-expanded="false"]) {{ margin-top: 14px; }}
.elevation {{
  --u: 38px; display: grid; row-gap: 2px; max-width: 760px;
  background: var(--panel); border: 1px solid var(--panel-edge); border-radius: 3px; padding: 8px 10px;
}}
.ru {{ display: grid; grid-template-columns: 58px minmax(0, 1fr); gap: 10px; }}
.ru-num {{ font: 500 10px/1 "IBM Plex Mono", monospace; color: var(--engrave); align-self: center; font-variant-numeric: tabular-nums; }}
.face {{
  background: #2a2e32; border-radius: 2px; padding: 0 10px; box-shadow: inset 3px 0 0 var(--c, var(--spare));
  display: flex; align-items: center; gap: 12px; color: #e4e6e3; min-width: 0; overflow: hidden; white-space: nowrap;
}}
.face .patched {{ margin-left: auto; overflow: hidden; text-overflow: ellipsis; }}
.face .patched a {{ color: inherit; }}
.ru.empty .face {{ background: transparent; box-shadow: none; border: 1px dashed #4a5157; color: var(--engrave); }}
.face-main {{ display: flex; flex-wrap: nowrap; align-items: center; gap: 10px; flex-shrink: 0; }}
.face-main b {{ font: 600 14px/1.2 "Barlow Condensed", sans-serif; letter-spacing: .04em; text-transform: uppercase; }}
.badge {{ font: 500 11px/1.2 "IBM Plex Sans", sans-serif; padding: 2px 7px; border-radius: 999px; }}
.badge.move {{ border: 1px dashed #8a9197; color: #c3c8cb; }}
.badge.plan {{ background: #34404d; color: #cfe0f2; }}
.badge.q {{ background: #4a3d17; color: #f6d77a; }}
.patched {{ margin: 0; font: 400 11px/1.3 "IBM Plex Mono", monospace; color: var(--engrave); }}
.patched.none {{ opacity: .7; }}
.slots {{ display: grid; grid-template-columns: repeat(10, minmax(0, 1fr)); gap: 3px; }}
.slot {{ background: var(--tape); color: var(--tape-ink); font: 500 10px/1 "IBM Plex Mono", monospace; text-align: center; padding: 4px 0; border-radius: 1px; }}
.slot.tbd {{ background: transparent; color: var(--engrave); border: 1px dashed #4a5157; }}
.notes {{ margin-top: 36px; border-top: 1px solid var(--line); padding-top: 16px; max-width: 760px; }}
.notes h2 {{ color: var(--accent); font: 700 20px/1 "Barlow Condensed", sans-serif; text-transform: uppercase; letter-spacing: .03em; margin: 0 0 10px; }}
.notes ul {{ margin: 0; padding: 0; list-style: none; display: grid; gap: 8px; }}
.notes li {{ display: grid; grid-template-columns: 170px 1fr; gap: 12px; }}
.notes a {{ color: var(--ink); font-weight: 600; text-decoration-color: var(--line); }}
.notes span {{ color: var(--muted); }}
.notes .q-general {{ color: var(--ink); font-weight: 600; }}
@media (max-width: 640px) {{
  .bay {{ grid-template-columns: 1fr; gap: 4px; }}
  .bay-head {{ flex-direction: row; align-items: baseline; gap: 10px; }}
  .notes li {{ grid-template-columns: 1fr; gap: 0; }}
}}
@media (prefers-reduced-motion: reduce) {{ .tape, .jack, .norm, .panel, .panel > *, .flip-icon {{ transition: none; }} }}
@page {{ size: letter landscape; margin: 0.4in; }}
@media print {{
  :root, :root[data-theme="dark"] {{
    --ground: #fff; --ink: #111; --muted: #555; --line: #bbb;
    --panel: #fff; --panel-edge: #999; --engrave: #444; --tape: #fff; --tape-ink: #111; --spare: #aaa;
    --norm: #cfcfcf; --norm-2: #e6e6e6;
  }}
  * {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  body {{ font-size: 11px; }}
  .wrap {{ max-width: none; padding: 0; }}
  .hint, .flag, .pop, .stats, .chip-sep, .wire-progress, .view-toggle {{ display: none !important; }}
  .sec-body {{ display: block !important; }}
  .sec-head::before {{ display: none; }}
  h1 {{ font-size: 19px; color: #111; }}
  .rack-name, .cables h2, .midi-list h2, .moves h2, .notes h2 {{ color: #111; }}
  .meta {{ margin-top: 2px; font-size: 9.5px; }}
  .top {{ padding-bottom: 4px; }}
  .legend {{ margin: 4px 0 6px; gap: 3px; }}
  .chip {{ font-size: 8.5px; padding: 2px 6px 2px 4px; }}
  .racks {{ gap: 0; }}
  .rack {{ gap: 0; }}
  .rack .bay {{ padding: 5px 0 6px; border-bottom: 1px solid #bbb; }}
  .rack-name {{ margin: 0 0 6px; font-size: 13px; }}
  .bay {{ grid-template-columns: 44px minmax(0, 1fr); gap: 3px 6px; break-inside: avoid; }}
  .bay-note {{ min-height: 16px; font-size: 8px; padding: 2px 4px; }}
  .bay-note-wrap summary {{ display: none; }}
  .bay-note-wrap .bay-note {{ display: block; }}
  .bay-head h2 {{ font-size: 18px; }}
  .bay-head h2.named {{ font-size: 10px; }}
  .bay-head p {{ font-size: 8.5px; }}
  .scroll {{ overflow: visible; }}
  .panel {{ min-width: 0; padding: 3px 5px 4px; row-gap: 2px; column-gap: 2px; box-shadow: none; }}
  .num {{ font-size: 7.5px; padding: 0; }}
  .tape {{ min-height: 21px; font-size: 8.5px; padding: 3px 2px 2px; border: 1px solid #333; }}
  .tape.blank {{ border: 0; box-shadow: inset 0 0 0 1px #ccc; }}
  .tape.blank.pending {{ box-shadow: none; border: 1px dashed #888; }}
  .jack {{ width: 11px; height: 11px; background: radial-gradient(circle, #555 0 28%, #fff 32%); border: 1.5px solid #333; }}
  .jack[data-cat="spare"] {{ border-color: #bbb; background: #fff; opacity: 1; }}
  .jack.drawn {{ width: 20px; height: 20px; border: 0; background: none; }}
  .jack.drawn.switch {{ width: 14px; height: 21px; }}
  .jack.drawn.ethernet {{ width: 20px; height: 18px; }}
  .norm {{ height: 9px; font-size: 6.5px; }}
  .norm.on {{ color: #111; }}
  .norm.on span {{ background: #fff; }}
  .norm.off {{ height: 5px; border-color: #bbb; }}
  .racks > .rack-group:first-child .bay:nth-child(5) {{ break-after: page; }}
  .racks > .rack-group:nth-child(2) {{ break-before: page; }}
  .racks > .rack-group + .rack-group {{ margin-top: 14px; }}
  .racks > .rack-group:nth-child(2) {{ margin-top: 0; }}
  .moves {{ display: none; }}
  .gear {{ break-before: page; margin-top: 0; }}
  .moves table {{ min-width: 0; font-size: 10px; }}
  .moves td, .moves th {{ padding: 3px 8px; }}
  .moves .lead {{ max-width: none; font-size: 10px; margin-bottom: 6px; }}
  .moves td small {{ margin-top: 0; font-size: 9px; }}
  .flip {{ margin: 0 4px 2px 0; padding: 1px 6px; font-size: 9.5px; }}
  .move-check {{ width: 13px; height: 13px; }}
  .flip.on {{ background: #e6e6e6; color: #111; }}
  .gear {{ gap: 0; }}
  .elevation {{ --u: 22px; max-width: none; padding: 4px 6px; row-gap: 1px; }}
  .face {{ background: #f3f3f3; color: #111; padding: 0 8px; gap: 10px; }}
  .face-main b {{ font-size: 12px; }}
  .badge {{ font-size: 9px; padding: 1px 5px; }}
  .badge.move {{ color: #333; border-color: #777; }}
  .badge.plan {{ background: #e3ecf5; color: #123; }}
  .badge.q {{ background: #fbefc8; color: #3a2d00; }}
  .patched {{ font-size: 9px; color: #444; }}
  .ghost {{ break-before: page; margin-top: 0; }}
  .gj-panel {{ background: #fff; border-color: #999; }}
  .gj-tabs {{ display: none; }}
  .gj-group li, .gj-group small {{ color: #111; }}
  .gj-jacks i {{ background: #fff; border: 1.2px solid #333; box-shadow: none; }}
  .solder {{ break-before: page; margin-top: 0; max-width: none; }}
  .solder svg {{ max-width: 520px; }}
  .crimes {{ break-inside: avoid; margin-top: 18px; max-width: none; }}
  .crime-list li {{ grid-template-columns: 150px 1fr; }}
  .todos {{ break-inside: avoid; margin-top: 18px; }}
  .cables {{ break-before: page; margin-top: 0; }}
  .cables .lead {{ font-size: 10px; max-width: none; }}
  .room-grid {{ grid-template-columns: repeat(2, 1fr); gap: 8px; }}
  .room-card {{ break-inside: avoid; padding: 6px 8px 8px; }}
  .room-card tbody th b {{ font-size: 10px; }}
  .room-card tbody th .kind {{ width: 40px; font-size: 7.5px; }}
  .room-card tbody th small {{ font-size: 8px; }}
  .room-card thead th {{ font-size: 7px; width: 40px; padding: 0 2px 3px; }}
  .room-card tbody th, .room-card tbody td {{ padding: 2px 4px 2px 0; }}
  .room-note {{ min-height: 26px; margin-top: 5px; font-size: 8.5px; }}
  .cable-check {{ width: 12px; height: 12px; }}
  .midi-list {{ break-before: page; margin-top: 0; max-width: none; }}
  .midi-list h2 {{ font-size: 15px; margin-bottom: 4px; }}
  .midi-list table {{ min-width: 0; font-size: 10px; }}
  .midi-list td, .midi-list th {{ padding: 3px 8px; }}
  .midi-check {{ width: 13px; height: 13px; }}
  .need {{ font-size: 9px; padding: 1px 6px; }}
  .notes {{ break-inside: avoid; margin-top: 12px; padding-top: 8px; }}
  .notes li {{ grid-template-columns: 150px 1fr; }}
}}
</style>

<div class="wrap">
  <div class="top">
    <div>
      <h1>Studio Carquinez Patch Bay</h1>
      <p class="meta"><span id="view-name">Front view</span>, top of rack first. Left 16 ports: console buckets. Right 8: outboard, FX, monitoring. Generated {date.today().isoformat()} from <code>config.py</code>.</p>
    </div>
    <dl class="stats">
      <div><dt>Bays</dt><dd>{bay_count}</dd></div>
      <div><dt>Spare ports</dt><dd>{total_spare()}</dd></div>
      <div><dt>Rear plugged in</dt><dd><span id="wired-total">0</span><small id="wired-of"></small></dd></div>
    </dl>
  </div>
  <div class="wire-progress" id="wire-progress" hidden>
    <div class="wp-label"><b id="wp-pct">0%</b> plugged in (rear panels) <span id="wp-count"></span></div>
    <div class="wp-track" role="progressbar" aria-label="Rear panel jacks plugged in" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" id="wp-bar">
      <div class="wp-fill" id="wp-fill"></div>
    </div>
  </div>
  <div class="view-toggle">
    <button type="button" id="flip-view" class="flip-btn" aria-pressed="false">
      <span class="flip-icon" aria-hidden="true">⟲</span> Flip patch bay
    </button>
    <span class="view-state" id="view-state">Looking at the front</span>
  </div>
  <div class="legend" role="group" aria-label="Highlight a category">{render_legend()}</div>
  <p class="hint">Click a category to highlight it. Hover a label for its port range. The strip between the jack rows shows normalling: hatched = normalled (card standard, half-normal), dashed = not normalled (card turned; top and bottom are separate while the rear top jack is wired); <b>?</b> marks an open question.</p>
  <div class="racks">{render_racks()}</div>
  <div class="gear">{''.join(render_gear_rack(r) for r in gear_racks)}</div>
  <section class="notes">
    <h2>Open questions</h2>
    <ul>{render_notes()}</ul>
  </section>
  {render_ghost_rear()}
  {render_room_cables()}
  {render_solder()}
  {render_compromises()}
  {render_todos()}
  {render_midi_list()}
  {render_moves()}
</div>
<script>
(function () {{
  var btn = document.getElementById('flip-view');
  if (!btn) return;
  btn.addEventListener('click', function () {{
    var rear = !document.body.classList.contains('rear');
    document.body.classList.toggle('rear', rear);
    btn.setAttribute('aria-pressed', rear ? 'true' : 'false');
    document.getElementById('view-name').textContent = rear ? 'Rear view' : 'Front view';
    document.getElementById('view-state').textContent = rear
      ? 'Looking at the back - port 1 is on the right'
      : 'Looking at the front';
  }});
}})();
// Ghost rear panel: show one group at a time.
(function () {{
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.gj-tab'));
  if (!tabs.length) return;
  tabs.forEach(function (tab) {{
    tab.addEventListener('click', function () {{
      var show = tab.dataset.show;
      tabs.forEach(function (t) {{ t.setAttribute('aria-pressed', t === tab ? 'true' : 'false'); }});
      document.querySelectorAll('.gj-group').forEach(function (g) {{
        g.hidden = show !== 'all' && g.dataset.group !== show;
      }});
    }});
  }});
}})();
// Every section folds away; the choice is remembered in this browser.
(function () {{
  var KEY = 'patchbay-sections';
  function state() {{ try {{ return JSON.parse(localStorage.getItem(KEY) || '{{}}'); }} catch (e) {{ return {{}}; }} }}
  function remember(id, open) {{
    try {{
      var st = state();
      st[id] = open;
      localStorage.setItem(KEY, JSON.stringify(st));
    }} catch (e) {{}}
  }}
  var saved = state();
  var blocks = document.querySelectorAll('.rack-group, .gear-rack, .ghost, .cables, .midi-list, .solder, .crimes, .todos, .notes');
  Array.prototype.forEach.call(blocks, function (block, i) {{
    var head = block.querySelector('h2');
    if (!head) return;
    var id = block.id || head.textContent.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-') || 'sec-' + i;
    var body = document.createElement('div');
    body.className = 'sec-body';
    while (head.nextSibling) body.appendChild(head.nextSibling);
    block.appendChild(body);
    head.classList.add('sec-head');
    head.setAttribute('role', 'button');
    head.setAttribute('tabindex', '0');
    var open = id in saved ? !!saved[id] : true;
    function apply(next) {{
      open = next;
      body.hidden = !open;
      head.setAttribute('aria-expanded', open ? 'true' : 'false');
    }}
    apply(open);
    function toggle() {{
      apply(!open);
      remember(id, open);
    }}
    head.addEventListener('click', toggle);
    head.addEventListener('keydown', function (e) {{
      if (e.key === 'Enter' || e.key === ' ') {{
        e.preventDefault();
        toggle();
      }}
    }});
  }});
}})();
document.querySelectorAll('.chip').forEach(function (chip) {{
  chip.addEventListener('click', function () {{
    var on = chip.getAttribute('aria-pressed') !== 'true';
    document.querySelectorAll('.chip').forEach(function (c) {{ c.setAttribute('aria-pressed', 'false'); }});
    document.querySelectorAll('.hit').forEach(function (el) {{ el.classList.remove('hit'); }});
    document.body.classList.toggle('focusing', on);
    if (!on) return;
    chip.setAttribute('aria-pressed', 'true');
    var sel = chip.dataset.flag === 'unplugged' ? '.panel .wire[aria-pressed="false"]' : chip.dataset.flag ? '.panel [data-pending]' : chip.dataset.norm ? '.panel [data-norm="' + chip.dataset.norm + '"]' : '.panel [data-cat="' + chip.dataset.cat + '"]';
    document.querySelectorAll(sel).forEach(function (el) {{ el.classList.add('hit'); }});
  }});
}});
document.querySelectorAll('.pop').forEach(function (pop) {{
  pop.addEventListener('toggle', function (e) {{
    if (e.newState !== 'open') return;
    var btn = document.querySelector('[popovertarget="' + pop.id + '"]');
    var r = btn.getBoundingClientRect();
    var w = pop.offsetWidth, h = pop.offsetHeight;
    var left = Math.min(Math.max(16, r.left + r.width / 2 - w / 2), window.innerWidth - w - 16);
    var top = r.bottom + 8;
    if (top + h > window.innerHeight - 8) top = Math.max(8, r.top - h - 8);
    pop.style.left = left + 'px';
    pop.style.top = top + 'px';
  }});
}});
window.addEventListener('scroll', function () {{
  document.querySelectorAll('.pop:popover-open').forEach(function (p) {{ p.hidePopover(); }});
}}, {{ passive: true, capture: true }});
// Plugged-in jacks: saved in the artifact's shared store when available, else this browser.
(function () {{
  var jacks = Array.prototype.slice.call(document.querySelectorAll('.jack.wire'));
  if (!jacks.length) return;
  var total = document.getElementById('wired-total');
  var of = document.getElementById('wired-of');
  if (of) of.textContent = ' / ' + jacks.length;
  var store = null;
  function paint() {{
    var perBay = {{}}, all = 0;
    jacks.forEach(function (j) {{
      if (j.getAttribute('aria-pressed') === 'true') {{ all++; perBay[j.dataset.bay] = (perBay[j.dataset.bay] || 0) + 1; }}
    }});
    if (total) total.textContent = all;
    document.querySelectorAll('.wired-count').forEach(function (el) {{ el.textContent = perBay[el.dataset.bay] || 0; }});
    var on = {{}};
    jacks.forEach(function (j) {{ on[j.dataset.wire] = j.getAttribute('aria-pressed') === 'true'; }});
    document.querySelectorAll('.gj-group li[data-wires]').forEach(function (li) {{
      li.classList.toggle('connected', li.dataset.wires.split(',').every(function (id) {{ return on[id]; }}));
    }});
    var pct = Math.round(all / jacks.length * 1000) / 10;
    var box = document.getElementById('wire-progress');
    if (box) {{
      box.hidden = false;
      document.getElementById('wp-pct').textContent = pct + '%';
      document.getElementById('wp-count').textContent = '(' + all + ' of ' + jacks.length + ' jacks)';
      document.getElementById('wp-fill').style.width = pct + '%';
      document.getElementById('wp-bar').setAttribute('aria-valuenow', pct);
    }}
  }}
  function set(j, on) {{ j.setAttribute('aria-pressed', on ? 'true' : 'false'); }}
  function localLoad() {{ try {{ return JSON.parse(localStorage.getItem('patchbay-wired') || '{{}}'); }} catch (e) {{ return {{}}; }} }}
  function localSave() {{
    try {{
      var st = {{}};
      jacks.forEach(function (j) {{ if (j.getAttribute('aria-pressed') === 'true') st[j.dataset.wire] = true; }});
      localStorage.setItem('patchbay-wired', JSON.stringify(st));
    }} catch (e) {{}}
  }}
  var saved = localLoad();
  jacks.forEach(function (j) {{ set(j, !!saved[j.dataset.wire]); }});
  paint();
  jacks.forEach(function (j) {{
    j.addEventListener('click', function () {{
      var on = j.getAttribute('aria-pressed') !== 'true';
      set(j, on);
      paint();
      localSave();
      if (store) store.collection('wired').doc(j.dataset.wire).set({{ plugged: on }}).catch(function () {{}});
    }});
  }});
  if (window.claude && window.claude.use) {{
    window.claude.use('db').then(function (db) {{
      if (!db) return;
      store = db;
      db.collection('wired').onSnapshot(function (snap) {{
        var st = {{}};
        snap.docs.forEach(function (d) {{ st[d.id] = !!(d.data() || {{}}).plugged; }});
        jacks.forEach(function (j) {{ if (j.dataset.wire in st) set(j, st[j.dataset.wire]); }});
        paint();
        localSave();
      }}, function () {{ store = null; }});
    }});
  }}
}})();
// Room cable pulls: saved in the artifact's shared store when available, else this browser.
(function () {{
  var boxes = Array.prototype.slice.call(document.querySelectorAll('.cable-check'));
  if (!boxes.length) return;
  var store = null;
  function paint() {{
    var per = {{}}, all = 0;
    boxes.forEach(function (b) {{
      var row = b.closest('tr');
      if (row) row.classList.toggle('done', Array.prototype.every.call(row.querySelectorAll('.cable-check'), function (x) {{ return x.checked; }}));
      per[b.dataset.room] = per[b.dataset.room] || [0, 0];
      per[b.dataset.room][1]++;
      if (b.checked) {{ all++; per[b.dataset.room][0]++; }}
    }});
    document.querySelectorAll('.room-count').forEach(function (el) {{
      var c = per[el.dataset.room] || [0, 0];
      el.closest('.room-card').classList.toggle('done', c[0] === c[1]);
    }});
    document.querySelectorAll('.cable-bars .wire-progress').forEach(function (bar) {{
      var g = bar.dataset.group;
      var kind = bar.dataset.kind;
      var mine = boxes.filter(function (b) {{
        return (g === 'all' || b.dataset.group === g) && (!kind || b.dataset.kind === kind);
      }});
      var done = mine.filter(function (b) {{ return b.checked; }}).length;
      var pct = mine.length ? Math.round(done / mine.length * 1000) / 10 : 0;
      bar.querySelector('.wp-pct').textContent = pct + '%';
      bar.querySelector('.wp-count').textContent = '(' + done + ' of ' + mine.length + ')';
      bar.querySelector('.wp-fill').style.width = pct + '%';
      bar.querySelector('.wp-track').setAttribute('aria-valuenow', pct);
    }});
  }}
  function localLoad() {{ try {{ return JSON.parse(localStorage.getItem('patchbay-cables') || '{{}}'); }} catch (e) {{ return {{}}; }} }}
  function localSave() {{
    try {{
      var st = {{}};
      boxes.forEach(function (b) {{ st[b.dataset.task] = b.checked; }});
      localStorage.setItem('patchbay-cables', JSON.stringify(st));
    }} catch (e) {{}}
  }}
  var saved = localLoad();
  boxes.forEach(function (b) {{ b.checked = !!saved[b.dataset.task]; }});
  paint();
  boxes.forEach(function (b) {{
    b.addEventListener('change', function () {{
      paint();
      localSave();
      if (store) store.collection('cables').doc(b.dataset.task).set({{ pulled: b.checked }}).catch(function () {{}});
    }});
  }});
  if (window.claude && window.claude.use) {{
    window.claude.use('db').then(function (db) {{
      if (!db) return;
      store = db;
      db.collection('cables').onSnapshot(function (snap) {{
        var st = {{}};
        snap.docs.forEach(function (d) {{ st[d.id] = !!(d.data() || {{}}).pulled; }});
        boxes.forEach(function (b) {{ if (b.dataset.task in st) b.checked = st[b.dataset.task]; }});
        paint();
        localSave();
      }}, function () {{ store = null; }});
    }});
  }}
}})();
// To do list: saved in the artifact's store (else this browser).
(function () {{
  var boxes = Array.prototype.slice.call(document.querySelectorAll('.todo-check'));
  if (!boxes.length) return;
  var progress = document.getElementById('todo-progress');
  var store = null;
  function paint() {{
    var done = 0;
    boxes.forEach(function (b) {{ b.closest('li').classList.toggle('done', b.checked); if (b.checked) done++; }});
    if (progress) progress.querySelector('b').textContent = done;
  }}
  function localLoad() {{ try {{ return JSON.parse(localStorage.getItem('patchbay-todos') || '{{}}'); }} catch (e) {{ return {{}}; }} }}
  function localSave() {{
    try {{
      var st = {{}};
      boxes.forEach(function (b) {{ st[b.dataset.task] = b.checked; }});
      localStorage.setItem('patchbay-todos', JSON.stringify(st));
    }} catch (e) {{}}
  }}
  var saved = localLoad();
  boxes.forEach(function (b) {{ b.checked = !!saved[b.dataset.task]; }});
  paint();
  boxes.forEach(function (b) {{
    b.addEventListener('change', function () {{
      paint();
      localSave();
      if (store) store.collection('todos').doc(b.dataset.task).set({{ done: b.checked }}).catch(function () {{}});
    }});
  }});
  if (window.claude && window.claude.use) {{
    window.claude.use('db').then(function (db) {{
      if (!db) return;
      store = db;
      db.collection('todos').onSnapshot(function (snap) {{
        var st = {{}};
        snap.docs.forEach(function (d) {{ st[d.id] = !!(d.data() || {{}}).done; }});
        boxes.forEach(function (b) {{ if (b.dataset.task in st) b.checked = st[b.dataset.task]; }});
        paint();
        localSave();
      }}, function () {{ store = null; }});
    }});
  }}
}})();
// Free-text notes: room cards and each patch bay, saved in the artifact's store (else this browser).
function setupNotes(selector, collection, key, attr) {{
  var notes = Array.prototype.slice.call(document.querySelectorAll(selector));
  if (!notes.length) return;
  var store = null, timers = {{}};
  var id = function (n) {{ return n.dataset[attr]; }};
  function localLoad() {{ try {{ return JSON.parse(localStorage.getItem(key) || '{{}}'); }} catch (e) {{ return {{}}; }} }}
  function localSave() {{
    try {{
      var st = {{}};
      notes.forEach(function (n) {{ if (n.value) st[id(n)] = n.value; }});
      localStorage.setItem(key, JSON.stringify(st));
    }} catch (e) {{}}
  }}
  var saved = localLoad();
  notes.forEach(function (n) {{ if (saved[id(n)]) n.value = saved[id(n)]; }});
  notes.forEach(function (n) {{
    n.addEventListener('input', function () {{
      localSave();
      clearTimeout(timers[id(n)]);
      n.classList.add('saving');
      timers[id(n)] = setTimeout(function () {{
        n.classList.remove('saving');
        if (store) store.collection(collection).doc(id(n)).set({{ text: n.value }}).catch(function () {{}});
      }}, 700);
    }});
  }});
  if (window.claude && window.claude.use) {{
    window.claude.use('db').then(function (db) {{
      if (!db) return;
      store = db;
      db.collection(collection).onSnapshot(function (snap) {{
        var st = {{}};
        snap.docs.forEach(function (d) {{ st[d.id] = (d.data() || {{}}).text || ''; }});
        notes.forEach(function (n) {{
          if (n === document.activeElement) return;
          if (id(n) in st && n.value !== st[id(n)]) n.value = st[id(n)];
        }});
        localSave();
      }}, function () {{ store = null; }});
    }});
  }}
}}
setupNotes('.room-note', 'room_notes', 'patchbay-notes', 'room');
setupNotes('.bay-note', 'bay_notes', 'patchbay-bay-notes', 'bay');
// Open a bay's notes when it has something in it, and flag it in the summary.
(function () {{
  var KEY = 'patchbay-note-open';
  function openState() {{
    try {{ return JSON.parse(localStorage.getItem(KEY) || '{{}}'); }} catch (e) {{ return {{}}; }}
  }}
  function remember(bay, open) {{
    try {{
      var st = openState();
      st[bay] = open;
      localStorage.setItem(KEY, JSON.stringify(st));
    }} catch (e) {{}}
  }}
  function mark(n) {{
    var wrap = n.closest('.bay-note-wrap');
    if (!wrap) return;
    wrap.classList.toggle('has-text', !!n.value.trim());
  }}
  var saved = openState();
  var notes = Array.prototype.slice.call(document.querySelectorAll('.bay-note'));
  notes.forEach(function (n) {{
    var wrap = n.closest('.bay-note-wrap');
    var bay = n.dataset.bay;
    mark(n);
    // Remembered choice wins; otherwise open a bay that already has notes.
    wrap.open = bay in saved ? !!saved[bay] : !!n.value.trim();
    wrap.addEventListener('toggle', function () {{ remember(bay, wrap.open); }});
    n.addEventListener('input', function () {{ mark(n); }});
  }});
  setInterval(function () {{ notes.forEach(mark); }}, 2000);
}})();
// MIDI hookups: saved in the artifact's shared store when available, else this browser.
(function () {{
  var boxes = Array.prototype.slice.call(document.querySelectorAll('.midi-check'));
  if (!boxes.length) return;
  var progress = document.getElementById('midi-progress');
  var store = null;
  function paint() {{
    var done = 0;
    boxes.forEach(function (b) {{ b.closest('tr').classList.toggle('done', b.checked); if (b.checked) done++; }});
    if (progress) progress.querySelector('b').textContent = done;
  }}
  function localLoad() {{ try {{ return JSON.parse(localStorage.getItem('patchbay-midi') || '{{}}'); }} catch (e) {{ return {{}}; }} }}
  function localSave() {{
    try {{
      var st = {{}};
      boxes.forEach(function (b) {{ st[b.dataset.task] = b.checked; }});
      localStorage.setItem('patchbay-midi', JSON.stringify(st));
    }} catch (e) {{}}
  }}
  var saved = localLoad();
  boxes.forEach(function (b) {{ b.checked = !!saved[b.dataset.task]; }});
  paint();
  boxes.forEach(function (b) {{
    b.addEventListener('change', function () {{
      paint();
      localSave();
      if (store) store.collection('midi').doc(b.dataset.task).set({{ connected: b.checked }}).catch(function () {{}});
    }});
  }});
  if (window.claude && window.claude.use) {{
    window.claude.use('db').then(function (db) {{
      if (!db) return;
      store = db;
      db.collection('midi').onSnapshot(function (snap) {{
        var st = {{}};
        snap.docs.forEach(function (d) {{ st[d.id] = !!(d.data() || {{}}).connected; }});
        boxes.forEach(function (b) {{ if (b.dataset.task in st) b.checked = st[b.dataset.task]; }});
        paint();
        localSave();
      }}, function () {{ store = null; }});
    }});
  }}
}})();
// Move checklist: saved in the artifact's shared store when available, else this browser.
(function () {{
  var boxes = Array.prototype.slice.call(document.querySelectorAll('.move-check'));
  var progress = document.getElementById('move-progress');
  var store = null;
  function paint() {{
    var done = 0;
    boxes.forEach(function (b) {{
      b.closest('tr').classList.toggle('done', b.checked);
      if (b.checked) done++;
    }});
    if (progress) progress.querySelector('b').textContent = done;
  }}
  function localLoad() {{
    try {{ return JSON.parse(localStorage.getItem('patchbay-moves') || '{{}}'); }} catch (e) {{ return {{}}; }}
  }}
  function localSave() {{
    try {{
      var state = {{}};
      boxes.forEach(function (b) {{ state[b.dataset.task] = b.checked; }});
      localStorage.setItem('patchbay-moves', JSON.stringify(state));
    }} catch (e) {{}}
  }}
  var saved = localLoad();
  boxes.forEach(function (b) {{ b.checked = !!saved[b.dataset.task]; }});
  paint();
  boxes.forEach(function (b) {{
    b.addEventListener('change', function () {{
      paint();
      localSave();
      if (store) {{
        store.collection('moves').doc(b.dataset.task).set({{ done: b.checked }}).catch(function () {{}});
      }}
    }});
  }});
  if (window.claude && window.claude.use) {{
    window.claude.use('db').then(function (db) {{
      if (!db) return;
      store = db;
      db.collection('moves').onSnapshot(function (snap) {{
        var state = {{}};
        snap.docs.forEach(function (d) {{ state[d.id] = !!(d.data() || {{}}).done; }});
        boxes.forEach(function (b) {{ if (b.dataset.task in state) b.checked = state[b.dataset.task]; }});
        paint();
        localSave();
      }}, function () {{ store = null; }});
    }});
  }}
}})();
</script>
"""


print_pdf_path = "printable_reference/patch_bay_view.pdf"
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def render_print_pdf():
    """Print the HTML view to a letter-landscape PDF with headless Chrome (page breaks come from the print CSS)."""
    import subprocess
    if not os.path.exists(chrome_path):
        print(f"Skipping {print_pdf_path}: Google Chrome not found")
        return
    subprocess.run([chrome_path, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=5000", f"--print-to-pdf={os.path.abspath(print_pdf_path)}",
                    "file://" + os.path.abspath(output_path)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Printable view saved to {print_pdf_path}")


if __name__ == "__main__":
    from validate import validate
    validate(all_configs, gear_racks, installed_units, previous_configs, card_changes, midi_instruments)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(build_html())
    print(f"HTML view saved to {output_path}")
    render_print_pdf()

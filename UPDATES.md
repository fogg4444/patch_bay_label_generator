# Patch Bay Change Log

---

## 2026-09-20

### Reorganized: Main Rack Patch Bays

Full re-layout of bays 1–10 (top of rack first). Console buckets stay 16 wide on the left; the right 8 ports are grouped by job.

- **Bay 1:** instruments & pedals (1–9, spares reserved for more), mono outboard, stereo outboard, Art Comp far right
- **Bays 2–3:** Ghost channel inserts, with group inserts and aux sends on the right
- **Bays 4–9:** worm hole → line in, Apollo ↔ Ghost tape, with Aux 8 / Moog / Main Insert, FX returns, monitoring and 2-track on the right
- **Bay 10:** room sends (L over R), basement snake, group outs → Hearback

### Added
- SSL Fusion (bay 1), Aux 4 normalled into the Moog delay, stereo sends to 10 rooms
- MIDI patch bay label (22 jacks) and power switch label (10 switches) - names still to fill in

### Removed
- Tascam TSR-8, Pro Verb, Transition Delay

### Changed
- 902 de-esser no longer normalled; Ghost Mix Out normalled
- Porch renamed to Deck on the ethernet bay

---

## 2026-03-08

### Added: Ethernet Patch Bay

Added a new single-row ethernet patch bay label (20 ports).

**Ports 1–8: Hearback outputs**
- Hearback Out 1–8 (grouped block)

**Ports 9–18: Room network drops**
- Kitchen
- Bath Up
- Bath Dn
- Den
- Gallery
- Master Bed
- Guest Bed
- Office
- Front Porch
- Back Porch

### Moved: Bay 10 Reorganized

Cleaned up Patch Bay 10 layout. Old placeholder entries removed and routing consolidated.

**Removed from Bay 10:**
- TBD (was port 1 top)
- Office (was port 1 bottom)
- Mast Bed (was port 2 top)
- Bath Upper (was port 2 bottom)
- Kitchen (was port 3 top)
- TBD (was port 3 bottom)

**Moved within Bay 10:**
- Room inputs (Kitchen–Back Porch) moved to ports 1–10 (far left)
- Moog DLY moved to port 14 (inside filler block, left of Sub 37)
- Tanzbar OUT L/R moved to ports 15–16 (left of Sub 37)
- Filler block consolidated to ports 11–16

---

## 2026-03-07

### Added: Room Inputs to Patch Bay 10

Added room microphone/line inputs into the existing Patch Bay 10, replacing the spare filler block.

**Rooms (stereo — top row = L, bottom row = R):**
- Kitchen
- Bathroom (up)
- Bathroom (down)
- Den
- Gallery
- Master Bed
- Guest Bed
- Office

**Rooms (mono — single jack):**
- Front Porch (port 9)
- Back Porch (port 10)

Ports 11–24 left spare for future expansion.
All connections non-normalled.

---

## 2026-03-07

### Added: Printable Reference Sheet

Added auto-generated 2-page 8.5×11" landscape PDF reference guide output to `printable_reference/reference_sheet.pdf`.

Features:
- All patch bays displayed in a grid layout
- Column numbers 1–24 on each bay header
- Diagonal hatching indicates normalled connections
- Normalled key in bottom-right corner

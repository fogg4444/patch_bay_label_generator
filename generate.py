import csv
from datetime import date
from enum import Enum
import json
import os
from PIL import Image, ImageDraw, ImageFont

print('Creating your patch bay label')

csv_output_file = "csv_output/patch_bay.csv"

pixels_per_inch = 300

# Define the image dimensions and patch point width
image_width_inches = 17
image_height_inches = 0.14

font_size = 30

# Mac os
font_location = '/System/Library/Fonts/Supplemental/Andale Mono.ttf'

# github codespaces
# font_location = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

background_color = "white"
ink_color = "black"

expected_count = 24

image_width_px = int(image_width_inches * pixels_per_inch)
image_height_px = int(image_height_inches * pixels_per_inch)

# Load a font (this will need to be changed to a path on your system)
fnt = ImageFont.truetype(font_location, font_size)

def clear_csv_file():
    open(csv_output_file, 'w').close()


def append_line_to_csv_file(line_to_append_as_list):
    with open(csv_output_file, "a") as f:
        f.write(f"{','.join(line_to_append_as_list)}\n")


def generate_single_label(top_or_bottom_key: str, reverse: bool):
    image_size_tuple = (image_width_px, image_height_px)

    image = Image.new('RGB', image_size_tuple, background_color)
    d = ImageDraw.Draw(image)

    last_used_x_position = 0

    label_output_dir = "label_outputs"
    label_name = config['label_name']

    front_rear_prefix = "front"
    entries_list = config["entries"]

    if reverse is True:
        entries_list = reversed(entries_list)
        front_rear_prefix = "rear"

    image_output_destination = f"{label_output_dir}/{label_name}-{front_rear_prefix}-{top_or_bottom_key}.png"

    csv_list = []

    # loop through entries
    for i, entry in enumerate(entries_list):
        
        csv_list.append(entry[top_or_bottom_key])

        patch_width = image_width_px / expected_count

        rect_width = patch_width * entry['width']

        rect_x_start = last_used_x_position
        rect_x_end = rect_x_start + rect_width

        text_entry = entry[top_or_bottom_key]

        text_length_px = int(d.textlength(text_entry, font=fnt))
        
        # # Calcluate height of font
        ascent, descent = fnt.getmetrics()
        text_height_px = ascent + descent

        text_x = last_used_x_position + (rect_width / 2) - (text_length_px / 2)
        text_y = (image_height_px - text_height_px) / 2
        text_pos = (text_x, text_y)

        last_used_x_position = rect_x_end

        rect_y_start = 0
        rect_y_end = image_height_px
        rect_top_config = [rect_x_start, rect_y_start, rect_x_end, rect_y_end]
        rect_width = 2

        # genreate rectangle
        d.rectangle(rect_top_config, width=rect_width, outline=(ink_color))

        # generate text
        d.text(text_pos, text_entry, font=fnt, fill=(ink_color))
        
        # Add underline only if it's a normalled connection
        underline_padding = 8
        underline_y_position = rect_y_end - underline_padding
        underline_pos = [rect_x_start + underline_padding, underline_y_position, rect_x_end - underline_padding, underline_y_position]
        if entry['normalled'] is True:
            d.line(underline_pos, width=1, fill=ink_color)

        # Add trailing commas to csv file entries
        for i in range(entry['width'] - 1):
            csv_list.append('')

    if reverse is not True:
        # Only append lines to CSV if reverse is not true
        # ie: only generate csv file for front of patch bay
        append_line_to_csv_file(csv_list)
    
    image.save(image_output_destination)

def draw_bold_text(d, pos, text, font, fill):
    """Simulate bold by drawing text twice with a 1px horizontal offset."""
    x, y = pos
    d.text((x, y), text, font=font, fill=fill)
    d.text((x + 1, y), text, font=font, fill=fill)


def draw_hatch(d, x1, y1, x2, y2, spacing=8, color='#b8b8b8'):
    """Draw subtle 45-degree diagonal lines clipped to a rectangle."""
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    k_min = x1 - y2
    k_max = x2 - y1
    for k in range(k_min, k_max, spacing):
        # Entry point (from left edge or top edge)
        if y1 <= x1 - k <= y2:
            sx, sy = x1, x1 - k
        elif x1 <= y1 + k <= x2:
            sx, sy = y1 + k, y1
        else:
            continue
        # Exit point (from right edge or bottom edge)
        if y1 <= x2 - k <= y2:
            ex, ey = x2, x2 - k
        elif x1 <= y2 + k <= x2:
            ex, ey = y2 + k, y2
        else:
            continue
        d.line([(sx, sy), (ex, ey)], fill=color, width=1)


def generate_reference_page(page_configs, page_num, page_count):
    page_width_px = int(11 * pixels_per_inch)
    page_height_px = int(8.5 * pixels_per_inch)

    margin = 40
    ref_font_size = 20
    ref_fnt = ImageFont.truetype(font_location, ref_font_size)
    title_fnt = ImageFont.truetype(font_location, 30)
    num_fnt = ImageFont.truetype(font_location, 14)
    key_fnt = ImageFont.truetype(font_location, 16)

    image = Image.new('RGB', (page_width_px, page_height_px), 'white')
    d = ImageDraw.Draw(image)

    bay_label_col_width = 140
    content_x = margin + bay_label_col_width
    patch_area_width = page_width_px - margin - content_x
    unit_width = patch_area_width / expected_count

    header_height = 34
    bay_gap = 10
    title_space = 70
    n_bays = len(page_configs)
    available = page_height_px - 2 * margin - title_space
    cell_height = int((available / n_bays - header_height - bay_gap) / 2)

    ascent, descent = ref_fnt.getmetrics()
    text_h = ascent + descent
    num_ascent, num_descent = num_fnt.getmetrics()
    num_text_h = num_ascent + num_descent

    current_y = margin

    page_label = f"  ({page_num}/{page_count})"
    draw_bold_text(d, (margin, current_y), "Studio Carquinez Patch Bay Reference" + page_label,
                   font=title_fnt, fill='black')
    date_str = date.today().strftime("%Y-%m-%d")
    dw = int(d.textlength(date_str, font=title_fnt))
    draw_bold_text(d, (page_width_px - margin - dw, current_y), date_str, font=title_fnt, fill='black')
    current_y += title_space

    for bay_config in page_configs:
        row_right = content_x + patch_area_width

        # Header bar
        d.rectangle([margin, current_y, row_right, current_y + header_height], fill='#222222')
        draw_bold_text(d, (margin + 8, current_y + (header_height - text_h) // 2),
                       f"Patch Bay {bay_config['label_name']}", font=ref_fnt, fill='white')

        # Column numbers in white over the header bar
        for col in range(1, expected_count + 1):
            nx = content_x + (col - 1) * unit_width
            nw = d.textlength(str(col), font=num_fnt)
            d.text((nx + (unit_width - nw) / 2, current_y + (header_height - num_text_h) / 2),
                   str(col), font=num_fnt, fill='white')

        current_y += header_height

        # Row label cells ("TOP" / "BOTTOM")
        for row_idx, row_label in enumerate(["TOP", "BOTTOM"]):
            y0 = current_y + row_idx * cell_height
            y1 = y0 + cell_height
            d.rectangle([margin, y0, margin + bay_label_col_width, y1], outline='black', width=1)
            tw = int(d.textlength(row_label, font=ref_fnt))
            draw_bold_text(d, (margin + (bay_label_col_width - tw) // 2, y0 + (cell_height - text_h) // 2),
                           row_label, font=ref_fnt, fill='black')

        # Patch entry cells
        x = content_x
        for entry in bay_config['entries']:
            cell_w = unit_width * entry['width']

            for row_idx, text_key in enumerate(["top", "bottom"]):
                y0 = current_y + row_idx * cell_height
                y1 = y0 + cell_height

                if entry['normalled']:
                    draw_hatch(d, x, y0, x + cell_w, y1)

                d.rectangle([x, y0, x + cell_w, y1], outline='black', width=1)

                text = entry[text_key]
                tw = d.textlength(text, font=ref_fnt)
                tx = x + (cell_w - tw) / 2
                ty = y0 + (cell_height - text_h) / 2
                draw_bold_text(d, (tx, ty), text, font=ref_fnt, fill='black')

            x += cell_w

        current_y += cell_height * 2 + bay_gap

    # Legend — bottom-right corner, no margin
    key_ascent, key_descent = key_fnt.getmetrics()
    key_text_h = key_ascent + key_descent
    legend_cell_w = 70
    legend_cell_h = 34
    padding = 12
    legend_x = page_width_px - padding - legend_cell_w
    legend_y = page_height_px - padding - legend_cell_h

    draw_hatch(d, legend_x, legend_y, legend_x + legend_cell_w, legend_y + legend_cell_h)
    d.rectangle([legend_x, legend_y, legend_x + legend_cell_w, legend_y + legend_cell_h],
                outline='black', width=1)
    label = "= Normalled"
    lw = d.textlength(label, font=key_fnt)
    draw_bold_text(d, (legend_x - lw - 8, legend_y + (legend_cell_h - key_text_h) // 2),
                   label, font=key_fnt, fill='black')

    return image


def generate_reference_sheet(all_configs):
    mid = len(all_configs) // 2 + len(all_configs) % 2
    page1 = generate_reference_page(all_configs[:mid], 1, 2)
    page2 = generate_reference_page(all_configs[mid:], 2, 2)
    os.makedirs('printable_reference', exist_ok=True)
    path = 'printable_reference/reference_sheet.pdf'
    page1.save(path, save_all=True, append_images=[page2])
    print(f"Reference sheet saved to {path}")


def generate_patch_bay_labels_from_json(config, index):
    # Tally total width and check that we're the right size
    total_width = 0
    for i, entry in enumerate(config["entries"]):
        total_width += entry['width']
    
    if total_width is not expected_count:
        raise Exception(f"Config has {total_width}, but needs {expected_count} items")

    append_line_to_csv_file([])
    append_line_to_csv_file([f"Patch bay: {config['label_name']}"])
    append_line_to_csv_file([])

    # Generaet top and bottom front
    generate_single_label(
        top_or_bottom_key="top",
        reverse=False
    )
    generate_single_label(
        top_or_bottom_key="bottom",
        reverse=False
    )

    # Generate top and bottom for rear
    generate_single_label(
        top_or_bottom_key="top",
        reverse=True
    )
    generate_single_label(
        top_or_bottom_key="bottom",
        reverse=True
    )

config = [
  {
    "label_name": "1",
    "entries": [
        {
            "normalled": True,
            "top": "Worm hole Matched to Left Side Patch bay 1-16 top",
            "bottom": "Console Line In 1-16",
            "width": 16
        },
        {
            "normalled": False,
            "top": "API L/R In",
            "bottom": "API L/R Out",
            "width": 2
        },
        {
            "normalled": False,
            "top": "Dbx 160A L/R In",
            "bottom": "Dbx 160A L/R Out",
            "width": 2
        },
        {
            "normalled": False,
            "top": "D-Comp L/R In",
            "bottom": "D-Comp L/R Out",
            "width": 2
        },
        {
            "normalled": True,
            "top": "902 De-esser IN 1-2",
            "bottom": "902 De-esser OUT 1-2",
            "width": 2
        }
    ]
  },
  {
    "label_name": "2",
    "entries": [
        {
            "normalled": True,
            "top": "Worm hole Matched to Left Side Patch bay 1-16 bottom",
            "bottom": "Console Line In 17-32",
            "width": 16
        },
        {
            "normalled": True,
            "top": "Aux 1 Out",
            "bottom": "EMT 140 IN",
            "width": 1
        },
        {
            "normalled": True,
            "top": "Aux 2 Out",
            "bottom": "PCM60 IN",
            "width": 1
        },
        {
            "normalled": True,
            "top": "Aux 3 Out",
            "bottom": "SDE 1000 IN",
            "width": 1
        },
        {
            "normalled": True,
            "top": "Aux 4 Out",
            "bottom": "-",
            "width": 1
        },
        {
            "normalled": True,
            "top": "Aux 5 / 6 Out",
            "bottom": "Pro Verb Out",
            "width": 2
        },
        {
            "normalled": True,
            "top": "Aux 7 Out",
            "bottom": "Pro Verb In",
            "width": 2
        },
    ]
  },
  {
    "label_name": "3",
    "entries": [
        {
            "normalled": True,
            "top": "Apollo #1 1-16 Out",
            "bottom": "Ghost 1-16 Tape In",
            "width": 16
        },
        {
            "normalled": True,
            "top": "Aux 8 Out L/R",
            "bottom": "-",
            "width": 2
        },
        {
            "normalled": True,
            "top": "Studio A O/P L/R",
            "bottom": "Headamp Pro Input",
            "width": 2
        },
        {
            "normalled": True,
            "top": "Studio Phones B L/R Out",
            "bottom": "Meyer Mains In L/R",
            "width": 2
        },
        {
            "normalled": False,
            "top": "PCM60 Return L/R",
            "bottom": "EMT 140 Return L/R",
            "width": 2
        },
    ]
  },
  {
    "label_name": "4",
    "entries": [
        {
            "normalled": True,
            "top": "Apollo #2 17-32 Out",
            "bottom": "Ghost 17-32 Tape In",
            "width": 16
        },
        {
            "normalled": False,
            "top": "Tascam TSR-8 In 1-8",
            "bottom": "Tascam TSR-8 Out 1-8",
            "width": 8
        }
    ]
  },
  {
    "label_name": "5",
    "entries": [
        {
            "normalled": True,
            "top": "Ghost 1-16 Tape Send",
            "bottom": "Apollo #1 1-16 In",
            "width": 16
        },
        {
            "normalled": True,
            "top": "Control Room Out",
            "bottom": "Yamaha Monitors In",
            "width": 2
        },
        {
            "normalled": True,
            "top": "Apollo 2 Track Out",
            "bottom": "Ghost 2 Track A Input",
            "width": 2
        },
        {
            "normalled": True,
            "top": "Record Player OUT",
            "bottom": "Ghost 2 Track B Input",
            "width": 2
        },
        {
            "normalled": True,
            "top": "Ghost Mix OUT",
            "bottom": "-",
            "width": 2
        }
    ]
  },
  {
    "label_name": "6",
    "entries": [
        {
            "normalled": True,
            "top": "Ghost 17-32 Tape Send",
            "bottom": "Apollo #2 17-32 In",
            "width": 16
        },
        {
            "normalled": True,
            "top": "Alt CRM Out L/R",
            "bottom": "Mix Cube L / -",
            "width": 2
        },
        {
            "normalled": False,
            "top": "Hearback IN 1, 2, 3, 4",
            "bottom": "Hearback IN 5, 6, 7, 8",
            "width": 4
        },
        {
            "normalled": False,
            "top": "-",
            "bottom": "-",
            "width": 1
        },
        {
            "normalled": False,
            "top": "LA-2A In",
            "bottom": "LA-2A Out",
            "width": 1
        }
    ]
  },
  {
    "label_name": "7",
    "entries": [
        {
            "normalled": True,
            "top": "Ghost Channel Insert Send 1-16",
            "bottom": "Ghost Channel Insert Return 1-16",
            "width": 16
        },
        {
            "normalled": False,
            "top": "Group 1 / 2 Out",
            "bottom": "FX 1 In L / R",
            "width": 2
        },
        {
            "normalled": False,
            "top": "Group 3 / 4 Out",
            "bottom": "FX 2 In L / R",
            "width": 2
        },
        {
            "normalled": False,
            "top": "Group 5 / 6 Out",
            "bottom": "FX 3 In L / R",
            "width": 2
        },
        {
            "normalled": False,
            "top": "Group 7 / 8 Out",
            "bottom": "FX 4 In L / R",
            "width": 2
        },
    ]
  },
  {
    "label_name": "8",
    "entries": [
        {
            "normalled": True,
            "top": "Ghost Channel Insert Send 17-32",
            "bottom": "Ghost Channel Insert Return 17-32",
            "width": 16
        },
        {
            "normalled": False,
            "top": "Group 1 - 8 Insert Send",
            "bottom": "Group 1 - 8 Insert Return",
            "width": 8
        },
    ]
  },
  {
    "label_name": "9",
    "entries": [
        {
            "normalled": True,
            "top": "Main Insert Send",
            "bottom": "Main Insert Return",
            "width": 2
        },
        {
            "normalled": False,
            "top": "Basement Snake Send A, B, C, D",
            "bottom": "Basement Snake Send E, F, G, H",
            "width": 4
        },
        {
            "normalled": False,
            "top": "-",
            "bottom": "-",
            "width": 10
        },
        {
            "normalled": False,
            "top": "SDE 1000 Return",
            "bottom": "-",
            "width": 1
        },
        {
            "normalled": False,
            "top": "-",
            "bottom": "-",
            "width": 1
        },
        {
            "normalled": False,
            "top": "DBX 160 Link",
            "bottom": "DBX 160 Link",
            "width": 1
        },
        {
            "normalled": False,
            "top": "Fuzz In",
            "bottom": "Fuzz Out",
            "width": 1
        },
        {
            "normalled": False,
            "top": "Transition Delay In",
            "bottom": "Transition Delay Out",
            "width": 2
        },
        {
            "normalled": False,
            "top": "-",
            "bottom": "Phones Amp In L/R",
            "width": 2
        },
    ]
  },
    {
    "label_name": "10",
    "entries": [
        {
            "normalled": False,
            "top": "TBD",
            "bottom": "Office",
            "width": 1
        },
        {
            "normalled": False,
            "top": "Mast Bed",
            "bottom": "Bath Upper",
            "width": 1
        },
        {
            "normalled": False,
            "top": "Kitchen",
            "bottom": "TBD",
            "width": 1
        },
        {
            "normalled": False,
            "top": "Moog DLY IN",
            "bottom": "Moog DLY OUT",
            "width": 1
        },
        {
            "normalled": False,
            "top": "Tanzbar OUT L/R",
            "bottom": "-",
            "width": 2
        },
        {"normalled": False, "top": "Kitchen L",    "bottom": "Kitchen R",    "width": 1},
        {"normalled": False, "top": "Bath Up L",    "bottom": "Bath Up R",    "width": 1},
        {"normalled": False, "top": "Bath Dn L",    "bottom": "Bath Dn R",    "width": 1},
        {"normalled": False, "top": "Den L",        "bottom": "Den R",        "width": 1},
        {"normalled": False, "top": "Gallery L",    "bottom": "Gallery R",    "width": 1},
        {"normalled": False, "top": "Master Bed L", "bottom": "Master Bed R", "width": 1},
        {"normalled": False, "top": "Guest Bed L",  "bottom": "Guest Bed R",  "width": 1},
        {"normalled": False, "top": "Office L",     "bottom": "Office R",     "width": 1},
        {"normalled": False, "top": "Front Porch",  "bottom": "Front Porch",  "width": 1},
        {"normalled": False, "top": "Back Porch",   "bottom": "Back Porch",   "width": 1},
        {"normalled": False, "top": "-",            "bottom": "-",            "width": 3},
        {
            "normalled": True,
            "top": "-",
            "bottom": "Sub 37 OUT",
            "width": 1
        },
        {
            "normalled": False,
            "top": "MXR Dist IN",
            "bottom": "MXR Dist OUT",
            "width": 1
        },
        {
            "normalled": False,
            "top": "Art Comp IN L/R",
            "bottom": "Art Comp OUT L/R",
            "width": 2
        },
        {
            "normalled": False,
            "top": "UA 550 In",
            "bottom": "UA 550 Out",
            "width": 1
        },
    ]
  },
  {
    "label_name": "11-amp-rack",
    "entries": [
        {
            "normalled": True,
            "top": "L / R Audio Source Out",
            "bottom": "DBX Drive Rack L/R IN",
            "width": 2
        },
        {
            "normalled": True,
            "top": "DBX High Out L/R",
            "bottom": "High Amp In L/R",
            "width": 2
        },
        {
            "normalled": True,
            "top": "DBX Mid Out L/R",
            "bottom": "Mid Amp In L/R",
            "width": 2
        },
        {
            "normalled": True,
            "top": "DBX Low Out L/R",
            "bottom": "Low Amp In L/R",
            "width": 2
        },
        {
            "normalled": True,
            "top": "-",
            "bottom": "-",
            "width": 16
        },
    ]
  }
]

all_configs = config
clear_csv_file()

for i, config in enumerate(all_configs):
    generate_patch_bay_labels_from_json(config, i)

generate_reference_sheet(all_configs)
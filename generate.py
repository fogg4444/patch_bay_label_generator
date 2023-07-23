import csv
from enum import Enum
import json
from PIL import Image, ImageDraw, ImageFont

print('Creating your patch bay label')

csv_output_file = "csv_output/patch_bay.csv"

pixels_per_inch = 300

# Define the image dimensions and patch point width
image_width_inches = 17
image_height_inches = 0.14

font_size = 30
font_location = '/System/Library/Fonts/Supplemental/Andale Mono.ttf'

background_color = "white"
ink_color = "black"

expected_count = 24

image_width_px = int(image_width_inches * pixels_per_inch)
image_height_px = int(image_height_inches * pixels_per_inch)

# Load a font (this will need to be changed to a path on your system)
fnt = ImageFont.truetype(font_location, font_size)

def clear_csv_file():
    print('delete csv file contents')
    open(csv_output_file, 'w').close()
    

def append_line_to_csv_file(line_to_append_as_list):
    print('append line to csv file')
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

    csv_top_list = []
    csv_bottom_list = []

    # loop through entries
    for i, entry in enumerate(entries_list):
        
        csv_top_list.append(entry['top'])
        csv_bottom_list.append(entry['bottom'])

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
            csv_top_list.append('')
            csv_bottom_list.append('')

    append_line_to_csv_file(csv_top_list)
    append_line_to_csv_file(csv_bottom_list)

    print("generating label...", image_output_destination)
    
    image.save(image_output_destination)

def generate_patch_bay_labels_from_json(config, index):
    # Tally total width and check that we're the right size
    total_width = 0
    for i, entry in enumerate(config["entries"]):
        total_width += entry['width']
    
    if total_width is not expected_count:
        raise Exception(f"Config has {total_width}, but needs {expected_count} items")

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
            "top": "-",
            "bottom": "-",
            "width": 1
        },
        {
            "normalled": True,
            "top": "-",
            "bottom": "-",
            "width": 1
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
            "normalled": False,
            "top": "Aux 1 Out",
            "bottom": "Moog DLY In",
            "width": 1
        },
        {
            "normalled": False,
            "top": "Aux 2 Out",
            "bottom": "Fuzz In",
            "width": 1
        },
        {
            "normalled": False,
            "top": "Aux 3 Out",
            "bottom": "-",
            "width": 1
        },
        {
            "normalled": False,
            "top": "Aux 4 Out",
            "bottom": "-",
            "width": 1
        },
        {
            "normalled": False,
            "top": "Aux 5 Out",
            "bottom": "-",
            "width": 1
        },
        {
            "normalled": False,
            "top": "Aux 6 Out",
            "bottom": "-",
            "width": 1
        },
        {
            "normalled": False,
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
            "top": "Apollo 16 Out",
            "bottom": "Ghost 17-32 Tape In",
            "width": 16
        },
        {
            "normalled": False,
            "top": "-",
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
            "top": "-",
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
            "top": "-",
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
            "top": "-",
            "bottom": "-",
            "width": 1
        },
        {
            "normalled": False,
            "top": "-",
            "bottom": "-",
            "width": 1
        }
    ]
  },
  {
    "label_name": "4",
    "entries": [
        {
            "normalled": True,
            "top": "Apollo 16 In",
            "bottom": "Ghost 1-16 Tape Direct Out",
            "width": 16
        },
        {
            "normalled": False,
            "top": "-",
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
            "top": "-",
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
            "top": "-",
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
            "top": "-",
            "bottom": "-",
            "width": 1
        },
        {
            "normalled": False,
            "top": "-",
            "bottom": "-",
            "width": 1
        }
    ]
  },
  {
    "label_name": "5",
    "entries": [
        {
            "normalled": True,
            "top": "-",
            "bottom": "-",
            "width": 24
        }
    ]
  },
  {
    "label_name": "6",
    "entries": [
        {
            "normalled": True,
            "top": "Ghost Channel Insert Send 1-16",
            "bottom": "Ghost Channel Insert Return 1-16",
            "width": 16
        },
        {
            "normalled": False,
            "top": "Group 1 -  8 Direct Outputs",
            "bottom": "-",
            "width": 8
        },
    ]
  },
  {
    "label_name": "7",
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
    "label_name": "8-amp-rack",
    "entries": [
        {
            "normalled": True,
            "top": "L / R Main Input",
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

clear_csv_file()

for i, config in enumerate(config):    
    generate_patch_bay_labels_from_json(config, i)
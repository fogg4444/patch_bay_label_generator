from datetime import date
import os
from PIL import Image, ImageDraw, ImageFont
from config import config as all_configs

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


def generate_single_label(top_or_bottom_key: str, reverse: bool, port_count: int = expected_count):
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

        patch_width = image_width_px / port_count

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


def wrap_text(d, text, font, max_width):
    """Split text into lines that each fit within max_width pixels."""
    words = text.split()
    lines = []
    current = ''
    for word in words:
        candidate = (current + ' ' + word).strip()
        if d.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if lines else [text]


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
    num_fnt = ImageFont.truetype(font_location, 18)
    key_fnt = ImageFont.truetype(font_location, 16)

    image = Image.new('RGB', (page_width_px, page_height_px), 'white')
    d = ImageDraw.Draw(image)

    bay_label_col_width = 140
    content_x = margin + bay_label_col_width
    patch_area_width = page_width_px - margin - content_x

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
    date_str = "Last updated: " + date.today().strftime("%Y-%m-%d")
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
        bay_port_count = bay_config.get("port_count", expected_count)
        bay_unit_width = patch_area_width / bay_port_count
        for col in range(1, bay_port_count + 1):
            nx = content_x + (col - 1) * bay_unit_width
            nw = d.textlength(str(col), font=num_fnt)
            draw_bold_text(d, (nx + (bay_unit_width - nw) / 2, current_y + (header_height - num_text_h) / 2),
                           str(col), font=num_fnt, fill='white')

        current_y += header_height

        single_row = bay_config.get("single_row", False)
        row_labels = [""] if single_row else ["TOP", "BOTTOM"]
        row_keys   = ["top"] if single_row else ["top", "bottom"]
        row_height = cell_height * 2 if single_row else cell_height

        # Row label cells
        for row_idx, row_label in enumerate(row_labels):
            y0 = current_y + row_idx * row_height
            y1 = y0 + row_height
            d.rectangle([margin, y0, margin + bay_label_col_width, y1], outline='black', width=1)
            if row_label:
                tw = int(d.textlength(row_label, font=ref_fnt))
                draw_bold_text(d, (margin + (bay_label_col_width - tw) // 2, y0 + (row_height - text_h) // 2),
                               row_label, font=ref_fnt, fill='black')

        # Patch entry cells
        x = content_x
        for entry in bay_config['entries']:
            cell_w = bay_unit_width * entry['width']

            for row_idx, text_key in enumerate(row_keys):
                y0 = current_y + row_idx * row_height
                y1 = y0 + row_height

                if entry['normalled']:
                    draw_hatch(d, x, y0, x + cell_w, y1)

                d.rectangle([x, y0, x + cell_w, y1], outline='black', width=1)

                text = entry[text_key]
                padding = 4
                lines = wrap_text(d, text, ref_fnt, cell_w - padding * 2)
                total_text_h = len(lines) * text_h
                ty = y0 + (row_height - total_text_h) / 2
                for line in lines:
                    tw = d.textlength(line, font=ref_fnt)
                    tx = x + (cell_w - tw) / 2
                    draw_bold_text(d, (tx, ty), line, font=ref_fnt, fill='black')
                    ty += text_h

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

    label = "Normalled ="
    lw = int(d.textlength(label, font=key_fnt))
    legend_x = page_width_px - padding - legend_cell_w
    draw_bold_text(d, (legend_x - lw - 8, legend_y + (legend_cell_h - key_text_h) // 2),
                   label, font=key_fnt, fill='black')
    draw_hatch(d, legend_x, legend_y, legend_x + legend_cell_w, legend_y + legend_cell_h)
    d.rectangle([legend_x, legend_y, legend_x + legend_cell_w, legend_y + legend_cell_h],
                outline='black', width=1)

    return image


def generate_changelog_page():
    page_width_px = int(11 * pixels_per_inch)
    page_height_px = int(8.5 * pixels_per_inch)
    margin = 40

    image = Image.new('RGB', (page_width_px, page_height_px), 'white')
    d = ImageDraw.Draw(image)

    title_fnt    = ImageFont.truetype(font_location, 30)
    heading_fnt  = ImageFont.truetype(font_location, 30)
    body_fnt     = ImageFont.truetype(font_location, 26)
    date_fnt     = ImageFont.truetype(font_location, 22)

    # Title row
    draw_bold_text(d, (margin, margin), "Studio Carquinez Patch Bay Reference  —  Change Log", font=title_fnt, fill='black')
    date_str = "Last updated: " + date.today().strftime("%Y-%m-%d")
    dw = int(d.textlength(date_str, font=title_fnt))
    draw_bold_text(d, (page_width_px - margin - dw, margin), date_str, font=title_fnt, fill='black')

    current_y = margin + 55
    line_gap = 8

    # Parse and render UPDATES.md
    try:
        with open('UPDATES.md', 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    section_box = 28   # checkbox size for section headings
    item_box    = 18   # checkbox size for bullet items
    section_indent = margin
    item_indent    = margin + 40

    for raw in lines:
        line = raw.rstrip()
        if not line or line == '---' or line.startswith('# '):
            continue

        if line.startswith('## '):
            current_y += 12
            d.line([margin, current_y, page_width_px - margin, current_y], fill='#bbbbbb', width=2)
            current_y += 8
            ascent, descent = date_fnt.getmetrics()
            draw_bold_text(d, (section_indent, current_y), line[3:], font=date_fnt, fill='#555555')
            current_y += ascent + descent + line_gap

        elif line.startswith('### '):
            current_y += 4
            ascent, descent = heading_fnt.getmetrics()
            cy = current_y + (ascent + descent - section_box) // 2
            d.rectangle([section_indent, cy, section_indent + section_box, cy + section_box],
                        outline='black', width=3)
            draw_bold_text(d, (section_indent + section_box + 12, current_y), line[4:],
                           font=heading_fnt, fill='black')
            current_y += ascent + descent + line_gap + 4

        elif line.startswith('**') and line.endswith('**'):
            ascent, descent = body_fnt.getmetrics()
            draw_bold_text(d, (item_indent, current_y), line.strip('*'), font=body_fnt, fill='#333333')
            current_y += ascent + descent + line_gap

        elif line.startswith('- '):
            ascent, descent = body_fnt.getmetrics()
            cy = current_y + (ascent + descent - item_box) // 2
            d.rectangle([item_indent, cy, item_indent + item_box, cy + item_box],
                        outline='black', width=2)
            d.text((item_indent + item_box + 10, current_y), line[2:], font=body_fnt, fill='black')
            current_y += ascent + descent + line_gap

        else:
            ascent, descent = body_fnt.getmetrics()
            d.text((item_indent, current_y), line, font=body_fnt, fill='black')
            current_y += ascent + descent + line_gap

    # Large "all done" checkbox at the bottom
    checkbox_size = 60
    checkbox_x = margin
    checkbox_y = page_height_px - margin - checkbox_size
    d.rectangle([checkbox_x, checkbox_y, checkbox_x + checkbox_size, checkbox_y + checkbox_size],
                outline='black', width=4)
    check_fnt = ImageFont.truetype(font_location, 26)
    check_label = "All patch changes applied to hardware"
    ascent, descent = check_fnt.getmetrics()
    draw_bold_text(d, (checkbox_x + checkbox_size + 20,
                       checkbox_y + (checkbox_size - ascent - descent) // 2),
                   check_label, font=check_fnt, fill='black')

    return image


def generate_reference_sheet(all_configs):
    mid = len(all_configs) // 2 + len(all_configs) % 2
    page1 = generate_reference_page(all_configs[:mid], 1, 2)
    page2 = generate_reference_page(all_configs[mid:], 2, 2)
    page3 = generate_changelog_page()
    os.makedirs('printable_reference', exist_ok=True)
    path = 'printable_reference/reference_sheet.pdf'
    page1.save(path, save_all=True, append_images=[page2, page3])
    print(f"Reference sheet saved to {path}")


def generate_patch_bay_labels_from_json(config, index):
    port_count = config.get("port_count", expected_count)
    total_width = sum(e['width'] for e in config["entries"])

    if total_width != port_count:
        raise Exception(f"Config has {total_width}, but needs {port_count} items")

    append_line_to_csv_file([])
    append_line_to_csv_file([f"Patch bay: {config['label_name']}"])
    append_line_to_csv_file([])

    if config.get("single_row"):
        generate_single_label(top_or_bottom_key="top", reverse=False, port_count=port_count)
    else:
        generate_single_label(top_or_bottom_key="top", reverse=False, port_count=port_count)
        generate_single_label(top_or_bottom_key="bottom", reverse=False, port_count=port_count)
        generate_single_label(top_or_bottom_key="top", reverse=True, port_count=port_count)
        generate_single_label(top_or_bottom_key="bottom", reverse=True, port_count=port_count)

clear_csv_file()

for i, config in enumerate(all_configs):
    generate_patch_bay_labels_from_json(config, i)

generate_reference_sheet(all_configs)

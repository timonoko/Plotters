#! /usr/bin/python3

"""
Displays G-code graphics, scaling them to a fixed output size.
"""

from PIL import Image, ImageFont, ImageDraw, ImageOps
import time,sys,math,os,datetime

# --- Configuration ---
OUTPUT_WIDTH = 1600
OUTPUT_HEIGHT = 1000
PADDING = 50 # pixels

try:
    os.system('killall display')
except:
    pass

try:   F=open(sys.argv[1],'r')
except: F=open('gcode.gcode','r')

def parsee(s):
    i=0
    tulos={}
    number=""
    prevalfa="kakka"
    while i<len(s):
        if s[i]=="(": break
        elif ord(s[i]) in range(ord('0'),ord('9')+1) or s[i]=='-' or s[i]=='.':
            number+=s[i]
        else:
            if prevalfa != "kakka" and number != "":
                tulos.update({prevalfa:float(number)})
                number=""
            if ord(s[i]) in range(ord('A'),ord('Z')+1):
                prevalfa=s[i]
        i+=1
    if prevalfa != "kakka" and number != "":
        tulos.update({prevalfa:float(number)})
    return tulos

# --- First Pass: Find boundaries of the G-code ---
F_lines = F.readlines()
F.close()
max_gcode_x = 0.0
max_gcode_y = 0.0
for line in F_lines:
    s = parsee(line)
    if 'X' in s:
        x = float(s['X'])
        if x > max_gcode_x: max_gcode_x = x
    if 'Y' in s:
        y = float(s['Y'])
        if y > max_gcode_y: max_gcode_y = y

if max_gcode_x == 0 or max_gcode_y == 0:
    print("Could not find valid X, Y coordinates in G-code.")
    sys.exit(1)

# --- Calculate Scale Factor ---
x_scale = (OUTPUT_WIDTH - 2*PADDING) / max_gcode_x
y_scale = (OUTPUT_HEIGHT - 2*PADDING) / max_gcode_y
SCALE = min(x_scale, y_scale)

print(f"G-code bounds: X={max_gcode_x:.2f}, Y={max_gcode_y:.2f}")
print(f"Calculated scale factor: {SCALE:.2f}")

# --- Second Pass: Draw the image ---
IMG=Image.new(mode="RGB",size=(OUTPUT_WIDTH, OUTPUT_HEIGHT),color=(0xe5,0xd5,0xa4))
draw = ImageDraw.Draw(IMG)

PREV_X=0.0
PREV_Y=0.0
PEN_DOWN=False

def get_coords(s):
    # Returns scaled and padded coordinates
    try: x = (float(s['X']) * SCALE) + PADDING
    except: x = PREV_X
    try: y = (float(s['Y']) * SCALE) + PADDING
    except: y = PREV_Y
    return x, y

last_g_motion = 0
for k in F_lines:
    s=parsee(k)
    x, y = get_coords(s)

    if 'G' in s:
        g_code = s['G']
        if g_code in [0, 1, 2, 3]: last_g_motion = g_code
        if g_code == 4:
            if 'P' in s: time.sleep(s['P'])
        elif g_code in [0,1,2,3]:
             if 'Z' in s and s['Z']<1: PEN_DOWN=True
             if PEN_DOWN and last_g_motion != 0: draw.line([(PREV_X, PREV_Y), (x, y)], fill=(0,0,0), width=1)
             if 'Z' in s and s['Z']>1: PEN_DOWN=False
    elif 'X' in s or 'Y' in s:
        if last_g_motion in [0, 1, 2, 3]:
            if PEN_DOWN and last_g_motion != 0: draw.line([(PREV_X, PREV_Y), (x, y)], fill=(0,0,0), width=1)

    if 'M' in s:
        if s['M'] in [3, 4]: PEN_DOWN=True
        if s['M'] == 5: PEN_DOWN=False

    PREV_X, PREV_Y = x, y


# --- Gridlines and Labels ---
IMG=ImageOps.flip(IMG)
draw = ImageDraw.Draw(IMG) # Recreate draw object for flipped image

try:
    font = ImageFont.truetype("DejaVuSans.ttf", 12)
except IOError:
    font = ImageFont.load_default()

# We loop in g-code units (inches) and convert to pixels
major_step_inches = 0.5
intermediate_step_inches = 0.1
minor_step_inches = 0.025 # A finer grid

# --- X-axis Grid and Labels ---
for i in range(int(max_gcode_x / minor_step_inches) + 1):
    gcode_x = i * minor_step_inches
    px_x = int((gcode_x * SCALE) + PADDING)

    # Use floating point modulo with a small tolerance
    is_major = math.isclose(gcode_x % major_step_inches, 0.0) or math.isclose(gcode_x % major_step_inches, major_step_inches)
    is_intermediate = math.isclose(gcode_x % intermediate_step_inches, 0.0) or math.isclose(gcode_x % intermediate_step_inches, intermediate_step_inches)

    if is_major:
        draw.line([(px_x, 0), (px_x, IMG.height)], fill=(255, 0, 0), width=1)
        draw.text((px_x + 2, IMG.height - PADDING + 10), f"{gcode_x:.1f}", font=font, fill=(0,0,255))
    elif is_intermediate:
        draw.line([(px_x, 0), (px_x, IMG.height)], fill=(255, 100, 100), width=1)
        draw.text((px_x + 2, IMG.height - PADDING + 10), f"{gcode_x:.1f}", font=font, fill=(100,100,255))
    else: # Minor line
        draw.line([(px_x, 0), (px_x, IMG.height)], fill=(255, 150, 150), width=1)

# --- Y-axis Grid and Labels ---
for i in range(int(max_gcode_y / minor_step_inches) + 1):
    gcode_y = i * minor_step_inches
    px_y_unflipped = (gcode_y * SCALE) + PADDING
    px_y_flipped = IMG.height - px_y_unflipped

    is_major = math.isclose(gcode_y % major_step_inches, 0.0) or math.isclose(gcode_y % major_step_inches, major_step_inches)
    is_intermediate = math.isclose(gcode_y % intermediate_step_inches, 0.0) or math.isclose(gcode_y % intermediate_step_inches, intermediate_step_inches)

    if is_major:
        draw.line([(0, px_y_flipped), (IMG.width, px_y_flipped)], fill=(255, 0, 0), width=1)
        draw.text((PADDING - 30, px_y_flipped - 6), f"{gcode_y:.1f}", font=font, fill=(255,0,0))
    elif is_intermediate:
        draw.line([(0, px_y_flipped), (IMG.width, px_y_flipped)], fill=(255, 100, 100), width=1)
        draw.text((PADDING - 30, px_y_flipped - 6), f"{gcode_y:.1f}", font=font, fill=(255,100,100))
    else: # Minor line
        draw.line([(0, px_y_flipped), (IMG.width, px_y_flipped)], fill=(255, 150, 150), width=1)



try:
    IMG.save(sys.argv[3])
    print(f"Successfully saved image to {sys.argv[3]}")
except Exception as e:
    print(f"Error saving file: {e}")
    pass

IMG.show()

import re
import sys
import argparse

def correct_and_scale_gcode(input_file, output_file, desired_width_cm=None):
    """
    Reads a G-code file, moves it to the origin (0,0).
    If desired_width_cm is provided, it scales the G-code so its largest
    dimension matches the specified width in centimeters.
    Assumes the input G-code units are INCHES.
    """
    min_x = float('inf')
    min_y = float('inf')
    max_x = float('-inf')
    max_y = float('-inf')

    # --- First pass: find min and max coordinates ---
    has_coords = False
    with open(input_file, 'r') as f:
        for line in f:
            match = re.search(r'X([\d\.\-]+)\s*Y([\d\.\-]+)', line)
            if match:
                has_coords = True
                x = float(match.group(1))
                y = float(match.group(2))
                if x < min_x: min_x = x
                if y < min_y: min_y = y
                if x > max_x: max_x = x
                if y > max_y: max_y = y

    if not has_coords:
        print("No X, Y coordinates found in the file. Copying file without changes.")
        with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
            f_out.write(f_in.read())
        return

    # --- Calculate scaling factor ---
    scale_factor = 1.0
    if desired_width_cm is not None:
        CM_PER_INCH = 2.54
        desired_size_inches = desired_width_cm / CM_PER_INCH
        
        current_width = max_x - min_x
        current_height = max_y - min_y
        max_dimension = max(current_width, current_height)

        if max_dimension == 0:
            print("Cannot scale a zero-sized drawing.")
        else:
            scale_factor = desired_size_inches / max_dimension
        
        print(f"Original size (inches): {current_width:.4f}w x {current_height:.4f}h")
        print(f"Target size: {desired_size_inches:.4f} inches (~{desired_width_cm}cm)")
        print(f"Calculated scaling factor: {scale_factor:.4f}")
    else:
        print("No width specified. Moving to origin without scaling (scale factor = 1.0).")


    # --- Second pass: rewrite with corrected and scaled coordinates ---
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            original_line = line
            match = re.search(r'X([\d\.\-]+)\s*Y([\d\.\-]+)', line)
            if match:
                x = float(match.group(1))
                y = float(match.group(2))
                new_x = (x - min_x) * scale_factor
                new_y = (y - min_y) * scale_factor
                line = line.replace(match.group(0), f'X{new_x:.4f} Y{new_y:.4f}')

            # Also scale other relevant values
            if scale_factor != 1.0:
                z_match = re.search(r'Z([\d\.\-]+)', line)
                if z_match:
                    z = float(z_match.group(1))
                    new_z = z * scale_factor
                    line = line.replace(z_match.group(0), f'Z{new_z:.4f}')

                f_match = re.search(r'F([\d\.\-]+)', line)
                if f_match:
                    f_val = float(f_match.group(1))
                    new_f = f_val * scale_factor
                    line = line.replace(f_match.group(0), f'F{new_f:.4f}')
            
            f_out.write(line)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Correct G-code position and optionally scale it.')
    parser.add_argument('input_file', help='The input G-code file.')
    parser.add_argument('output_file', help='The output G-code file.')
    parser.add_argument('--width-cm', type=float, help='Optional: desired width in centimeters. The G-code will be scaled to this size.')
    
    args = parser.parse_args()
    
    correct_and_scale_gcode(args.input_file, args.output_file, args.width_cm)
    print(f"\nG-code processing complete. Output saved to {args.output_file}")

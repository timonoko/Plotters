
import cv2
import numpy as np
import sys

def _find_closest_point_on_contour(source_point, target_contour):
    """
    Finds the closest point on a target_contour to a source_point.
    """
    min_dist = float('inf')
    closest_target_point = None

    for tp in target_contour:
        dist = np.linalg.norm(np.array(source_point) - tp[0])
        if dist < min_dist:
            min_dist = dist
            closest_target_point = tuple(tp[0])
    return closest_target_point

def main():
    # --- Argument Parsing ---
    if len(sys.argv) < 3: # Removed '--scale' from mandatory args check
        print("Usage: python add_bridges.py <input_image> <output_image>")
        print("Example: python add_bridges.py input.jpg output.png")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Bridge count and width are now fixed as per user request
    num_bridges = 3
    fixed_bridge_pixel_width = 3
    print(f"Using {num_bridges} bridges with a fixed width of {fixed_bridge_pixel_width} pixels.")

    # --- 1. Load and Binarize Image ---
    try:
        img = cv2.imread(input_file)
        if img is None:
            raise FileNotFoundError
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Threshold to get white objects on a black background
    _, binary_image = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    
    # --- 2. Find Contours of all white areas ---
    # CHAIN_APPROX_SIMPLE saves memory
    contours, hierarchy = cv2.findContours(binary_image, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    if not contours or len(contours) < 2:
        print("Less than two white areas found. No bridges needed. Saving binarized image.")
        cv2.imwrite(output_file, binary_image)
        return

    # --- 3. Identify Mainland and Islands ---
    # We will only bridge top-level contours (i.e., not holes within holes)
    top_level_indices = [i for i, h in enumerate(hierarchy[0]) if h[3] == -1]

    if len(top_level_indices) < 2:
        print("Only one top-level white area found. No bridges needed. Saving binarized image.")
        cv2.imwrite(output_file, binary_image)
        return
        
    top_level_contours = [contours[i] for i in top_level_indices]

    # Sort by area to find the biggest one (mainland)
    top_level_contours.sort(key=cv2.contourArea, reverse=True)
    
    mainland_contour = top_level_contours[0]
    island_contours = top_level_contours[1:]
    
    print(f"Found mainland and {len(island_contours)} island(s).")

    # --- 4. Build Bridges ---
    # Create a copy of the image to draw bridges on
    output_image = binary_image.copy()

    for i, island in enumerate(island_contours):
        print(f"Processing island {i+1}...")
        # Ensure island has enough points for num_bridges
        if len(island) < num_bridges:
            print(f"  Island {i+1} has too few points ({len(island)}) to place {num_bridges} bridges. Skipping.")
            continue

        for b_idx in range(num_bridges):
            # Calculate an evenly spaced point on the island's contour
            island_point_index = (b_idx * len(island)) // num_bridges
            island_source_point = tuple(island[island_point_index][0])

            # Find the closest point on the mainland to this island_source_point
            mainland_target_point = _find_closest_point_on_contour(island_source_point, mainland_contour)

            if mainland_target_point:
                print(f"  Bridging from island point {island_source_point} to mainland point {mainland_target_point}")
                # Draw a white line to create the bridge
                cv2.line(output_image, island_source_point, mainland_target_point, (255, 255, 255), fixed_bridge_pixel_width)
            else:
                print(f"  Could not find a mainland target point for island point {island_source_point}. Skipping bridge.")

    # --- 5. Save the final image ---
    cv2.imwrite(output_file, output_image)
    print(f"Successfully created bridged image: {output_file}")

if __name__ == "__main__":
    main()

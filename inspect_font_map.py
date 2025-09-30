from fontTools import ttLib
import os

def inspect_font_mapping(font_path):
    """
    Inspects a TrueType font file and prints its character-to-glyph mapping.
    This helps to identify which characters (e.g., 'A', 'B') correspond
    to which glyphs (e.g., 'aries', 'taurus').
    """
    if not os.path.exists(font_path):
        print(f"ERROR: Font file not found at '{font_path}'.")
        return

    try:
        font = ttLib.TTFont(font_path)
        print(f"--- Inspecting Font: {font_path} ---")

        # The 'cmap' table maps character codes to glyph names.
        # We get the best cmap available in the font.
        cmap = font.getBestCmap()

        if not cmap:
            print("ERROR: No suitable 'cmap' table found in the font.")
            return

        print("\nDiscovered Character-to-Glyph-Name Mappings:")

        # Sort the items by character code for a structured output.
        sorted_mappings = sorted(cmap.items())

        for char_code, glyph_name in sorted_mappings:
            # The char_code is an integer (Unicode/ASCII value).
            # We convert it to its character representation.
            character = chr(char_code)

            # We only care about standard, printable ASCII characters,
            # as this is likely how a symbol font is mapped.
            if 32 <= char_code <= 126:
                print(f"  - Character: '{character}' (Code: {hex(char_code)}) -> Glyph Name: '{glyph_name}'")

        print("\n--- Inspection Complete ---")

    except Exception as e:
        print(f"An error occurred while inspecting the font: {e}")

if __name__ == "__main__":
    # Define the path to the astrological font
    astro_font_file = os.path.join("fonts", "EnigmaAstrology2.ttf")
    inspect_font_mapping(astro_font_file)
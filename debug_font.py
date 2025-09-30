import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase

def debug_font_loader():
    """
    A diagnostic script to load a specific font file and print its family name(s)
    as understood by the Qt Font Database. This helps verify that the font is
    being loaded correctly and reveals the exact name to use in the application.
    """
    # It's necessary to have a QApplication instance to use QFontDatabase
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    font_filename = "EnigmaAstrology2.ttf"
    font_path = os.path.join("fonts", font_filename)

    print(f"--- Font Debugger Initialized ---")
    print(f"Attempting to load font from: '{font_path}'")

    if not os.path.exists(font_path):
        print(f"ERROR: Font file not found at the specified path.")
        print(f"Please ensure '{font_filename}' is in the 'fonts' directory.")
        return

    # Add the font to the application's font database
    font_id = QFontDatabase.addApplicationFont(font_path)

    if font_id == -1:
        print(f"CRITICAL ERROR: Failed to load font '{font_path}'.")
        print("This could mean the file is corrupted, not a valid font, or there are permission issues.")
    else:
        # Retrieve the family names associated with the loaded font
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            print(f"SUCCESS: Font loaded successfully!")
            print(f"Registered Font Families for '{font_filename}':")
            for i, family in enumerate(families):
                print(f"  - Family {i+1}: '{family}'")
            print("\nRECOMMENDATION: Use the first family name in this list in your QFont constructor.")
        else:
            print(f"ERROR: Font was loaded (ID: {font_id}) but no family names were found.")
            print("This is unusual and may indicate a problem with the font file itself.")

    print(f"--- Font Debugger Finished ---")

if __name__ == "__main__":
    debug_font_loader()
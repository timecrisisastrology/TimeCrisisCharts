import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase

# Set the Qt platform plugin to 'offscreen' to avoid display errors in headless environments.
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

def debug_font_loading():
    """
    A diagnostic script to verify the loading of the custom astrological font
    and to report the exact family name that PyQt discovers.
    """
    print("--- Font Debugger ---")

    # This is necessary to initialize the Qt application environment,
    # which is required for QFontDatabase to work correctly.
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    font_filename = "EnigmaAstrology2.ttf"
    font_path = os.path.join("fonts", font_filename)

    if not os.path.exists(font_path):
        print(f"ERROR: Font file not found at '{font_path}'.")
        print("Please ensure the 'fonts' directory exists and contains the required font file.")
        return

    print(f"Attempting to load font from: '{font_path}'")

    # Add the font to the application's font database
    font_id = QFontDatabase.addApplicationFont(font_path)

    if font_id == -1:
        print("CRITICAL ERROR: Failed to load the font. It may be corrupt or incompatible.")
        return

    # Retrieve the family names associated with the loaded font
    families = QFontDatabase.applicationFontFamilies(font_id)

    if not families:
        print("ERROR: Font was loaded, but no font family name could be retrieved.")
        print("This often indicates an issue with the font file itself or the operating system's font handling.")
    else:
        print(f"SUCCESS: Font loaded successfully!")
        print(f"Discovered Font Family Name(s): {families}")

        # The first name in the list is typically the one to use
        discovered_name = families[0]
        expected_name = "EnigmaAstrology2"

        print(f"   -> The primary family name is: '{discovered_name}'")

        if discovered_name == expected_name:
            print("   -> Verification successful: The discovered name matches the expected hardcoded name.")
        else:
            print(f"   -> WARNING: The discovered name '{discovered_name}' does not match the expected name '{expected_name}'.")
            print("      If you see rendering issues, update the hardcoded font name in `main_app.py` to match the discovered name.")

    print("--- Debugger Finished ---")

if __name__ == "__main__":
    debug_font_loading()
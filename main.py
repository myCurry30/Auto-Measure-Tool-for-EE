"""Application entry point for PySide6 version."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.main_window import MainWindow


def main():
    """Main application entry point."""
    # Create application
    app = QApplication(sys.argv)
    # High DPI scaling is enabled by default in Qt6/PySide6

    # Create and show main window
    window = MainWindow()
    window.show()

    print("=" * 60)
    print("Nettrix Power Sequence Test Tool V3.0 (PySide6)")
    print("=" * 60)
    print("Features:")
    print("  - PySide6 GUI with macOS-style design")
    print("  - Light/Dark theme support")
    print("  - Rounded cards with shadows")
    print("  - Smooth animations")
    print("  - Tektronix oscilloscope support (MSO4/5/6, DPO7000, DPO5000)")
    print("  - Excel test report generation")
    print("  - Automated screenshot capture")
    print("=" * 60)

    # Run application
    result = app.exec()
    print("\nApplication closed.")
    return result


if __name__ == "__main__":
    sys.exit(main())
"""Application entry point for PySide6 version."""
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from app.main_window import MainWindow


def main():
    """Main application entry point."""
    # Create application
    app = QApplication(sys.argv)

    # Set application icon (title bar + taskbar)
    icon_path = os.path.join(PROJECT_ROOT, "resources", "app_icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Create and show main window
    window = MainWindow()
    window.show()

    print("=" * 50)
    print("  硬件工程师自动化测试工具  V2.0")
    print("  Nettrix  |  liujch2")
    print("=" * 50)
    print("  Scope: MSO4/5/6  DPO7000  DPO5000  (PyVISA)")
    print("  Test:  Sequence + Monotony (P/N toggle)")
    print("  Excel: Signal read, data write, screenshot insert")
    print("  UI:    PySide6  |  Light/Dark  |  Sheet-aware config")
    print("=" * 50)

    # Run application
    result = app.exec()
    print("\nApplication closed.")
    return result


if __name__ == "__main__":
    sys.exit(main())
"""Launch the X4FT GUI application.

Entry point for the graphical user interface.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from x4ft.gui import MainWindow
from x4ft.utils.logger import get_logger

logger = get_logger('gui')


def main():
    """Main entry point for GUI application."""
    logger.info("Starting X4FT GUI...")

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("X4FT")
    app.setOrganizationName("X4FT")

    # Create and show main window
    window = MainWindow()
    window.show()

    logger.info("GUI initialized successfully")

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

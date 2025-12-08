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
from PyQt6.QtGui import QPalette, QColor
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

    # Set Fusion style for modern, consistent appearance
    app.setStyle("Fusion")

    # Create light theme palette
    palette = QPalette()

    # Window colors
    palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))

    # Base colors (for input fields, etc.)
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))

    # Button colors
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))

    # Highlight colors
    palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

    # Disabled colors
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))

    app.setPalette(palette)

    # Create and show main window
    window = MainWindow()
    window.show()

    logger.info("GUI initialized successfully with light theme")

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

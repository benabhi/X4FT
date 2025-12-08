"""Ship information panel widget."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QGridLayout
from PyQt6.QtCore import Qt

from x4ft.database.schema import Ship


class ShipInfoPanel(QWidget):
    """Panel displaying information about the selected ship."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_ship = None
        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Main info group
        info_group = QGroupBox("Ship Information")
        info_layout = QGridLayout()

        # Name
        info_layout.addWidget(QLabel("<b>Name:</b>"), 0, 0)
        self.name_label = QLabel("-")
        info_layout.addWidget(self.name_label, 0, 1)

        # Class
        info_layout.addWidget(QLabel("<b>Class:</b>"), 1, 0)
        self.class_label = QLabel("-")
        info_layout.addWidget(self.class_label, 1, 1)

        # Type
        info_layout.addWidget(QLabel("<b>Type:</b>"), 2, 0)
        self.type_label = QLabel("-")
        info_layout.addWidget(self.type_label, 2, 1)

        # Size
        info_layout.addWidget(QLabel("<b>Size:</b>"), 3, 0)
        self.size_label = QLabel("-")
        info_layout.addWidget(self.size_label, 3, 1)

        # Faction
        info_layout.addWidget(QLabel("<b>Faction:</b>"), 4, 0)
        self.faction_label = QLabel("-")
        info_layout.addWidget(self.faction_label, 4, 1)

        # Price
        info_layout.addWidget(QLabel("<b>Price:</b>"), 5, 0)
        self.price_label = QLabel("-")
        info_layout.addWidget(self.price_label, 5, 1)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Description
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout()
        self.description_label = QLabel("-")
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        desc_layout.addWidget(self.description_label)
        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)

        layout.addStretch()

    def set_ship(self, ship: Ship):
        """Set and display ship information.

        Args:
            ship: Ship object to display
        """
        self.current_ship = ship

        if not ship:
            self._clear()
            return

        # Update labels
        self.name_label.setText(ship.name or "-")
        self.class_label.setText(ship.ship_class or "-")
        self.type_label.setText(ship.ship_type.title() if ship.ship_type else "-")
        self.size_label.setText(ship.size.upper() if ship.size else "-")

        # Faction
        if ship.factions:
            faction_names = ", ".join([f.name for f in ship.factions])
            self.faction_label.setText(faction_names)
        else:
            self.faction_label.setText("-")

        # Price
        if ship.price_avg:
            self.price_label.setText(f"{ship.price_avg:,.0f} Cr")
        else:
            self.price_label.setText("-")

        # Description
        self.description_label.setText(ship.description or "No description available")

    def _clear(self):
        """Clear all displayed information."""
        self.name_label.setText("-")
        self.class_label.setText("-")
        self.type_label.setText("-")
        self.size_label.setText("-")
        self.faction_label.setText("-")
        self.price_label.setText("-")
        self.description_label.setText("-")

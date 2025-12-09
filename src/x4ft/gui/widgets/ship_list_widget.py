"""Ship list widget for selecting ships."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QComboBox, QHBoxLayout
)
from PyQt6.QtCore import pyqtSignal
from sqlalchemy.orm import Session

from x4ft.database.schema import Ship
from x4ft.utils.logger import get_logger

logger = get_logger('ship_list_widget')


class ShipListWidget(QWidget):
    """Widget for displaying and filtering ship list."""

    ship_selected = pyqtSignal(int)  # ship_id

    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.session = session
        self.ships = []
        self._init_ui()
        self._load_ships()

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Ship name...")
        self.search_edit.textChanged.connect(self._filter_ships)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # Size filter
        size_layout = QHBoxLayout()
        size_label = QLabel("Size:")
        self.size_combo = QComboBox()
        self.size_combo.addItems(["All", "XS", "S", "M", "L", "XL"])
        self.size_combo.currentTextChanged.connect(self._filter_ships)
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_combo)
        layout.addLayout(size_layout)

        # Type filter
        type_layout = QHBoxLayout()
        type_label = QLabel("Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItem("All")
        self.type_combo.currentTextChanged.connect(self._filter_ships)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # Ship list
        self.ship_list = QListWidget()
        self.ship_list.itemClicked.connect(self._on_ship_clicked)
        layout.addWidget(self.ship_list)

    def _load_ships(self):
        """Load ships from database."""
        try:
            # Load ships and immediately extract needed data to avoid session issues
            ships_query = self.session.query(Ship).order_by(Ship.name).all()

            # Convert to dict to avoid session detachment issues
            self.ships = []
            types = set()

            for ship in ships_query:
                # Extract data while still in session
                ship_data = {
                    'id': ship.id,
                    'name': ship.name,
                    'size': ship.size,
                    'ship_type': ship.ship_type
                }
                self.ships.append(ship_data)

                if ship.ship_type:
                    types.add(ship.ship_type.title())

            self.type_combo.addItems(sorted(types))

            # Display ships
            self._filter_ships()

        except Exception as e:
            logger.error(f"Error loading ships: {e}", exc_info=True)

    def _filter_ships(self):
        """Filter and display ships based on current filters."""
        try:
            self.ship_list.clear()

            search_text = self.search_edit.text().lower()
            size_filter = self.size_combo.currentText()
            type_filter = self.type_combo.currentText()

            for ship in self.ships:
                # Skip ships without name
                if not ship['name']:
                    continue

                # Apply filters
                if search_text and search_text not in ship['name'].lower():
                    continue

                if size_filter != "All":
                    if not ship['size'] or ship['size'].upper() != size_filter:
                        continue

                if type_filter != "All":
                    if not ship['ship_type'] or ship['ship_type'].title() != type_filter:
                        continue

                # Add to list
                item_text = f"{ship['name']}"
                if ship['ship_type']:
                    item_text += f" ({ship['ship_type'].title()})"

                item = QListWidgetItem(item_text)
                item.setData(256, ship['id'])  # Store ship ID

                self.ship_list.addItem(item)

        except Exception as e:
            logger.error(f"Error filtering ships: {e}", exc_info=True)

    def _on_ship_clicked(self, item: QListWidgetItem):
        """Handle ship selection."""
        if not item:
            return

        ship_id = item.data(256)
        if ship_id:
            self.ship_selected.emit(ship_id)

    def get_selected_ship_id(self) -> int:
        """Get currently selected ship ID."""
        current_item = self.ship_list.currentItem()
        if current_item:
            return current_item.data(256)
        return None

"""Software panel widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QListWidget, QListWidgetItem, QComboBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from sqlalchemy.orm import Session
from typing import Dict, List

from x4ft.database.schema import Equipment
from x4ft.utils.logger import get_logger

logger = get_logger('software_panel')


class SoftwarePanel(QWidget):
    """Panel for selecting installed software modules."""

    software_changed = pyqtSignal()  # Emitted when software selection changes

    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.session = session
        self.installed_software: List[int] = []  # List of equipment IDs
        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)

        # Group box
        group = QGroupBox("Installed Software")
        group_layout = QVBoxLayout()

        # Available software dropdown
        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("Add software:"))

        self.software_combo = QComboBox()
        self.software_combo.addItem("-- Select Software --", None)
        add_layout.addWidget(self.software_combo, 1)

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self._add_software)
        add_layout.addWidget(self.add_button)

        group_layout.addLayout(add_layout)

        # List of installed software
        self.software_list = QListWidget()
        self.software_list.setMaximumHeight(150)
        group_layout.addWidget(self.software_list)

        # Remove button
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self._remove_software)
        self.remove_button.setEnabled(False)
        group_layout.addWidget(self.remove_button)

        self.software_list.itemSelectionChanged.connect(
            lambda: self.remove_button.setEnabled(len(self.software_list.selectedItems()) > 0)
        )

        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()

        # Load available software
        self._load_available_software()

    def _load_available_software(self):
        """Load all available software from database."""
        try:
            software_list = self.session.query(Equipment).filter(
                Equipment.equipment_type == 'software'
            ).order_by(Equipment.name).all()

            self.software_combo.clear()
            self.software_combo.addItem("-- Select Software --", None)

            for sw in software_list:
                # Format: Name MkX - Price
                label = sw.name
                if sw.mk_level and sw.mk_level > 1:
                    label += f" Mk{sw.mk_level}"

                price = sw.price_avg or 0
                label += f" - {price:,.0f} Cr"

                self.software_combo.addItem(label, sw.id)

            logger.info(f"Loaded {len(software_list)} software modules")

        except Exception as e:
            logger.error(f"Error loading software: {e}", exc_info=True)

    def _add_software(self):
        """Add selected software to installed list."""
        software_id = self.software_combo.currentData()
        if not software_id:
            return

        # Check if already installed
        if software_id in self.installed_software:
            logger.debug(f"Software {software_id} already installed")
            return

        try:
            software = self.session.query(Equipment).filter_by(id=software_id).first()
            if not software:
                return

            # Add to list
            self.installed_software.append(software_id)

            # Add to UI list
            label = software.name
            if software.mk_level and software.mk_level > 1:
                label += f" Mk{software.mk_level}"

            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, software_id)
            self.software_list.addItem(item)

            # Emit signal
            self.software_changed.emit()

            logger.info(f"Added software: {label}")

        except Exception as e:
            logger.error(f"Error adding software: {e}", exc_info=True)

    def _remove_software(self):
        """Remove selected software from installed list."""
        selected_items = self.software_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            software_id = item.data(Qt.ItemDataRole.UserRole)
            if software_id in self.installed_software:
                self.installed_software.remove(software_id)

            row = self.software_list.row(item)
            self.software_list.takeItem(row)

            logger.info(f"Removed software: {item.text()}")

        # Emit signal
        self.software_changed.emit()

    def get_installed_software(self) -> List[int]:
        """Get list of installed software IDs.

        Returns:
            List of equipment IDs
        """
        return self.installed_software.copy()

    def get_software_info(self) -> Dict:
        """Get software information for cost breakdown.

        Returns:
            Dict with items list and total cost
        """
        items = []
        total_cost = 0

        try:
            for software_id in self.installed_software:
                software = self.session.query(Equipment).filter_by(id=software_id).first()
                if software:
                    name = software.name
                    if software.mk_level and software.mk_level > 1:
                        name += f" Mk{software.mk_level}"

                    cost = software.price_avg or 0
                    total_cost += cost

                    items.append({
                        'name': name,
                        'cost': cost
                    })

        except Exception as e:
            logger.error(f"Error getting software info: {e}", exc_info=True)

        return {
            'items': items,
            'total_cost': total_cost
        }

    def clear(self):
        """Clear all installed software."""
        self.installed_software.clear()
        self.software_list.clear()
        self.software_changed.emit()

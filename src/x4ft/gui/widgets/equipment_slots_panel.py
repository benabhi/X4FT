"""Equipment slots panel widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox,
    QGroupBox, QScrollArea, QFormLayout
)
from PyQt6.QtCore import pyqtSignal
from sqlalchemy.orm import Session
from typing import Dict, List

from x4ft.database.schema import Ship, ShipSlot, Equipment
from x4ft.utils.logger import get_logger

logger = get_logger('equipment_slots_panel')


class EquipmentSlotsPanel(QWidget):
    """Panel for managing equipment in ship slots."""

    equipment_changed = pyqtSignal(str, int)  # slot_name, equipment_id (or None)

    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.session = session
        self.current_ship = None
        self.slot_combos: Dict[str, QComboBox] = {}
        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        # Scroll area for slots
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)

        self.empty_label = QLabel("Selecciona una nave para ver sus slots de equipamiento")
        self.main_layout.addWidget(self.empty_label)
        self.main_layout.addStretch()

        scroll.setWidget(self.container)

        layout = QVBoxLayout(self)
        layout.addWidget(scroll)

    def set_ship(self, ship: Ship):
        """Set current ship and display its slots.

        Args:
            ship: Ship object
        """
        self.current_ship = ship
        self.slot_combos.clear()

        # Clear existing layout
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not ship or not ship.slots:
            self.empty_label = QLabel("Esta nave no tiene slots de equipamiento")
            self.main_layout.addWidget(self.empty_label)
            self.main_layout.addStretch()
            return

        # Group slots by type
        slots_by_type = {}
        for slot in ship.slots:
            slot_type = slot.slot_type or "other"
            if slot_type not in slots_by_type:
                slots_by_type[slot_type] = []
            slots_by_type[slot_type].append(slot)

        # Create groups
        type_names = {
            'weapon': 'Armas',
            'turret': 'Torretas',
            'shield': 'Escudos',
            'engine': 'Motor',
            'thruster': 'Propulsores'
        }

        for slot_type in ['weapon', 'turret', 'shield', 'engine', 'thruster']:
            if slot_type in slots_by_type:
                group = self._create_slot_group(
                    type_names.get(slot_type, slot_type.title()),
                    slots_by_type[slot_type]
                )
                self.main_layout.addWidget(group)

        self.main_layout.addStretch()

    def _create_slot_group(self, group_name: str, slots: List[ShipSlot]) -> QGroupBox:
        """Create a group for slot type.

        Args:
            group_name: Display name for group
            slots: List of slots in this group

        Returns:
            QGroupBox with slot controls
        """
        group = QGroupBox(group_name)
        layout = QFormLayout()

        for slot in sorted(slots, key=lambda s: s.slot_index or 0):
            # Create combo box for this slot
            combo = QComboBox()
            combo.addItem("(Vacío)", None)

            # Load compatible equipment
            compatible_equipment = self._get_compatible_equipment(slot)
            for eq in compatible_equipment:
                label = eq.name
                if eq.mk_level:
                    label += f" Mk{eq.mk_level}"
                combo.addItem(label, eq.id)

            # Connect signal
            combo.currentIndexChanged.connect(
                lambda idx, s=slot.slot_name, c=combo: self._on_equipment_changed(s, c)
            )

            # Store combo
            self.slot_combos[slot.slot_name] = combo

            # Add to layout
            slot_label = f"{slot.slot_name}:"
            if slot.slot_size:
                slot_label = f"{slot.slot_size.upper()} - {slot_label}"

            layout.addRow(slot_label, combo)

        group.setLayout(layout)
        return group

    def _get_compatible_equipment(self, slot: ShipSlot) -> List[Equipment]:
        """Get equipment compatible with slot.

        Args:
            slot: Ship slot

        Returns:
            List of compatible equipment
        """
        try:
            query = self.session.query(Equipment)

            # Filter by type
            if slot.slot_type:
                if slot.slot_type == 'turret':
                    # Turrets can accept both turrets and weapons
                    query = query.filter(Equipment.equipment_type.in_(['turret', 'weapon']))
                else:
                    query = query.filter(Equipment.equipment_type == slot.slot_type)

            # Filter by size if specified
            if slot.slot_size:
                query = query.filter(Equipment.size == slot.slot_size)

            return query.order_by(Equipment.name).all()

        except Exception as e:
            logger.error(f"Error loading compatible equipment: {e}", exc_info=True)
            return []

    def _on_equipment_changed(self, slot_name: str, combo: QComboBox):
        """Handle equipment selection change.

        Args:
            slot_name: Name of the slot
            combo: Combo box that changed
        """
        equipment_id = combo.currentData()
        self.equipment_changed.emit(slot_name, equipment_id or 0)

    def set_equipment(self, slot_name: str, equipment_id: int):
        """Set equipment for a slot programmatically.

        Args:
            slot_name: Name of the slot
            equipment_id: Equipment ID to set
        """
        if slot_name not in self.slot_combos:
            return

        combo = self.slot_combos[slot_name]
        for i in range(combo.count()):
            if combo.itemData(i) == equipment_id:
                combo.setCurrentIndex(i)
                return

    def get_equipment_config(self) -> Dict[str, int]:
        """Get current equipment configuration.

        Returns:
            Dict mapping slot names to equipment IDs
        """
        config = {}
        for slot_name, combo in self.slot_combos.items():
            equipment_id = combo.currentData()
            if equipment_id:
                config[slot_name] = equipment_id
        return config

    def clear(self):
        """Clear all equipment selections."""
        for combo in self.slot_combos.values():
            combo.setCurrentIndex(0)  # Set to "(Vacío)"

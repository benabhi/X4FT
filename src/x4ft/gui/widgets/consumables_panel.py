"""Consumables panel widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTreeWidget,
    QTreeWidgetItem, QComboBox, QPushButton, QSpinBox, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt
from sqlalchemy.orm import Session
from typing import Dict, List

from x4ft.database.schema import Equipment


class ConsumablesPanel(QWidget):
    """Panel for managing consumables inventory (missiles, drones, etc.)."""

    consumables_changed = pyqtSignal()  # Emitted when consumables change

    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.session = session
        self.consumables_data = {}  # {equipment_id: quantity}
        self.available_consumables = {}  # {type: [Equipment]}
        self._init_ui()
        self._load_consumables()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)

        group = QGroupBox("Consumables")
        group_layout = QVBoxLayout()

        # Add consumable controls
        add_layout = QHBoxLayout()

        add_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("Missiles", "missile")
        self.type_combo.addItem("Countermeasures", "countermeasure")
        self.type_combo.addItem("Deployables", "deployable")
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        add_layout.addWidget(self.type_combo)

        add_layout.addWidget(QLabel("Item:"))
        self.item_combo = QComboBox()
        self.item_combo.setMinimumWidth(200)
        add_layout.addWidget(self.item_combo, 1)

        add_layout.addWidget(QLabel("Qty:"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(9999)
        self.quantity_spin.setValue(1)
        add_layout.addWidget(self.quantity_spin)

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self._add_consumable)
        add_layout.addWidget(self.add_button)

        group_layout.addLayout(add_layout)

        # Tree widget for consumables list
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Consumable", "Quantity", "Unit Cost", "Total Cost"])
        self.tree.setColumnWidth(0, 250)
        self.tree.setColumnWidth(1, 80)
        self.tree.setColumnWidth(2, 100)
        self.tree.setAlternatingRowColors(True)
        group_layout.addWidget(self.tree)

        # Buttons
        button_layout = QHBoxLayout()

        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self._remove_selected)
        button_layout.addWidget(self.remove_button)

        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self._clear_all)
        button_layout.addWidget(self.clear_button)

        button_layout.addStretch()
        group_layout.addLayout(button_layout)

        # Total cost label
        self.total_label = QLabel("<b>Total Consumables Cost: 0 Cr</b>")
        self.total_label.setStyleSheet("color: #006400; padding: 5px;")
        group_layout.addWidget(self.total_label)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def _load_consumables(self):
        """Load available consumables from database."""
        try:
            # Load missiles
            missiles = self.session.query(Equipment).filter(
                Equipment.equipment_type == 'missile'
            ).order_by(Equipment.name).all()
            self.available_consumables['missile'] = missiles

            # Load countermeasures
            countermeasures = self.session.query(Equipment).filter(
                Equipment.equipment_type == 'countermeasure'
            ).order_by(Equipment.name).all()
            self.available_consumables['countermeasure'] = countermeasures

            # Load deployables (drones, mines, etc.)
            deployables = self.session.query(Equipment).filter(
                Equipment.equipment_type.in_(['deployable', 'drone'])
            ).order_by(Equipment.name).all()
            self.available_consumables['deployable'] = deployables

            # Populate item combo for current type
            self._on_type_changed(0)

        except Exception as e:
            print(f"Error loading consumables: {e}")

    def _on_type_changed(self, index: int):
        """Handle consumable type change."""
        self.item_combo.clear()

        consumable_type = self.type_combo.currentData()
        items = self.available_consumables.get(consumable_type, [])

        for item in items:
            label = item.name
            if item.mk_level:
                label += f" Mk{item.mk_level}"

            # Add price to label
            price = item.price_avg or 0
            label += f" - {price:,.0f} Cr"

            self.item_combo.addItem(label, item.id)

    def _add_consumable(self):
        """Add consumable to list."""
        equipment_id = self.item_combo.currentData()
        if not equipment_id:
            return

        quantity = self.quantity_spin.value()

        # Add or update quantity
        if equipment_id in self.consumables_data:
            self.consumables_data[equipment_id] += quantity
        else:
            self.consumables_data[equipment_id] = quantity

        self._update_tree()
        self.consumables_changed.emit()

    def _remove_selected(self):
        """Remove selected consumable from list."""
        current = self.tree.currentItem()
        if not current:
            return

        equipment_id = current.data(0, Qt.ItemDataRole.UserRole)
        if equipment_id in self.consumables_data:
            del self.consumables_data[equipment_id]
            self._update_tree()
            self.consumables_changed.emit()

    def _clear_all(self):
        """Clear all consumables."""
        self.consumables_data.clear()
        self._update_tree()
        self.consumables_changed.emit()

    def _update_tree(self):
        """Update tree widget with current consumables."""
        self.tree.clear()

        total_cost = 0

        for equipment_id, quantity in self.consumables_data.items():
            # Get equipment details
            equipment = self.session.query(Equipment).filter_by(id=equipment_id).first()
            if not equipment:
                continue

            name = equipment.name
            if equipment.mk_level:
                name += f" Mk{equipment.mk_level}"

            unit_cost = equipment.price_avg or 0
            item_total = unit_cost * quantity

            item = QTreeWidgetItem([
                name,
                str(quantity),
                f"{unit_cost:,.0f} Cr",
                f"{item_total:,.0f} Cr"
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, equipment_id)

            self.tree.addTopLevelItem(item)
            total_cost += item_total

        # Update total label
        self.total_label.setText(f"<b>Total Consumables Cost: {total_cost:,.0f} Cr</b>")

    def get_consumables_info(self) -> Dict:
        """Get consumables information for cost calculation.

        Returns:
            Dictionary with:
                - total_cost: Total cost of all consumables
                - items: List of {equipment_id, name, quantity, unit_cost}
        """
        items = []
        total_cost = 0

        for equipment_id, quantity in self.consumables_data.items():
            equipment = self.session.query(Equipment).filter_by(id=equipment_id).first()
            if not equipment:
                continue

            name = equipment.name
            if equipment.mk_level:
                name += f" Mk{equipment.mk_level}"

            unit_cost = equipment.price_avg or 0
            item_cost = unit_cost * quantity

            items.append({
                'equipment_id': equipment_id,
                'name': name,
                'quantity': quantity,
                'unit_cost': unit_cost,
                'total_cost': item_cost
            })

            total_cost += item_cost

        return {
            'total_cost': total_cost,
            'items': items
        }

    def set_consumables(self, consumables_data: Dict[int, int]):
        """Set consumables programmatically.

        Args:
            consumables_data: Dictionary of {equipment_id: quantity}
        """
        self.consumables_data = consumables_data.copy()
        self._update_tree()

    def clear(self):
        """Clear all consumables."""
        self.consumables_data.clear()
        self._update_tree()

"""Crew panel widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QGroupBox,
    QHBoxLayout, QSpinBox
)
from PyQt6.QtCore import pyqtSignal
from sqlalchemy.orm import Session

from x4ft.database.schema import CrewType


class CrewPanel(QWidget):
    """Panel for selecting crew quantity and type for cost calculation."""

    crew_changed = pyqtSignal(int, int)  # crew_type_id, quantity

    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.session = session
        self.crew_types = []
        self.max_capacity = 0
        self._init_ui()
        self._load_crew_types()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)

        group = QGroupBox("Crew")
        group_layout = QVBoxLayout()

        # Capacity label
        self.capacity_label = QLabel("Capacity: 0 / 0")
        self.capacity_label.setStyleSheet("font-weight: bold;")
        group_layout.addWidget(self.capacity_label)

        # Crew type selector
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Crew Type:"))

        self.type_combo = QComboBox()
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        group_layout.addLayout(type_layout)

        # Quantity selector
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("Quantity:"))

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(0)
        self.quantity_spin.setMaximum(0)
        self.quantity_spin.valueChanged.connect(self._on_quantity_changed)
        quantity_layout.addWidget(self.quantity_spin)
        group_layout.addLayout(quantity_layout)

        # Cost per crew label
        self.unit_cost_label = QLabel("Cost per crew: 0 Cr")
        group_layout.addWidget(self.unit_cost_label)

        # Efficiency info label
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        group_layout.addWidget(self.info_label)

        # Total crew cost label
        self.total_cost_label = QLabel("<b>Total Crew Cost: 0 Cr</b>")
        self.total_cost_label.setStyleSheet("color: #006400;")
        group_layout.addWidget(self.total_cost_label)

        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()

    def _load_crew_types(self):
        """Load crew types from database."""
        try:
            self.crew_types = self.session.query(CrewType).order_by(CrewType.skill_level).all()

            for crew in self.crew_types:
                label = f"{crew.skill_level} \u2605 - {crew.name}"
                self.type_combo.addItem(label, crew.id)

            # Select first item
            if self.crew_types:
                self._update_info()

        except Exception as e:
            self.type_combo.addItem("0 \u2605 - No crew", 0)

    def _on_type_changed(self, index: int):
        """Handle crew type selection change."""
        if index >= 0:
            self._update_info()
            self._emit_change()

    def _on_quantity_changed(self, value: int):
        """Handle quantity change."""
        self._update_capacity_label()
        self._update_total_cost()
        self._emit_change()

    def _update_info(self):
        """Update info labels with crew type details."""
        crew = self._get_selected_crew_type()
        if crew:
            bonus = crew.efficiency_bonus or 0
            cost = crew.price_avg or 0

            # Update unit cost
            self.unit_cost_label.setText(f"Cost per crew: {cost:,.0f} Cr")

            # Update efficiency info
            info = f"<b>Efficiency Bonus:</b> +{bonus:.0f}%<br>"
            if crew.description:
                info += f"<i>{crew.description}</i>"
            self.info_label.setText(info)

            self._update_total_cost()
        else:
            self.unit_cost_label.setText("Cost per crew: 0 Cr")
            self.info_label.setText("No bonuses")
            self.total_cost_label.setText("<b>Total Crew Cost: 0 Cr</b>")

    def _update_capacity_label(self):
        """Update capacity label."""
        current = self.quantity_spin.value()
        self.capacity_label.setText(f"Capacity: {current} / {self.max_capacity}")

    def _update_total_cost(self):
        """Update total crew cost label."""
        crew = self._get_selected_crew_type()
        quantity = self.quantity_spin.value()

        if crew and quantity > 0:
            cost = crew.price_avg or 0
            total = cost * quantity
            self.total_cost_label.setText(f"<b>Total Crew Cost: {total:,.0f} Cr</b>")
        else:
            self.total_cost_label.setText("<b>Total Crew Cost: 0 Cr</b>")

    def _get_selected_crew_type(self) -> CrewType:
        """Get currently selected crew type."""
        crew_id = self.type_combo.currentData()
        if crew_id:
            # Query fresh to avoid detached instance errors
            return self.session.query(CrewType).filter_by(id=crew_id).first()
        return None

    def _emit_change(self):
        """Emit crew change signal."""
        crew = self._get_selected_crew_type()
        crew_id = crew.id if crew else 0
        quantity = self.quantity_spin.value()
        self.crew_changed.emit(crew_id, quantity)

    def set_capacity(self, capacity: int):
        """Set maximum crew capacity from ship.

        Args:
            capacity: Maximum crew capacity
        """
        self.max_capacity = capacity
        self.quantity_spin.setMaximum(capacity)
        self._update_capacity_label()

    def set_crew(self, crew_type_id: int, quantity: int):
        """Set crew type and quantity programmatically.

        Args:
            crew_type_id: ID of crew type
            quantity: Number of crew
        """
        # Set type
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == crew_type_id:
                self.type_combo.setCurrentIndex(i)
                break

        # Set quantity
        self.quantity_spin.setValue(quantity)

    def get_crew_info(self) -> dict:
        """Get current crew information.

        Returns:
            Dictionary with crew_type_id, quantity, unit_cost, total_cost
        """
        crew = self._get_selected_crew_type()
        quantity = self.quantity_spin.value()

        if crew and quantity > 0:
            unit_cost = crew.price_avg or 0
            return {
                'crew_type_id': crew.id,
                'crew_type_name': crew.name,
                'quantity': quantity,
                'unit_cost': unit_cost,
                'total_cost': unit_cost * quantity,
                'skill_level': crew.skill_level
            }
        else:
            return {
                'crew_type_id': 0,
                'crew_type_name': 'None',
                'quantity': 0,
                'unit_cost': 0,
                'total_cost': 0,
                'skill_level': 0
            }

"""Cost breakdown panel widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QTreeWidget, QTreeWidgetItem, QLabel
)
from PyQt6.QtCore import Qt
from typing import Dict, List


class CostPanel(QWidget):
    """Panel displaying itemized cost breakdown."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.costs = {}

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Create group box
        group = QGroupBox("Cost Breakdown")
        group_layout = QVBoxLayout()

        # Info message
        info_label = QLabel("ℹ️ <i>Prices shown are average values and do not account for economic variations during gameplay.</i>")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        group_layout.addWidget(info_label)

        # Create tree widget for itemized costs
        self.cost_tree = QTreeWidget()
        self.cost_tree.setHeaderLabels(["Item", "Cost"])
        self.cost_tree.setColumnWidth(0, 250)
        self.cost_tree.setAlternatingRowColors(True)
        group_layout.addWidget(self.cost_tree)

        # Total cost label
        self.total_label = QLabel("<b>Total Cost: 0 Cr</b>")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.total_label.setStyleSheet("font-size: 14pt; padding: 10px;")
        group_layout.addWidget(self.total_label)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def update_costs(self, cost_breakdown: Dict):
        """Update cost breakdown display.

        Args:
            cost_breakdown: Dictionary with cost information:
                - ship_cost: Base ship cost
                - ship_name: Ship name
                - equipment_costs: List of {name, cost}
                - software_cost: Total software cost
                - software_details: List of {name, cost}
                - crew_cost: Total crew cost
                - crew_details: {type, quantity, unit_cost}
                - consumables_cost: Total consumables cost
                - consumables_details: List of {name, quantity, unit_cost}
                - total: Total cost
        """
        self.costs = cost_breakdown
        self.cost_tree.clear()

        total = 0

        # Ship cost
        ship_cost = cost_breakdown.get('ship_cost', 0)
        ship_name = cost_breakdown.get('ship_name', 'Unknown Ship')
        if ship_cost > 0:
            ship_item = QTreeWidgetItem([ship_name, self._format_cost(ship_cost)])
            ship_item.setForeground(1, Qt.GlobalColor.darkBlue)
            self.cost_tree.addTopLevelItem(ship_item)
            total += ship_cost

        # Equipment costs
        equipment_costs = cost_breakdown.get('equipment_costs', [])
        if equipment_costs:
            equipment_parent = QTreeWidgetItem(["Equipment", ""])
            equipment_parent.setExpanded(True)
            equipment_subtotal = 0

            for item in equipment_costs:
                name = item.get('name', 'Unknown')
                cost = item.get('cost', 0)
                slot = item.get('slot', '')

                label = f"{name}"
                if slot:
                    label = f"[{slot}] {name}"

                child = QTreeWidgetItem([label, self._format_cost(cost)])
                equipment_parent.addChild(child)
                equipment_subtotal += cost

            equipment_parent.setText(1, self._format_cost(equipment_subtotal))
            equipment_parent.setForeground(1, Qt.GlobalColor.darkGreen)
            self.cost_tree.addTopLevelItem(equipment_parent)
            total += equipment_subtotal

        # Software costs
        software_cost = cost_breakdown.get('software_cost', 0)
        software_details = cost_breakdown.get('software_details', [])
        if software_cost > 0:
            software_parent = QTreeWidgetItem(["Software", self._format_cost(software_cost)])
            software_parent.setForeground(1, Qt.GlobalColor.darkYellow)
            software_parent.setExpanded(True)

            for item in software_details:
                name = item.get('name', 'Unknown')
                cost = item.get('cost', 0)
                child = QTreeWidgetItem([name, self._format_cost(cost)])
                software_parent.addChild(child)

            self.cost_tree.addTopLevelItem(software_parent)
            total += software_cost

        # Crew cost
        crew_cost = cost_breakdown.get('crew_cost', 0)
        crew_details = cost_breakdown.get('crew_details', {})
        if crew_cost > 0:
            crew_parent = QTreeWidgetItem(["Crew", self._format_cost(crew_cost)])
            crew_parent.setForeground(1, Qt.GlobalColor.darkMagenta)

            # Add crew details if available
            if crew_details:
                crew_type = crew_details.get('type', 'Unknown')
                quantity = crew_details.get('quantity', 0)
                unit_cost = crew_details.get('unit_cost', 0)
                detail_text = f"{quantity}x {crew_type} @ {self._format_cost(unit_cost)} each"
                crew_parent.addChild(QTreeWidgetItem([detail_text, ""]))
                crew_parent.setExpanded(True)

            self.cost_tree.addTopLevelItem(crew_parent)
            total += crew_cost

        # Consumables cost
        consumables_cost = cost_breakdown.get('consumables_cost', 0)
        consumables_details = cost_breakdown.get('consumables_details', [])
        if consumables_cost > 0:
            consumables_parent = QTreeWidgetItem(["Consumables", self._format_cost(consumables_cost)])
            consumables_parent.setForeground(1, Qt.GlobalColor.darkCyan)
            consumables_parent.setExpanded(True)

            for item in consumables_details:
                name = item.get('name', 'Unknown')
                quantity = item.get('quantity', 0)
                unit_cost = item.get('unit_cost', 0)
                item_cost = quantity * unit_cost

                label = f"{quantity}x {name} @ {self._format_cost(unit_cost)} each"
                child = QTreeWidgetItem([label, self._format_cost(item_cost)])
                consumables_parent.addChild(child)

            self.cost_tree.addTopLevelItem(consumables_parent)
            total += consumables_cost

        # Update total
        self.total_label.setText(f"<b>Total Cost: {self._format_cost(total)}</b>")

    def _format_cost(self, cost: float) -> str:
        """Format cost value with thousands separator.

        Args:
            cost: Cost value

        Returns:
            Formatted string (e.g., "1,234,567 Cr")
        """
        return f"{cost:,.0f} Cr"

    def clear(self):
        """Clear all cost information."""
        self.cost_tree.clear()
        self.total_label.setText("<b>Total Cost: 0 Cr</b>")
        self.costs = {}

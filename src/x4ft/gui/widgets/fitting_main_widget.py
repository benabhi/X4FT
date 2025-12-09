"""Main fitting widget that assembles all components."""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QTabWidget,
    QPushButton, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from sqlalchemy.orm import Session

from x4ft.gui.widgets.ship_list_widget import ShipListWidget
from x4ft.gui.widgets.ship_info_panel import ShipInfoPanel
from x4ft.gui.widgets.equipment_slots_panel import EquipmentSlotsPanel
from x4ft.gui.widgets.modifications_panel import ModificationsPanel
from x4ft.gui.widgets.crew_panel import CrewPanel
from x4ft.gui.widgets.consumables_panel import ConsumablesPanel
from x4ft.gui.widgets.stats_panel import StatsPanel
from x4ft.gui.widgets.cost_panel import CostPanel
from x4ft.core.fitting_manager import FittingManager
from x4ft.database.schema import Ship
from x4ft.utils.logger import get_logger

logger = get_logger('fitting_main_widget')


class FittingMainWidget(QWidget):
    """Main widget for ship fitting interface."""

    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.session = session
        self.fitting_manager = FittingManager(session)
        self.current_ship = None

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """Initialize the user interface."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # === LEFT SIDE: Sidebar with tabs ===
        sidebar_tabs = QTabWidget()

        # Ships tab
        self.ship_list = ShipListWidget(self.session)
        sidebar_tabs.addTab(self.ship_list, "Ships")

        # Builds tab (placeholder for now)
        builds_widget = QWidget()
        sidebar_tabs.addTab(builds_widget, "Builds")

        splitter.addWidget(sidebar_tabs)

        # === RIGHT SIDE: Main content (horizontal split) ===
        # Create horizontal splitter for two columns
        content_splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- LEFT COLUMN: Configuration Tabs ---
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Tab widget for different sections
        self.tabs = QTabWidget()

        # Tab 1: Ship Info
        self.ship_info_panel = ShipInfoPanel()
        self.tabs.addTab(self.ship_info_panel, "Ship Info")

        # Tab 2: Equipment
        self.equipment_panel = EquipmentSlotsPanel(self.session)
        self.tabs.addTab(self.equipment_panel, "Equipment")

        # Tab 3: Modifications
        self.modifications_panel = ModificationsPanel(self.session)
        self.tabs.addTab(self.modifications_panel, "Modifications")

        # Tab 4: Crew & Consumables (with scroll area)
        from PyQt6.QtWidgets import QScrollArea
        crew_consumables_scroll = QScrollArea()
        crew_consumables_scroll.setWidgetResizable(True)
        crew_consumables_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        crew_consumables_widget = QWidget()
        crew_consumables_layout = QVBoxLayout(crew_consumables_widget)
        crew_consumables_layout.setSpacing(10)

        self.crew_panel = CrewPanel(self.session)
        self.consumables_panel = ConsumablesPanel(self.session)

        crew_consumables_layout.addWidget(self.crew_panel)
        crew_consumables_layout.addWidget(self.consumables_panel)
        crew_consumables_layout.addStretch()

        crew_consumables_scroll.setWidget(crew_consumables_widget)
        self.tabs.addTab(crew_consumables_scroll, "Crew & Consumables")

        # Tab 5: Cost
        self.cost_panel = CostPanel()
        self.tabs.addTab(self.cost_panel, "Cost Breakdown")

        # Add tabs to layout
        left_layout.addWidget(self.tabs)

        # Save build button fixed at bottom
        self.save_button = QPushButton("💾 Save Build")
        self.save_button.clicked.connect(self._save_build)
        left_layout.addWidget(self.save_button)

        content_splitter.addWidget(left_column)

        # --- RIGHT COLUMN: Stats ---
        self.stats_panel = StatsPanel()
        content_splitter.addWidget(self.stats_panel)

        # Set initial splitter sizes (50% each column)
        content_splitter.setSizes([500, 500])

        splitter.addWidget(content_splitter)

        # Set sidebar vs content ratio (25% sidebar, 75% content)
        splitter.setSizes([250, 750])

        main_layout.addWidget(splitter)

    def _connect_signals(self):
        """Connect widget signals."""
        # Ship selection
        self.ship_list.ship_selected.connect(self._on_ship_selected)

        # Equipment changes
        self.equipment_panel.equipment_changed.connect(self._on_equipment_changed)

        # Modifications changes
        self.modifications_panel.mod_changed.connect(self._on_mod_changed)

        # Crew changes
        self.crew_panel.crew_changed.connect(self._on_crew_changed)

        # Consumables changes
        self.consumables_panel.consumables_changed.connect(self._on_consumables_changed)

    def _on_ship_selected(self, ship_id: int):
        """Handle ship selection.

        Args:
            ship_id: ID of selected ship
        """
        try:
            # Load ship
            ship = self.session.query(Ship).filter_by(id=ship_id).first()
            if not ship:
                logger.error(f"Ship {ship_id} not found")
                return

            self.current_ship = ship

            # Update fitting manager
            self.fitting_manager.set_ship(ship_id)

            # Update panels
            self.ship_info_panel.set_ship(ship)
            self.equipment_panel.set_ship(ship)
            self.crew_panel.set_capacity(ship.crew_capacity or 0)
            self.crew_panel.set_crew(0, 0)  # Reset crew
            self.consumables_panel.clear()

            # Update stats with base values
            stats = self.fitting_manager.get_calculated_stats()
            self.stats_panel.update_stats(stats, stats)  # Base stats = current stats initially

            # Update costs
            self._update_costs()

            logger.info(f"Loaded ship: {ship.name}")

        except Exception as e:
            logger.error(f"Error loading ship: {e}", exc_info=True)

    def _on_equipment_changed(self, slot_name: str, equipment_id: int):
        """Handle equipment change.

        Args:
            slot_name: Name of the slot
            equipment_id: ID of equipment (or 0 for empty)
        """
        try:
            # Update fitting manager
            eq_id = equipment_id if equipment_id > 0 else None
            self.fitting_manager.set_equipment(slot_name, eq_id)

            # Recalculate and update stats
            self._update_stats()

            # Update costs
            self._update_costs()

        except Exception as e:
            logger.error(f"Error changing equipment: {e}", exc_info=True)

    def _on_mod_changed(self, category: str, mod_id: int):
        """Handle modification change.

        Args:
            category: Mod category (engine, weapon, shield, ship)
            mod_id: ID of modification (or None for no mod)
        """
        try:
            # Update fitting manager
            self.fitting_manager.set_modification(category, mod_id)

            # Recalculate and update stats
            self._update_stats()

            # Update costs
            self._update_costs()

        except Exception as e:
            logger.error(f"Error changing modification: {e}", exc_info=True)

    def _on_crew_changed(self, crew_type_id: int, quantity: int):
        """Handle crew change.

        Args:
            crew_type_id: ID of crew type
            quantity: Number of crew
        """
        try:
            # Update costs (crew changes affect cost but not stats)
            self._update_costs()

        except Exception as e:
            logger.error(f"Error changing crew: {e}", exc_info=True)

    def _on_consumables_changed(self):
        """Handle consumables change."""
        try:
            # Update costs
            self._update_costs()

        except Exception as e:
            logger.error(f"Error changing consumables: {e}", exc_info=True)

    def _update_stats(self):
        """Recalculate and update stats display."""
        stats = self.fitting_manager.get_calculated_stats()

        # Get base stats for comparison
        base_stats = {
            'hull_base': self.current_ship.hull_max if self.current_ship else 0,
            'cargo_capacity': self.current_ship.cargo_capacity if self.current_ship else 0,
        }

        self.stats_panel.update_stats(stats, base_stats)

    def _update_costs(self):
        """Update cost breakdown display."""
        if not self.current_ship:
            return

        try:
            # Ship cost
            ship_cost = self.current_ship.price_avg or 0

            # Equipment costs
            equipment_costs = self.equipment_panel.get_equipment_costs()

            # Crew costs
            crew_info = self.crew_panel.get_crew_info()
            crew_cost = crew_info.get('total_cost', 0)
            crew_details = {
                'type': crew_info.get('crew_type_name', 'None'),
                'quantity': crew_info.get('quantity', 0),
                'unit_cost': crew_info.get('unit_cost', 0)
            }

            # Consumables costs
            consumables_info = self.consumables_panel.get_consumables_info()
            consumables_cost = consumables_info.get('total_cost', 0)
            consumables_details = [
                {
                    'name': item['name'],
                    'quantity': item['quantity'],
                    'unit_cost': item['unit_cost']
                }
                for item in consumables_info.get('items', [])
            ]

            # Build cost breakdown
            cost_breakdown = {
                'ship_cost': ship_cost,
                'ship_name': self.current_ship.name,
                'equipment_costs': equipment_costs,
                'crew_cost': crew_cost,
                'crew_details': crew_details,
                'consumables_cost': consumables_cost,
                'consumables_details': consumables_details,
                'total': ship_cost + sum(e['cost'] for e in equipment_costs) + crew_cost + consumables_cost
            }

            self.cost_panel.update_costs(cost_breakdown)

        except Exception as e:
            logger.error(f"Error updating costs: {e}", exc_info=True)

    def _save_build(self):
        """Save current build."""
        if not self.current_ship:
            QMessageBox.warning(self, "No Ship", "Please select a ship first.")
            return

        try:
            # Ask for build name
            name, ok = QInputDialog.getText(
                self,
                "Save Build",
                "Enter a name for this build:"
            )

            if not ok or not name:
                return

            # Ask for description (optional)
            description, ok = QInputDialog.getText(
                self,
                "Save Build",
                "Enter a description (optional):"
            )

            if not ok:
                description = ""

            # Save build using fitting manager
            build = self.fitting_manager.save_build(name, description)

            if build:
                QMessageBox.information(
                    self,
                    "Build Saved",
                    f"Build '{name}' has been saved successfully!"
                )
                logger.info(f"Build saved: {name}")
            else:
                QMessageBox.warning(
                    self,
                    "Save Failed",
                    "Failed to save build. Please try again."
                )

        except Exception as e:
            logger.error(f"Error saving build: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Error saving build: {str(e)}"
            )

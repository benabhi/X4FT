"""Main fitting widget that assembles all components."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QTabWidget
from PyQt6.QtCore import Qt
from sqlalchemy.orm import Session

from x4ft.gui.widgets.ship_list_widget import ShipListWidget
from x4ft.gui.widgets.ship_info_panel import ShipInfoPanel
from x4ft.gui.widgets.equipment_slots_panel import EquipmentSlotsPanel
from x4ft.gui.widgets.crew_panel import CrewPanel
from x4ft.gui.widgets.stats_panel import StatsPanel
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
        sidebar_tabs.addTab(self.ship_list, "Naves")

        # Builds tab (placeholder for now)
        builds_widget = QWidget()
        sidebar_tabs.addTab(builds_widget, "Builds")

        splitter.addWidget(sidebar_tabs)

        # === RIGHT SIDE: Main content ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Create vertical splitter for upper/lower panels
        content_splitter = QSplitter(Qt.Orientation.Vertical)

        # --- Upper Panel: Configuration ---
        upper_widget = QWidget()
        upper_layout = QHBoxLayout(upper_widget)
        upper_layout.setContentsMargins(5, 5, 5, 5)

        # Left column: Ship info + Crew
        left_column = QWidget()
        left_column_layout = QVBoxLayout(left_column)
        self.ship_info_panel = ShipInfoPanel()
        self.crew_panel = CrewPanel(self.session)
        left_column_layout.addWidget(self.ship_info_panel)
        left_column_layout.addWidget(self.crew_panel)
        left_column_layout.addStretch()

        # Right column: Equipment slots
        self.equipment_panel = EquipmentSlotsPanel(self.session)

        upper_layout.addWidget(left_column, 1)
        upper_layout.addWidget(self.equipment_panel, 2)

        content_splitter.addWidget(upper_widget)

        # --- Lower Panel: Stats ---
        self.stats_panel = StatsPanel()
        content_splitter.addWidget(self.stats_panel)

        # Set initial splitter sizes (60% upper, 40% lower)
        content_splitter.setSizes([600, 400])

        right_layout.addWidget(content_splitter)
        splitter.addWidget(right_widget)

        # Set sidebar vs content ratio (25% sidebar, 75% content)
        splitter.setSizes([250, 750])

        main_layout.addWidget(splitter)

    def _connect_signals(self):
        """Connect widget signals."""
        # Ship selection
        self.ship_list.ship_selected.connect(self._on_ship_selected)

        # Equipment changes
        self.equipment_panel.equipment_changed.connect(self._on_equipment_changed)

        # Crew changes
        self.crew_panel.crew_level_changed.connect(self._on_crew_changed)

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
            self.crew_panel.set_level(0)  # Reset crew

            # Update stats with base values
            stats = self.fitting_manager.get_calculated_stats()
            self.stats_panel.update_stats(stats, stats)  # Base stats = current stats initially

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

        except Exception as e:
            logger.error(f"Error changing equipment: {e}", exc_info=True)

    def _on_crew_changed(self, level: int):
        """Handle crew level change.

        Args:
            level: New crew level
        """
        try:
            # Update fitting manager
            self.fitting_manager.set_crew_level(level)

            # Recalculate and update stats
            self._update_stats()

        except Exception as e:
            logger.error(f"Error changing crew: {e}", exc_info=True)

    def _update_stats(self):
        """Recalculate and update stats display."""
        stats = self.fitting_manager.get_calculated_stats()

        # Get base stats for comparison
        base_stats = {
            'hull_base': self.current_ship.hull_max if self.current_ship else 0,
            'cargo_capacity': self.current_ship.cargo_capacity if self.current_ship else 0,
        }

        self.stats_panel.update_stats(stats, base_stats)

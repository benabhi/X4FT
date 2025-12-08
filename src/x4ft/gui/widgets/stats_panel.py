"""Ship statistics panel widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt
from typing import Dict


class StatsPanel(QWidget):
    """Panel displaying calculated ship statistics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_stats = {}
        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface."""
        # Create scroll area for stats
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Container widget
        container = QWidget()
        layout = QVBoxLayout(container)

        # Defense stats
        defense_group = self._create_defense_group()
        layout.addWidget(defense_group)

        # Propulsion stats
        propulsion_group = self._create_propulsion_group()
        layout.addWidget(propulsion_group)

        # Armament stats
        armament_group = self._create_armament_group()
        layout.addWidget(armament_group)

        # Storage stats
        storage_group = self._create_storage_group()
        layout.addWidget(storage_group)

        # Crew stats
        crew_group = self._create_crew_group()
        layout.addWidget(crew_group)

        layout.addStretch()

        scroll.setWidget(container)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

    def _create_defense_group(self) -> QGroupBox:
        """Create defense statistics group."""
        group = QGroupBox("Defense")
        layout = QGridLayout()

        # Hull
        layout.addWidget(QLabel("<b>Hull:</b>"), 0, 0)
        self.hull_label = QLabel("0")
        layout.addWidget(self.hull_label, 0, 1)

        # Shield capacity
        layout.addWidget(QLabel("<b>Shield Capacity:</b>"), 1, 0)
        self.shield_capacity_label = QLabel("0 MJ")
        layout.addWidget(self.shield_capacity_label, 1, 1)

        # Shield recharge
        layout.addWidget(QLabel("<b>Shield Recharge:</b>"), 2, 0)
        self.shield_recharge_label = QLabel("0 MJ/s")
        layout.addWidget(self.shield_recharge_label, 2, 1)

        # Shield delay
        layout.addWidget(QLabel("<b>Recharge Delay:</b>"), 3, 0)
        self.shield_delay_label = QLabel("0 s")
        layout.addWidget(self.shield_delay_label, 3, 1)

        group.setLayout(layout)
        return group

    def _create_propulsion_group(self) -> QGroupBox:
        """Create propulsion statistics group."""
        group = QGroupBox("Propulsion")
        layout = QGridLayout()

        # Velocity
        layout.addWidget(QLabel("<b>Velocity:</b>"), 0, 0)
        self.velocity_label = QLabel("0 m/s")
        layout.addWidget(self.velocity_label, 0, 1)

        # Boost velocity
        layout.addWidget(QLabel("<b>Boost Velocity:</b>"), 1, 0)
        self.boost_velocity_label = QLabel("0 m/s")
        layout.addWidget(self.boost_velocity_label, 1, 1)

        # Travel velocity
        layout.addWidget(QLabel("<b>Travel Velocity:</b>"), 2, 0)
        self.travel_velocity_label = QLabel("0 m/s")
        layout.addWidget(self.travel_velocity_label, 2, 1)

        # Forward thrust
        layout.addWidget(QLabel("<b>Forward Thrust:</b>"), 3, 0)
        self.forward_thrust_label = QLabel("0 N")
        layout.addWidget(self.forward_thrust_label, 3, 1)

        # Strafe thrust
        layout.addWidget(QLabel("<b>Strafe Thrust:</b>"), 4, 0)
        self.strafe_thrust_label = QLabel("0 N")
        layout.addWidget(self.strafe_thrust_label, 4, 1)

        group.setLayout(layout)
        return group

    def _create_armament_group(self) -> QGroupBox:
        """Create armament statistics group."""
        group = QGroupBox("Armament")
        layout = QGridLayout()

        # DPS hull
        layout.addWidget(QLabel("<b>Hull DPS:</b>"), 0, 0)
        self.dps_hull_label = QLabel("0")
        layout.addWidget(self.dps_hull_label, 0, 1)

        # DPS shield
        layout.addWidget(QLabel("<b>Shield DPS:</b>"), 1, 0)
        self.dps_shield_label = QLabel("0")
        layout.addWidget(self.dps_shield_label, 1, 1)

        # Weapon count
        layout.addWidget(QLabel("<b>Weapons:</b>"), 2, 0)
        self.weapon_count_label = QLabel("0")
        layout.addWidget(self.weapon_count_label, 2, 1)

        # Turret count
        layout.addWidget(QLabel("<b>Turrets:</b>"), 3, 0)
        self.turret_count_label = QLabel("0")
        layout.addWidget(self.turret_count_label, 3, 1)

        group.setLayout(layout)
        return group

    def _create_storage_group(self) -> QGroupBox:
        """Create storage statistics group."""
        group = QGroupBox("Storage")
        layout = QGridLayout()

        # Cargo
        layout.addWidget(QLabel("<b>Cargo:</b>"), 0, 0)
        self.cargo_label = QLabel("0")
        layout.addWidget(self.cargo_label, 0, 1)

        # Missiles
        layout.addWidget(QLabel("<b>Missiles:</b>"), 1, 0)
        self.missile_storage_label = QLabel("0")
        layout.addWidget(self.missile_storage_label, 1, 1)

        # Drones
        layout.addWidget(QLabel("<b>Drones:</b>"), 2, 0)
        self.drone_storage_label = QLabel("0")
        layout.addWidget(self.drone_storage_label, 2, 1)

        # Units
        layout.addWidget(QLabel("<b>Units:</b>"), 3, 0)
        self.unit_storage_label = QLabel("0")
        layout.addWidget(self.unit_storage_label, 3, 1)

        group.setLayout(layout)
        return group

    def _create_crew_group(self) -> QGroupBox:
        """Create crew statistics group."""
        group = QGroupBox("Crew")
        layout = QGridLayout()

        # Capacity
        layout.addWidget(QLabel("<b>Capacity:</b>"), 0, 0)
        self.crew_capacity_label = QLabel("0")
        layout.addWidget(self.crew_capacity_label, 0, 1)

        # Level
        layout.addWidget(QLabel("<b>Level:</b>"), 1, 0)
        self.crew_level_label = QLabel("0 ")
        layout.addWidget(self.crew_level_label, 1, 1)

        # Efficiency
        layout.addWidget(QLabel("<b>Efficiency:</b>"), 2, 0)
        self.crew_efficiency_label = QLabel("+0%")
        layout.addWidget(self.crew_efficiency_label, 2, 1)

        group.setLayout(layout)
        return group

    def update_stats(self, stats: Dict, base_stats: Dict = None):
        """Update displayed statistics.

        Args:
            stats: Current calculated stats
            base_stats: Optional base stats for comparison
        """
        if base_stats:
            self.base_stats = base_stats

        # Defense
        hull = stats.get('hull_total', 0)
        self.hull_label.setText(f"{hull:,.0f}")
        self._maybe_color_label(self.hull_label, hull, self.base_stats.get('hull_base', hull))

        shield_cap = stats.get('shield_capacity', 0)
        self.shield_capacity_label.setText(f"{shield_cap:,.0f} MJ")

        shield_rech = stats.get('shield_recharge', 0)
        self.shield_recharge_label.setText(f"{shield_rech:,.1f} MJ/s")

        shield_delay = stats.get('shield_delay', 0)
        self.shield_delay_label.setText(f"{shield_delay:.1f} s")

        # Propulsion
        vel = stats.get('velocity', 0)
        self.velocity_label.setText(f"{vel:,.0f} m/s")

        boost_vel = stats.get('boost_velocity', 0)
        self.boost_velocity_label.setText(f"{boost_vel:,.0f} m/s")

        travel_vel = stats.get('travel_velocity', 0)
        self.travel_velocity_label.setText(f"{travel_vel:,.0f} m/s")

        fwd_thrust = stats.get('forward_thrust', 0)
        self.forward_thrust_label.setText(f"{fwd_thrust:,.0f} N")

        strafe = stats.get('strafe_thrust', 0)
        self.strafe_thrust_label.setText(f"{strafe:,.0f} N")

        # Armament
        dps_hull = stats.get('dps_hull_total', 0)
        self.dps_hull_label.setText(f"{dps_hull:,.0f}")

        dps_shield = stats.get('dps_shield_total', 0)
        self.dps_shield_label.setText(f"{dps_shield:,.0f}")

        weapon_count = stats.get('weapon_count', 0)
        self.weapon_count_label.setText(str(weapon_count))

        turret_count = stats.get('turret_count', 0)
        self.turret_count_label.setText(str(turret_count))

        # Storage
        cargo = stats.get('cargo_capacity', 0)
        self.cargo_label.setText(f"{cargo:,.0f}")
        self._maybe_color_label(self.cargo_label, cargo, self.base_stats.get('cargo_capacity', cargo))

        missiles = stats.get('missile_storage', 0)
        self.missile_storage_label.setText(str(missiles))

        drones = stats.get('drone_storage', 0)
        self.drone_storage_label.setText(str(drones))

        units = stats.get('unit_storage', 0)
        self.unit_storage_label.setText(str(units))

        # Crew
        crew_cap = stats.get('crew_capacity', 0)
        self.crew_capacity_label.setText(str(crew_cap))

        crew_level = stats.get('crew_level', 0)
        self.crew_level_label.setText(f"{crew_level} ")

        crew_eff = stats.get('crew_efficiency', 0)
        self.crew_efficiency_label.setText(f"+{crew_eff:.0f}%")

    def _maybe_color_label(self, label: QLabel, current: float, base: float):
        """Color label based on comparison to base value.

        Args:
            label: Label widget to color
            current: Current value
            base: Base value for comparison
        """
        if current > base:
            label.setStyleSheet("color: green;")
        elif current < base:
            label.setStyleSheet("color: red;")
        else:
            label.setStyleSheet("")

    def clear(self):
        """Clear all statistics."""
        self.update_stats({}, {})

"""Fitting manager for ship build calculations.

Manages ship builds, equipment configuration, and stat calculations.
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from x4ft.database.schema import (
    Ship, ShipSlot, Equipment, WeaponStats, ShieldStats,
    EngineStats, ThrusterStats, EquipmentMod, CrewType, Build
)
from x4ft.utils.logger import get_logger

logger = get_logger('fitting_manager')


class FittingManager:
    """Manages ship fitting configurations and calculates modified stats.

    This class maintains the current build state and provides methods
    for configuring equipment, modifications, and calculating resulting
    ship statistics.
    """

    def __init__(self, session: Session):
        """Initialize the fitting manager.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.logger = logger

        # Current build state
        self.current_ship: Optional[Ship] = None
        self.equipment_config: Dict[str, int] = {}  # slot_name -> equipment_id
        self.mods_config: Dict[str, int] = {}  # category -> mod_id
        self.consumables_config: List[Dict] = []  # [{type, id, quantity}]
        self.crew_level: int = 0

        # Cached calculated stats
        self._cached_stats: Optional[Dict] = None
        self._stats_dirty = True

    def set_ship(self, ship_id: int) -> bool:
        """Set the current ship for fitting.

        Args:
            ship_id: Database ID of the ship

        Returns:
            True if ship was loaded successfully
        """
        try:
            self.current_ship = self.session.query(Ship).filter_by(id=ship_id).first()
            if not self.current_ship:
                self.logger.error(f"Ship with ID {ship_id} not found")
                return False

            # Reset configuration
            self.equipment_config = {}
            self.mods_config = {}
            self.consumables_config = []
            self.crew_level = 0
            self._stats_dirty = True

            self.logger.info(f"Loaded ship: {self.current_ship.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error loading ship: {e}", exc_info=True)
            return False

    def set_equipment(self, slot_name: str, equipment_id: Optional[int]) -> bool:
        """Set equipment for a specific slot.

        Args:
            slot_name: Name of the slot (e.g., "con_weapon_01")
            equipment_id: Equipment ID to install, or None to clear slot

        Returns:
            True if equipment was set successfully
        """
        if not self.current_ship:
            self.logger.warning("No ship loaded")
            return False

        try:
            # Validate slot exists
            slot = next((s for s in self.current_ship.slots if s.slot_name == slot_name), None)
            if not slot:
                self.logger.error(f"Slot {slot_name} not found on current ship")
                return False

            # If clearing slot
            if equipment_id is None:
                if slot_name in self.equipment_config:
                    del self.equipment_config[slot_name]
                self._stats_dirty = True
                return True

            # Validate equipment exists and is compatible
            equipment = self.session.query(Equipment).filter_by(id=equipment_id).first()
            if not equipment:
                self.logger.error(f"Equipment with ID {equipment_id} not found")
                return False

            if not self._is_equipment_compatible(slot, equipment):
                self.logger.warning(f"Equipment {equipment.name} not compatible with slot {slot_name}")
                return False

            # Set equipment
            self.equipment_config[slot_name] = equipment_id
            self._stats_dirty = True
            self.logger.debug(f"Equipped {equipment.name} in {slot_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error setting equipment: {e}", exc_info=True)
            return False

    def set_modification(self, category: str, mod_id: Optional[int]) -> bool:
        """Set modification for a category.

        Args:
            category: Mod category (engine, weapon, shield, chassis)
            mod_id: Mod ID to apply, or None to clear

        Returns:
            True if mod was set successfully
        """
        if not self.current_ship:
            self.logger.warning("No ship loaded")
            return False

        try:
            # If clearing mod
            if mod_id is None:
                if category in self.mods_config:
                    del self.mods_config[category]
                self._stats_dirty = True
                return True

            # Validate mod exists
            mod = self.session.query(EquipmentMod).filter_by(id=mod_id).first()
            if not mod:
                self.logger.error(f"Mod with ID {mod_id} not found")
                return False

            if mod.mod_category != category:
                self.logger.error(f"Mod category mismatch: {mod.mod_category} != {category}")
                return False

            # Set mod
            self.mods_config[category] = mod_id
            self._stats_dirty = True
            self.logger.debug(f"Applied mod {mod.name} to {category}")
            return True

        except Exception as e:
            self.logger.error(f"Error setting modification: {e}", exc_info=True)
            return False

    def set_crew_level(self, level: int) -> bool:
        """Set crew skill level.

        Args:
            level: Crew level (0-5 stars)

        Returns:
            True if level was set successfully
        """
        if not 0 <= level <= 5:
            self.logger.error(f"Invalid crew level: {level}")
            return False

        self.crew_level = level
        self._stats_dirty = True
        return True

    def add_consumable(self, consumable_type: str, consumable_id: int, quantity: int) -> bool:
        """Add or update consumable in configuration.

        Args:
            consumable_type: Type (missile, mine, drone, etc.)
            consumable_id: Consumable ID
            quantity: Quantity to add

        Returns:
            True if consumable was added
        """
        # Find existing entry
        for entry in self.consumables_config:
            if entry['type'] == consumable_type and entry['id'] == consumable_id:
                entry['quantity'] = quantity
                return True

        # Add new entry
        self.consumables_config.append({
            'type': consumable_type,
            'id': consumable_id,
            'quantity': quantity
        })
        return True

    def remove_consumable(self, consumable_type: str, consumable_id: int) -> bool:
        """Remove consumable from configuration.

        Args:
            consumable_type: Type (missile, mine, drone, etc.)
            consumable_id: Consumable ID

        Returns:
            True if consumable was removed
        """
        self.consumables_config = [
            entry for entry in self.consumables_config
            if not (entry['type'] == consumable_type and entry['id'] == consumable_id)
        ]
        return True

    def get_calculated_stats(self) -> Dict:
        """Calculate and return current ship stats.

        Returns:
            Dictionary of calculated statistics
        """
        if not self.current_ship:
            return {}

        if not self._stats_dirty and self._cached_stats:
            return self._cached_stats

        stats = self._calculate_stats()
        self._cached_stats = stats
        self._stats_dirty = False

        return stats

    def _calculate_stats(self) -> Dict:
        """Internal method to calculate ship stats.

        Returns:
            Dictionary of all calculated stats
        """
        if not self.current_ship:
            return {}

        ship = self.current_ship

        # Start with base ship stats
        stats = {
            # Defense
            'hull_base': ship.hull_max or 0,
            'hull_total': ship.hull_max or 0,
            'shield_capacity': 0.0,
            'shield_recharge': 0.0,
            'shield_delay': 0.0,

            # Storage
            'cargo_capacity': ship.cargo_capacity or 0,
            'missile_storage': ship.missile_storage or 0,
            'drone_storage': ship.drone_storage or 0,
            'unit_storage': ship.unit_storage or 0,

            # Crew
            'crew_capacity': ship.crew_capacity or 0,
            'crew_level': self.crew_level,
            'crew_efficiency': 0.0,

            # Propulsion (base values)
            'forward_thrust': 0.0,
            'reverse_thrust': 0.0,
            'boost_thrust': 0.0,
            'boost_duration': 0.0,
            'travel_thrust': 0.0,
            'strafe_thrust': 0.0,

            # Calculated velocities
            'velocity': 0.0,
            'boost_velocity': 0.0,
            'travel_velocity': 0.0,

            # Armament
            'dps_hull_total': 0.0,
            'dps_shield_total': 0.0,
            'weapon_count': 0,
            'turret_count': 0,

            # Equipment lists
            'equipped_weapons': [],
            'equipped_turrets': [],
            'equipped_shields': [],
            'equipped_engine': None,
            'equipped_thrusters': None,
        }

        # Apply equipment stats
        for slot_name, equipment_id in self.equipment_config.items():
            equipment = self.session.query(Equipment).filter_by(id=equipment_id).first()
            if not equipment:
                continue

            # Add equipment hull to ship hull
            if equipment.hull:
                stats['hull_total'] += equipment.hull

            # Process by equipment type
            if equipment.equipment_type in ['weapon', 'turret']:
                self._apply_weapon_stats(equipment, stats)
            elif equipment.equipment_type == 'shield':
                self._apply_shield_stats(equipment, stats)
            elif equipment.equipment_type == 'engine':
                self._apply_engine_stats(equipment, stats)
            elif equipment.equipment_type == 'thruster':
                self._apply_thruster_stats(equipment, stats)

        # Apply modifications
        self._apply_modifications(stats)

        # Apply crew bonuses
        self._apply_crew_bonuses(stats)

        # Calculate velocities
        self._calculate_velocities(stats, ship)

        return stats

    def _apply_weapon_stats(self, equipment: Equipment, stats: Dict):
        """Apply weapon or turret stats to totals."""
        if not equipment.weapon_stats:
            return

        ws = equipment.weapon_stats

        # Add to DPS totals
        if ws.dps_hull:
            stats['dps_hull_total'] += ws.dps_hull
        if ws.dps_shield:
            stats['dps_shield_total'] += ws.dps_shield

        # Count weapons/turrets
        if equipment.equipment_type == 'weapon':
            stats['weapon_count'] += 1
            stats['equipped_weapons'].append({
                'name': equipment.name,
                'dps_hull': ws.dps_hull or 0,
                'dps_shield': ws.dps_shield or 0,
                'range': ws.range_max or 0
            })
        elif equipment.equipment_type == 'turret':
            stats['turret_count'] += 1
            stats['equipped_turrets'].append({
                'name': equipment.name,
                'dps_hull': ws.dps_hull or 0,
                'dps_shield': ws.dps_shield or 0,
                'range': ws.range_max or 0
            })

    def _apply_shield_stats(self, equipment: Equipment, stats: Dict):
        """Apply shield stats to totals."""
        if not equipment.shield_stats:
            return

        ss = equipment.shield_stats

        # Add to shield totals
        if ss.capacity:
            stats['shield_capacity'] += ss.capacity
        if ss.recharge_rate:
            stats['shield_recharge'] += ss.recharge_rate

        # Use max delay
        if ss.recharge_delay and ss.recharge_delay > stats['shield_delay']:
            stats['shield_delay'] = ss.recharge_delay

        stats['equipped_shields'].append({
            'name': equipment.name,
            'capacity': ss.capacity or 0,
            'recharge': ss.recharge_rate or 0
        })

    def _apply_engine_stats(self, equipment: Equipment, stats: Dict):
        """Apply engine stats."""
        if not equipment.engine_stats:
            return

        es = equipment.engine_stats

        stats['forward_thrust'] = es.forward_thrust or 0
        stats['reverse_thrust'] = es.reverse_thrust or 0
        stats['boost_thrust'] = es.boost_thrust or 0
        stats['boost_duration'] = es.boost_duration or 0
        stats['travel_thrust'] = es.travel_thrust or 0

        stats['equipped_engine'] = {
            'name': equipment.name,
            'forward_thrust': es.forward_thrust or 0,
            'boost_thrust': es.boost_thrust or 0,
            'travel_thrust': es.travel_thrust or 0
        }

    def _apply_thruster_stats(self, equipment: Equipment, stats: Dict):
        """Apply thruster stats."""
        if not equipment.thruster_stats:
            return

        ts = equipment.thruster_stats
        stats['strafe_thrust'] = ts.thrust_strafe or 0

        stats['equipped_thrusters'] = {
            'name': equipment.name,
            'strafe': ts.thrust_strafe or 0,
            'pitch': ts.thrust_pitch or 0,
            'yaw': ts.thrust_yaw or 0,
            'roll': ts.thrust_roll or 0
        }

    def _apply_modifications(self, stats: Dict):
        """Apply equipment modifications to stats."""
        for category, mod_id in self.mods_config.items():
            mod = self.session.query(EquipmentMod).filter_by(id=mod_id).first()
            if not mod:
                continue

            # Use average of min/max effect
            multiplier = (mod.effect_min + mod.effect_max) / 2.0

            # Apply based on category and type
            if category == 'engine':
                if mod.mod_type in ['thrust', 'forwardthrust']:
                    stats['forward_thrust'] *= multiplier
                elif mod.mod_type == 'boostthrust':
                    stats['boost_thrust'] *= multiplier
                elif mod.mod_type == 'travelthrust':
                    stats['travel_thrust'] *= multiplier

            elif category == 'weapon':
                if mod.mod_type == 'damage':
                    stats['dps_hull_total'] *= multiplier
                    stats['dps_shield_total'] *= multiplier

            elif category == 'shield':
                if mod.mod_type == 'capacity':
                    stats['shield_capacity'] *= multiplier
                elif mod.mod_type == 'rechargerate':
                    stats['shield_recharge'] *= multiplier

            elif category in ['ship', 'chassis']:
                if mod.mod_type == 'hull':
                    stats['hull_total'] *= multiplier
                elif mod.mod_type == 'cargo':
                    stats['cargo_capacity'] *= multiplier

    def _apply_crew_bonuses(self, stats: Dict):
        """Apply crew skill bonuses."""
        if self.crew_level == 0:
            return

        # Get crew type for this level
        crew = self.session.query(CrewType).filter_by(skill_level=self.crew_level).first()
        if not crew or not crew.efficiency_bonus:
            return

        stats['crew_efficiency'] = crew.efficiency_bonus

        # Apply efficiency bonus to relevant stats
        bonus = 1.0 + (crew.efficiency_bonus / 100.0)

        # Crew affects: weapons, shields, engines
        stats['dps_hull_total'] *= bonus
        stats['dps_shield_total'] *= bonus
        stats['shield_recharge'] *= bonus
        stats['forward_thrust'] *= bonus
        stats['boost_thrust'] *= bonus
        stats['travel_thrust'] *= bonus

    def _calculate_velocities(self, stats: Dict, ship: Ship):
        """Calculate velocity from thrust and drag.

        Formula from X4 Wiki: Speed = thrust / drag
        Mass affects acceleration, not top speed.
        """
        # Using forward drag as baseline
        drag = ship.forward_drag or 0.01  # Avoid division by zero

        if stats['forward_thrust'] > 0:
            stats['velocity'] = stats['forward_thrust'] / drag

        if stats['boost_thrust'] > 0:
            stats['boost_velocity'] = stats['boost_thrust'] / drag

        if stats['travel_thrust'] > 0:
            stats['travel_velocity'] = stats['travel_thrust'] / drag

    def _is_equipment_compatible(self, slot: ShipSlot, equipment: Equipment) -> bool:
        """Check if equipment is compatible with slot.

        Args:
            slot: Ship slot
            equipment: Equipment to check

        Returns:
            True if compatible
        """
        # Check slot size compatibility (equipment size must match slot size)
        # NOTE: Ship size is IRRELEVANT - slots determine compatibility
        # A medium ship can have small, medium, and large slots
        if slot.slot_size and equipment.size:
            if slot.slot_size.lower() != equipment.size.lower():
                self.logger.debug(f"Slot size mismatch: slot={slot.slot_size}, equipment={equipment.size}")
                return False

        # Check type compatibility
        if slot.slot_type != equipment.equipment_type:
            # Special case: turret slots can accept weapons
            if not (slot.slot_type == 'turret' and equipment.equipment_type == 'weapon'):
                return False

        # Check tags (if equipment has tags requirement)
        if equipment.tags:
            equipment_tags = set(equipment.tags.split(','))
            slot_tags = set(slot.tags.split(',')) if slot.tags else set()

            # Equipment must have at least one matching tag
            if not equipment_tags.intersection(slot_tags):
                return False

        return True

    def save_build(self, name: str, description: str = "") -> Optional[Build]:
        """Save current configuration as a build.

        Args:
            name: Build name
            description: Optional description

        Returns:
            Created Build object or None on error
        """
        if not self.current_ship:
            self.logger.error("No ship loaded")
            return None

        try:
            now = datetime.now()

            # Create build
            build = Build(
                name=name,
                description=description,
                ship_id=self.current_ship.id,
                created_at=now,
                updated_at=now,
                equipment_config=json.dumps(self.equipment_config),
                mods_config=json.dumps(self.mods_config),
                consumables_config=json.dumps(self.consumables_config),
                crew_level=self.crew_level,
                stats_snapshot=json.dumps(self.get_calculated_stats())
            )

            self.session.add(build)
            self.session.commit()

            self.logger.info(f"Saved build: {name}")
            return build

        except Exception as e:
            self.logger.error(f"Error saving build: {e}", exc_info=True)
            self.session.rollback()
            return None

    def load_build(self, build_id: int) -> bool:
        """Load a saved build configuration.

        Args:
            build_id: Build ID to load

        Returns:
            True if build was loaded successfully
        """
        try:
            build = self.session.query(Build).filter_by(id=build_id).first()
            if not build:
                self.logger.error(f"Build {build_id} not found")
                return False

            # Load ship
            if not self.set_ship(build.ship_id):
                return False

            # Load configuration
            self.equipment_config = json.loads(build.equipment_config) if build.equipment_config else {}
            self.mods_config = json.loads(build.mods_config) if build.mods_config else {}
            self.consumables_config = json.loads(build.consumables_config) if build.consumables_config else []
            self.crew_level = build.crew_level or 0

            self._stats_dirty = True

            self.logger.info(f"Loaded build: {build.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error loading build: {e}", exc_info=True)
            return False

    def update_build(self, build_id: int) -> bool:
        """Update an existing build with current configuration.

        Args:
            build_id: Build ID to update

        Returns:
            True if build was updated successfully
        """
        try:
            build = self.session.query(Build).filter_by(id=build_id).first()
            if not build:
                self.logger.error(f"Build {build_id} not found")
                return False

            # Update configuration
            build.updated_at = datetime.now()
            build.equipment_config = json.dumps(self.equipment_config)
            build.mods_config = json.dumps(self.mods_config)
            build.consumables_config = json.dumps(self.consumables_config)
            build.crew_level = self.crew_level
            build.stats_snapshot = json.dumps(self.get_calculated_stats())

            self.session.commit()

            self.logger.info(f"Updated build: {build.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating build: {e}", exc_info=True)
            self.session.rollback()
            return False

    def delete_build(self, build_id: int) -> bool:
        """Delete a saved build.

        Args:
            build_id: Build ID to delete

        Returns:
            True if build was deleted successfully
        """
        try:
            build = self.session.query(Build).filter_by(id=build_id).first()
            if not build:
                self.logger.error(f"Build {build_id} not found")
                return False

            self.session.delete(build)
            self.session.commit()

            self.logger.info(f"Deleted build: {build.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting build: {e}", exc_info=True)
            self.session.rollback()
            return False

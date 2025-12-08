"""Comprehensive data integrity verification script."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from x4ft.database.connection import DatabaseManager
from x4ft.database.schema import (
    Ship, ShipSlot, Equipment, WeaponStats, ShieldStats,
    EngineStats, ThrusterStats, ExtractorMetadata
)
from sqlalchemy import func, and_


class DataVerifier:
    """Verifies data integrity in the extraction database."""

    def __init__(self, db_path: str):
        self.db = DatabaseManager(db_path)
        self.errors = []
        self.warnings = []
        self.info = []

    def verify_all(self):
        """Run all verification checks."""
        print("="*80)
        print("X4FT DATA INTEGRITY VERIFICATION")
        print("="*80)
        print()

        with self.db.get_session() as session:
            self.verify_ships(session)
            self.verify_ship_slots(session)
            self.verify_weapons(session)
            self.verify_shields(session)
            self.verify_engines(session)
            self.verify_thrusters(session)
            self.verify_relationships(session)
            self.verify_metadata(session)

        self.print_report()

    def verify_ships(self, session):
        """Verify ship data completeness."""
        print("Verifying Ships...")
        print("-" * 80)

        total = session.query(Ship).count()
        self.info.append(f"Total ships: {total}")

        # Check for missing names
        unnamed = session.query(Ship).filter(
            and_(Ship.name == Ship.macro_name, Ship.basename == "")
        ).count()
        if unnamed > 0:
            self.warnings.append(f"{unnamed} ships have unresolved names")

        # Check for missing critical data
        no_hull = session.query(Ship).filter(Ship.hull_max == 0).count()
        if no_hull > 0:
            self.warnings.append(f"{no_hull} ships have 0 hull")

        no_mass = session.query(Ship).filter(Ship.mass == 0).count()
        if no_mass > 0:
            self.warnings.append(f"{no_mass} ships have 0 mass")

        # Check size distribution
        for size in ['xs', 's', 'm', 'l', 'xl']:
            count = session.query(Ship).filter(Ship.size == size).count()
            self.info.append(f"  Size {size.upper()}: {count} ships")

        # Check for ships with physics data
        with_physics = session.query(Ship).filter(
            Ship.pitch_inertia > 0
        ).count()
        self.info.append(f"Ships with physics data: {with_physics}/{total}")

        # Check for ships with jerk data
        with_jerk = session.query(Ship).filter(
            Ship.jerk_forward_accel > 0
        ).count()
        self.info.append(f"Ships with jerk data: {with_jerk}/{total}")

        print()

    def verify_ship_slots(self, session):
        """Verify ship slot data."""
        print("Verifying Ship Slots...")
        print("-" * 80)

        total_slots = session.query(ShipSlot).count()
        self.info.append(f"Total ship slots: {total_slots}")

        # Check slot type distribution
        slot_types = session.query(
            ShipSlot.slot_type, func.count(ShipSlot.id)
        ).group_by(ShipSlot.slot_type).all()

        for slot_type, count in slot_types:
            self.info.append(f"  {slot_type}: {count} slots")

        # Check for slots without ship
        orphaned = session.query(ShipSlot).filter(
            ~session.query(Ship).filter(Ship.id == ShipSlot.ship_id).exists()
        ).count()
        if orphaned > 0:
            self.errors.append(f"{orphaned} orphaned ship slots (no parent ship)")

        # Ships without slots
        ships_no_slots = session.query(Ship).filter(
            ~session.query(ShipSlot).filter(ShipSlot.ship_id == Ship.id).exists()
        ).count()
        if ships_no_slots > 0:
            self.info.append(f"{ships_no_slots} ships have no slots (may be normal for some ship types)")

        print()

    def verify_weapons(self, session):
        """Verify weapon data completeness."""
        print("Verifying Weapons...")
        print("-" * 80)

        total_weapons = session.query(Equipment).filter(
            Equipment.equipment_type.in_(['weapon', 'turret'])
        ).count()
        self.info.append(f"Total weapons/turrets: {total_weapons}")

        weapons = session.query(Equipment).filter(Equipment.equipment_type == 'weapon').count()
        turrets = session.query(Equipment).filter(Equipment.equipment_type == 'turret').count()
        self.info.append(f"  Weapons: {weapons}")
        self.info.append(f"  Turrets: {turrets}")

        # Check for weapons without stats
        weapons_no_stats = session.query(Equipment).filter(
            Equipment.equipment_type.in_(['weapon', 'turret']),
            ~session.query(WeaponStats).filter(
                WeaponStats.equipment_id == Equipment.id
            ).exists()
        ).count()
        if weapons_no_stats > 0:
            self.errors.append(f"{weapons_no_stats} weapons missing weapon_stats")

        # Check for weapons with damage data
        with_damage = session.query(Equipment).join(WeaponStats).filter(
            Equipment.equipment_type.in_(['weapon', 'turret']),
            WeaponStats.damage_hull > 0
        ).count()
        self.info.append(f"Weapons with damage data: {with_damage}/{total_weapons}")

        # Check for weapons with DPS
        with_dps = session.query(Equipment).join(WeaponStats).filter(
            Equipment.equipment_type.in_(['weapon', 'turret']),
            WeaponStats.dps_hull > 0
        ).count()
        self.info.append(f"Weapons with DPS calculated: {with_dps}/{total_weapons}")

        # Check for weapons with range data
        with_range = session.query(Equipment).join(WeaponStats).filter(
            Equipment.equipment_type.in_(['weapon', 'turret']),
            WeaponStats.range_max > 0
        ).count()
        self.info.append(f"Weapons with range data: {with_range}/{total_weapons}")

        # Size distribution
        for size in ['s', 'm', 'l', 'xl']:
            count = session.query(Equipment).filter(
                Equipment.equipment_type.in_(['weapon', 'turret']),
                Equipment.size == size
            ).count()
            if count > 0:
                self.info.append(f"  Size {size.upper()}: {count} weapons/turrets")

        print()

    def verify_shields(self, session):
        """Verify shield data completeness."""
        print("Verifying Shields...")
        print("-" * 80)

        total = session.query(Equipment).filter(Equipment.equipment_type == 'shield').count()
        self.info.append(f"Total shields: {total}")

        # Check for shields without stats
        no_stats = session.query(Equipment).filter(
            Equipment.equipment_type == 'shield',
            ~session.query(ShieldStats).filter(
                ShieldStats.equipment_id == Equipment.id
            ).exists()
        ).count()
        if no_stats > 0:
            self.errors.append(f"{no_stats} shields missing shield_stats")

        # Check for shields with capacity data
        with_capacity = session.query(Equipment).join(ShieldStats).filter(
            Equipment.equipment_type == 'shield',
            ShieldStats.capacity > 0
        ).count()
        self.info.append(f"Shields with capacity data: {with_capacity}/{total}")

        # Check for shields with recharge data
        with_recharge = session.query(Equipment).join(ShieldStats).filter(
            Equipment.equipment_type == 'shield',
            ShieldStats.recharge_rate > 0
        ).count()
        self.info.append(f"Shields with recharge data: {with_recharge}/{total}")

        # Size distribution
        for size in ['s', 'm', 'l', 'xl']:
            count = session.query(Equipment).filter(
                Equipment.equipment_type == 'shield',
                Equipment.size == size
            ).count()
            if count > 0:
                self.info.append(f"  Size {size.upper()}: {count} shields")

        print()

    def verify_engines(self, session):
        """Verify engine data completeness."""
        print("Verifying Engines...")
        print("-" * 80)

        total = session.query(Equipment).filter(Equipment.equipment_type == 'engine').count()
        self.info.append(f"Total engines: {total}")

        # Check for engines without stats
        no_stats = session.query(Equipment).filter(
            Equipment.equipment_type == 'engine',
            ~session.query(EngineStats).filter(
                EngineStats.equipment_id == Equipment.id
            ).exists()
        ).count()
        if no_stats > 0:
            self.errors.append(f"{no_stats} engines missing engine_stats")

        # Check for engines with thrust data
        with_thrust = session.query(Equipment).join(EngineStats).filter(
            Equipment.equipment_type == 'engine',
            EngineStats.forward_thrust > 0
        ).count()
        self.info.append(f"Engines with thrust data: {with_thrust}/{total}")

        # Check for engines with boost data
        with_boost = session.query(Equipment).join(EngineStats).filter(
            Equipment.equipment_type == 'engine',
            EngineStats.boost_thrust > 0
        ).count()
        self.info.append(f"Engines with boost data: {with_boost}/{total}")

        # Check for engines with travel data
        with_travel = session.query(Equipment).join(EngineStats).filter(
            Equipment.equipment_type == 'engine',
            EngineStats.travel_thrust > 0
        ).count()
        self.info.append(f"Engines with travel data: {with_travel}/{total}")

        # Size distribution
        for size in ['s', 'm', 'l', 'xl']:
            count = session.query(Equipment).filter(
                Equipment.equipment_type == 'engine',
                Equipment.size == size
            ).count()
            if count > 0:
                self.info.append(f"  Size {size.upper()}: {count} engines")

        print()

    def verify_thrusters(self, session):
        """Verify thruster data completeness."""
        print("Verifying Thrusters...")
        print("-" * 80)

        total = session.query(Equipment).filter(Equipment.equipment_type == 'thruster').count()
        self.info.append(f"Total thrusters: {total}")

        # Check for thrusters without stats
        no_stats = session.query(Equipment).filter(
            Equipment.equipment_type == 'thruster',
            ~session.query(ThrusterStats).filter(
                ThrusterStats.equipment_id == Equipment.id
            ).exists()
        ).count()
        if no_stats > 0:
            self.errors.append(f"{no_stats} thrusters missing thruster_stats")

        # Check for thrusters with strafe data
        with_strafe = session.query(Equipment).join(ThrusterStats).filter(
            Equipment.equipment_type == 'thruster',
            ThrusterStats.thrust_strafe > 0
        ).count()
        self.info.append(f"Thrusters with strafe data: {with_strafe}/{total}")

        # Size distribution
        for size in ['s', 'm', 'l', 'xl']:
            count = session.query(Equipment).filter(
                Equipment.equipment_type == 'thruster',
                Equipment.size == size
            ).count()
            if count > 0:
                self.info.append(f"  Size {size.upper()}: {count} thrusters")

        print()

    def verify_relationships(self, session):
        """Verify database relationships are consistent."""
        print("Verifying Relationships...")
        print("-" * 80)

        # Check ship -> slots relationship
        ships = session.query(Ship).all()
        for ship in ships[:10]:  # Sample first 10
            slot_count = len(ship.slots)
            if slot_count > 100:  # Sanity check
                self.warnings.append(f"Ship {ship.name} has {slot_count} slots (seems excessive)")

        # Check equipment -> stats relationships
        equipment_list = session.query(Equipment).all()
        for eq in equipment_list[:10]:  # Sample first 10
            if eq.equipment_type == 'weapon' or eq.equipment_type == 'turret':
                if not eq.weapon_stats:
                    self.warnings.append(f"Weapon {eq.name} missing weapon_stats")
            elif eq.equipment_type == 'shield':
                if not eq.shield_stats:
                    self.warnings.append(f"Shield {eq.name} missing shield_stats")
            elif eq.equipment_type == 'engine':
                if not eq.engine_stats:
                    self.warnings.append(f"Engine {eq.name} missing engine_stats")
            elif eq.equipment_type == 'thruster':
                if not eq.thruster_stats:
                    self.warnings.append(f"Thruster {eq.name} missing thruster_stats")

        self.info.append("Relationship verification complete")
        print()

    def verify_metadata(self, session):
        """Verify extraction metadata."""
        print("Verifying Metadata...")
        print("-" * 80)

        metadata = session.query(ExtractorMetadata).all()
        for meta in metadata:
            self.info.append(f"{meta.key}: {meta.value}")

        required_keys = ['last_extraction_time', 'schema_version', 'ship_count']
        existing_keys = [m.key for m in metadata]
        for key in required_keys:
            if key not in existing_keys:
                self.warnings.append(f"Missing metadata key: {key}")

        print()

    def print_report(self):
        """Print verification report."""
        print()
        print("="*80)
        print("VERIFICATION REPORT")
        print("="*80)
        print()

        # Print info
        if self.info:
            print("INFORMATION:")
            print("-" * 80)
            for msg in self.info:
                print(f"  [INFO] {msg}")
            print()

        # Print warnings
        if self.warnings:
            print("WARNINGS:")
            print("-" * 80)
            for msg in self.warnings:
                print(f"  [WARN] {msg}")
            print()

        # Print errors
        if self.errors:
            print("ERRORS:")
            print("-" * 80)
            for msg in self.errors:
                print(f"  [ERROR] {msg}")
            print()

        # Summary
        print("="*80)
        print("SUMMARY:")
        print(f"  Info: {len(self.info)}")
        print(f"  Warnings: {len(self.warnings)}")
        print(f"  Errors: {len(self.errors)}")
        print()

        if self.errors:
            print("[FAIL] VERIFICATION FAILED - Please fix errors before proceeding")
            return False
        elif self.warnings:
            print("[PASS] VERIFICATION PASSED WITH WARNINGS - Review warnings")
            return True
        else:
            print("[OK] VERIFICATION PASSED - All data looks good!")
            return True


if __name__ == "__main__":
    db_path = Path(__file__).parent.parent / "data" / "x4ft.db"

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print("Please run extract_game_data.py first")
        sys.exit(1)

    verifier = DataVerifier(str(db_path))
    success = verifier.verify_all()

    sys.exit(0 if success else 1)

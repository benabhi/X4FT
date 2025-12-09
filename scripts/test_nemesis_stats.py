"""Test script to verify Nemesis Sentinel stats calculation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from x4ft.database.connection import DatabaseManager
from x4ft.database.schema import Ship, Equipment, ShieldStats, EngineStats, ThrusterStats, WeaponStats
from x4ft.core.fitting_manager import FittingManager

db = DatabaseManager('data/x4ft.db')

with db.get_session() as session:
    # Get Nemesis Sentinel
    ship = session.query(Ship).filter_by(id=90).first()

    print("="*80)
    print("NEMESIS SENTINEL - BASE STATS")
    print("="*80)
    print(f"Hull: {ship.hull_max:,}")
    print(f"Mass: {ship.mass}")
    print(f"Forward Drag: {ship.forward_drag}")
    print(f"Cargo: {ship.cargo_capacity}")
    print(f"Crew Capacity: {ship.crew_capacity}")
    print(f"Missile Storage: {ship.missile_storage}")
    print()

    # Expected equipment (from user):
    # 1x PAR Combat Engine M Mk3
    # 1x Combat Thruster M Mk3
    # 2x PAR Shield Generator M Mk3
    # 5x Torpedo Launcher M Mk2
    # 2x PAR Beam Turret M Mk1

    print("="*80)
    print("SEARCHING FOR EQUIPMENT")
    print("="*80)

    # Find PAR Combat Engine M Mk3
    print("\n1. PAR Combat Engine M Mk3:")
    engine = session.query(Equipment).join(EngineStats).filter(
        Equipment.equipment_type == 'engine',
        Equipment.faction_prefix == 'PAR',
        Equipment.name.like('%Combat%'),
        Equipment.size == 'm',
        Equipment.mk_level == 3
    ).first()
    if engine:
        print(f"   Found: {engine.name}")
        print(f"   Forward: {engine.engine_stats.forward_thrust}")
        print(f"   Boost: {engine.engine_stats.boost_thrust}")
        print(f"   Travel: {engine.engine_stats.travel_thrust}")
    else:
        print("   NOT FOUND - searching alternatives...")
        engines = session.query(Equipment).join(EngineStats).filter(
            Equipment.equipment_type == 'engine',
            Equipment.size == 'm'
        ).limit(5).all()
        for e in engines:
            print(f"      {e.faction_prefix} {e.name} Mk{e.mk_level}")

    # Find Combat Thruster M Mk3
    print("\n2. Combat Thruster M Mk3:")
    thruster = session.query(Equipment).join(ThrusterStats).filter(
        Equipment.equipment_type == 'thruster',
        Equipment.name.like('%Combat%'),
        Equipment.size == 'm',
        Equipment.mk_level == 3
    ).first()
    if thruster:
        print(f"   Found: {thruster.name}")
        print(f"   Strafe: {thruster.thruster_stats.thrust_strafe}")
    else:
        print("   NOT FOUND")

    # Find PAR Shield M Mk3
    print("\n3. PAR Shield Generator M Mk3:")
    shield = session.query(Equipment).join(ShieldStats).filter(
        Equipment.equipment_type == 'shield',
        Equipment.faction_prefix == 'PAR',
        Equipment.size == 'm',
        Equipment.mk_level == 3
    ).first()
    if shield:
        print(f"   Found: {shield.name}")
        print(f"   Capacity: {shield.shield_stats.capacity}")
        print(f"   Recharge: {shield.shield_stats.recharge_rate}")
        print(f"   Total for 2x: {shield.shield_stats.capacity * 2}")
    else:
        print("   NOT FOUND")

    # Find Torpedo Launcher M Mk2
    print("\n4. Torpedo Launcher M Mk2:")
    torpedo = session.query(Equipment).join(WeaponStats).filter(
        Equipment.equipment_type == 'weapon',
        Equipment.name.like('%Torpedo%'),
        Equipment.size == 'm',
        Equipment.mk_level == 2
    ).first()
    if torpedo:
        print(f"   Found: {torpedo.name}")
        print(f"   DPS: {torpedo.weapon_stats.dps_hull}")
        print(f"   Total for 5x: {torpedo.weapon_stats.dps_hull * 5}")
    else:
        print("   NOT FOUND")

    # Find PAR Beam Turret M Mk1
    print("\n5. PAR Beam Turret M Mk1:")
    turret = session.query(Equipment).join(WeaponStats).filter(
        Equipment.equipment_type == 'turret',
        Equipment.faction_prefix == 'PAR',
        Equipment.name.like('%Beam%'),
        Equipment.size == 'm',
        Equipment.mk_level == 1
    ).first()
    if turret:
        print(f"   Found: {turret.name}")
        print(f"   DPS: {turret.weapon_stats.dps_hull}")
        print(f"   Total for 2x: {turret.weapon_stats.dps_hull * 2}")
    else:
        print("   NOT FOUND")

    print()
    print("="*80)
    print("EXPECTED VALUES FROM GAME")
    print("="*80)
    print("Hull (Casco MJ): 12,000")
    print("Shield (Escudo MJ): 11,040")
    print("Velocity: 400 m/s")
    print("Boost Velocity: 2,287 m/s")
    print("Travel Velocity: 3,072 m/s")
    print("Crew: 7")
    print("Units: 0")
    print("Cargo: 672")
    print("Missiles: 50")
    print("Countermeasures: 100")
    print("Deployables: 8")

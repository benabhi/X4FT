"""Analyze extracted data to identify irrelevant items for fitting tool."""

import sys
from pathlib import Path
from collections import defaultdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from x4ft.database.connection import DatabaseManager
from x4ft.config import X4FTConfig
from sqlalchemy import text


def analyze_ships(session):
    """Analyze ships for station modules and other irrelevant entries."""
    print("\n" + "="*80)
    print("ANALYZING SHIPS")
    print("="*80)

    # Station modules (hull=0 or mass=0)
    result = session.execute(text("""
        SELECT COUNT(*),
               SUM(CASE WHEN hull_max = 0 THEN 1 ELSE 0 END) as zero_hull,
               SUM(CASE WHEN mass = 0 THEN 1 ELSE 0 END) as zero_mass
        FROM ships
    """)).fetchone()

    print(f"\nTotal ships: {result[0]}")
    print(f"  With 0 hull: {result[1]} (likely station modules)")
    print(f"  With 0 mass: {result[2]} (likely station modules)")

    # Ships with specific patterns
    patterns = [
        ('_storage_', 'Storage modules'),
        ('_hab_', 'Habitation modules'),
        ('_prod_', 'Production modules'),
        ('_connection_', 'Connection structures'),
        ('_video_', 'Video macros'),
        ('_virtual_', 'Virtual items'),
    ]

    print("\nShips with suspicious patterns:")
    for pattern, desc in patterns:
        result = session.execute(text(f"""
            SELECT COUNT(*) FROM ships WHERE macro_name LIKE '%{pattern}%'
        """)).fetchone()
        if result[0] > 0:
            print(f"  {desc}: {result[0]}")

    # Recommended exclusions
    result = session.execute(text("""
        SELECT COUNT(*) FROM ships
        WHERE hull_max = 0 OR mass = 0
           OR macro_name LIKE '%_storage_%'
           OR macro_name LIKE '%_hab_%'
           OR macro_name LIKE '%_prod_%'
           OR macro_name LIKE '%_connection_%'
    """)).fetchone()

    print(f"\n[RECOMMENDATION] Exclude {result[0]} station modules/irrelevant ships")


def analyze_weapons(session):
    """Analyze weapons for video macros and other irrelevant entries."""
    print("\n" + "="*80)
    print("ANALYZING WEAPONS/TURRETS")
    print("="*80)

    result = session.execute(text("SELECT COUNT(*) FROM equipment WHERE equipment_type='weapon'")).fetchone()
    print(f"\nTotal weapons/turrets: {result[0]}")

    # Video macros
    result = session.execute(text("""
        SELECT COUNT(*) FROM equipment
        WHERE equipment_type='weapon' AND macro_name LIKE '%_video_%'
    """)).fetchone()
    if result[0] > 0:
        print(f"  Video macros: {result[0]}")

    # Virtual
    result = session.execute(text("""
        SELECT COUNT(*) FROM equipment
        WHERE equipment_type='weapon' AND macro_name LIKE '%_virtual_%'
    """)).fetchone()
    if result[0] > 0:
        print(f"  Virtual macros: {result[0]}")

    # Without stats
    result = session.execute(text("""
        SELECT COUNT(*) FROM equipment e
        LEFT JOIN weapon_stats ws ON e.id = ws.equipment_id
        WHERE e.equipment_type='weapon' AND ws.equipment_id IS NULL
    """)).fetchone()
    if result[0] > 0:
        print(f"  Without stats: {result[0]}")

    # List some examples
    result = session.execute(text("""
        SELECT macro_name FROM equipment
        WHERE equipment_type='weapon' AND (
            macro_name LIKE '%_video_%' OR
            macro_name LIKE '%_virtual_%'
        )
        LIMIT 10
    """)).fetchall()

    if result:
        print("\n  Examples of irrelevant weapons:")
        for row in result:
            print(f"    - {row[0]}")

    # Recommended exclusions
    result = session.execute(text("""
        SELECT COUNT(*) FROM equipment
        WHERE equipment_type='weapon' AND (
            macro_name LIKE '%_video_%' OR
            macro_name LIKE '%_virtual_%'
        )
    """)).fetchone()

    print(f"\n[RECOMMENDATION] Exclude {result[0]} video/virtual weapons")


def analyze_shields(session):
    """Analyze shields for video macros and other irrelevant entries."""
    print("\n" + "="*80)
    print("ANALYZING SHIELDS")
    print("="*80)

    result = session.execute(text("SELECT COUNT(*) FROM equipment WHERE equipment_type='shield'")).fetchone()
    print(f"\nTotal shields: {result[0]}")

    # Video macros
    result = session.execute(text("""
        SELECT COUNT(*) FROM equipment
        WHERE equipment_type='shield' AND macro_name LIKE '%_video_%'
    """)).fetchone()
    if result[0] > 0:
        print(f"  Video macros: {result[0]}")

    # Virtual
    result = session.execute(text("""
        SELECT COUNT(*) FROM equipment
        WHERE equipment_type='shield' AND macro_name LIKE '%_virtual_%'
    """)).fetchone()
    if result[0] > 0:
        print(f"  Virtual macros: {result[0]}")

    # Without stats
    result = session.execute(text("""
        SELECT COUNT(*) FROM equipment e
        LEFT JOIN shield_stats ss ON e.id = ss.equipment_id
        WHERE e.equipment_type='shield' AND ss.equipment_id IS NULL
    """)).fetchone()
    if result[0] > 0:
        print(f"  Without stats: {result[0]}")

    # Recommended exclusions
    result = session.execute(text("""
        SELECT COUNT(*) FROM equipment
        WHERE equipment_type='shield' AND (
            macro_name LIKE '%_video_%' OR
            macro_name LIKE '%_virtual_%'
        )
    """)).fetchone()

    print(f"\n[RECOMMENDATION] Exclude {result[0]} video/virtual shields")


def analyze_engines(session):
    """Analyze engines for video macros and other irrelevant entries."""
    print("\n" + "="*80)
    print("ANALYZING ENGINES")
    print("="*80)

    result = session.execute(text("SELECT COUNT(*) FROM equipment WHERE equipment_type='engine'")).fetchone()
    print(f"\nTotal engines: {result[0]}")

    # Video macros
    result = session.execute(text("""
        SELECT COUNT(*) FROM equipment
        WHERE equipment_type='engine' AND macro_name LIKE '%_video_%'
    """)).fetchone()
    if result[0] > 0:
        print(f"  Video macros: {result[0]}")

    # Virtual
    result = session.execute(text("""
        SELECT COUNT(*) FROM equipment
        WHERE equipment_type='engine' AND macro_name LIKE '%_virtual_%'
    """)).fetchone()
    if result[0] > 0:
        print(f"  Virtual macros: {result[0]}")

    # Without stats
    result = session.execute(text("""
        SELECT COUNT(*) FROM equipment e
        LEFT JOIN engine_stats es ON e.id = es.equipment_id
        WHERE e.equipment_type='engine' AND es.equipment_id IS NULL
    """)).fetchone()
    if result[0] > 0:
        print(f"  Without stats: {result[0]}")

    # Recommended exclusions
    result = session.execute(text("""
        SELECT COUNT(*) FROM equipment
        WHERE equipment_type='engine' AND (
            macro_name LIKE '%_video_%' OR
            macro_name LIKE '%_virtual_%'
        )
    """)).fetchone()

    print(f"\n[RECOMMENDATION] Exclude {result[0]} video/virtual engines")


def analyze_thrusters(session):
    """Analyze thrusters."""
    print("\n" + "="*80)
    print("ANALYZING THRUSTERS")
    print("="*80)

    result = session.execute(text("SELECT COUNT(*) FROM equipment WHERE equipment_type='thruster'")).fetchone()
    print(f"\nTotal thrusters: {result[0]}")

    # Check for issues
    result = session.execute(text("""
        SELECT COUNT(*) FROM equipment
        WHERE equipment_type='thruster' AND (
            macro_name LIKE '%_video_%' OR
            macro_name LIKE '%_virtual_%'
        )
    """)).fetchone()

    if result[0] > 0:
        print(f"  Video/virtual macros: {result[0]}")
        print(f"\n[RECOMMENDATION] Exclude {result[0]} video/virtual thrusters")
    else:
        print("\n[OK] All thrusters appear to be valid")


def main():
    """Main analysis entry point."""
    config = X4FTConfig.load(Path('config.json'))
    db = DatabaseManager(config.database_path)

    print("="*80)
    print("X4FT DATA QUALITY ANALYSIS")
    print("="*80)
    print("\nAnalyzing extracted data for fitting tool relevance...\n")

    with db.get_session() as session:
        analyze_ships(session)
        analyze_weapons(session)
        analyze_shields(session)
        analyze_engines(session)
        analyze_thrusters(session)

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("\nRecommendations for fitting tool:")
    print("  1. EXCLUDE ships with hull=0 or mass=0 (station modules)")
    print("  2. EXCLUDE equipment with '_video_' in macro_name (video macros)")
    print("  3. EXCLUDE equipment with '_virtual_' in macro_name (virtual items)")
    print("  4. EXCLUDE equipment without stats (incomplete data)")
    print("\nThese filters will ensure only player-usable items are in the fitting tool.")
    print("="*80)


if __name__ == "__main__":
    main()

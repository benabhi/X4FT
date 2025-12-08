"""Export weapons data to CSV."""

import sys
import csv
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from x4ft.database.connection import DatabaseManager
from x4ft.config import X4FTConfig
from sqlalchemy import text


def export_weapons_to_csv():
    """Export all weapons to CSV with their stats."""

    # Get project root and config
    project_root = Path(__file__).parent.parent.parent
    config = X4FTConfig.load(project_root / 'config.json')
    db = DatabaseManager(config.database_path)

    # Output to scripts/csv/ folder
    output_file = Path(__file__).parent / 'weapons.csv'

    with db.get_session() as session:
        # Get all weapons with stats
        weapons_query = text("""
            SELECT
                e.macro_name, e.name, e.equipment_type, e.size, e.mk_level,
                e.description, e.hull, e.price_min, e.price_avg, e.price_max, e.tags,
                ws.damage_hull, ws.damage_shield, ws.fire_rate, ws.reload_time,
                ws.projectile_speed, ws.projectile_lifetime, ws.range_max,
                ws.heat_per_shot, ws.heat_dissipation, ws.overheat_time,
                ws.rotation_speed, ws.dps_hull, ws.dps_shield
            FROM equipment e
            LEFT JOIN weapon_stats ws ON e.id = ws.equipment_id
            WHERE e.equipment_type IN ('weapon', 'turret')
            ORDER BY e.equipment_type, e.size, e.mk_level, e.name
        """)

        weapons = session.execute(weapons_query).fetchall()

        # Write CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'Macro Name', 'Name', 'Type', 'Size', 'Mk Level',
                'Description', 'Hull', 'Price Min', 'Price Avg', 'Price Max', 'Tags',
                'Damage Hull', 'Damage Shield', 'Fire Rate', 'Reload Time',
                'Projectile Speed', 'Projectile Lifetime', 'Range Max',
                'Heat Per Shot', 'Heat Dissipation', 'Overheat Time',
                'Rotation Speed', 'DPS Hull', 'DPS Shield'
            ])

            # Data rows
            for weapon in weapons:
                writer.writerow(weapon)

    print(f"[OK] Exported {len(weapons)} weapons to {output_file.name}")
    print(f"  Columns: Name, Type, Size, Damage, DPS, Heat, etc.")
    print(f"  File: {output_file.absolute()}")


if __name__ == "__main__":
    export_weapons_to_csv()

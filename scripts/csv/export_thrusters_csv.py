"""Export thrusters data to CSV."""

import sys
import csv
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from x4ft.database.connection import DatabaseManager
from x4ft.config import X4FTConfig
from sqlalchemy import text


def export_thrusters_to_csv():
    """Export all thrusters to CSV with their stats."""

    # Get project root and config
    project_root = Path(__file__).parent.parent.parent
    config = X4FTConfig.load(project_root / 'config.json')
    db = DatabaseManager(config.database_path)

    # Output to scripts/csv/ folder
    output_file = Path(__file__).parent / 'thrusters.csv'

    with db.get_session() as session:
        # Get all thrusters with stats
        thrusters_query = text("""
            SELECT
                e.macro_name, e.name, e.size, e.mk_level,
                e.description, e.price_min, e.price_avg, e.price_max, e.tags,
                ts.thrust_strafe, ts.thrust_pitch, ts.thrust_yaw, ts.thrust_roll
            FROM equipment e
            LEFT JOIN thruster_stats ts ON e.id = ts.equipment_id
            WHERE e.equipment_type = 'thruster'
            ORDER BY e.size, e.mk_level, e.name
        """)

        thrusters = session.execute(thrusters_query).fetchall()

        # Write CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'Macro Name', 'Name', 'Size', 'Mk Level',
                'Description', 'Price Min', 'Price Avg', 'Price Max', 'Tags',
                'Thrust Strafe', 'Thrust Pitch', 'Thrust Yaw', 'Thrust Roll'
            ])

            # Data rows
            for thruster in thrusters:
                writer.writerow(thruster)

    print(f"[OK] Exported {len(thrusters)} thrusters to {output_file.name}")
    print(f"  Columns: Name, Size, Angular, Strafe, etc.")
    print(f"  File: {output_file.absolute()}")


if __name__ == "__main__":
    export_thrusters_to_csv()

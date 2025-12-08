"""Export engines data to CSV."""

import sys
import csv
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from x4ft.database.connection import DatabaseManager
from x4ft.config import X4FTConfig
from sqlalchemy import text


def export_engines_to_csv():
    """Export all engines to CSV with their stats."""

    # Get project root and config
    project_root = Path(__file__).parent.parent.parent
    config = X4FTConfig.load(project_root / 'config.json')
    db = DatabaseManager(config.database_path)

    # Output to scripts/csv/ folder
    output_file = Path(__file__).parent / 'engines.csv'

    with db.get_session() as session:
        # Get all engines with stats
        engines_query = text("""
            SELECT
                e.macro_name, e.name, e.size, e.mk_level,
                e.description, e.price_min, e.price_avg, e.price_max, e.tags,
                es.forward_thrust, es.reverse_thrust,
                es.boost_thrust, es.boost_duration, es.boost_recharge,
                es.travel_thrust, es.travel_charge_time, es.travel_attack_time, es.travel_release_time
            FROM equipment e
            LEFT JOIN engine_stats es ON e.id = es.equipment_id
            WHERE e.equipment_type = 'engine'
            ORDER BY e.size, e.mk_level, e.name
        """)

        engines = session.execute(engines_query).fetchall()

        # Write CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'Macro Name', 'Name', 'Size', 'Mk Level',
                'Description', 'Price Min', 'Price Avg', 'Price Max', 'Tags',
                'Forward Thrust', 'Reverse Thrust',
                'Boost Thrust', 'Boost Duration', 'Boost Recharge',
                'Travel Thrust', 'Travel Charge Time', 'Travel Attack Time', 'Travel Release Time'
            ])

            # Data rows
            for engine in engines:
                writer.writerow(engine)

    print(f"[OK] Exported {len(engines)} engines to {output_file.name}")
    print(f"  Columns: Name, Size, Thrust, Boost, Travel, etc.")
    print(f"  File: {output_file.absolute()}")


if __name__ == "__main__":
    export_engines_to_csv()

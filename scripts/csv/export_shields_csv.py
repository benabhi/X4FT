"""Export shields data to CSV."""

import sys
import csv
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from x4ft.database.connection import DatabaseManager
from x4ft.config import X4FTConfig
from sqlalchemy import text


def export_shields_to_csv():
    """Export all shields to CSV with their stats."""

    # Get project root and config
    project_root = Path(__file__).parent.parent.parent
    config = X4FTConfig.load(project_root / 'config.json')
    db = DatabaseManager(config.database_path)

    # Output to scripts/csv/ folder
    output_file = Path(__file__).parent / 'shields.csv'

    with db.get_session() as session:
        # Get all shields with stats
        shields_query = text("""
            SELECT
                e.macro_name, e.name, e.size, e.mk_level,
                e.description, e.hull, e.price_min, e.price_avg, e.price_max, e.tags,
                ss.capacity, ss.recharge_rate, ss.recharge_delay
            FROM equipment e
            LEFT JOIN shield_stats ss ON e.id = ss.equipment_id
            WHERE e.equipment_type = 'shield'
            ORDER BY e.size, e.mk_level, e.name
        """)

        shields = session.execute(shields_query).fetchall()

        # Write CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'Macro Name', 'Name', 'Size', 'Mk Level',
                'Description', 'Hull', 'Price Min', 'Price Avg', 'Price Max', 'Tags',
                'Capacity', 'Recharge Rate', 'Recharge Delay'
            ])

            # Data rows
            for shield in shields:
                writer.writerow(shield)

    print(f"[OK] Exported {len(shields)} shields to {output_file.name}")
    print(f"  Columns: Name, Size, Capacity, Recharge Rate, etc.")
    print(f"  File: {output_file.absolute()}")


if __name__ == "__main__":
    export_shields_to_csv()

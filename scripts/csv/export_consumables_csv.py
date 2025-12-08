"""Export consumables data to CSV for verification."""

import sys
import csv
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from x4ft.database.connection import DatabaseManager
from x4ft.config import X4FTConfig
from sqlalchemy import text


def export_consumables_to_csv():
    """Export all consumables to CSV."""

    # Get project root and config
    project_root = Path(__file__).parent.parent.parent
    config = X4FTConfig.load(project_root / 'config.json')
    db = DatabaseManager(config.database_path)

    # Output to scripts/csv/ folder
    output_file = Path(__file__).parent / 'consumables.csv'

    with db.get_session() as session:
        # Get all consumables
        query = text("""
            SELECT
                ware_id, macro_name, name, description, consumable_type, size, mk_level,
                price_min, price_avg, price_max, tags
            FROM consumables
            ORDER BY consumable_type, name
        """)

        consumables = session.execute(query).fetchall()

        # Write CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'Ware ID', 'Macro Name', 'Name', 'Description', 'Type', 'Size', 'Mk Level',
                'Price Min', 'Price Avg', 'Price Max', 'Tags'
            ])

            # Data rows
            for consumable in consumables:
                writer.writerow([
                    consumable[0],  # ware_id
                    consumable[1],  # macro_name
                    consumable[2],  # name
                    consumable[3],  # description
                    consumable[4],  # consumable_type
                    consumable[5],  # size
                    consumable[6],  # mk_level
                    consumable[7],  # price_min
                    consumable[8],  # price_avg
                    consumable[9],  # price_max
                    consumable[10], # tags
                ])

    print(f"[OK] Exported {len(consumables)} consumables to {output_file}")
    print(f"  Types: missiles, mines, satellites, drones, laser_towers, countermeasures")
    print(f"  File: {output_file.absolute()}")


if __name__ == "__main__":
    export_consumables_to_csv()

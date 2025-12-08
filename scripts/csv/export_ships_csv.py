"""Export ships data to CSV for verification."""

import sys
import csv
from pathlib import Path
from collections import defaultdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from x4ft.database.connection import DatabaseManager
from x4ft.config import X4FTConfig
from sqlalchemy import text


def export_ships_to_csv():
    """Export all ships to CSV with their main attributes and slot counts."""

    # Get project root and config
    project_root = Path(__file__).parent.parent.parent
    config = X4FTConfig.load(project_root / 'config.json')
    db = DatabaseManager(config.database_path)

    # Output to scripts/csv/ folder
    output_file = Path(__file__).parent / 'ships.csv'

    with db.get_session() as session:
        # Get all ships
        ships_query = text("""
            SELECT
                macro_name, name, description, size, ship_type, ship_class, purpose_primary,
                hull_max, mass, price_min, price_avg, price_max,
                cargo_capacity, missile_storage, drone_storage,
                unit_storage, crew_capacity, makerrace,
                forward_drag, pitch_inertia, yaw_inertia, roll_inertia
            FROM ships
            ORDER BY size, makerrace, name
        """)

        ships = session.execute(ships_query).fetchall()

        # Get slot counts for each ship
        slots_query = text("""
            SELECT ship_id, slot_type, COUNT(*) as count
            FROM ship_slots
            GROUP BY ship_id, slot_type
        """)

        slots_data = session.execute(slots_query).fetchall()

        # Organize slots by ship
        ship_slots = defaultdict(lambda: defaultdict(int))
        for ship_id, slot_type, count in slots_data:
            ship_slots[ship_id][slot_type] = count

        # Write CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'Macro Name', 'Name', 'Description', 'Size', 'Type', 'Class', 'Purpose',
                'Hull', 'Mass', 'Price Min', 'Price Avg', 'Price Max',
                'Cargo', 'Missiles', 'Drones', 'Units', 'Crew',
                'Race', 'Engine Slots', 'Shield Slots', 'Weapon Slots',
                'Turret Slots', 'Unknown Slots', 'Total Slots',
                'Forward Drag', 'Pitch Inertia', 'Yaw Inertia', 'Roll Inertia'
            ])

            # Data rows
            for i, ship in enumerate(ships, 1):
                ship_id = i  # Assuming ship_id matches row number
                slots = ship_slots[ship_id]

                total_slots = sum(slots.values())

                writer.writerow([
                    ship[0],  # macro_name
                    ship[1],  # name
                    ship[2],  # description
                    ship[3],  # size
                    ship[4],  # ship_type
                    ship[5],  # ship_class
                    ship[6],  # purpose_primary
                    ship[7],  # hull_max
                    ship[8],  # mass
                    ship[9],  # price_min
                    ship[10], # price_avg
                    ship[11], # price_max
                    ship[12], # cargo_capacity
                    ship[13], # missile_storage
                    ship[14], # drone_storage
                    ship[15], # unit_storage
                    ship[16], # crew_capacity
                    ship[17], # makerrace
                    slots.get('engine', 0),
                    slots.get('shield', 0),
                    slots.get('weapon', 0),
                    slots.get('turret', 0),
                    slots.get('unknown', 0),
                    total_slots,
                    ship[18], # forward_drag
                    ship[19], # pitch_inertia
                    ship[20], # yaw_inertia
                    ship[21], # roll_inertia
                ])

    print(f"[OK] Exported {len(ships)} ships to {output_file}")
    print(f"  Columns: Name, Size, Type, Hull, Mass, Cargo, Slots, Physics, etc.")
    print(f"  File: {output_file.absolute()}")


if __name__ == "__main__":
    export_ships_to_csv()

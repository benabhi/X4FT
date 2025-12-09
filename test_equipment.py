import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from x4ft.database.database_manager import DatabaseManager
from x4ft.database.schema import Ship, Equipment, EngineStats

db = DatabaseManager('data/x4ft.db')
session = db.get_session()

# Find Asp Raider
ship = session.query(Ship).filter(Ship.name.like('%Asp Raider%')).first()
if ship:
    print(f"Ship: {ship.name}")
    print(f"  Size: {ship.size}")
    print()

# Find engines of size S
print("Engines with size 's':")
engines = session.query(Equipment).filter(
    Equipment.equipment_type == 'engine',
    Equipment.size == 's'
).all()
print(f"  Found {len(engines)} engines")
for engine in engines[:5]:
    print(f"  - {engine.name} (size: {engine.size})")

print()

# Find engines with any size
print("All engines (any size):")
all_engines = session.query(Equipment).filter(
    Equipment.equipment_type == 'engine'
).all()
print(f"  Found {len(all_engines)} engines total")

# Group by size
from collections import Counter
size_counts = Counter(e.size for e in all_engines)
print("  Sizes:")
for size, count in sorted(size_counts.items()):
    print(f"    {size}: {count}")

session.close()

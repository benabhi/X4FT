"""Check PAR equipment in database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from x4ft.database.connection import DatabaseManager
from x4ft.database.schema import Equipment

db = DatabaseManager('data/x4ft.db')

with db.get_session() as session:
    print("="*80)
    print("COMBAT ENGINES M MK3")
    print("="*80)
    engines = session.query(Equipment).filter(
        Equipment.equipment_type == 'engine',
        Equipment.name.like('%Combat%'),
        Equipment.size == 'm',
        Equipment.mk_level == 3
    ).all()

    for e in engines[:15]:
        print(f"[{e.faction_prefix or 'NONE':4}] {e.name:30} | Ware: {e.ware_id}")

    print()
    print("="*80)
    print("SHIELD GENERATORS M MK3")
    print("="*80)
    shields = session.query(Equipment).filter(
        Equipment.equipment_type == 'shield',
        Equipment.size == 'm',
        Equipment.mk_level == 3
    ).all()

    for s in shields[:15]:
        print(f"[{s.faction_prefix or 'NONE':4}] {s.name:30} | Ware: {s.ware_id}")

    print()
    print("="*80)
    print("BEAM TURRETS M MK1")
    print("="*80)
    turrets = session.query(Equipment).filter(
        Equipment.equipment_type == 'turret',
        Equipment.name.like('%Beam%'),
        Equipment.size == 'm',
        Equipment.mk_level == 1
    ).all()

    for t in turrets[:15]:
        print(f"[{t.faction_prefix or 'NONE':4}] {t.name:30} | Ware: {t.ware_id}")

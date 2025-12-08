"""Validation utilities for filtering irrelevant game data."""

from typing import Optional


def is_valid_equipment_macro(macro_name: str) -> bool:
    """Check if an equipment macro is valid for fitting tool.

    Excludes:
    - Video macros (_video_)
    - Virtual macros (_virtual_)

    Args:
        macro_name: Macro name to validate

    Returns:
        True if valid, False if should be excluded
    """
    if not macro_name:
        return False

    # Exclude video macros (UI/display only)
    if '_video_' in macro_name.lower():
        return False

    # Exclude virtual macros (placeholders/test items)
    if '_virtual_' in macro_name.lower():
        return False

    return True


def is_valid_ship(
    macro_name: str,
    hull_max: float,
    mass: float
) -> bool:
    """Check if a ship is valid for fitting tool.

    Excludes:
    - Station modules (hull=0 or mass=0)
    - Storage modules
    - Habitation modules
    - Production modules
    - Connection structures

    Args:
        macro_name: Ship macro name
        hull_max: Ship hull points
        mass: Ship mass

    Returns:
        True if valid flyable ship, False if station module or invalid
    """
    if not macro_name:
        return False

    # Exclude ships with 0 hull or mass (station modules)
    if hull_max == 0 or mass == 0:
        return False

    # Exclude known station module patterns
    module_patterns = [
        '_storage_',
        '_hab_',
        '_prod_',
        '_connection_',
    ]

    macro_lower = macro_name.lower()
    for pattern in module_patterns:
        if pattern in macro_lower:
            return False

    return True


def should_exclude_ship(
    macro_name: str,
    hull_max: float,
    mass: float,
    ship_class: str = "",
    ship_type: str = "",
    makerrace: str = "",
    size: str = ""
) -> Optional[str]:
    """Check if a ship should be excluded and return reason.

    Excludes NPC-only ships and non-pilotable vessels based on player research:
    - Personal vehicles (mass traffic NPCs)
    - Kha'ak ships (not capturable)
    - Xenon XS drones (not capturable, but other Xenon ships ARE capturable since Update 7.0)
    - Story/Scenario ships (mission-specific)
    - Pods and distress drones

    Args:
        macro_name: Ship macro name
        hull_max: Ship hull points
        mass: Ship mass
        ship_class: Ship class (e.g., 'ship_s', 'ship_m', 'spacesuit')
        ship_type: Ship type (e.g., 'fighter', 'personalvehicle', 'distressdrone')
        makerrace: Ship maker race (e.g., 'argon', 'khaak', 'xenon')
        size: Ship size (e.g., 'xs', 's', 'm', 'l', 'xl')

    Returns:
        Exclusion reason string if should be excluded, None if valid
    """
    macro_lower = macro_name.lower()

    # Exclude spacesuits (not flyable ships)
    if ship_class and ship_class.lower() == 'spacesuit':
        return "spacesuit (not a ship)"

    # === NPC-ONLY SHIPS (verified via web research) ===

    # Personal vehicles (mass traffic: civilian ships, transporters, tour buses)
    # These are NPC-only decorative ships around stations
    if ship_type and ship_type.lower() == 'personalvehicle':
        return "personal vehicle (NPC mass traffic)"

    # Kha'ak ships (enemy faction, not capturable/pilotable by players)
    if makerrace and makerrace.lower() == 'khaak':
        return "Kha'ak ship (enemy, not capturable)"

    # Xenon XS drones (not pilotable)
    # NOTE: Other Xenon ships (S/M/L/XL) ARE capturable since Update 7.0, so keep them
    if makerrace and makerrace.lower() == 'xenon' and size and size.lower() == 'xs':
        return "Xenon drone (not capturable)"

    # Story/Scenario ships (mission-specific, not for general use)
    if 'story' in macro_lower or 'scenario' in macro_lower:
        return "story/scenario ship (mission-specific)"

    # Pods (escape pods, boarding pods - not pilotable ships)
    if 'escapepod' in macro_lower or 'boardingpod' in macro_lower:
        return "pod (not a pilotable ship)"

    # Distress drones (autonomous NPC drones)
    if ship_type and ship_type.lower() == 'distressdrone':
        return "distress drone (NPC autonomous)"

    # === CONSUMABLES (moved to separate consumables table) ===

    # Exclude consumables that are classified as ships but aren't pilotable
    # These are deployable items carried in cargo bays
    if 'lasertower' in macro_lower:
        return "laser tower (consumable)"
    if 'drone' in macro_lower and 'droneship' not in macro_lower:
        return "drone (consumable)"

    # === STATION MODULES ===

    # Exclude station modules
    if hull_max == 0 and mass == 0:
        return "station module (0 hull & mass)"
    if hull_max == 0:
        return "station module (0 hull)"
    if mass == 0:
        return "station module (0 mass)"

    if '_storage_' in macro_lower:
        return "storage module"
    if '_hab_' in macro_lower:
        return "habitation module"
    if '_prod_' in macro_lower:
        return "production module"
    if '_connection_' in macro_lower:
        return "connection structure"

    return None


def should_exclude_equipment(macro_name: str) -> Optional[str]:
    """Check if equipment should be excluded and return reason.

    Excludes:
    - Video/virtual macros (UI/test items)
    - Scenario/story equipment (NPCs/missions only)
    - Missile/mine engines (internal propulsion systems)
    - NPC-only equipment (drones, police, civilian ships)

    Args:
        macro_name: Equipment macro name

    Returns:
        Exclusion reason string if should be excluded, None if valid
    """
    macro_lower = macro_name.lower()

    # UI/Test items
    if '_video_' in macro_lower:
        return "video macro (UI only)"
    if '_virtual_' in macro_lower:
        return "virtual macro (test item)"

    # Scenario/Story items (NPC enemy equipment)
    if 'scenario' in macro_lower:
        return "scenario equipment (NPCs only)"
    if 'story' in macro_lower:
        return "story equipment (mission-specific)"

    # Missile/Mine propulsion systems (not ship equipment)
    if 'engine_missile_' in macro_lower:
        return "missile engine (internal)"
    if 'engine_limpet_' in macro_lower:
        return "limpet mine engine (internal)"
    if 'engine_special_mine_' in macro_lower:
        return "mine engine (internal)"

    # NPC-only equipment (drones, police, civilian ships)
    if 'engine_gen_xs_' in macro_lower:
        return "NPC drone/system engine"
    if '_xs_police_' in macro_lower and 'engine_' in macro_lower:
        return "NPC police engine"
    if '_xs_pv_' in macro_lower and 'engine_' in macro_lower:
        return "NPC civilian engine"
    if 'engine_gen_xs_static' in macro_lower:
        return "static engine (decorative)"

    return None

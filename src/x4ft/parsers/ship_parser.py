"""Parser for ship macros - simplified initial version."""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from lxml import etree

from .base_parser import BaseParser
from .validation import is_valid_ship, should_exclude_ship


@dataclass
class ShipSlotData:
    """Parsed ship slot/connection data."""

    slot_name: str
    slot_type: str  # weapon, turret, shield, engine, thruster
    slot_size: str = ""  # xs, s, m, l, xl
    slot_index: int = 0
    tags: str = ""  # Comma-separated tags


@dataclass
class ShipData:
    """Parsed ship data - ALL attributes from game XML."""

    macro_name: str
    name: str
    size: str  # xs, s, m, l, xl

    # Identification
    basename: str = ""
    description: str = ""
    variation: str = ""
    shortvariation: str = ""
    makerrace: str = ""
    icon: str = ""

    # Classification
    ship_type: str = ""
    ship_class: str = ""
    purpose_primary: str = ""
    component_ref: Optional[str] = None

    # Base stats
    hull_max: int = 0
    mass: float = 0.0

    # Explosion damage
    explosion_damage: float = 0.0
    explosion_damage_shield: float = 0.0

    # Storage
    cargo_capacity: int = 0
    missile_storage: int = 0
    drone_storage: int = 0
    unit_storage: int = 0

    # Crew
    crew_capacity: int = 0

    # Secrecy
    secrecy_level: int = 0

    # Physics - Inertia
    pitch_inertia: float = 0.0
    yaw_inertia: float = 0.0
    roll_inertia: float = 0.0

    # Physics - Drag
    forward_drag: float = 0.0
    reverse_drag: float = 0.0
    horizontal_drag: float = 0.0
    vertical_drag: float = 0.0
    pitch_drag: float = 0.0
    yaw_drag: float = 0.0
    roll_drag: float = 0.0

    # Physics - Acceleration factors
    forward_accfactor: float = 1.0

    # Jerk
    jerk_forward_accel: float = 0.0
    jerk_forward_decel: float = 0.0
    jerk_forward_ratio: float = 0.0
    jerk_boost_accel: float = 0.0
    jerk_boost_ratio: float = 0.0
    jerk_travel_accel: float = 0.0
    jerk_travel_decel: float = 0.0
    jerk_travel_ratio: float = 0.0
    jerk_strafe: float = 0.0
    jerk_angular: float = 0.0

    # Thruster
    thruster_tags: str = ""

    # Sound
    sound_occlusion_inside: float = 0.0
    shipdetail_sound: str = ""

    # Slots/Connections
    slots: List[ShipSlotData] = field(default_factory=list)


class ShipParser(BaseParser):
    """Parses ship macro XML files."""

    # Ship size mapping based on class
    SIZE_MAP = {
        "ship_xs": "xs",
        "ship_s": "s",
        "ship_m": "m",
        "ship_l": "l",
        "ship_xl": "xl",
    }

    def __init__(self, extracted_path: Path, macro_index: Dict[str, str], text_resolver=None):
        """Initialize ship parser.

        Args:
            extracted_path: Root of extracted files
            macro_index: Mapping of macro_name -> file_path from index/macros.xml
            text_resolver: Optional text resolver for names
        """
        super().__init__(extracted_path, text_resolver)
        self.macro_index = macro_index

    def parse(self) -> List[ShipData]:
        """Parse all ship macros.

        Returns:
            List of ShipData objects
        """
        ships = []

        # Find ship macro files directly from filesystem
        # This is more reliable than using the index which may be incomplete
        ship_files = []
        units_path = self.extracted_path / "assets" / "units"

        if units_path.exists():
            for size_dir in units_path.iterdir():
                if not size_dir.is_dir():
                    continue

                macros_dir = size_dir / "macros"
                if macros_dir.exists():
                    for xml_file in macros_dir.glob("ship_*_macro.xml"):
                        # Get relative path from extracted_path
                        rel_path = xml_file.relative_to(self.extracted_path)
                        macro_name = xml_file.stem
                        ship_files.append((macro_name, str(rel_path)))

        self.logger.info(f"Found {len(ship_files)} ship macro files")

        for macro_name, macro_path in ship_files:
            # Skip DVD placeholders and parts
            if "_dvd_" in macro_name or "_part_" in macro_name:
                continue

            ship = self._parse_ship_macro(macro_name, macro_path)
            if ship:
                ships.append(ship)

        self.logger.info(f"Successfully parsed {len(ships)} ships")
        return ships

    def _extract_cargo_from_storage_components(self, macro_root) -> int:
        """Extract total cargo capacity from ship's storage components.

        Ships don't have cargo capacity in their main macro. Instead, it's defined
        in separate storage component macros referenced in <connections>.

        Args:
            macro_root: Root element of the ship macro XML

        Returns:
            Total cargo capacity from all storage components
        """
        total_cargo = 0

        # Find all connections
        connections_elem = macro_root.find(".//connections")
        if connections_elem is None:
            return 0

        # Look for storage connections (con_storage*, con_shipstorage*)
        for connection in connections_elem.findall("connection"):
            conn_ref = connection.get("ref", "")

            # Check if this is a cargo storage connection
            if not (conn_ref.startswith("con_storage") or conn_ref.startswith("con_shipstorage")):
                continue

            # Get the storage macro reference
            macro_elem = connection.find("macro")
            if macro_elem is None:
                continue

            storage_macro_name = macro_elem.get("ref", "")
            if not storage_macro_name:
                continue

            # Load the storage component macro
            # Storage macros are typically in the same directory as the ship
            # Try to find it in assets/units/size_*/macros/
            storage_root = None
            for size in ["xs", "s", "m", "l", "xl"]:
                storage_path = f"assets/units/size_{size}/macros/{storage_macro_name}.xml"
                storage_root = self.parse_file(storage_path)
                if storage_root is not None:
                    break

            if storage_root is None:
                # Try props/SurfaceElements for some storage types
                storage_path = f"assets/props/SurfaceElements/macros/{storage_macro_name}.xml"
                storage_root = self.parse_file(storage_path)

            if storage_root is None:
                continue

            # Extract cargo capacity from storage component
            cargo_elem = storage_root.find(".//properties/cargo")
            if cargo_elem is not None:
                cargo_max = self.get_int(cargo_elem, "max", 0)
                total_cargo += cargo_max

        return total_cargo

    def _parse_ship_macro(self, macro_name: str, macro_path: str) -> Optional[ShipData]:
        """Parse a single ship macro file - extract ALL attributes.

        Args:
            macro_name: Name of the macro
            macro_path: Relative path to macro file

        Returns:
            ShipData object or None if parsing failed
        """
        root = self.parse_file(macro_path)
        if root is None:
            return None

        # Find the macro element
        macro_elem = root.find(f".//macro[@name='{macro_name}']")
        if macro_elem is None:
            macro_elem = root.find(".//macro")
            if macro_elem is None:
                self.logger.warning(f"No macro element found in {macro_path}")
                return None

        # Get ship class/size
        ship_class = macro_elem.get("class", "")
        ship_size = self.SIZE_MAP.get(ship_class, "s")

        # Get component reference
        component_elem = macro_elem.find("component")
        component_ref = component_elem.get("ref") if component_elem is not None else None

        # Get properties
        props = macro_elem.find("properties")
        if props is None:
            self.logger.warning(f"No properties found for {macro_name}")
            return None

        # === IDENTIFICATION ===
        ident = props.find("identification")
        basename = ""
        variation = ""
        shortvariation = ""
        description = ""
        makerrace = ""
        icon = ""
        name = macro_name

        if ident is not None:
            basename = self.get_text_value(ident, "basename")
            variation = self.get_text_value(ident, "variation")
            shortvariation = self.get_text_value(ident, "shortvariation")
            description = self.get_text_value(ident, "description")
            makerrace = ident.get("makerrace", "")
            icon = ident.get("icon", "")

            # Combine basename and variation for full name
            if basename and variation:
                name = f"{basename} {variation}"
            elif basename:
                name = basename
            else:
                name = self.get_text_value(ident, "name") or macro_name

        # === HULL ===
        hull_elem = props.find("hull")
        hull_max = self.get_int(hull_elem, "max", 0)

        # === PHYSICS ===
        physics_elem = props.find("physics")
        mass = self.get_float(physics_elem, "mass", 0.0)

        # Inertia
        pitch_inertia = 0.0
        yaw_inertia = 0.0
        roll_inertia = 0.0
        if physics_elem is not None:
            inertia_elem = physics_elem.find("inertia")
            if inertia_elem is not None:
                pitch_inertia = self.get_float(inertia_elem, "pitch", 0.0)
                yaw_inertia = self.get_float(inertia_elem, "yaw", 0.0)
                roll_inertia = self.get_float(inertia_elem, "roll", 0.0)

        # Drag
        forward_drag = 0.0
        reverse_drag = 0.0
        horizontal_drag = 0.0
        vertical_drag = 0.0
        pitch_drag = 0.0
        yaw_drag = 0.0
        roll_drag = 0.0
        if physics_elem is not None:
            drag_elem = physics_elem.find("drag")
            if drag_elem is not None:
                forward_drag = self.get_float(drag_elem, "forward", 0.0)
                reverse_drag = self.get_float(drag_elem, "reverse", 0.0)
                horizontal_drag = self.get_float(drag_elem, "horizontal", 0.0)
                vertical_drag = self.get_float(drag_elem, "vertical", 0.0)
                pitch_drag = self.get_float(drag_elem, "pitch", 0.0)
                yaw_drag = self.get_float(drag_elem, "yaw", 0.0)
                roll_drag = self.get_float(drag_elem, "roll", 0.0)

        # Acceleration factors
        forward_accfactor = 1.0
        if physics_elem is not None:
            accfactors_elem = physics_elem.find("accfactors")
            if accfactors_elem is not None:
                forward_accfactor = self.get_float(accfactors_elem, "forward", 1.0)

        # === JERK ===
        jerk_elem = props.find("jerk")
        jerk_forward_accel = 0.0
        jerk_forward_decel = 0.0
        jerk_forward_ratio = 0.0
        jerk_boost_accel = 0.0
        jerk_boost_ratio = 0.0
        jerk_travel_accel = 0.0
        jerk_travel_decel = 0.0
        jerk_travel_ratio = 0.0
        jerk_strafe = 0.0
        jerk_angular = 0.0

        if jerk_elem is not None:
            forward_elem = jerk_elem.find("forward")
            if forward_elem is not None:
                jerk_forward_accel = self.get_float(forward_elem, "accel", 0.0)
                jerk_forward_decel = self.get_float(forward_elem, "decel", 0.0)
                jerk_forward_ratio = self.get_float(forward_elem, "ratio", 0.0)

            boost_elem = jerk_elem.find("forward_boost")
            if boost_elem is not None:
                jerk_boost_accel = self.get_float(boost_elem, "accel", 0.0)
                jerk_boost_ratio = self.get_float(boost_elem, "ratio", 0.0)

            travel_elem = jerk_elem.find("forward_travel")
            if travel_elem is not None:
                jerk_travel_accel = self.get_float(travel_elem, "accel", 0.0)
                jerk_travel_decel = self.get_float(travel_elem, "decel", 0.0)
                jerk_travel_ratio = self.get_float(travel_elem, "ratio", 0.0)

            strafe_elem = jerk_elem.find("strafe")
            if strafe_elem is not None:
                jerk_strafe = self.get_float(strafe_elem, "value", 0.0)

            angular_elem = jerk_elem.find("angular")
            if angular_elem is not None:
                jerk_angular = self.get_float(angular_elem, "value", 0.0)

        # === STORAGE ===
        storage_elem = props.find("storage")
        missile_storage = self.get_int(storage_elem, "missile", 0)
        drone_storage = self.get_int(storage_elem, "drone", 0)
        unit_storage = self.get_int(storage_elem, "unit", 0)

        # Cargo capacity is NOT in the storage element - it's in separate storage components
        # Extract from connected storage component macros
        cargo_capacity = self._extract_cargo_from_storage_components(root)

        # === CREW ===
        people_elem = props.find("people")
        crew_capacity = self.get_int(people_elem, "capacity", 0)

        # === EXPLOSION DAMAGE ===
        explosion_elem = props.find("explosiondamage")
        explosion_damage = self.get_float(explosion_elem, "value", 0.0)
        explosion_damage_shield = self.get_float(explosion_elem, "shield", 0.0)

        # === SECRECY ===
        secrecy_elem = props.find("secrecy")
        secrecy_level = self.get_int(secrecy_elem, "level", 0)

        # === SHIP TYPE & PURPOSE ===
        ship_elem = props.find("ship")
        ship_type = ship_elem.get("type", "") if ship_elem is not None else ""

        purpose_elem = props.find("purpose")
        purpose_primary = purpose_elem.get("primary", "") if purpose_elem is not None else ""

        # === THRUSTER ===
        thruster_elem = props.find("thruster")
        thruster_tags = thruster_elem.get("tags", "") if thruster_elem is not None else ""

        # === SOUND ===
        sound_occlusion_elem = props.find("sound_occlusion")
        sound_occlusion_inside = self.get_float(sound_occlusion_elem, "inside", 0.0)

        sounds_elem = props.find("sounds")
        shipdetail_sound = ""
        if sounds_elem is not None:
            shipdetail_elem = sounds_elem.find("shipdetail")
            if shipdetail_elem is not None:
                shipdetail_sound = shipdetail_elem.get("ref", "")

        # === SLOTS/CONNECTIONS ===
        # Parse connections from both macro and component file
        slots = self._parse_connections(macro_elem)

        # Also parse component connections (where hardpoints are defined)
        if component_ref:
            component_slots = self._parse_component_connections(component_ref, macro_path)
            slots.extend(component_slots)

        # Validate ship - exclude station modules and invalid ships
        exclusion_reason = should_exclude_ship(macro_name, hull_max, mass)
        if exclusion_reason:
            self.logger.debug(f"Excluding {macro_name}: {exclusion_reason}")
            return None

        # Create and return ShipData with ALL attributes
        return ShipData(
            macro_name=macro_name,
            name=name,
            size=ship_size,
            basename=basename,
            description=description,
            variation=variation,
            shortvariation=shortvariation,
            makerrace=makerrace,
            icon=icon,
            ship_type=ship_type,
            ship_class=ship_class,
            purpose_primary=purpose_primary,
            component_ref=component_ref,
            hull_max=hull_max,
            mass=mass,
            explosion_damage=explosion_damage,
            explosion_damage_shield=explosion_damage_shield,
            cargo_capacity=cargo_capacity,
            missile_storage=missile_storage,
            drone_storage=drone_storage,
            unit_storage=unit_storage,
            crew_capacity=crew_capacity,
            secrecy_level=secrecy_level,
            pitch_inertia=pitch_inertia,
            yaw_inertia=yaw_inertia,
            roll_inertia=roll_inertia,
            forward_drag=forward_drag,
            reverse_drag=reverse_drag,
            horizontal_drag=horizontal_drag,
            vertical_drag=vertical_drag,
            pitch_drag=pitch_drag,
            yaw_drag=yaw_drag,
            roll_drag=roll_drag,
            forward_accfactor=forward_accfactor,
            jerk_forward_accel=jerk_forward_accel,
            jerk_forward_decel=jerk_forward_decel,
            jerk_forward_ratio=jerk_forward_ratio,
            jerk_boost_accel=jerk_boost_accel,
            jerk_boost_ratio=jerk_boost_ratio,
            jerk_travel_accel=jerk_travel_accel,
            jerk_travel_decel=jerk_travel_decel,
            jerk_travel_ratio=jerk_travel_ratio,
            jerk_strafe=jerk_strafe,
            jerk_angular=jerk_angular,
            thruster_tags=thruster_tags,
            sound_occlusion_inside=sound_occlusion_inside,
            shipdetail_sound=shipdetail_sound,
            slots=slots
        )

    def _parse_connections(self, macro_elem: etree._Element) -> List[ShipSlotData]:
        """Parse connections/slots from macro element.

        Args:
            macro_elem: The <macro> element

        Returns:
            List of ShipSlotData objects
        """
        slots = []
        connections_elem = macro_elem.find("connections")
        if connections_elem is None:
            return slots

        # Map connection types to slot types
        CONNECTION_TYPE_MAP = {
            "weapon": "weapon",
            "turret": "turret",
            "shield": "shield",
            "shieldgenerator": "shield",
            "engine": "engine",
            "thruster": "thruster",
        }

        # Size extraction from macro ref
        SIZE_PATTERNS = ["_xs_", "_s_", "_m_", "_l_", "_xl_"]

        slot_index = 0
        for conn_elem in connections_elem.findall("connection"):
            slot_name = conn_elem.get("ref", "")
            if not slot_name:
                continue

            # Try to determine slot type from name
            slot_type = "unknown"
            slot_name_lower = slot_name.lower()

            # Check common prefixes
            if "weapon" in slot_name_lower:
                slot_type = "weapon"
            elif "turret" in slot_name_lower:
                slot_type = "turret"
            elif "shield" in slot_name_lower:
                slot_type = "shield"
            elif "engine" in slot_name_lower:
                slot_type = "engine"
            elif "thruster" in slot_name_lower:
                slot_type = "thruster"

            # Also check the macro connection attribute
            macro_elem_child = conn_elem.find("macro")
            if macro_elem_child is not None:
                connection_attr = macro_elem_child.get("connection", "")
                if connection_attr in CONNECTION_TYPE_MAP:
                    slot_type = CONNECTION_TYPE_MAP[connection_attr]

                # Try to extract size from macro ref
                macro_ref = macro_elem_child.get("ref", "")
                slot_size = ""
                for size_pattern in SIZE_PATTERNS:
                    if size_pattern in macro_ref:
                        slot_size = size_pattern.strip("_")
                        break
            else:
                slot_size = ""

            # Extract tags if available
            tags = conn_elem.get("tags", "")

            slots.append(ShipSlotData(
                slot_name=slot_name,
                slot_type=slot_type,
                slot_size=slot_size,
                slot_index=slot_index,
                tags=tags
            ))
            slot_index += 1

        return slots

    def _parse_component_connections(self, component_ref: str, macro_path: str) -> List[ShipSlotData]:
        """Parse connections from the component file (where hardpoints are defined).

        Args:
            component_ref: Name of the component (e.g., "ship_arg_s_fighter_01")
            macro_path: Path to the macro file (used to determine component path)

        Returns:
            List of ShipSlotData objects with hardpoint slots
        """
        slots = []

        # Determine component file path
        # Component files are in the same directory as macro files, but without "_macro" suffix
        # e.g., "assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml"
        #    -> "assets/units/size_s/ship_arg_s_fighter_01.xml"
        try:
            from pathlib import Path
            macro_file_path = Path(macro_path)
            component_dir = macro_file_path.parent.parent  # Go up from "macros" to size_s
            component_file = component_dir / f"{component_ref}.xml"
            component_path_str = str(component_file)

            # Parse component file
            root = self.parse_file(component_path_str)
            if root is None:
                return slots

            # Find the component element
            component_elem = root.find(f".//component[@name='{component_ref}']")
            if component_elem is None:
                component_elem = root.find(".//component")
                if component_elem is None:
                    return slots

            # Find connections in component
            connections_elem = component_elem.find("connections")
            if connections_elem is None:
                return slots

            # Slot type keywords to look for in tags
            SLOT_TYPE_KEYWORDS = {
                "weapon": "weapon",
                "turret": "turret",
                "shield": "shield",
                "shieldgenerator": "shield",
                "engine": "engine",
                "thruster": "thruster",
            }

            # Size patterns
            SIZE_PATTERNS = {
                "extrasmall": "xs",
                "small": "s",
                "medium": "m",
                "large": "l",
                "extralarge": "xl",
            }

            slot_index = 0
            for conn_elem in connections_elem.findall("connection"):
                conn_name = conn_elem.get("name", "")
                if not conn_name:
                    continue

                # Get tags attribute
                tags = conn_elem.get("tags", "")
                if not tags:
                    continue  # Skip connections without tags

                tags_lower = tags.lower()

                # Determine slot type from tags
                slot_type = "unknown"
                for keyword, stype in SLOT_TYPE_KEYWORDS.items():
                    if keyword in tags_lower:
                        slot_type = stype
                        break

                # Skip non-hardpoint connections
                if slot_type == "unknown":
                    continue

                # Determine slot size from tags
                slot_size = ""
                for size_word, size_code in SIZE_PATTERNS.items():
                    if size_word in tags_lower:
                        slot_size = size_code
                        break

                slots.append(ShipSlotData(
                    slot_name=conn_name,
                    slot_type=slot_type,
                    slot_size=slot_size,
                    slot_index=slot_index,
                    tags=tags
                ))
                slot_index += 1

        except Exception as e:
            self.logger.debug(f"Could not parse component {component_ref}: {e}")

        return slots

"""Parser for weapon macros."""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from lxml import etree

from .base_parser import BaseParser
from .validation import should_exclude_equipment


@dataclass
class WeaponData:
    """Parsed weapon data."""

    macro_name: str
    name: str
    equipment_type: str  # weapon or turret
    size: str = ""  # xs, s, m, l, xl
    mk_level: int = 1

    # Identification
    basename: str = ""
    description: str = ""
    makerrace: str = ""

    # Basic stats
    hull: int = 0

    # Heat management
    heat_overheat: float = 0.0
    heat_cooldelay: float = 0.0
    heat_coolrate: float = 0.0
    heat_reenable: float = 0.0

    # Rotation (for turrets)
    rotation_speed_max: float = 0.0
    rotation_accel_max: float = 0.0

    # Bullet reference (for later processing)
    bullet_class: str = ""

    # Component reference
    component_ref: Optional[str] = None

    # Tags (from wares.xml, populated later)
    tags: str = ""


class WeaponParser(BaseParser):
    """Parses weapon macro XML files."""

    # Size mapping
    SIZE_MAP = {
        "_xs_": "xs",
        "_s_": "s",
        "_m_": "m",
        "_l_": "l",
        "_xl_": "xl",
    }

    def __init__(self, extracted_path: Path, macro_index: Dict[str, str], text_resolver=None):
        """Initialize weapon parser.

        Args:
            extracted_path: Root of extracted files
            macro_index: Mapping of macro_name -> file_path from index/macros.xml
            text_resolver: Optional text resolver for names
        """
        super().__init__(extracted_path, text_resolver)
        self.macro_index = macro_index

    def parse(self) -> List[WeaponData]:
        """Parse all weapon macros.

        Returns:
            List of WeaponData objects
        """
        weapons = []

        # Find weapon macro files from filesystem
        # Scan both weapon and turret directories
        weapon_patterns = [
            ("assets/props/weaponsystems", "weapon_*_macro.xml"),
            ("assets/props/weaponsystems", "turret_*_macro.xml"),
        ]

        weapon_files = []
        for base_dir, pattern in weapon_patterns:
            base_path = self.extracted_path / base_dir
            if base_path.exists():
                for xml_file in base_path.rglob(pattern):
                    rel_path = xml_file.relative_to(self.extracted_path)
                    macro_name = xml_file.stem

                    # Determine if weapon or turret
                    equipment_type = "turret" if "turret_" in macro_name else "weapon"
                    weapon_files.append((macro_name, str(rel_path), equipment_type))

        self.logger.info(f"Found {len(weapon_files)} weapon/turret macro files")

        for macro_name, macro_path, equipment_type in weapon_files:
            weapon = self._parse_weapon_macro(macro_name, macro_path, equipment_type)
            if weapon:
                weapons.append(weapon)

        self.logger.info(f"Successfully parsed {len(weapons)} weapons/turrets")
        return weapons

    def _parse_weapon_macro(self, macro_name: str, macro_path: str, equipment_type: str) -> Optional[WeaponData]:
        """Parse a single weapon macro file.

        Args:
            macro_name: Name of the macro
            macro_path: Relative path to macro file
            equipment_type: "weapon" or "turret"

        Returns:
            WeaponData object or None if parsing failed
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
        description = ""
        makerrace = ""
        mk_level = 1
        name = macro_name

        if ident is not None:
            basename = self.get_text_value(ident, "basename")
            description = self.get_text_value(ident, "description")
            makerrace = ident.get("makerrace", "")
            mk_level = self.get_int(ident, "mk", 1)

            # Use basename as name if available
            if basename:
                name = f"{basename} Mk{mk_level}" if mk_level > 1 else basename
            else:
                name = self.get_text_value(ident, "name") or macro_name

        # === SIZE EXTRACTION ===
        size = ""
        for size_pattern, size_code in self.SIZE_MAP.items():
            if size_pattern in macro_name:
                size = size_code
                break

        # === HULL ===
        hull_elem = props.find("hull")
        hull = self.get_int(hull_elem, "max", 0)

        # === HEAT ===
        heat_elem = props.find("heat")
        heat_overheat = self.get_float(heat_elem, "overheat", 0.0)
        heat_cooldelay = self.get_float(heat_elem, "cooldelay", 0.0)
        heat_coolrate = self.get_float(heat_elem, "coolrate", 0.0)
        heat_reenable = self.get_float(heat_elem, "reenable", 0.0)

        # === ROTATION ===
        rotation_speed_elem = props.find("rotationspeed")
        rotation_speed_max = self.get_float(rotation_speed_elem, "max", 0.0)

        rotation_accel_elem = props.find("rotationacceleration")
        rotation_accel_max = self.get_float(rotation_accel_elem, "max", 0.0)

        # === BULLET REFERENCE ===
        bullet_elem = props.find("bullet")
        bullet_class = bullet_elem.get("class", "") if bullet_elem is not None else ""

        # Validate weapon - exclude video/virtual macros
        exclusion_reason = should_exclude_equipment(macro_name)
        if exclusion_reason:
            self.logger.debug(f"Excluding {macro_name}: {exclusion_reason}")
            return None

        return WeaponData(
            macro_name=macro_name,
            name=name,
            equipment_type=equipment_type,
            size=size,
            mk_level=mk_level,
            basename=basename,
            description=description,
            makerrace=makerrace,
            hull=hull,
            heat_overheat=heat_overheat,
            heat_cooldelay=heat_cooldelay,
            heat_coolrate=heat_coolrate,
            heat_reenable=heat_reenable,
            rotation_speed_max=rotation_speed_max,
            rotation_accel_max=rotation_accel_max,
            bullet_class=bullet_class,
            component_ref=component_ref
        )

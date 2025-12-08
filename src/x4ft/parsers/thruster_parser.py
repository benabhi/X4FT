"""Parser for thruster macros."""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from lxml import etree

from .base_parser import BaseParser


@dataclass
class ThrusterData:
    """Parsed thruster data."""

    macro_name: str
    name: str
    size: str = ""  # xs, s, m, l, xl
    mk_level: int = 1

    # Identification
    basename: str = ""
    shortname: str = ""
    description: str = ""

    # Basic stats
    hull_integrated: bool = False

    # Thrust values for maneuvering
    thrust_strafe: float = 0.0
    thrust_pitch: float = 0.0
    thrust_yaw: float = 0.0
    thrust_roll: float = 0.0

    # Component reference
    component_ref: Optional[str] = None

    # Tags (from wares.xml, populated later)
    tags: str = ""


class ThrusterParser(BaseParser):
    """Parses thruster macro XML files."""

    # Size mapping
    SIZE_MAP = {
        "_xs_": "xs",
        "_s_": "s",
        "_m_": "m",
        "_l_": "l",
        "_xl_": "xl",
    }

    def __init__(self, extracted_path: Path, macro_index: Dict[str, str], text_resolver=None):
        """Initialize thruster parser.

        Args:
            extracted_path: Root of extracted files
            macro_index: Mapping of macro_name -> file_path from index/macros.xml
            text_resolver: Optional text resolver for names
        """
        super().__init__(extracted_path, text_resolver)
        self.macro_index = macro_index

    def parse(self) -> List[ThrusterData]:
        """Parse all thruster macros.

        Returns:
            List of ThrusterData objects
        """
        thrusters = []

        # Find thruster macro files from filesystem
        thruster_files = []
        props_path = self.extracted_path / "assets" / "props"

        if props_path.exists():
            for xml_file in props_path.rglob("thruster_*_macro.xml"):
                rel_path = xml_file.relative_to(self.extracted_path)
                macro_name = xml_file.stem
                thruster_files.append((macro_name, str(rel_path)))

        self.logger.info(f"Found {len(thruster_files)} thruster macro files")

        for macro_name, macro_path in thruster_files:
            thruster = self._parse_thruster_macro(macro_name, macro_path)
            if thruster:
                thrusters.append(thruster)

        self.logger.info(f"Successfully parsed {len(thrusters)} thrusters")
        return thrusters

    def _parse_thruster_macro(self, macro_name: str, macro_path: str) -> Optional[ThrusterData]:
        """Parse a single thruster macro file.

        Args:
            macro_name: Name of the macro
            macro_path: Relative path to macro file

        Returns:
            ThrusterData object or None if parsing failed
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
        shortname = ""
        description = ""
        mk_level = 1
        name = macro_name

        if ident is not None:
            basename = self.get_text_value(ident, "basename")
            shortname = self.get_text_value(ident, "shortname")
            description = self.get_text_value(ident, "description")
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
        hull_integrated = self.get_bool(hull_elem, "integrated", False)

        # === THRUST ===
        thrust_elem = props.find("thrust")
        thrust_strafe = self.get_float(thrust_elem, "strafe", 0.0)
        thrust_pitch = self.get_float(thrust_elem, "pitch", 0.0)
        thrust_yaw = self.get_float(thrust_elem, "yaw", 0.0)
        thrust_roll = self.get_float(thrust_elem, "roll", 0.0)

        return ThrusterData(
            macro_name=macro_name,
            name=name,
            size=size,
            mk_level=mk_level,
            basename=basename,
            shortname=shortname,
            description=description,
            hull_integrated=hull_integrated,
            thrust_strafe=thrust_strafe,
            thrust_pitch=thrust_pitch,
            thrust_yaw=thrust_yaw,
            thrust_roll=thrust_roll,
            component_ref=component_ref
        )

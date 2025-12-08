"""Parser for engine macros."""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from lxml import etree

from .base_parser import BaseParser
from .validation import should_exclude_equipment


@dataclass
class EngineData:
    """Parsed engine data."""

    macro_name: str
    name: str
    size: str = ""  # xs, s, m, l, xl
    mk_level: int = 1

    # Identification
    basename: str = ""
    shortname: str = ""
    description: str = ""
    makerrace: str = ""

    # Basic stats
    hull_integrated: bool = False

    # Thrust
    forward_thrust: float = 0.0
    reverse_thrust: float = 0.0

    # Boost
    boost_duration: float = 0.0
    boost_thrust: float = 0.0
    boost_recharge: float = 0.0
    boost_acceleration: float = 0.0
    boost_attack: float = 0.0
    boost_release: float = 0.0
    boost_coast: float = 0.0

    # Travel mode
    travel_charge: float = 0.0
    travel_thrust: float = 0.0
    travel_attack: float = 0.0
    travel_release: float = 0.0

    # Component reference
    component_ref: Optional[str] = None

    # Tags (from wares.xml, populated later)
    tags: str = ""


class EngineParser(BaseParser):
    """Parses engine macro XML files."""

    # Size mapping
    SIZE_MAP = {
        "_xs_": "xs",
        "_s_": "s",
        "_m_": "m",
        "_l_": "l",
        "_xl_": "xl",
    }

    def __init__(self, extracted_path: Path, macro_index: Dict[str, str], text_resolver=None):
        """Initialize engine parser.

        Args:
            extracted_path: Root of extracted files
            macro_index: Mapping of macro_name -> file_path from index/macros.xml
            text_resolver: Optional text resolver for names
        """
        super().__init__(extracted_path, text_resolver)
        self.macro_index = macro_index

    def parse(self) -> List[EngineData]:
        """Parse all engine macros.

        Returns:
            List of EngineData objects
        """
        engines = []

        # Find engine macro files from filesystem
        engine_files = []
        props_path = self.extracted_path / "assets" / "props"

        if props_path.exists():
            for xml_file in props_path.rglob("engine_*_macro.xml"):
                rel_path = xml_file.relative_to(self.extracted_path)
                macro_name = xml_file.stem
                engine_files.append((macro_name, str(rel_path)))

        self.logger.info(f"Found {len(engine_files)} engine macro files")

        for macro_name, macro_path in engine_files:
            engine = self._parse_engine_macro(macro_name, macro_path)
            if engine:
                engines.append(engine)

        self.logger.info(f"Successfully parsed {len(engines)} engines")
        return engines

    def _parse_engine_macro(self, macro_name: str, macro_path: str) -> Optional[EngineData]:
        """Parse a single engine macro file.

        Args:
            macro_name: Name of the macro
            macro_path: Relative path to macro file

        Returns:
            EngineData object or None if parsing failed
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
        makerrace = ""
        mk_level = 1
        name = macro_name

        if ident is not None:
            basename = self.get_text_value(ident, "basename")
            shortname = self.get_text_value(ident, "shortname")
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
        hull_integrated = self.get_bool(hull_elem, "integrated", False)

        # === THRUST ===
        thrust_elem = props.find("thrust")
        forward_thrust = self.get_float(thrust_elem, "forward", 0.0)
        reverse_thrust = self.get_float(thrust_elem, "reverse", 0.0)

        # === BOOST ===
        boost_elem = props.find("boost")
        boost_duration = self.get_float(boost_elem, "duration", 0.0)
        boost_thrust = self.get_float(boost_elem, "thrust", 0.0)
        boost_recharge = self.get_float(boost_elem, "recharge", 0.0)
        boost_acceleration = self.get_float(boost_elem, "acceleration", 0.0)
        boost_attack = self.get_float(boost_elem, "attack", 0.0)
        boost_release = self.get_float(boost_elem, "release", 0.0)
        boost_coast = self.get_float(boost_elem, "coast", 0.0)

        # === TRAVEL ===
        travel_elem = props.find("travel")
        travel_charge = self.get_float(travel_elem, "charge", 0.0)
        travel_thrust = self.get_float(travel_elem, "thrust", 0.0)
        travel_attack = self.get_float(travel_elem, "attack", 0.0)
        travel_release = self.get_float(travel_elem, "release", 0.0)

        # Validate engine - exclude video/virtual macros
        exclusion_reason = should_exclude_equipment(macro_name)
        if exclusion_reason:
            self.logger.debug(f"Excluding {macro_name}: {exclusion_reason}")
            return None

        return EngineData(
            macro_name=macro_name,
            name=name,
            size=size,
            mk_level=mk_level,
            basename=basename,
            shortname=shortname,
            description=description,
            makerrace=makerrace,
            hull_integrated=hull_integrated,
            forward_thrust=forward_thrust,
            reverse_thrust=reverse_thrust,
            boost_duration=boost_duration,
            boost_thrust=boost_thrust,
            boost_recharge=boost_recharge,
            boost_acceleration=boost_acceleration,
            boost_attack=boost_attack,
            boost_release=boost_release,
            boost_coast=boost_coast,
            travel_charge=travel_charge,
            travel_thrust=travel_thrust,
            travel_attack=travel_attack,
            travel_release=travel_release,
            component_ref=component_ref
        )

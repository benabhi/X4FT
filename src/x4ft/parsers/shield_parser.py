"""Parser for shield generator macros."""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from lxml import etree

from .base_parser import BaseParser
from .validation import should_exclude_equipment


@dataclass
class ShieldData:
    """Parsed shield generator data."""

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
    hull: int = 0
    hull_integrated: bool = False

    # Shield capacity and recharge
    capacity: int = 0
    recharge_rate: float = 0.0
    recharge_delay: float = 0.0

    # Component reference
    component_ref: Optional[str] = None

    # Tags (from wares.xml, populated later)
    tags: str = ""


class ShieldParser(BaseParser):
    """Parses shield generator macro XML files."""

    # Size mapping
    SIZE_MAP = {
        "_xs_": "xs",
        "_s_": "s",
        "_m_": "m",
        "_l_": "l",
        "_xl_": "xl",
    }

    def __init__(self, extracted_path: Path, macro_index: Dict[str, str], text_resolver=None):
        """Initialize shield parser.

        Args:
            extracted_path: Root of extracted files
            macro_index: Mapping of macro_name -> file_path from index/macros.xml
            text_resolver: Optional text resolver for names
        """
        super().__init__(extracted_path, text_resolver)
        self.macro_index = macro_index

    def parse(self) -> List[ShieldData]:
        """Parse all shield generator macros.

        Returns:
            List of ShieldData objects
        """
        shields = []

        # Find shield macro files from filesystem
        shield_files = []
        props_path = self.extracted_path / "assets" / "props"

        if props_path.exists():
            for xml_file in props_path.rglob("shield_*_macro.xml"):
                rel_path = xml_file.relative_to(self.extracted_path)
                macro_name = xml_file.stem
                shield_files.append((macro_name, str(rel_path)))

        self.logger.info(f"Found {len(shield_files)} shield macro files")

        for macro_name, macro_path in shield_files:
            shield = self._parse_shield_macro(macro_name, macro_path)
            if shield:
                shields.append(shield)

        self.logger.info(f"Successfully parsed {len(shields)} shields")
        return shields

    def _parse_shield_macro(self, macro_name: str, macro_path: str) -> Optional[ShieldData]:
        """Parse a single shield macro file.

        Args:
            macro_name: Name of the macro
            macro_path: Relative path to macro file

        Returns:
            ShieldData object or None if parsing failed
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
        hull = self.get_int(hull_elem, "max", 0)
        hull_integrated = self.get_bool(hull_elem, "integrated", False)

        # === RECHARGE (SHIELD CAPACITY & RECHARGE) ===
        recharge_elem = props.find("recharge")
        capacity = self.get_int(recharge_elem, "max", 0)
        recharge_rate = self.get_float(recharge_elem, "rate", 0.0)
        recharge_delay = self.get_float(recharge_elem, "delay", 0.0)

        # Validate shield - exclude video/virtual macros
        exclusion_reason = should_exclude_equipment(macro_name)
        if exclusion_reason:
            self.logger.debug(f"Excluding {macro_name}: {exclusion_reason}")
            return None

        return ShieldData(
            macro_name=macro_name,
            name=name,
            size=size,
            mk_level=mk_level,
            basename=basename,
            shortname=shortname,
            description=description,
            makerrace=makerrace,
            hull=hull,
            hull_integrated=hull_integrated,
            capacity=capacity,
            recharge_rate=recharge_rate,
            recharge_delay=recharge_delay,
            component_ref=component_ref
        )

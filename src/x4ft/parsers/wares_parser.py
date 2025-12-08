"""Parser for libraries/wares.xml - master list of all game items."""

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from lxml import etree

from .base_parser import BaseParser


@dataclass
class WareData:
    """Represents a ware from wares.xml."""

    id: str
    name: str
    description: str
    ware_type: str  # ship, weapon, shield, engine, etc.
    tags: List[str]
    price_min: int
    price_avg: int
    price_max: int
    component_ref: Optional[str]
    owners: List[str]  # Faction IDs


class WaresParser(BaseParser):
    """Parses libraries/wares.xml - the master list of all game items."""

    WARES_PATH = "libraries/wares.xml"

    def __init__(self, extracted_path: Path, text_resolver=None):
        """Initialize wares parser.

        Args:
            extracted_path: Root of extracted files
            text_resolver: Optional text resolver for names
        """
        super().__init__(extracted_path, text_resolver)

    # Map ware tags to types
    TAG_TO_TYPE = {
        "ship": "ship",
        "weapon": "weapon",
        "turret": "turret",
        "shield": "shield",
        "engine": "engine",
        "thruster": "thruster",
        "software": "software",
        "missile": "missile",
        "countermeasure": "countermeasure",
        "drone": "drone",
    }

    def parse(self) -> List[WareData]:
        """Parse all wares from wares.xml.

        Returns:
            List of WareData objects
        """
        root = self.parse_file(self.WARES_PATH)
        if root is None:
            return []

        wares = []

        for ware_elem in root.findall(".//ware"):
            ware = self._parse_ware(ware_elem)
            if ware:
                wares.append(ware)

        self.logger.info(f"Parsed {len(wares)} wares from wares.xml")
        return wares

    def _parse_ware(self, elem: etree._Element) -> Optional[WareData]:
        """Parse a single <ware> element.

        Args:
            elem: XML element for ware

        Returns:
            WareData object or None if invalid
        """
        ware_id = elem.get("id")
        if not ware_id:
            return None

        # Parse tags
        tags_str = elem.get("tags", "")
        tags = [tag.strip() for tag in tags_str.split() if tag.strip()]

        # Determine ware type from tags
        ware_type = "other"
        for tag in tags:
            if tag in self.TAG_TO_TYPE:
                ware_type = self.TAG_TO_TYPE[tag]
                break

        # Parse price
        price_elem = elem.find("price")
        price_min = self.get_int(price_elem, "min", 0)
        price_avg = self.get_int(price_elem, "average", 0)
        price_max = self.get_int(price_elem, "max", 0)

        # Get component reference (links to macro)
        component_elem = elem.find("component")
        component_ref = component_elem.get("ref") if component_elem is not None else None

        # Get owner factions
        owners = []
        for owner in elem.findall(".//owner"):
            faction = owner.get("faction")
            if faction:
                owners.append(faction)

        return WareData(
            id=ware_id,
            name=self.get_text_value(elem, "name"),
            description=self.get_text_value(elem, "description"),
            ware_type=ware_type,
            tags=tags,
            price_min=price_min,
            price_avg=price_avg,
            price_max=price_max,
            component_ref=component_ref,
            owners=owners
        )

    def get_wares_by_type(self, ware_type: str) -> List[WareData]:
        """Get wares filtered by type.

        Args:
            ware_type: Type to filter (ship, weapon, etc.)

        Returns:
            List of matching wares
        """
        all_wares = self.parse()
        return [w for w in all_wares if w.ware_type == ware_type]

    def get_ware_map(self) -> dict:
        """Get mapping of ware_id -> WareData.

        Returns:
            Dictionary mapping ware IDs to WareData
        """
        wares = self.parse()
        return {w.id: w for w in wares}

"""Parser for bullet macros - weapon projectile data."""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from lxml import etree

from .base_parser import BaseParser


@dataclass
class BulletData:
    """Parsed bullet/projectile data."""

    macro_name: str

    # Bullet properties
    speed: float = 0.0
    lifetime: float = 0.0
    amount: int = 1
    barrelamount: int = 1

    # Damage
    damage_value: float = 0.0
    damage_repair: float = 0.0

    # Heat per shot
    heat_value: float = 0.0

    # Reload
    reload_rate: float = 0.0

    # Ammunition
    ammunition_value: int = 0
    ammunition_reload: float = 0.0

    # Calculated fields
    range_max: float = 0.0  # speed * lifetime


class BulletParser(BaseParser):
    """Parses bullet macro XML files."""

    def __init__(self, extracted_path: Path, text_resolver=None):
        """Initialize bullet parser.

        Args:
            extracted_path: Root of extracted files
            text_resolver: Optional text resolver for names
        """
        super().__init__(extracted_path, text_resolver)

    def parse(self) -> Dict[str, BulletData]:
        """Parse all bullet macros.

        Returns:
            Dictionary mapping bullet macro names to BulletData objects
        """
        bullets = {}

        # Find bullet macro files from filesystem
        bullet_files = []
        fx_path = self.extracted_path / "assets" / "fx" / "weaponfx" / "macros"

        if fx_path.exists():
            for xml_file in fx_path.glob("bullet_*_macro.xml"):
                macro_name = xml_file.stem
                rel_path = xml_file.relative_to(self.extracted_path)
                bullet_files.append((macro_name, str(rel_path)))

        self.logger.info(f"Found {len(bullet_files)} bullet macro files")

        for macro_name, macro_path in bullet_files:
            bullet = self._parse_bullet_macro(macro_name, macro_path)
            if bullet:
                bullets[macro_name] = bullet

        self.logger.info(f"Successfully parsed {len(bullets)} bullets")
        return bullets

    def _parse_bullet_macro(self, macro_name: str, macro_path: str) -> Optional[BulletData]:
        """Parse a single bullet macro file.

        Args:
            macro_name: Name of the macro
            macro_path: Relative path to macro file

        Returns:
            BulletData object or None if parsing failed
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

        # Get properties
        props = macro_elem.find("properties")
        if props is None:
            self.logger.warning(f"No properties found for {macro_name}")
            return None

        # === BULLET PROPERTIES ===
        bullet_elem = props.find("bullet")
        speed = self.get_float(bullet_elem, "speed", 0.0)
        lifetime = self.get_float(bullet_elem, "lifetime", 0.0)
        amount = self.get_int(bullet_elem, "amount", 1)
        barrelamount = self.get_int(bullet_elem, "barrelamount", 1)

        # === DAMAGE ===
        damage_elem = props.find("damage")
        damage_value = self.get_float(damage_elem, "value", 0.0)
        damage_repair = self.get_float(damage_elem, "repair", 0.0)

        # === HEAT ===
        heat_elem = props.find("heat")
        heat_value = self.get_float(heat_elem, "value", 0.0)

        # === RELOAD ===
        reload_elem = props.find("reload")
        reload_rate = self.get_float(reload_elem, "rate", 0.0)

        # === AMMUNITION ===
        ammunition_elem = props.find("ammunition")
        ammunition_value = self.get_int(ammunition_elem, "value", 0)
        ammunition_reload = self.get_float(ammunition_elem, "reload", 0.0)

        # Calculate max range
        range_max = speed * lifetime if speed and lifetime else 0.0

        return BulletData(
            macro_name=macro_name,
            speed=speed,
            lifetime=lifetime,
            amount=amount,
            barrelamount=barrelamount,
            damage_value=damage_value,
            damage_repair=damage_repair,
            heat_value=heat_value,
            reload_rate=reload_rate,
            ammunition_value=ammunition_value,
            ammunition_reload=ammunition_reload,
            range_max=range_max
        )

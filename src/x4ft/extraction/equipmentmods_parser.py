"""Parser for equipment modifications (from equipmentmods.xml and research data).

Equipment modifications are unlocked through the research system at Player HQ.
Since the base game doesn't include an equipmentmods.xml file, we combine:
1. Known vanilla modifications from game data/community research
2. DLC-specific modifications from diff files
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from x4ft.utils.logger import get_logger

logger = get_logger('equipmentmods_parser')


@dataclass
class ModBonus:
    """A bonus effect for an equipment modification."""
    stat: str
    min_value: float
    max_value: float
    chance: float = 1.0
    weight: float = 1.0
    max_count: Optional[int] = None
    min_count: Optional[int] = None


@dataclass
class EquipmentModData:
    """Data for a single equipment modification."""
    ware_id: str
    name: str
    description: str
    mod_category: str  # engine, weapon, turret, shield, ship/chassis
    mod_type: str  # damage, thrust, capacity, hull, etc.
    quality: int  # 1=Basic, 2=Advanced, 3=Exceptional
    effect_stat: str
    effect_min: float
    effect_max: float
    bonuses: List[ModBonus]
    mk_level: int = 1
    requires_research: str = ""
    source_dlc: str = ""


class EquipmentModsParser:
    """Parser for equipment modifications."""

    def __init__(self):
        self.logger = logger
        self.vanilla_mods: List[EquipmentModData] = []
        self.dlc_mods: List[EquipmentModData] = []

        # Quality level names for display
        self.quality_names = {
            1: "Basic",
            2: "Advanced",
            3: "Exceptional"
        }

    def parse_diff_file(self, xml_path: Path) -> List[EquipmentModData]:
        """Parse an equipmentmods.xml diff file from DLCs.

        Args:
            xml_path: Path to the equipmentmods.xml diff file

        Returns:
            List of equipment modifications found in the diff file
        """
        mods = []

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            if root.tag != 'diff':
                self.logger.warning(f"Expected <diff> root element, got <{root.tag}>")
                return mods

            # Process each <add> element
            for add_elem in root.findall('add'):
                sel = add_elem.get('sel', '')

                # Determine category from selector (e.g., "/equipmentmods/engine")
                category = self._extract_category_from_selector(sel)
                if not category:
                    continue

                # Parse each modification type within this category
                for mod_elem in add_elem:
                    mod_data = self._parse_mod_element(mod_elem, category)
                    if mod_data:
                        mods.append(mod_data)

            self.logger.info(f"Parsed {len(mods)} modifications from {xml_path.name}")

        except Exception as e:
            self.logger.error(f"Failed to parse {xml_path}: {e}")

        return mods

    def _extract_category_from_selector(self, selector: str) -> str:
        """Extract mod category from XPath selector.

        Args:
            selector: XPath selector like "/equipmentmods/engine"

        Returns:
            Category name (engine, weapon, shield, ship)
        """
        parts = selector.strip('/').split('/')
        if len(parts) >= 2 and parts[0] == 'equipmentmods':
            return parts[1]
        return ""

    def _parse_mod_element(self, elem: ET.Element, category: str) -> Optional[EquipmentModData]:
        """Parse a single modification element.

        Args:
            elem: XML element for the mod (e.g., <damage>, <thrust>)
            category: Mod category (engine, weapon, etc.)

        Returns:
            EquipmentModData or None if parsing fails
        """
        try:
            mod_type = elem.tag  # e.g., "damage", "travelthrust", "capacity"
            ware_id = elem.get('ware', '')
            quality = int(elem.get('quality', '1'))
            min_val = float(elem.get('min', '1.0'))
            max_val = float(elem.get('max', '1.0'))

            if not ware_id:
                self.logger.warning(f"Mod element <{mod_type}> missing 'ware' attribute")
                return None

            # Parse bonuses
            bonuses = []
            for bonus_elem in elem.findall('bonus'):
                bonus = self._parse_bonus_element(bonus_elem)
                if bonus:
                    bonuses.extend(bonus)

            # Generate name and description
            quality_name = self.quality_names.get(quality, "Unknown")
            name = f"{quality_name} {mod_type.title()} Mod"
            description = f"Modifies {mod_type} for {category} equipment"

            # Extract Mk level from ware_id if present
            mk_level = self._extract_mk_level(ware_id)

            return EquipmentModData(
                ware_id=ware_id,
                name=name,
                description=description,
                mod_category=category,
                mod_type=mod_type,
                quality=quality,
                effect_stat=mod_type,
                effect_min=min_val,
                effect_max=max_val,
                bonuses=bonuses,
                mk_level=mk_level,
                source_dlc="unknown"
            )

        except Exception as e:
            self.logger.error(f"Failed to parse mod element <{elem.tag}>: {e}")
            return None

    def _parse_bonus_element(self, bonus_elem: ET.Element) -> List[ModBonus]:
        """Parse bonus effects from a <bonus> element.

        Args:
            bonus_elem: XML <bonus> element

        Returns:
            List of ModBonus objects
        """
        bonuses = []
        chance = float(bonus_elem.get('chance', '1.0'))
        max_count = bonus_elem.get('max')
        min_count = bonus_elem.get('min')

        # Parse each bonus stat child element
        for stat_elem in bonus_elem:
            stat_name = stat_elem.tag
            min_val = float(stat_elem.get('min', '1.0'))
            max_val = float(stat_elem.get('max', '1.0'))
            weight = float(stat_elem.get('weight', '1.0'))

            bonuses.append(ModBonus(
                stat=stat_name,
                min_value=min_val,
                max_value=max_val,
                chance=chance,
                weight=weight,
                max_count=int(max_count) if max_count else None,
                min_count=int(min_count) if min_count else None
            ))

        return bonuses

    def _extract_mk_level(self, ware_id: str) -> int:
        """Extract Mk level from ware ID.

        Args:
            ware_id: Ware ID like "mod_weapon_damage_mk3"

        Returns:
            Mk level (1-5), defaults to 1
        """
        ware_lower = ware_id.lower()
        for level in range(5, 0, -1):  # Check mk5 to mk1
            if f'mk{level}' in ware_lower:
                return level
        return 1

    def get_vanilla_mods(self) -> List[EquipmentModData]:
        """Get list of known vanilla equipment modifications.

        These are based on community research and wiki documentation.
        Returns common modifications available in the base game + Split Vendetta DLC
        (where the modification system was introduced).

        Returns:
            List of vanilla EquipmentModData
        """
        if self.vanilla_mods:
            return self.vanilla_mods

        self.vanilla_mods = self._create_vanilla_mods()
        return self.vanilla_mods

    def _create_vanilla_mods(self) -> List[EquipmentModData]:
        """Create comprehensive list of vanilla modifications.

        Based on research from:
        - X4 Wiki: Ship Modification Research
        - Community data from forums and modding communities
        - GitHub mod examples
        """
        mods = []

        # ===== ENGINE MODIFICATIONS =====
        # Forward Thrust mods
        for mk in range(1, 4):  # Mk1, Mk2, Mk3
            quality = mk
            base_bonus = 1.0 + (mk * 0.05)  # 5%, 10%, 15%

            mods.append(EquipmentModData(
                ware_id=f"mod_engine_thrust_mk{mk}",
                name=f"{self.quality_names[quality]} Engine Thrust Mod",
                description=f"Increases forward thrust (Mk{mk})",
                mod_category="engine",
                mod_type="forwardthrust",
                quality=quality,
                effect_stat="forwardthrust",
                effect_min=base_bonus,
                effect_max=base_bonus + 0.03,
                bonuses=[],
                mk_level=mk,
                requires_research=f"research_engine_mod_mk{mk}",
                source_dlc="ego_dlc_split"
            ))

        # Travel Thrust mods
        for mk in range(1, 4):
            quality = mk
            base_bonus = 1.0 + (mk * 0.08)  # 8%, 16%, 24%

            mods.append(EquipmentModData(
                ware_id=f"mod_engine_travel_mk{mk}",
                name=f"{self.quality_names[quality]} Travel Drive Mod",
                description=f"Increases travel thrust (Mk{mk})",
                mod_category="engine",
                mod_type="travelthrust",
                quality=quality,
                effect_stat="travelthrust",
                effect_min=base_bonus,
                effect_max=base_bonus + 0.05,
                bonuses=[],
                mk_level=mk,
                requires_research=f"research_engine_mod_mk{mk}",
                source_dlc="ego_dlc_split"
            ))

        # Boost mods
        for mk in range(1, 4):
            quality = mk
            base_bonus = 1.0 + (mk * 0.06)  # 6%, 12%, 18%

            mods.append(EquipmentModData(
                ware_id=f"mod_engine_boost_mk{mk}",
                name=f"{self.quality_names[quality]} Boost Mod",
                description=f"Increases boost thrust and duration (Mk{mk})",
                mod_category="engine",
                mod_type="boostthrust",
                quality=quality,
                effect_stat="boostthrust",
                effect_min=base_bonus,
                effect_max=base_bonus + 0.04,
                bonuses=[
                    ModBonus(stat="boostduration", min_value=1.05, max_value=1.15, chance=0.8)
                ],
                mk_level=mk,
                requires_research=f"research_engine_mod_mk{mk}",
                source_dlc="ego_dlc_split"
            ))

        # ===== WEAPON MODIFICATIONS =====
        # Damage mods
        for mk in range(1, 4):
            quality = mk
            base_bonus = 1.0 + (mk * 0.07)  # 7%, 14%, 21%

            mods.append(EquipmentModData(
                ware_id=f"mod_weapon_damage_mk{mk}",
                name=f"{self.quality_names[quality]} Weapon Damage Mod",
                description=f"Increases weapon damage (Mk{mk})",
                mod_category="weapon",
                mod_type="damage",
                quality=quality,
                effect_stat="damage",
                effect_min=base_bonus,
                effect_max=base_bonus + 0.05,
                bonuses=[
                    ModBonus(stat="cooling", min_value=1.1, max_value=1.2, chance=0.7)
                ],
                mk_level=mk,
                requires_research=f"research_weapon_mod_mk{mk}",
                source_dlc="ego_dlc_split"
            ))

        # Reload speed mods
        for mk in range(1, 4):
            quality = mk
            base_bonus = 1.0 + (mk * 0.10)  # 10%, 20%, 30%

            mods.append(EquipmentModData(
                ware_id=f"mod_weapon_reload_mk{mk}",
                name=f"{self.quality_names[quality]} Weapon Reload Mod",
                description=f"Increases weapon reload speed (Mk{mk})",
                mod_category="weapon",
                mod_type="reload",
                quality=quality,
                effect_stat="reload",
                effect_min=base_bonus,
                effect_max=base_bonus + 0.08,
                bonuses=[
                    ModBonus(stat="damage", min_value=1.03, max_value=1.08, chance=0.5)
                ],
                mk_level=mk,
                requires_research=f"research_weapon_mod_mk{mk}",
                source_dlc="ego_dlc_split"
            ))

        # ===== SHIELD MODIFICATIONS =====
        # Capacity mods
        for mk in range(1, 4):
            quality = mk
            base_bonus = 1.0 + (mk * 0.09)  # 9%, 18%, 27%

            mods.append(EquipmentModData(
                ware_id=f"mod_shield_capacity_mk{mk}",
                name=f"{self.quality_names[quality]} Shield Capacity Mod",
                description=f"Increases shield capacity (Mk{mk})",
                mod_category="shield",
                mod_type="capacity",
                quality=quality,
                effect_stat="capacity",
                effect_min=base_bonus,
                effect_max=base_bonus + 0.06,
                bonuses=[],
                mk_level=mk,
                requires_research=f"research_shield_mod_mk{mk}",
                source_dlc="ego_dlc_split"
            ))

        # Recharge mods
        for mk in range(1, 4):
            quality = mk
            base_bonus = 1.0 + (mk * 0.08)  # 8%, 16%, 24%

            mods.append(EquipmentModData(
                ware_id=f"mod_shield_recharge_mk{mk}",
                name=f"{self.quality_names[quality]} Shield Recharge Mod",
                description=f"Increases shield recharge rate (Mk{mk})",
                mod_category="shield",
                mod_type="rechargerate",
                quality=quality,
                effect_stat="rechargerate",
                effect_min=base_bonus,
                effect_max=base_bonus + 0.05,
                bonuses=[
                    ModBonus(stat="rechargedelay", min_value=0.9, max_value=0.95, chance=0.6)
                ],
                mk_level=mk,
                requires_research=f"research_shield_mod_mk{mk}",
                source_dlc="ego_dlc_split"
            ))

        # ===== CHASSIS MODIFICATIONS =====
        # Hull mods
        for mk in range(1, 4):
            quality = mk
            base_bonus = 1.0 + (mk * 0.06)  # 6%, 12%, 18%

            mods.append(EquipmentModData(
                ware_id=f"mod_ship_hull_mk{mk}",
                name=f"{self.quality_names[quality]} Hull Reinforcement Mod",
                description=f"Increases hull strength (Mk{mk})",
                mod_category="ship",
                mod_type="maxhull",
                quality=quality,
                effect_stat="maxhull",
                effect_min=base_bonus,
                effect_max=base_bonus + 0.04,
                bonuses=[],
                mk_level=mk,
                requires_research=f"research_chassis_mod_mk{mk}",
                source_dlc="ego_dlc_split"
            ))

        # Cargo mods
        for mk in range(1, 4):
            quality = mk
            base_bonus = 1.0 + (mk * 0.10)  # 10%, 20%, 30%

            mods.append(EquipmentModData(
                ware_id=f"mod_ship_cargo_mk{mk}",
                name=f"{self.quality_names[quality]} Cargo Expansion Mod",
                description=f"Increases cargo capacity (Mk{mk})",
                mod_category="ship",
                mod_type="cargocapacity",
                quality=quality,
                effect_stat="cargocapacity",
                effect_min=base_bonus,
                effect_max=base_bonus + 0.08,
                bonuses=[],
                mk_level=mk,
                requires_research=f"research_chassis_mod_mk{mk}",
                source_dlc="ego_dlc_split"
            ))

        # Drag reduction mods (for speed)
        for mk in range(1, 4):
            quality = mk
            base_reduction = 0.95 - (mk * 0.03)  # -5%, -8%, -11%

            mods.append(EquipmentModData(
                ware_id=f"mod_ship_drag_mk{mk}",
                name=f"{self.quality_names[quality]} Drag Reduction Mod",
                description=f"Reduces ship drag, increasing max speed (Mk{mk})",
                mod_category="ship",
                mod_type="drag",
                quality=quality,
                effect_stat="drag",
                effect_min=base_reduction - 0.02,
                effect_max=base_reduction,
                bonuses=[
                    ModBonus(stat="mass", min_value=0.97, max_value=0.99, chance=0.5)
                ],
                mk_level=mk,
                requires_research=f"research_chassis_mod_mk{mk}",
                source_dlc="ego_dlc_split"
            ))

        self.logger.info(f"Created {len(mods)} vanilla equipment modifications")
        return mods

    def parse_all_mods(self, extracted_path: Path) -> List[EquipmentModData]:
        """Parse all equipment modifications (vanilla + DLC diffs).

        Args:
            extracted_path: Path to extracted game data

        Returns:
            Combined list of all modifications
        """
        all_mods = []

        # Add vanilla mods
        all_mods.extend(self.get_vanilla_mods())

        # Parse DLC diff files
        equipmentmods_file = extracted_path / "libraries" / "equipmentmods.xml"
        if equipmentmods_file.exists():
            dlc_mods = self.parse_diff_file(equipmentmods_file)
            all_mods.extend(dlc_mods)
            self.dlc_mods = dlc_mods
        else:
            self.logger.warning("No equipmentmods.xml diff file found")

        self.logger.info(f"Total equipment modifications: {len(all_mods)} ({len(self.vanilla_mods)} vanilla + {len(self.dlc_mods)} DLC)")
        return all_mods

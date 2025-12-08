"""Parser for index/macros.xml and index/components.xml files."""

from pathlib import Path
from typing import Dict
from lxml import etree

from .base_parser import BaseParser


class MacroIndexParser(BaseParser):
    """Parses index/macros.xml to build macro name -> file path mapping."""

    MACROS_INDEX_PATH = "index/macros.xml"
    COMPONENTS_INDEX_PATH = "index/components.xml"

    def parse(self) -> Dict[str, str]:
        """Parse macro index and return mapping.

        Returns:
            Dictionary mapping macro_name -> relative_file_path
        """
        return self.parse_macro_index()

    def parse_macro_index(self) -> Dict[str, str]:
        """Parse index/macros.xml for macro definitions.

        Returns:
            Dictionary: {macro_name: file_path}

        Example:
            {
                "ship_arg_m_fighter_01_a_macro": "assets/units/size_m/macros/ship_arg_m_fighter_01_a_macro.xml",
                "weapon_gen_m_gatling_01_mk1_macro": "assets/props/WeaponSystems/Gatling/macros/weapon_gen_m_gatling_01_mk1_macro.xml"
            }
        """
        root = self.parse_file(self.MACROS_INDEX_PATH)
        if root is None:
            self.logger.warning("Macro index file not found, returning empty index")
            return {}

        macro_map = {}

        # Find all <entry> elements
        for entry in root.findall(".//entry"):
            name = entry.get("name")
            value = entry.get("value")

            if name and value:
                macro_map[name] = value

        self.logger.info(f"Loaded {len(macro_map)} macro definitions from index")
        return macro_map

    def parse_component_index(self) -> Dict[str, str]:
        """Parse index/components.xml for component definitions.

        Returns:
            Dictionary: {component_name: file_path}

        Example:
            {
                "ship_arg_m_fighter_01_a": "assets/units/size_m/ship_arg_m_fighter_01_a.xml"
            }
        """
        root = self.parse_file(self.COMPONENTS_INDEX_PATH)
        if root is None:
            self.logger.warning("Component index file not found, returning empty index")
            return {}

        component_map = {}

        for entry in root.findall(".//entry"):
            name = entry.get("name")
            value = entry.get("value")

            if name and value:
                component_map[name] = value

        self.logger.info(f"Loaded {len(component_map)} component definitions from index")
        return component_map

    def parse_both_indexes(self) -> tuple[Dict[str, str], Dict[str, str]]:
        """Parse both macro and component indexes.

        Returns:
            Tuple of (macro_map, component_map)
        """
        macros = self.parse_macro_index()
        components = self.parse_component_index()
        return macros, components

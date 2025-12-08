"""Base parser class for all XML parsers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Any, Optional
from lxml import etree
import logging


class BaseParser(ABC):
    """Base class for all XML parsers."""

    def __init__(self, extracted_path: Path, text_resolver=None):
        """Initialize parser.

        Args:
            extracted_path: Root directory of extracted game files
            text_resolver: Optional TextResolver instance for resolving {pageID,textID} refs
        """
        self.extracted_path = extracted_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.text_resolver = text_resolver

    def parse_file(self, relative_path: str) -> Optional[etree._Element]:
        """Parse XML file using lxml for better XPath support.

        Args:
            relative_path: Path relative to extracted_path

        Returns:
            Root element of parsed XML, or None if file doesn't exist
        """
        # Clean path - remove extensions/ prefix if present
        # XRCatTool extracts all files into a unified structure
        clean_path = relative_path
        if "extensions\\" in clean_path or "extensions/" in clean_path:
            # Remove the extensions/ego_dlc_xxx/ prefix
            parts = clean_path.replace("\\", "/").split("/")
            if parts[0] == "extensions":
                # Remove "extensions" and the DLC folder name
                clean_path = "/".join(parts[2:])

        file_path = self.extracted_path / clean_path
        if not file_path.exists():
            self.logger.warning(f"File not found: {clean_path}")
            return None

        try:
            return etree.parse(str(file_path)).getroot()
        except etree.XMLSyntaxError as e:
            self.logger.error(f"XML syntax error in {clean_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing {clean_path}: {e}")
            return None

    def get_text_value(self, element: etree._Element, attr: str) -> str:
        """Get attribute value, handling {pageID,textID} text references.

        In X4, many names are stored as references like "{20104,60301}"
        which point to entries in t/*.xml translation files.

        Args:
            element: XML element
            attr: Attribute name

        Returns:
            Resolved text value or original attribute value
        """
        value = element.get(attr, "")

        # Resolve text references if resolver is available
        if self.text_resolver and value.startswith("{"):
            return self.text_resolver.resolve(value)

        return value

    def get_int(self, element: Optional[etree._Element], attr: str, default: int = 0) -> int:
        """Safely get integer attribute.

        Args:
            element: XML element (can be None)
            attr: Attribute name
            default: Default value if not found

        Returns:
            Integer value or default
        """
        if element is None:
            return default

        value = element.get(attr)
        if value is None:
            return default

        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_float(self, element: Optional[etree._Element], attr: str, default: float = 0.0) -> float:
        """Safely get float attribute.

        Args:
            element: XML element (can be None)
            attr: Attribute name
            default: Default value if not found

        Returns:
            Float value or default
        """
        if element is None:
            return default

        value = element.get(attr)
        if value is None:
            return default

        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_bool(self, element: Optional[etree._Element], attr: str, default: bool = False) -> bool:
        """Safely get boolean attribute.

        Args:
            element: XML element (can be None)
            attr: Attribute name
            default: Default value if not found

        Returns:
            Boolean value or default
        """
        if element is None:
            return default

        value = element.get(attr)
        if value is None:
            return default

        return value.lower() in ('true', '1', 'yes')

    @abstractmethod
    def parse(self) -> List[Any]:
        """Parse and return list of parsed objects.

        This method must be implemented by subclasses.

        Returns:
            List of parsed objects
        """
        pass

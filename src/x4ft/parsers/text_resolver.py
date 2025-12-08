"""Text resolver for X4 {pageID,textID} references."""

from pathlib import Path
from typing import Dict, Optional, Tuple
from lxml import etree
import re
import logging


class TextResolver:
    """Resolves {pageID,textID} text references from t/*.xml files."""

    def __init__(self, extracted_path: Path, language_id: int = 44):
        """Initialize text resolver.

        Args:
            extracted_path: Root directory of extracted game files
            language_id: Language ID to use (44 = English)
        """
        self.extracted_path = extracted_path
        self.language_id = language_id
        self.logger = logging.getLogger(__name__)

        # Text lookup dictionary: (page_id, text_id) -> text
        self._text_cache: Dict[Tuple[int, int], str] = {}
        self._loaded = False

    def load_texts(self) -> None:
        """Load all text files for the configured language."""
        if self._loaded:
            return

        t_path = self.extracted_path / "t"
        if not t_path.exists():
            self.logger.warning(f"Translation directory not found: {t_path}")
            return

        # Find all XML files for this language
        # Language files are named like 0001-l044.xml where 044 is the language ID
        lang_suffix = f"-l{self.language_id:03d}.xml"

        text_files = list(t_path.glob(f"*{lang_suffix}"))

        if not text_files:
            self.logger.warning(f"No translation files found for language {self.language_id}")
            return

        self.logger.info(f"Loading {len(text_files)} translation files...")

        for text_file in text_files:
            try:
                tree = etree.parse(str(text_file))
                root = tree.getroot()

                # Parse each page
                for page in root.findall(".//page"):
                    page_id = int(page.get("id", 0))

                    # Parse each text entry
                    for t_elem in page.findall(".//t"):
                        text_id = int(t_elem.get("id", 0))
                        text = t_elem.text or ""

                        # Store in cache
                        self._text_cache[(page_id, text_id)] = text

            except Exception as e:
                self.logger.warning(f"Error parsing {text_file.name}: {e}")

        self._loaded = True
        self.logger.info(f"Loaded {len(self._text_cache)} text entries")

    def resolve(self, text_ref: str, sanitize: bool = True, max_depth: int = 5) -> str:
        """Resolve a text reference to actual text, handling nested references.

        Args:
            text_ref: Text reference in format "{pageID,textID}" or plain text
            sanitize: Whether to sanitize the resolved text (remove escape chars, etc.)
            max_depth: Maximum recursion depth for nested references

        Returns:
            Resolved text, or original string if not a reference or not found

        Examples:
            >>> resolver.resolve("{1001,1}")
            'Hull'
            >>> resolver.resolve("Plain text")
            'Plain text'
            >>> resolver.resolve("{20101,11002}")
            'Argon Destroyer Mk1'  # (if found)
        """
        # Ensure texts are loaded
        if not self._loaded:
            self.load_texts()

        result = self._resolve_recursive(text_ref, depth=0, max_depth=max_depth)

        # Sanitize if requested
        if sanitize and result:
            result = self.sanitize_text(result)

        return result

    def _resolve_recursive(self, text_ref: str, depth: int, max_depth: int) -> str:
        """Recursively resolve text references.

        Args:
            text_ref: Text reference or plain text
            depth: Current recursion depth
            max_depth: Maximum recursion depth

        Returns:
            Resolved text
        """
        if depth >= max_depth:
            return text_ref

        # Check if this is a text reference
        if not text_ref or not text_ref.startswith("{"):
            # Not a reference, but might contain references - resolve them
            return self._resolve_embedded_references(text_ref, depth, max_depth)

        # Parse the reference
        match = re.match(r"\{(\d+),\s*(\d+)\}", text_ref)
        if not match:
            return text_ref

        page_id = int(match.group(1))
        text_id = int(match.group(2))

        # Look up in cache
        text = self._text_cache.get((page_id, text_id))

        if text is None:
            # Not found, return original reference
            self.logger.debug(f"Text not found: {text_ref}")
            return text_ref

        # Resolve any embedded references in the resolved text
        return self._resolve_embedded_references(text, depth + 1, max_depth)

    def _resolve_embedded_references(self, text: str, depth: int, max_depth: int) -> str:
        """Find and resolve any embedded {pageID,textID} references in text.

        Args:
            text: Text that may contain embedded references
            depth: Current recursion depth
            max_depth: Maximum recursion depth

        Returns:
            Text with all embedded references resolved
        """
        if not text or depth >= max_depth:
            return text

        # Find all {pageID,textID} patterns
        pattern = r'\{(\d+),\s*(\d+)\}'

        def replace_reference(match):
            page_id = int(match.group(1))
            text_id = int(match.group(2))
            resolved = self._text_cache.get((page_id, text_id))
            if resolved:
                # Recursively resolve the resolved text
                return self._resolve_recursive(resolved, depth + 1, max_depth)
            return match.group(0)  # Return original if not found

        return re.sub(pattern, replace_reference, text)

    def sanitize_text(self, text: str) -> str:
        """Sanitize text by removing unnecessary escape characters and cleaning up.

        Args:
            text: Text to sanitize

        Returns:
            Cleaned text

        Examples:
            >>> sanitize_text(r"\(Gas\)")
            '(Gas)'
            >>> sanitize_text(r"Ship \{Name\}")
            'Ship {Name}'
            >>> sanitize_text("(Chthonios E (Gas))Chthonios E (Gas)")
            'Chthonios E (Gas)'
            >>> sanitize_text('PE(pronounce the letters "P" and "E" separately)')
            'PE'
        """
        if not text:
            return text

        # Remove backslash escapes before common characters
        # X4 XML escapes ( ) { } [ ] and other special chars
        text = text.replace(r'\(', '(')
        text = text.replace(r'\)', ')')
        text = text.replace(r'\{', '{')
        text = text.replace(r'\}', '}')
        text = text.replace(r'\[', '[')
        text = text.replace(r'\]', ']')

        # Remove any remaining unresolved text references
        # Pattern: {digits,digits} potentially with spaces
        text = re.sub(r'\s*\{\d+,\s*\d+\}\s*', '', text)

        # Remove pronunciation/explanation parentheticals
        # Patterns like: "PE(pronounce the letters...)" → "PE"
        #                "#dace(Pronounced Day-S...)" → "#dace"
        #                "Ship A(speak as letter names)" → "Ship A"
        pronunciation_keywords = [
            'pronounce',
            'pronounced',
            'pronunciation',
            'hashtag is not spoken',
            'see pronunciation',
            'same as',
            'the letters',
            'speak as letter names',
            'speak normally as numbers',
            'spoken as',
            'stands for',
        ]

        for keyword in pronunciation_keywords:
            # Case-insensitive removal of parenthetical explanations
            pattern = r'\([^)]*' + re.escape(keyword) + r'[^)]*\)'
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Remove duplicated text pattern: "(Text)Text" → "Text"
        # This handles cases like "(Chthonios E (Gas))Chthonios E (Gas)" → "Chthonios E (Gas)"
        # Also handles: "(Drone 1)Drone1" → "Drone 1"
        # Also handles: "(Xenon Shield Generator)XenonShield Generator" → "Xenon Shield Generator"
        # Match: (captured_text)captured_text
        # Use a loop to handle nested cases
        max_iterations = 3
        for _ in range(max_iterations):
            before = text

            # Pattern 1: Exact match with spaces - (Text With Spaces)Text With Spaces
            text = re.sub(r'\(([^()]+(?:\([^()]*\))?[^()]*)\)\1\s*', r'\1', text)

            # Pattern 2: Match where inside has spaces but outside doesn't
            # Example: (Drone 1)Drone1 → Drone 1
            # Strategy: Find (Word Number)WordNumber pattern
            text = re.sub(r'\(([A-Za-z]+)\s+(\d+)\)\1\2(?!\w)', r'\1 \2', text)

            # Pattern 3: Inside has spaces, outside doesn't, but they're the same text
            # Example: (Xenon Shield Generator)XenonShield Generator → Xenon Shield Generator
            # Strategy: Check if removing spaces makes them equal
            match = re.search(r'\(([^)]+)\)([^\s,]+(?:\s+[^\s,]+)*)', text)
            if match:
                inside = match.group(1)
                outside = match.group(2)
                # Compare without spaces
                if inside.replace(' ', '') == outside.replace(' ', ''):
                    # Keep the version with proper spacing (prefer inside if it has spaces)
                    if ' ' in inside:
                        text = text.replace(match.group(0), inside, 1)
                    else:
                        text = text.replace(match.group(0), outside, 1)

            # Pattern 4: Generic parenthetical prefix removal
            # Example: (Speed Upgrade Mk1)Spacesuit Thrusters Mk1 → Spacesuit Thrusters Mk1
            # If we have (SomethingDifferent)ActualName, keep ActualName
            # Only apply if patterns above didn't match
            if text == before:
                text = re.sub(r'^\([^)]+\)([A-Z][^,]*)', r'\1', text)

            if text == before:
                break  # No more matches

        # Clean up extra whitespace
        text = ' '.join(text.split())
        text = text.strip()

        return text

    def resolve_multiple(self, text_refs: list) -> list:
        """Resolve multiple text references at once.

        Args:
            text_refs: List of text references

        Returns:
            List of resolved texts
        """
        return [self.resolve(ref) for ref in text_refs]

    def get_text(self, page_id: int, text_id: int, default: str = "") -> str:
        """Get text by page and text IDs directly.

        Args:
            page_id: Page ID
            text_id: Text ID
            default: Default value if not found

        Returns:
            Resolved text or default
        """
        if not self._loaded:
            self.load_texts()

        return self._text_cache.get((page_id, text_id), default)

    def clear_cache(self) -> None:
        """Clear the text cache and force reload on next use."""
        self._text_cache.clear()
        self._loaded = False

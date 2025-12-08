"""Wrapper for Egosoft's XRCatTool.exe to extract game catalogs."""

import subprocess
from pathlib import Path
from typing import List, Optional
import logging


class CatalogExtractor:
    """Wrapper for XRCatTool.exe to extract .cat/.dat files."""

    def __init__(self, xrcattool_path: Path, output_path: Path):
        """Initialize catalog extractor.

        Args:
            xrcattool_path: Path to XRCatTool.exe
            output_path: Directory where files will be extracted
        """
        self.tool_path = xrcattool_path
        self.output_path = output_path
        self.logger = logging.getLogger(__name__)

        # Validate tool exists
        if not self.tool_path.exists():
            raise FileNotFoundError(f"XRCatTool not found at: {self.tool_path}")

    def extract(
        self,
        input_paths: List[Path],
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> bool:
        """Extract files from catalogs using XRCatTool.

        Files from later input_paths overwrite files from earlier paths,
        implementing the game's overlay/priority system.

        Args:
            input_paths: List of .cat files or directories, in load order
            include_patterns: Regex patterns for files to include (XRCatTool format)
            exclude_patterns: Regex patterns for files to exclude (XRCatTool format)

        Returns:
            True if extraction succeeded, False otherwise

        Example:
            extractor.extract(
                input_paths=[Path("01.cat"), Path("02.cat")],
                include_patterns=[r"^libraries/.*\.xml$", r"^index/.*\.xml$"]
            )
        """
        # Ensure output directory exists
        self.output_path.mkdir(parents=True, exist_ok=True)

        # Build command
        cmd = [str(self.tool_path)]

        # Add input paths (all at once, later files overwrite earlier)
        cmd.append("-in")
        cmd.extend([str(p) for p in input_paths])

        # Add output path
        cmd.extend(["-out", str(self.output_path)])

        # Add include patterns
        if include_patterns:
            cmd.append("-include")
            cmd.extend(include_patterns)

        # Add exclude patterns
        if exclude_patterns:
            cmd.append("-exclude")
            cmd.extend(exclude_patterns)

        self.logger.info(f"Running XRCatTool with {len(input_paths)} input catalogs")
        self.logger.debug(f"Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.tool_path.parent,  # Run from tool directory
                timeout=600  # 10 minute timeout
            )

            if result.returncode != 0:
                self.logger.error(f"XRCatTool failed with return code {result.returncode}")
                self.logger.error(f"stderr: {result.stderr}")
                return False

            self.logger.info("Extraction completed successfully")
            if result.stdout:
                self.logger.debug(f"stdout: {result.stdout}")

            return True

        except subprocess.TimeoutExpired:
            self.logger.error("XRCatTool timed out after 10 minutes")
            return False
        except Exception as e:
            self.logger.error(f"Error running XRCatTool: {e}")
            return False

    def extract_xml_only(self, input_paths: List[Path]) -> bool:
        """Extract only XML files needed for data extraction.

        This includes:
        - libraries/*.xml (wares, macros, components)
        - index/*.xml (macro/component indexes)
        - assets/**/*.xml (ship/equipment macros)
        - t/*.xml (translation files)

        Args:
            input_paths: List of .cat files in load order

        Returns:
            True if extraction succeeded
        """
        include = [
            r"^libraries/.*\.xml$",     # Wares, macro indexes
            r"^index/.*\.xml$",          # Component indexes
            r"^assets/.*\.xml$",         # Ship/equipment macros
            r"^t/.*\.xml$"               # Translation files (for names)
        ]

        # Exclude non-essential assets to save time/space
        # NOTE: We keep assets/fx/weaponfx/ for bullet macros (damage data)
        exclude = [
            r"^assets/fx/(?!weaponfx)",  # Effects except weaponfx - not needed
            r"^assets/environments/",    # Environments - not needed
            r"^assets/characters/",      # Characters - not needed
            r"^assets/audio/"            # Audio - not needed
        ]

        return self.extract(input_paths, include, exclude)

    def extract_specific_file(self, input_paths: List[Path], file_path: str, output_dir: Path) -> bool:
        """Extract a specific file from catalogs.

        Args:
            input_paths: List of .cat files to extract from
            file_path: Relative path of the specific file to extract (e.g., "libraries/wares.xml")
            output_dir: Directory where the file will be extracted

        Returns:
            True if extraction succeeded
        """
        # Temporarily change output path
        original_output = self.output_path
        self.output_path = output_dir

        try:
            # Convert file path to regex pattern (escape special chars, anchor to start)
            import re
            escaped_path = re.escape(file_path)
            include_pattern = f"^{escaped_path}$"

            result = self.extract(input_paths, [include_pattern], [])
            return result
        finally:
            # Restore original output path
            self.output_path = original_output

    def get_extraction_info(self) -> dict:
        """Get information about the last extraction.

        Returns:
            Dictionary with extraction info
        """
        if not self.output_path.exists():
            return {
                "extracted": False,
                "path": str(self.output_path),
                "file_count": 0
            }

        # Count extracted files
        xml_files = list(self.output_path.glob("**/*.xml"))

        return {
            "extracted": True,
            "path": str(self.output_path),
            "file_count": len(xml_files),
            "xml_files": len(xml_files)
        }

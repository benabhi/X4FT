"""Auto-detection of X4 Foundations installation and DLCs.

Scans all available drives to find X4 installation directories and
automatically detects installed DLCs with correct priority ordering.
"""

import os
import string
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass

from x4ft.utils.logger import get_logger

logger = get_logger('game_detector')


@dataclass
class DLCInfo:
    """Information about a detected DLC."""
    id: str
    name: str
    path: Path
    priority: int
    release_date: str  # For sorting


# DLC information with release dates for priority ordering
DLC_DATABASE = {
    'ego_dlc_mini_01': DLCInfo(
        id='ego_dlc_mini_01',
        name='Bonus Content',
        path=Path(),  # Set during detection
        priority=1,
        release_date='2018-11-30'  # Base game release
    ),
    'ego_dlc_split': DLCInfo(
        id='ego_dlc_split',
        name='Split Vendetta',
        path=Path(),
        priority=2,
        release_date='2020-03-31'
    ),
    'ego_dlc_terran': DLCInfo(
        id='ego_dlc_terran',
        name='Cradle of Humanity',
        path=Path(),
        priority=3,
        release_date='2021-03-16'
    ),
    'ego_dlc_pirate': DLCInfo(
        id='ego_dlc_pirate',
        name='Tides of Avarice',
        path=Path(),
        priority=4,
        release_date='2022-02-14'
    ),
    'ego_dlc_boron': DLCInfo(
        id='ego_dlc_boron',
        name='Kingdom End',
        path=Path(),
        priority=5,
        release_date='2023-08-15'
    ),
    'ego_dlc_timelines': DLCInfo(
        id='ego_dlc_timelines',
        name='Timelines',
        path=Path(),
        priority=6,
        release_date='2024-04-18'
    )
}


class GameDetector:
    """Detects X4 Foundations installation across all drives."""

    def __init__(self):
        self.logger = logger

    def get_available_drives(self) -> List[str]:
        """Get list of available drives on Windows.

        Returns:
            List of drive letters (e.g., ['C:', 'D:', 'E:'])
        """
        if os.name == 'nt':  # Windows
            drives = []
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drives.append(letter + ':')
            return drives
        else:  # Linux/Mac
            return ['/']

    def find_steam_installation(self) -> Optional[Path]:
        """Find X4 in Steam library folders.

        Checks common Steam installation paths and reads libraryfolders.vdf
        to find all Steam library locations.

        Returns:
            Path to X4 installation or None
        """
        self.logger.info("Searching for Steam installation...")

        # Common Steam paths
        common_steam_paths = [
            Path("C:/Program Files (x86)/Steam"),
            Path("C:/Program Files/Steam"),
            Path("D:/Steam"),
            Path("E:/Steam"),
        ]

        steam_paths_to_check = []

        # Find Steam installations
        for steam_path in common_steam_paths:
            if steam_path.exists():
                steam_paths_to_check.append(steam_path)

                # Try to read libraryfolders.vdf for additional library paths
                library_vdf = steam_path / "steamapps" / "libraryfolders.vdf"
                if library_vdf.exists():
                    try:
                        with open(library_vdf, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Simple parsing - look for "path" entries
                            for line in content.split('\n'):
                                if '"path"' in line:
                                    # Extract path between quotes
                                    parts = line.split('"')
                                    if len(parts) >= 4:
                                        library_path = Path(parts[3].replace('\\\\', '/'))
                                        if library_path.exists():
                                            steam_paths_to_check.append(library_path)
                    except Exception as e:
                        self.logger.warning(f"Could not parse libraryfolders.vdf: {e}")

        # Check each Steam library for X4
        for steam_path in steam_paths_to_check:
            x4_path = steam_path / "steamapps" / "common" / "X4 Foundations"
            if self._is_valid_x4_installation(x4_path):
                self.logger.info(f"Found Steam installation at: {x4_path}")
                return x4_path

        return None

    def find_gog_installation(self) -> Optional[Path]:
        """Find X4 in GOG Galaxy library.

        Returns:
            Path to X4 installation or None
        """
        self.logger.info("Searching for GOG installation...")

        common_gog_paths = [
            Path("C:/GOG Games/X4 Foundations"),
            Path("C:/Program Files (x86)/GOG Galaxy/Games/X4 Foundations"),
            Path("D:/GOG Games/X4 Foundations"),
        ]

        for gog_path in common_gog_paths:
            if self._is_valid_x4_installation(gog_path):
                self.logger.info(f"Found GOG installation at: {gog_path}")
                return gog_path

        return None

    def find_epic_installation(self) -> Optional[Path]:
        """Find X4 in Epic Games library.

        Returns:
            Path to X4 installation or None
        """
        self.logger.info("Searching for Epic Games installation...")

        common_epic_paths = [
            Path("C:/Program Files/Epic Games/X4Foundations"),
            Path("D:/Epic Games/X4Foundations"),
        ]

        for epic_path in common_epic_paths:
            if self._is_valid_x4_installation(epic_path):
                self.logger.info(f"Found Epic Games installation at: {epic_path}")
                return epic_path

        return None

    def scan_all_drives(self) -> Optional[Path]:
        """Scan all drives for X4 installation.

        This is a fallback method that searches common installation patterns
        across all available drives.

        Returns:
            Path to X4 installation or None
        """
        self.logger.info("Scanning all drives for X4 installation...")

        drives = self.get_available_drives()

        # Common installation patterns
        patterns = [
            "Games/X4 Foundations",
            "Games/X4Foundations",
            "steamapps/common/X4 Foundations",
            "GOG Games/X4 Foundations",
            "Epic Games/X4Foundations",
        ]

        for drive in drives:
            for pattern in patterns:
                potential_path = Path(drive) / pattern
                if self._is_valid_x4_installation(potential_path):
                    self.logger.info(f"Found installation at: {potential_path}")
                    return potential_path

        return None

    def _is_valid_x4_installation(self, path: Path) -> bool:
        """Check if a path contains a valid X4 installation.

        Args:
            path: Path to check

        Returns:
            True if valid X4 installation found
        """
        if not path.exists():
            return False

        # Check for essential files/folders
        essential_files = [
            path / "X4.exe",  # Main executable
            # Extensions folder might not exist on first install
        ]

        # Check for cat files (base game content)
        has_cat_files = any((path / f"{i:02d}.cat").exists() for i in range(1, 10))

        # Check for executable
        has_exe = (path / "X4.exe").exists()

        return has_exe and has_cat_files

    def detect_dlcs(self, game_path: Path) -> List[Dict]:
        """Detect installed DLCs in the game directory.

        Args:
            game_path: Path to X4 installation

        Returns:
            List of DLC configuration dictionaries
        """
        self.logger.info("Detecting installed DLCs...")

        extensions_dir = game_path / "extensions"
        if not extensions_dir.exists():
            self.logger.warning("No extensions directory found")
            return []

        detected_dlcs = []

        for dlc_id, dlc_info in DLC_DATABASE.items():
            dlc_path = extensions_dir / dlc_id
            if dlc_path.exists() and (dlc_path / "content.xml").exists():
                self.logger.info(f"Found DLC: {dlc_info.name}")

                detected_dlcs.append({
                    'id': dlc_id,
                    'name': dlc_info.name,
                    'path': str(dlc_path),
                    'enabled': True,
                    'priority': dlc_info.priority
                })

        # Sort by priority (chronological order)
        detected_dlcs.sort(key=lambda x: x['priority'])

        self.logger.info(f"Detected {len(detected_dlcs)} DLCs")
        return detected_dlcs

    def auto_detect(self) -> Optional[Tuple[Path, List[Dict]]]:
        """Auto-detect X4 installation and DLCs.

        Tries multiple detection methods in order:
        1. Steam installation
        2. GOG installation
        3. Epic Games installation
        4. Full drive scan (fallback)

        Returns:
            Tuple of (game_path, dlcs_list) or None if not found
        """
        self.logger.info("Starting auto-detection of X4 Foundations...")

        # Try Steam first (most common)
        game_path = self.find_steam_installation()

        # Try GOG
        if not game_path:
            game_path = self.find_gog_installation()

        # Try Epic Games
        if not game_path:
            game_path = self.find_epic_installation()

        # Last resort: scan all drives
        if not game_path:
            game_path = self.scan_all_drives()

        if not game_path:
            self.logger.warning("Could not auto-detect X4 installation")
            return None

        # Detect DLCs
        dlcs = self.detect_dlcs(game_path)

        self.logger.info(f"Auto-detection successful: {game_path}")
        return game_path, dlcs

    def validate_game_path(self, path: Path) -> Tuple[bool, Optional[str]]:
        """Validate a manually provided game path.

        Args:
            path: Path to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not path.exists():
            return False, f"Path does not exist: {path}"

        if not self._is_valid_x4_installation(path):
            return False, "Not a valid X4 Foundations installation (missing X4.exe or .cat files)"

        return True, None

    def get_xrcattool_path(self) -> Optional[Path]:
        """Find XRCatTool.exe in the project.

        Returns:
            Path to XRCatTool.exe or None
        """
        # Assuming we're running from project root or a known location
        possible_paths = [
            Path.cwd() / "tools" / "XTools_1.11" / "XRCatTool.exe",
            Path(__file__).parent.parent.parent.parent / "tools" / "XTools_1.11" / "XRCatTool.exe",
        ]

        for path in possible_paths:
            if path.exists():
                self.logger.info(f"Found XRCatTool at: {path}")
                return path

        self.logger.warning("XRCatTool.exe not found")
        return None

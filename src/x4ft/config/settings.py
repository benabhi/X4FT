"""Configuration management for X4FT."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import json
import logging


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"  # Overall logging level
    console_level: str = "INFO"  # Console output level
    file_level: str = "DEBUG"  # File output level
    max_file_size_mb: int = 10  # Max log file size before rotation
    backup_count: int = 5  # Number of backup log files to keep
    cleanup_days: int = 30  # Delete logs older than this

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "level": self.level,
            "console_level": self.console_level,
            "file_level": self.file_level,
            "max_file_size_mb": self.max_file_size_mb,
            "backup_count": self.backup_count,
            "cleanup_days": self.cleanup_days
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LoggingConfig":
        """Create from dictionary."""
        return cls(
            level=data.get("level", "INFO"),
            console_level=data.get("console_level", "INFO"),
            file_level=data.get("file_level", "DEBUG"),
            max_file_size_mb=data.get("max_file_size_mb", 10),
            backup_count=data.get("backup_count", 5),
            cleanup_days=data.get("cleanup_days", 30)
        )

    def get_level_int(self, level_name: str) -> int:
        """Convert level string to int."""
        return getattr(logging, level_name.upper(), logging.INFO)


@dataclass
class ExtensionConfig:
    """Configuration for a single DLC/extension."""

    id: str
    name: str
    path: Path
    enabled: bool = True
    priority: int = 0  # Higher priority loads later (overwrites earlier)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "path": str(self.path),
            "enabled": self.enabled,
            "priority": self.priority
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExtensionConfig":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            path=Path(data["path"]),
            enabled=data.get("enabled", True),
            priority=data.get("priority", 0)
        )


@dataclass
class X4FTConfig:
    """Main application configuration."""

    game_path: Path
    xrcattool_path: Path
    extraction_path: Path
    database_path: Path
    extensions: List[ExtensionConfig] = field(default_factory=list)
    cleanup_after_extraction: bool = False
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def load(cls, config_path: Path) -> "X4FTConfig":
        """Load configuration from JSON file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        extensions = [
            ExtensionConfig.from_dict(ext)
            for ext in data.get("extensions", [])
        ]

        logging_config = LoggingConfig.from_dict(data.get("logging", {}))

        return cls(
            game_path=Path(data["game_path"]),
            xrcattool_path=Path(data["xrcattool_path"]),
            extraction_path=Path(data["extraction_path"]),
            database_path=Path(data["database_path"]),
            extensions=extensions,
            cleanup_after_extraction=data.get("cleanup_after_extraction", False),
            logging=logging_config
        )

    def save(self, config_path: Path) -> None:
        """Save configuration to JSON file."""
        data = {
            "game_path": str(self.game_path),
            "xrcattool_path": str(self.xrcattool_path),
            "extraction_path": str(self.extraction_path),
            "database_path": str(self.database_path),
            "extensions": [ext.to_dict() for ext in self.extensions],
            "cleanup_after_extraction": self.cleanup_after_extraction,
            "logging": self.logging.to_dict()
        }

        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def create_default(cls, game_path: Path, project_root: Path) -> "X4FTConfig":
        """Create default configuration with auto-detected extensions."""
        xrcattool = project_root / "tools" / "XTools_1.11" / "XRCatTool.exe"
        extraction_path = project_root / "data" / "extracted"
        database_path = project_root / "data" / "x4ft.db"

        config = cls(
            game_path=game_path,
            xrcattool_path=xrcattool,
            extraction_path=extraction_path,
            database_path=database_path
        )

        # Auto-detect extensions
        config.extensions = config.auto_detect_extensions()

        return config

    def auto_detect_extensions(self) -> List[ExtensionConfig]:
        """Scan game directory for extensions and return them in load order."""
        extensions_path = self.game_path / "extensions"

        if not extensions_path.exists():
            return []

        # DLC priority order (higher number = loaded later = higher priority)
        dlc_priority = {
            "ego_dlc_mini_01": 1,   # Bonus Content
            "ego_dlc_split": 2,      # Split Vendetta
            "ego_dlc_terran": 3,     # Cradle of Humanity
            "ego_dlc_pirate": 4,     # Tides of Avarice
            "ego_dlc_boron": 5,      # Kingdom End
            "ego_dlc_timelines": 6,  # Timelines (highest priority)
        }

        # DLC display names
        dlc_names = {
            "ego_dlc_mini_01": "Bonus Content",
            "ego_dlc_split": "Split Vendetta",
            "ego_dlc_terran": "Cradle of Humanity",
            "ego_dlc_pirate": "Tides of Avarice",
            "ego_dlc_boron": "Kingdom End",
            "ego_dlc_timelines": "Timelines",
        }

        extensions = []

        for dlc_dir in extensions_path.iterdir():
            if not dlc_dir.is_dir():
                continue

            dlc_id = dlc_dir.name

            # Check if content.xml exists
            content_xml = dlc_dir / "content.xml"
            if not content_xml.exists():
                continue

            # Create extension config
            ext = ExtensionConfig(
                id=dlc_id,
                name=dlc_names.get(dlc_id, dlc_id),
                path=dlc_dir,
                enabled=True,
                priority=dlc_priority.get(dlc_id, 0)
            )
            extensions.append(ext)

        # Sort by priority
        extensions.sort(key=lambda x: x.priority)

        return extensions

    def get_catalog_load_order(self) -> List[Path]:
        """Get all catalog files in correct load order."""
        catalogs = []

        # Add base game catalogs (01.cat through 09.cat)
        for i in range(1, 10):
            cat_file = self.game_path / f"{i:02d}.cat"
            if cat_file.exists():
                catalogs.append(cat_file)

        # Add extension catalogs in priority order
        for ext in sorted(self.extensions, key=lambda x: x.priority):
            if not ext.enabled:
                continue

            # Each extension can have ext_01.cat, ext_02.cat, ext_03.cat
            for i in range(1, 4):
                ext_cat = ext.path / f"ext_{i:02d}.cat"
                if ext_cat.exists():
                    catalogs.append(ext_cat)

        return catalogs

    def validate(self) -> bool:
        """Validate configuration paths and settings."""
        # Check game path exists
        if not self.game_path.exists():
            raise ValueError(f"Game path does not exist: {self.game_path}")

        # Check at least one base catalog exists
        if not (self.game_path / "01.cat").exists():
            raise ValueError(f"No base catalogs found in: {self.game_path}")

        # Check XRCatTool exists
        if not self.xrcattool_path.exists():
            raise ValueError(f"XRCatTool not found: {self.xrcattool_path}")

        return True

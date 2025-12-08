"""CLI script to extract game data from X4 Foundations."""

import sys
import logging
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from x4ft.config import X4FTConfig
from x4ft.extraction.extraction_manager import ExtractionManager
from x4ft.utils.logger import get_logger, set_console_level, setup_component_log


def setup_logging(level: str = "INFO"):
    """Configure logging for the extraction process.

    Uses the centralized X4FT logging system with rotating logs in logs/ directory.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Set console output level
    set_console_level(numeric_level)

    # Setup extraction-specific log file
    setup_component_log('extraction', level=numeric_level)


def progress_callback(message: str, progress: float):
    """Callback for extraction progress.

    Args:
        message: Progress message
        progress: Progress percentage (0.0 to 1.0)
    """
    bar_length = 40
    filled_length = int(bar_length * progress)
    bar = '#' * filled_length + '-' * (bar_length - filled_length)
    print(f'\r[{bar}] {progress*100:.0f}% - {message}', end='', flush=True)

    if progress >= 1.0:
        print()  # New line when complete


def main():
    """Main entry point for extraction script."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Extract game data from X4 Foundations")
    parser.add_argument('-y', '--yes', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    print("=" * 60)
    print("X4FT - X4 Foundations Data Extractor")
    print("=" * 60)
    print()

    # Get project root
    project_root = Path(__file__).parent.parent
    config_path = project_root / "config.json"

    # Check if config exists
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        print()
        print("Please create a config.json file in the project root.")
        print("See config.example.json for an example.")
        sys.exit(1)

    try:
        # Load configuration
        print(f"Loading configuration from: {config_path}")
        config = X4FTConfig.load(config_path)

        # Setup logging
        setup_logging(config.logging.level)
        logger = get_logger('scripts.extract_game_data')

        # Display configuration
        print(f"  Game path: {config.game_path}")
        print(f"  XRCatTool: {config.xrcattool_path}")
        print(f"  Output DB: {config.database_path}")
        print(f"  Extensions: {len(config.extensions)}")
        for ext in config.extensions:
            status = "enabled" if ext.enabled else "disabled"
            print(f"    - {ext.name} ({status})")
        print()

        # Confirm before proceeding
        if not args.yes:
            print("This will extract game data and populate the database.")
            response = input("Continue? [Y/n]: ").strip().lower()
            if response and response != 'y':
                print("Extraction cancelled.")
                sys.exit(0)

        print()

        # Create extraction manager
        manager = ExtractionManager(config, progress_callback=progress_callback)

        # Run extraction
        logger.info("Starting extraction process...")
        success = manager.run_full_extraction()

        print()
        if success:
            print("[OK] Extraction completed successfully!")
            print(f"  Database: {config.database_path}")
            print(f"  Extracted files: {config.extraction_path}")
            sys.exit(0)
        else:
            print("[ERROR] Extraction failed. Check logs/extraction.log for details.")
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        logging.exception("Extraction failed with exception:")
        sys.exit(1)


if __name__ == "__main__":
    main()

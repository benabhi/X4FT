"""Helper script to create config.json automatically."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from x4ft.config import X4FTConfig


def main():
    """Create config.json interactively."""
    print("=" * 60)
    print("X4FT - Configuration Generator")
    print("=" * 60)
    print()

    # Get game path
    default_game_path = r"D:\Games\steamapps\common\X4 Foundations"
    print(f"Enter X4 Foundations installation path")
    print(f"Default: {default_game_path}")
    game_path_input = input("Game path: ").strip()

    if not game_path_input:
        game_path = Path(default_game_path)
    else:
        game_path = Path(game_path_input)

    # Validate game path
    if not game_path.exists():
        print(f"Error: Path does not exist: {game_path}")
        sys.exit(1)

    if not (game_path / "01.cat").exists():
        print(f"Error: No X4 catalogs found in: {game_path}")
        print("Make sure this is the correct X4 Foundations installation directory.")
        sys.exit(1)

    print(f"✓ Found X4 installation at: {game_path}")
    print()

    # Project root
    project_root = Path(__file__).parent.parent

    # Create config with auto-detected extensions
    print("Auto-detecting DLCs...")
    config = X4FTConfig.create_default(game_path, project_root)

    print(f"Found {len(config.extensions)} DLCs:")
    for ext in config.extensions:
        print(f"  - {ext.name} (priority: {ext.priority})")
    print()

    # Save config
    config_path = project_root / "config.json"
    config.save(config_path)

    print(f"✓ Configuration saved to: {config_path}")
    print()
    print("You can now run the extraction script:")
    print("  python scripts/extract_game_data.py")
    print()


if __name__ == "__main__":
    main()

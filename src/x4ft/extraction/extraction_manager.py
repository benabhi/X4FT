"""Orchestrates the complete data extraction pipeline."""

from pathlib import Path
from typing import Callable, Optional
import shutil
from datetime import datetime

from ..config import X4FTConfig
from ..database.connection import DatabaseManager
from ..database.schema import Ship, ShipSlot, Equipment, WeaponStats, ShieldStats, EngineStats, ThrusterStats, Faction, Consumable, ExtractorMetadata
from .catalog_extractor import CatalogExtractor
from .xml_diff_applicator import XMLDiffApplicator
from ..parsers.text_resolver import TextResolver
from ..parsers.macro_index_parser import MacroIndexParser
from ..parsers.wares_parser import WaresParser
from ..parsers.ship_parser import ShipParser
from ..parsers.weapon_parser import WeaponParser
from ..parsers.bullet_parser import BulletParser
from ..parsers.shield_parser import ShieldParser
from ..parsers.engine_parser import EngineParser
from ..parsers.thruster_parser import ThrusterParser
from ..parsers.validation import should_exclude_ship, should_exclude_equipment
from ..utils.logger import get_logger


class ExtractionManager:
    """Orchestrates the complete data extraction pipeline."""

    def __init__(
        self,
        config: X4FTConfig,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ):
        """Initialize extraction manager.

        Args:
            config: Application configuration
            progress_callback: Optional callback for progress updates (message, percentage)
        """
        self.config = config
        self.progress_callback = progress_callback
        self.logger = get_logger('extraction')

        # Initialize components
        self.extractor = CatalogExtractor(
            config.xrcattool_path,
            config.extraction_path
        )
        self.db_manager = DatabaseManager(config.database_path)

    def run_full_extraction(self) -> bool:
        """Run the complete extraction pipeline.

        Steps:
        1. Clean/prepare extraction directory
        2. Extract catalogs using XRCatTool
        3. Parse index files
        4. Parse wares
        5. Parse ships
        6. Populate database

        Returns:
            True if successful, False otherwise
        """
        try:
            self._report_progress("Validating configuration...", 0.0)
            self.config.validate()

            self._report_progress("Preparing extraction directory...", 0.05)
            self._prepare_extraction_directory()

            self._report_progress("Extracting game catalogs...", 0.10)
            if not self._extract_catalogs():
                return False

            self._report_progress("Applying XML diffs...", 0.25)
            self._apply_xml_diffs()

            self._report_progress("Loading text resolver...", 0.30)
            text_resolver = self._create_text_resolver()

            self._report_progress("Parsing macro indexes...", 0.40)
            macro_index, component_index = self._parse_indexes()

            self._report_progress("Parsing wares...", 0.50)
            wares = self._parse_wares(text_resolver)

            self._report_progress("Parsing ships...", 0.60)
            ships = self._parse_ships(macro_index, text_resolver)

            self._report_progress("Parsing weapons...", 0.65)
            weapons = self._parse_weapons(macro_index, text_resolver)

            self._report_progress("Parsing bullets...", 0.68)
            bullets = self._parse_bullets(text_resolver)

            self._report_progress("Parsing shields...", 0.70)
            shields = self._parse_shields(macro_index, text_resolver)

            self._report_progress("Parsing engines...", 0.73)
            engines = self._parse_engines(macro_index, text_resolver)

            self._report_progress("Parsing thrusters...", 0.76)
            thrusters = self._parse_thrusters(macro_index, text_resolver)

            self._report_progress("Creating database tables...", 0.80)
            self._setup_database()

            self._report_progress("Populating database...", 0.85)
            self._populate_database(wares, ships, weapons, bullets, shields, engines, thrusters)

            self._report_progress("Saving extraction metadata...", 0.95)
            self._save_metadata()

            self._report_progress("Extraction complete!", 1.0)
            self.logger.info("Extraction completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Extraction failed: {e}", exc_info=True)
            self._report_progress(f"Error: {e}", 0.0)
            return False

    def _prepare_extraction_directory(self) -> None:
        """Clean and prepare extraction directory."""
        if self.config.extraction_path.exists():
            self.logger.info(f"Cleaning extraction directory: {self.config.extraction_path}")
            # Don't delete, XRCatTool handles overwrites
        else:
            self.config.extraction_path.mkdir(parents=True, exist_ok=True)

    def _extract_catalogs(self) -> bool:
        """Extract game catalogs using XRCatTool.

        Returns:
            True if successful
        """
        catalogs = self.config.get_catalog_load_order()
        self.logger.info(f"Extracting {len(catalogs)} catalogs in priority order")

        for cat in catalogs:
            self.logger.debug(f"  - {cat.name}")

        return self.extractor.extract_xml_only(catalogs)

    def _parse_indexes(self) -> tuple:
        """Parse macro and component indexes.

        Returns:
            Tuple of (macro_index, component_index)
        """
        parser = MacroIndexParser(self.config.extraction_path)
        macro_index, component_index = parser.parse_both_indexes()

        self.logger.info(f"Loaded {len(macro_index)} macros and {len(component_index)} components")
        return macro_index, component_index

    def _create_text_resolver(self) -> TextResolver:
        """Create and initialize text resolver.

        Returns:
            TextResolver instance
        """
        resolver = TextResolver(self.config.extraction_path, language_id=44)  # English
        resolver.load_texts()
        return resolver

    def _parse_wares(self, text_resolver: TextResolver) -> list:
        """Parse wares from libraries/wares.xml.

        Args:
            text_resolver: Text resolver for names

        Returns:
            List of WareData objects
        """
        parser = WaresParser(self.config.extraction_path, text_resolver)
        wares = parser.parse()
        self.logger.info(f"Parsed {len(wares)} wares")
        return wares

    def _parse_ships(self, macro_index: dict, text_resolver: TextResolver) -> list:
        """Parse ship macros.

        Args:
            macro_index: Mapping of macro names to file paths
            text_resolver: Text resolver for names

        Returns:
            List of ShipData objects
        """
        parser = ShipParser(self.config.extraction_path, macro_index, text_resolver)
        ships = parser.parse()
        self.logger.info(f"Parsed {len(ships)} ships")
        return ships

    def _parse_weapons(self, macro_index: dict, text_resolver: TextResolver) -> list:
        """Parse weapon macros.

        Args:
            macro_index: Mapping of macro names to file paths
            text_resolver: Text resolver for names

        Returns:
            List of WeaponData objects
        """
        parser = WeaponParser(self.config.extraction_path, macro_index, text_resolver)
        weapons = parser.parse()
        self.logger.info(f"Parsed {len(weapons)} weapons")
        return weapons

    def _parse_bullets(self, text_resolver: TextResolver) -> dict:
        """Parse bullet macros.

        Args:
            text_resolver: Text resolver for names

        Returns:
            Dictionary mapping bullet macro names to BulletData objects
        """
        parser = BulletParser(self.config.extraction_path, text_resolver)
        bullets = parser.parse()
        self.logger.info(f"Parsed {len(bullets)} bullets")
        return bullets

    def _parse_shields(self, macro_index: dict, text_resolver: TextResolver) -> list:
        """Parse shield generator macros.

        Args:
            macro_index: Mapping of macro names to file paths
            text_resolver: Text resolver for names

        Returns:
            List of ShieldData objects
        """
        parser = ShieldParser(self.config.extraction_path, macro_index, text_resolver)
        shields = parser.parse()
        self.logger.info(f"Parsed {len(shields)} shields")
        return shields

    def _parse_engines(self, macro_index: dict, text_resolver: TextResolver) -> list:
        """Parse engine macros.

        Args:
            macro_index: Mapping of macro names to file paths
            text_resolver: Text resolver for names

        Returns:
            List of EngineData objects
        """
        parser = EngineParser(self.config.extraction_path, macro_index, text_resolver)
        engines = parser.parse()
        self.logger.info(f"Parsed {len(engines)} engines")
        return engines

    def _parse_thrusters(self, macro_index: dict, text_resolver: TextResolver) -> list:
        """Parse thruster macros.

        Args:
            macro_index: Mapping of macro names to file paths
            text_resolver: Text resolver for names

        Returns:
            List of ThrusterData objects
        """
        parser = ThrusterParser(self.config.extraction_path, macro_index, text_resolver)
        thrusters = parser.parse()
        self.logger.info(f"Parsed {len(thrusters)} thrusters")
        return thrusters

    def _setup_database(self) -> None:
        """Create or recreate database tables."""
        if self.db_manager.database_exists():
            self.logger.info("Database exists, recreating tables...")
            self.db_manager.recreate_tables()
        else:
            self.logger.info("Creating new database...")
            self.db_manager.create_tables()

    def _populate_database(self, wares: list, ships: list, weapons: list, bullets: dict, shields: list, engines: list, thrusters: list) -> None:
        """Populate database with parsed data.

        Args:
            wares: List of WareData objects
            ships: List of ShipData objects
            weapons: List of WeaponData objects
            bullets: Dictionary mapping bullet macro names to BulletData objects
            shields: List of ShieldData objects
            engines: List of EngineData objects
            thrusters: List of ThrusterData objects
        """
        with self.db_manager.get_session() as session:
            # Create wares price lookup dictionary (by component_ref / macro_name)
            wares_prices = {}
            for ware in wares:
                if ware.component_ref:
                    wares_prices[ware.component_ref] = {
                        'min': ware.price_min,
                        'avg': ware.price_avg,
                        'max': ware.price_max
                    }
            self.logger.info(f"Built price lookup for {len(wares_prices)} wares")

            # Insert ships with ALL attributes (filter out invalid ships)
            self.logger.info(f"Filtering and inserting {len(ships)} ships into database...")
            ships_inserted = 0
            ships_excluded = 0
            for ship_data in ships:
                # Check if ship should be excluded (NPC-only, story ships, etc.)
                exclusion_reason = should_exclude_ship(
                    ship_data.macro_name,
                    ship_data.hull_max,
                    ship_data.mass,
                    ship_data.ship_class,
                    ship_data.ship_type,
                    ship_data.makerrace,
                    ship_data.size
                )
                if exclusion_reason:
                    self.logger.debug(f"  Excluding ship {ship_data.macro_name}: {exclusion_reason}")
                    ships_excluded += 1
                    continue

                # Get prices from wares if available (use macro_name to match wares)
                prices = wares_prices.get(ship_data.macro_name, {'min': 0, 'avg': 0, 'max': 0})

                ship = Ship(
                    macro_name=ship_data.macro_name,
                    component_ref=ship_data.component_ref,
                    # Identification
                    name=ship_data.name,
                    basename=ship_data.basename,
                    description=ship_data.description,
                    variation=ship_data.variation,
                    shortvariation=ship_data.shortvariation,
                    makerrace=ship_data.makerrace,
                    icon=ship_data.icon,
                    # Classification
                    size=ship_data.size,
                    ship_type=ship_data.ship_type,
                    ship_class=ship_data.ship_class,
                    purpose_primary=ship_data.purpose_primary,
                    # Base stats
                    hull_max=ship_data.hull_max,
                    mass=ship_data.mass,
                    # Prices (from wares.xml)
                    price_min=prices['min'],
                    price_avg=prices['avg'],
                    price_max=prices['max'],
                    # Explosion damage
                    explosion_damage=ship_data.explosion_damage,
                    explosion_damage_shield=ship_data.explosion_damage_shield,
                    # Storage
                    cargo_capacity=ship_data.cargo_capacity,
                    missile_storage=ship_data.missile_storage,
                    drone_storage=ship_data.drone_storage,
                    unit_storage=ship_data.unit_storage,
                    # Crew
                    crew_capacity=ship_data.crew_capacity,
                    # Secrecy
                    secrecy_level=ship_data.secrecy_level,
                    # Physics - Inertia
                    pitch_inertia=ship_data.pitch_inertia,
                    yaw_inertia=ship_data.yaw_inertia,
                    roll_inertia=ship_data.roll_inertia,
                    # Physics - Drag
                    forward_drag=ship_data.forward_drag,
                    reverse_drag=ship_data.reverse_drag,
                    horizontal_drag=ship_data.horizontal_drag,
                    vertical_drag=ship_data.vertical_drag,
                    pitch_drag=ship_data.pitch_drag,
                    yaw_drag=ship_data.yaw_drag,
                    roll_drag=ship_data.roll_drag,
                    # Physics - Acceleration factors
                    forward_accfactor=ship_data.forward_accfactor,
                    # Jerk
                    jerk_forward_accel=ship_data.jerk_forward_accel,
                    jerk_forward_decel=ship_data.jerk_forward_decel,
                    jerk_forward_ratio=ship_data.jerk_forward_ratio,
                    jerk_boost_accel=ship_data.jerk_boost_accel,
                    jerk_boost_ratio=ship_data.jerk_boost_ratio,
                    jerk_travel_accel=ship_data.jerk_travel_accel,
                    jerk_travel_decel=ship_data.jerk_travel_decel,
                    jerk_travel_ratio=ship_data.jerk_travel_ratio,
                    jerk_strafe=ship_data.jerk_strafe,
                    jerk_angular=ship_data.jerk_angular,
                    # Thruster
                    thruster_tags=ship_data.thruster_tags,
                    # Sound
                    sound_occlusion_inside=ship_data.sound_occlusion_inside,
                    shipdetail_sound=ship_data.shipdetail_sound
                )
                session.add(ship)
                ships_inserted += 1

            session.flush()  # Flush to get ship IDs
            self.logger.info(f"Inserted {ships_inserted} ships ({ships_excluded} excluded: spacesuits/modules)")

            # Insert ship slots
            total_slots = 0
            for ship_data in ships:
                # Find the ship we just inserted
                ship = session.query(Ship).filter_by(macro_name=ship_data.macro_name).first()
                if ship:
                    for slot_data in ship_data.slots:
                        slot = ShipSlot(
                            ship_id=ship.id,
                            slot_name=slot_data.slot_name,
                            slot_type=slot_data.slot_type,
                            slot_size=slot_data.slot_size,
                            slot_index=slot_data.slot_index,
                            tags=slot_data.tags
                        )
                        session.add(slot)
                        total_slots += 1

            session.flush()
            self.logger.info(f"Inserted {total_slots} equipment slots")

            # Insert weapons (filter out invalid equipment)
            self.logger.info(f"Filtering and inserting {len(weapons)} weapons into database...")
            weapons_inserted = 0
            weapons_excluded = 0
            for weapon_data in weapons:
                # Check if equipment should be excluded
                exclusion_reason = should_exclude_equipment(weapon_data.macro_name)
                if exclusion_reason:
                    self.logger.debug(f"  Excluding weapon {weapon_data.macro_name}: {exclusion_reason}")
                    weapons_excluded += 1
                    continue

                # Get prices from wares if available
                prices = wares_prices.get(weapon_data.macro_name, {'min': 0, 'avg': 0, 'max': 0})

                equipment = Equipment(
                    macro_name=weapon_data.macro_name,
                    name=weapon_data.name,
                    description=weapon_data.description,
                    equipment_type=weapon_data.equipment_type,
                    size=weapon_data.size,
                    mk_level=weapon_data.mk_level,
                    hull=weapon_data.hull,
                    tags=weapon_data.tags,
                    price_min=prices['min'],
                    price_avg=prices['avg'],
                    price_max=prices['max']
                )
                session.add(equipment)
                weapons_inserted += 1

            session.flush()  # Flush to get equipment IDs
            self.logger.info(f"Inserted {weapons_inserted} weapons ({weapons_excluded} excluded: scenario/story/internal)")

            # Insert weapon stats (with bullet data for damage/DPS)
            weapon_stats_count = 0
            for weapon_data in weapons:
                # Find the equipment we just inserted
                equipment = session.query(Equipment).filter_by(macro_name=weapon_data.macro_name).first()
                if equipment:
                    # Get bullet data if available
                    bullet = bullets.get(weapon_data.bullet_class)

                    # Calculate DPS if we have bullet and reload data
                    damage_hull = bullet.damage_value if bullet else 0.0
                    damage_shield = damage_hull  # X4 doesn't separate hull/shield damage for bullets

                    # Calculate fire rate and DPS
                    fire_rate = 0.0
                    dps_hull = 0.0
                    dps_shield = 0.0
                    projectile_speed = bullet.speed if bullet else 0.0
                    range_max = bullet.range_max if bullet else 0.0

                    if bullet and bullet.reload_rate > 0:
                        fire_rate = bullet.reload_rate  # shots per second
                        dps_hull = damage_hull * fire_rate
                        dps_shield = damage_shield * fire_rate

                    weapon_stats = WeaponStats(
                        equipment_id=equipment.id,
                        damage_hull=damage_hull,
                        damage_shield=damage_shield,
                        fire_rate=fire_rate,
                        reload_time=0.0,  # Will calculate if needed
                        projectile_speed=projectile_speed,
                        range_max=range_max,
                        heat_per_shot=bullet.heat_value if bullet else weapon_data.heat_overheat,
                        heat_dissipation=weapon_data.heat_coolrate,
                        overheat_time=weapon_data.heat_cooldelay,
                        rotation_speed=weapon_data.rotation_speed_max,
                        dps_hull=dps_hull,
                        dps_shield=dps_shield
                    )
                    session.add(weapon_stats)
                    weapon_stats_count += 1

            session.flush()
            self.logger.info(f"Inserted {weapon_stats_count} weapon stats with damage/DPS data")

            # Insert shields (filter out invalid equipment)
            self.logger.info(f"Filtering and inserting {len(shields)} shields into database...")
            shields_inserted = 0
            shields_excluded = 0
            for shield_data in shields:
                # Check if equipment should be excluded
                exclusion_reason = should_exclude_equipment(shield_data.macro_name)
                if exclusion_reason:
                    self.logger.debug(f"  Excluding shield {shield_data.macro_name}: {exclusion_reason}")
                    shields_excluded += 1
                    continue

                # Get prices from wares if available
                prices = wares_prices.get(shield_data.macro_name, {'min': 0, 'avg': 0, 'max': 0})

                equipment = Equipment(
                    macro_name=shield_data.macro_name,
                    name=shield_data.name,
                    description=shield_data.description,
                    equipment_type="shield",
                    size=shield_data.size,
                    mk_level=shield_data.mk_level,
                    hull=shield_data.hull,
                    tags=shield_data.tags,
                    price_min=prices['min'],
                    price_avg=prices['avg'],
                    price_max=prices['max']
                )
                session.add(equipment)
                shields_inserted += 1

            session.flush()
            self.logger.info(f"Inserted {shields_inserted} shields ({shields_excluded} excluded: scenario/story/internal)")

            # Insert shield stats
            shield_stats_count = 0
            for shield_data in shields:
                equipment = session.query(Equipment).filter_by(macro_name=shield_data.macro_name).first()
                if equipment:
                    shield_stats = ShieldStats(
                        equipment_id=equipment.id,
                        capacity=shield_data.capacity,
                        recharge_rate=shield_data.recharge_rate,
                        recharge_delay=shield_data.recharge_delay
                    )
                    session.add(shield_stats)
                    shield_stats_count += 1

            session.flush()
            self.logger.info(f"Inserted {shield_stats_count} shield stats")

            # Insert engines (filter out invalid equipment)
            self.logger.info(f"Filtering and inserting {len(engines)} engines into database...")
            engines_inserted = 0
            engines_excluded = 0
            for engine_data in engines:
                # Check if equipment should be excluded
                exclusion_reason = should_exclude_equipment(engine_data.macro_name)
                if exclusion_reason:
                    self.logger.debug(f"  Excluding engine {engine_data.macro_name}: {exclusion_reason}")
                    engines_excluded += 1
                    continue

                # Get prices from wares if available
                prices = wares_prices.get(engine_data.macro_name, {'min': 0, 'avg': 0, 'max': 0})

                equipment = Equipment(
                    macro_name=engine_data.macro_name,
                    name=engine_data.name,
                    description=engine_data.description,
                    equipment_type="engine",
                    size=engine_data.size,
                    mk_level=engine_data.mk_level,
                    tags=engine_data.tags,
                    price_min=prices['min'],
                    price_avg=prices['avg'],
                    price_max=prices['max']
                )
                session.add(equipment)
                engines_inserted += 1

            session.flush()
            self.logger.info(f"Inserted {engines_inserted} engines ({engines_excluded} excluded: scenario/story/internal)")

            # Insert engine stats
            engine_stats_count = 0
            for engine_data in engines:
                equipment = session.query(Equipment).filter_by(macro_name=engine_data.macro_name).first()
                if equipment:
                    engine_stats = EngineStats(
                        equipment_id=equipment.id,
                        forward_thrust=engine_data.forward_thrust,
                        reverse_thrust=engine_data.reverse_thrust,
                        boost_thrust=engine_data.boost_thrust,
                        boost_duration=engine_data.boost_duration,
                        boost_recharge=engine_data.boost_recharge,
                        travel_thrust=engine_data.travel_thrust,
                        travel_charge_time=engine_data.travel_charge,
                        travel_attack_time=engine_data.travel_attack,
                        travel_release_time=engine_data.travel_release
                    )
                    session.add(engine_stats)
                    engine_stats_count += 1

            session.flush()
            self.logger.info(f"Inserted {engine_stats_count} engine stats")

            # Insert thrusters (filter out invalid equipment)
            self.logger.info(f"Filtering and inserting {len(thrusters)} thrusters into database...")
            thrusters_inserted = 0
            thrusters_excluded = 0
            for thruster_data in thrusters:
                # Check if equipment should be excluded
                exclusion_reason = should_exclude_equipment(thruster_data.macro_name)
                if exclusion_reason:
                    self.logger.debug(f"  Excluding thruster {thruster_data.macro_name}: {exclusion_reason}")
                    thrusters_excluded += 1
                    continue

                # Get prices from wares if available
                prices = wares_prices.get(thruster_data.macro_name, {'min': 0, 'avg': 0, 'max': 0})

                equipment = Equipment(
                    macro_name=thruster_data.macro_name,
                    name=thruster_data.name,
                    description=thruster_data.description,
                    equipment_type="thruster",
                    size=thruster_data.size,
                    mk_level=thruster_data.mk_level,
                    tags=thruster_data.tags,
                    price_min=prices['min'],
                    price_avg=prices['avg'],
                    price_max=prices['max']
                )
                session.add(equipment)
                thrusters_inserted += 1

            session.flush()
            self.logger.info(f"Inserted {thrusters_inserted} thrusters ({thrusters_excluded} excluded: scenario/story/internal)")

            # Insert thruster stats
            thruster_stats_count = 0
            for thruster_data in thrusters:
                equipment = session.query(Equipment).filter_by(macro_name=thruster_data.macro_name).first()
                if equipment:
                    thruster_stats = ThrusterStats(
                        equipment_id=equipment.id,
                        thrust_strafe=thruster_data.thrust_strafe,
                        thrust_pitch=thruster_data.thrust_pitch,
                        thrust_yaw=thruster_data.thrust_yaw,
                        thrust_roll=thruster_data.thrust_roll
                    )
                    session.add(thruster_stats)
                    thruster_stats_count += 1

            session.flush()
            self.logger.info(f"Inserted {thruster_stats_count} thruster stats")

            # Insert consumables (extracted from wares)
            self.logger.info(f"Extracting and inserting consumables from {len(wares)} wares...")
            consumables_inserted = 0

            for ware in wares:
                # Determine consumable type based on ware properties
                consumable_type = None
                ware_name_lower = ware.name.lower()
                ware_id_lower = ware.id.lower()

                # Categorize by name/id patterns
                if 'missile' in ware_name_lower or 'missile' in ware_id_lower:
                    consumable_type = 'missile'
                elif 'mine' in ware_name_lower and 'miner' not in ware_name_lower:
                    consumable_type = 'mine'
                elif 'satellite' in ware_name_lower or 'probe' in ware_id_lower or 'beacon' in ware_id_lower:
                    consumable_type = 'satellite'
                elif 'lasertower' in ware_id_lower or 'tower' in ware_name_lower:
                    consumable_type = 'laser_tower'
                elif ('drone' in ware_id_lower or 'drone' in ware_name_lower) and 'dronecomponents' not in ware_id_lower and 'module_gen_prod' not in ware_id_lower:
                    consumable_type = 'drone'
                elif 'countermeasure' in ware_id_lower or 'flare' in ware_id_lower:
                    consumable_type = 'countermeasure'

                # Skip if not a consumable
                if consumable_type is None:
                    continue

                # Extract size from ware_id if available (e.g., missile_*_s_* -> size='s')
                size = ""
                for size_code in ['_xs_', '_s_', '_m_', '_l_', '_xl_']:
                    if size_code in ware_id_lower:
                        size = size_code.strip('_')
                        break

                # Extract Mk level from name
                mk_level = 1
                if 'mk1' in ware_name_lower or 'mk 1' in ware_name_lower:
                    mk_level = 1
                elif 'mk2' in ware_name_lower or 'mk 2' in ware_name_lower:
                    mk_level = 2
                elif 'mk3' in ware_name_lower or 'mk 3' in ware_name_lower:
                    mk_level = 3

                # Create consumable entry
                consumable = Consumable(
                    ware_id=ware.id,
                    macro_name=ware.component_ref if ware.component_ref else None,
                    name=ware.name,
                    description=ware.description,
                    consumable_type=consumable_type,
                    size=size,
                    mk_level=mk_level,
                    price_min=ware.price_min,
                    price_avg=ware.price_avg,
                    price_max=ware.price_max,
                    tags=','.join(ware.tags) if ware.tags else ""
                )
                session.add(consumable)
                consumables_inserted += 1

            session.flush()
            self.logger.info(f"Inserted {consumables_inserted} consumables")

    def _apply_xml_diffs(self) -> None:
        """Apply XML diffs from DLCs to base game files.

        X4 uses XML diff files in DLCs for certain library files. This method:
        1. Identifies files that need diff merging (libraries/*.xml, index/*.xml)
        2. Extracts base game versions of these files
        3. Extracts DLC versions and applies diffs in priority order
        4. Writes merged files back to extraction directory
        """
        # Files that commonly use diff format in DLCs
        diff_files = [
            "libraries/wares.xml",
            "index/macros.xml",
            "index/components.xml",
        ]

        diff_applicator = XMLDiffApplicator()
        temp_dir = self.config.extraction_path.parent / "temp_diff"

        try:
            temp_dir.mkdir(parents=True, exist_ok=True)

            for rel_path in diff_files:
                self.logger.debug(f"Processing {rel_path} for diff merging...")

                # Extract base game version
                base_dir = temp_dir / "base"
                base_dir.mkdir(parents=True, exist_ok=True)

                base_catalogs = []
                for i in range(1, 10):
                    cat_file = self.config.game_path / f"{i:02d}.cat"
                    if cat_file.exists():
                        base_catalogs.append(cat_file)

                if not self.extractor.extract_specific_file(base_catalogs, rel_path, base_dir):
                    self.logger.warning(f"Could not extract base version of {rel_path}")
                    continue

                base_file = base_dir / rel_path
                if not base_file.exists():
                    self.logger.warning(f"Base file not found: {base_file}")
                    continue

                # Check if base is already a diff (shouldn't be)
                from lxml import etree
                try:
                    tree = etree.parse(str(base_file))
                    if tree.getroot().tag == "diff":
                        self.logger.info(f"{rel_path} base is a diff, skipping merge")
                        continue
                except:
                    continue

                # Extract DLC versions in priority order
                diff_files_list = []
                for ext in sorted(self.config.extensions, key=lambda x: x.priority):
                    if not ext.enabled:
                        continue

                    dlc_dir = temp_dir / ext.id
                    dlc_dir.mkdir(parents=True, exist_ok=True)

                    # Try to extract from this DLC's catalogs
                    dlc_catalogs = []
                    for i in range(1, 4):
                        ext_cat = ext.path / f"ext_{i:02d}.cat"
                        if ext_cat.exists():
                            dlc_catalogs.append(ext_cat)

                    if dlc_catalogs:
                        self.extractor.extract_specific_file(dlc_catalogs, rel_path, dlc_dir)
                        dlc_file = dlc_dir / rel_path
                        if dlc_file.exists():
                            diff_files_list.append(dlc_file)

                # Apply diffs to create merged file
                if diff_files_list:
                    output_file = self.config.extraction_path / rel_path
                    if diff_applicator.apply_diffs(base_file, diff_files_list, output_file):
                        self.logger.info(f"Successfully merged {len(diff_files_list)} diffs for {rel_path}")
                    else:
                        self.logger.warning(f"Failed to merge diffs for {rel_path}")

        except Exception as e:
            self.logger.error(f"Error applying XML diffs: {e}")
        finally:
            # Clean up temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _save_metadata(self) -> None:
        """Save extraction metadata to database."""
        with self.db_manager.get_session() as session:
            metadata = [
                ExtractorMetadata(key="last_extraction_time", value=datetime.now().isoformat()),
                ExtractorMetadata(key="game_path", value=str(self.config.game_path)),
                ExtractorMetadata(key="schema_version", value="1.0"),
                ExtractorMetadata(key="ship_count", value=str(self.db_manager.get_row_count('ships')))
            ]

            for meta in metadata:
                # Delete old value if exists
                old = session.query(ExtractorMetadata).filter_by(key=meta.key).first()
                if old:
                    session.delete(old)
                session.add(meta)

    def _report_progress(self, message: str, progress: float) -> None:
        """Report progress via callback and logging.

        Args:
            message: Progress message
            progress: Progress percentage (0.0 to 1.0)
        """
        self.logger.info(f"[{progress*100:.0f}%] {message}")
        if self.progress_callback:
            self.progress_callback(message, progress)

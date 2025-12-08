"""Database schema for X4FT using SQLAlchemy ORM."""

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Table, Text
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()

# Association tables for many-to-many relationships
ship_faction_table = Table(
    'ship_faction',
    Base.metadata,
    Column('ship_id', Integer, ForeignKey('ships.id'), primary_key=True),
    Column('faction_id', Integer, ForeignKey('factions.id'), primary_key=True)
)

equipment_faction_table = Table(
    'equipment_faction',
    Base.metadata,
    Column('equipment_id', Integer, ForeignKey('equipment.id'), primary_key=True),
    Column('faction_id', Integer, ForeignKey('factions.id'), primary_key=True)
)


class Faction(Base):
    """Game factions (Argon, Paranid, Split, etc.)."""

    __tablename__ = 'factions'

    id = Column(Integer, primary_key=True)
    faction_id = Column(String(64), unique=True, nullable=False)  # e.g., "argon"
    name = Column(String(128))

    def __repr__(self):
        return f"<Faction(id='{self.faction_id}', name='{self.name}')>"


class Ship(Base):
    """Ship base stats and classification."""

    __tablename__ = 'ships'

    id = Column(Integer, primary_key=True)
    macro_name = Column(String(128), unique=True, nullable=False)
    ware_id = Column(String(128))
    component_ref = Column(String(128))  # Reference to component file

    # Identification
    name = Column(String(256))
    basename = Column(String(256))
    description = Column(Text)
    variation = Column(String(128))
    shortvariation = Column(String(128))
    makerrace = Column(String(64))  # argon, paranid, teladi, etc.
    icon = Column(String(128))

    # Classification
    size = Column(String(8))  # xs, s, m, l, xl
    ship_type = Column(String(64))  # fighter, freighter, destroyer, gunboat, etc.
    ship_class = Column(String(64))  # ship_xs, ship_s, ship_m, ship_l, ship_xl
    purpose_primary = Column(String(64))  # fight, trade, mine, etc.

    # Base stats
    hull_max = Column(Integer, default=0)
    mass = Column(Float, default=0.0)

    # Explosion damage
    explosion_damage = Column(Float, default=0.0)
    explosion_damage_shield = Column(Float, default=0.0)

    # Storage
    cargo_capacity = Column(Integer, default=0)
    missile_storage = Column(Integer, default=0)
    drone_storage = Column(Integer, default=0)
    unit_storage = Column(Integer, default=0)

    # Crew
    crew_capacity = Column(Integer, default=0)

    # Secrecy
    secrecy_level = Column(Integer, default=0)

    # Physics - Inertia
    pitch_inertia = Column(Float, default=0.0)
    yaw_inertia = Column(Float, default=0.0)
    roll_inertia = Column(Float, default=0.0)

    # Physics - Drag
    forward_drag = Column(Float, default=0.0)
    reverse_drag = Column(Float, default=0.0)
    horizontal_drag = Column(Float, default=0.0)
    vertical_drag = Column(Float, default=0.0)
    pitch_drag = Column(Float, default=0.0)
    yaw_drag = Column(Float, default=0.0)
    roll_drag = Column(Float, default=0.0)

    # Physics - Acceleration factors
    forward_accfactor = Column(Float, default=1.0)

    # Jerk - Forward
    jerk_forward_accel = Column(Float, default=0.0)
    jerk_forward_decel = Column(Float, default=0.0)
    jerk_forward_ratio = Column(Float, default=0.0)

    # Jerk - Boost
    jerk_boost_accel = Column(Float, default=0.0)
    jerk_boost_ratio = Column(Float, default=0.0)

    # Jerk - Travel
    jerk_travel_accel = Column(Float, default=0.0)
    jerk_travel_decel = Column(Float, default=0.0)
    jerk_travel_ratio = Column(Float, default=0.0)

    # Jerk - Strafe and Angular
    jerk_strafe = Column(Float, default=0.0)
    jerk_angular = Column(Float, default=0.0)

    # Thruster tags
    thruster_tags = Column(String(128))

    # Sound
    sound_occlusion_inside = Column(Float, default=0.0)
    shipdetail_sound = Column(String(128))

    # Pricing (from wares)
    price_min = Column(Integer, default=0)
    price_avg = Column(Integer, default=0)
    price_max = Column(Integer, default=0)

    # Source tracking
    source_dlc = Column(String(64))  # Which DLC this came from

    # Relationships
    factions = relationship("Faction", secondary=ship_faction_table, backref="ships")
    slots = relationship("ShipSlot", back_populates="ship", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ship(macro='{self.macro_name}', name='{self.name}', size='{self.size}')>"


class ShipSlot(Base):
    """Equipment slots on a ship."""

    __tablename__ = 'ship_slots'

    id = Column(Integer, primary_key=True)
    ship_id = Column(Integer, ForeignKey('ships.id'), nullable=False)

    slot_name = Column(String(64), nullable=False)  # e.g., "con_weapon_01"
    slot_type = Column(String(32), nullable=False)  # weapon, turret, shield, engine, thruster
    slot_size = Column(String(8))  # xs, s, m, l, xl
    slot_index = Column(Integer, default=0)  # For ordering slots

    # Compatibility tags
    tags = Column(String(256))  # Comma-separated: "standard,highpowered"

    # Relationship
    ship = relationship("Ship", back_populates="slots")

    def __repr__(self):
        return f"<ShipSlot(name='{self.slot_name}', type='{self.slot_type}', size='{self.slot_size}')>"


class Equipment(Base):
    """Base equipment table for weapons, shields, engines, etc."""

    __tablename__ = 'equipment'

    id = Column(Integer, primary_key=True)
    macro_name = Column(String(128), unique=True, nullable=False)
    ware_id = Column(String(128))
    name = Column(String(256))
    description = Column(Text)

    equipment_type = Column(String(32), nullable=False)  # weapon, turret, shield, engine, thruster, missile
    size = Column(String(8))  # xs, s, m, l, xl
    mk_level = Column(Integer, default=1)  # Mk1, Mk2, Mk3

    # Generic stats
    hull = Column(Integer, default=0)

    # Pricing
    price_min = Column(Integer, default=0)
    price_avg = Column(Integer, default=0)
    price_max = Column(Integer, default=0)

    # Compatibility tags
    tags = Column(String(256))

    # Source tracking
    source_dlc = Column(String(64))

    # Relationships
    factions = relationship("Faction", secondary=equipment_faction_table, backref="equipment")
    weapon_stats = relationship("WeaponStats", back_populates="equipment", uselist=False, cascade="all, delete-orphan")
    shield_stats = relationship("ShieldStats", back_populates="equipment", uselist=False, cascade="all, delete-orphan")
    engine_stats = relationship("EngineStats", back_populates="equipment", uselist=False, cascade="all, delete-orphan")
    thruster_stats = relationship("ThrusterStats", back_populates="equipment", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Equipment(macro='{self.macro_name}', type='{self.equipment_type}', name='{self.name}')>"


class WeaponStats(Base):
    """Extended stats for weapons/turrets."""

    __tablename__ = 'weapon_stats'

    id = Column(Integer, primary_key=True)
    equipment_id = Column(Integer, ForeignKey('equipment.id'), unique=True, nullable=False)

    # Damage
    damage_hull = Column(Float, default=0.0)
    damage_shield = Column(Float, default=0.0)

    # Fire rate
    fire_rate = Column(Float, default=0.0)  # rounds per second
    reload_time = Column(Float, default=0.0)

    # Projectile
    projectile_speed = Column(Float, default=0.0)
    projectile_lifetime = Column(Float, default=0.0)
    range_max = Column(Float, default=0.0)  # calculated: speed * lifetime

    # Heat
    heat_per_shot = Column(Float, default=0.0)
    heat_dissipation = Column(Float, default=0.0)
    overheat_time = Column(Float, default=0.0)

    # Rotation (for turrets)
    rotation_speed = Column(Float, default=0.0)

    # DPS calculated
    dps_hull = Column(Float, default=0.0)
    dps_shield = Column(Float, default=0.0)

    # Relationship
    equipment = relationship("Equipment", back_populates="weapon_stats")

    def __repr__(self):
        return f"<WeaponStats(damage_hull={self.damage_hull}, dps_hull={self.dps_hull})>"


class ShieldStats(Base):
    """Extended stats for shields."""

    __tablename__ = 'shield_stats'

    id = Column(Integer, primary_key=True)
    equipment_id = Column(Integer, ForeignKey('equipment.id'), unique=True, nullable=False)

    capacity = Column(Integer, default=0)
    recharge_rate = Column(Float, default=0.0)  # per second
    recharge_delay = Column(Float, default=0.0)  # seconds after damage

    # Relationship
    equipment = relationship("Equipment", back_populates="shield_stats")

    def __repr__(self):
        return f"<ShieldStats(capacity={self.capacity}, recharge={self.recharge_rate})>"


class EngineStats(Base):
    """Extended stats for engines."""

    __tablename__ = 'engine_stats'

    id = Column(Integer, primary_key=True)
    equipment_id = Column(Integer, ForeignKey('equipment.id'), unique=True, nullable=False)

    # Thrust values
    forward_thrust = Column(Float, default=0.0)
    reverse_thrust = Column(Float, default=0.0)

    # Boost
    boost_thrust = Column(Float, default=0.0)
    boost_duration = Column(Float, default=0.0)
    boost_recharge = Column(Float, default=0.0)

    # Travel mode
    travel_thrust = Column(Float, default=0.0)
    travel_charge_time = Column(Float, default=0.0)
    travel_attack_time = Column(Float, default=0.0)
    travel_release_time = Column(Float, default=0.0)

    # Relationship
    equipment = relationship("Equipment", back_populates="engine_stats")

    def __repr__(self):
        return f"<EngineStats(forward={self.forward_thrust}, boost={self.boost_thrust})>"


class ThrusterStats(Base):
    """Extended stats for thrusters (maneuvering)."""

    __tablename__ = 'thruster_stats'

    id = Column(Integer, primary_key=True)
    equipment_id = Column(Integer, ForeignKey('equipment.id'), unique=True, nullable=False)

    thrust_strafe = Column(Float, default=0.0)
    thrust_pitch = Column(Float, default=0.0)
    thrust_yaw = Column(Float, default=0.0)
    thrust_roll = Column(Float, default=0.0)

    # Relationship
    equipment = relationship("Equipment", back_populates="thruster_stats")

    def __repr__(self):
        return f"<ThrusterStats(strafe={self.thrust_strafe}, pitch={self.thrust_pitch})>"


class Consumable(Base):
    """Consumable items (missiles, mines, satellites, drones, laser towers, etc.)."""

    __tablename__ = 'consumables'

    id = Column(Integer, primary_key=True)
    macro_name = Column(String(128), unique=True)
    ware_id = Column(String(128), unique=True, nullable=False)

    # Identification
    name = Column(String(256))
    description = Column(Text)

    # Classification
    consumable_type = Column(String(64))  # missile, mine, satellite, drone, laser_tower, countermeasure
    size = Column(String(8))  # xs, s, m, l, xl (if applicable)
    mk_level = Column(Integer, default=1)

    # Pricing
    price_min = Column(Integer, default=0)
    price_avg = Column(Integer, default=0)
    price_max = Column(Integer, default=0)

    # Additional metadata
    tags = Column(String(256))  # Comma-separated tags from wares

    def __repr__(self):
        return f"<Consumable(name='{self.name}', type='{self.consumable_type}')>"


class ExtractorMetadata(Base):
    """Track extraction metadata for re-run detection."""

    __tablename__ = 'extractor_metadata'

    id = Column(Integer, primary_key=True)
    key = Column(String(64), unique=True, nullable=False)
    value = Column(String(512))

    # Common keys: 'last_extraction_time', 'game_version', 'dlc_list', 'schema_version'

    def __repr__(self):
        return f"<ExtractorMetadata(key='{self.key}', value='{self.value}')>"


class AppSettings(Base):
    """Application settings (configurable from GUI).

    Settings stored here override config.json values and can be modified at runtime.
    Categories: logging, ui, performance, paths, etc.
    """

    __tablename__ = 'app_settings'

    id = Column(Integer, primary_key=True)
    category = Column(String(32), nullable=False)  # logging, ui, performance, paths
    key = Column(String(64), nullable=False)
    value = Column(String(512))
    value_type = Column(String(16), default='string')  # string, int, float, bool, json
    description = Column(String(256))  # For GUI tooltips
    is_user_modified = Column(Boolean, default=False)  # Track if user changed from default

    def __repr__(self):
        return f"<AppSettings(category='{self.category}', key='{self.key}', value='{self.value}')>"

    @property
    def typed_value(self):
        """Get value converted to appropriate type."""
        if self.value is None:
            return None

        if self.value_type == 'int':
            return int(self.value)
        elif self.value_type == 'float':
            return float(self.value)
        elif self.value_type == 'bool':
            return self.value.lower() in ('true', '1', 'yes')
        elif self.value_type == 'json':
            import json
            return json.loads(self.value)
        else:
            return self.value

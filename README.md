# X4FT - X4 Foundations Fitting Tool

Herramienta de escritorio similar a PyFA para EVE Online, pero para X4 Foundations. Permite visualizar naves, equipamiento y crear builds optimizados para ver cómo el equipamiento y las modificaciones afectan las estadísticas finales de las naves.

## 🎯 Características Principales

- **Extracción Automática de Datos**: Extrae y procesa información directamente de los archivos del juego
- **Base de Datos Completa**: Almacena naves, equipamiento, modificaciones, consumibles y tripulación
- **Soporte Multi-DLC**: Detecta y procesa automáticamente todos los DLCs instalados
- **Sistema de Modificaciones**: Incluye todas las modificaciones de investigación (Research Mods)
- **Logging Robusto**: Sistema de logs configurable con rotación automática

## 📊 Estado del Proyecto

### ✅ Completado - Sistema de Extracción de Datos

- **Arquitectura Base**
  - ✅ Estructura modular del proyecto
  - ✅ Sistema de configuración JSON con validación
  - ✅ Logging centralizado con rotación de archivos
  - ✅ Gestión de base de datos con SQLAlchemy ORM

- **Extracción de Datos**
  - ✅ Wrapper para XRCatTool (herramienta oficial de Egosoft)
  - ✅ Extracción automática de archivos .cat del juego base
  - ✅ Procesamiento de DLCs con sistema de prioridades
  - ✅ Aplicación automática de XML diffs (parches de DLCs)
  - ✅ Sistema de re-detección inteligente (solo extrae si hay cambios)

- **Parsers Implementados**
  - ✅ **Naves** (263 naves pilotables): Hull, mass, cargo, physics, jerk, thrust
  - ✅ **Armas y Torretas** (269 items): Damage, DPS, fire rate, projectile stats
  - ✅ **Escudos** (101 items): Capacity, recharge rate, delay
  - ✅ **Motores** (150 items): Forward/boost/travel thrust, timings
  - ✅ **Thrusters** (18 items): Strafe, pitch, yaw, roll
  - ✅ **Consumibles** (48 items): Missiles, mines, satellites, drones, laser towers
  - ✅ **Tipos de Tripulación** (6 niveles): Precios escalados por habilidad (0-5 estrellas)
  - ✅ **Modificaciones de Equipamiento** (33 mods): Engine, weapon, shield, chassis mods

- **Base de Datos SQLite**
  - ✅ 14 tablas relacionales con SQLAlchemy ORM
  - ✅ 5,669 slots de equipamiento catalogados
  - ✅ Precios de wares (min/avg/max) desde wares.xml
  - ✅ Relaciones faction-equipment para filtrado
  - ✅ Metadata de extracción para versionado

### 🔄 En Desarrollo - Sistema de Fitting

- ⏳ Lógica de cálculo de estadísticas con modificaciones
- ⏳ Sistema de builds persistentes
- ⏳ Validación de compatibilidad de equipamiento

### 📅 Planificado - Interfaz Gráfica

- ⏳ GUI con PyQt6
- ⏳ Visualizador de naves y estadísticas
- ⏳ Editor de builds con drag & drop
- ⏳ Comparador de configuraciones
- ⏳ Exportación/importación de builds

## 📁 Estructura del Proyecto

```
X4FT/
├── src/x4ft/
│   ├── config/                    # Sistema de configuración
│   │   └── settings.py            # Configuración JSON con validación
│   ├── extraction/                # Sistema de extracción de datos
│   │   ├── catalog_extractor.py  # Wrapper de XRCatTool
│   │   ├── xml_diff_applicator.py # Aplicador de diffs de DLCs
│   │   ├── extraction_manager.py # Orquestador principal
│   │   └── equipmentmods_parser.py # Parser de modificaciones
│   ├── parsers/                   # Parsers de XML del juego
│   │   ├── ship_parser.py        # Naves y componentes
│   │   ├── weapon_parser.py      # Armas y torretas
│   │   ├── bullet_parser.py      # Proyectiles
│   │   ├── shield_parser.py      # Escudos
│   │   ├── engine_parser.py      # Motores
│   │   ├── thruster_parser.py    # Thrusters de maniobra
│   │   ├── wares_parser.py       # Precios y wares
│   │   ├── text_resolver.py      # Textos de idioma
│   │   └── macro_index_parser.py # Índice de macros
│   ├── database/                  # Base de datos SQLite
│   │   ├── schema.py              # Modelos SQLAlchemy
│   │   └── connection.py          # Gestor de conexiones
│   ├── utils/                     # Utilidades
│   │   └── logger.py              # Sistema de logging
│   ├── models/                    # Dataclasses (futuro)
│   ├── core/                      # Lógica de fitting (futuro)
│   └── gui/                       # Interfaz PyQt6 (futuro)
├── scripts/
│   ├── extract_game_data.py       # CLI para extracción
│   └── create_config.py           # Generador de config.json
├── data/
│   ├── extracted/                 # XMLs extraídos del juego
│   │   ├── libraries/            # Bibliotecas del juego
│   │   ├── assets/               # Assets (macros, componentes)
│   │   └── t/                    # Archivos de idioma
│   └── x4ft.db                    # Base de datos SQLite
├── logs/                          # Logs de la aplicación
│   ├── x4ft.log                   # Log principal (rotativo)
│   ├── extraction.log             # Log de extracción (rotativo)
│   └── errors.log                 # Solo errores
├── tools/
│   └── XTools_1.11/               # Herramientas oficiales de Egosoft
│       └── XRCatTool.exe          # Extractor de archivos .cat
├── config.json                    # Configuración del usuario
├── config.example.json            # Plantilla de configuración
└── README.md
```

## 🗄️ Schema de Base de Datos

### Tablas Principales

| Tabla | Registros | Descripción |
|-------|-----------|-------------|
| **ships** | 263 | Naves pilotables (excluye spacesuits/modules) |
| **ship_slots** | 5,669 | Slots de equipamiento por nave |
| **equipment** | 538 | Armas, escudos, motores, thrusters |
| **weapon_stats** | 269 | Estadísticas de armas (damage, DPS, fire rate) |
| **shield_stats** | 101 | Estadísticas de escudos (capacity, recharge) |
| **engine_stats** | 150 | Estadísticas de motores (thrust, boost, travel) |
| **thruster_stats** | 18 | Estadísticas de thrusters (strafe, rotation) |
| **consumables** | 48 | Missiles, mines, drones, satellites |
| **crew_types** | 6 | Niveles de tripulación (0-5 estrellas) |
| **equipment_mods** | 33 | Modificaciones de investigación |
| **equipment_mod_bonuses** | — | Bonuses de las modificaciones |
| **factions** | — | Facciones del juego |
| **app_settings** | — | Configuración de la aplicación |
| **extractor_metadata** | — | Metadata de extracción |

### Modificaciones de Equipamiento (Research Mods)

**33 modificaciones totales** (30 vanilla + 3 DLC):

| Categoría | Cantidad | Tipos |
|-----------|----------|-------|
| **Engine** | 11 | Forward thrust, Travel thrust, Boost |
| **Weapon** | 7 | Damage, Reload speed |
| **Shield** | 6 | Capacity, Recharge rate |
| **Chassis** | 9 | Hull, Cargo capacity, Drag reduction |

**Niveles de Calidad:**
- **Basic** (Verde): +5-10% bonus
- **Advanced** (Azul): +10-20% bonus
- **Exceptional** (Morado): +20-50% bonus

## 🚀 Instalación

### Requisitos

- **Python 3.9+**
- **X4 Foundations** instalado (Steam/GOG/Epic)
- **DLCs opcionales** (auto-detectados si están instalados)

### 1. Clonar el Repositorio

```bash
git clone https://github.com/benabhi/X4FT.git
cd X4FT
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

O instalación en modo desarrollo:

```bash
pip install -e .
```

**Dependencias principales:**
- `lxml` - Parseo de XML
- `SQLAlchemy` - ORM para base de datos
- `PyQt6` - GUI (futuro)

### 3. Crear Configuración

**Opción A: Script automático (recomendado)**

```bash
python scripts/create_config.py
```

El script detecta automáticamente:
- Path de instalación de X4 (Steam/GOG/Epic)
- DLCs instalados
- Paths de herramientas

**Opción B: Manual**

```bash
cp config.example.json config.json
# Editar config.json con tu configuración
```

**Ejemplo de config.json:**

```json
{
  "game_path": "D:\\Games\\steamapps\\common\\X4 Foundations",
  "xrcattool_path": "C:\\X4FT\\tools\\XTools_1.11\\XRCatTool.exe",
  "extraction_path": "C:\\X4FT\\data\\extracted",
  "database_path": "C:\\X4FT\\data\\x4ft.db",
  "extensions": [
    {
      "id": "ego_dlc_split",
      "name": "Split Vendetta",
      "path": "D:\\Games\\steamapps\\common\\X4 Foundations\\extensions\\ego_dlc_split",
      "enabled": true,
      "priority": 1
    }
  ],
  "logging": {
    "level": "INFO",
    "console_level": "INFO",
    "file_level": "DEBUG",
    "max_file_size_mb": 10,
    "backup_count": 5
  }
}
```

## 💻 Uso

### Extracción de Datos del Juego

```bash
python scripts/extract_game_data.py
```

**El proceso de extracción:**

1. ✅ Valida configuración y paths
2. 🔍 Verifica cambios desde última extracción
3. 📦 Extrae archivos .cat del juego base
4. 🎮 Procesa DLCs en orden de prioridad
5. 🔀 Aplica XML diffs (parches de DLCs)
6. 📝 Parsea XMLs de naves, equipamiento, etc.
7. 💾 Crea/actualiza base de datos SQLite
8. 📊 Guarda metadata de extracción

**Tiempo estimado**: 30-90 segundos (depende del hardware)

**Progreso visual:**

```
[10%] Extracting base game files...
[25%] Extracting DLC: Split Vendetta...
[40%] Applying XML diffs...
[50%] Parsing ships...
[60%] Parsing weapons...
[80%] Populating database...
[100%] Extraction complete!

✅ Extraction completed successfully!
  Database: C:\X4FT\data\x4ft.db
  Extracted: 263 ships, 538 equipment, 48 consumables, 33 mods
```

### Uso desde Python

**Extracción programática:**

```python
from x4ft.extraction import ExtractionManager
from x4ft.config import X4FTConfig

# Cargar configuración
config = X4FTConfig.load("config.json")

# Crear manager con callback de progreso
def on_progress(message: str, percentage: float):
    print(f"[{percentage*100:.0f}%] {message}")

manager = ExtractionManager(config, progress_callback=on_progress)

# Ejecutar extracción completa
success = manager.run_full_extraction()
```

**Consultas a la Base de Datos:**

```python
from x4ft.database.connection import DatabaseManager
from x4ft.database.schema import Ship, Equipment, EquipmentMod
from pathlib import Path

db = DatabaseManager(Path("data/x4ft.db"))

# Ejemplo 1: Listar naves medianas (M)
with db.get_session() as session:
    ships = session.query(Ship).filter(Ship.size == "m").all()
    for ship in ships:
        print(f"{ship.name} - Hull: {ship.hull_max:,} - Cargo: {ship.cargo_capacity:,}")

# Ejemplo 2: Armas más poderosas
with db.get_session() as session:
    weapons = session.query(Equipment).join(WeaponStats)\
        .order_by(WeaponStats.dps_hull.desc())\
        .limit(10).all()

    for weapon in weapons:
        stats = weapon.weapon_stats
        print(f"{weapon.name} - DPS: {stats.dps_hull:.0f}")

# Ejemplo 3: Modificaciones de motor
with db.get_session() as session:
    engine_mods = session.query(EquipmentMod)\
        .filter(EquipmentMod.mod_category == "engine")\
        .all()

    for mod in engine_mods:
        bonus = int((mod.effect_min - 1.0) * 100)
        print(f"{mod.name} - +{bonus}% {mod.effect_stat}")
```

**Logging:**

```python
from x4ft.utils.logger import get_logger, set_console_level
import logging

# Obtener logger para un módulo
logger = get_logger('my_module')

logger.debug("Mensaje de depuración")
logger.info("Información general")
logger.warning("Advertencia")
logger.error("Error")

# Cambiar nivel de consola
set_console_level(logging.DEBUG)
```

## 🔧 Sistema de Logging

**Archivos de Log:**
- `logs/x4ft.log` - Log principal (rotativo, max 10MB, 5 backups)
- `logs/extraction.log` - Log específico de extracción
- `logs/errors.log` - Solo errores y críticos (rotativo, max 5MB)

**Configuración en config.json:**

```json
{
  "logging": {
    "level": "INFO",           # Nivel global: DEBUG, INFO, WARNING, ERROR
    "console_level": "INFO",   # Nivel de consola
    "file_level": "DEBUG",     # Nivel de archivos
    "max_file_size_mb": 10,    # Tamaño máximo por archivo
    "backup_count": 5,         # Número de backups a mantener
    "cleanup_days": 30         # Días antes de borrar logs antiguos
  }
}
```

## 📚 Ejemplos de Queries SQL

**Top 10 naves por cargo:**
```sql
SELECT name, cargo_capacity, size, ship_type
FROM ships
ORDER BY cargo_capacity DESC
LIMIT 10;
```

**Armas con mayor DPS contra hull:**
```sql
SELECT e.name, e.size, ws.dps_hull, ws.damage_hull
FROM equipment e
JOIN weapon_stats ws ON e.id = ws.equipment_id
WHERE e.equipment_type = 'weapon'
ORDER BY ws.dps_hull DESC
LIMIT 10;
```

**Escudos con mejor ratio capacidad/recarga:**
```sql
SELECT e.name, e.size, ss.capacity, ss.recharge_rate,
       (ss.capacity / ss.recharge_rate) as time_to_full
FROM equipment e
JOIN shield_stats ss ON e.id = ss.equipment_id
ORDER BY time_to_full ASC
LIMIT 10;
```

**Tripulación por nivel de habilidad:**
```sql
SELECT name, skill_level, price_avg, efficiency_bonus
FROM crew_types
ORDER BY skill_level;
```

**Modificaciones excepcionales de armas:**
```sql
SELECT name, mod_type, quality, effect_min, effect_max
FROM equipment_mods
WHERE mod_category = 'weapon' AND quality = 3
ORDER BY effect_min DESC;
```

## 🛠️ Desarrollo

### Agregar un Nuevo Parser

1. Crear archivo en `src/x4ft/parsers/nuevo_parser.py`
2. Heredar de una clase base o implementar interfaz común
3. Implementar método `parse()` que retorne lista de objetos
4. Agregar al pipeline en `extraction_manager.py`
5. Crear schema en `database/schema.py` si es necesario

**Ejemplo:**

```python
from pathlib import Path
from typing import List
from ..utils.logger import get_logger

class MiParser:
    def __init__(self, extracted_path: Path):
        self.extracted_path = extracted_path
        self.logger = get_logger('mi_parser')

    def parse(self) -> List[dict]:
        self.logger.info("Iniciando parseo...")
        # Tu lógica aquí
        return resultados
```

### Ejecutar Tests

```bash
pytest tests/
```

### Verificar Code Style

```bash
flake8 src/
black src/ --check
```

## 🎯 Roadmap

### ✅ Fase 1: Extracción de Datos (COMPLETADA)
- [x] Estructura del proyecto
- [x] Sistema de configuración JSON
- [x] Wrapper para XRCatTool
- [x] Todos los parsers de XML
- [x] Base de datos SQLite completa
- [x] Sistema de logging robusto
- [x] Soporte multi-DLC
- [x] Sistema de modificaciones de investigación

### 🔄 Fase 2: Core Logic (EN DESARROLLO)
- [ ] Motor de cálculo de estadísticas
- [ ] Aplicación de modificaciones de investigación
- [ ] Sistema de builds persistentes
- [ ] Validación de compatibilidad de equipamiento
- [ ] Cálculo de costos totales (nave + equipo + crew + mods)
- [ ] Comparador de configuraciones

### 📅 Fase 3: GUI (PLANIFICADA)
- [ ] Diseño de interfaz con PyQt6
- [ ] Ventana principal con navegación
- [ ] Visualizador de naves con stats
- [ ] Editor de builds con drag & drop
- [ ] Sistema de filtros y búsqueda
- [ ] Comparador visual de builds
- [ ] Exportación/importación de builds
- [ ] Temas claro/oscuro

### 🚀 Fase 4: Funcionalidades Avanzadas
- [ ] Cálculo de DPS efectivo vs diferentes targets
- [ ] Simulación de combate básica
- [ ] Optimizador automático de builds
- [ ] Integración con APIs de comunidad
- [ ] Sistema de builds compartidos
- [ ] Actualización automática de datos del juego

## 🐛 Problemas Conocidos

- Algunos archivos de video/scenario no tienen propiedades completas (esperado)
- Ciertas naves de storage/modules se excluyen intencionalmente
- Los precios de wares pueden variar in-game según economía dinámica

## 🤝 Contribuciones

Este es un proyecto personal en desarrollo activo. Sugerencias y feedback son bienvenidos a través de GitHub Issues.

## 📝 Notas Técnicas

### DLCs Soportados
- ✅ Split Vendetta (ego_dlc_split)
- ✅ Cradle of Humanity (ego_dlc_terran)
- ✅ Tides of Avarice (ego_dlc_pirate)
- ✅ Kingdom End (ego_dlc_boron)
- ✅ Timelines (ego_dlc_timelines)
- ✅ Bonus Content (ego_dlc_mini_01)

### Sistema de XML Diffs
X4 usa archivos XML diff para aplicar cambios de DLCs sobre el juego base. X4FT aplica automáticamente estos diffs en el orden correcto según las prioridades configuradas.

### Filtrado de Datos
El sistema filtra automáticamente:
- Naves no pilotables (spacesuits, storage modules)
- Equipamiento de escenarios/story (ware IDs específicos)
- Macros de video/cutscenes
- Entidades de debug/test

## 📄 Licencia

Proyecto personal - En desarrollo activo

---

**Desarrollado con** [Claude Code](https://claude.com/claude-code)

**Repositorio**: https://github.com/benabhi/X4FT

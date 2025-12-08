# X4FT - X4 Foundations Fitting Tool

Herramienta de escritorio similar a PyFA para EVE Online, pero para X4 Foundations. Permite visualizar naves, módulos y crear builds para ver cómo el equipamiento afecta las estadísticas de las naves.

## Estado del Proyecto

🚧 **En desarrollo** - Actualmente implementando la extracción de datos del juego.

### Completado
- ✅ Estructura base del proyecto
- ✅ Sistema de configuración

### En desarrollo
- 🔄 Extracción de datos de archivos .cat del juego
- 🔄 Parseo de XMLs (naves, módulos, armas, escudos)
- 🔄 Base de datos SQLite

### Pendiente
- ⏳ GUI con PyQt6
- ⏳ Sistema de builds/fitting
- ⏳ Cálculos de estadísticas
- ⏳ Exportación de builds

## Estructura del Proyecto

```
X4FT/
├── src/x4ft/
│   ├── config/          # Configuración y paths del juego
│   ├── extraction/      # 🔄 Extracción de archivos .cat
│   ├── parsers/         # 🔄 Parseo de XMLs del juego
│   ├── database/        # 🔄 Modelos SQLAlchemy y conexión
│   ├── models/          # Dataclasses para datos del juego
│   ├── core/            # ⏳ Lógica de fitting y cálculos
│   └── gui/             # ⏳ Interfaz PyQt6
├── data/
│   ├── extracted/       # XMLs extraídos del juego
│   └── x4ft.db          # Base de datos SQLite
├── scripts/
│   └── extract_game_data.py  # CLI para extracción
└── Tools/
    └── XTools_1.11/     # Herramientas oficiales de Egosoft
```

## Instalación

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

O usando el proyecto:

```bash
pip install -e .
```

### 2. Crear Configuración

Opción A: Usar el script generador (recomendado):

```bash
python scripts/create_config.py
```

Opción B: Copiar el ejemplo manualmente:

```bash
copy config.example.json config.json
# Editar config.json con tus paths
```

## Uso

### Extracción de Datos del Juego

```bash
python scripts/extract_game_data.py
```

El script:
1. Valida la configuración
2. Extrae archivos .cat del juego usando XRCatTool
3. Parsea XMLs de naves, módulos y equipamiento
4. Crea/actualiza la base de datos SQLite
5. Guarda metadata de la extracción

**Tiempo estimado**: 2-5 minutos dependiendo del hardware

### Desde Python

```python
from x4ft.extraction import ExtractionManager
from x4ft.config import X4FTConfig

config = X4FTConfig.load("config.json")
manager = ExtractionManager(config)

# Con callback de progreso
def progress(msg, pct):
    print(f"[{pct*100:.0f}%] {msg}")

manager = ExtractionManager(config, progress_callback=progress)
success = manager.run_full_extraction()
```

### Consultar la Base de Datos

```python
from x4ft.database.connection import DatabaseManager
from x4ft.database.schema import Ship
from pathlib import Path

# Conectar a la base de datos
db = DatabaseManager(Path("data/x4ft.db"))

# Consultar naves
with db.get_session() as session:
    ships = session.query(Ship).filter(Ship.size == "m").all()
    for ship in ships:
        print(f"{ship.name} - Hull: {ship.hull_max}")
```

## Dependencias

- Python 3.9+
- lxml - Parseo de XML
- SQLAlchemy - ORM para base de datos
- PyQt6 - GUI (próximamente)

## Roadmap

### Fase 1: Extracción de Datos (Actual)
- [x] Estructura del proyecto
- [ ] Wrapper para XRCatTool
- [ ] Parsers de XMLs
- [ ] Base de datos SQLite
- [ ] Sistema de actualización

### Fase 2: Core Logic
- [ ] Modelos de builds
- [ ] Cálculo de estadísticas
- [ ] Sistema de slots/compatibilidad

### Fase 3: GUI
- [ ] Ventana principal
- [ ] Lista de naves
- [ ] Editor de builds
- [ ] Visualización de stats
- [ ] Importar/Exportar builds

## Licencia

Proyecto personal - En desarrollo

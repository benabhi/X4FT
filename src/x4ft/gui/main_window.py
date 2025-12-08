"""Main application window for X4FT.

Provides the main interface with menu bar, data overview, and ship/equipment browsers.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QMenuBar, QMenu, QMessageBox, QStatusBar, QPushButton, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from pathlib import Path

from x4ft.config import X4FTConfig
from x4ft.database.connection import DatabaseManager
from x4ft.utils.logger import get_logger
from x4ft.gui.extraction_dialog import ExtractionDialog

logger = get_logger('gui.main_window')


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.logger = logger
        self.config: X4FTConfig = None
        self.db_manager: DatabaseManager = None

        self._init_ui()
        self._check_initial_data()

    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("X4FT - X4 Foundations Fitting Tool")
        self.setMinimumSize(1200, 800)

        # Create menu bar
        self._create_menu_bar()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)

        # Welcome/Status section
        self._create_welcome_section(layout)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()

        # === DATOS Menu ===
        datos_menu = menubar.addMenu("&Datos")

        # Extract Game Data action
        extract_action = QAction("&Extraer Datos del Juego...", self)
        extract_action.setShortcut("Ctrl+E")
        extract_action.setStatusTip("Extraer datos de los archivos del juego")
        extract_action.triggered.connect(self._show_extraction_dialog)
        datos_menu.addAction(extract_action)

        datos_menu.addSeparator()

        # Reload Database action
        reload_action = QAction("&Recargar Base de Datos", self)
        reload_action.setShortcut("F5")
        reload_action.setStatusTip("Recargar datos desde la base de datos")
        reload_action.triggered.connect(self._reload_database)
        datos_menu.addAction(reload_action)

        datos_menu.addSeparator()

        # Exit action
        exit_action = QAction("&Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Salir de la aplicación")
        exit_action.triggered.connect(self.close)
        datos_menu.addAction(exit_action)

        # === HERRAMIENTAS Menu ===
        tools_menu = menubar.addMenu("&Herramientas")

        # Database Statistics
        stats_action = QAction("&Estadísticas de Base de Datos", self)
        stats_action.setStatusTip("Ver estadísticas de datos extraídos")
        stats_action.triggered.connect(self._show_database_stats)
        tools_menu.addAction(stats_action)

        tools_menu.addSeparator()

        # Settings
        settings_action = QAction("&Configuración...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.setStatusTip("Configurar la aplicación")
        settings_action.triggered.connect(self._show_settings)
        tools_menu.addAction(settings_action)

        # === AYUDA Menu ===
        help_menu = menubar.addMenu("A&yuda")

        # About
        about_action = QAction("&Acerca de X4FT", self)
        about_action.setStatusTip("Información sobre la aplicación")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        # Documentation
        docs_action = QAction("&Documentación", self)
        docs_action.setStatusTip("Abrir documentación")
        docs_action.triggered.connect(self._show_documentation)
        help_menu.addAction(docs_action)

    def _create_welcome_section(self, parent_layout: QVBoxLayout):
        """Create welcome/status section.

        Args:
            parent_layout: Parent layout to add to
        """
        # Welcome group
        welcome_group = QGroupBox("Bienvenido a X4FT")
        welcome_layout = QVBoxLayout()

        welcome_label = QLabel(
            "<h2>X4 Foundations Fitting Tool</h2>"
            "<p>Herramienta para crear y analizar builds de naves en X4 Foundations</p>"
        )
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(welcome_label)

        # Status section
        self.data_status_label = QLabel()
        self.data_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(self.data_status_label)

        # Action button
        self.action_button = QPushButton("Extraer Datos del Juego")
        self.action_button.setMinimumHeight(40)
        self.action_button.clicked.connect(self._show_extraction_dialog)
        welcome_layout.addWidget(self.action_button)

        welcome_group.setLayout(welcome_layout)
        parent_layout.addWidget(welcome_group)

        # Add stretch to center content
        parent_layout.addStretch()

    def _check_initial_data(self):
        """Check if database has data on startup."""
        try:
            # Try to load config
            config_path = Path("config.json")
            if config_path.exists():
                self.config = X4FTConfig.load(config_path)
                self.db_manager = DatabaseManager(self.config.database_path)

                # Check if database has data
                with self.db_manager.get_session() as session:
                    from x4ft.database.schema import Ship
                    ship_count = session.query(Ship).count()

                    if ship_count > 0:
                        self._update_data_status(ship_count)
                    else:
                        self._show_no_data_warning()
            else:
                self._show_no_config_warning()

        except Exception as e:
            self.logger.error(f"Error checking initial data: {e}")
            self._show_no_data_warning()

    def _update_data_status(self, ship_count: int):
        """Update data status display.

        Args:
            ship_count: Number of ships in database
        """
        self.data_status_label.setText(
            f"<p style='color: green;'>✓ Base de datos cargada: {ship_count} naves disponibles</p>"
        )
        self.action_button.setText("Re-extraer Datos")
        self.status_bar.showMessage(f"Datos cargados: {ship_count} naves")

    def _show_no_data_warning(self):
        """Show warning when no data is available."""
        self.data_status_label.setText(
            "<p style='color: orange;'>⚠ No se encontraron datos extraídos</p>"
            "<p>Para usar el fitting tool, primero debes extraer los datos del juego.</p>"
            "<p>Haz clic en el botón debajo para comenzar.</p>"
        )
        self.status_bar.showMessage("No hay datos - Extracción requerida")

    def _show_no_config_warning(self):
        """Show warning when config is missing."""
        self.data_status_label.setText(
            "<p style='color: red;'>❌ No se encontró archivo de configuración</p>"
            "<p>La extracción de datos creará la configuración automáticamente.</p>"
        )
        self.status_bar.showMessage("Configuración no encontrada")

    def _show_extraction_dialog(self):
        """Show the data extraction dialog."""
        dialog = ExtractionDialog(self)
        dialog.extraction_completed.connect(self._on_extraction_completed)
        dialog.exec()

    def _on_extraction_completed(self, success: bool):
        """Handle extraction completion.

        Args:
            success: True if extraction was successful
        """
        if success:
            self._reload_database()
            QMessageBox.information(
                self,
                "Extracción Completada",
                "Los datos del juego se han extraído correctamente.\n\n"
                "La aplicación está lista para usar."
            )
        else:
            QMessageBox.warning(
                self,
                "Extracción Fallida",
                "Hubo un error durante la extracción de datos.\n\n"
                "Revisa los logs para más información."
            )

    def _reload_database(self):
        """Reload database data."""
        self.logger.info("Reloading database...")
        self._check_initial_data()
        self.status_bar.showMessage("Base de datos recargada", 3000)

    def _show_database_stats(self):
        """Show database statistics dialog."""
        if not self.db_manager:
            QMessageBox.warning(
                self,
                "Sin Datos",
                "No hay datos cargados. Primero extrae los datos del juego."
            )
            return

        try:
            with self.db_manager.get_session() as session:
                from x4ft.database.schema import Ship, Equipment, Consumable, EquipmentMod
                from sqlalchemy import func

                ship_count = session.query(Ship).count()
                equipment_count = session.query(Equipment).count()
                consumables_count = session.query(Consumable).count()
                mods_count = session.query(EquipmentMod).count()

                stats_text = (
                    f"<h3>Estadísticas de Base de Datos</h3>"
                    f"<p><b>Naves:</b> {ship_count}</p>"
                    f"<p><b>Equipamiento:</b> {equipment_count}</p>"
                    f"<p><b>Consumibles:</b> {consumables_count}</p>"
                    f"<p><b>Modificaciones:</b> {mods_count}</p>"
                )

                QMessageBox.information(self, "Estadísticas", stats_text)

        except Exception as e:
            self.logger.error(f"Error showing stats: {e}")
            QMessageBox.critical(self, "Error", f"Error al obtener estadísticas: {e}")

    def _show_settings(self):
        """Show settings dialog."""
        QMessageBox.information(
            self,
            "Configuración",
            "Diálogo de configuración (por implementar)"
        )

    def _show_about(self):
        """Show about dialog."""
        about_text = (
            "<h2>X4FT - X4 Foundations Fitting Tool</h2>"
            "<p>Versión 0.1.0 (Alpha)</p>"
            "<p>Herramienta de fitting para X4 Foundations, similar a PyFA para EVE Online.</p>"
            "<p><br></p>"
            "<p><b>Desarrollado con:</b> Python, PyQt6, SQLAlchemy</p>"
            "<p><b>Repositorio:</b> <a href='https://github.com/benabhi/X4FT'>github.com/benabhi/X4FT</a></p>"
            "<p><br></p>"
            "<p><i>Desarrollado con Claude Code</i></p>"
        )

        QMessageBox.about(self, "Acerca de X4FT", about_text)

    def _show_documentation(self):
        """Show documentation."""
        QMessageBox.information(
            self,
            "Documentación",
            "Consulta el README.md en el repositorio de GitHub:\n\n"
            "https://github.com/benabhi/X4FT"
        )

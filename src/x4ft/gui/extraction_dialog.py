"""Extraction dialog with auto-detection, progress tracking, and live logs.

Provides an intuitive interface for extracting game data with:
- Auto-detection of X4 installation
- Manual path selection fallback
- DLC detection and configuration
- Real-time progress bars
- Live log output
- Professional appearance
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QListWidget, QListWidgetItem, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QTextCursor
from pathlib import Path
import sys

from x4ft.utils.game_detector import GameDetector
from x4ft.utils.logger import get_logger
from x4ft.config import X4FTConfig, ExtensionConfig
from x4ft.extraction import ExtractionManager

logger = get_logger('gui.extraction_dialog')


class ExtractionWorker(QThread):
    """Worker thread for running extraction in background."""

    progress_updated = pyqtSignal(str, float)  # message, percentage
    log_message = pyqtSignal(str)  # log message
    extraction_finished = pyqtSignal(bool)  # success

    def __init__(self, config: X4FTConfig):
        super().__init__()
        self.config = config
        self.logger = get_logger('extraction_worker')

    def run(self):
        """Run extraction in background thread."""
        try:
            self.log_message.emit("=== Iniciando extracción de datos ===\n")

            # Create extraction manager with callback
            manager = ExtractionManager(
                self.config,
                progress_callback=self._progress_callback
            )

            # Run extraction
            success = manager.run_full_extraction()

            if success:
                self.log_message.emit("\n=== ✓ Extracción completada exitosamente ===\n")
            else:
                self.log_message.emit("\n=== ✗ Extracción fallida ===\n")

            self.extraction_finished.emit(success)

        except Exception as e:
            self.logger.error(f"Extraction error: {e}", exc_info=True)
            self.log_message.emit(f"\n=== ✗ ERROR: {e} ===\n")
            self.extraction_finished.emit(False)

    def _progress_callback(self, message: str, percentage: float):
        """Handle progress updates from extraction manager.

        Args:
            message: Progress message
            percentage: Progress percentage (0.0 to 1.0)
        """
        self.progress_updated.emit(message, percentage)
        self.log_message.emit(f"[{percentage*100:.0f}%] {message}\n")


class ExtractionDialog(QDialog):
    """Dialog for game data extraction with auto-detection."""

    extraction_completed = pyqtSignal(bool)  # success

    def __init__(self, parent=None):
        super().__init__(parent)

        self.logger = logger
        self.detector = GameDetector()
        self.game_path: Path = None
        self.dlcs: list = []
        self.worker: ExtractionWorker = None

        self._init_ui()
        self._auto_detect()

    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Extracción de Datos del Juego")
        self.setMinimumSize(800, 700)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # === Game Path Section ===
        path_group = self._create_path_section()
        layout.addWidget(path_group)

        # === DLCs Section ===
        dlc_group = self._create_dlc_section()
        layout.addWidget(dlc_group)

        # === Progress Section ===
        progress_group = self._create_progress_section()
        layout.addWidget(progress_group)

        # === Log Section ===
        log_group = self._create_log_section()
        layout.addWidget(log_group)

        # === Buttons ===
        button_layout = self._create_buttons()
        layout.addLayout(button_layout)

    def _create_path_section(self) -> QGroupBox:
        """Create game path selection section.

        Returns:
            QGroupBox with path controls
        """
        group = QGroupBox("Ruta de Instalación de X4 Foundations")
        layout = QVBoxLayout()

        # Auto-detect status
        self.path_status_label = QLabel()
        self.path_status_label.setWordWrap(True)
        layout.addWidget(self.path_status_label)

        # Path input
        path_input_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("Detectando automáticamente...")
        path_input_layout.addWidget(self.path_edit)

        browse_button = QPushButton("Examinar...")
        browse_button.clicked.connect(self._browse_game_path)
        path_input_layout.addWidget(browse_button)

        layout.addLayout(path_input_layout)

        group.setLayout(layout)
        return group

    def _create_dlc_section(self) -> QGroupBox:
        """Create DLC list section.

        Returns:
            QGroupBox with DLC list
        """
        group = QGroupBox("DLCs Detectados")
        layout = QVBoxLayout()

        self.dlc_status_label = QLabel("Detectando DLCs instalados...")
        layout.addWidget(self.dlc_status_label)

        self.dlc_list = QListWidget()
        self.dlc_list.setMaximumHeight(150)
        layout.addWidget(self.dlc_list)

        group.setLayout(layout)
        return group

    def _create_progress_section(self) -> QGroupBox:
        """Create progress tracking section.

        Returns:
            QGroupBox with progress bars
        """
        group = QGroupBox("Progreso de Extracción")
        layout = QVBoxLayout()

        # Overall progress
        self.overall_progress_label = QLabel("Esperando inicio...")
        layout.addWidget(self.overall_progress_label)

        self.overall_progress = QProgressBar()
        self.overall_progress.setMinimum(0)
        self.overall_progress.setMaximum(100)
        self.overall_progress.setValue(0)
        layout.addWidget(self.overall_progress)

        # Current task
        self.task_label = QLabel("")
        self.task_label.setWordWrap(True)
        layout.addWidget(self.task_label)

        group.setLayout(layout)
        return group

    def _create_log_section(self) -> QGroupBox:
        """Create live log display section.

        Returns:
            QGroupBox with log text area
        """
        group = QGroupBox("Log de Extracción")
        layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMinimumHeight(200)
        layout.addWidget(self.log_text)

        group.setLayout(layout)
        return group

    def _create_buttons(self) -> QHBoxLayout:
        """Create action buttons.

        Returns:
            QHBoxLayout with buttons
        """
        layout = QHBoxLayout()
        layout.addStretch()

        self.start_button = QPushButton("Iniciar Extracción")
        self.start_button.setMinimumWidth(150)
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self._start_extraction)
        layout.addWidget(self.start_button)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setMinimumWidth(150)
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

        return layout

    def _auto_detect(self):
        """Run auto-detection of game installation."""
        self._log("Iniciando detección automática del juego...")
        self.path_status_label.setText("🔍 Detectando instalación de X4 Foundations...")

        # Run detection in a timer to not block UI
        QTimer.singleShot(100, self._run_detection)

    def _run_detection(self):
        """Actually run the detection."""
        result = self.detector.auto_detect()

        if result:
            game_path, dlcs = result
            self.game_path = game_path
            self.dlcs = dlcs

            self.path_edit.setText(str(game_path))
            self.path_status_label.setText(
                f"✓ Instalación detectada automáticamente"
            )

            self._update_dlc_list()
            self.start_button.setEnabled(True)
            self._log(f"✓ Juego encontrado en: {game_path}")
            self._log(f"✓ {len(dlcs)} DLCs detectados")

        else:
            self.path_status_label.setText(
                "⚠ No se pudo detectar automáticamente la instalación.\n"
                "Por favor, selecciona manualmente la carpeta del juego."
            )
            self._log("⚠ No se encontró instalación automáticamente")
            self._log("Por favor, selecciona la carpeta manualmente usando 'Examinar...'")

    def _browse_game_path(self):
        """Open file dialog to browse for game path."""
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setWindowTitle("Seleccionar carpeta de X4 Foundations")

        if dialog.exec():
            selected_path = Path(dialog.selectedFiles()[0])
            is_valid, error_msg = self.detector.validate_game_path(selected_path)

            if is_valid:
                self.game_path = selected_path
                self.path_edit.setText(str(selected_path))
                self.path_status_label.setText("✓ Ruta válida seleccionada")

                # Detect DLCs
                self.dlcs = self.detector.detect_dlcs(selected_path)
                self._update_dlc_list()

                self.start_button.setEnabled(True)
                self._log(f"✓ Ruta seleccionada manualmente: {selected_path}")
                self._log(f"✓ {len(self.dlcs)} DLCs detectados")

            else:
                QMessageBox.critical(
                    self,
                    "Ruta Inválida",
                    f"La ruta seleccionada no es válida:\n\n{error_msg}\n\n"
                    "Asegúrate de seleccionar la carpeta raíz de X4 Foundations\n"
                    "(debe contener X4.exe y archivos .cat)"
                )
                self._log(f"✗ Ruta inválida: {error_msg}")

    def _update_dlc_list(self):
        """Update DLC list display."""
        self.dlc_list.clear()

        if not self.dlcs:
            self.dlc_status_label.setText("No se encontraron DLCs instalados")
            return

        self.dlc_status_label.setText(
            f"{len(self.dlcs)} DLC(s) detectado(s) - se procesarán en orden de prioridad:"
        )

        for dlc in self.dlcs:
            item_text = f"✓ {dlc['name']} (Prioridad: {dlc['priority']})"
            item = QListWidgetItem(item_text)
            self.dlc_list.addItem(item)

    def _start_extraction(self):
        """Start the extraction process."""
        if not self.game_path:
            QMessageBox.warning(
                self,
                "Sin Ruta",
                "Por favor selecciona una ruta de instalación válida"
            )
            return

        # Check for XRCatTool
        xrcattool_path = self.detector.get_xrcattool_path()
        if not xrcattool_path:
            QMessageBox.critical(
                self,
                "XRCatTool No Encontrado",
                "No se encontró XRCatTool.exe en la carpeta tools/XTools_1.11/\n\n"
                "Esta herramienta es necesaria para extraer los archivos del juego.\n"
                "Por favor, descarga XTools de la web oficial de Egosoft."
            )
            return

        # Create config
        try:
            config = self._create_config(xrcattool_path)

            # Save config
            config.save(Path("config.json"))
            self._log("✓ Configuración guardada en config.json")

            # Disable controls
            self.start_button.setEnabled(False)
            self.cancel_button.setText("Cerrar")

            # Create and start worker
            self.worker = ExtractionWorker(config)
            self.worker.progress_updated.connect(self._on_progress)
            self.worker.log_message.connect(self._log)
            self.worker.extraction_finished.connect(self._on_extraction_finished)
            self.worker.start()

            self._log("\n=== Extracción iniciada ===\n")

        except Exception as e:
            self.logger.error(f"Error starting extraction: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Error al iniciar la extracción:\n\n{e}"
            )

    def _create_config(self, xrcattool_path: Path) -> X4FTConfig:
        """Create configuration for extraction.

        Args:
            xrcattool_path: Path to XRCatTool.exe

        Returns:
            X4FTConfig object
        """
        # Convert DLCs to ExtensionConfig objects
        extensions = [
            ExtensionConfig(
                id=dlc['id'],
                name=dlc['name'],
                path=Path(dlc['path']),
                enabled=dlc['enabled'],
                priority=dlc['priority']
            )
            for dlc in self.dlcs
        ]

        # Create config
        config = X4FTConfig(
            game_path=self.game_path,
            xrcattool_path=xrcattool_path,
            extraction_path=Path.cwd() / "data" / "extracted",
            database_path=Path.cwd() / "data" / "x4ft.db",
            extensions=extensions,
            cleanup_after_extraction=False
        )

        return config

    def _on_progress(self, message: str, percentage: float):
        """Handle progress updates.

        Args:
            message: Progress message
            percentage: Progress (0.0 to 1.0)
        """
        self.overall_progress.setValue(int(percentage * 100))
        self.task_label.setText(message)
        self.overall_progress_label.setText(f"Progreso: {percentage*100:.0f}%")

    def _log(self, message: str):
        """Add message to log display.

        Args:
            message: Message to log
        """
        self.log_text.append(message)
        # Auto-scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def _on_extraction_finished(self, success: bool):
        """Handle extraction completion.

        Args:
            success: True if extraction succeeded
        """
        self.overall_progress.setValue(100 if success else 0)

        if success:
            self.overall_progress_label.setText("✓ Extracción completada")
            self.task_label.setText("Todos los datos se han extraído correctamente")
        else:
            self.overall_progress_label.setText("✗ Extracción fallida")
            self.task_label.setText("Hubo errores durante la extracción")

        self.cancel_button.setText("Cerrar")
        self.extraction_completed.emit(success)

    def reject(self):
        """Handle dialog rejection."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Cancelar Extracción",
                "¿Estás seguro de que quieres cancelar la extracción?\n\n"
                "Esto detendrá el proceso actual.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.worker.terminate()
                self.worker.wait()
                super().reject()
        else:
            super().reject()

"""Crew panel widget."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QGroupBox, QHBoxLayout
from PyQt6.QtCore import pyqtSignal
from sqlalchemy.orm import Session

from x4ft.database.schema import CrewType


class CrewPanel(QWidget):
    """Panel for selecting crew skill level."""

    crew_level_changed = pyqtSignal(int)  # level (0-5)

    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.session = session
        self.crew_types = []
        self._init_ui()
        self._load_crew_types()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)

        group = QGroupBox("Tripulación")
        group_layout = QVBoxLayout()

        # Level selector
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Nivel de Habilidad:"))

        self.level_combo = QComboBox()
        self.level_combo.currentIndexChanged.connect(self._on_level_changed)
        level_layout.addWidget(self.level_combo)
        group_layout.addLayout(level_layout)

        # Info label
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        group_layout.addWidget(self.info_label)

        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()

    def _load_crew_types(self):
        """Load crew types from database."""
        try:
            self.crew_types = self.session.query(CrewType).order_by(CrewType.skill_level).all()

            for crew in self.crew_types:
                label = f"{crew.skill_level}  - {crew.name}"
                self.level_combo.addItem(label, crew.skill_level)

            # Select first item
            if self.crew_types:
                self._update_info(0)

        except Exception as e:
            self.level_combo.addItem("0  - Sin tripulación", 0)

    def _on_level_changed(self, index: int):
        """Handle level selection change."""
        if index >= 0:
            level = self.level_combo.itemData(index)
            self._update_info(level)
            self.crew_level_changed.emit(level)

    def _update_info(self, level: int):
        """Update info label with crew details."""
        crew = next((c for c in self.crew_types if c.skill_level == level), None)
        if crew:
            bonus = crew.efficiency_bonus or 0
            info = f"<b>Bonus de Eficiencia:</b> +{bonus:.0f}%<br>"
            if crew.description:
                info += f"<i>{crew.description}</i>"
            self.info_label.setText(info)
        else:
            self.info_label.setText("Sin bonificaciones")

    def set_level(self, level: int):
        """Set crew level programmatically."""
        for i in range(self.level_combo.count()):
            if self.level_combo.itemData(i) == level:
                self.level_combo.setCurrentIndex(i)
                break

    def get_level(self) -> int:
        """Get current crew level."""
        return self.level_combo.currentData() or 0

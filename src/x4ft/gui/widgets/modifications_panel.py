"""Panel for selecting equipment modifications."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout,
    QComboBox, QLabel, QScrollArea
)
from PyQt6.QtCore import pyqtSignal
from sqlalchemy.orm import Session
from typing import Dict, Optional

from x4ft.database.schema import EquipmentMod, EquipmentModBonus
from x4ft.utils.logger import get_logger

logger = get_logger('modifications_panel')


class ModificationsPanel(QWidget):
    """Panel for selecting equipment modifications.

    In X4, equipment mods are applied to specific pieces of equipment
    (one mod per equipment piece). They provide stat bonuses like:
    - Engine: thrust, travel speed, boost
    - Weapon: damage, reload speed
    - Shield: capacity, recharge rate
    - Ship (Hull): max hull, cargo capacity, drag
    """

    # Signal: mod_changed(mod_category: str, mod_id: int or None)
    mod_changed = pyqtSignal(str, object)

    def __init__(self, session: Session, parent=None):
        super().__init__(parent)
        self.session = session
        self.mod_combos: Dict[str, QComboBox] = {}
        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for modifications
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.main_layout = QVBoxLayout(scroll_widget)

        # Info label
        info = QLabel(
            "Equipment Modifications enhance specific equipment pieces.\n"
            "Each piece of equipment can have ONE mod installed."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #888; font-style: italic; padding: 5px;")
        self.main_layout.addWidget(info)

        # Create groups for each mod category
        self._create_mod_groups()

        self.main_layout.addStretch()
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

    def _create_mod_groups(self):
        """Create modification selection groups."""
        # Mod categories and their descriptions
        categories = {
            'engine': {
                'title': 'Engine Modifications',
                'desc': 'Enhance thrust, travel speed, or boost performance'
            },
            'weapon': {
                'title': 'Weapon Modifications',
                'desc': 'Improve damage output or reload speed'
            },
            'shield': {
                'title': 'Shield Modifications',
                'desc': 'Increase shield capacity or recharge rate'
            },
            'ship': {
                'title': 'Hull/Chassis Modifications',
                'desc': 'Reinforce hull, expand cargo, or reduce drag'
            }
        }

        for category, info in categories.items():
            group = self._create_mod_category_group(
                category,
                info['title'],
                info['desc']
            )
            self.main_layout.addWidget(group)

    def _create_mod_category_group(
        self,
        category: str,
        title: str,
        description: str
    ) -> QGroupBox:
        """Create a group for one mod category.

        Args:
            category: Mod category (engine, weapon, shield, ship)
            title: Display title
            description: Category description

        Returns:
            QGroupBox with mod selection
        """
        group = QGroupBox(title)
        layout = QFormLayout()

        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 10px; padding-bottom: 5px;")
        layout.addRow(desc_label)

        # Combo box for mod selection
        combo = QComboBox()
        combo.addItem("(No Modification)", None)

        # Load mods for this category
        try:
            mods = self.session.query(EquipmentMod).filter(
                EquipmentMod.mod_category == category
            ).order_by(
                EquipmentMod.mod_type,
                EquipmentMod.quality
            ).all()

            for mod in mods:
                # Format label with quality and effect
                quality_names = {1: "Basic", 2: "Advanced", 3: "Exceptional"}
                quality = quality_names.get(mod.quality, f"Q{mod.quality}")

                # Get effect range
                effect_str = self._format_effect(mod)

                label = f"{quality} - {mod.name} ({effect_str})"
                combo.addItem(label, mod.id)

        except Exception as e:
            logger.error(f"Error loading mods for {category}: {e}", exc_info=True)

        # Connect signal
        combo.currentIndexChanged.connect(
            lambda idx, cat=category, c=combo: self._on_mod_changed(cat, c)
        )

        # Store combo reference
        self.mod_combos[category] = combo

        layout.addRow("Modification:", combo)
        group.setLayout(layout)
        return group

    def _format_effect(self, mod: EquipmentMod) -> str:
        """Format mod effect for display.

        Args:
            mod: Equipment mod

        Returns:
            Formatted effect string like "+10% Damage" or "+5-10% Thrust"
        """
        if mod.effect_min == mod.effect_max:
            # Fixed value
            sign = "+" if mod.effect_min > 0 else ""
            value = int(mod.effect_min * 100)
            return f"{sign}{value}% {mod.effect_stat.title()}"
        else:
            # Range
            sign = "+" if mod.effect_min > 0 else ""
            min_val = int(mod.effect_min * 100)
            max_val = int(mod.effect_max * 100)
            return f"{sign}{min_val}-{max_val}% {mod.effect_stat.title()}"

    def _on_mod_changed(self, category: str, combo: QComboBox):
        """Handle mod selection change.

        Args:
            category: Mod category
            combo: Combo box that changed
        """
        mod_id = combo.currentData()
        logger.debug(f"Mod changed for {category}: {mod_id}")
        self.mod_changed.emit(category, mod_id)

    def get_selected_mods(self) -> Dict[str, Optional[int]]:
        """Get currently selected mods.

        Returns:
            Dictionary mapping category -> mod_id (or None)
        """
        return {
            category: combo.currentData()
            for category, combo in self.mod_combos.items()
        }

    def set_mods(self, mods: Dict[str, Optional[int]]):
        """Set selected mods.

        Args:
            mods: Dictionary mapping category -> mod_id
        """
        for category, mod_id in mods.items():
            if category in self.mod_combos:
                combo = self.mod_combos[category]

                # Find index of mod_id
                for i in range(combo.count()):
                    if combo.itemData(i) == mod_id:
                        combo.setCurrentIndex(i)
                        break

    def clear_mods(self):
        """Clear all mod selections."""
        for combo in self.mod_combos.values():
            combo.setCurrentIndex(0)  # Set to "(No Modification)"

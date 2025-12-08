"""XML diff applicator for X4 Foundations DLC overlay system.

X4 uses XML diff files in DLCs to modify base game files. This module
applies those diffs to create the final merged XML files.
"""

import logging
from pathlib import Path
from typing import List, Optional
from lxml import etree
from copy import deepcopy


class XMLDiffApplicator:
    """Applies X4-style XML diffs to base XML files."""

    def __init__(self):
        """Initialize the diff applicator."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def apply_diffs(self, base_file: Path, diff_files: List[Path], output_file: Path) -> bool:
        """Apply a series of XML diff files to a base XML file.

        Args:
            base_file: Path to the base XML file
            diff_files: List of diff files in priority order (lowest to highest)
            output_file: Path where merged result will be saved

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load base XML
            if not base_file.exists():
                self.logger.error(f"Base file not found: {base_file}")
                return False

            base_tree = etree.parse(str(base_file))
            base_root = base_tree.getroot()

            # If base is already a diff, this is an error
            if base_root.tag == "diff":
                self.logger.error(f"Base file is a diff file, not a base: {base_file}")
                return False

            # Apply each diff in order
            for diff_file in diff_files:
                if not diff_file.exists():
                    self.logger.warning(f"Diff file not found, skipping: {diff_file}")
                    continue

                diff_tree = etree.parse(str(diff_file))
                diff_root = diff_tree.getroot()

                # Skip if not a diff file
                if diff_root.tag != "diff":
                    self.logger.debug(f"Not a diff file, skipping: {diff_file}")
                    continue

                self.logger.debug(f"Applying diff from: {diff_file.name}")
                self._apply_single_diff(base_root, diff_root)

            # Save merged result
            output_file.parent.mkdir(parents=True, exist_ok=True)
            base_tree.write(
                str(output_file),
                encoding="utf-8",
                xml_declaration=True,
                pretty_print=True
            )

            self.logger.info(f"Successfully merged {len(diff_files)} diffs into {output_file.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error applying diffs: {e}")
            return False

    def _apply_single_diff(self, base_root: etree._Element, diff_root: etree._Element):
        """Apply a single diff to the base XML tree.

        Args:
            base_root: Root element of the base XML
            diff_root: Root element of the diff XML
        """
        # Process each diff operation
        for operation in diff_root:
            if operation.tag == "add":
                self._apply_add(base_root, operation)
            elif operation.tag == "remove":
                self._apply_remove(base_root, operation)
            elif operation.tag == "replace":
                self._apply_replace(base_root, operation)
            else:
                self.logger.warning(f"Unknown diff operation: {operation.tag}")

    def _apply_add(self, base_root: etree._Element, add_op: etree._Element):
        """Apply an <add> operation.

        Format: <add sel="/path/to/parent">
                  <elements to add.../>
                </add>
        """
        sel = add_op.get("sel")
        if not sel:
            self.logger.warning("Add operation missing 'sel' attribute")
            return

        # Find target elements using XPath
        try:
            targets = base_root.xpath(sel)
            if not targets:
                self.logger.warning(f"Add target not found: {sel}")
                return

            # Add children to each target
            for target in targets:
                for child in add_op:
                    # Clone the element to avoid moving it
                    new_elem = deepcopy(child)
                    target.append(new_elem)

        except Exception as e:
            self.logger.warning(f"Error applying add to {sel}: {e}")

    def _apply_remove(self, base_root: etree._Element, remove_op: etree._Element):
        """Apply a <remove> operation.

        Format: <remove sel="/path/to/element"/>
        """
        sel = remove_op.get("sel")
        if not sel:
            self.logger.warning("Remove operation missing 'sel' attribute")
            return

        try:
            targets = base_root.xpath(sel)
            for target in targets:
                parent = target.getparent()
                if parent is not None:
                    parent.remove(target)

        except Exception as e:
            self.logger.warning(f"Error applying remove to {sel}: {e}")

    def _apply_replace(self, base_root: etree._Element, replace_op: etree._Element):
        """Apply a <replace> operation.

        Format: <replace sel="/path/to/element">
                  <new element.../>
                </replace>
        """
        sel = replace_op.get("sel")
        if not sel:
            self.logger.warning("Replace operation missing 'sel' attribute")
            return

        try:
            targets = base_root.xpath(sel)
            for target in targets:
                parent = target.getparent()
                if parent is not None:
                    # Get replacement element (first child of replace op)
                    if len(replace_op) > 0:
                        replacement = deepcopy(replace_op[0])
                        # Insert replacement before target
                        target_index = list(parent).index(target)
                        parent.insert(target_index, replacement)
                        # Remove original
                        parent.remove(target)

        except Exception as e:
            self.logger.warning(f"Error applying replace to {sel}: {e}")

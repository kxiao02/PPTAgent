"""
Template discovery and validation utilities for PPTAgent.

This module provides functions to discover, validate, and retrieve information
about PPTAgent templates from multiple sources.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pptagent.utils import get_logger, package_join

logger = get_logger(__name__)


@dataclass
class TemplateInfo:
    """Information about a PPTAgent template."""

    name: str
    path: Path
    description: str
    has_preview: bool
    has_metadata: bool
    slide_count: int
    source: str  # "built-in" or custom path

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "path": str(self.path),
            "description": self.description,
            "has_preview": self.has_preview,
            "has_metadata": self.has_metadata,
            "slide_count": self.slide_count,
            "source": self.source,
        }


def validate_template(template_path: Path) -> tuple[bool, list[str]]:
    """
    Validate that a template directory has the required structure.

    Args:
        template_path: Path to the template directory

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []

    # Check if directory exists
    if not template_path.exists():
        return False, ["Template directory does not exist"]

    if not template_path.is_dir():
        return False, ["Template path is not a directory"]

    # Check for required files
    source_pptx = template_path / "source.pptx"
    if not source_pptx.exists():
        issues.append("Missing required file: source.pptx")

    description_txt = template_path / "description.txt"
    if not description_txt.exists():
        issues.append("Missing recommended file: description.txt")

    # Check for optional but important files
    slide_induction = template_path / "slide_induction.json"
    if not slide_induction.exists():
        issues.append(
            "Missing slide_induction.json (will be auto-generated on first use)"
        )

    image_stats = template_path / "image_stats.json"
    if not image_stats.exists():
        issues.append(
            "Missing image_stats.json (will be auto-generated on first use)"
        )

    preview_png = template_path / "preview.png"
    if not preview_png.exists():
        issues.append(
            "Missing preview.png (run scripts/generate_template_previews.sh)"
        )

    # If source.pptx is missing, template is invalid
    is_valid = source_pptx.exists()

    return is_valid, issues


def get_template_info(template_path: Path, source: str = "unknown") -> TemplateInfo | None:
    """
    Get information about a template.

    Args:
        template_path: Path to the template directory
        source: Source of the template ("built-in", custom path, etc.)

    Returns:
        TemplateInfo object or None if template is invalid
    """
    is_valid, issues = validate_template(template_path)

    if not is_valid:
        logger.warning(f"Invalid template at {template_path}: {issues}")
        return None

    # Read description
    desc_file = template_path / "description.txt"
    description = "No description available"
    if desc_file.exists():
        try:
            description = desc_file.read_text(encoding="utf-8").strip()
        except Exception as e:
            logger.warning(f"Failed to read description for {template_path.name}: {e}")

    # Check for preview
    preview_file = template_path / "preview.png"
    has_preview = preview_file.exists()

    # Check for metadata
    slide_induction_file = template_path / "slide_induction.json"
    image_stats_file = template_path / "image_stats.json"
    has_metadata = slide_induction_file.exists() and image_stats_file.exists()

    # Get slide count from slide_induction.json if available
    slide_count = 0
    if slide_induction_file.exists():
        try:
            with open(slide_induction_file, encoding="utf-8") as f:
                slide_induction = json.load(f)
                slide_count = len(slide_induction)
        except Exception as e:
            logger.warning(f"Failed to read slide count for {template_path.name}: {e}")

    return TemplateInfo(
        name=template_path.name,
        path=template_path,
        description=description,
        has_preview=has_preview,
        has_metadata=has_metadata,
        slide_count=slide_count,
        source=source,
    )


def get_template_search_paths() -> list[Path]:
    """
    Get all directories to search for templates.

    Searches in:
    1. Built-in templates directory (pptagent/templates/)
    2. Custom directories from PPTAGENT_TEMPLATE_DIRS environment variable

    Environment variable format:
        PPTAGENT_TEMPLATE_DIRS="/path/to/dir1:/path/to/dir2"
        (colon-separated on Unix, semicolon-separated on Windows)

    Returns:
        List of Path objects to search for templates
    """
    search_paths = []

    # 1. Built-in templates
    builtin_templates = Path(package_join("templates"))
    if builtin_templates.exists():
        search_paths.append(builtin_templates)
    else:
        logger.warning(f"Built-in templates directory not found: {builtin_templates}")

    # 2. Custom template directories from environment variable
    custom_dirs = os.environ.get("PPTAGENT_TEMPLATE_DIRS", "")
    if custom_dirs:
        # Use appropriate separator based on OS
        separator = ";" if os.name == "nt" else ":"
        for custom_dir in custom_dirs.split(separator):
            custom_path = Path(custom_dir.strip())
            if custom_path.exists() and custom_path.is_dir():
                search_paths.append(custom_path)
                logger.info(f"Added custom template directory: {custom_path}")
            else:
                logger.warning(f"Custom template directory not found: {custom_path}")

    return search_paths


def discover_templates(
    include_invalid: bool = False,
    sort_by: str = "name",
) -> list[TemplateInfo]:
    """
    Discover all available templates from all search paths.

    Args:
        include_invalid: If True, include templates with validation issues
                        (they will have warnings in the log)
        sort_by: How to sort results - "name", "source", or "slide_count"

    Returns:
        List of TemplateInfo objects for discovered templates

    Example:
        >>> templates = discover_templates()
        >>> for template in templates:
        ...     print(f"{template.name}: {template.description}")

        >>> # With custom template directories
        >>> os.environ["PPTAGENT_TEMPLATE_DIRS"] = "/my/templates:/shared/templates"
        >>> templates = discover_templates()
    """
    all_templates = []
    search_paths = get_template_search_paths()

    logger.info(f"Searching for templates in {len(search_paths)} directories")

    for search_path in search_paths:
        source = "built-in" if "templates" in str(search_path) and package_join("templates") in str(search_path) else str(search_path)

        # Iterate through subdirectories
        for template_dir in sorted(search_path.iterdir()):
            if not template_dir.is_dir():
                continue

            # Skip hidden directories
            if template_dir.name.startswith("."):
                continue

            template_info = get_template_info(template_dir, source=source)

            if template_info is not None:
                all_templates.append(template_info)
                logger.debug(f"Discovered template: {template_info.name} from {source}")
            elif include_invalid:
                # Create minimal info for invalid templates
                all_templates.append(
                    TemplateInfo(
                        name=template_dir.name,
                        path=template_dir,
                        description="[Invalid template - see logs]",
                        has_preview=False,
                        has_metadata=False,
                        slide_count=0,
                        source=source,
                    )
                )

    # Sort templates
    if sort_by == "name":
        all_templates.sort(key=lambda t: t.name)
    elif sort_by == "source":
        all_templates.sort(key=lambda t: (t.source, t.name))
    elif sort_by == "slide_count":
        all_templates.sort(key=lambda t: (-t.slide_count, t.name))
    else:
        logger.warning(f"Unknown sort_by value: {sort_by}, using 'name'")
        all_templates.sort(key=lambda t: t.name)

    logger.info(f"Discovered {len(all_templates)} templates")
    return all_templates


def find_template(name: str) -> Path | None:
    """
    Find a template by name across all search paths.

    Args:
        name: Template name to search for

    Returns:
        Path to the template directory, or None if not found

    Example:
        >>> template_path = find_template("beamer")
        >>> if template_path:
        ...     print(f"Found template at {template_path}")
    """
    templates = discover_templates()

    for template in templates:
        if template.name == name:
            return template.path

    logger.warning(f"Template '{name}' not found")
    return None


def list_template_names() -> list[str]:
    """
    Get a list of all available template names.

    Returns:
        List of template names

    Example:
        >>> names = list_template_names()
        >>> print("Available templates:", ", ".join(names))
    """
    templates = discover_templates()
    return [template.name for template in templates]


if __name__ == "__main__":
    # CLI tool for template discovery
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--validate":
        # Validate all templates
        templates = discover_templates(include_invalid=True)
        print(f"\nFound {len(templates)} templates:\n")

        for template in templates:
            is_valid, issues = validate_template(template.path)
            status = "✓ VALID" if is_valid and not issues else "⚠ ISSUES"

            print(f"{status} {template.name}")
            print(f"  Source: {template.source}")
            print(f"  Path: {template.path}")

            if issues:
                print("  Issues:")
                for issue in issues:
                    print(f"    - {issue}")

            print()
    else:
        # List all templates
        templates = discover_templates()
        print(f"\nDiscovered {len(templates)} templates:\n")

        for template in templates:
            preview_marker = "🖼" if template.has_preview else "  "
            metadata_marker = "📊" if template.has_metadata else "  "

            print(f"{preview_marker}{metadata_marker} {template.name}")
            print(f"     {template.description}")
            print(f"     Source: {template.source}")

            if template.slide_count > 0:
                print(f"     Slides: {template.slide_count}")

            print()

        print("\nLegend: 🖼 = has preview, 📊 = has metadata")
        print("\nUse --validate to check template validity")

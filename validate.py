"""Validate YAML files for Awesome Certifications

Raises:
    ValueError: Invalid Category or sub-category
    KeyError: Missing Parent key
"""
from pathlib import Path
import yaml


def import_yaml(filename: str) -> dict:
    """Load Yaml file.

    Args:
        filename (str): string ending in '.yaml'

    Returns:
        dict: yaml dictionary
    """
    yaml_file: Path = Path(".", filename)

    with yaml_file.open(encoding="UTF-8") as file:
        yaml_data: dict = yaml.safe_load(file)

    return yaml_data


def validate_categories() -> None:
    """Validate category relation and existence of parent.

    Raises:
        ValueError: Invalid Category or sub-category
        KeyError: Missing Parent key
    """
    categories_data: dict = import_yaml("categories.yaml")

    categories: set = set(categories_data['Categories'])
    sub_categories: dict = categories_data['Sub-Categories']
    all_cats_and_sub_cats: set = categories | set(sub_categories.keys())

    for key in sub_categories:
        try:
            key_parents: set = set(sub_categories[key]["Parent"])

            if not key_parents <= all_cats_and_sub_cats:
                raise ValueError(key, key_parents)

        except KeyError as err:
            raise KeyError(f"{key} sub-category has no {err.args[0]}") from err
        except ValueError as err:
            raise ValueError(
                f"Entry '{err.args[0]}' has invalid parent:",
                f" {err.args[1] - all_cats_and_sub_cats}"
            ) from err


if __name__ == "__main__":
    validate_categories()

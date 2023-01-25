"""Validate YAML files for Awesome Certifications

Raises:
    ValueError: Invalid Category or sub-category
    KeyError: Missing Parent key
"""
from pathlib import Path
import yaml
import yamllint
from yamllint import config as yaml_config
from yamllint import linter as yaml_linter
from iteration_utilities import duplicates


def import_yaml(filename: str) -> dict:
    """Load Yaml file.

    Args:
        filename (str): string ending in '.yaml'

    Returns:
        dict: yaml dictionary
    """
    yaml_file: Path = Path(".", filename)

    lint_yaml_file(yaml_file)

    with yaml_file.open(encoding="UTF-8") as file:
        yaml_data: dict = yaml.safe_load(file)

    return yaml_data


def lint_yaml_file(yaml_path: Path) -> None:
    """Lint yaml file with yamllint.

    Args:
        yaml_path (Path): path to yaml file

    Raises:
        RuntimeError: If yaml has linting errors
        SystemExit: exit if errors
    """
    config = yaml_config.YamlLintConfig("extends: default")

    with yaml_path.open(encoding="UTF-8") as yaml_file:
        yaml_problems = yaml_linter.run(yaml_file, config)

        problems: list = [
            problem
            for problem in yaml_problems
            if isinstance(problem, yamllint.linter.LintProblem)
        ]

        try:
            if problems:
                raise RuntimeError(problems)
        except RuntimeError as err:
            print(f"The YAML document {yaml_path} has the following errors:")
            print(*problems, sep="\n")
            raise SystemExit from err


def validate_categories() -> None:
    """Validate categories.yaml"""
    categories_data: dict = import_yaml("categories.yaml")

    check_categories_for_duplicates(categories_data["Categories"])
    validate_subcategory_parents(categories_data)


def check_categories_for_duplicates(categories: list) -> None:
    """Check for duplicates in main category list.

    Args:
        categories (list): list from yaml

    Raises:
        ValueError: Duplicate items detected.
    """
    try:
        if duplicate_categories := list(duplicates(categories)):
            raise ValueError(duplicate_categories)
    except ValueError as err:
        raise ValueError(
            "::: Error in categories.yaml: duplicate categories not allowed: ",
            err.args[0],
        ) from err


def validate_subcategory_parents(categories_data: dict) -> None:
    """Validate category relation and existence of parent.

    Raises:
        ValueError: Invalid Category or sub-category
        KeyError: Missing Parent key
    """

    categories: set = set(categories_data["Categories"])
    sub_categories: dict = categories_data["Sub-Categories"]
    all_cats_and_sub_cats: set = categories | set(sub_categories.keys())

    # Require Parent key and valid category or sub-category as parent.
    for key in sub_categories:
        try:
            key_parents: set = set(sub_categories[key]["Parent"])

            # <= is subset operator not less-than-or-equal
            if not key_parents <= all_cats_and_sub_cats:
                raise ValueError(key, key_parents)

        except (KeyError, TypeError) as err:
            raise KeyError(
                "::: Error in categories.yaml: "  # noblack
                f"{key} sub-category has no Parent"
            ) from err
        except ValueError as err:
            raise ValueError(
                "::: Error in categories.yaml: ",
                f"Entry '{err.args[0]}' has invalid parent:",
                # - is a set difference operator, not subtract.
                f" {err.args[1] - all_cats_and_sub_cats}",
            ) from err


def validate_providers() -> None:
    """Validate providers.yaml"""
    providers_data: dict = import_yaml("providers.yaml")

    check_provider_keys(providers_data, required_keys={"Short Name", "URLs"})


def check_provider_keys(providers_data: dict, required_keys: set) -> None:
    """Validate that provider has two keys, "Short Name" and "URLs"

    Args:
        providers_data (dict): yaml dict

    Raises:
        RuntimeError: if missing keys or too many keys.
    """

    problems: list = []
    for provider in providers_data["Providers"]:
        present_keys = set(providers_data["Providers"][provider].keys())

        if required_keys != present_keys:
            problems.append(
                (
                    f"Provider '{provider}' is missing the following keys: "
                    f"{required_keys - present_keys}"
                )
            )

        if len(present_keys) > len(required_keys):
            problems.append(
                (f"Provider '{provider}' has too many keys: {present_keys}")
            )

    try:
        if problems:
            raise RuntimeError(problems)
    except RuntimeError as err:
        print("The providers in providers.yaml have the following errors:")
        print(*problems, sep="\n")
        raise SystemExit from err


def validate() -> None:
    """validate awesome certification yaml files."""
    validate_categories()
    validate_providers()


if __name__ == "__main__":
    validate()

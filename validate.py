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

CERTIFICATIONS_YAML: str = "certifications.yaml"
CATEGORIES_YAML: str = "categories.yaml"
PROVIDERS_YAML: str = "providers.yaml"


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
    categories_data: dict = import_yaml(CATEGORIES_YAML)

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
    providers_data: dict = import_yaml(PROVIDERS_YAML)

    check_keys(  # noblack
        providers_data, "Providers", required_keys={"Short Name", "URLs"}
    )


def check_keys(yaml_data: dict, root_key: str, required_keys: set) -> None:
    """Validate that provider has two keys, "Short Name" and "URLs"

    Args:
        yaml_data (dict): yaml dict

    Raises:
        RuntimeError: if missing keys or too many keys.
    """

    if root_key == "Providers":
        entry_type = "Provider"
    elif root_key == "Certifications":
        entry_type = "Certification"

    problems: list = []
    for entry in yaml_data[root_key]:
        present_keys = set(yaml_data[root_key][entry].keys())

        if required_keys != present_keys:
            problems.append(
                (
                    f"{entry_type} '{entry}' is missing the following keys: "
                    f"{required_keys - present_keys}"
                )
            )

        if len(present_keys) > len(required_keys):
            problems.append(
                (f"{entry_type} '{entry}' has too many keys: {present_keys}")
            )

    try:
        if problems:
            raise RuntimeError(problems)
    except RuntimeError as err:
        print(
            f"The {root_key.lower()} in {root_key.lower()}.yaml "
            "have the following errors:"
        )
        print(*problems, sep="\n")
        raise SystemExit from err


def validate_certifications() -> None:
    """Validate certifications.yaml"""

    certifications_data: dict = import_yaml(CERTIFICATIONS_YAML)

    check_keys(
        certifications_data,
        "Certifications",
        required_keys={
            "Short Name",
            "Provider",
            "Categories",
            "Sub-Categories",
            "Exam Code",
            "Cost",
            "Exam Duration",
            "Number of Questions",
            "Exam Format",
            "Passing Score",
            "Delivery Channel",
            "Exam Syllabus",
            "Testing Policies",
            "Hard Prerequisites",
            "Soft Prerequisites",
            "Registration URL",
            "Practice Test URLs",
            "Study URLs",
        },
    )

    validate_cert_providers()
    validate_cert_categories()


def validate_cert_providers() -> None:
    """Check that cert provider is in providers.yaml"""

    certifications_data: dict = import_yaml(CERTIFICATIONS_YAML)
    providers_data: dict = import_yaml(PROVIDERS_YAML)

    certifications: dict = certifications_data['Certifications']
    providers: dict = providers_data["Providers"]

    providers_set: set = set(list(providers))

    problems: list = []
    for cert in certifications:
        provider: str = certifications[cert]["Provider"]
        if provider != "NA" and provider not in providers_set:
            problems.append(
                f"Error for cert: '{cert}'. "
                f"'{provider}' not in providers.yaml"
            )

    exit_on_problem(problems)


def validate_cert_categories() -> None:
    """Validate certification categories are in categories.yaml"""

    certifications_data: dict = import_yaml(CERTIFICATIONS_YAML)
    categories_data: dict = import_yaml(CATEGORIES_YAML)

    certifications: dict = certifications_data['Certifications']
    categories: set = set(categories_data["Categories"])
    sub_categories: dict = categories_data["Sub-Categories"]
    all_cats_and_sub_cats: set = categories | set(sub_categories.keys())

    problems: list = []
    for cert in certifications:
        cert_categories: set = set(certifications[cert]['Categories'])
        cert_subcategories: set = set(certifications[cert]['Sub-Categories'])
        cert_cats_and_sub_cats: set = cert_categories | cert_subcategories

        if not cert_cats_and_sub_cats <= all_cats_and_sub_cats:
            problems.append(
                f"Error for cert: '{cert}'. "
                f"{cert_cats_and_sub_cats - all_cats_and_sub_cats}"
                " is not a category or sub-category defined in categories.yaml"
            )

    exit_on_problem(problems)


def exit_on_problem(problems: list) -> None:
    """Exit if problem.

    Args:
        problems (list): list of problems

    Raises:
        ValueError:
        SystemExit:
    """

    try:
        if problems:
            raise ValueError(problems)
    except ValueError as err:
        print(*problems, sep="\n")
        raise SystemExit from err


def validate() -> None:
    """validate awesome certification yaml files."""
    validate_categories()
    validate_providers()
    validate_certifications()


if __name__ == "__main__":
    validate()

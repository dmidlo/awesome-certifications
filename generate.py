"""WARNING: MVP code ahead.  It's smelly"""

from collections import deque
from mdutils.mdutils import MdUtils

from validate import validate, import_yaml

CERTIFICATIONS_YAML: str = "certifications.yaml"
CATEGORIES_YAML: str = "categories.yaml"
PROVIDERS_YAML: str = "providers.yaml"


def initialize_dom() -> dict:
    """Create a document object model to be rendered as markdown

    there has got to be a better way.

    This takes the contents of the yaml files and creates
    a sensibly structured dict from the data model(s) they
    describe.

    Returns:
        dict: a dom that only has headings (dict keys)
    """
    dom: dict = {}
    certifications_data = import_yaml(CERTIFICATIONS_YAML)
    categories_data = import_yaml(CATEGORIES_YAML)

    certifications = certifications_data["Certifications"]
    categories = set(categories_data["Categories"])
    sub_categories = categories_data["Sub-Categories"]
    sub_category_parents = {
        parent
        for subcat in sub_categories
        for parent in sub_categories[subcat]["Parent"]
    } - categories
    parents = categories | sub_category_parents

    dom_cats = {
        cat
        for cert in certifications
        for cat in certifications[cert]["Categories"]  # noqa:E501
    }
    dom_subcats = {
        subcat
        for cert in certifications
        for subcat in certifications[cert]["Sub-Categories"]
    }
    dom_all_cats = deque(dom_cats | dom_subcats)

    while len(dom_all_cats) > 0:
        cat = dom_all_cats.popleft()

        if cat in parents and cat in categories:
            if cat not in dom:
                dom[cat] = {}
            else:
                dom_all_cats.append(cat)

        elif cat in parents and cat not in categories:
            if set(sub_categories[cat]["Parent"]) <= categories:

                for parent in sub_categories[cat]["Parent"]:
                    if parent in dom:
                        dom[parent][cat] = {}
                    else:
                        dom_all_cats.append(cat)

        else:
            for parent in sub_categories[cat]["Parent"]:
                if parent in dom and parent in categories:
                    dom[parent][cat] = {}
                elif parent not in dom and parent in categories:
                    dom_all_cats.append(cat)
                else:
                    for cat_parent in sub_categories[cat]["Parent"]:
                        for sub_parent in sub_categories[cat_parent]["Parent"]:
                            if sub_parent in categories:
                                if (
                                    sub_parent in dom
                                    and cat_parent in dom[sub_parent]  # noqa:E501
                                ):  # noqa:E501
                                    dom[sub_parent][cat_parent][cat] = {}
                                else:
                                    dom_all_cats.append(cat)
                            else:
                                for root_parent in sub_categories[sub_parent][
                                    "Parent"
                                ]:  # noqa:E501
                                    if (
                                        root_parent in dom
                                        and sub_parent in dom[root_parent]
                                    ):
                                        if (
                                            cat_parent
                                            not in dom[root_parent][sub_parent]
                                        ):
                                            dom[root_parent][sub_parent][
                                                cat_parent
                                            ] = {}

                                        dom[root_parent][sub_parent][
                                            cat_parent
                                        ][  # noqa:E501
                                            cat
                                        ] = {}
                                    else:
                                        dom_all_cats.append(cat)

    return dom


def populate_dom_with_certs(dom: dict) -> dict:
    """Add certs to their respective nodes in the skeleton dom

    Args:
        dom (dict): skeleton dom (from initialize_dom)

    Returns:
        dict: unsorted but data complete dom
    """
    certifications_data = import_yaml(CERTIFICATIONS_YAML)
    categories_data = import_yaml(CATEGORIES_YAML)

    certifications = certifications_data["Certifications"]
    categories = set(categories_data["Categories"])
    sub_categories = categories_data["Sub-Categories"]

    for cert_key in certifications:
        cert_data = certifications[cert_key]

        cert_categories = set(cert_data["Categories"])
        cert_sub_categories = set(cert_data["Sub-Categories"])
        all_cert_cats = deque(cert_categories | cert_sub_categories)

        cert_cat_ancestry: list = []
        while len(all_cert_cats) > 0:
            cat = all_cert_cats.popleft()

            if cert_cat_ancestry and cat not in categories:
                if sub_categories[cat]["Parent"][0] == cert_cat_ancestry[-1]:
                    cert_cat_ancestry.append(cat)
                else:
                    all_cert_cats.append(cat)
            elif cat in categories:
                cert_cat_ancestry.append(cat)
            else:
                all_cert_cats.append(cat)

        merge_cert_into_dom(dom, cert_cat_ancestry[-1], {cert_key: cert_data})

    return dom


def merge_cert_into_dom(dom: dict, dest_key: str, dest_data: dict):
    """Traverse and Recurse the dom add data when appropriate key is found

    Args:
        dom (dict): skeleton dom
        dest_key (str): existing key in skeleton dom
        dest_data (dict): value/data to add to skeleton key
    """
    for item in dom.items():
        if isinstance(item[1], dict):
            if dest_key == item[0]:
                item[1].update(dest_data)
                break
            else:
                merge_cert_into_dom(item[1], dest_key, dest_data)


def sort_dom(dom: dict) -> dict:
    """Sort dom with default sort

    Args:
        dom (dict): data complete dom

    Returns:
        dict: sorted dom

    TODO: Once more certifications are filled out, need to add cert sorting.
    """
    certifications_data = import_yaml(CERTIFICATIONS_YAML)
    categories_data = import_yaml(CATEGORIES_YAML)
    providers_data = import_yaml(PROVIDERS_YAML)

    certifications = list(certifications_data["Certifications"])
    categories: list = categories_data["Categories"]
    sub_categories: list = list(categories_data["Sub-Categories"])
    cats_and_subcats: set = set(categories) | set(sub_categories)

    providers = list(providers_data["Providers"])
    sorting_order: list = (
        categories + sub_categories + providers + certifications
    )  # noqa:E501

    dom = sort_cats_and_sub_cats(dom, cats_and_subcats, sorting_order)
    return dom


def sort_cats_and_sub_cats(
    dom: dict, cats_and_subcats: set, sorting_order: list, v_dom=dict()
):
    """Traverse and recurse through dom dict, sorting each key's children.

    Args:
        dom (dict): document object model.
        cats_and_subcats (set): all categories and subcategories
        sorting_order (list): might someday be used to provide custom sort.
        v_dom (_type_, optional): placeholder to build a sorted dom.

    Returns:
        dict: returns a sorted copy of dom.
    """
    if len(v_dom) == 0:
        v_dom = dict(sorted(dom.items()))
    else:
        v_dom = dict(sorted(v_dom.items()))

    for item in v_dom.items():
        if item[0] in cats_and_subcats and isinstance(item[1], dict):
            sorted_item_1 = dict(sorted(item[1].items()))
            item[1].clear()
            item[1].update(sorted_item_1)
            sort_cats_and_sub_cats(
                dom, cats_and_subcats, sorting_order, item[1]
            )  # noqa:E501


    # Quick and dirty solution.  Tired of working on sorting
    # this works, but it's yucky.
    if dom == v_dom:
        return v_dom


def convert_dom_to_markdown(dom: dict) -> None:
    """Convert dom to markdown using mdutils

    Args:
        dom (dict): the dom.
    """
    categories_data = import_yaml(CATEGORIES_YAML)

    categories: list = categories_data["Categories"]
    sub_categories: list = list(categories_data["Sub-Categories"])
    cats_and_subcats: set = set(categories) | set(sub_categories)

    md_file = MdUtils(file_name="README", title="Awesome Certifications")

    generate_markdown_body(dom, md_file, cats_and_subcats)

    md_file.new_table_of_contents(table_title="Contents", depth=2)
    md_file.create_md_file()


def generate_markdown_body(dom: dict, md_file, cats_and_subcats: set, depth=0):
    """Traverse and recurse through the dom adding content to md_file.

    Args:
        dom (dict): the dom.
        md_file (_type_): a instance of an MdUtils file.
        cats_and_subcats (set): a set of all categories and subcategories.
        depth (int, optional): recursion depth to set markdown header level.
    """
    depth += 1
    for item in dom.items():
        if item[0] in cats_and_subcats:
            md_file.new_header(level=depth, title=item[0])
            generate_markdown_body(item[1], md_file, cats_and_subcats, depth)
        else:
            md_file.new_header(level=depth, title=item[0])
            for key in item[1]:
                md_file.new_line(f"**{key}:** {item[1][key]}")


def generate() -> None:
    """Put it all together."""
    convert_dom_to_markdown(
        sort_dom(populate_dom_with_certs(initialize_dom()))
    )  # noqa:E501


def run() -> None:
    """Validate yaml file contents and generate README.md"""
    validate()
    generate()


if __name__ == "__main__":
    run()

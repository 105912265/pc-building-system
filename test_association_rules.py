# Author: Kshitij Kshirsagar
# Filename: test_association_rules.py
# Last edited: 19/06/2026

from src.association_recommender import (
    create_component_item,
    load_association_rules,
    recommend_associated_parts,
    remove_component_prefix
)


def test_cpu_motherboard_rules():
    """
    used to test motherboard recommendations based on a selected CPU
    :return: None
    """
    rules = load_association_rules()

    selected_items = [
        create_component_item(
            "CPU",
            "AMD Ryzen 9 5900X"
        )
    ]

    recommendations = recommend_associated_parts(
        selected_items=selected_items,
        rules=rules,
        required_component_type="Motherboard",
        limit=5
    )

    print(
        "Motherboard recommendations "
        "for AMD Ryzen 9 5900X:"
    )

    if not recommendations:
        print(
            "No association recommendations were found."
        )
        return

    for index, recommendation in enumerate(
        recommendations,
        start=1
    ):
        component_name = remove_component_prefix(
            recommendation["item"]
        )

        print(
            f"{index}. {component_name}"
        )

        print(
            f"   Confidence: "
            f"{recommendation['confidence']:.3f}"
        )

        print(
            f"   Lift: "
            f"{recommendation['lift']:.3f}"
        )

        print(
            f"   Support: "
            f"{recommendation['support']:.3f}"
        )


if __name__ == "__main__":
    test_cpu_motherboard_rules()
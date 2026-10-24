# Author: Kshitij Kshirsagar
# Filename: association_recommender.py
# Last edited: 19/06/2026

import os

import joblib


def load_association_rules(
    filename="models/association_rules.pkl"
):
    """
    used to load trained association rules
    :param filename: location of the saved association rule model
    :return rules: DataFrame containing association rules
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(
            f"Association rule model was not found: {filename}. "
            "Run src/train_association_rules.py first."
        )

    return joblib.load(filename)


def create_component_item(
    component_type,
    component_name
):
    """
    used to create the item format expected by the association rules
    :param component_type: component category such as CPU or GPU
    :param component_name: name of selected component
    :return: formatted association rule item
    """
    return f"{component_type}:{component_name}"


def recommend_associated_parts(
    selected_items,
    rules,
    required_component_type=None,
    limit=5
):
    """
    used to recommend commonly associated components
    :param selected_items: list of selected component strings
    :param rules: DataFrame containing trained association rules
    :param required_component_type: optional component type to recommend
    :param limit: maximum number of recommendations returned
    :return recommendations: ranked associated part recommendations
    """
    selected_set = set(
        selected_items
    )

    found_recommendations = []

    for _, rule in rules.iterrows():
        antecedents = set(
            rule["antecedents"]
        )

        consequents = set(
            rule["consequents"]
        )

        if not antecedents.issubset(
            selected_set
        ):
            continue

        for item in consequents:
            if item in selected_set:
                continue

            if required_component_type is not None:
                required_prefix = (
                    f"{required_component_type}:"
                )

                if not item.startswith(
                    required_prefix
                ):
                    continue

            recommendation_score = (
                float(rule["lift"]) * 0.50
                + float(rule["confidence"]) * 0.35
                + float(rule["support"]) * 0.15
            )

            found_recommendations.append({
                "item": item,
                "confidence": float(
                    rule["confidence"]
                ),
                "lift": float(
                    rule["lift"]
                ),
                "support": float(
                    rule["support"]
                ),
                "score": recommendation_score
            })

    found_recommendations.sort(
        key=lambda recommendation: (
            recommendation["score"],
            recommendation["lift"],
            recommendation["confidence"]
        ),
        reverse=True
    )

    unique_recommendations = []
    used_items = set()

    for recommendation in found_recommendations:
        item = recommendation["item"]

        if item in used_items:
            continue

        used_items.add(item)

        unique_recommendations.append(
            recommendation
        )

        if len(unique_recommendations) >= limit:
            break

    return unique_recommendations


def remove_component_prefix(item):
    """
    used to remove the component category from a recommendation item
    :param item: item such as Motherboard:MSI B550M
    :return: component name without prefix
    """
    if ":" not in item:
        return item

    return item.split(
        ":",
        1
    )[1]


def reorder_components_by_rules(
    components,
    rule_suggestions
):
    """
    used to place association-rule suggestions before other compatible components
    :param components: list of compatible component objects
    :param rule_suggestions: association rule recommendations
    :return reordered_components: compatible components with suggested parts first
    """
    suggested_names = [
        remove_component_prefix(
            suggestion["item"]
        )
        for suggestion in rule_suggestions
    ]

    suggestion_positions = {
        name: index
        for index, name in enumerate(
            suggested_names
        )
    }

    suggested_components = [
        component
        for component in components
        if component.name in suggestion_positions
    ]

    suggested_components.sort(
        key=lambda component: suggestion_positions[
            component.name
        ]
    )

    other_components = [
        component
        for component in components
        if component.name not in suggestion_positions
    ]

    return (
        suggested_components
        + other_components
    )


def get_suggested_component_names(
    rule_suggestions
):
    """
    used to return only the component names from association rule suggestions
    :param rule_suggestions: list of association recommendations
    :return: set containing suggested component names
    """
    return {
        remove_component_prefix(
            suggestion["item"]
        )
        for suggestion in rule_suggestions
    }
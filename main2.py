# Author: Kshitij Kshirsagar
# Filename: main2.py
# Last edited: 19/06/2026

from pc_build import PCBUILD

from src.data_loader import (
    load_cpus,
    load_gpus,
    load_motherboards,
    load_psu,
    load_ram,
    load_storage
)

from src.build_generator import (
    recommend_three_builds,
    find_compatible_motherboards,
    find_compatible_ram,
    find_affordable_storage,
    final_build_is_compatible
)

from src.association_recommender import (
    create_component_item,
    get_suggested_component_names,
    load_association_rules,
    recommend_associated_parts,
    reorder_components_by_rules
)


def get_number_input(message, minimum=0):
    """
    used to receive and validate a number entered by the user
    :param message: input message shown to user
    :param minimum: smallest accepted number
    :return value: validated float value
    """
    while True:
        try:
            value = float(
                input(message)
            )

            if value < minimum:
                print(
                    f"Please enter a value "
                    f"of at least {minimum}."
                )
                continue

            return value

        except ValueError:
            print(
                "Please enter a valid number."
            )


def get_menu_choice(message, options):
    """
    used to receive a valid numbered choice from the user
    :param message: heading shown before menu options
    :param options: list of available choices
    :return: selected option value
    """
    print(message)

    for index, option in enumerate(
        options,
        start=1
    ):
        print(
            f"{index}. {option}"
        )

    while True:
        try:
            choice = int(
                input("Select an option: ")
            )

            if 1 <= choice <= len(options):
                return options[
                    choice - 1
                ]

            print(
                "Please select a valid "
                "option number."
            )

        except ValueError:
            print(
                "Please enter a number."
            )


def choose_component(
    message,
    components,
    suggested_names=None
):
    """
    used to let the user choose one component from a filtered list
    :param message: heading shown before component options
    :param components: list of compatible component objects
    :param suggested_names: names suggested by association rules
    :return: component selected by user or None
    """
    if not components:
        return None

    if suggested_names is None:
        suggested_names = set()

    print(
        f"\n{message}"
    )

    for index, component in enumerate(
        components,
        start=1
    ):
        suggestion_text = ""

        if component.name in suggested_names:
            suggestion_text = (
                " [Association recommendation]"
            )

        print(
            f"{index}. {component.name} - "
            f"${component.price:.2f}"
            f"{suggestion_text}"
        )

    while True:
        try:
            choice = int(
                input("Select an option: ")
            )

            if 1 <= choice <= len(components):
                return components[
                    choice - 1
                ]

            print(
                "Please select a valid "
                "option number."
            )

        except ValueError:
            print(
                "Please enter a number."
            )


def choose_recommendation(recommendations):
    """
    used to let the user choose one recommended build
    :param recommendations: list containing three recommended builds
    :return: selected recommendation dictionary
    """
    print(
        "\nChoose a recommended "
        "core component option:"
    )

    while True:
        try:
            choice = int(
                input("Select an option: ")
            )

            if 1 <= choice <= len(
                recommendations
            ):
                return recommendations[
                    choice - 1
                ]

            print(
                "Please select a valid "
                "option number."
            )

        except ValueError:
            print(
                "Please enter a number."
            )


def display_recommendations(
    recommendations,
    budget
):
    """
    used to display value, balanced and performance recommendations
    :param recommendations: list of recommended build dictionaries
    :param budget: user's selected budget
    :return: None
    """
    print(
        "\nRecommended Core Component Options"
    )

    for index, recommendation in enumerate(
        recommendations,
        start=1
    ):
        print(
            f"\nOption {index}: "
            f"{recommendation['type']}"
        )

        print(
            recommendation["description"]
        )

        print(
            f"CPU: "
            f"{recommendation['cpu'].name} - "
            f"${recommendation['cpu'].price:.2f}"
        )

        print(
            f"GPU: "
            f"{recommendation['gpu'].name} - "
            f"${recommendation['gpu'].price:.2f}"
        )

        print(
            f"PSU: "
            f"{recommendation['psu'].name} - "
            f"${recommendation['psu'].price:.2f}"
        )

        print(
            f"Suggested motherboard: "
            f"{recommendation['motherboard'].name}"
        )

        print(
            f"Suggested RAM: "
            f"{recommendation['ram'].name}"
        )

        print(
            f"Suggested storage: "
            f"{recommendation['storage'].name}"
        )

        print(
            f"Estimated complete price: "
            f"${recommendation['estimated_total']:.2f}"
        )

        difference = (
            recommendation["estimated_total"]
            - budget
        )

        if difference > 0:
            print(
                f"Above budget by: "
                f"${difference:.2f}"
            )
        else:
            print(
                f"Below budget by: "
                f"${abs(difference):.2f}"
            )


def main():
    """
    used to run the complete PC recommendation system
    :return: None
    """
    cpus = load_cpus(
        "data/cpu_bench.csv"
    )

    gpus = load_gpus(
        "data/gpu_bench.csv"
    )

    rams = load_ram(
        "data/ram.csv"
    )

    psus = load_psu(
        "data/psus.csv"
    )

    motherboards = load_motherboards(
        "data/motherboards.csv"
    )

    storages = load_storage(
        "data/storage.csv"
    )

    try:
        rules = load_association_rules()

    except FileNotFoundError as error:
        print(error)
        print(
            "Train the association rules before "
            "running the recommender."
        )
        return

    budget = get_number_input(
        "What is your total PC budget? $",
        minimum=1
    )

    preferred_cpu_brand = get_menu_choice(
        "\nChoose your CPU preference:",
        [
            "Any",
            "AMD",
            "Intel"
        ]
    )

    preferred_gpu_brand = get_menu_choice(
        "\nChoose your GPU preference:",
        [
            "Any",
            "NVIDIA",
            "Radeon"
        ]
    )

    recommendations = recommend_three_builds(
        cpus=cpus,
        gpus=gpus,
        motherboards=motherboards,
        ram_list=rams,
        storage_list=storages,
        psus=psus,
        budget=budget,
        preferred_cpu_brand=(
            preferred_cpu_brand
        ),
        preferred_gpu_brand=(
            preferred_gpu_brand
        )
    )

    if not recommendations:
        print(
            "\nNo build recommendations were "
            "found for the selected budget "
            "and preferences."
        )
        return

    display_recommendations(
        recommendations,
        budget
    )

    selected_recommendation = (
        choose_recommendation(
            recommendations
        )
    )

    selected_cpu = (
        selected_recommendation["cpu"]
    )

    selected_gpu = (
        selected_recommendation["gpu"]
    )

    selected_psu = (
        selected_recommendation["psu"]
    )

    selected_association_items = [
        create_component_item(
            "CPU",
            selected_cpu.name
        ),
        create_component_item(
            "GPU",
            selected_gpu.name
        ),
        create_component_item(
            "PSU",
            selected_psu.name
        )
    ]

    maximum_final_price = max(
        budget,
        selected_recommendation[
            "estimated_total"
        ]
    )

    remaining_budget = (
        maximum_final_price
        - selected_recommendation[
            "core_price"
        ]
    )

    motherboard_rule_suggestions = (
        recommend_associated_parts(
            selected_items=(
                selected_association_items
            ),
            rules=rules,
            required_component_type=(
                "Motherboard"
            ),
            limit=5
        )
    )

    compatible_motherboards = (
        find_compatible_motherboards(
            selected_cpu,
            motherboards,
            remaining_budget
        )
    )

    compatible_motherboards = (
        reorder_components_by_rules(
            compatible_motherboards,
            motherboard_rule_suggestions
        )
    )

    suggested_motherboard_names = (
        get_suggested_component_names(
            motherboard_rule_suggestions
        )
    )

    selected_motherboard = choose_component(
        "Choose a compatible motherboard:",
        compatible_motherboards,
        suggested_motherboard_names
    )

    if selected_motherboard is None:
        print(
            "No compatible motherboards were "
            "found within the available price."
        )
        return

    remaining_budget -= (
        selected_motherboard.price
    )

    selected_association_items.append(
        create_component_item(
            "Motherboard",
            selected_motherboard.name
        )
    )

    ram_rule_suggestions = (
        recommend_associated_parts(
            selected_items=(
                selected_association_items
            ),
            rules=rules,
            required_component_type="RAM",
            limit=5
        )
    )

    compatible_ram = find_compatible_ram(
        selected_motherboard,
        rams,
        remaining_budget
    )

    compatible_ram = (
        reorder_components_by_rules(
            compatible_ram,
            ram_rule_suggestions
        )
    )

    suggested_ram_names = (
        get_suggested_component_names(
            ram_rule_suggestions
        )
    )

    selected_ram = choose_component(
        "Choose compatible RAM:",
        compatible_ram,
        suggested_ram_names
    )

    if selected_ram is None:
        print(
            "No compatible RAM was found "
            "within the available price."
        )
        return

    remaining_budget -= selected_ram.price

    selected_association_items.append(
        create_component_item(
            "RAM",
            selected_ram.name
        )
    )

    storage_rule_suggestions = (
        recommend_associated_parts(
            selected_items=(
                selected_association_items
            ),
            rules=rules,
            required_component_type="Storage",
            limit=5
        )
    )

    affordable_storage = (
        find_affordable_storage(
            storages,
            remaining_budget
        )
    )

    affordable_storage = (
        reorder_components_by_rules(
            affordable_storage,
            storage_rule_suggestions
        )
    )

    suggested_storage_names = (
        get_suggested_component_names(
            storage_rule_suggestions
        )
    )

    selected_storage = choose_component(
        "Choose a storage option:",
        affordable_storage,
        suggested_storage_names
    )

    if selected_storage is None:
        print(
            "No storage options were found "
            "within the available price."
        )
        return

    final_build = PCBUILD()

    final_build.add_component(
        selected_cpu
    )

    final_build.add_component(
        selected_gpu
    )

    final_build.add_component(
        selected_motherboard
    )

    final_build.add_component(
        selected_ram
    )

    final_build.add_component(
        selected_storage
    )

    final_build.add_component(
        selected_psu
    )

    is_compatible = (
        final_build_is_compatible(
            selected_cpu,
            selected_gpu,
            selected_psu,
            selected_motherboard,
            selected_ram,
            selected_storage
        )
    )

    if not is_compatible:
        print(
            "\nThe final build contains "
            "incompatible components."
        )
        return

    print(
        "\nFinal PC Build"
    )

    print(
        "--------------"
    )

    print(
        final_build.display_build()
    )

    final_price = (
        final_build.total_price()
    )

    price_difference = (
        final_price - budget
    )

    print(
        f"\nTotal price: "
        f"${final_price:.2f}"
    )

    print(
        f"Total wattage: "
        f"{final_build.total_watts()}W"
    )

    if price_difference > 0:
        print(
            f"This build is "
            f"${price_difference:.2f} "
            f"above your budget."
        )
    else:
        print(
            f"You have "
            f"${abs(price_difference):.2f} "
            f"remaining in your budget."
        )

    final_build.save_build()

    print(
        "\nBuild saved to output/build.txt"
    )


if __name__ == "__main__":
    main()
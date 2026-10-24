# Author: Kshitij Kshirsagar
# Filename: app.py
# Last edited: 14/08/2026

from html import escape

import streamlit as st

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

from src.fps_estimator import (
    load_game_fps_baselines,
    estimate_fps_for_games
)


st.set_page_config(
    page_title="Smart PC Builder",
    page_icon="🖥️",
    layout="wide"
)


def load_css(css_file):
    with open(css_file, "r", encoding="utf8") as file:
        st.markdown(
            f"<style>{file.read()}</style>",
            unsafe_allow_html=True
        )


load_css("assets/style.css")


@st.cache_resource
def load_component_data():
    cpus = load_cpus("data/cpu_bench.csv")
    gpus = load_gpus("data/gpu_bench.csv")
    rams = load_ram("data/ram.csv")
    psus = load_psu("data/psus.csv")
    motherboards = load_motherboards("data/motherboards.csv")
    storages = load_storage("data/storage.csv")

    return cpus, gpus, rams, psus, motherboards, storages


@st.cache_resource
def load_rules():
    return load_association_rules()


@st.cache_resource
def load_fps_data():
    return load_game_fps_baselines("data/game_fps_baselines.csv")


def format_component(component):
    return f"{component.name} - ${component.price:.2f}"


def calculate_power_score(recommendation):
    cpu = recommendation["cpu"]
    gpu = recommendation["gpu"]

    cpu_score = min(cpu.cpu_mark / 50000, 1)
    gpu_score = min(gpu.g3d_mark / 28000, 1)

    power_score = (
        cpu_score * 0.35
        + gpu_score * 0.65
    ) * 100

    return round(power_score)


def get_power_label(power_score):
    if power_score >= 85:
        return "Extreme"

    if power_score >= 70:
        return "High"

    if power_score >= 55:
        return "Strong"

    if power_score >= 40:
        return "Moderate"

    return "Entry"


def render_html(html):
    st.markdown(
        html,
        unsafe_allow_html=True
    )


def display_header():
    render_html(
        '<div class="hero-panel">'
        '<div class="hero-tag">Benchmark-based gaming PC recommender</div>'
        '<h1>Smart PC Builder</h1>'
        '<p>Select your budget and preferences, choose a PC build, view the power indicator, and check estimated game FPS.</p>'
        '</div>'
    )


def display_build_card(recommendation, budget, index):
    power_score = calculate_power_score(recommendation)
    power_label = get_power_label(power_score)

    difference = recommendation["estimated_total"] - budget

    if difference > 0:
        budget_text = f"${difference:.2f} over budget"
        budget_class = "warning-text"
    else:
        budget_text = f"${abs(difference):.2f} under budget"
        budget_class = "positive-text"

    build_type = escape(recommendation["type"])
    description = escape(recommendation["description"])

    render_html(
        '<div class="build-choice-card">'
        f'<div class="build-choice-title">{build_type}</div>'
        f'<div class="build-choice-price">${recommendation["estimated_total"]:.2f}</div>'
        f'<div class="build-choice-power">{power_label} Power</div>'
        '<div class="mini-meter">'
        f'<div class="mini-meter-fill" style="width: {power_score}%;"></div>'
        '</div>'
        f'<p>{description}</p>'
        f'<p class="{budget_class}">{budget_text}</p>'
        '</div>'
    )

    if st.button(
        f"Select {recommendation['type']}",
        key=f"select_build_{index}"
    ):
        st.session_state["selected_recommendation_index"] = index


def display_speedometer(power_score):
    rotation = -120 + (power_score * 2.4)
    power_label = get_power_label(power_score)

    render_html(
        '<div class="gauge-panel">'
        '<div class="gauge-wrapper">'
        '<div class="gauge-ring"></div>'
        '<div class="gauge-inner"></div>'
        f'<div class="gauge-needle" style="transform: rotate({rotation}deg);"></div>'
        '<div class="gauge-center"></div>'
        f'<div class="gauge-score">{power_score}</div>'
        f'<div class="gauge-label">{power_label} Power</div>'
        '</div>'
        '</div>'
    )


def display_benchmark_strip(cpu, gpu):
    render_html(
        '<div class="benchmark-strip">'
        '<div class="benchmark-card">'
        '<div class="benchmark-title">GPU</div>'
        f'<div class="benchmark-value">{int(gpu.g3d_mark)}</div>'
        '<div class="benchmark-subtitle">G3D Mark</div>'
        '</div>'
        '<div class="benchmark-card">'
        '<div class="benchmark-title">CPU</div>'
        f'<div class="benchmark-value">{int(cpu.cpu_mark)}</div>'
        '<div class="benchmark-subtitle">CPU Mark</div>'
        '</div>'
        '</div>'
    )


def build_association_items(
    cpu=None,
    gpu=None,
    psu=None,
    motherboard=None,
    ram=None
):
    selected_items = []

    if cpu is not None:
        selected_items.append(
            create_component_item("CPU", cpu.name)
        )

    if gpu is not None:
        selected_items.append(
            create_component_item("GPU", gpu.name)
        )

    if psu is not None:
        selected_items.append(
            create_component_item("PSU", psu.name)
        )

    if motherboard is not None:
        selected_items.append(
            create_component_item("Motherboard", motherboard.name)
        )

    if ram is not None:
        selected_items.append(
            create_component_item("RAM", ram.name)
        )

    return selected_items


def display_fps_rows(fps_estimates):
    if not fps_estimates:
        st.info("Select one or more games.")
        return

    render_html('<div class="fps-output-panel">')

    for fps_entry in fps_estimates:
        fps_value = fps_entry["estimated_fps"]

        if fps_value >= 120:
            fps_class = "fps-high"
        elif fps_value >= 60:
            fps_class = "fps-medium"
        else:
            fps_class = "fps-low"

        game_name = escape(fps_entry["game"])

        render_html(
            '<div class="fps-row">'
            f'<div class="fps-game">{game_name}</div>'
            f'<div class="fps-value {fps_class}">{fps_value} FPS</div>'
            '</div>'
        )

    render_html('</div>')

    st.caption(
        "Estimated at 1080p High settings. These are comparison estimates, not guaranteed real-world FPS."
    )


def show_core_details(recommendation):
    with st.expander("View selected core components"):
        st.write(
            f"**CPU:** {recommendation['cpu'].name} - ${recommendation['cpu'].price:.2f}"
        )

        st.write(
            f"**GPU:** {recommendation['gpu'].name} - ${recommendation['gpu'].price:.2f}"
        )

        st.write(
            f"**PSU:** {recommendation['psu'].name} - ${recommendation['psu'].price:.2f}"
        )

        st.write(
            f"**Estimated complete price:** ${recommendation['estimated_total']:.2f}"
        )


def show_final_build(final_build, budget):
    final_price = final_build.total_price()
    price_difference = final_price - budget

    render_html(
        '<div class="final-panel">'
        '<h2>Final PC Build</h2>'
    )

    for component in final_build.show_components():
        render_html(
            '<div class="final-component-row">'
            f'{escape(component.display_info())}'
            '</div>'
        )

    render_html(
        f'<div class="final-summary-line"><b>Total price:</b> ${final_price:.2f}</div>'
        f'<div class="final-summary-line"><b>Total wattage:</b> {final_build.total_watts()}W</div>'
    )

    if price_difference > 0:
        st.warning(
            f"This build is ${price_difference:.2f} above your budget."
        )
    else:
        st.success(
            f"You have ${abs(price_difference):.2f} remaining in your budget."
        )

    render_html("</div>")


def main():
    display_header()

    try:
        (
            cpus,
            gpus,
            rams,
            psus,
            motherboards,
            storages
        ) = load_component_data()

    except FileNotFoundError as error:
        st.error(error)
        st.stop()

    try:
        rules = load_rules()

    except FileNotFoundError:
        st.error(
            "Association rules model was not found. Run `py src/train_association_rules.py` first."
        )
        st.stop()

    try:
        fps_data = load_fps_data()

    except FileNotFoundError:
        st.error(
            "Game FPS baseline file was not found. Create `data/game_fps_baselines.csv` first."
        )
        st.stop()

    st.sidebar.header("Build Preferences")

    budget = st.sidebar.number_input(
        "Total PC Budget ($)",
        min_value=500.0,
        max_value=5000.0,
        value=1500.0,
        step=50.0
    )

    preferred_cpu_brand = st.sidebar.selectbox(
        "CPU Preference",
        [
            "Any",
            "AMD",
            "Intel"
        ]
    )

    preferred_gpu_brand = st.sidebar.selectbox(
        "GPU Preference",
        [
            "Any",
            "NVIDIA",
            "Radeon"
        ]
    )

    if st.sidebar.button("Generate Recommendations"):
        recommendations = recommend_three_builds(
            cpus=cpus,
            gpus=gpus,
            motherboards=motherboards,
            ram_list=rams,
            storage_list=storages,
            psus=psus,
            budget=budget,
            preferred_cpu_brand=preferred_cpu_brand,
            preferred_gpu_brand=preferred_gpu_brand
        )

        st.session_state["recommendations"] = recommendations
        st.session_state["selected_recommendation_index"] = 0

    if "recommendations" not in st.session_state:
        st.info(
            "Set your preferences in the sidebar and click **Generate Recommendations**."
        )
        return

    recommendations = st.session_state["recommendations"]

    if not recommendations:
        st.error(
            "No build recommendations were found for the selected budget and preferences."
        )
        return

    st.markdown("## Choose Your PC")

    build_columns = st.columns(
        len(recommendations)
    )

    for index, recommendation in enumerate(recommendations):
        with build_columns[index]:
            display_build_card(
                recommendation,
                budget,
                index
            )

    if "selected_recommendation_index" not in st.session_state:
        st.session_state["selected_recommendation_index"] = 0

    selected_recommendation_index = st.session_state[
        "selected_recommendation_index"
    ]

    selected_recommendation = recommendations[
        selected_recommendation_index
    ]

    selected_cpu = selected_recommendation["cpu"]
    selected_gpu = selected_recommendation["gpu"]
    selected_psu = selected_recommendation["psu"]

    power_score = calculate_power_score(
        selected_recommendation
    )

    st.markdown("## Performance Lab")

    left_lab_col, right_lab_col = st.columns(
        [1, 1.2]
    )

    with left_lab_col:
        display_speedometer(power_score)
        display_benchmark_strip(
            selected_cpu,
            selected_gpu
        )

    with right_lab_col:
        render_html(
            '<div class="games-panel-title">Estimated Game Performance</div>'
        )

        game_names = fps_data["game"].tolist()

        games_col, fps_col = st.columns(
            [1, 1]
        )

        with games_col:
            selected_games = st.multiselect(
                "Games",
                game_names,
                default=game_names,
                key="selected_games"
            )

        with fps_col:
            fps_estimates = estimate_fps_for_games(
                selected_cpu,
                selected_gpu,
                selected_games,
                fps_data
            )

            display_fps_rows(
                fps_estimates
            )

    show_core_details(
        selected_recommendation
    )

    maximum_final_price = max(
        budget,
        selected_recommendation["estimated_total"]
    )

    remaining_budget = (
        maximum_final_price
        - selected_recommendation["core_price"]
    )

    st.markdown("## Customise Supporting Parts")

    render_html(
        '<div class="customise-panel">'
        '<div class="customise-title">Remaining budget for motherboard, RAM and storage</div>'
        f'<div class="customise-value">${remaining_budget:.2f}</div>'
        '</div>'
    )

    selected_association_items = build_association_items(
        cpu=selected_cpu,
        gpu=selected_gpu,
        psu=selected_psu
    )

    motherboard_rule_suggestions = recommend_associated_parts(
        selected_items=selected_association_items,
        rules=rules,
        required_component_type="Motherboard",
        limit=5
    )

    compatible_motherboards = find_compatible_motherboards(
        selected_cpu,
        motherboards,
        remaining_budget
    )

    compatible_motherboards = reorder_components_by_rules(
        compatible_motherboards,
        motherboard_rule_suggestions
    )

    suggested_motherboard_names = get_suggested_component_names(
        motherboard_rule_suggestions
    )

    if not compatible_motherboards:
        st.error("No compatible motherboards were found.")
        return

    motherboard_options = [
        format_component(motherboard)
        for motherboard in compatible_motherboards
    ]

    selected_motherboard_label = st.selectbox(
        "Choose Motherboard",
        motherboard_options
    )

    selected_motherboard = compatible_motherboards[
        motherboard_options.index(selected_motherboard_label)
    ]

    if selected_motherboard.name in suggested_motherboard_names:
        st.success(
            "This motherboard was prioritised by association rules."
        )

    remaining_after_motherboard = (
        remaining_budget
        - selected_motherboard.price
    )

    selected_association_items = build_association_items(
        cpu=selected_cpu,
        gpu=selected_gpu,
        psu=selected_psu,
        motherboard=selected_motherboard
    )

    ram_rule_suggestions = recommend_associated_parts(
        selected_items=selected_association_items,
        rules=rules,
        required_component_type="RAM",
        limit=5
    )

    compatible_ram = find_compatible_ram(
        selected_motherboard,
        rams,
        remaining_after_motherboard
    )

    compatible_ram = reorder_components_by_rules(
        compatible_ram,
        ram_rule_suggestions
    )

    suggested_ram_names = get_suggested_component_names(
        ram_rule_suggestions
    )

    if not compatible_ram:
        st.error("No compatible RAM was found.")
        return

    ram_options = [
        format_component(ram)
        for ram in compatible_ram
    ]

    selected_ram_label = st.selectbox(
        "Choose RAM",
        ram_options
    )

    selected_ram = compatible_ram[
        ram_options.index(selected_ram_label)
    ]

    if selected_ram.name in suggested_ram_names:
        st.success(
            "This RAM was prioritised by association rules."
        )

    remaining_after_ram = (
        remaining_after_motherboard
        - selected_ram.price
    )

    selected_association_items = build_association_items(
        cpu=selected_cpu,
        gpu=selected_gpu,
        psu=selected_psu,
        motherboard=selected_motherboard,
        ram=selected_ram
    )

    storage_rule_suggestions = recommend_associated_parts(
        selected_items=selected_association_items,
        rules=rules,
        required_component_type="Storage",
        limit=5
    )

    affordable_storage = find_affordable_storage(
        storages,
        remaining_after_ram
    )

    affordable_storage = reorder_components_by_rules(
        affordable_storage,
        storage_rule_suggestions
    )

    suggested_storage_names = get_suggested_component_names(
        storage_rule_suggestions
    )

    if not affordable_storage:
        st.error("No storage options were found.")
        return

    storage_options = [
        format_component(storage)
        for storage in affordable_storage
    ]

    selected_storage_label = st.selectbox(
        "Choose Storage",
        storage_options
    )

    selected_storage = affordable_storage[
        storage_options.index(selected_storage_label)
    ]

    if selected_storage.name in suggested_storage_names:
        st.success(
            "This storage option was prioritised by association rules."
        )

    final_build = PCBUILD()

    final_build.add_component(selected_cpu)
    final_build.add_component(selected_gpu)
    final_build.add_component(selected_motherboard)
    final_build.add_component(selected_ram)
    final_build.add_component(selected_storage)
    final_build.add_component(selected_psu)

    is_compatible = final_build_is_compatible(
        selected_cpu,
        selected_gpu,
        selected_psu,
        selected_motherboard,
        selected_ram,
        selected_storage
    )

    if not is_compatible:
        st.error(
            "The final build contains incompatible components."
        )
        return

    show_final_build(
        final_build,
        budget
    )

    if st.button("Save Build"):
        final_build.save_build()
        st.success(
            "Build saved to output/build.txt"
        )


if __name__ == "__main__":
    main()